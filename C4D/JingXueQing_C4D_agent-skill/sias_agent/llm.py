"""本地 Ollama 客户端。

职责：
1. 封装 /api/chat 与 /v1/chat/completions（OpenAI 兼容层），证明「没有走云端」。
2. 记录每次调用的真实指标：prompt/eval token 数、耗时、tok/s。
3. 结构化输出：小模型 JSON 不稳，这里做多层修复而不是直接放弃。
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Iterable

from .config import OLLAMA_URL, ModelProfile


class OllamaUnavailable(RuntimeError):
    """本地 Ollama 服务没起来——这是必须暴露给用户的硬失败，不做静默降级。"""


@dataclass
class CallStat:
    """一次本地推理调用的可复核指标。"""

    model: str
    prompt_tokens: int = 0
    eval_tokens: int = 0
    total_ms: int = 0
    load_ms: int = 0

    @property
    def tok_per_s(self) -> float:
        return round(self.eval_tokens / (self.total_ms / 1000), 2) if self.total_ms else 0.0

    @property
    def prefill_tok_per_s(self) -> float:
        # Ollama 把 load+prompt_eval 合并在 total_duration 之前，这里用近似口径。
        return 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "prompt_tokens": self.prompt_tokens,
            "eval_tokens": self.eval_tokens,
            "total_ms": self.total_ms,
            "load_ms": self.load_ms,
            "tok_per_s": self.tok_per_s,
        }


@dataclass
class LLMResponse:
    text: str
    stat: CallStat
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def _post(path: str, payload: dict[str, Any], timeout: int = 600) -> dict[str, Any]:
    req = urllib.request.Request(
        OLLAMA_URL + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except urllib.error.URLError as e:
        raise OllamaUnavailable(
            f"无法连接本地 Ollama ({OLLAMA_URL})：{e.reason}。\n"
            f"请先运行：ollama serve"
        ) from e


class LocalLLM:
    """对本地模型的薄封装。所有生成都必须经过这里，便于统一记录证据。"""

    def __init__(self, profile: ModelProfile) -> None:
        self.profile = profile
        self.stats: list[CallStat] = []

    # ------------------------------------------------------------ 基础对话
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        num_ctx: int | None = None,
        format_: str | dict[str, Any] | None = None,
        images: list[str] | None = None,
    ) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.profile.ollama_tag,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.profile.temperature if temperature is None else temperature,
                "num_ctx": num_ctx or self.profile.num_ctx,
            },
        }
        if tools:
            payload["tools"] = tools
        if format_ is not None:
            # Ollama 原生 structured output：用 JSON schema 约束解码
            payload["format"] = format_
        if images:
            # 多模态：把 base64 图片挂到最后一条 user 消息上。
            # 注意必须重建列表——直接改 dict 不会写回原 messages。
            msgs = [dict(m) for m in messages]
            attached = False
            for m in reversed(msgs):
                if m.get("role") == "user":
                    m["images"] = list(images)
                    attached = True
                    break
            if not attached:
                msgs.append({"role": "user", "content": "请描述这张图片。",
                             "images": list(images)})
            payload["messages"] = msgs

        t0 = time.perf_counter()
        data = _post("/api/chat", payload)
        wall_ms = int((time.perf_counter() - t0) * 1000)

        msg = data.get("message", {}) or {}
        stat = CallStat(
            model=self.profile.ollama_tag,
            prompt_tokens=int(data.get("prompt_eval_count") or 0),
            eval_tokens=int(data.get("eval_count") or 0),
            total_ms=int(data.get("total_duration", 0) / 1e6) or wall_ms,
            load_ms=int(data.get("load_duration", 0) / 1e6),
        )
        self.stats.append(stat)

        return LLMResponse(
            text=(msg.get("content") or "").strip(),
            stat=stat,
            tool_calls=msg.get("tool_calls") or [],
            raw=data,
        )

    # ------------------------------------------------------------ 结构化输出
    def json_chat(
        self,
        messages: list[dict[str, Any]],
        schema: dict[str, Any],
        *,
        temperature: float | None = None,
        max_retry: int = 2,
        images: list[str] | None = None,
    ) -> Any:
        """要求返回符合 schema 的 JSON。

        小模型（2B）在长 prompt 下容易漏字段/加解释，因此：
        第一次用 Ollama 原生 schema 约束；失败则退回纯文本 + 自愈修复。
        """
        last_err: Exception | None = None
        msgs = list(messages)
        for attempt in range(max_retry + 1):
            try:
                use_schema = attempt == 0
                resp = self.chat(
                    msgs,
                    temperature=temperature,
                    format_=schema if use_schema else None,
                    images=images if attempt == 0 else None,
                )
                return _extract_json(resp.text)
            except Exception as e:  # noqa: BLE001 - 逐轮降级，不吞异常
                last_err = e
                msgs = msgs + [
                    {"role": "assistant", "content": ""},
                    {
                        "role": "user",
                        "content": (
                            "上一次输出不是合法 JSON（错误：" + str(e)[:160] + "）。"
                            "现在只输出一个 JSON 对象，不要任何解释文字、不要 markdown 代码块标记。"
                            "必须严格符合这个结构：" + json.dumps(schema, ensure_ascii=False)[:900]
                        ),
                    },
                ]
                images = None  # 重试时不再重复携带图片，省显存/带宽
        raise RuntimeError(f"结构化输出在{max_retry + 1} 轮内失败：{last_err}")

    # ------------------------------------------------------------ 证据
    def perf_summary(self) -> dict[str, Any]:
        if not self.stats:
            return {"calls": 0}
        tot_eval = sum(s.eval_tokens for s in self.stats)
        tot_ms = sum(s.total_ms for s in self.stats)
        return {
            "calls": len(self.stats),
            "total_eval_tokens": tot_eval,
            "total_ms": tot_ms,
            "mean_tok_per_s": round(tot_eval / (tot_ms / 1000), 2) if tot_ms else 0.0,
            "per_call": [s.as_dict() for s in self.stats],
        }


# ---------------------------------------------------------------- JSON 修复
_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def _extract_json(text: str) -> Any:
    """从模型输出里挖出 JSON。分层兜底，任何一层成功即返回。"""
    if not text or not text.strip():
        raise ValueError("模型返回空字符串")
    s = text.strip()

    # 1) 直接解析
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    # 2) 去掉 markdown 代码块
    m = _FENCE.search(s)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            s = m.group(1).strip()

    # 3) 截取第一个 { 或 [ 到最后一个配对括号
    for opener, closer in (("{", "}"), ("[", "]")):
        i, j = s.find(opener), s.rfind(closer)
        if i != -1 and j > i:
            frag = s[i : j + 1]
            try:
                return json.loads(frag)
            except json.JSONDecodeError:
                fixed = _repair(frag)
                if fixed is not None:
                    return fixed
    fixed = _repair(s)
    if fixed is not None:
        return fixed
    raise ValueError(f"无法从输出中解析 JSON：{text[:200]}")


def _repair(frag: str) -> Any | None:
    """针对小模型的常见畸形 JSON 做外科手术式修复。"""
    t = frag
    # 单引号 -> 双引号（仅当整段不含双引号时，避免破坏正常字符串）
    if '"' not in t and "'" in t:
        t = t.replace("'", '"')
    # 去掉尾逗号
    t = re.sub(r",\s*([}\]])", r"\1", t)
    # Python 字面量 -> JSON
    t = re.sub(r"\bNone\b", "null", t)
    t = re.sub(r"\bTrue\b", "true", t)
    t = re.sub(r"\bFalse\b", "false", t)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return None


def iter_messages(turns: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """过滤掉空 content 的 tool 消息，避免部分后端报错。"""
    out = []
    for t in turns:
        c = t.get("content")
        if c is None or (isinstance(c, str) and not c.strip()):
            continue
        out.append(t)
    return out
