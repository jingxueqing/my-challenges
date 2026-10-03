#!/usr/bin/env python3
"""AttnScope 评测入口（L1 选择性阶梯，v0.1 可运行原型）

用法
----
# 1) 离线冒烟：用 MockRunner 验证管线（不调用任何 API、不产生科学结论）
python run_eval.py --runner mock --items-per-cell 20 --out results/mock_l1.json

# 2) 真实模型（需要一个 OpenAI 兼容端点）
export OPENAI_API_KEY=sk-...
python run_eval.py --runner openai --model gpt-4o-mini --items-per-cell 20 \
                   --out results/gpt4o-mini_l1.json

# 3) 自定义网关 / 本地 vLLM
python run_eval.py --runner openai --model Qwen/Qwen2.5-72B-Instruct \
                   --base-url http://localhost:8000/v1 --out results/qwen_l1.json

输出
----
一个 JSON，含按 (condition × similarity) 分组的 AES 斜率、B70 断点、
诱饵捕获率、分半信度，以及各负荷档的正确率。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from attnscope.ladders import build_l1_suite
from attnscope.runners import MockRunner, OpenAICompatibleRunner, dump_json
from attnscope.scoring import evaluate_l1_response, score_l1


def run_l1(runner, items, verbose: bool = False):
    results = []
    for i, it in enumerate(items):
        if hasattr(runner, "set_context"):
            runner.set_context(condition=it.condition, load_n=it.load_n,
                               similarity=it.similarity, gold=it.gold_id,
                               lure=it.lure_id)
        resp = runner.complete(it.prompt)
        results.append(evaluate_l1_response(it, resp))
        if verbose and (i + 1) % 100 == 0:
            print(f"  ...已完成 {i + 1}/{len(items)}", file=sys.stderr)
    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="AttnScope L1 选择性阶梯评测")
    ap.add_argument("--runner", choices=["mock", "openai"], default="mock")
    ap.add_argument("--model", default=None, help="openai runner 的模型名")
    ap.add_argument("--base-url", default=None, help="OpenAI 兼容端点 base_url")
    ap.add_argument("--seed", type=int, default=20261003)
    ap.add_argument("--items-per-cell", type=int, default=50,
                    help="每个 (条件×相似度×负荷) 格子里的题目数。"
                         "20 时单格标准误约 ±0.09，噪声过大；默认 50。")
    ap.add_argument("--loads", default="4,8,16,32,64")
    ap.add_argument("--similarities", default="0.2,0.5,0.9")
    ap.add_argument("--conditions", default="feature,conjunction")
    ap.add_argument("--out", default="results/l1.json")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    loads = [int(x) for x in args.loads.split(",")]
    sims = [float(x) for x in args.similarities.split(",")]
    conds = [x.strip() for x in args.conditions.split(",")]

    if args.runner == "openai":
        if not args.model:
            ap.error("--runner openai 必须指定 --model")
        runner = OpenAICompatibleRunner(model=args.model, base_url=args.base_url)
    else:
        runner = MockRunner(seed=args.seed)

    items = build_l1_suite(seed=args.seed, loads=loads, similarities=sims,
                           conditions=conds, items_per_cell=args.items_per_cell)
    print(f"题目总数：{len(items)}（{len(conds)} 条件 × {len(sims)} 相似度 "
          f"× {len(loads)} 负荷 × {args.items_per_cell} 题）")

    results = run_l1(runner, items, verbose=args.verbose)
    report = {
        "config": {
            "ladder": "L1-selective",
            "runner": args.runner,
            "model": args.model or f"MockRunner(seed={args.seed})",
            "seed": args.seed,
            "loads": loads, "similarities": sims, "conditions": conds,
            "items_per_cell": args.items_per_cell,
            "note": ("MockRunner 仅用于管线冒烟测试，其数值不代表任何模型，"
                     "也不构成任何科学结论。"),
        },
        "scores": score_l1(results),
    }

    dump_json(report, args.out)
    print(json.dumps(report["scores"], ensure_ascii=False, indent=2))
    print(f"\n结果已写入：{os.path.abspath(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
