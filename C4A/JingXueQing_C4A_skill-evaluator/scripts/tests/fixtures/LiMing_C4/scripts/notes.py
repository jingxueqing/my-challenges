#!/usr/bin/env python3
"""会议纪要生成器。"""
import argparse
import re
from pathlib import Path

TODO_RE = re.compile(r"(需要|待办|action\s*item)", re.IGNORECASE)


def split_speaker(line: str):
    if "：" in line:
        who, _, said = line.partition("：")
        return who.strip(), said.strip()
    return None, line.strip()


def build(transcript: str) -> str:
    topics, todos = [], []
    for line in transcript.splitlines():
        who, said = split_speaker(line)
        if not said:
            continue
        if TODO_RE.search(said):
            todos.append(f"- [ ] {said}")
        else:
            topics.append(f"- {who or '未知'}：{said}")
    out = ["## 议题"] + (topics or ["- （无）"]) + ["", "## 结论", "- 见议题", "", "## 待办"]
    out += todos or ["- （无）"]
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="会议纪要生成器")
    ap.add_argument("input", help="转写文本 .txt 路径")
    ap.add_argument("-o", "--output", default="summary.md")
    a = ap.parse_args()
    text = Path(a.input).read_text(encoding="utf-8")
    Path(a.output).write_text(build(text), encoding="utf-8")
    print(f"已生成 {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
