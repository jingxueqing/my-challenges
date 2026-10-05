"""评审流水线编排 —— 把 Level 1→4 串成一条命令。

    python3 scripts/evaluate_c4.py <文件夹> --out 输出目录

设计：每层是独立函数，流水线只做编排。
这样测试可以单独测任一层，助教也可以只跑 Level1/2 做快速盘点。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import collect, completeness, quality, report as reporter
from .rubric import DEFAULT_WEIGHTS, rules_version

W_COMPLETENESS = 0.4
W_QUALITY = 0.6


def evaluate(
    folder: str | Path,
    *,
    challenge: str = "C4",
    weights: dict[str, float] | None = None,
    out_dir: str | Path | None = None,
    write_xlsx: bool = True,
    write_html: bool = True,
    write_json: bool = True,
    levels: tuple[int, ...] = (1, 2, 3, 4),
) -> reporter.EvaluationReport:
    """跑完整流水线。levels 可限制只跑到某一级。"""
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)

    # ---- Level 1 ----
    scan = collect.scan(folder, challenge=challenge)
    max_lv = max(levels)

    authors: list[reporter.AuthorReport] = []
    for author, files in scan.by_author.items():
        # ---- Level 2 ----
        comp = completeness.check_author(author, files)
        # ---- Level 3 ----
        qual = (quality.evaluate_quality(author, files, weights=w)
                if max_lv >= 3 else None)
        q_score = qual.quality_score if qual else 0.0
        composite = comp.score * W_COMPLETENESS + q_score * W_QUALITY
        versions = sorted({f"v{f.version}" for f in files if f.version})
        authors.append(reporter.AuthorReport(
            author=author, completeness=comp, quality=qual,
            composite=round(composite, 3), file_count=len(files),
            versions=versions, needs_human=(qual.needs_human if qual else []),
        ))

    # 排名：先比综合分，同分比完整性，再按作者名稳定排序
    authors.sort(key=lambda a: (-a.composite, -a.completeness.score, a.author))
    for i, a in enumerate(authors, 1):
        a.rank = i

    rep = reporter.EvaluationReport(
        folder=str(scan.folder),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        rubric_version=rules_version(),
        authors=authors, n_files=len(scan.c4_files),
        non_c4_count=len(scan.non_c4), weights=w,
    )

    # ---- Level 4 ----
    if max_lv >= 4 and out_dir:
        out = Path(out_dir).expanduser()
        out.mkdir(parents=True, exist_ok=True)
        (out / "评审报告.md").write_text(reporter.render_markdown(rep), encoding="utf-8")
        if write_html:
            (out / "评审仪表盘.html").write_text(reporter.render_html(rep), encoding="utf-8")
        if write_xlsx:
            reporter.write_xlsx(rep, out / "评审详表.xlsx")
        if write_json:
            (out / "评审结果.json").write_text(
                json.dumps(rep.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        # 附一份文件清单，方便核对扫描范围
        (out / "文件清单.json").write_text(
            json.dumps([f.to_dict() for f in scan.c4_files],
                       ensure_ascii=False, indent=2), encoding="utf-8")

    return rep


def quick_scan(folder: str | Path, challenge: str = "C4") -> dict:
    """只跑 Level 1 —— 盘点谁交了什么，秒级返回。"""
    scan = collect.scan(folder, challenge=challenge)
    return {
        "summary": scan.summary(),
        "authors": {
            a: [{"name": f.name, "size_kb": f.size_kb, "ext": f.ext,
                 "author_source": f.author_source} for f in fs]
            for a, fs in scan.by_author.items()
        },
    }
