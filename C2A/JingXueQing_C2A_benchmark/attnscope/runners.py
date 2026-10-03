"""AttnScope · 模型接入层

两个 Runner：
  MockRunner              —— 离线冒烟测试用。模拟一个「资源受限的注意力系统」：
                             正确率随负荷上升而下降，且部分错误是「被最相似诱饵捕获」。
                             用于验证评分管线是否跑得通，**不产生任何科学结论**。
  OpenAICompatibleRunner  —— 任何 OpenAI 兼容的 /v1/chat/completions 端点；
                             通过 base_url 切换 OpenAI / Anthropic 网关 / vLLM / 本地模型。
"""

from __future__ import annotations

import json
import math
import os
import random
from typing import Optional, Protocol


class Runner(Protocol):
    def complete(self, prompt: str) -> str: ...


class MockRunner:
    """离线基线模型：可参数化的「注意力效率」模拟。

    Args:
        base_acc:      N=4 零干扰基线正确率
        slope_factor:  负荷每翻一倍，正确率下降多少（越大 = 越容易被干扰压垮）
        lure_bias:     出错时「被最相似诱饵捕获」的概率
    """

    def __init__(self, seed: int = 7, base_acc: float = 0.95,
                 slope_factor: float = 0.06, lure_bias: float = 0.6,
                 condition_penalty: float = 0.25):
        self.rng = random.Random(seed)
        self.base_acc = base_acc
        self.slope_factor = slope_factor
        self.lure_bias = lure_bias
        self.condition_penalty = condition_penalty
        self._state: dict = {}

    def set_context(self, **kw) -> None:
        """注入当前题目的上下文（condition / load_n / gold / lure）。"""
        self._state = kw

    def complete(self, prompt: str) -> str:
        st = self._state
        load_n = int(st.get("load_n", 4))
        cond = st.get("condition", "feature")
        gold = st.get("gold", "AB-0000")
        lure = st.get("lure", "")

        steps = math.log2(max(load_n, 1)) - 2           # N=4 时为 0
        pen = self.condition_penalty if cond == "conjunction" else 0.0
        acc = max(0.0, min(1.0, self.base_acc
                           - self.slope_factor * steps
                           - pen * float(st.get("similarity", 0.5))))

        if self.rng.random() < acc:
            return gold
        if lure and self.rng.random() < self.lure_bias:
            return lure
        return "ZZ-9999"


class OpenAICompatibleRunner:
    """OpenAI 兼容端点。

    用法示例：
        OpenAICompatibleRunner(model="gpt-4o-mini")                     # OpenAI
        OpenAICompatibleRunner(model="claude-...", base_url=".../v1")   # 兼容网关
        OpenAICompatibleRunner(model="qwen/...", base_url="http://localhost:8000/v1")
    """

    def __init__(self, model: str, base_url: Optional[str] = None,
                 api_key: Optional[str] = None, temperature: float = 0.0,
                 max_retries: int = 3):
        try:
            from openai import OpenAI
        except ImportError as e:  # pragma: no cover
            raise ImportError("需要 openai 包：pip install openai") from e
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self._client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url or os.environ.get("OPENAI_BASE_URL"),
        )

    def complete(self, prompt: str) -> str:
        last = None
        for _ in range(self.max_retries):
            try:
                r = self._client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                )
                return (r.choices[0].message.content or "").strip()
            except Exception as exc:  # noqa: BLE001
                last = exc
        raise RuntimeError(f"调用失败：{last}")


def load_results_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(obj, path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
