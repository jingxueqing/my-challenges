#!/usr/bin/env python3
"""qa_extractor.py —— L2/L3 Q&A 抽取器（独立可跑）

    python qa_extractor.py --input out/linked.jsonl --output out/qa.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wcm.bridge import read_jsonl  # noqa: E402
from wcm.config import load_config, project_path  # noqa: E402
from wcm.qa import extract  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="抽取问答对，做成课程 FAQ 原料")
    p.add_argument("--input", "-i", default=project_path("out", "linked.jsonl"))
    p.add_argument("--output", "-o", default=project_path("out", "qa.json"))
    p.add_argument("--min-quality", type=float, default=None)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    cfg = load_config()
    rows = read_jsonl(args.input)
    res = extract(rows, cfg, args.min_quality)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)
    if not args.quiet:
        print(f"问题 {res['total_questions']} · 答出 {res['answered']} · 入库 {res['kept']} · 均分 {res['avg_quality']}")
        for pair in res["top_pairs"]:
            print(f"  [{pair['quality_score']}] {pair['question'][:50]} → {pair['answerer']['nickname']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
