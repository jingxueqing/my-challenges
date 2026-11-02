#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_excel.py —— 用 openpyxl 从 submissions.json 生成 Excel 报表（不手填一格）。

Sheet：
  1 总览     学生 × 挑战 矩阵 + 完成率 + 条件格式 + 柱状图
  2 按学生   每个学生一行一条记录，列全展开
  3 按挑战   每个挑战的必填项、提交人数、完成率
  4 时间线   按「提交时间(近似)」倒序
  5 缺失项   只列缺件记录，红底高亮（附一句该补什么）
  6 数据来源 口径、根目录、补丁、坑（评审用来复核）
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "JingXueQing_C6A_数据"
OUT = BASE / "JingXueQing_C6A_report.xlsx"

NAVY = "1F3864"
INK = "1A1A1A"
GREY = "F2F4F7"
OK_FILL = PatternFill("solid", fgColor="E3F4E1")
WARN_FILL = PatternFill("solid", fgColor="FFF2D9")
BAD_FILL = PatternFill("solid", fgColor="FBE0DE")
HEAD_FILL = PatternFill("solid", fgColor=NAVY)
SUB_FILL = PatternFill("solid", fgColor="DCE6F1")
THIN = Side(style="thin", color="D9D9D9")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
STATUS_MARK = {"complete": "✅ 完整", "partial": "⚠️ 缺件", "missing": "❌ 未提交"}
STATUS_FILL = {"complete": OK_FILL, "partial": WARN_FILL, "missing": BAD_FILL}


def style_header(ws, row: int, n_cols: int, height: int = 22) -> None:
    ws.row_dimensions[row].height = height
    for c in range(1, n_cols + 1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HEAD_FILL
        cell.font = Font(bold=True, color="FFFFFF", size=10)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER


def set_widths(ws, widths: dict[str, int]) -> None:
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def title_block(ws, text: str, sub: str, n_cols: int) -> int:
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_cols)
    c = ws.cell(row=1, column=1, value=text)
    c.font = Font(bold=True, size=15, color=NAVY)
    c.alignment = Alignment(vertical="center")
    ws.row_dimensions[1].height = 26
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n_cols)
    c2 = ws.cell(row=2, column=1, value=sub)
    c2.font = Font(size=9, color="666666")
    c2.alignment = Alignment(vertical="center")
    return 3


def sheet_overview(wb: Workbook, payload: dict) -> None:
    ws = wb.create_sheet("总览")
    chals = payload["matrix"]["challenges"]
    n_cols = 4 + len(chals)
    row = title_block(
        ws,
        "Elite 20 提交数据总览",
        f"生成时间 {payload['generated_at']} ｜ {payload['stats']['n_students']} 位提交者 × "
        f"{len(chals)} 个挑战 ｜ 数据源：本机真实提交包（口径见「数据来源」页）",
        n_cols,
    )
    header = ["学生"] + [c["id"] for c in chals] + ["已提交", "完整条数", "平均完整度"]
    for i, h in enumerate(header, 1):
        ws.cell(row=row, column=i, value=h)
    style_header(ws, row, len(header))
    head_row = row
    row += 1

    for m_row in payload["matrix"]["rows"]:
        student = m_row["student"]
        ws.cell(row=row, column=1, value=student).font = Font(bold=True, size=10)
        for j, cell in enumerate(m_row["cells"], 2):
            c = ws.cell(row=row, column=j, value={"complete": "✅", "partial": "⚠️", "missing": "❌"}[cell["status"]])
            c.alignment = Alignment(horizontal="center")
            c.fill = STATUS_FILL[cell["status"]]
            c.border = BORDER
            if cell["submitted_at"]:
                c.comment = None
                c.value = {"complete": "✅", "partial": "⚠️", "missing": "❌"}[cell["status"]]
        recs = [r for r in payload["records"] if r["student"] == student]
        base = len(header) - 2
        ws.cell(row=row, column=base, value=len(recs)).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=base + 1, value=sum(1 for r in recs if r["status"] == "complete")).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=base + 2, value=round(sum(r["completeness"] for r in recs) / max(1, len(recs)), 3)).number_format = "0%"
        row += 1

    set_widths(ws, {"A": 14, "B": 6})
    for i in range(2, len(chals) + 2):
        ws.column_dimensions[get_column_letter(i)].width = 6.5
    for i in range(len(chals) + 2, len(header) + 1):
        ws.column_dimensions[get_column_letter(i)].width = 10
    ws.freeze_panes = ws.cell(row=head_row + 1, column=2)

    # --- 每个挑战的完成率（带柱状图）
    row += 2
    ws.cell(row=row, column=1, value="按挑战的完成率").font = Font(bold=True, size=12, color=NAVY)
    row += 1
    head2 = ["挑战", "标题", "必填项", "提交人数", "完整", "缺件", "平均完整度"]
    for i, h in enumerate(head2, 1):
        ws.cell(row=row, column=i, value=h)
    style_header(ws, row, len(head2))
    chart_start = row + 1
    for c in chals:
        row += 1
        recs = [r for r in payload["records"] if r["challenge_id"] == c["id"]]
        ws.cell(row=row, column=1, value=c["id"]).font = Font(bold=True, size=9)
        ws.cell(row=row, column=2, value=c["title"][:40]).font = Font(size=9)
        ws.cell(row=row, column=3, value=c["n_required"]).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=4, value=len(recs)).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=5, value=sum(1 for r in recs if r["status"] == "complete")).alignment = Alignment(horizontal="center")
        ws.cell(row=row, column=6, value=sum(1 for r in recs if r["status"] == "partial")).alignment = Alignment(horizontal="center")
        avg = round(sum(r["completeness"] for r in recs) / len(recs), 3) if recs else 0
        cc = ws.cell(row=row, column=7, value=avg)
        cc.number_format = "0%"
        cc.fill = OK_FILL if avg >= 0.99 else (WARN_FILL if avg > 0 else BAD_FILL)
    chart_end = row

    chart = BarChart()
    chart.type = "bar"
    chart.title = "各挑战平均完整度"
    chart.y_axis.title = "完整度"
    chart.height, chart.width = 11, 16
    data = Reference(ws, min_col=7, min_row=chart_start - 1, max_row=chart_end)
    cats = Reference(ws, min_col=1, min_row=chart_start, max_row=chart_end)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    ws.add_chart(chart, f"I{chart_start}")

    ws.sheet_view.showGridLines = False


def sheet_by_student(wb: Workbook, payload: dict) -> None:
    ws = wb.create_sheet("按学生")
    head = ["学生", "挑战", "挑战名", "状态", "完整度", "必填项", "已交必填", "缺失项",
            "文件数", "提交时间(近似)", "提交包数", "命名合规", "AI日志", "C4A评审分"]
    row = title_block(ws, "按学生：每位提交者的全部记录", "状态口径：✅ 必填齐全 / ⚠️ 有产出但缺必填 / ❌ 本机无记录", len(head))
    for i, h in enumerate(head, 1):
        ws.cell(row=row, column=i, value=h)
    style_header(ws, row, len(head))
    head_row = row
    for r in sorted(payload["records"], key=lambda x: (x["student"], x["challenge_id"])):
        row += 1
        vals = [r["student"], r["challenge_id"], r["challenge_title"][:36], STATUS_MARK[r["status"]],
                r["completeness"], len(r["items"]), len(r["present_required"]),
                " / ".join(r["missing"]) or "-", r["n_files"], r["submitted_at"][:19].replace("T", " "),
                len(r["packages"]), r["quality"]["naming_compliance"],
                "是" if r["quality"]["ai_log_ok"] else "否",
                (r["review"] or {}).get("composite", "-")]
        for i, v in enumerate(vals, 1):
            c = ws.cell(row=row, column=i, value=v)
            c.border = BORDER
            c.font = Font(size=9)
            if i in (4,):
                c.fill = STATUS_FILL[r["status"]]
            if i in (5, 12):
                c.number_format = "0%"
            if i in (2, 6, 7, 9, 11, 13, 14):
                c.alignment = Alignment(horizontal="center")
        if r["missing"]:
            ws.cell(row=row, column=8).fill = BAD_FILL
    set_widths(ws, {"A": 13, "B": 8, "C": 34, "D": 10, "E": 8, "F": 8, "G": 9, "H": 40,
                    "I": 8, "J": 19, "K": 9, "L": 9, "M": 8, "N": 10})
    ws.freeze_panes = ws.cell(row=head_row + 1, column=2)
    ws.auto_filter.ref = f"A{head_row}:{get_column_letter(len(head))}{row}"
    ws.sheet_view.showGridLines = False


def sheet_by_challenge(wb: Workbook, payload: dict) -> None:
    ws = wb.create_sheet("按挑战")
    head = ["挑战", "标题", "必填项数", "提交人数", "完整", "缺件", "平均完整度", "规格来源", "必填项清单"]
    row = title_block(ws, "按挑战：每个挑战的提交情况", "必填项来自各自 CHALLENGE.md（origin=challenge_doc 为自动抽取，patch 为人工补丁）", len(head))
    for i, h in enumerate(head, 1):
        ws.cell(row=row, column=i, value=h)
    style_header(ws, row, len(head))
    head_row = row
    for c in payload["challenges"]:
        row += 1
        recs = [r for r in payload["records"] if r["challenge_id"] == c["id"]]
        avg = round(sum(r["completeness"] for r in recs) / len(recs), 3) if recs else 0
        vals = [c["id"], c["title"][:38], c["n_required"], len(recs),
                sum(1 for r in recs if r["status"] == "complete"),
                sum(1 for r in recs if r["status"] == "partial"), avg, c["origin"],
                "、".join(i["label"] for i in c["items"] if i["required"])[:120]]
        for i, v in enumerate(vals, 1):
            cell = ws.cell(row=row, column=i, value=v)
            cell.border = BORDER
            cell.font = Font(size=9)
            if i == 7:
                cell.number_format = "0%"
                cell.fill = OK_FILL if avg >= 0.99 else (WARN_FILL if avg > 0 else BAD_FILL)
            if i in (1, 3, 4, 5, 6):
                cell.alignment = Alignment(horizontal="center")
    set_widths(ws, {"A": 8, "B": 34, "C": 9, "D": 9, "E": 7, "F": 7, "G": 10, "H": 20, "I": 70})
    ws.freeze_panes = ws.cell(row=head_row + 1, column=2)
    ws.auto_filter.ref = f"A{head_row}:{get_column_letter(len(head))}{row}"
    ws.sheet_view.showGridLines = False


def sheet_timeline(wb: Workbook, payload: dict) -> None:
    ws = wb.create_sheet("时间线")
    head = ["提交时间(近似)", "学生", "挑战", "挑战名", "状态", "文件数", "缺失项"]
    row = title_block(ws, "时间线：按提交时间倒序", "口径：取提交包内文件的最后修改时间（本地无平台时间戳，属近似值）", len(head))
    for i, h in enumerate(head, 1):
        ws.cell(row=row, column=i, value=h)
    style_header(ws, row, len(head))
    head_row = row
    for r in sorted(payload["records"], key=lambda x: x["submitted_at"], reverse=True):
        row += 1
        vals = [r["submitted_at"][:19].replace("T", " "), r["student"], r["challenge_id"],
                r["challenge_title"][:34], STATUS_MARK[r["status"]], r["n_files"],
                " / ".join(r["missing"]) or "-"]
        for i, v in enumerate(vals, 1):
            c = ws.cell(row=row, column=i, value=v)
            c.border = BORDER
            c.font = Font(size=9)
            if i == 5:
                c.fill = STATUS_FILL[r["status"]]
            if i in (2, 6):
                c.alignment = Alignment(horizontal="center")
    set_widths(ws, {"A": 19, "B": 13, "C": 8, "D": 34, "E": 10, "F": 8, "G": 42})
    ws.freeze_panes = ws.cell(row=head_row + 1, column=1)
    ws.sheet_view.showGridLines = False


def sheet_missing(wb: Workbook, payload: dict) -> None:
    ws = wb.create_sheet("缺失项")
    head = ["学生", "挑战", "缺失的必填项", "已交必填项", "完整度", "建议动作"]
    row = title_block(ws, "缺失项：只列「交了但缺件」的记录（红底）",
                      "❌ 完全无记录的格子不在此页（那不是缺件，是没有数据，见总览矩阵）", len(head))
    for i, h in enumerate(head, 1):
        ws.cell(row=row, column=i, value=h)
    style_header(ws, row, len(head))
    head_row = row
    rows = [r for r in payload["records"] if r["missing"]]
    for r in sorted(rows, key=lambda x: (-x["completeness"], x["student"])):
        row += 1
        hint = f"补 {r['missing'][0]}" if len(r["missing"]) == 1 else f"优先补 {r['missing'][0]}（共缺 {len(r['missing'])} 项）"
        vals = [r["student"], r["challenge_id"], " / ".join(r["missing"]),
                " / ".join(r["present_required"]) or "-", r["completeness"], hint]
        for i, v in enumerate(vals, 1):
            c = ws.cell(row=row, column=i, value=v)
            c.border = BORDER
            c.font = Font(size=9)
            if i == 3:
                c.fill = BAD_FILL
            if i == 5:
                c.number_format = "0%"
            if i in (2,):
                c.alignment = Alignment(horizontal="center")
    # 空表也要说明
    if not rows:
        ws.cell(row=row + 1, column=1, value="本次扫描没有出现「缺件」记录。").font = Font(italic=True, color="666666")
    set_widths(ws, {"A": 13, "B": 8, "C": 46, "D": 40, "E": 9, "F": 30})
    ws.freeze_panes = ws.cell(row=head_row + 1, column=1)
    ws.sheet_view.showGridLines = False


def sheet_source(wb: Workbook, payload: dict) -> None:
    ws = wb.create_sheet("数据来源")
    row = title_block(ws, "数据来源与口径（评审复核用）", "这一页回答：数据从哪来、怎么算的、哪里可能错", 3)
    prov = payload["provenance"]
    blocks: list[tuple[str, list[str]]] = [
        ("数据根目录", [f"{r['label']}：{r['path']}" for r in prov["roots"]]),
        ("挑战规格来源", [f"{cid}：{origin}" for cid, origin in prov["specs_origin"].items()]),
        ("扫描规则", [f"{k}：{v}" for k, v in prov["scan_rules"].items()]),
        ("已知局限（必须写清）", prov["caveats"]),
        ("生成信息", [f"schema {payload['schema_version']}", f"generated_at {payload['generated_at']}",
                      f"记录 {payload['stats']['n_records']} 条 / 文件 {payload['stats']['n_files']} 个",
                      f"生成脚本 make_excel.py（openpyxl）"]),
    ]
    for title, lines in blocks:
        row += 1
        c = ws.cell(row=row, column=1, value=title)
        c.font = Font(bold=True, size=11, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor=NAVY)
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
        for line in lines:
            row += 1
            cell = ws.cell(row=row, column=1, value=line)
            cell.font = Font(size=9)
            cell.alignment = Alignment(wrap_text=True, vertical="top")
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=3)
            ws.row_dimensions[row].height = 26 if len(line) > 60 else 16
    set_widths(ws, {"A": 60, "B": 40, "C": 30})
    ws.sheet_view.showGridLines = False


def main() -> int:
    payload = json.loads((DATA / "submissions.json").read_text(encoding="utf-8"))
    wb = Workbook()
    wb.remove(wb.active)
    sheet_overview(wb, payload)
    sheet_by_student(wb, payload)
    sheet_by_challenge(wb, payload)
    sheet_timeline(wb, payload)
    sheet_missing(wb, payload)
    sheet_source(wb, payload)
    wb.properties.title = "Elite 20 提交数据报表"
    wb.properties.creator = "C6A pipeline (openpyxl)"
    wb.properties.created = datetime.now()
    wb.save(OUT)
    print(f"[excel] {OUT.name} 生成完成（{len(wb.sheetnames)} 个 Sheet：{'、'.join(wb.sheetnames)}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
