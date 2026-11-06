#!/usr/bin/env python3
"""Audit a challenge deliverable folder against the challenge's own rules.

Reads `challenge.yaml` (or `challenge.json`) from the challenge pack, then
checks the deliverable folder for required files, naming convention, and
empty artifacts. Prints a markdown report to stdout and exits 0 when every
check passes, 1 when something is missing.

Stdlib only — no third-party dependency.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
from pathlib import Path


def read_challenge(pack: Path) -> dict:
    """Minimal YAML/JSON reader for the few fields we need."""
    meta: dict = {"id": "", "pattern": "", "deadline": ""}
    yfile = pack / "challenge.yaml"
    jfile = pack / "challenge.json"
    text = ""
    if yfile.is_file():
        text = yfile.read_text(encoding="utf-8", errors="replace")
        for key, field in (("id", "id"), ("deliverables_pattern", "pattern"), ("deadline", "deadline")):
            m = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
            if m:
                meta[field] = m.group(1).strip().strip('"').strip("'")
        meta["source"] = str(yfile)
    elif jfile.is_file():
        data = json.loads(jfile.read_text(encoding="utf-8"))
        meta["id"] = str(data.get("challenge_id") or data.get("id") or "")
        meta["pattern"] = str(data.get("deliverables_pattern") or "")
        meta["deadline"] = str(data.get("deadline") or "")
        meta["source"] = str(jfile)
    else:
        meta["source"] = "(none — rules taken from CLI flags only)"
    return meta


def walk_files(root: Path) -> list[Path]:
    out: list[Path] = []
    for p in sorted(root.rglob("*")):
        if p.is_file() and not p.name.startswith("."):
            out.append(p)
    return out


def check_naming(rel: str, name: str, challenge_id: str) -> tuple[bool, str]:
    """Deliverable convention: <Name>_<CHALLENGE_ID>_<description>.<ext>."""
    base = Path(rel).name
    if base.upper().startswith("README") or base.upper() in {"LICENSE"}:
        return True, "README/说明类文件豁免"
    parts = base.split("_")
    problems = []
    if parts[0] != name and not base.startswith(name):
        problems.append(f"前缀应为 {name}")
    if len(parts) > 1 and parts[1] != challenge_id:
        problems.append(f"第二段应为 {challenge_id}")
    if len(parts) < 3:
        problems.append("缺少描述段")
    return (not problems), "；".join(problems) if problems else "命名合规"


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit challenge deliverables.")
    ap.add_argument("deliver_dir", help="交付物目录")
    ap.add_argument("--pack", help="挑战资料包目录（含 challenge.yaml）", default=None)
    ap.add_argument("--name", required=True, help="姓名拼音，如 JingXueQing")
    ap.add_argument("--challenge-id", default=None, help="挑战 ID，如 C10H")
    ap.add_argument("--required", nargs="*", default=None,
                    help="覆盖默认必备文件模式，如 '*AI日志*' '*安装记录*'")
    args = ap.parse_args()

    root = Path(args.deliver_dir).expanduser().resolve()
    if not root.is_dir():
        print(f"✗ 目录不存在：{root}")
        return 1

    meta = {"id": "", "pattern": "", "deadline": "", "source": "(none)"}
    if args.pack:
        meta = read_challenge(Path(args.pack).expanduser())

    cid = args.challenge_id or meta["id"]
    patterns = args.required or [p for p in meta["pattern"].split(",") if p.strip()]
    if not patterns:
        patterns = ["*AI日志*", "*安装记录*", "*配置说明*"]
    if not cid:
        print("✗ 无法确定挑战 ID：请传 --challenge-id 或在 --pack 里提供 challenge.yaml")
        return 1

    files = walk_files(root)
    rels = [str(p.relative_to(root)) for p in files]
    rows: list[tuple[str, str]] = []
    failures = 0

    # A deliverable can be a file or a whole directory (e.g. "*demo*").
    dirs = [p.name for p in sorted(root.rglob("*")) if p.is_dir()]
    names = rels + dirs

    # Check 1 — required deliverables present
    for pat in patterns:
        pat = pat.strip()
        hits = [n for n in names if fnmatch.fnmatch(Path(n).name, pat)]
        ok = bool(hits)
        failures += 0 if ok else 1
        detail = ", ".join(hits[:3]) + (f" 等 {len(hits)} 个" if len(hits) > 3 else "") if hits else "缺失"
        rows.append((f"必备文件 `{pat}`", ("✓ " if ok else "✗ ") + detail))

    # Check 2 — naming convention, top-level deliverables only. Files nested in
    # a deliverable folder (skill bundles, evidence transcripts) keep their own
    # canonical names and are exempt.
    bad_naming = []
    for r in rels:
        if "/" in r:
            continue
        ok, why = check_naming(r, args.name, cid)
        if not ok:
            bad_naming.append(f"{r}（{why}）")
    failures += 0 if not bad_naming else 1
    rows.append(("命名规范 <Name>_<ID>_<描述>",
                 "✓ 全部合规" if not bad_naming else "✗ " + "；".join(bad_naming[:5])))

    # Check 3 — empty files
    empty = [r for r, p in zip(rels, files) if p.stat().st_size == 0]
    failures += 0 if not empty else 1
    rows.append(("空文件检查", "✓ 无空文件" if not empty else "✗ " + ", ".join(empty)))

    # Check 4 — AI log must be non-trivial (red flag in rubric)
    ai = [p for p in files if "AI日志" in p.name]
    ai_ok = bool(ai) and max((p.stat().st_size for p in ai), default=0) > 500
    failures += 0 if ai_ok else 1
    rows.append(("AI 日志非空且 >500 字节",
                 "✓ " + f"{max(p.stat().st_size for p in ai)} 字节" if ai_ok else "✗ 缺失或过短"))

    total = sum(p.stat().st_size for p in files)
    print(f"# 交付物自检报告：{root.name}\n")
    print(f"- 规则来源：`{meta['source']}`")
    print(f"- 挑战 ID：{cid}｜截止：{meta['deadline'] or '未标注'}")
    print(f"- 文件数：{len(files)}｜总体积：{total / 1024:.1f} KB\n")
    print("| 检查项 | 结果 |")
    print("|---|---|")
    for k, v in rows:
        print(f"| {k} | {v} |")
    print()
    if failures:
        print(f"**结论：{failures} 项未通过。**")
        return 1
    print("**结论：全部通过。**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
