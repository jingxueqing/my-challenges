"""统一命令行入口：一条命令跑完整链路，也可以逐层单独跑。

    python -m wcm.cli run --days 14 --fs ~/Desktop/挑战的产物 --owner JingXueQing
    python -m wcm.cli query "C4B 还有谁没交"
    python -m wcm.cli watch --days 14
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any

from . import alerts as alerts_mod
from . import dashboard as dash_mod
from . import nudge as nudge_mod
from . import profile as profile_mod
from . import qa as qa_mod
from . import report as report_mod
from .bridge import SourceError, fetch_messages, read_jsonl, write_jsonl
from .bridge.fs_scan import scan
from .classifier import classify_batch, evaluate, make_llm_reviewer, summarize_batch
from .config import load_config, project_path
from .ingest import ingest
from .linker import link_messages, link_summary
from .query import answer as query_answer
from .store import CST, GraphStore
from .submissions import build as build_submissions
from .watcher import watch_once

OUT = project_path("out")
DEFAULT_FIXTURE = project_path("data", "fixtures", "messages_raw.jsonl")
DEFAULT_LABELS = project_path("data", "fixtures", "labels.jsonl")


# ------------------------------ IO 小工具 ------------------------------
def _p(name: str) -> str:
    return os.path.join(OUT, name)


def _dump(path: str, obj: Any) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2)
    return path


def _load(path: str, default: Any = None) -> Any:
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _say(msg: str, quiet: bool = False) -> None:
    if not quiet:
        print(msg)


# ------------------------------ 全链路 ------------------------------
def run_pipeline(args) -> dict[str, Any]:
    cfg = load_config()
    quiet = getattr(args, "quiet", False)
    days = args.days

    _say("① 桥接：把群消息变成 JSONL …", quiet)
    fixture = args.fixture or (DEFAULT_FIXTURE if args.source == "replay" else None)
    messages, bridge_meta = fetch_messages(
        cfg, source_name=args.source, days=days, fixture=fixture, url=args.url,
        db_path=args.db, db_key=args.key, since=args.since, until=args.until,
    )
    write_jsonl(_p("messages.jsonl"), messages)
    _say(f"   {bridge_meta['count']} 条 · {bridge_meta['earliest']} → {bridge_meta['latest']}", quiet)

    _say("② 真实提交包（磁盘扫描）…", quiet)
    fs_subs: list[dict[str, Any]] = []
    if args.fs:
        owner = None
        if args.owner:
            st = cfg.roster.resolve(args.owner)
            owner = st.wxid if st else args.owner
        fs_subs = scan(args.fs, cfg, student_hint=owner)
        _dump(_p("submissions_fs.json"), {"count": len(fs_subs), "root": args.fs, "owner": args.owner, "submissions": fs_subs})
        _say(f"   {len(fs_subs)} 项 / {sum(s['artifact_count'] for s in fs_subs)} 个文件", quiet)
    else:
        # 不传 --fs 时不报错，但必须让用户看见「这次没有磁盘真值」，
        # 否则提交数会明显偏小，而人不会知道是自己少传了参数。
        _say("   未传 --fs，跳过磁盘扫描：提交矩阵只由群消息推断，会偏小", quiet)

    _say("③ 分类 …", quiet)
    reviewer = make_llm_reviewer() if getattr(args, "llm_review", False) else None
    classified = classify_batch(messages, cfg, llm_review=reviewer)
    write_jsonl(_p("classified.jsonl"), classified)
    metrics = None
    if os.path.exists(args.labels):
        metrics = evaluate(classified, read_jsonl(args.labels))
        metrics["mode"] = "rule+context" if not reviewer else "rule+context+llm"
        _dump(_p("metrics.json"), metrics)
        _say(f"   准确率 {metrics['accuracy']:.1%} · macro-F1 {metrics['macro_f1']} · 错 {metrics['error_count']} 条", quiet)

    _say("④ 挑战关联 …", quiet)
    linked = link_messages(classified, cfg)
    write_jsonl(_p("linked.jsonl"), linked)
    ls = link_summary(linked)
    _say(f"   覆盖 {ls['linked']}/{ls['total']}（{ls['coverage']:.0%}）· 方式 {ls['by_method']}", quiet)

    _say("⑤ 提交矩阵 …", quiet)
    subs = build_submissions(linked, cfg, fs_subs)
    _dump(_p("submissions.json"), subs)
    _say(f"   {subs['submission_count']} 项提交 · 完整 {subs['complete_count']} · 缺件 {subs['needs_revision_count']} · 文件 {subs['artifact_count']}", quiet)

    _say("⑥ Q&A 沉淀 …", quiet)
    qa = qa_mod.extract(linked, cfg)
    _dump(_p("qa.json"), qa)
    _say(f"   问题 {qa['total_questions']} · 答出 {qa['answered']} · 入库 {qa['kept']} 对", quiet)

    _say("⑦ 学生画像 …", quiet)
    profiles = profile_mod.build(cfg, linked, subs, qa)
    _dump(_p("profiles.json"), profiles)
    _say(f"   活跃 {profiles['active_count']} · 沉默 {profiles['silent_count']}", quiet)

    _say("⑧ 预警 …", quiet)
    alerts_data = alerts_mod.evaluate(cfg, linked, subs, qa, profiles, _as_of(args))
    _dump(_p("alerts.json"), alerts_data)
    _say(f"   {alerts_data['total']} 条（高 {alerts_data['by_severity']['high']} / 中 {alerts_data['by_severity']['medium']} / 低 {alerts_data['by_severity']['low']}）", quiet)

    _say("⑨ 周报 …", quiet)
    rep = report_mod.build(cfg, linked, subs, qa, profiles, alerts_data, window_days=days or 7, classify_metrics=metrics)
    with open(_p("report.md"), "w", encoding="utf-8") as fh:
        fh.write(rep["markdown"])
    _dump(_p("report.json"), rep["snapshot"])
    _say(f"   {_p('report.md')}", quiet)

    _say("⑩ 看板 …", quiet)
    html_text = dash_mod.render(cfg, linked, subs, qa, profiles, alerts_data, metrics, days or 7)
    dash_mod.write(_p("dashboard/index.html"), html_text)
    _say(f"   {_p('dashboard/index.html')}", quiet)

    _say("⑪ 写入图 …", quiet)
    store = GraphStore(_p("graph.db"))
    ing = ingest(cfg, store, linked, subs, qa, profiles, rep["snapshot"])
    _say(f"   节点 {ing['stats']} · 边 {ing['edges']}", quiet)
    store.close()

    _say("⑫ 催办草稿 …", quiet)
    nd = nudge_mod.build(cfg, alerts_data, profiles)
    _dump(_p("nudges.json"), {"private": nd["private"], "group": nd["group"]})
    with open(_p("nudges.md"), "w", encoding="utf-8") as fh:
        fh.write(nd["markdown"])

    summary = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "bridge": bridge_meta,
        "classify": summarize_batch(classified),
        "metrics": {k: metrics[k] for k in ("accuracy", "macro_f1", "total", "error_count")} if metrics else None,
        "link": ls,
        "submissions": {k: subs[k] for k in ("submission_count", "complete_count", "needs_revision_count", "artifact_count", "cells")},
        "qa": {k: qa[k] for k in ("total_questions", "answered", "kept", "answer_rate", "avg_quality")},
        "profiles": {k: profiles[k] for k in ("active_count", "silent_count")},
        "alerts": {k: alerts_data[k] for k in ("total", "by_severity", "by_type")},
        "outputs": sorted(os.listdir(OUT)),
    }
    _dump(_p("summary.json"), summary)
    globals()["_LAST_SUMMARY"] = summary
    _say("", quiet)
    _say("完成。产物在 out/：", quiet)
    for f in ["messages.jsonl", "classified.jsonl", "linked.jsonl", "submissions.json", "qa.json",
              "profiles.json", "alerts.json", "report.md", "dashboard/index.html", "graph.db", "metrics.json"]:
        if os.path.exists(_p(f)):
            _say(f"  · {f}", quiet)
    return summary


def _as_of(args) -> datetime | None:
    val = getattr(args, "as_of", None)
    if not val:
        return None
    try:
        return datetime.fromisoformat(val).replace(tzinfo=CST)
    except ValueError:
        return None


# ------------------------------ 单步命令 ------------------------------
def cmd_bridge(args) -> int:
    fixture = args.fixture or (DEFAULT_FIXTURE if args.source == "replay" else None)
    cfg = load_config()
    messages, meta = fetch_messages(cfg, source_name=args.source, days=args.days, fixture=fixture, url=args.url)
    out = args.output or _p("messages.jsonl")
    write_jsonl(out, messages)
    _dump(os.path.splitext(out)[0] + ".meta.json", meta)
    _say(f"{meta['count']} 条 → {out}")
    return 0


def cmd_classify(args) -> int:
    cfg = load_config()
    msgs = read_jsonl(args.input or _p("messages.jsonl"))
    reviewer = make_llm_reviewer() if args.llm_review else None
    pred = classify_batch(msgs, cfg, llm_review=reviewer)
    write_jsonl(args.output or _p("classified.jsonl"), pred)
    summary = summarize_batch(pred)
    _say(json.dumps(summary, ensure_ascii=False, indent=2))
    if os.path.exists(args.labels):
        metrics = evaluate(pred, read_jsonl(args.labels))
        _dump(_p("metrics.json"), metrics)
        _say(f"准确率 {metrics['accuracy']:.1%} / macro-F1 {metrics['macro_f1']}")
    return 0


def cmd_link(args) -> int:
    cfg = load_config()
    rows = read_jsonl(args.input or _p("classified.jsonl"))
    linked = link_messages(rows, cfg)
    write_jsonl(args.output or _p("linked.jsonl"), linked)
    _say(json.dumps(link_summary(linked), ensure_ascii=False, indent=2))
    return 0


def cmd_submissions(args) -> int:
    cfg = load_config()
    rows = read_jsonl(args.input or _p("linked.jsonl"))
    fs = (_load(_p("submissions_fs.json"), {}) or {}).get("submissions", [])
    subs = build_submissions(rows, cfg, fs)
    _dump(_p("submissions.json"), subs)
    _say(f"{subs['submission_count']} 项 / 完整 {subs['complete_count']} / 缺件 {subs['needs_revision_count']}")
    for r in subs["rows"][:15]:
        _say(f"  {r['nickname']:<5} {r['challenge']:<5} {r['status']:<15} 缺 {r['missing']}")
    return 0


def cmd_qa(args) -> int:
    cfg = load_config()
    rows = read_jsonl(args.input or _p("linked.jsonl"))
    res = qa_mod.extract(rows, cfg)
    _dump(_p("qa.json"), res)
    _say(f"问题 {res['total_questions']} / 答出 {res['answered']} / 入库 {res['kept']} / 均分 {res['avg_quality']}")
    for p in res["top_pairs"]:
        _say(f"  [{p['quality_score']}] {p['question'][:40]} → {p['answerer']['nickname']}")
    return 0


def cmd_profile(args) -> int:
    cfg = load_config()
    rows = read_jsonl(_p("linked.jsonl"))
    subs = _load(_p("submissions.json"), {})
    qa = _load(_p("qa.json"), {"pairs": []})
    res = profile_mod.build(cfg, rows, subs, qa)
    _dump(_p("profiles.json"), res)
    for p in res["profiles"]:
        _say(f"{p['rank']:>2}. {p['nickname']:<5} {p['engagement_score']:>5} 分 · {p['msg_count']:>2} 条 · 答 {p['answers_given']} · 提交 {p['accepted']} · {'; '.join(p['risk_flags']) or '正常'}")
    return 0


def cmd_alerts(args) -> int:
    cfg = load_config()
    rows = read_jsonl(_p("linked.jsonl"))
    subs = _load(_p("submissions.json"), {})
    qa = _load(_p("qa.json"), {})
    profiles = _load(_p("profiles.json"), {"profiles": []})
    res = alerts_mod.evaluate(cfg, rows, subs, qa, profiles, _as_of(args))
    _dump(_p("alerts.json"), res)
    _say(alerts_mod.digest_markdown(res, limit=20))
    return 0


def cmd_report(args) -> int:
    cfg = load_config()
    rows = read_jsonl(_p("linked.jsonl"))
    subs, qa = _load(_p("submissions.json"), {}), _load(_p("qa.json"), {})
    profiles, alerts_data = _load(_p("profiles.json"), {}), _load(_p("alerts.json"), {})
    metrics = _load(_p("metrics.json"), None)
    rep = report_mod.build(cfg, rows, subs, qa, profiles, alerts_data, window_days=args.days or 7, classify_metrics=metrics)
    path = args.output or _p("report.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(rep["markdown"])
    _dump(_p("report.json"), rep["snapshot"])
    _say(rep["markdown"])
    return 0


def cmd_dashboard(args) -> int:
    cfg = load_config()
    rows = read_jsonl(_p("linked.jsonl"))
    subs, qa = _load(_p("submissions.json"), {}), _load(_p("qa.json"), {})
    profiles, alerts_data = _load(_p("profiles.json"), {}), _load(_p("alerts.json"), {})
    metrics = _load(_p("metrics.json"), None)
    html_text = dash_mod.render(cfg, rows, subs, qa, profiles, alerts_data, metrics, args.days or 7)
    path = dash_mod.write(args.output or _p("dashboard/index.html"), html_text)
    _say(f"看板已生成：{path}")
    return 0


def cmd_ingest(args) -> int:
    cfg = load_config()
    rows = read_jsonl(_p("linked.jsonl"))
    subs, qa = _load(_p("submissions.json"), {}), _load(_p("qa.json"), {})
    profiles = _load(_p("profiles.json"), {})
    report = _load(_p("report.json"), None)
    store = GraphStore(args.db or _p("graph.db"))
    res = ingest(cfg, store, rows, subs, qa, profiles, report)
    _say(json.dumps(res, ensure_ascii=False, indent=2))
    store.close()
    return 0


def cmd_query(args) -> int:
    cfg = load_config()
    store = GraphStore(args.db or _p("graph.db"))
    res = query_answer(store, cfg, " ".join(args.question))
    store.close()
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        _say(f"问：{' '.join(args.question)}")
        _say(f"（意图：{res['intent']}，置信度 {res.get('confidence')}）")
        _say("")
        _say(res["answer"])
        if res.get("evidence"):
            _say("")
            _say("证据节点：" + "、".join(str(e) for e in res["evidence"][:8]))
    return 0


def cmd_watch(args) -> int:
    cfg = load_config()
    store = GraphStore(args.db or _p("graph.db"))
    fixture = args.fixture or (DEFAULT_FIXTURE if args.source == "replay" else None)
    res = watch_once(cfg, store, source_name=args.source, days=args.days, fixture=fixture, url=args.url, dry_run=args.dry_run)
    store.close()
    _say(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


def cmd_nudge(args) -> int:
    cfg = load_config()
    alerts_data = _load(_p("alerts.json"), {"alerts": [], "as_of": ""})
    profiles = _load(_p("profiles.json"), {"profiles": []})
    res = nudge_mod.build(cfg, alerts_data, profiles)
    _dump(_p("nudges.json"), {"private": res["private"], "group": res["group"]})
    path = _p("nudges.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(res["markdown"])
    _say(res["markdown"])
    _say(f"\n草稿已写入 {path}（不会自动发送）")
    return 0


def cmd_doctor(args) -> int:
    """环境自检：交付给别人之前先跑这个。"""
    import sqlite3

    cfg = load_config()
    checks = []
    checks.append(("Python", sys.version.split()[0], sys.version_info >= (3, 10)))
    checks.append(("SQLite", sqlite3.sqlite_version, True))
    try:
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE VIRTUAL TABLE t USING fts5(a)")
        checks.append(("FTS5 全文索引", "可用", True))
        conn.close()
    except Exception:  # noqa: BLE001
        checks.append(("FTS5 全文索引", "不可用（会退化为 LIKE）", False))
    checks.append(("回放数据集", f"{sum(1 for _ in open(DEFAULT_FIXTURE))} 条" if os.path.exists(DEFAULT_FIXTURE) else "缺失", os.path.exists(DEFAULT_FIXTURE)))
    checks.append(("标注集", "存在" if os.path.exists(DEFAULT_LABELS) else "缺失", os.path.exists(DEFAULT_LABELS)))
    checks.append(("挑战配置", f"{len(cfg.challenges)} 个", len(cfg.challenges) > 0))
    checks.append(("学生名单", f"{len(cfg.roster)} 人", len(cfg.roster) > 0))
    try:
        import sqlcipher3  # noqa: F401

        checks.append(("sqlcipher3", "已安装（可直连微信库）", True))
    except ImportError:
        checks.append(("sqlcipher3", "未安装（仅影响 sqlcipher 直连，不影响 replay）", None))
    wx_dir = os.path.expanduser("~/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files")
    if os.path.isdir(wx_dir):
        dbs = []
        for root, _, files in os.walk(wx_dir):
            for f in files:
                if f.endswith(".db"):
                    dbs.append(os.path.join(root, f))
        encrypted = 0
        for db in dbs[:20]:
            try:
                with open(db, "rb") as fh:
                    if fh.read(16) != b"SQLite format 3\x00":
                        encrypted += 1
            except OSError:
                pass
        checks.append(("本机微信库", f"发现 {len(dbs)} 个 .db，抽样 {min(20, len(dbs))} 个中 {encrypted} 个加密", None))
    else:
        checks.append(("本机微信库", "未发现", None))

    width = max(len(c[0]) for c in checks) + 2
    for name, detail, ok in checks:
        mark = "✅" if ok is True else ("⚠️ " if ok is None else "❌")
        _say(f"{mark} {name:<{width}}{detail}")
    _say("\n结论：核心链路只依赖标准库，`run` 可直接跑；直连微信库需要额外密钥，属于可选路径。")
    return 0


def cmd_selftest(args) -> int:
    import subprocess

    here = project_path()
    return subprocess.call([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=here)


# ------------------------------ 参数 ------------------------------
def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wcm", description="微信群 → 班级管理 Agent 技能")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp, with_source=True):
        if with_source:
            sp.add_argument("--source", default="replay", choices=["replay", "chatlog", "sqlcipher"])
            sp.add_argument("--fixture", default=None)
            sp.add_argument("--url", default="http://127.0.0.1:5030")
            sp.add_argument("--db", default=None, help="sqlcipher 的 db 路径，或 ingest/query 的 graph.db 路径")
            sp.add_argument("--key", default="")
        sp.add_argument("--days", type=int, default=7)
        sp.add_argument("--quiet", action="store_true")

    sp = sub.add_parser("run", help="跑完整链路（桥接→分类→关联→提交→QA→画像→预警→周报→看板→图）")
    add_common(sp)
    sp.add_argument("--since", default=None)
    sp.add_argument("--until", default=None)
    sp.add_argument("--as-of", dest="as_of", default=None, help="按指定日期计算预警（演练用）")
    sp.add_argument("--fs", default=None, help="额外扫描磁盘提交包目录")
    sp.add_argument("--owner", default=None, help="无姓名文件归属给谁")
    sp.add_argument("--labels", default=DEFAULT_LABELS)
    sp.add_argument("--llm-review", action="store_true", help="用 LLM 复核低置信度消息（需环境变量）")
    sp.set_defaults(func=run_pipeline)

    sp = sub.add_parser("bridge")
    add_common(sp)
    sp.add_argument("--output", "-o", default=None)
    sp.set_defaults(func=cmd_bridge)

    sp = sub.add_parser("classify")
    sp.add_argument("--input", default=None)
    sp.add_argument("--output", default=None)
    sp.add_argument("--labels", default=DEFAULT_LABELS)
    sp.add_argument("--llm-review", action="store_true")
    sp.set_defaults(func=cmd_classify)

    sp = sub.add_parser("link")
    sp.add_argument("--input", default=None)
    sp.add_argument("--output", default=None)
    sp.set_defaults(func=cmd_link)

    sp = sub.add_parser("submissions")
    sp.add_argument("--input", default=None)
    sp.set_defaults(func=cmd_submissions)

    sp = sub.add_parser("qa")
    sp.add_argument("--input", default=None)
    sp.set_defaults(func=cmd_qa)

    sp = sub.add_parser("profile")
    sp.set_defaults(func=cmd_profile)

    sp = sub.add_parser("alerts")
    sp.add_argument("--as-of", dest="as_of", default=None)
    sp.set_defaults(func=cmd_alerts)

    sp = sub.add_parser("report")
    sp.add_argument("--days", type=int, default=7)
    sp.add_argument("--output", "-o", default=None)
    sp.set_defaults(func=cmd_report)

    sp = sub.add_parser("dashboard")
    sp.add_argument("--days", type=int, default=7)
    sp.add_argument("--output", "-o", default=None)
    sp.set_defaults(func=cmd_dashboard)

    sp = sub.add_parser("ingest")
    sp.add_argument("--db", default=None)
    sp.set_defaults(func=cmd_ingest)

    sp = sub.add_parser("query")
    sp.add_argument("question", nargs="+")
    sp.add_argument("--db", default=None)
    sp.add_argument("--json", action="store_true")
    sp.set_defaults(func=cmd_query)

    sp = sub.add_parser("watch")
    add_common(sp)
    sp.add_argument("--dry-run", action="store_true")
    sp.set_defaults(func=cmd_watch)

    sp = sub.add_parser("nudge")
    sp.set_defaults(func=cmd_nudge)

    sp = sub.add_parser("doctor")
    sp.set_defaults(func=cmd_doctor)

    sp = sub.add_parser("selftest")
    sp.set_defaults(func=cmd_selftest)

    args = p.parse_args(argv)
    try:
        result = args.func(args)
        return result if isinstance(result, int) else 0
    except SourceError as exc:
        print(f"取数失败：{exc}", file=sys.stderr)
        return 3
    except FileNotFoundError as exc:
        print(f"缺输入：{exc}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
