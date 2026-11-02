#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""digest.py —— 通知系统：把当前数据压成一页「每日/每周提交状态摘要」，可直接发群。

输出：
  报告/每日摘要_YYYY-MM-DD.md   给老师/助教看的完整版
  报告/群里通知_YYYY-MM-DD.txt   可直接复制到群里的短消息
"""
from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "JingXueQing_C6A_数据"
REPORT = BASE / "JingXueQing_C6A_数据" / "报告"


def main() -> int:
    payload = json.loads((DATA / "submissions.json").read_text(encoding="utf-8"))
    today = date.today().isoformat()
    REPORT.mkdir(parents=True, exist_ok=True)
    records = payload["records"]
    stats = payload["stats"]

    missing_rows = [r for r in records if r["missing"]]
    counter = Counter()
    for r in missing_rows:
        for m in r["missing"]:
            counter[m] += 1

    lines = [
        f"# 提交状态摘要 · {today}",
        "",
        f"> 自动生成，数据源：{len(payload['provenance']['roots'])} 个本机目录 ｜ "
        f"生成时间 {payload['generated_at']}",
        "",
        "## 一、总览",
        "",
        f"- 提交者：{stats['n_students']} 位（{stats['n_packages']} 个提交包，{stats['n_files']} 个文件）",
        f"- 挑战：{stats['n_challenges']} 个（规格来自官方 CHALLENGE.md）",
        f"- 有数据记录：{stats['n_records']} 条，其中必填项全齐 {stats['n_complete']} 条、缺件 {stats['n_partial']} 条",
        f"- 平均完整度：{stats['avg_completeness']:.0%}",
        "",
        "## 二、需要提醒的缺件（按人）",
        "",
    ]
    if missing_rows:
        for r in sorted(missing_rows, key=lambda x: (x["student"], x["challenge_id"])):
            lines.append(f"- **{r['student']} · {r['challenge_id']} {r['challenge_title']}**"
                         f"（完整度 {r['completeness']:.0%}）：缺 {'、'.join(r['missing'])}")
    else:
        lines.append("- 本轮没有缺件。")

    lines += ["", "## 三、最常缺的交付项", ""]
    for label, n in counter.most_common(10):
        lines.append(f"- {label}：{n} 人缺")
    if not counter:
        lines.append("- 无")

    lines += ["", "## 四、系统给出的结论", ""]
    for ins in payload["insights"]:
        lines.append(f"- [{ins['level']}] **{ins['title']}**")
        lines.append(f"  - 证据：{ins['evidence']}")

    lines += ["", "## 五、怎么复核", "",
              "1. 打开 `JingXueQing_C6A_仪表盘/index.html`，点任意格子看该条记录的文件与交付项。",
              "2. 打开 `JingXueQing_C6A_report.xlsx` →「数据来源」页，看口径与已知局限。",
              "3. 原始数据：`JingXueQing_C6A_数据/submissions.json`（记录级）、`files.csv`（文件级）。", ""]
    (REPORT / f"每日摘要_{today}.md").write_text("\n".join(lines), encoding="utf-8")

    # 发群短消息
    head = [f"【Elite 20 提交状态 {today}】",
            f"已收录 {stats['n_students']} 位提交者 / {stats['n_challenges']} 个挑战 / {stats['n_records']} 条记录，"
            f"必填全齐 {stats['n_complete']} 条，缺件 {stats['n_partial']} 条。"]
    if missing_rows:
        head.append("待补：" + "；".join(
            f"{r['student']}-{r['challenge_id']}（{'、'.join(r['missing'])}）" for r in missing_rows[:8]))
        if len(missing_rows) > 8:
            head.append(f"……共 {len(missing_rows)} 条，详见仪表盘「缺失项」页。")
    head.append("仪表盘：双击 JingXueQing_C6A_仪表盘/index.html")
    (REPORT / f"群里通知_{today}.txt").write_text("\n".join(head), encoding="utf-8")

    print(f"[digest] 报告/每日摘要_{today}.md 与 报告/群里通知_{today}.txt 已生成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
