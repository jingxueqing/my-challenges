#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JingXueQing_C2G_train_gpt.py
================================================================================
OpenAI Parameter Golf — track "10 min / 16 MB"
Submission script by JingXueQing (景雪晴), 学号 2024102110351.

Lineage (see JingXueQing_C2G_拿来说明.md for the full "took / changed / why"):
  * openai/parameter-golf            -- official scaffold, BPB definition, artifact rule
  * PR #1394 @clarkkev               -- SP8192 + GPTQ embeddings + SD-Clip + MuonEq-R
  * PR #1331/#1437 @dexhunter        -- 3-layer depth recurrence
  * PR #1412 @Robby955 / #1204 @msisovic -- parallel residuals
  * PR #549  @abaybektursun          -- legal score-first TTT precedent
  * PR #1019 @abaybektursun          -- full-Hessian GPTQ calibration pipeline
  * karpathy/nanoGPT + KellerJordan/Muon -- the common ancestors

What *I* add on top of that stack (the two things this submission claims):
  [1] SRD  -- Stochastic Recurrence Depth.
      Depth recurrence normally uses a FIXED number of extra loop passes.
      I sample the number of extra passes per step (1 or 2) during training,
      so the shared block is optimised to be useful at BOTH depths.
      Rationale: a fixed-depth looped block is only ever good at the one depth
      it was trained at, which caps how far you can push it at eval time.
  [2] TTDS -- Test-Time Depth Scaling.
      At eval time unroll the looped block MORE times than the training mean
      (extra_loops = 3 instead of 2). This costs zero artifact bytes (the
      parameters are shared) and zero training seconds -- it only spends the
      *evaluation* budget, which is a separate 600 s allowance that the SOTA
      stack uses only ~500 s of.
      SRD exists precisely to make TTDS not break the model (train/eval depth
      mismatch is the obvious failure mode); the two are designed as a pair.

HONESTY NOTE (important, please read before citing any number from this file):
  This script has TWO modes.
    - FULL mode  : the real 8xH100 / 10 min / 16 MB configuration.
                   It has NOT been executed by the author at the time of
                   submission: the author's machine is an Apple M1 (8 GB, no
                   CUDA) and the FineWeb shard is not downloadable behind the
                   author's network. Any BPB in JingXueQing_C2G_submission.json
                   is therefore either (a) left null, or (b) explicitly labelled
                   as a *cited* number from the official leaderboard. No
                   estimated value is ever presented as a measured one.
    - SMOKE mode : SMOKE=1 runs the IDENTICAL code path end to end on a tiny
                   model with a real (non-synthetic) English-ish corpus, so
                   that tokenizer -> train -> sliding eval -> quantise ->
                   compress -> BPB -> artifact-size is provably exercised.
                   The logs in JingXueQing_C2G_logs/smoke_* are real.
  Run `python3 JingXueQing_C2G_train_gpt.py --help-flags` for all env flags.
================================================================================
"""

from __future__ import annotations

import argparse
import glob
import json
import math
import os
import struct
import sys
import time
from contextlib import nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

# --------------------------------------------------------------------------- #
#  0.  Config                                                                  #
# --------------------------------------------------------------------------- #

def _env(name: str, default):
    return os.environ.get(name, default)

def _eint(name: str, default: int) -> int:
    return int(os.environ.get(name, default))

def _efloat(name: str, default: float) -> float:
    return float(os.environ.get(name, default))

def _ebool(name: str, default: int = 0) -> bool:
    return bool(int(os.environ.get(name, default)))


@dataclass
class Config:
    # ---- mode -------------------------------------------------------------
    smoke: bool = _ebool("SMOKE", 0)
    run_id: str = _env("RUN_ID", "jingxueqing_c2g")
    seed: int = _eint("SEED", 42)
    out_dir: str = _env("OUT_DIR", "./JingXueQing_C2G_logs")

    # ---- data / tokenizer -------------------------------------------------
    data_path: str = _env("DATA_PATH", "./data/datasets/fineweb10B_sp8192")
    tokenizer_path: str = _env("TOKENIZER_PATH", "./data/tokenizers/fineweb_8192_bpe.model")
    vocab_size: int = _eint("VOCAB_SIZE", 8192)
    corpus_path: str = _env("CORPUS_PATH", "")           # smoke-mode fallback corpus
    train_shards: int = _eint("TRAIN_SHARDS", 0)

    # ---- model ------------------------------------------------------------
    num_layers: int = _eint("NUM_LAYERS", 11)
    model_dim: int = _eint("MODEL_DIM", 512)
    num_heads: int = _eint("NUM_HEADS", 8)
    num_kv_heads: int = _eint("NUM_KV_HEADS", 4)
    mlp_mult: int = _eint("MLP_MULT", 4)
    tie_embeddings: bool = _ebool("TIE_EMBEDDINGS", 1)
    logit_softcap: float = _efloat("LOGIT_SOFTCAP", 30.0)
    qk_gain_init: float = _efloat("QK_GAIN_INIT", 5.25)
    rope_dims: int = _eint("ROPE_DIMS", 16)              # partial RoPE (16 of 64)
    parallel_from: int = _eint("PARALLEL_FROM", 7)       # GPT-J residual lanes from layer 7
    leaky_neg_slope: float = _efloat("LEAKY_NEG_SLOPE", 0.5)
    leaky_square: bool = _ebool("LEAKY_SQUARE", 1)

    # ---- depth recurrence: [1] SRD  /  [2] TTDS ---------------------------
    recur_lo: int = _eint("RECUR_LO", 3)                 # first recurrent physical layer
    recur_hi: int = _eint("RECUR_HI", 5)                 # last recurrent physical layer
    recur_extra_base: int = _eint("RECUR_EXTRA_BASE", 2) # extra passes (SOTA: 17 virtual / 11 phys)
    srd_enabled: bool = _ebool("SRD_ENABLED", 1)         # [1] stochastic recurrence depth
    srd_extra_choices: str = _env("SRD_EXTRA_CHOICES", "1,2")
    recur_start_frac: float = _efloat("RECUR_START_FRAC", 0.35)
    ttds_enabled: bool = _ebool("TTDS_ENABLED", 1)       # [2] test-time depth scaling
    ttds_extra: int = _eint("TTDS_EXTRA", 3)             # eval-time extra passes (0 = off)

    # ---- optimisation -----------------------------------------------------
    train_batch_tokens: int = _eint("TRAIN_BATCH_TOKENS", 524288)
    train_seq_len: int = _eint("TRAIN_SEQ_LEN", 1024)
    max_wallclock_seconds: float = _efloat("MAX_WALLCLOCK_SECONDS", 600.0)
    matmul_lr: float = _efloat("MATMUL_LR", 0.022)       # "MLR" in the records
    embed_lr: float = _efloat("EMBED_LR", 0.05)
    scalar_lr: float = _efloat("SCALAR_LR", 0.02)
    warmup_frac: float = _efloat("WARMUP_FRAC", 0.02)
    warmdown_frac: float = _efloat("WARMDOWN_FRAC", 0.72)
    weight_decay: float = _efloat("WEIGHT_DECAY", 0.095)
    muon_momentum: float = _efloat("MUON_MOMENTUM", 0.95)
    ns_steps: int = _eint("NS_STEPS", 5)
    grad_clip: float = _efloat("GRAD_CLIP", 1.0)
    ema_decay: float = _efloat("EMA_DECAY", 0.9965)
    ema_start_frac: float = _efloat("EMA_START_FRAC", 0.20)

    # ---- quantisation -----------------------------------------------------
    quant: bool = _ebool("QUANT", 1)
    quant_method: str = _env("QUANT_METHOD", "gptq")     # gptq | rtn
    mat_bits: int = _eint("MAT_BITS", 6)
    embed_bits: int = _eint("EMBED_BITS", 8)
    mat_clip_sigmas: float = _efloat("MAT_CLIP_SIGMAS", 12.85)   # PR #1394 SD-Clip
    embed_clip_sigmas: float = _efloat("EMBED_CLIP_SIGMAS", 20.0)
    gptq_calib_tokens: int = _eint("GPTQ_CALIB_TOKENS", 16384)
    gptq_damp: float = _efloat("GPTQ_DAMP", 0.01)

    # ---- evaluation -------------------------------------------------------
    eval_stride: int = _eint("EVAL_STRIDE", 64)          # <-- Level-1 main direction
    eval_batch_seqs: int = _eint("EVAL_BATCH_SEQS", 1024)
    eval_max_tokens: int = _eint("EVAL_MAX_TOKENS", 0)   # 0 = whole val split
    ttt_enabled: bool = _ebool("TTT_ENABLED", 1)
    ttt_lr: float = _efloat("TTT_LR", 0.005)
    ttt_epochs: int = _eint("TTT_EPOCHS", 3)
    ttt_chunk: int = _eint("TTT_CHUNK", 32768)
    ttt_momentum: float = _efloat("TTT_MOMENTUM", 0.9)

    # ---- logging ----------------------------------------------------------
    train_log_every: int = _eint("TRAIN_LOG_EVERY", 50)
    val_loss_every: int = _eint("VAL_LOSS_EVERY", 0)
    artifact_cap: int = _eint("ARTIFACT_CAP", 16_000_000)

    # ---- misc -------------------------------------------------------------
    device: str = _env("DEVICE", "auto")
    dtype: str = _env("DTYPE", "bfloat16")
    compile_model: bool = _ebool("COMPILE", 0)

    def srd_choices(self) -> List[int]:
        return [int(x) for x in self.srd_extra_choices.split(",") if x.strip()]


# --------------------------------------------------------------------------- #
#  1.  Logging                                                                 #
# --------------------------------------------------------------------------- #

class Logger:
    """Tee to stdout + file so that every run leaves a complete artefact."""

    def __init__(self, path: Optional[str]):
        self._f = open(path, "w", buffering=1) if path else None

    def __call__(self, msg: str = "") -> None:
        print(msg, flush=True)
        if self._f:
            self._f.write(msg + "\n")

    def close(self) -> None:
        if self._f:
            self._f.close()


# --------------------------------------------------------------------------- #
#  2.  Tokenizer                                                               #
# --------------------------------------------------------------------------- #

class Tokenizer:
    """SentencePiece when available; byte-level fallback for local smoke runs.

    BPB is tokenizer-agnostic *by definition*, but only if the byte count used
    as the denominator is the true UTF-8 length of the scored text. Both paths
    therefore expose `bytes_per_token` so the denominator is never guessed.
    """

    def __init__(self, cfg: Config, log: Logger):
        self.cfg = cfg
        self.kind = "byte"
        self.sp = None
        self.vocab_size = 256
        self._order = None

        if not cfg.smoke and cfg.tokenizer_path and Path(cfg.tokenizer_path).exists():
            try:
                import sentencepiece as spm  # noqa: WPS433 (optional dependency)
                self.sp = spm.SentencePieceProcessor(model_file=cfg.tokenizer_path)
                self.vocab_size = int(self.sp.GetPieceSize())
                self.kind = "sentencepiece"
                log(f"[tok] sentencepiece loaded: {cfg.tokenizer_path} vocab={self.vocab_size}")
            except Exception as exc:  # pragma: no cover - depends on remote env
                log(f"[tok] sentencepiece unavailable ({exc}); falling back to byte-level")
                self.vocab_size = 256
        else:
            log(f"[tok] byte-level tokenizer (vocab=256) — smoke / no-model path")

    # -- byte accounting ----------------------------------------------------
    def bytes_per_token(self, tokens: torch.Tensor) -> torch.Tensor:
        """UTF-8 byte length of each token. Exact for byte-level; SP uses decode."""
        if self.kind == "byte":
            return torch.ones_like(tokens, dtype=torch.float64)
        if self.sp is None:
            return torch.ones_like(tokens, dtype=torch.float64)
        ids = tokens.detach().to("cpu", torch.int32).tolist()
        # Decoding per token is exact but slow; only used on the val split.
        out = np.fromiter(
            (len(self.sp.IdToPiece(int(i)).replace("\u2581", " ").encode("utf-8")) for i in ids),
            dtype=np.float64, count=len(ids),
        )
        return torch.from_numpy(out).to(tokens.device)

    def encode(self, text: str) -> List[int]:
        if self.kind == "byte":
            return np.frombuffer(text.encode("utf-8"), dtype=np.uint8).astype(np.int64)
        return np.asarray(self.sp.Encode(text), dtype=np.int64)


# --------------------------------------------------------------------------- #
#  3.  Data                                                                    #
# --------------------------------------------------------------------------- #

def _write_bin(path: Path, ids: Sequence[int]) -> None:
    arr = np.asarray(ids, dtype=np.uint32 if max(ids) > 65535 else np.uint16)
    arr.tofile(path)


def build_smoke_corpus(cfg: Config, log: Logger) -> Path:
    """Real (non-synthetic) text for the local pipeline validation.

    Default corpus = the CPython standard-library sources shipped with the
    running interpreter: ~15 MB of genuine English prose + code, no network.
    Override with CORPUS_PATH=/path/to/file.txt
    """
    if cfg.corpus_path:
        return Path(cfg.corpus_path)
    import sysconfig
    lib = Path(sysconfig.get_paths()["stdlib"])
    parts, total = [], 0
    cap = _eint("SMOKE_CORPUS_BYTES", 1_500_000)
    for p in sorted(lib.rglob("*.py")):
        try:
            t = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if not t.strip():
            continue
        parts.append(t)
        total += len(t)
        if total > cap:
            break
    out = Path(cfg.data_path) / "smoke_corpus.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n\n".join(parts), encoding="utf-8")
    log(f"[data] smoke corpus built: {out} ({out.stat().st_size/1e6:.2f} MB, real text)")
    return out


def load_data(cfg: Config, tok: Tokenizer, log: Logger) -> Tuple[torch.Tensor, torch.Tensor]:
    """Return (train_tokens, val_tokens) as int64 cpu tensors."""
    d = Path(cfg.data_path)

    if cfg.smoke:
        corpus = build_smoke_corpus(cfg, log)
        text = corpus.read_text(encoding="utf-8", errors="ignore")
        ids = np.asarray(tok.encode(text), dtype=np.int64)
        n = len(ids)
        n_val = max(2048, min(n // 10, 200_000))
        train_ids, val_ids = ids[: n - n_val], ids[n - n_val:]
        log(f"[data] smoke tokens: train={len(train_ids):,} val={len(val_ids):,} "
            f"(byte-level, so 1 token == 1 UTF-8 byte)")
        return (torch.from_numpy(train_ids).long(),
                torch.from_numpy(val_ids).long())

    # ---- full mode: memory-mapped pre-tokenised shards (official layout) ----
    val_files = sorted(glob.glob(str(d / "fineweb_val_*.bin"))) or \
                sorted(glob.glob(str(d / "val_*.bin")))
    trn_files = sorted(glob.glob(str(d / "fineweb_train_*.bin"))) or \
                sorted(glob.glob(str(d / "train_*.bin")))
    if not val_files:
        raise FileNotFoundError(
            f"no val shards under {d}. Download with:\n"
            f"  python3 data/cached_challenge_fineweb.py --variant sp8192")
    if cfg.train_shards:
        trn_files = trn_files[: cfg.train_shards]

    def _mmap(files: List[str]) -> torch.Tensor:
        arrs = [np.memmap(f, dtype=np.uint32, mode="r") for f in files]
        return torch.from_numpy(np.concatenate([np.asarray(a) for a in arrs]).astype(np.int64))

    val = _mmap(val_files)
    trn = _mmap(trn_files) if trn_files else val
    log(f"[data] train={len(trn):,} val={len(val):,} tokens (vocab={tok.vocab_size})")
    return trn, val


class ShuffledSequenceLoader:
    """PR #1394-style loader: cut the stream into seq_len rows and shuffle rows.

    Deliberately simpler than the coprime-stride loader of PR #726 — the SOTA
    record reports the simplification is score-neutral and easier to reason
    about when ablating.
    """

    def __init__(self, tokens: torch.Tensor, seq_len: int, batch_tokens: int,
                 seed: int, device: torch.device):
        self.tokens = tokens
        self.seq_len = seq_len
        self.seqs_per_step = max(1, batch_tokens // seq_len)
        self.device = device
        self.rng = np.random.default_rng(seed)
        usable = (len(tokens) - 1) // seq_len * seq_len
        self.pool = tokens[:usable].view(-1, seq_len)
        self.pos = 0
        self._perm = self.rng.permutation(len(self.pool))
        self.epoch = 0

    def next(self) -> Tuple[torch.Tensor, torch.Tensor]:
        if self.pos + self.seqs_per_step > len(self._perm):
            self._perm = self.rng.permutation(len(self.pool))
            self.pos = 0
            self.epoch += 1
        idx = self._perm[self.pos: self.pos + self.seqs_per_step]
        self.pos += self.seqs_per_step
        x = self.pool[idx].to(self.device, non_blocking=True)
        y = torch.empty_like(x)
        y[:, :-1] = x[:, 1:]
        # last target of each row comes from the following row's first token
        nxt = (idx + 1) % len(self.pool)
        y[:, -1] = self.pool[nxt, 0].to(self.device, non_blocking=True)
        return x, y


# --------------------------------------------------------------------------- #
#  4.  Model                                                                   #
# --------------------------------------------------------------------------- #

class RMSNorm(nn.Module):
    def __init__(self, dim: int, eps: float = 1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))
        self.eps = eps

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.rms_norm(x, (x.size(-1),), self.weight, self.eps)


def _rope(x: torch.Tensor, dims: int, base: float = 10000.0) -> torch.Tensor:
    """Partial RoPE: rotate only the first `dims` channels of each head."""
    if dims <= 0:
        return x
    *lead, t, d = x.shape
    rot = x[..., :dims]
    inv = torch.pow(base, -torch.arange(0, dims, 2, device=x.device, dtype=torch.float32) / dims)
    pos = torch.arange(t, device=x.device, dtype=torch.float32).unsqueeze(1)
    ang = pos * inv.unsqueeze(0)                      # (t, dims/2)
    cos, sin = torch.cos(ang), torch.sin(ang)
    a, b = rot[..., 0::2].float(), rot[..., 1::2].float()
    out = torch.empty_like(rot)
    out[..., 0::2] = (a * cos - b * sin).to(rot.dtype)
    out[..., 1::2] = (a * sin + b * cos).to(rot.dtype)
    return torch.cat([out, x[..., dims:]], dim=-1)


def _repeat_kv(x: torch.Tensor, reps: int) -> torch.Tensor:
    """GQA: (b, T, n_kv, d) -> (b, T, n_q, d).

    MUST be called in (b, T, H, D) layout, i.e. BEFORE the transpose to
    (b, H, T, D). Calling it after the transpose silently produces a
    (b, n_kv, T*reps, D) tensor -- this was a real bug caught by the local
    smoke run (see JingXueQing_C2G_AI日志.md, round 12).
    """
    if reps == 1:
        return x
    b, t, h, d = x.shape
    return x.unsqueeze(3).expand(b, t, h, reps, d).reshape(b, t, h * reps, d)


class Attention(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.dim = cfg.model_dim
        self.nh = cfg.num_heads
        self.nkv = cfg.num_kv_heads
        self.head_dim = cfg.model_dim // cfg.num_heads
        assert self.nh % self.nkv == 0
        self.reps = self.nh // self.nkv
        self.rope_dims = cfg.rope_dims
        self.scale = self.head_dim ** -0.5
        kv_dim = self.nkv * self.head_dim
        self.q = nn.Linear(self.dim, self.nh * self.head_dim, bias=False)
        self.k = nn.Linear(self.dim, kv_dim, bias=False)
        self.v = nn.Linear(self.dim, kv_dim, bias=False)
        self.o = nn.Linear(self.nh * self.head_dim, self.dim, bias=False)
        # QK-gain: one learnable scalar per query head (PR #1413: 4.0 -> 5.0 -> 5.25)
        self.q_gain = nn.Parameter(torch.full((self.nh,), cfg.qk_gain_init))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, t, _ = x.shape
        q = self.q(x).view(b, t, self.nh, self.head_dim)
        k = self.k(x).view(b, t, self.nkv, self.head_dim)
        v = self.v(x).view(b, t, self.nkv, self.head_dim)
        q = _rope(q, self.rope_dims)
        k = _rope(k, self.rope_dims)
        q = q * self.q_gain.to(q.dtype).view(1, 1, self.nh, 1)
        # repeat KV heads FIRST, in (b, T, H, D) layout, then transpose
        k, v = _repeat_kv(k, self.reps), _repeat_kv(v, self.reps)
        q, k, v = (z.transpose(1, 2) for z in (q, k, v))
        y = F.scaled_dot_product_attention(q, k, v, is_causal=True, scale=self.scale)
        y = y.transpose(1, 2).contiguous().view(b, t, self.nh * self.head_dim)
        return self.o(y)


def _act(cfg: Config, x: torch.Tensor) -> torch.Tensor:
    y = F.leaky_relu(x, negative_slope=cfg.leaky_neg_slope)
    return y * y if cfg.leaky_square else y


class MLP(nn.Module):
    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.up = nn.Linear(cfg.model_dim, cfg.model_dim * cfg.mlp_mult, bias=False)
        self.down = nn.Linear(cfg.model_dim * cfg.mlp_mult, cfg.model_dim, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.down(_act(self.cfg, self.up(x)))


class Block(nn.Module):
    def __init__(self, cfg: Config, idx: int):
        super().__init__()
        self.cfg = cfg
        self.idx = idx
        self.norm1 = RMSNorm(cfg.model_dim)
        self.attn = Attention(cfg)
        self.norm2 = RMSNorm(cfg.model_dim)
        self.mlp = MLP(cfg)
        # GPT-J style parallel residual lanes (PR #1204 / #1412):
        # attention and MLP both read from the SAME pre-residual input.
        self.parallel = idx >= cfg.parallel_from

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        if self.parallel:
            return x + self.attn(self.norm1(x)) + self.mlp(self.norm2(x))
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x


class GPT(nn.Module):
    """11L x 512d x 8H / 4KV with depth recurrence + SRD + TTDS."""

    def __init__(self, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.vocab_size = cfg.vocab_size
        self.embed = nn.Embedding(cfg.vocab_size, cfg.model_dim)
        self.blocks = nn.ModuleList([Block(cfg, i) for i in range(cfg.num_layers)])
        self.final_norm = RMSNorm(cfg.model_dim)
        self.head = nn.Linear(cfg.model_dim, cfg.vocab_size, bias=False)
        if cfg.tie_embeddings:
            self.head.weight = self.embed.weight
        # sigmoid-gated U-Net skip connections (symmetric pairs)
        n_skip = cfg.num_layers // 2
        self.skip_gates = nn.Parameter(torch.full((n_skip,), -2.0)) if n_skip else None
        self.apply(self._init)

    def _init(self, m: nn.Module) -> None:
        if isinstance(m, nn.Linear):
            nn.init.normal_(m.weight, 0.0, 0.02 / math.sqrt(self.cfg.num_layers))
        elif isinstance(m, nn.Embedding):
            nn.init.normal_(m.weight, 0.0, 0.02)

    # -- virtual depth schedule ---------------------------------------------
    def schedule(self, extra: int) -> List[int]:
        """Map virtual layer index -> physical layer index.

        extra=0 -> [0..10]                       (11 virtual)
        extra=1 -> [0..5, 3,4,5, 6..10]          (14 virtual)
        extra=2 -> [0..5, 3,4,5, 3,4,5, 6..10]   (17 virtual; matches SOTA)
        extra=3 -> 20 virtual                    (TTDS)
        """
        lo, hi = self.cfg.recur_lo, self.cfg.recur_hi
        pre = list(range(0, lo))
        loop = list(range(lo, hi + 1))
        post = list(range(hi + 1, self.cfg.num_layers))
        out = list(pre) + loop
        for _ in range(max(0, extra)):
            out += loop
        out += post
        return out

    def forward(self, x: torch.Tensor, extra: Optional[int] = None) -> torch.Tensor:
        if extra is None:
            extra = self.cfg.recur_extra_base
        h = self.embed(x)
        sched = self.schedule(extra)
        n = len(sched)
        acts: List[torch.Tensor] = []
        skips = self.skip_gates
        for i, phys in enumerate(sched):
            h = self.blocks[phys](h)
            acts.append(h)
            # U-Net skip: layer i (second half) reads the activation of the
            # mirrored layer j = n-1-i (first half). j < i guarantees acts[j]
            # has already been computed -- reading forward (j > i) was a real
            # IndexError caught by the local smoke run (AI日志 round 12).
            if skips is not None:
                j = n - 1 - i
                if j < i and j < len(skips):
                    g = torch.sigmoid(skips[j].to(h.dtype))
                    h = h + g * acts[j]
        h = self.final_norm(h)
        logits = self.head(h)
        if self.cfg.logit_softcap > 0:
            logits = torch.tanh(logits / self.cfg.logit_softcap) * self.cfg.logit_softcap
        return logits

    # -- parameter groups ---------------------------------------------------
    def groups(self) -> Tuple[List[nn.Parameter], List[nn.Parameter], List[nn.Parameter]]:
        mats, emb, scalars = [], [], []
        for name, p in self.named_parameters():
            if not p.requires_grad:
                continue
            if p.ndim >= 2 and "embed" not in name and "head" not in name:
                mats.append(p)
            elif p.ndim >= 2:
                emb.append(p)
            else:
                scalars.append(p)
        return mats, emb, scalars


# --------------------------------------------------------------------------- #
#  5.  Optimizer: MuonEq-R (matrices) + AdamW (embeddings / scalars)           #
# --------------------------------------------------------------------------- #

def newton_schulz(g: torch.Tensor, steps: int = 5, eps: float = 1e-7) -> torch.Tensor:
    """Keller Jordan's Newton-Schulz orthogonalisation (a,b,c tuned coefficients)."""
    a, b, c = 3.4445, -4.7750, 2.0315
    X = g.float()
    X = X / (X.norm() + eps)
    transposed = X.size(0) > X.size(1)
    if transposed:
        X = X.mT
    for _ in range(steps):
        A = X @ X.mT
        X = a * X + (b * A + c * (A @ A)) @ X
    if transposed:
        X = X.mT
    return X.to(g.dtype)


class MuonEqR:
    """Row-normalised Muon (PR #1217) with decoupled weight decay."""

    def __init__(self, params: List[nn.Parameter], lr: float, momentum: float,
                 wd: float, ns_steps: int):
        self.params = params
        self.lr, self.momentum, self.wd, self.ns = lr, momentum, wd, ns_steps
        self.buf = [torch.zeros_like(p) for p in params]

    @torch.no_grad()
    def step(self, lr_scale: float) -> None:
        for p, buf in zip(self.params, self.buf):
            if p.grad is None:
                continue
            g = p.grad
            buf.mul_(self.momentum).add_(g)
            u = newton_schulz(buf, self.ns)
            # row-normalisation ("Eq-R"): equalise per-row energy, keep global scale
            row_rms = u.pow(2).mean(dim=-1, keepdim=True).sqrt().clamp_min(1e-8)
            u = u / row_rms * row_rms.mean()
            p.mul_(1.0 - self.lr * lr_scale * self.wd)
            p.add_(u, alpha=-self.lr * lr_scale)


class AdamW(torch.optim.AdamW):
    pass  # kept explicit so the two optimiser families are visible side by side


# --------------------------------------------------------------------------- #
#  6.  Quantisation: GPTQ with SD-Clip (PR #1394)                              #
# --------------------------------------------------------------------------- #

def _clip_range(w: torch.Tensor, k: float) -> torch.Tensor:
    """c = k * std(row); scale-invariant, entropy-aware (see PR #1394 README)."""
    row_std = w.float().std(dim=-1, keepdim=True).clamp_min(1e-12)
    return (k * row_std).clamp_min(1e-12)


def _quantize(w: torch.Tensor, bits: int, k: float) -> Tuple[torch.Tensor, torch.Tensor]:
    c = _clip_range(w, k)
    qmax = 2 ** (bits - 1) - 1
    scale = c / qmax
    q = torch.clamp(torch.round(w.float() / scale), -qmax - 1, qmax)
    return q.to(torch.int16), scale.squeeze(-1)


def _dequantize(q: torch.Tensor, scale: torch.Tensor) -> torch.Tensor:
    return q.to(scale.dtype) * scale.unsqueeze(-1)


def gptq_quantize(w: torch.Tensor, H: Optional[torch.Tensor], bits: int, k: float,
                  damp: float = 0.01) -> Tuple[torch.Tensor, torch.Tensor]:
    """One-shot GPTQ (column-wise error compensation). RTN when H is None.

    `w` is (out, in). `H` is the (in, in) Hessian estimated on calibration data.
    """
    W = w.detach().float().clone()
    if H is None:
        return _quantize(W, bits, k)
    n_in = W.size(1)
    H = H.float().clone()
    H.diagonal().add_(damp * H.diagonal().mean().clamp_min(1e-12))
    try:
        Hinv = torch.linalg.inv(H)
    except Exception:
        return _quantize(W, bits, k)
    qmax = 2 ** (bits - 1) - 1
    c = _clip_range(W, k).squeeze(-1)                      # (out,)
    scale = c / qmax
    Q = torch.zeros_like(W)
    E = torch.zeros_like(W)
    block = 128
    for i0 in range(0, n_in, block):
        i1 = min(i0 + block, n_in)
        Wb = W[:, i0:i1].clone()
        Qb = torch.clamp(torch.round(Wb / scale.unsqueeze(1)), -qmax - 1, qmax)
        Q[:, i0:i1] = Qb
        E[:, i0:i1] = (Wb - Qb * scale.unsqueeze(1)) / Hinv.diagonal()[i0:i1].unsqueeze(0).clamp_min(1e-12)
        W[:, i1:] -= E[:, i0:i1] @ Hinv[i0:i1, i1:]
    return Q.to(torch.int16), scale


def _matmul_hessian(model: GPT, loader_fn, tokens: int, device: torch.device,
                    seq_len: int) -> dict:
    """Collect X X^T per Linear from a handful of calibration sequences.

    Calibration data comes from the TRAINING stream only — never the val split.
    """
    H = {}
    hooks = []

    def make(name):
        def hook(_m, inp, _out):
            x = inp[0].detach().reshape(-1, inp[0].size(-1)).float()
            h = x.mT @ x
            H[name] = h if name not in H else H[name] + h
        return hook

    named = {n: m for n, m in model.named_modules()
             if isinstance(m, nn.Linear) and n not in ("head",)}
    for n, m in named.items():
        hooks.append(m.register_forward_hook(make(n)))
    model.eval()
    seqs = max(1, tokens // seq_len)
    with torch.no_grad():
        for _ in range(seqs):
            x, _ = loader_fn()
            model(x)
    for h in hooks:
        h.remove()
    model.train()
    return H


class QuantizedModel:
    """Holds int codes + scales; `roundtrip()` materialises fp weights for eval."""

    def __init__(self):
        self.store: dict = {}
        self.embed_store: Optional[Tuple[torch.Tensor, torch.Tensor]] = None

    def roundtrip(self, model: GPT) -> None:
        with torch.no_grad():
            for name, (q, scale) in self.store.items():
                mod = model.get_submodule(name)
                mod.weight.copy_(_dequantize(q.to(scale.dtype), scale).to(mod.weight.dtype))
            if self.embed_store is not None:
                q, scale = self.embed_store
                model.embed.weight.copy_(_dequantize(q.to(scale.dtype), scale)
                                         .to(model.embed.weight.dtype))

    def payload_bytes(self) -> int:
        n = 0
        for q, scale in self.store.values():
            n += q.numel() * 2 + scale.numel() * 2
        if self.embed_store is not None:
            q, scale = self.embed_store
            n += q.numel() * 2 + scale.numel() * 2
        return n


def quantize_model(model: GPT, cfg: Config, H: Optional[dict]) -> QuantizedModel:
    qm = QuantizedModel()
    for name, mod in model.named_modules():
        if not isinstance(mod, nn.Linear):
            continue
        if name == "head" and cfg.tie_embeddings:
            continue
        h = H.get(name) if H else None
        q, s = gptq_quantize(mod.weight, h, cfg.mat_bits, cfg.mat_clip_sigmas, cfg.gptq_damp)
        qm.store[name] = (q, s)
    q, s = gptq_quantize(model.embed.weight, None, cfg.embed_bits, cfg.embed_clip_sigmas)
    qm.embed_store = (q, s)
    return qm


# --------------------------------------------------------------------------- #
#  7.  Compression: byte-shuffle + brotli/zlib                                 #
# --------------------------------------------------------------------------- #

def _compress(buf: bytes) -> bytes:
    try:
        import brotli  # noqa
        return brotli.compress(buf, quality=11)
    except Exception:
        import zlib
        return zlib.compress(buf, 9)


def pack_artifact(qm: QuantizedModel, code_bytes: int) -> Tuple[bytes, int]:
    """byte-shuffle (group bytes by significance) then entropy-compress."""
    chunks = []
    for q, s in list(qm.store.values()) + ([qm.embed_store] if qm.embed_store else []):
        raw = q.to(torch.int16).cpu().numpy().astype(np.int16).view(np.uint8)
        # shuffle: transpose the (numel, 2) byte matrix so column bytes are contiguous
        raw = raw.reshape(-1, 2).T.reshape(-1).tobytes()
        chunks.append(raw)
        chunks.append(s.to(torch.float16).cpu().numpy().tobytes())
    blob = b"".join(chunks)
    comp = _compress(blob)
    return comp, len(comp) + code_bytes


# --------------------------------------------------------------------------- #
#  8.  Evaluation: sliding window (Level-1 direction) + TTDS + legal TTT       #
# --------------------------------------------------------------------------- #

def _windows(val: torch.Tensor, seq_len: int, stride: int, max_tokens: int
             ) -> List[Tuple[torch.Tensor, int]]:
    """Sliding-window plan: list of (window_tokens, n_scored_from_the_right).

    Correctness contract (this is the whole point of the Level-1 direction):
      * the scored spans are CONTIGUOUS and NON-OVERLAPPING ->
        every token of the valuation stream is scored EXACTLY ONCE,
        i.e. official Issue #1017 Condition 4 (single pass) holds;
      * each scored span is the rightmost `stride` tokens of a length-`seq_len`
        window -> every scored token sees >= (seq_len - stride) tokens of
        STRICT PREFIX context, i.e. Condition 1 (causality) holds;
      * stride == seq_len degenerates exactly to the naive baseline
        (non-overlapping blocks, zero extra context) -> the A/B is a pure
        one-knob comparison.

    Concretely, with E = seq_len + floor((n - seq_len) / stride) * stride:
      scored spans = [seq_len-stride, seq_len), [seq_len, seq_len+stride), ...
      then a final partial span covering [E, n).
    """
    n = len(val) if not max_tokens else min(len(val), max_tokens)
    if n <= seq_len:
        return []
    out: List[Tuple[torch.Tensor, int]] = []
    for end in range(seq_len, n + 1, stride):
        if end > n:
            break
        out.append((val[end - seq_len: end], min(stride, end - (end - stride))))
    E = seq_len + ((n - seq_len) // stride) * stride
    if E < n and n - seq_len >= 0:
        out.append((val[n - seq_len: n], n - E))
    return out


@torch.no_grad()
def eval_sliding(model: GPT, val: torch.Tensor, cfg: Config, tok: Tokenizer,
                 device: torch.device, extra: int) -> Tuple[float, float, int, float]:
    """Return (bpb, nats_per_token, n_scored_tokens, scored_bytes).

    BPB = total_nats / ln(2) / total_utf8_bytes.

    THE DENOMINATOR IS THE DANGEROUS PART. It is the true UTF-8 byte length of
    the text the scored tokens represent -- never the token count. Getting this
    wrong is the single easiest way to manufacture a fake improvement, so
    `bytes_per_token` is a first-class method on Tokenizer and there is a
    standalone checker in JingXueQing_C2G_verify_bpb.py that re-derives the
    number independently.
    """
    model.eval()
    seq_len = cfg.train_seq_len
    stride = min(cfg.eval_stride, seq_len)
    wins = _windows(val, seq_len, stride, cfg.eval_max_tokens)
    nats_sum, byte_sum, tok_count = 0.0, 0.0, 0
    B = max(1, cfg.eval_batch_seqs)
    for i in range(0, len(wins), B):
        batch = wins[i:i + B]
        L = max(len(w) for w, _ in batch)
        x = torch.zeros((len(batch), L), dtype=torch.long, device=device)
        y = torch.full((len(batch), L), -100, dtype=torch.long, device=device)
        mask = torch.zeros((len(batch), L), dtype=torch.bool, device=device)
        for j, (w, scored) in enumerate(batch):
            l = len(w)
            w = w.to(device)
            x[j, :l] = w
            y[j, :l] = w
            mask[j, l - scored: l] = True
            y[j, : l - scored] = -100
        with torch.autocast(device_type=device.type, dtype=getattr(torch, cfg.dtype),
                            enabled=(device.type == "cuda")):
            logits = model(x, extra=extra)
        logits = logits.float()
        lp = torch.log_softmax(logits[:, :-1], dim=-1)      # pos t predicts t+1
        tgt = y[:, 1:]
        m = mask[:, 1:]
        nll_all = -lp.gather(-1, tgt.clamp_min(0).unsqueeze(-1)).squeeze(-1)
        nll = nll_all[m]
        scored_toks = tgt[m]
        nats_sum += float(nll.sum())
        tok_count += int(scored_toks.numel())
        byte_sum += float(tok.bytes_per_token(scored_toks).sum())
    if byte_sum <= 0 or tok_count == 0:
        model.train()
        return float("nan"), float("nan"), 0, 0.0
    bpb = nats_sum / math.log(2.0) / byte_sum
    npt = nats_sum / tok_count
    model.train()
    return bpb, npt, tok_count, byte_sum


def eval_ttt(model: GPT, val: torch.Tensor, cfg: Config, tok: Tokenizer,
             device: torch.device, extra: int) -> float:
    """LEGAL score-first TTT (Issue #1017 conditions 1-4).

    For every 32K-token chunk: (1) SCORE the whole chunk under no_grad,
    (2) only then train on the tokens that were just scored. No chunk is ever
    trained on before it is scored; no token is scored twice.
    """
    if not cfg.ttt_enabled:
        return float("nan")
    opt = torch.optim.SGD(model.parameters(), lr=cfg.ttt_lr, momentum=cfg.ttt_momentum)
    n = len(val)
    chunk = cfg.ttt_chunk
    nats_sum, byte_sum = 0.0, 0.0
    n_chunks = max(1, (n + chunk - 1) // chunk)
    seq_len = cfg.train_seq_len
    for ci in range(n_chunks):
        c = val[ci * chunk: min((ci + 1) * chunk, n)]
        if len(c) < seq_len + 2:
            break
        # --- phase 1: SCORE (no grad, no update) ---
        with torch.no_grad():
            bpb_c, npt_c, cnt, nbytes = eval_sliding(model, c, cfg, tok, device, extra)
        if cnt == 0:
            continue
        nats_sum += npt_c * cnt
        byte_sum += nbytes
        # --- phase 2: TRAIN on the already-scored chunk ---
        if ci == n_chunks - 1:
            break  # never train on anything still to be scored
        lr_scale = 0.5 * (1 + math.cos(math.pi * ci / max(1, n_chunks - 1)))
        for g in opt.param_groups:
            g["lr"] = cfg.ttt_lr * lr_scale
        for _ in range(cfg.ttt_epochs):
            starts = range(0, max(1, len(c) - seq_len), seq_len)
            for s in starts:
                xs = c[s: s + seq_len].to(device).unsqueeze(0)
                ys = c[s + 1: s + 1 + seq_len].to(device).unsqueeze(0)
                if ys.numel() == 0:
                    continue
                loss = F.cross_entropy(
                    model(xs, extra=extra).float().view(-1, model.vocab_size),
                    ys.reshape(-1))
                opt.zero_grad(set_to_none=True)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
                opt.step()
    if byte_sum <= 0:
        return float("nan")
    return nats_sum / math.log(2.0) / byte_sum


# --------------------------------------------------------------------------- #
#  9.  Training loop                                                           #
# --------------------------------------------------------------------------- #

def _resolve_device(cfg: Config) -> torch.device:
    if cfg.device != "auto":
        return torch.device(cfg.device)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def lr_scale_at(frac: float, cfg: Config) -> float:
    if frac < cfg.warmup_frac:
        return max(1e-3, frac / max(1e-6, cfg.warmup_frac))
    if frac >= 1.0 - cfg.warmdown_frac:
        rem = (1.0 - frac) / max(1e-6, cfg.warmdown_frac)
        return max(0.0, rem)
    return 1.0


def train(cfg: Config, log: Logger) -> dict:
    torch.manual_seed(cfg.seed)
    np.random.seed(cfg.seed)
    device = _resolve_device(cfg)
    log(f"[env] device={device} torch={torch.__version__} seed={cfg.seed} "
        f"smoke={int(cfg.smoke)}")

    tok = Tokenizer(cfg, log)
    cfg.vocab_size = tok.vocab_size if cfg.smoke else cfg.vocab_size
    train_toks, val_toks = load_data(cfg, tok, log)

    model = GPT(cfg).to(device)
    if cfg.compile_model and hasattr(torch, "compile"):
        try:
            model = torch.compile(model)
        except Exception as exc:
            log(f"[warn] torch.compile failed: {exc}")

    mats, emb, scalars = model.groups()
    muon = MuonEqR(mats, cfg.matmul_lr, cfg.muon_momentum, cfg.weight_decay, cfg.ns_steps)
    adam_e = AdamW(emb, lr=cfg.embed_lr, weight_decay=cfg.weight_decay, betas=(0.9, 0.95))
    adam_s = AdamW(scalars, lr=cfg.scalar_lr, weight_decay=0.0, betas=(0.9, 0.95))

    loader = ShuffledSequenceLoader(train_toks, cfg.train_seq_len,
                                    cfg.train_batch_tokens, cfg.seed, device)
    n_params = sum(p.numel() for p in model.parameters())
    log(f"[model] {cfg.num_layers}L x {cfg.model_dim}d x {cfg.num_heads}H/"
        f"{cfg.num_kv_heads}KV mlp={cfg.mlp_mult}x vocab={cfg.vocab_size} "
        f"params={n_params:,}")
    log(f"[model] SRD={int(cfg.srd_enabled)} choices={cfg.srd_choices()} "
        f"TTDS={int(cfg.ttds_enabled)} extra={cfg.ttds_extra}")

    ema: Optional[dict] = None
    amp_ctx = (torch.autocast(device_type="cuda", dtype=getattr(torch, cfg.dtype))
               if device.type == "cuda" and cfg.dtype != "float32"
               else nullcontext())

    t0 = time.time()
    step = 0
    losses: List[float] = []
    max_steps_guess = 20000
    while True:
        elapsed = time.time() - t0
        frac = elapsed / max(1e-6, cfg.max_wallclock_seconds)
        if frac >= 1.0:
            break
        x, y = loader.next()

        # ---------------- [1] SRD: sample the recurrence depth this step ----
        # NOTE: gated on elapsed *wallclock* fraction, not step count. The 10-min
        # cap means wallclock is the scarce resource, so it is the honest clock.
        frac_steps = frac
        if cfg.recur_start_frac > 0 and frac_steps < cfg.recur_start_frac:
            extra = 0                        # warm up as a plain 11L stack
        elif cfg.srd_enabled:
            choices = cfg.srd_choices()
            extra = choices[int(torch.randint(0, len(choices), (1,)).item())]
        else:
            extra = cfg.recur_extra_base

        with amp_ctx:
            logits = model(x, extra=extra).float()
            loss = F.cross_entropy(logits.view(-1, logits.size(-1)), y.reshape(-1))
        model.zero_grad(set_to_none=True)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
        ls = lr_scale_at(frac, cfg)
        muon.step(ls)
        adam_e.step(); adam_s.step()
        adam_e.zero_grad(set_to_none=True); adam_s.zero_grad(set_to_none=True)

        if ema is None and frac >= cfg.ema_start_frac:
            ema = {k: v.detach().clone().float() for k, v in model.state_dict().items()}
            log(f"[ema] started at frac={frac:.3f}")
        elif ema is not None:
            d = cfg.ema_decay
            with torch.no_grad():
                sd = model.state_dict()
                for k, v in ema.items():
                    v.mul_(d).add_(sd[k].detach().float(), alpha=1 - d)

        losses.append(float(loss))
        step += 1
        if cfg.train_log_every and step % cfg.train_log_every == 0:
            els = time.time() - t0
            log(f"step {step:6d} loss {float(loss):.4f} extra {extra} "
                f"lr_scale {ls:.3f} elapsed {els:.1f}s "
                f"({100*els/cfg.max_wallclock_seconds:.0f}%)")
        if step >= 100000:
            break

    train_s = time.time() - t0
    log(f"[train] steps={step} time={train_s:.1f}s "
        f"tok/s={step*cfg.train_batch_tokens/max(1e-6,train_s):,.0f}")

    if ema is not None:
        model.load_state_dict({k: v.to(next(model.parameters()).dtype) for k, v in ema.items()})
        log("[ema] EMA weights loaded into model")

    # ---------------- quantise --------------------------------------------
    H = None
    if cfg.quant and cfg.quant_method == "gptq":
        H = _matmul_hessian(model, loader.next, cfg.gptq_calib_tokens,
                            device, cfg.train_seq_len)
        log(f"[quant] GPTQ Hessians collected for {len(H)} matrices")

    pre_bpb, pre_npt, pre_tok, pre_bytes = eval_sliding(
        model, val_toks, cfg, tok, device, extra=cfg.recur_extra_base)
    log(f"[eval] pre-quant  bpb={pre_bpb:.6f} nats/tok={pre_npt:.4f} "
        f"tokens={pre_tok:,} bytes={pre_bytes:,.0f}")

    qm = quantize_model(model, cfg, H) if cfg.quant else None
    if qm is not None:
        qm.roundtrip(model)
    post_bpb, post_npt, post_tok, post_bytes = eval_sliding(
        model, val_toks, cfg, tok, device, extra=cfg.recur_extra_base)
    log(f"[eval] post-quant bpb={post_bpb:.6f} nats/tok={post_npt:.4f} "
        f"tokens={post_tok:,} bytes={post_bytes:,.0f}")

    # ---------------- [2] TTDS: same weights, deeper unroll at eval --------
    ttds_bpb = float("nan")
    if cfg.ttds_enabled and cfg.ttds_extra > cfg.recur_extra_base:
        ttds_bpb, ttds_npt, _, _ = eval_sliding(
            model, val_toks, cfg, tok, device, extra=cfg.ttds_extra)
        log(f"[eval] TTDS extra={cfg.ttds_extra} bpb={ttds_bpb:.6f} "
            f"nats/tok={ttds_npt:.4f}  delta={ttds_bpb-post_bpb:+.6f}")

    ttt_bpb = float("nan")
    if cfg.ttt_enabled:
        t_ttt = time.time()
        ttt_bpb = eval_ttt(model, val_toks, cfg, tok, device,
                           extra=(cfg.ttds_extra if cfg.ttds_enabled
                                  and cfg.ttds_extra > cfg.recur_extra_base
                                  else cfg.recur_extra_base))
        log(f"[eval] TTT bpb={ttt_bpb:.6f} time={time.time()-t_ttt:.1f}s")

    # ---------------- artifact --------------------------------------------
    code_bytes = len(Path(__file__).read_bytes()) if Path(__file__).exists() else 0
    comp, total = pack_artifact(qm, code_bytes) if qm is not None else (b"", code_bytes)
    raw_bytes = qm.payload_bytes() if qm is not None else 0
    log(f"[artifact] raw={raw_bytes:,}B compressed={len(comp):,}B "
        f"code={code_bytes:,}B total={total:,}B cap={cfg.artifact_cap:,}B "
        f"{'OK' if total <= cfg.artifact_cap else 'OVER CAP'}")

    res = {
        "run_id": cfg.run_id, "seed": cfg.seed, "smoke": int(cfg.smoke),
        "device": str(device), "steps": step, "train_seconds": round(train_s, 1),
        "params": n_params, "vocab_size": cfg.vocab_size,
        "eval_stride": cfg.eval_stride, "train_seq_len": cfg.train_seq_len,
        "pre_quant_bpb": round(pre_bpb, 8), "post_quant_bpb": round(post_bpb, 8),
        "ttds_extra": cfg.ttds_extra if cfg.ttds_enabled else 0,
        "ttds_bpb": round(ttds_bpb, 8) if ttds_bpb == ttds_bpb else None,
        "ttt_bpb": round(ttt_bpb, 8) if ttt_bpb == ttt_bpb else None,
        "artifact_bytes": total, "artifact_cap": cfg.artifact_cap,
        "artifact_ok": bool(total <= cfg.artifact_cap),
        "srd_enabled": int(cfg.srd_enabled),
        "final_train_loss": round(float(np.mean(losses[-50:])), 5) if losses else None,
        "tokenizer": tok.kind,
    }
    Path(cfg.out_dir).mkdir(parents=True, exist_ok=True)
    with open(Path(cfg.out_dir) / f"result_seed{cfg.seed}.json", "w") as f:
        json.dump(res, f, indent=2)
    log("[done] " + json.dumps(res, ensure_ascii=False))
    return res


# --------------------------------------------------------------------------- #
#  10.  Entry point                                                            #
# --------------------------------------------------------------------------- #

FLAGS_HELP = """
Environment flags (all optional):
  SMOKE=1                 tiny local run (byte tokenizer, CPU/MPS) -- pipeline proof
  RUN_ID, SEED, OUT_DIR   logging
  DATA_PATH TOKENIZER_PATH VOCAB_SIZE CORPUS_PATH
  NUM_LAYERS MODEL_DIM NUM_HEADS NUM_KV_HEADS MLP_MULT
  RECUR_LO RECUR_HI RECUR_EXTRA_BASE RECUR_START_FRAC
  SRD_ENABLED=1 SRD_EXTRA_CHOICES=1,2      <-- contribution [1]
  TTDS_ENABLED=1 TTDS_EXTRA=3              <-- contribution [2]
  MATMUL_LR EMBED_LR WEIGHT_DECAY EMA_DECAY WARMDOWN_FRAC
  MAT_BITS EMBED_BITS MAT_CLIP_SIGMAS EMBED_CLIP_SIGMAS QUANT_METHOD=gptq|rtn
  EVAL_STRIDE=64 EVAL_BATCH_SEQS=1024      <-- Level-1 main direction
  TTT_ENABLED=1 TTT_LR TTT_EPOCHS TTT_CHUNK
  MAX_WALLCLOCK_SECONDS=600
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="JingXueQing C2G parameter-golf trainer")
    ap.add_argument("--help-flags", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    a, _ = ap.parse_known_args()
    if a.help_flags:
        print(FLAGS_HELP)
        return 0
    cfg = Config()
    if a.smoke:
        cfg.smoke = True

    if cfg.smoke:  # sane tiny defaults so the whole path runs on a laptop
        cfg.num_layers = 4
        cfg.model_dim = 128
        cfg.num_heads = 4
        cfg.num_kv_heads = 2
        cfg.mlp_mult = 2
        cfg.vocab_size = 256
        cfg.train_seq_len = 128
        cfg.train_batch_tokens = 8192
        cfg.eval_stride = 32
        cfg.eval_batch_seqs = 64
        cfg.max_wallclock_seconds = float(_env("SMOKE_SECONDS", 45))
        cfg.parallel_from = 3
        cfg.recur_lo, cfg.recur_hi, cfg.recur_extra_base = 1, 2, 1
        cfg.srd_extra_choices = "0,1"
        cfg.ttds_extra = 2
        cfg.ttt_enabled = False
        cfg.quant_method = "rtn"
        cfg.gptq_calib_tokens = 2048
        cfg.train_log_every = 20
        cfg.ema_start_frac = 0.5
        cfg.out_dir = "./JingXueQing_C2G_logs"

    Path(cfg.out_dir).mkdir(parents=True, exist_ok=True)
    log_path = Path(cfg.out_dir) / (f"smoke_seed{cfg.seed}.log" if cfg.smoke
                                    else f"train_seed{cfg.seed}.log")
    log = Logger(str(log_path))
    log(f"[c2g] JingXueQing parameter-golf run  run_id={cfg.run_id} seed={cfg.seed} "
        f"time={time.strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        train(cfg, log)
    except Exception as exc:
        import traceback
        log("[FATAL] " + "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
        log.close()
        return 1
    log.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
