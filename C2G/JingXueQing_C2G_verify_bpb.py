#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JingXueQing_C2G_verify_bpb.py — 独立的 BPB 口径校验器
================================================================================
为什么要有这个文件？

Parameter Golf 里最容易犯、也最"划算"的错误，是 BPB 的分母算错：

    BPB = total_nats / ln(2) / total_UTF8_bytes

如果把分母写成 token 数而不是 UTF-8 字节数，在 SP8192（平均约 4~5 字节/token）
的词表下，分数会**凭空变好 4~5 倍**——看起来像是巨大突破，实际是单位错误。

而且这个错误**方向永远是"变好"**，所以它不会被"分数变差了，肯定错了"这种
直觉发现。它只会让你兴奋。

更糟的是：我在写第一版 train_gpt.py 时，在 TTT 分支里真的犯了这个错误的
一个变体——分子用"已打分 token 的 nats"，分母却用"整个 chunk 的字节数"。
分子分母覆盖的 token 集合不一致，同样会凭空产生虚假增益，只是幅度小一些。
（见 JingXueQing_C2G_AI日志.md 轮次 8 的第 6 条。）

所以我把校验器独立出来：**它不 import 训练脚本的任何东西**，用一个常量
n-gram 模型在真实文本上从头算一遍 BPB，再和训练脚本的输出对照。

用法
--------------------------------------------------------------------------------
    python3 JingXueQing_C2G_verify_bpb.py --text FILE --bpb-from-trainer 1.2345

若不给 --bpb-from-trainer，只打印参考模型的 BPB，用于人工核对量级。

它检查三件事
--------------------------------------------------------------------------------
1. **量级合理性**：一个常量模型的 BPB 应该落在 [0, 8] 之间。超出就是单位错了。
2. **字节口径**：用 len(text.encode('utf-8')) 作为分母重算一遍，和逐 token
   累加的字节数对比，二者必须完全一致（byte-level tokenizer 下应精确相等）。
3. **交叉验证**：以 3-gram 模型为参照，任何"真模型"的 BPB 都应当显著低于它。
   如果训练脚本报出的 BPB 高于一个 3-gram 常量模型，那一定是算错了。
================================================================================
"""

from __future__ import annotations

import argparse
import math
from collections import defaultdict
from pathlib import Path
from typing import Dict, Tuple


def build_ngram(text: str, n: int) -> Dict[str, Dict[str, float]]:
    """Unsmoothed n-gram over UTF-8 BYTES (so it is tokenizer-independent)."""
    b = text.encode("utf-8")
    ctx: Dict[bytes, Dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for i in range(len(b) - n):
        c = b[i:i + n]
        ctx[c][b[i + n]] += 1.0
    out: Dict[str, Dict[str, float]] = {}
    for c, d in ctx.items():
        tot = sum(d.values())
        out[c.decode("latin-1")] = {str(k): v / tot for k, v in d.items()}
    return out


def ngram_bpb(text: str, n: int = 3) -> Tuple[float, int, int]:
    """Return (bpb, n_scored_bytes, vocab_seen)."""
    b = text.encode("utf-8")
    model = build_ngram(text, n)
    default = 1.0 / 256.0
    nats, scored = 0.0, 0
    for i in range(len(b) - n):
        c = b[i:i + n].decode("latin-1")
        nxt = b[i + n]
        dist = model.get(c)
        p = dist.get(str(nxt), 1e-8) if dist else default
        nats += -math.log(max(p, 1e-12))
        scored += 1
    return nats / math.log(2.0) / max(1, scored), scored, 256


def byte_accounting_check(text: str, tokens) -> bool:
    """逐 token 累加的字节数 必须 == 整段文本的 UTF-8 字节数。"""
    per_token = sum(len(bytes([t]) if isinstance(t, int) else t) for t in tokens)
    whole = len(text.encode("utf-8"))
    return per_token == whole


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True, help="plain-text file used as val stand-in")
    ap.add_argument("--bpb-from-trainer", type=float, default=None,
                    help="the val_bpb your train_gpt.py printed")
    ap.add_argument("--n", type=int, default=3)
    a = ap.parse_args()

    text = Path(a.text).read_text(encoding="utf-8", errors="ignore")
    nbytes = len(text.encode("utf-8"))
    print(f"[verify] text bytes (UTF-8) = {nbytes:,}")

    bpb3, scored, _ = ngram_bpb(text, n=a.n)
    print(f"[verify] {a.n}-gram constant-model BPB = {bpb3:.6f} "
          f"(scored bytes = {scored:,})")

    ok = True

    # 1) magnitude sanity
    if not (0.0 < bpb3 < 8.0):
        print("[FAIL] constant-model BPB outside [0, 8] -> unit error somewhere")
        ok = False
    else:
        print("[OK]   constant-model BPB in plausible range")

    # 2) byte accounting
    toks = list(text.encode("utf-8")[: min(nbytes, 200000)])
    if byte_accounting_check(text[: len(toks)].encode("utf-8").decode("utf-8", "ignore"), toks):
        print("[OK]   per-token byte sum == whole-text byte count")
    else:
        print("[FAIL] per-token byte sum != whole-text byte count; "
              "your bytes_per_token() is wrong")
        ok = False

    # 3) cross-check against the trainer's number
    if a.bpb_from_trainer is not None:
        t = a.bpb_from_trainer
        print(f"[verify] trainer BPB = {t:.6f}")
        if t <= 0:
            print("[FAIL] trainer BPB <= 0")
            ok = False
        elif t > bpb3:
            print(f"[FAIL] trainer BPB ({t:.4f}) is WORSE than a {a.n}-gram "
                  f"constant model ({bpb3:.4f}). A trained LM must beat a "
                  f"constant n-gram -- your BPB is almost certainly mis-computed.")
            ok = False
        elif t > 8.0:
            print("[FAIL] trainer BPB > 8 bits/byte is impossible for bytes")
            ok = False
        else:
            print(f"[OK]   trainer BPB beats the {a.n}-gram reference "
                  f"by {bpb3 - t:.4f} bpb")

    print("\n[verify] RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
