"""Level 4 —— 报告生成（Markdown + Excel + HTML）。

Excel 用标准库 zipfile 手写 SpreadsheetML（.xlsx 就是一个 zip + XML），
这样整个技能保持零第三方依赖，助教在任何装了 Python 的机器上都能跑。
"""

from __future__ import annotations

import html
import re
import zipfile
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from .completeness import CompletenessResult
from .quality import QualityResult

LEVEL_ICON = {"✅": "✅", "⚠️": "⚠️", "❌": "❌"}


@dataclass
class AuthorReport:
    author: str
    completeness: CompletenessResult
    quality: Optional[QualityResult]
    composite: float= 0.0      # 0~1
    rank: int = 0
    file_count: int = 0
    versions: list[str] = field(default_factory=list)
    needs_human: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "author": self.author, "composite": round(self.composite, 3),
            "rank": self.rank, "file_count": self.file_count,
            "versions": self.versions, "needs_human": self.needs_human,
            "completeness": self.completeness.to_dict(),
            "quality": self.quality.to_dict() if self.quality else None,
        }


@dataclass
class EvaluationReport:
    folder: str
    generated_at: str
    rubric_version: str
    authors: list[AuthorReport]
    n_files: int
    non_c4_count: int
    weights: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "folder": self.folder, "generated_at": self.generated_at,
            "rubric_version": self.rubric_version, "n_files": self.n_files,
            "n_authors": len(self.authors), "non_c4_count": self.non_c4_count,
            "weights": self.weights,
            "authors": [a.to_dict() for a in self.authors],
        }

    # ---------- 统计 ----------
    def stats(self) -> dict:
        n = len(self.authors)
        if not n:
            return {"n": 0}
        full = sum(1 for a in self.authors if a.completeness.n_missing == 0 and a.completeness.n_partial == 0)
        partial = sum(1 for a in self.authors if 0 < a.completeness.score < 1 and a.completeness.n_missing < 5)
        avg_q = sum(a.quality.quality_score for a in self.authors if a.quality) / max(
            1, sum(1 for a in self.authors if a.quality))
        avg_c = sum(a.completeness.score for a in self.authors) / n
        # 最常见缺失 / 最弱维度
        miss_count: dict[str, int] = {}
        weak: dict[str, int] = {}
        for a in self.authors:
            for s in a.completeness.slots:
                if s.status == "❌":
                    miss_count[s.label] = miss_count.get(s.label, 0) + 1
            if a.quality:
                for c in a.quality.criteria:
                    if c.grade == "❌":
                        weak[c.label] = weak.get(c.label, 0) + 1
        return {
            "n": n, "full": full, "partial": partial,
            "avg_quality": round(avg_q, 3), "avg_completeness": round(avg_c, 3),
            "avg_total_points": round(avg_q * 4, 2),
            "most_missing": max(miss_count.items(), key=lambda x: -x[1])[0] if miss_count else "—",
            "most_missing_n": max(miss_count.values()) if miss_count else 0,
            "weakest": max(weak.items(), key=lambda x: -x[1])[0] if weak else "—",
            "weakest_n": max(weak.values()) if weak else 0,
            "needs_human": sum(1 for a in self.authors if a.needs_human),
        }


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------

def render_markdown(rep: EvaluationReport, *, max_evidence: int = 3) -> str:
    s = rep.stats()
    L: list[str] = []
    A = L.append

    A("# C4 技能提交自动评审报告")
    A("")
    A(f"- **生成时间**：{rep.generated_at}")
    A(f"- **扫描路径**：`{rep.folder}`")
    A(f"- **识别提交**：{s.get('n', 0)} 位作者，{rep.n_files} 个 C4 相关文件"
      f"（另有 {rep.non_c4_count} 个非 C4 文件已过滤）")
    A(f"- **评审标准版本**：`{rep.rubric_version}`（四条件权重："
      + "、".join(f"{k} {v:.0%}" for k, v in rep.weights.items()) + "）")
    A(f"- **生成方式**：规则引擎自动评审，每条判定均附源文件与行号证据")
    A("")

    if not rep.authors:
        A(">⚠️ 未识别到任何 C4 提交。请检查：")
        A("> 1. 文件名是否含 `_C4_` 标记；")
        A("> 2. 目录路径是否正确；")
        A("> 3. 是否用了子文件夹按作者分组（父文件夹名会被当作作者名）。")
        return "\n".join(L)

    # ---- 一、班级总览 ----
    A("## 一、班级总览")
    A("")
    A("| 指标 | 数值 |")
    A("|------|------|")
    A(f"| 提交人数 | {s['n']} |")
    A(f"| 完整提交（5/5 无缺失） | {s['full']} |")
    A(f"| 部分缺失 | {s['partial']} |")
    A(f"| 平均完整性 | {s['avg_completeness']:.0%} |")
    A(f"| 平均质量分 | {s['avg_quality']:.2f}/4.00 |")
    A(f"| 需人工复核的作者 | {s.get('needs_human', 0)} |")
    A(f"| 全班最常缺失 | {s['most_missing']}（{s['most_missing_n']} 人） |")
    A(f"| 全班最弱维度 | {s['weakest']}（{s['weakest_n']} 人判❌） |")
    A("")

    # ---- 二、排名 ----
    A("## 二、综合排名")
    A("")
    A("> 综合分 = 完整性 × 40% + 质量分× 60%（质量分为四条件加权，满分 4.0）")
    A("")
    A("| 排名 | 作者 | 完整性 | 质量分 | 综合分 | 待复核 |")
    A("|------|------|--------|--------|--------|--------|")
    for a in rep.authors:
        q = f"{a.quality.total_points:.2f}/4" if a.quality else "—"
        A(f"| {a.rank} | **{a.author}** | {a.completeness.n_present}/5"
          f"{'⚠️' if a.completeness.n_partial else ''}"
          f" | {q} | **{a.composite:.3f}** |"
          f" {('、'.join(a.needs_human)) if a.needs_human else '—'} |")
    A("")

    # ---- 三、作者详情 ----
    A("## 三、作者详情")
    A("")
    for a in rep.authors:
        A(f"### {a.rank}. {a.author}")
        A("")
        A(f"文件数：{a.file_count}"
          + (f" ｜ 检出版本：{', '.join(a.versions)}" if a.versions else ""))
        A("")
        A("**① 完整性检查**")
        A("")
        A("| 必须文件 | 状态 | 证据强度 | 匹配文件 |")
        A("|---------|------|---------|----------|")
        for sl in a.completeness.slots:
            f = sl.matched_files[0] if sl.matched_files else "—"
            if len(sl.matched_files) > 1:
                f += f" (+{len(sl.matched_files)-1})"
            A(f"| {sl.label} | {sl.status} | {sl.strength:.2f} | `{f}` |")
        A("")
        A(f"**结论**：{a.completeness.verdict}（{a.completeness.score:.0%}）"
          + (f" ｜ 缺失：{'、'.join(a.completeness.missing_labels)}" if a.completeness.missing_labels else "")
          + (f" ｜ 弱证据需确认：{'、'.join(a.completeness.partial_labels)}" if a.completeness.partial_labels else ""))
        A("")

        if a.quality:
            A("**② 质量评审（四条件）**")
            A("")
            A("| 条件 | 评级 | 判定依据 | 置信度提示 |")
            A("|------|------|---------|-----------|")
            for c in a.quality.criteria:
                A(f"| {c.label} | {c.grade} | {c.reason} |"
                  f" {'⚠️ 需人工复核' if c.needs_human else '—'} |")
            A("")
            for c in a.quality.criteria:
                ev_lines = []
                for chk in c.checks:
                    for e in chk.evidence[:1]:
                        mark = "➕" if e.polarity == "positive" else "➖"
                        ev_lines.append(f"  - `{mark} {e.file}:{e.line}` {e.snippet[:70]}")
                        if len(ev_lines) >= max_evidence:
                            break
                    if len(ev_lines) >= max_evidence:
                        break
                if ev_lines:
                    A(f"<details><summary>{c.label} · {c.grade} 的关键证据</summary>")
                    A("")
                    A("\n".join(ev_lines))
                    A("")
                    A("</details>")
                    A("")
            A(f"**③ 质量总分**：{a.quality.total_points:.2f}/4.00"
              f"（加权原始分 {a.quality.quality_score:.3f}）")
            A("")
            if a.quality.advice:
                A("**④ 下一步行动建议**")
                A("")
                for i, adv in enumerate(a.quality.advice, 1):
                    A(f"{i}. {adv}")
                A("")
        else:
            A(">⚠️ 未能进行质量评审：无任何可读内容文件。")
            A("")

    # ---- 四、全班改进建议 ----
    A("## 四、全班共性改进建议")
    A("")
    A(f"1. **最缺`{s['most_missing']}`**（{s['most_missing_n']} 人缺失）——"
      f"下次提交前对照 C4 必交清单自查。")
    A(f"2. **最弱维度是`{s['weakest']}`**（{s['weakest_n']} 人判 ❌）——"
      f"建议在群内做一次该维度的专项分享。")
    A(f"3. **有 {s.get('needs_human', 0)} 位作者的判定证据不足**，"
      f"标记为「需人工复核」，请老师/助教对照源文件确认后再反馈。")
    A("")
    A("---")
    A("")
    A("*本报告由 `skill-evaluator` 自动生成。每条✅/⚠️/❌ 都可回溯到具体文件与行号；"
      "如认为某条判定有误，请对照报告中给出的 `文件:行号` 申诉。*")
    return "\n".join(L)


# --------------------------------------------------------------------------
# Excel（手写 xlsx，零依赖）
# --------------------------------------------------------------------------

def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _col_letter(n: int) -> str:
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _sheet_xml(rows: list[list], widths: list[int]) -> str:
    """行= list[list[cell]]；cell 为 str或 (str, bold) 。"""
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
    ]
    if widths:
        parts.append("<cols>")
        for i, w in enumerate(widths, 1):
            parts.append(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>')
        parts.append("</cols>")
    parts.append("<sheetData>")
    for ri, row in enumerate(rows, 1):
        parts.append(f'<row r="{ri}">')
        for ci, cell in enumerate(row, 1):
            ref = f"{_col_letter(ci)}{ri}"
            if isinstance(cell, tuple):
                text, bold = cell
            else:
                text, bold = cell, ri == 1
            st = ' s="1"' if (ri == 1 or bold) else ""
            parts.append(
                f'<c r="{ref}"{st} t="inlineStr"><is><t xml:space="preserve">'
                f"{_esc(text)}</t></is></c>"
            )
        parts.append("</row>")
    parts.append("</sheetData></worksheet>")
    return "".join(parts)


def write_xlsx(rep: EvaluationReport, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    s = rep.stats()

    # Sheet 1 排名
    rows1: list[list] = [[
        ("排名", True), ("作者", True), ("完整性(满分5)", True), ("完整性得分", True),
        ("质量分(满分4)", True), ("综合分", True), ("可复用", True), ("可执行", True),
        ("可验证", True), ("IO明确", True), ("缺失项", True), ("需人工复核", True),
    ]]
    for a in rep.authors:
        g = {c.key: c.grade for c in (a.quality.criteria if a.quality else [])}
        rows1.append([
            a.rank, a.author, a.completeness.n_present, round(a.completeness.score, 3),
            a.quality.total_points if a.quality else 0, round(a.composite, 3),
            g.get("reusable", "—"), g.get("executable", "—"),
            g.get("verifiable", "—"), g.get("clear_io", "—"),
            "、".join(a.completeness.missing_labels) or "—",
            "、".join(a.needs_human) or "—",
        ])

    # Sheet 2 完整性明细
    rows2: list[list] = [[
        ("作者", True), ("必须文件", True), ("状态", True), ("证据强度", True),
        ("匹配文件", True), ("判定理由", True),
    ]]
    for a in rep.authors:
        for sl in a.completeness.slots:
            rows2.append([
                a.author, sl.label, sl.status, sl.strength,
                "\n".join(sl.matched_files[:3]) or "—", sl.reason or "—",
            ])

    # Sheet 3 质量证据明细
    rows3: list[list] = [[
        ("作者", True), ("维度", True), ("检查项", True), ("通过", True),
        ("说明", True), ("证据", True),
    ]]
    for a in rep.authors:
        if not a.quality:
            continue
        for c in a.quality.criteria:
            for chk in c.checks:
                ev = "\n".join(e.render() for e in chk.evidence[:3]) or "—"
                rows3.append([a.author, c.label, chk.label,
                              "✅" if chk.passed else "❌", chk.detail, ev])

    # Sheet 4 改进建议
    rows4: list[list] = [[("作者", True), ("维度", True), ("建议", True)]]
    for a in rep.authors:
        if a.quality:
            for adv in a.quality.advice:
                m = re.match(r"\[(.+?)\]\s*(.*)", adv)
                rows4.append([a.author, m.group(1) if m else "—",
                              m.group(2) if m else adv])

    # Sheet 5 概览
    rows5: list[list] = [[("指标", True), ("数值", True)]]
    for k, v in [
        ("生成时间", rep.generated_at), ("扫描路径", rep.folder),
        ("评审标准版本", rep.rubric_version), ("作者数", s.get("n", 0)),
        ("C4 文件数", rep.n_files), ("完整提交", s.get("full", 0)),
        ("平均完整性", f"{s.get('avg_completeness', 0):.0%}"),
        ("平均质量分", f"{s.get('avg_quality', 0):.2f}/4"),
        ("最常缺失", s.get("most_missing", "—")),
        ("最弱维度", s.get("weakest", "—")),
        ("需人工复核人数", s.get("needs_human", 0)),
    ]:
        rows5.append([k, v])

    sheets = [
        ("排名总表", rows1, [6, 18, 16, 14, 14, 10, 9, 9, 9, 9, 24, 18]),
        ("完整性明细", rows2, [16, 20, 8, 10, 40, 36]),
        ("质量证据", rows3, [16, 10, 24, 8, 30, 60]),
        ("改进建议", rows4, [16, 10, 70]),
        ("概览", rows5, [20, 40]),
    ]

    # --- 打包 ---
    content_types = ['<?xml version="1.0" encoding="UTF-8"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>',
        '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>',
    ]
    for i in range(1, len(sheets) + 1):
        content_types.append(
            f'<Override PartName="/xl/worksheets/sheet{i}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    content_types.append("</Types>")

    rels = ('<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            "</Relationships>")

    wb = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
          'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>']
    for i, (name, _, _) in enumerate(sheets, 1):
        wb.append(f'<sheet name="{_esc(name)}" sheetId="{i}" r:id="rId{i}"/>')
    wb.append("</sheets></workbook>")

    wb_rels = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">']
    for i in range(1, len(sheets) + 1):
        wb_rels.append(
            f'<Relationship Id="rId{i}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
            f'target="worksheets/sheet{i}.xml"/>')
    wb_rels.append(f'<Relationship Id="rId{len(sheets)+1}" '
                   'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                   'target="styles.xml"/>')
    wb_rels.append("</Relationships>")

    styles = ('<?xml version="1.0" encoding="UTF-8"?>'
              '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
              '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
              '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
              '<fills count="3"><fill><patternFill patternType="none"/></fill>'
              '<fill><patternFill patternType="gray125"/></fill>'
              '<fill><patternFill patternType="solid"><fgColor rgb="FF2F5496"/>'
              '<bgColor indexed="64"/></patternFill></fill></fills>'
              '<borders count="1"><border/></borders>'
              '<cellStyleXfs count="1"><xf/></cellStyleXfs>'
              '<cellXfs count="2"><xf xfId="0"/><xf xfId="0" fontId="1" fillId="2" applyFont="1" applyFill="1"/></cellXfs>'
              "</styleSheet>")

    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "".join(content_types))
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/workbook.xml", "".join(wb))
        zf.writestr("xl/_rels/workbook.xml.rels", "".join(wb_rels))
        zf.writestr("xl/styles.xml", styles)
        for i, (_, rows, widths) in enumerate(sheets, 1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", _sheet_xml(rows, widths))
    return path


# --------------------------------------------------------------------------
# HTML 仪表板
# --------------------------------------------------------------------------

def render_html(rep: EvaluationReport) -> str:
    s = rep.stats()
    rows = []
    for a in rep.authors:
        g = {c.key: c for c in (a.quality.criteria if a.quality else [])}
        def gcell(k: str) -> str:
            c = g.get(k)
            if not c:
                return "<td class='na'>—</td>"
            return f"<td class='{c.grade}'>{c.grade}</td>"
        adv = "<br>".join(x.split("] ", 1)[-1] for x in (a.quality.advice[:2] if a.quality else []))
        rows.append(f"""
      <tr>
        <td class="rank">{a.rank}</td>
        <td class="name">{html.escape(a.author)}</td>
        <td><div class="bar"><i style="width:{a.completeness.score*100:.0f}%"></i></div>
            <span>{a.completeness.n_present}/5</span></td>
        {gcell('reusable')}{gcell('executable')}{gcell('verifiable')}{gcell('clear_io')}
        <td class="score">{a.quality.total_points if a.quality else 0:.2f}</td>
        <td class="total">{a.composite:.3f}</td>
        <td class="adv">{html.escape(adv) or '—'}</td>
      </tr>""")

    crits = ["reusable", "executable", "verifiable", "clear_io"]
    labels = {"reusable": "可复用", "executable": "可执行",
              "verifiable": "可验证", "clear_io": "IO 明确"}
    dist = ""
    for k in crits:
        n_ok = sum(1 for a in rep.authors if a.quality and (a.quality.by_key(k) or None)
                   and a.quality.by_key(k).grade == "✅")
        n_warn = sum(1 for a in rep.authors if a.quality and a.quality.by_key(k)
                     and a.quality.by_key(k).grade == "⚠️")
        n_bad = sum(1 for a in rep.authors if a.quality and a.quality.by_key(k)
                    and a.quality.by_key(k).grade == "❌")
        dist += (f'<div class="dist"><b>{labels[k]}</b>'
                 f'<span class="ok">✅ {n_ok}</span>'
                 f'<span class="warn">⚠️ {n_warn}</span>'
                 f'<span class="bad">❌ {n_bad}</span></div>')

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>C4 提交自动评审报告</title>
<style>
 :root {{ --bd:#e3e6ec; --mut:#6b7280; --ok:#16a34a; --warn:#d97706; --bad:#dc2626; --bg:#f7f8fa }}
 * {{ box-sizing:border-box }}
 body {{ margin:0; padding:32px; background:var(--bg); color:#1f2430;
   font:14px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif }}
 .wrap {{ max-width:1180px; margin:0 auto }}
 h1 {{ font-size:24px; margin:0 0 4px }}
 .sub {{ color:var(--mut); font-size:13px; margin-bottom:24px }}
 .cards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-bottom:24px }}
 .card {{ background:#fff; border:1px solid var(--bd); border-radius:10px; padding:16px }}
 .card .n {{ font-size:26px; font-weight:600 }}
 .card .l {{ color:var(--mut); font-size:12px; margin-top:2px }}
 .dist {{ display:flex; gap:8px; align-items:center; background:#fff; border:1px solid var(--bd);
   border-radius:10px; padding:10px 14px; margin-bottom:8px; font-size:13px }}
 .dist b {{ width:80px }}
 .ok {{ color:var(--ok) }} .warn {{ color:var(--warn) }} .bad {{ color:var(--bad) }}
 .na {{ color:var(--mut) }}
 table {{ width:100%; border-collapse:collapse; background:#fff; border:1px solid var(--bd);
   border-radius:10px; overflow:hidden }}
 th,td {{ padding:10px 12px; text-align:left; border-bottom:1px solid var(--bd); font-size:13px;
   vertical-align:top }}
 th {{ background:#eef1f6; font-weight:600; white-space:nowrap }}
 tr:last-child td {{ border-bottom:none }}
 td.rank {{ font-weight:600; color:var(--mut) }} td.name {{ font-weight:600 }}
 td.✅ {{ color:var(--ok); font-size:16px }} td.⚠️ {{ color:var(--warn); font-size:16px }}
 td.❌ {{ color:var(--bad); font-size:16px }}
 td.score,td.total {{ font-weight:600; font-variant-numeric:tabular-nums }}
 td.adv {{ color:var(--mut); font-size:12px; max-width:320px }}
 .bar {{ width:70px; height:6px; background:#e8eaef; border-radius:3px; overflow:hidden; display:inline-block;
   vertical-align:middle; margin-right:6px }}
 .bar i {{ display:block; height:100%; background:#2f5496 }}
 .foot {{ margin-top:20px; color:var(--mut); font-size:12px }}
</style></head><body><div class="wrap">
<h1>C4 技能提交自动评审报告</h1>
<div class="sub">生成时间 {rep.generated_at} ｜ 扫描路径 <code>{html.escape(rep.folder)}</code>
 ｜ 识别 {s.get('n',0)} 位作者 / {rep.n_files} 个 C4 文件 ｜ 标准 <code>{rep.rubric_version}</code></div>
<div class="cards">
  <div class="card"><div class="n">{s.get('n',0)}</div><div class="l">提交人数</div></div>
  <div class="card"><div class="n">{s.get('full',0)}</div><div class="l">完整提交（5/5）</div></div>
  <div class="card"><div class="n">{s.get('avg_completeness',0):.0%}</div><div class="l">平均完整性</div></div>
  <div class="card"><div class="n">{s.get('avg_quality',0):.2f}</div><div class="l">平均质量分 /4</div></div>
  <div class="card"><div class="n">{s.get('needs_human',0)}</div><div class="l">需人工复核</div></div>
</div>
<h2 style="font-size:15px;margin:20px 0 10px">四条件评级分布</h2>
{dist}
<h2 style="font-size:15px;margin:24px 0 10px">排名明细</h2>
<table><thead><tr><th>#</th><th>作者</th><th>完整性</th><th>可复用</th><th>可执行</th>
<th>可验证</th><th>IO明确</th><th>质量分</th><th>综合分</th><th>首要建议</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<div class="foot">由 skill-evaluator 自动生成（规则引擎，每条判定可回溯到文件:行号）。
综合分 = 完整性×40% + 质量分×60%。</div>
</div></body></html>"""
