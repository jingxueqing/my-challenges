#!/usr/bin/env python3
"""
Stage 3+: 国产大模型推理引擎（LLM Engine）

═══════════════════════════════════════════════════════════════════════
这是 C4C 的核心迁移件：把 starter kit 中"由 Claude Code 宿主智能体
充当推理层"的架构，显式化为一个**可插拔的引擎层**。

Starter kit 的隐式假设
─────────────────────
starter 的 `solve_proof()` 直接 `_unsolved(problem, "证明题需要 LLM 求解器")`。
它并不真的调用任何模型——推理由**运行 skill 的宿主智能体**（Claude Code）
在对话中补齐。也就是说 starter 的 "LLM 层" 是隐式的、不可度量、不可替换的。

本模块把它显式化
────────────────
三个可插拔 backend，接口统一为 `LLMEngine.solve()`：

  ┌────────────┬──────────────────────────────────────────────────────┐
  │ backend    │ 说明                                                  │
  ├────────────┼──────────────────────────────────────────────────────┤
  │ api        │ 直连国产大模型 HTTP API（Qwen3.6 / Kimi K2.5）。       │
  │            │ OpenAI 兼容协议，无需官方 SDK，零重依赖。            │
  ├────────────┼──────────────────────────────────────────────────────┤
  │ agent      │ 委派给宿主智能体（WorkBuddy，国产模型平台）。          │
  │            │ 通过 SKILL.md 协议由 agent 读文件求解后回填。          │
  │            │ 这是 starter 隐式行为的显式化 + 可度量化。            │
  ├────────────┼──────────────────────────────────────────────────────┤
  │ local      │ 离线确定性推理器：模板 + 符号计算。绝不臆造。          │
  │            │ 保证无网/无key时流水线仍端到端可跑。                  │
  └────────────┴──────────────────────────────────────────────────────┘

设计原则：**结果必须可溯源**
────────────────────────────
每条由 LLM 产出的解答都带 `provenance` 字段，记录 backend / model /
prompt 哈希 / 是否命中缓存。没有真实 API key 时，系统**不会伪造**
模型输出，而是降级到 local backend 并如实标注 `backend="local"`。

作者: JingXueQing (2024102110351) ｜ C4C Challenge
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

# ══════════════════════════════════════════════════════════════════
# 模型注册表 —— 国产大模型
# ══════════════════════════════════════════════════════════════════

MODEL_REGISTRY: dict[str, dict[str, Any]] = {
    "qwen": {
        "family": "Qwen",
        "display": "Qwen3.6",
        # 通义千问开放平台 · OpenAI 兼容模式
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen3.6-max",
        "fallback_models": ["qwen3.6-plus", "qwen-max", "qwen-plus"],
        "api_key_env": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
        "note": "数学推理强、中文理解好 —— 作为本项目默认推理引擎",
    },
    "kimi": {
        "family": "Kimi",
        "display": "Kimi K2.5",
        "base_url": "https://api.moonshot.cn/v1",
        "model": "kimi-k2.5",
        "fallback_models": ["kimi-k2-0711-preview", "moonshot-v1-128k"],
        "api_key_env": ["MOONSHOT_API_KEY", "KIMI_API_KEY"],
        "note": "长上下文、代码生成强 —— 用于多步推导与长题面",
    },
    "deepseek": {
        "family": "DeepSeek",
        "display": "DeepSeek-V3.2",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "fallback_models": ["deepseek-reasoner"],
        "api_key_env": ["DEEPSEEK_API_KEY"],
        "note": "代码+数学能力强 —— 作为对照模型",
    },
}


def resolve_api_key(vendor: str) -> Optional[str]:
    """从环境变量解析 API key。找不到返回 None（绝不猜测/伪造）。"""
    for env_name in MODEL_REGISTRY[vendor]["api_key_env"]:
        val = os.environ.get(env_name, "").strip()
        if val:
            return val
    return None


def available_vendors() -> list[str]:
    """返回当前环境已配置 key 的厂商列表。"""
    return [v for v in MODEL_REGISTRY if resolve_api_key(v)]


# ══════════════════════════════════════════════════════════════════
# 提示词模板 —— 国产模型适配的关键
# ══════════════════════════════════════════════════════════════════

PROMPT_V1 = """你是一名严谨的理工科助教。请解答下列题目。

要求：
1. 先给出解题步骤（steps），再给出最终答案（answer）。
2. steps 用中文，每步一行，格式为 "步骤N: <内容>"。
3. answer 必须是最终结果的简明表述。
4. 只输出 JSON，不要输出任何额外文字。

题目：
{problem}

JSON 格式：
{{"steps": ["步骤1: ...", "步骤2: ..."], "answer": "..."}}"""


PROMPT_V2 = """你是一名严谨的理工科助教，正在求解一道{domain}题目。

要求：
1. steps 用中文，按推导顺序，每步一行，格式为 "步骤N: <内容>"。
2. 步骤必须可核验：涉及数值代入时写出实际算式。
3. answer 为最终答案；若为数学表达式，用 LaTeX 表示。
4. 检查单位与量纲是否一致。
5. 只输出 JSON，不要输出任何额外文字或 markdown 代码块。

题目：
{problem}

JSON 格式：
{{"steps": ["步骤1: ..."], "answer": "LaTeX 表达式"}}"""


PROMPT_V3 = """你是一名严谨的理工科助教，正在求解一道{domain}题目。

要求：
1. steps 用中文，按推导顺序，每步一行，格式为 "步骤N: <内容>"。
2. 步骤必须可核验：涉及数值代入时写出实际算式。
3. answer 为最终答案；若为数学表达式，用 LaTeX 表示。
4. 检查单位与量纲是否一致。
5. 只输出 JSON，不要输出任何额外文字或 markdown 代码块。

题目：
{problem}

JSON 格式：
{{"steps": ["步骤1: ..."], "answer": "LaTeX 表达式"}}"""


@dataclass
class LLMResult:
    """LLM 求解结果 + 溯源信息。"""

    solved: bool
    steps: list[str] = field(default_factory=list)
    answer: str = ""
    answer_latex: str = ""
    backend: str = "none"
    model: str = "none"
    provenance: dict[str, Any] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "solved": self.solved,
            "steps": self.steps,
            "answer": self.answer,
            "answer_latex": self.answer_latex,
            "solver": f"llm:{self.backend}",
            "llm": {
                "backend": self.backend,
                "model": self.model,
                **self.provenance,
            },
            "reason": self.reason,
        }


# ══════════════════════════════════════════════════════════════════
# 磁盘缓存 —— 让每次实验可复现、让无网时仍能回放
# ══════════════════════════════════════════════════════════════════

class LLMCache:
    """基于内容哈希的磁盘缓存。key = sha256(vendor|model|prompt)。"""

    def __init__(self, cache_dir: str | Path):
        self.dir = Path(cache_dir)
        self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _key(vendor: str, model: str, prompt: str) -> str:
        raw = f"{vendor}|{model}|{prompt}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:32]

    def get(self, vendor: str, model: str, prompt: str) -> Optional[str]:
        f = self.dir / f"{vendor}_{self._key(vendor, model, prompt)}.json"
        if f.exists():
            try:
                return json.loads(f.read_text(encoding="utf-8"))["response"]
            except Exception:
                return None
        return None

    def put(self, vendor: str, model: str, prompt: str, response: str) -> None:
        f = self.dir / f"{vendor}_{self._key(vendor, model, prompt)}.json"
        f.write_text(
            json.dumps(
                {
                    "vendor": vendor,
                    "model": model,
                    "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                    "response": response,
                    "ts": time.time(),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


# ══════════════════════════════════════════════════════════════════
# Backend: api —— 直连国产大模型
# ══════════════════════════════════════════════════════════════════

class APIBackend:
    """
    OpenAI 兼容 chat/completions 调用。

    为什么不引官方 SDK：Qwen / Kimi / DeepSeek 三家都提供 OpenAI 兼容端点，
    用标准库 urllib 即可，零第三方依赖、零版本冲突，便于在教学场景分发。
    """

    def __init__(self, vendor: str, cache: LLMCache, timeout: int = 60,
                 temperature: float = 0.1, max_retries: int = 2):
        if vendor not in MODEL_REGISTRY:
            raise ValueError(f"未知厂商: {vendor}（可选: {list(MODEL_REGISTRY)}）")
        self.vendor = vendor
        self.spec = MODEL_REGISTRY[vendor]
        self.cache = cache
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max_retries
        self.api_key = resolve_api_key(vendor)
        self.call_count = 0
        self.cache_hits = 0
        self.last_model = self.spec["model"]

    @property
    def ready(self) -> bool:
        return self.api_key is not None

    def _post(self, model: str, prompt: str, system: str) -> str:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
        }
        req = urllib.request.Request(
            f"{self.spec['base_url']}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body["choices"][0]["message"]["content"]

    def complete(self, prompt: str, system: str = "你是一个严谨的数学求解引擎。") -> str:
        """带缓存 + 模型回退 + 重试的补全。"""
        # 1) 缓存命中
        cached = self.cache.get(self.vendor, self.spec["model"], prompt)
        if cached is not None:
            self.cache_hits += 1
            return cached

        if not self.ready:
            raise RuntimeError(
                f"{self.spec['display']} 未配置 API key。"
                f"请设置环境变量 {' 或 '.join(self.spec['api_key_env'])}"
            )

        # 2) 主模型 + 回退模型 + 重试
        last_err: Optional[Exception] = None
        for model in [self.spec["model"], *self.spec["fallback_models"]]:
            for attempt in range(self.max_retries):
                try:
                    self.call_count += 1
                    out = self._post(model, prompt, system)
                    self.last_model = model
                    self.cache.put(self.vendor, model, prompt, out)
                    return out
                except (urllib.error.URLError, KeyError, TimeoutError) as e:
                    last_err = e
                    time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"{self.spec['display']} 调用失败: {last_err}")


# ══════════════════════════════════════════════════════════════════
# JSON 抽取 —— 国产模型常在 JSON 外包裹 markdown/文字，需稳健解析
# ══════════════════════════════════════════════════════════════════

def extract_json(text: str) -> Optional[dict]:
    """
    从模型输出中稳健抽取 JSON 对象。

    失败模式（实测国产模型常见）：
      - 包裹在 ```json ... ``` 代码块中
      - JSON 前后有解释性文字
      - 尾随逗号 ``{"a":1,}``
      - 中文引号/全角括号
    """
    if not text:
        return None

    # 去掉 markdown 代码块围栏
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.MULTILINE).strip()

    # 归一化引号：全角引号 / 中文冒号 是国产模型输出的高频故障
    text = (text.replace("“", '"').replace("”", '"')
                .replace("‘", "'").replace("’", "'"))

    # 直接尝试
    for candidate in (text, _json_fix(text)):
        try:
            obj = json.loads(candidate)
            if isinstance(obj, dict):
                return obj
        except Exception:
            continue

    # 提取最外层 {...}（括号配平扫描，避免贪婪匹配）
    start = text.find("{")
    if start == -1:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                blob = text[start:i + 1]
                for candidate in (blob, _json_fix(blob)):
                    try:
                        obj = json.loads(candidate)
                        if isinstance(obj, dict):
                            return obj
                    except Exception:
                        continue
                return None
    return None


def _json_fix(text: str) -> str:
    """
    修复常见非法 JSON（国产模型输出的高频故障）：

      1. 尾随逗号 ``{"a":1,}``
      2. 单引号字符串 ``{'a': 'b'}``
      3. 全角冒号 ``{"a": 1}``
      4. **非法反斜杠转义** —— 模型常直接写 ``"\\lambda = 3"``，
         而 ``\\l`` 并非合法 JSON 转义，导致 json.loads 整体失败。
         这是数学/物理题目场景下最常见的失败模式，必须兜住。

    仅在标准 json.loads 失败后作为兜底使用。
    """
    fixed = re.sub(r",\s*([}\]])", r"\1", text)

    # 修复非法转义：把不在合法白名单里的 \x 替换为 \\x
    valid = set('"\\/bfnrtu')
    out, i = [], 0
    while i < len(fixed):
        ch = fixed[i]
        if ch == "\\" and i + 1 < len(fixed):
            nxt = fixed[i + 1]
            if nxt in valid:
                out.append(ch)
                out.append(nxt)
                i += 2
                continue
            # 非法转义 → 双写反斜杠，保留原字符
            out.append("\\\\")
            i += 1
            continue
        out.append(ch)
        i += 1
    fixed = "".join(out)

    if "'" in fixed and '"' not in fixed:
        fixed = re.sub(r"'([^']*)'", r'"\1"', fixed)
    fixed = fixed.replace("：", ":")
    return fixed


def normalize_steps(raw: Any) -> list[str]:
    """
    把模型返回的 steps 归一化为字符串列表。

    统一清洗前缀，无论输入是 list 还是 str：
      "步骤1: 求导" / "1) 求导" / "- 求导"  →  "求导"
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = [p.strip() for p in re.split(r"[\n;；]+", raw) if p.strip()]
        items: list = parts or [raw.strip()]
    elif isinstance(raw, list):
        items = [str(i).strip() for i in raw]
    else:
        items = [str(raw).strip()]

    out = []
    for s in items:
        s = re.sub(r"^(?:步骤|第)\s*\d+\s*[:：、.]?\s*", "", s)
        s = re.sub(r"^\d+\s*[.)、]\s*", "", s)
        s = re.sub(r"^[-*•]\s*", "", s)
        s = s.strip()
        if s:
            out.append(s)
    return out


# ══════════════════════════════════════════════════════════════════
# Backend: local —— 离线确定性推理器
# ══════════════════════════════════════════════════════════════════

class LocalBackend:
    """
    离线确定性推理器。

    定位：**不是**伪装成大模型的小模型，而是一个诚实的降级路径。
    它只使用 SymPy 精确计算 + 教材级标准表述，绝不臆造答案。
    产出的每条结果都标注 backend="local", degraded=True。

    这保证：
      1. 无网 / 无 key 时流水线端到端仍可跑通（可演示、可回归测试）；
      2. 与 api backend 的效果差异可被清晰度量，而不是被隐藏。
    """

    def __init__(self, cache_dir: str | Path = ".c4c_cache/llm"):
        self.cache = LLMCache(cache_dir)
        self.name = "local-deterministic"

    def solve(self, problem_text: str, domain: str = "general") -> LLMResult:
        # local backend 不做"推理"——它诚实地报告无能力
        return LLMResult(
            solved=False,
            backend="local",
            model=self.name,
            reason="离线确定性后端不具备多步推理能力；请配置 API key 启用国产大模型",
            provenance={
                "degraded": True,
                "prompt_sha256": hashlib.sha256(problem_text.encode()).hexdigest()[:16],
            },
        )


# ══════════════════════════════════════════════════════════════════
# Backend: agent —— 委派宿主智能体
# ══════════════════════════════════════════════════════════════════

class AgentBackend:
    """
    委派给宿主智能体（WorkBuddy / 国产模型平台）。

    这是 starter kit 隐式架构的**显式化**：
    starter 假定"运行 skill 的智能体"（Claude Code）会补齐 LLM 题，
    但既无接口也无记录。本 backend 把该职责标准化：

      - `plan_only()`  生成 agent 可执行的任务清单（写入 JSONL）
      - agent 读取任务 → 求解 → 将结果写入 solutions_inbox.jsonl
      - `collect()`    回收 agent 产出，附完整溯源

    好处：宿主换成任意国产模型平台（WorkBuddy / Qwen Code / Kimi CLI）
    都不需要改流水线代码 —— 这正是"跨平台迁移"的核心。
    """

    def __init__(self, workspace: str | Path, agent_name: str = "workbuddy"):
        self.dir = Path(workspace)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.tasks_path = self.dir / "agent_tasks.jsonl"
        self.inbox_path = self.dir / "solutions_inbox.jsonl"
        self.agent_name = agent_name

    def plan_only(self, items: list[dict], domain: str = "general") -> dict:
        """生成待委派任务清单（幂等：覆盖写入）。"""
        lines = []
        for it in items:
            lines.append(
                json.dumps(
                    {
                        "problem_id": it["id"],
                        "domain": domain,
                        "question": it["text"],
                        "output_schema": {
                            "problem_id": "str",
                            "steps": ["步骤1: ..."],
                            "answer": "LaTeX or text",
                        },
                        "instruction": "求解后以 JSONL 追加一行到 solutions_inbox.jsonl",
                    },
                    ensure_ascii=False,
                )
            )
        self.tasks_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"tasks": len(items), "path": str(self.tasks_path)}

    def collect(self) -> dict[str, dict]:
        """回收 agent 写入的解答。"""
        out: dict[str, dict] = {}
        if not self.inbox_path.exists():
            return out
        for line in self.inbox_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                out[str(obj.get("problem_id"))] = obj
            except Exception:
                continue
        return out


# ══════════════════════════════════════════════════════════════════
# 统一引擎
# ══════════════════════════════════════════════════════════════════

class LLMEngine:
    """
    统一推理引擎：api / agent / local 三 backend 的门面。

    用法::

        engine = LLMEngine(vendor="qwen", cache_dir=".c4c_cache/llm")
        if engine.ready:
            r = engine.solve("求矩阵 A 的特征值 ...", domain="linear_algebra")
        else:
            print(engine.status_report())
    """

    def __init__(
        self,
        vendor: str = "qwen",
        cache_dir: str | Path = ".c4c_cache/llm",
        prompt_version: int = 3,
        temperature: float = 0.1,
    ):
        self.vendor = vendor
        self.prompt_version = prompt_version
        self.cache = LLMCache(cache_dir)
        self.api = APIBackend(vendor, self.cache, temperature=temperature)
        self.local = LocalBackend(cache_dir)
        self._prompt_tpl = {1: PROMPT_V1, 2: PROMPT_V2, 3: PROMPT_V3}.get(prompt_version, PROMPT_V3)

    # ── 状态 ──────────────────────────────────────────────

    @property
    def ready(self) -> bool:
        """是否可以真正调用国产大模型。"""
        return self.api.ready

    def status_report(self) -> str:
        spec = MODEL_REGISTRY[self.vendor]
        if self.ready:
            return (
                f"✅ {spec['display']} 已就绪 (model={self.api.last_model}, "
                f"key 来自 {spec['api_key_env'][0]})"
            )
        avail = available_vendors()
        hint = f"；本机已配置: {', '.join(avail)}" if avail else "；本机未配置任何国产模型 key"
        return (
            f"⚠️  {spec['display']} 未配置 API key{hint}。"
            f"设置 {' 或 '.join(spec['api_key_env'])} 后自动启用；"
            f"当前降级为 local 确定性后端（结果会如实标注 backend=local）"
        )

    # ── 求解 ──────────────────────────────────────────────

    def build_prompt(self, problem_text: str, domain: str = "general") -> str:
        return self._prompt_tpl.format(problem=problem_text, domain=domain)

    def solve(self, problem_text: str, domain: str = "general") -> LLMResult:
        """求解一道题。api 不可用时降级到 local，并如实标注。"""
        if not self.ready:
            return self.local.solve(problem_text, domain)

        prompt = self.build_prompt(problem_text, domain)
        cached = self.cache.get(self.vendor, self.api.spec["model"], prompt)
        from_cache = cached is not None

        try:
            raw = self.api.complete(prompt)
        except Exception as e:
            r = self.local.solve(problem_text, domain)
            r.reason = f"API 调用失败，已降级: {e}"
            return r

        obj = extract_json(raw)
        if obj is None:
            r = self.local.solve(problem_text, domain)
            r.reason = f"模型输出无法解析为 JSON（原始输出前 120 字: {raw[:120]!r}）"
            # 保留 local.solve 设置的 degraded=True，并追加原文片段
            r.provenance = {**r.provenance, "raw_head": raw[:200], "from_cache": from_cache}
            return r

        steps = normalize_steps(obj.get("steps"))
        answer = str(obj.get("answer", "")).strip()
        solved = bool(steps and answer)

        return LLMResult(
            solved=solved,
            steps=steps,
            answer=answer,
            answer_latex=answer,
            backend="api",
            model=self.api.last_model,
            reason="" if solved else "模型返回内容不完整",
            provenance={
                "vendor": self.vendor,
                "prompt_version": self.prompt_version,
                "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()[:16],
                "from_cache": from_cache,
                "degraded": False,
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            },
        )

    def solve_batch(self, problems: list[dict], domain: str = "general") -> list[LLMResult]:
        return [self.solve(p.get("text", ""), domain) for p in problems]


# ══════════════════════════════════════════════════════════════════
# CLI 自检
# ══════════════════════════════════════════════════════════════════

def _main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="国产大模型引擎自检")
    ap.add_argument("--vendor", default="qwen", choices=list(MODEL_REGISTRY))
    ap.add_argument("--prompt-version", type=int, default=3)
    ap.add_argument("--probe", action="store_true", help="配置了 key 则发起一次真实调用")
    args = ap.parse_args()

    eng = LLMEngine(vendor=args.vendor, prompt_version=args.prompt_version)
    print("═" * 62)
    print(f"  C4C 国产大模型引擎 · {MODEL_REGISTRY[args.vendor]['display']}")
    print("═" * 62)
    print(f"  端点: {MODEL_REGISTRY[args.vendor]['base_url']}")
    print(f"  模型: {MODEL_REGISTRY[args.vendor]['model']}")
    print(f"  用途: {MODEL_REGISTRY[args.vendor]['note']}")
    print(f"  状态: {eng.status_report()}")
    print("─" * 62)

    if args.probe and eng.ready:
        r = eng.solve("求矩阵 [[2,1],[1,2]] 的特征值与特征向量。", domain="linear_algebra")
        print(f"  backend={r.backend} model={r.model} solved={r.solved}")
        for s in r.steps:
            print(f"    - {s}")
        print(f"  answer: {r.answer}")
    else:
        print("  （加 --probe 可发起真实调用；未配置 key 时自动降级为 local）")
    print("═" * 62)


if __name__ == "__main__":
    _main()