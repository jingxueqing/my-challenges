#!/usr/bin/env python3
"""challenge_linker.py —— L2 挑战关联器（独立可跑）

    python challenge_linker.py --input out/classified.jsonl --output out/linked.jsonl
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wcm.bridge import read_jsonl, write_jsonl  # noqa: E402
from wcm.config import load_config, project_path  # noqa: E402
from wcm.linker import link_messages, link_summary  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="把消息关联到具体挑战")
    p.add_argument("--input", "-i", default=project_path("out", "classified.jsonl"))
    p.add_argument("--output", "-o", default=project_path("out", "linked.jsonl"))
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    cfg = load_config()
    rows = read_jsonl(args.input)
    linked = link_messages(rows, cfg)
    write_jsonl(args.output, linked)
    if not args.quiet:
        print(json.dumps(link_summary(linked), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
