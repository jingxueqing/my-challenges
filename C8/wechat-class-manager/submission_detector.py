#!/usr/bin/env python3
"""submission_detector.py —— L2 提交检测器（独立可跑）

    python submission_detector.py --input out/linked.jsonl --fs ~/Desktop/挑战的产物 --owner JingXueQing
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wcm.bridge import read_jsonl  # noqa: E402
from wcm.bridge.fs_scan import scan  # noqa: E402
from wcm.config import load_config, project_path  # noqa: E402
from wcm.submissions import build  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="从消息 + 磁盘文件构建提交矩阵")
    p.add_argument("--input", "-i", default=project_path("out", "linked.jsonl"))
    p.add_argument("--output", "-o", default=project_path("out", "submissions.json"))
    p.add_argument("--fs", default=None, help="额外扫描的提交包目录")
    p.add_argument("--owner", default=None, help="无姓名文件归属给谁")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    cfg = load_config()
    rows = read_jsonl(args.input)
    fs = []
    if args.fs:
        owner = None
        if args.owner:
            st = cfg.roster.resolve(args.owner)
            owner = st.wxid if st else args.owner
        fs = scan(args.fs, cfg, student_hint=owner)
    res = build(rows, cfg, fs)
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(res, fh, ensure_ascii=False, indent=2)

    if not args.quiet:
        print(f"提交 {res['submission_count']} 项 · 完整 {res['complete_count']} · 缺件 {res['needs_revision_count']} · 文件 {res['artifact_count']}")
        print(f"{'同学':<8}{'挑战':<6}{'状态':<16}缺什么")
        for r in res["rows"]:
            print(f"{r['nickname']:<8}{r['challenge']:<6}{r['status']:<16}{','.join(r['missing']) or '—'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
