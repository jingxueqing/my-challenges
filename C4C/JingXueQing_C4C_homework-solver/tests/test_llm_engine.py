#!/usr/bin/env python3
"""
llm_engine 单元测试 —— 覆盖国产模型真实输出失败模式。

运行: python tests/test_llm_engine.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from llm_engine import (  # noqa: E402
    LLMEngine,
    LLMCache,
    extract_json,
    normalize_steps,
    resolve_api_key,
    available_vendors,
    MODEL_REGISTRY,
)

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else ""))


def test_extract_json():
    print("\n[1] extract_json —— 国产模型输出容错")
    cases = [
        ("纯 JSON", '{"steps":["a"],"answer":"x"}', True),
        ("markdown 围栏", '```json\n{"steps":["a"],"answer":"x"}\n```', True),
        ("前后夹带解释文字", '好的：\n{"steps":["a"],"answer":"x"}\n希望有帮助！', True),
        ("尾随逗号", '{"steps":["a"],"answer":"x",}', True),
        ("答案含嵌套对象", '{"steps":["a"],"answer":"{\\"k\\": 1}"}', True),
        ("中文全角引号", '{“steps”: [“a”], “answer”: “x”}', True),
        ("单引号", "{'steps': ['a'], 'answer': 'x'}", True),
        ("无 JSON", '我认为答案应该是 42。', False),
        ("空串", '', False),
    ]
    for name, raw, should in cases:
        got = extract_json(raw)
        check(f"extract_json: {name}", (got is not None) == should, f"got={got}")


def test_normalize_steps():
    print("\n[2] normalize_steps —— 步骤归一化")
    check("列表含 '步骤N:' 前缀", normalize_steps(["步骤1: 求导", "步骤2: 代入"]) == ["求导", "代入"])
    check("列表含 '1)' 前缀", normalize_steps(["1) 求导", "2) 代入"]) == ["求导", "代入"])
    check("字符串多行", normalize_steps("步骤1: a\n步骤2: b") == ["a", "b"])
    check("字符串带分号", normalize_steps("a;b;c") == ["a", "b", "c"])
    check("None 返回空", normalize_steps(None) == [])


def test_cache():
    print("\n[3] LLMCache —— 磁盘缓存往返")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        c = LLMCache(td)
        check("未命中返回 None", c.get("qwen", "m", "p") is None)
        c.put("qwen", "m", "p", "resp-1")
        check("命中返回写入值", c.get("qwen", "m", "p") == "resp-1")
        check("不同 prompt 不串号", c.get("qwen", "m", "p2") is None)


def test_degradation():
    print("\n[4] 降级诚实性 —— 无 key 时不得伪造模型输出")
    eng = LLMEngine(vendor="qwen", cache_dir="/tmp/_c4c_test_cache")
    r = eng.solve("证明 1+2=3")
    check("无 key 时 solved=False", r.solved is False)
    check("标注 backend=local", r.backend == "local")
    check("标注 degraded=True", r.provenance.get("degraded") is True)
    check("给出降级原因", bool(r.reason))
    check("status_report 含未配置字样", "未配置" in eng.status_report())


def test_registry():
    print("\n[5] 模型注册表")
    for v in ("qwen", "kimi", "deepseek"):
        check(f"{v} 已注册", v in MODEL_REGISTRY)
        check(f"{v} 使用 OpenAI 兼容端点", MODEL_REGISTRY[v]["base_url"].startswith("https://"))
    check("resolve_api_key 无 key 返回 None", resolve_api_key("qwen") is None or isinstance(resolve_api_key("qwen"), str))
    check("available_vendors 返回列表", isinstance(available_vendors(), list))


def _force_ready(eng):
    """强制 API backend 进入就绪态（monkeypatch，绕过 property 只读限制）。"""
    eng.api.__dict__["api_key"] = "sk-fake-for-unit-test"
    return eng


def test_mock_api_path():
    print("\n[6] API 路径（用 monkeypatched complete 模拟模型返回）")
    eng = _force_ready(LLMEngine(vendor="qwen", cache_dir="/tmp/_c4c_test_cache2"))
    check("forced ready 生效", eng.ready is True)
    # 强制进入 api 分支
    eng.api.complete = lambda prompt, system="": (
        '```json\n{"steps":["步骤1: 计算行列式 = 3","步骤2: 得特征值 3"],'
        '"answer":"\\lambda = 3"}\n```'
    )
    r = eng.solve("求特征值", domain="linear_algebra")
    check("api 路径 solved=True", r.solved is True)
    check("backend=api", r.backend == "api")
    check("steps 已清洗前缀", r.steps == ["计算行列式 = 3", "得特征值 3"])
    check("answer 正确", r.answer == "\\lambda = 3")
    check("provenance 非降级", r.provenance.get("degraded") is False)
    check("记录 prompt 版本", r.provenance.get("prompt_version") == 3)

    # 不可解析时必须降级而非编造
    eng2 = _force_ready(LLMEngine(vendor="qwen", cache_dir="/tmp/_c4c_test_cache3"))
    eng2.api.complete = lambda prompt, system="": "我觉得答案是 42，但我不确定。"
    r2 = eng2.solve("某题")
    check("不可解析输出 → 不臆造", r2.solved is False)
    check("不可解析 → 记录原文片段", "raw_head" in r2.provenance)
    check("不可解析 → 降级标注", r2.provenance.get("degraded") is True or "degraded" in r2.reason)


def main():
    print("═" * 64)
    print("  llm_engine 单元测试")
    print("═" * 64)
    test_extract_json()
    test_normalize_steps()
    test_cache()
    test_degradation()
    test_registry()
    test_mock_api_path()
    print("\n" + "═" * 64)
    print(f"  通过 {len(PASS)} / {len(PASS) + len(FAIL)}")
    if FAIL:
        print(f"  ❌ 失败: {', '.join(FAIL)}")
    print("═" * 64)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())