"""
jd_insight.cli — 命令行入口

用法
----
    python -m jd_insight.cli match --jd data/jd_01.txt --resume data/resume_demo.txt -o out/report.html
    python -m jd_insight.cli rank  --jobs data/jd_samples.csv --resume data/resume_demo.txt --top 10
    python -m jd_insight.cli taxonomy
    python -m jd_insight.cli selfcheck

设计约定：任何子命令失败都返回非 0 退出码（便于 CI 与技能调用方判断），
错误信息只输出到 stderr，正常结果只输出到 stdout。
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from typing import Dict, List

from . import __version__
from .matcher import match as do_match
from .matcher import rank_jobs
from .report import render, write_html, write_json
from .taxonomy import DOMAINS, stats, tags_in_domain


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _load_jobs(path: str) -> List[Dict[str, str]]:
    """支持 .csv（含表头 id,company,title,jd_text）与 .json（数组）。"""
    if path.lower().endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [
            {
                "id": str(d.get("id", i)),
                "company": d.get("company", ""),
                "title": d.get("title", ""),
                "jd_text": d.get("jd_text", ""),
            }
            for i, d in enumerate(data)
        ]

    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"title", "jd_text"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV 缺少必需列: {sorted(missing)}；实际列: {reader.fieldnames}")
        return [
            {
                "id": row.get("id") or str(i),
                "company": row.get("company", ""),
                "title": row.get("title", ""),
                "jd_text": row.get("jd_text", ""),
            }
            for i, row in enumerate(reader)
        ]


def cmd_match(args: argparse.Namespace) -> int:
    jd_text = _read(args.jd)
    resume_text = _read(args.resume)
    ranked = None
    if args.jobs:
        ranked = rank_jobs(resume_text, _load_jobs(args.jobs), top=args.top)

    result = do_match(jd_text, resume_text)
    html_out = render(
        result,
        resume_name=args.resume_name,
        jd_title=args.jd_title,
        ranked=ranked,
    )
    write_html(args.out, html_out)
    if args.json:
        payload = result.to_dict()
        if ranked:
            payload["ranking"] = ranked
        payload["meta"] = {"version": __version__, "jd": args.jd, "resume": args.resume}
        write_json(args.json, payload)

    print(f"总分 {result.total:.1f}/100 · {result.grade} · {result.role_type}")
    if result.hard_gaps:
        print("硬缺口：" + "、".join(t.name for t in result.hard_gaps))
    print(f"报告已写入 {args.out}")
    return 0


def cmd_rank(args: argparse.Namespace) -> int:
    jobs = _load_jobs(args.jobs)
    resume_text = _read(args.resume)
    rows = rank_jobs(resume_text, jobs, top=args.top)
    if args.json:
        write_json(args.json, {"resume": args.resume, "ranking": rows})
    w = max((len(r["title"]) for r in rows), default=10)
    for i, r in enumerate(rows, 1):
        print(f"{i:>2}. {r['total']:>5.1f}  {r['title']:<{w}}  {r['company']}  [{r['grade']}]")
    print(f"\n共 {len(jobs)} 条 JD，展示前 {len(rows)} 条。")
    return 0


def cmd_taxonomy(args: argparse.Namespace) -> int:
    s = stats()
    print(f"标签总数 {s['tags']} ｜ 关键词 {s['keywords']} ｜ 域 {len(DOMAINS)}")
    for d in DOMAINS:
        tags = tags_in_domain(d)
        print(f"\n[{d}] {len(tags)} 项")
        for t in tags:
            print(f"  {t.id}  {t.name:<10} w={t.weight_default:.2f}  kw={len(t.all_keywords())}")
    return 0


def cmd_selfcheck(args: argparse.Namespace) -> int:
    """不依赖 pytest 的冒烟检查，给"不会用 pytest 的人"用。"""
    from . import parser as jp

    ok = True
    problems: List[str] = []

    s = stats()
    if s["tags"] < 40:
        ok = False
        problems.append(f"标签数偏少：{s['tags']}")

    texts = [
        "熟悉 Python 数据清洗，能独立完成 SQL 取数与指标体系设计。",
        "负责用户增长与活动运营，具备跨部门沟通能力，英语流利者优先。",
    ]
    for t in texts:
        hits = jp.extract(t)
        if not hits:
            ok = False
            problems.append(f"零召回：{t[:16]}…")

    # 单调性：同一简历，多加一句相关经历不应降分
    jd = "要求熟悉 Python 数据处理，掌握 SQL，具备指标体系设计能力。"
    r1 = do_match(jd, "会 Python。")
    r2 = do_match(jd, "会 Python，熟悉 SQL 取数与指标口径对齐。")
    if r2.total < r1.total:
        ok = False
        problems.append(f"单调性被破坏：{r1.total:.1f} → {r2.total:.1f}")

    if ok:
        print("selfcheck 通过：标签体系完整、解析器有召回、打分单调。")
        return 0

    print("selfcheck 失败：", file=sys.stderr)
    for p in problems:
        print(" - " + p, file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="jd-insight",
        description="岗位画像与匹配度分析：把 JD 拆成能力向量，把简历映射上去，输出可解释的匹配报告。",
    )
    p.add_argument("-v", "--version", action="version", version=f"jd-insight {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("match", help="单条 JD × 单份简历，生成 HTML 报告")
    m.add_argument("--jd", required=True, help="JD 文本文件路径")
    m.add_argument("--resume", required=True, help="简历文本文件路径")
    m.add_argument("-o", "--out", default="out/report.html", help="HTML 输出路径")
    m.add_argument("--json", default=None, help="可选：同时输出 JSON 结果")
    m.add_argument("--jobs", default=None, help="可选：岗位库 csv/json，用于横向排名")
    m.add_argument("--top", type=int, default=10, help="排名展示条数")
    m.add_argument("--jd-title", default="目标岗位", help="报告中显示的岗位名")
    m.add_argument("--resume-name", default="候选人", help="报告中显示的候选人名")
    m.set_defaults(func=cmd_match)

    r = sub.add_parser("rank", help="一份简历 × 一批 JD，输出排名")
    r.add_argument("--jobs", required=True)
    r.add_argument("--resume", required=True)
    r.add_argument("--top", type=int, default=10)
    r.add_argument("--json", default=None)
    r.set_defaults(func=cmd_rank)

    t = sub.add_parser("taxonomy", help="查看能力标签体系")
    t.set_defaults(func=cmd_taxonomy)

    c = sub.add_parser("selfcheck", help="冒烟自检")
    c.set_defaults(func=cmd_selfcheck)

    return p


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"文件不存在：{exc.filename}", file=sys.stderr)
        return 2
    except (ValueError, KeyError) as exc:
        print(f"输入有问题：{exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
