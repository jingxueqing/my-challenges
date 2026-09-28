#!/usr/bin/env python3
"""check_quality.py — 覆盖度 + 术语一致性 + 机器感抽查。

用法:
    python check_quality.py --src corpus/en --dst course-zh --glossary pipeline/glossary.csv --out reports/quality_report.json

产出:
    - 覆盖度：已译篇数 / 应译篇数、字符比（中文/英文，健康区间 0.5~1.4）
    - 术语一致性：扫描译文中英文术语的"漏翻"（原文出现术语、译文既无统一译法也无保留原文）
    - 占位/漏译检测：TODO、[未翻译]、过短译文
"""
import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path


def cjk_ratio(text):
    total = len(text)
    cjk = sum(1 for c in text if "CJK" in unicodedata.name(c, ""))
    return cjk / max(total, 1)


def load_glossary(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if row["en"].strip() and row["zh"].strip():
                rows.append((row["en"].strip(), row["zh"].strip()))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--glossary", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    glossary = load_glossary(Path(args.glossary))
    src, dst = Path(args.src), Path(args.dst)
    manifest = json.loads((src / "manifest.json").read_text(encoding="utf-8"))

    issues, entries = [], []
    for m in manifest:
        slug = m.get("slug") or Path(m["file"]).stem
        en_path = src / (slug + ".md")
        zh_path = dst / (slug + ".zh.md")
        entry = {"slug": slug, "url": m.get("url", ""), "translated": zh_path.exists()}
        # 译文 front matter 自声明为 KNOWN_GAP 的，按原文抓取缺口计入（与台账/文字报告同源）
        declared_gap = zh_path.exists() and "KNOWN_GAP" in zh_path.read_text(encoding="utf-8")[:400]
        if not zh_path.exists():
            entry["status"] = "MISSING"
            issues.append(f"[覆盖] {slug} 缺少译文")
        elif declared_gap or not en_path.exists():
            entry["status"] = "GAP"
            issues.append(f"[缺口] {slug} 原文抓取缺口（已按缺口台账处理）")
        else:
            en = en_path.read_text(encoding="utf-8")
            zh = zh_path.read_text(encoding="utf-8")
            if "TODO>" in zh or "[未翻译]" in zh:
                entry["status"] = "PLACEHOLDER"
                issues.append(f"[漏译] {slug} 存在 TODO 占位")
            elif len(zh) < len(en) * 0.15:
                entry["status"] = "TOO_SHORT"
                issues.append(f"[过短] {slug} 译文字符不足原文 15%")
            else:
                entry["status"] = "OK"
            # 术语漏翻检查（只对高信号词，产品名除外）
            bad = []
            for en_t, zh_t in glossary:
                if re.search(r"(?<![A-Za-z])" + re.escape(en_t) + r"(?![A-Za-z])", en):
                    base = zh_t.split("（")[0].split("/")[0].strip()
                    if en_t in zh and base not in zh and not re.search(base, zh):
                        bad.append(en_t)
            if bad:
                entry["term_leaks"] = bad[:10]
                issues.append(f"[术语] {slug} 术语漏统一: {', '.join(bad[:10])}")
            entry["ratio"] = round(len(zh) / max(len(en), 1), 2)
        entries.append(entry)

    done = sum(1 for e in entries if e["translated"] and e["status"] == "OK")
    placeholders = [e for e in entries if e.get("status") == "PLACEHOLDER"]
    total = sum(1 for e in entries)
    coverage = done / max(total, 1)

    report = {
        "total_articles": total,
        "translated_ok": done,
        "placeholder": len(placeholders),
        "coverage_pct": round(coverage * 100, 1),
        "glossary_terms": len(glossary),
        "issues": issues,
        "entries": entries,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[check] 覆盖度: {done}/{total} = {report['coverage_pct']}%")
    print(f"[check] 术语表: {len(glossary)} 条")
    for i in issues:
        print("  -", i)
    if report["coverage_pct"] < 80:
        print("[check] 警告: 覆盖度低于 80% 验收线")
        sys.exit(2)


if __name__ == "__main__":
    main()
