#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""evidence_lint —— 证据链校验器

解决一个具体问题：交付文档里写「见 C4D 日志第 53 行」，
过两天文件改名、行号漂移，这条证据就变成了一句漂亮但无法核对的话。

这个工具把每条引用写成 `[ev:相对路径:L行号]`，然后真的去打开那个文件、翻到那一行、
把原文打印出来。**打不开就报错，退出码 1。**

用法：
  python3 evidence_lint.py ../JingXueQing_C3_参与记录.md --root /Users/jingxueqing/Desktop
  python3 evidence_lint.py *.md --root . --min 5      # 至少 5 条引用才算过

退出码：0 = 全部可核对；1 = 有坏引用/数量不足；2 = 输入错误
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

PATTERN = re.compile(r"\[ev:([^\]\s]+):L(\d+)\]")


@dataclass
class Citation:
    source: Path      # 引用写在哪个文档里
    line_no: int      # 写在文档第几行
    target: str       # 被引用的相对路径
    target_line: int  # 被引用的行号
    ok: bool = False
    quoted: str = ""
    reason: str = ""


def collect(doc: Path) -> List[Citation]:
    out: List[Citation] = []
    try:
        lines = doc.read_text(encoding="utf-8").splitlines()
    except OSError as e:
        print(f"读不到 {doc}：{e}", file=sys.stderr)
        return out
    for i, text in enumerate(lines, 1):
        for m in PATTERN.finditer(text):
            out.append(Citation(source=doc, line_no=i,
                                target=m.group(1), target_line=int(m.group(2))))
    return out


def verify(cit: Citation, root: Path) -> None:
    path = (root / cit.target).expanduser()
    if not path.exists():
        cit.reason = f"文件不存在：{path}"
        return
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as e:
        cit.reason = f"打不开：{e}"
        return
    if cit.target_line < 1 or cit.target_line > len(lines):
        cit.reason = f"行号越界：文件只有 {len(lines)} 行"
        return
    cit.ok = True
    cit.quoted = lines[cit.target_line - 1].strip()[:96]


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="校验 [ev:路径:L行号] 形式的证据引用")
    ap.add_argument("docs", nargs="+", help="待校验的 Markdown 文件")
    ap.add_argument("--root", default=".", help="相对路径的解析根目录")
    ap.add_argument("--min", type=int, default=0, help="要求的最少引用条数")
    ap.add_argument("--quiet", action="store_true", help="只输出结论行")
    args = ap.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    docs = [Path(d) for d in args.docs]
    missing = [d for d in docs if not d.exists()]
    if missing:
        for d in missing:
            print(f"找不到文档：{d}", file=sys.stderr)
        return 2

    cits: List[Citation] = []
    for d in docs:
        cits.extend(collect(d))
    for c in cits:
        verify(c, root)

    bad = [c for c in cits if not c.ok]
    if not args.quiet:
        for c in cits:
            flag = "✅" if c.ok else "❌"
            print(f"{flag} {c.source.name}:{c.line_no}  →  {c.target}:L{c.target_line}")
            print(f"     {c.quoted if c.ok else c.reason}")
        print("─" * 62)

    print(f"引用 {len(cits)} 条｜可核对 {len(cits) - len(bad)}｜坏引用 {len(bad)}｜要求 ≥ {args.min}")
    if bad:
        print("结论：❌ 有证据对不上，别提交。先把上面标 ❌ 的改掉。")
        return 1
    if len(cits) < args.min:
        print(f"结论：❌ 引用条数不足（{len(cits)} < {args.min}）")
        return 1
    print("结论：✅ 每条引用都能打开到具体那一行。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
