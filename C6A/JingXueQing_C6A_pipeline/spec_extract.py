#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""spec_extract.py —— 从官方挑战文档 CHALLENGE.md 自动抽取「必填交付物」规格。

设计口径（写进方案设计）：
1. 唯一的权威来源是 `我的挑战/挑战_<ID> .../CHALLENGE.md` 里的交付物表格/代码块，
   不手写、不猜；抽取不到时才用 `spec_patches.json` 人工补丁，且补丁必须写 reason。
2. 表格行形如  | 方案设计文档 | `姓名_C4A_方案设计.md` | 说明 |
   代码块行形如  姓名_C4D_方案设计.md   ← 说明
3. 行内出现「可选 / 如有 / 建议 / 额外 / Level 3 / Level 4」→ 记为非必填。
4. 输出 specs.json：{challenge_id: {title, source_file, items:[{label, pattern, required, source_line, origin}]}}
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CHALLENGE_ROOT = Path("/Users/jingxueqing/Desktop/我的挑战")
BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "JingXueQing_C6A_数据"

# 交付物文件名里出现的「姓氏占位符」，官方文档里写法不统一
NAME_TOKENS = r"(?:姓名|组名|你的名字|名字|YourName|yourname|name|Name)"
PATTERN_HINT = re.compile(NAME_TOKENS)
CHALLENGE_TOKEN = re.compile(r"_C\d+[A-Z]?(?:_|\.|$)")
CODE_SPAN = re.compile(r"`([^`]+)`")
LEADING_LINENO = re.compile(r"^(?:\d+\|)+")

OPTIONAL_MARKERS = ("可选", "如有", "建议", "额外", "加分", "Level 3", "Level 4", "（选做）", "(选做)")


def clean_line(line: str) -> str:
    """去掉导出时混进来的 `NNN|` 行号前缀。"""
    prev = None
    while prev != line:
        prev = line
        line = LEADING_LINENO.sub("", line)
    return line


def challenge_id_from_dir(name: str) -> tuple[str, str] | None:
    m = re.match(r"挑战_(C\d+[A-Z]?)\s*(.*?)_[a-z0-9]{6}_完整资料$", name)
    if not m:
        m2 = re.match(r"挑战_(C\d+[A-Z]?)\s*(.*?)_完整资料$", name)
        if not m2:
            return None
        return m2.group(1), m2.group(2).strip()
    return m.group(1), m.group(2).strip()


def pick_pattern(text: str) -> str | None:
    for span in CODE_SPAN.findall(text):
        if PATTERN_HINT.search(span) and CHALLENGE_TOKEN.search(span):
            return span.strip()
    # 表格里没写反引号的情况：直接找 姓名_xxx
    m = re.search(r"(" + NAME_TOKENS + r"_[A-Za-z0-9]*_C\d+[A-Z]?_[^\s|]+)", text)
    if m:
        return m.group(1).strip()
    return None


def is_optional(line: str, label: str) -> bool:
    blob = line + " " + label
    return any(marker in blob for marker in OPTIONAL_MARKERS)


def label_from_line(line: str, pattern: str) -> str:
    # 代码块：姓名_C6A_方案设计.md   ← 架构、技术选型
    if "←" in line:
        return line.split("←", 1)[1].strip() or "交付物"
    # 表格：取第一列
    if line.strip().startswith("|"):
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells:
            return cells[0].strip("*` ") or "交付物"
    tail = pattern.split("_", 2)[-1]
    return tail


def extract_from_markdown(path: Path) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    in_fence = False
    for idx, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = clean_line(raw)
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not line.strip():
            continue
        compact = line.strip()
        # 只要「像交付列表」的行：表格行 或 代码块行
        looks_like_table = compact.startswith("|")
        looks_like_fence = in_fence
        if not (looks_like_table or looks_like_fence):
            continue
        pattern = pick_pattern(compact)
        if not pattern:
            continue
        key = re.sub(r"\s+", "", pattern)
        if key in seen:
            continue
        seen.add(key)
        label = label_from_line(compact, pattern)
        items.append(
            {
                "label": label[:24],
                "pattern": pattern,
                "required": not is_optional(compact, label),
                "source_line": idx,
                "source_text": compact[:160],
                "origin": "challenge_doc",
            }
        )
    return items


def main() -> int:
    specs: dict[str, dict] = {}
    for folder in sorted(CHALLENGE_ROOT.glob("挑战_*")):
        doc = folder / "CHALLENGE.md"
        if not doc.exists():
            continue
        cid_title = challenge_id_from_dir(folder.name)
        if not cid_title:
            continue
        cid, title = cid_title
        items = extract_from_markdown(doc)
        if not items:
            continue
        specs[cid] = {
            "challenge_id": cid,
            "title": title,
            "source_file": str(doc),
            "items": items,
            "origin": "auto_extracted",
        }
    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "specs_extracted.json").write_text(
        json.dumps(specs, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"抽取到 {len(specs)} 个挑战的规格")
    for cid, spec in specs.items():
        req = sum(1 for i in spec["items"] if i["required"])
        print(f"  {cid:5s} 共 {len(spec['items']):2d} 项 / 必填 {req:2d} 项  — {spec['title'][:28]}")
    missing = sorted(
        cid_title[0]
        for cid_title in (challenge_id_from_dir(p.name) for p in CHALLENGE_ROOT.glob("挑战_*"))
        if cid_title and cid_title[0] not in specs
    )
    if missing:
        print("未能自动抽取（需要人工补丁）：", ", ".join(missing))
    return 0


if __name__ == "__main__":
    sys.exit(main())
