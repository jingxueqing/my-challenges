#!/usr/bin/env python3
"""classifier.py —— L2 消息分类器（可独立运行，也可被 pipeline 调用）

    python classifier.py --input out/messages.jsonl --output out/classified.jsonl
    python classifier.py --input out/messages.jsonl --llm-review     # 低置信度交 LLM 复核

输出每条消息一个 JSON 对象，带 intent / confidence / signals / scores，
signals 就是「凭什么这么判」，方便复核。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wcm.bridge import read_jsonl, write_jsonl  # noqa: E402
from wcm.classifier import classify_batch, evaluate, make_llm_reviewer, summarize_batch  # noqa: E402
from wcm.config import load_config, project_path  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="群消息意图分类")
    p.add_argument("--input", "-i", default=project_path("out", "messages.jsonl"))
    p.add_argument("--output", "-o", default=project_path("out", "classified.jsonl"))
    p.add_argument("--labels", default=project_path("data", "fixtures", "labels.jsonl"))
    p.add_argument("--metrics", default=project_path("out", "metrics.json"))
    p.add_argument("--llm-review", action="store_true")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    cfg = load_config()
    msgs = read_jsonl(args.input)
    reviewer = make_llm_reviewer() if args.llm_review else None
    out = classify_batch(msgs, cfg, llm_review=reviewer)
    write_jsonl(args.output, out)

    summary = summarize_batch(out)
    if not args.quiet:
        print(f"分类 {summary['total']} 条 → {summary['distribution']}")
        print(f"平均置信度 {summary['avg_confidence']}，建议人工复核 {summary['needs_review']} 条")
    if os.path.exists(args.labels):
        metrics = evaluate(out, read_jsonl(args.labels))
        with open(args.metrics, "w", encoding="utf-8") as fh:
            json.dump(metrics, fh, ensure_ascii=False, indent=2)
        if not args.quiet:
            print(f"准确率 {metrics['accuracy']:.1%} / macro-F1 {metrics['macro_f1']} → {args.metrics}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
