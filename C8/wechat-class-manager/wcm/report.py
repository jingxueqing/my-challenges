"""L4 报告引擎：把图里的状态渲染成「能直接发群」的周报。

输出两份：
    report.md  —— 人类可读，可直接贴群 / 转公众号（C4B/C4C 的输入）
    report.json—— 机器可读快照，给 dashboard 和 AAR 对比用

原则：每个数字后面都能追到来源。写不出出处就不写这个数字。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .config import KIND_CN, ClassConfig


def _ts(s: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(s))
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=timezone(timedelta(hours=8)))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone(timedelta(hours=8)))


def _bar(rate: float, width: int = 14) -> str:
    filled = int(round(rate * width))
    return "█" * filled + "░" * (width - filled)


def build(
    cfg: ClassConfig,
    linked: list[dict[str, Any]],
    submissions: dict[str, Any],
    qa: dict[str, Any],
    profiles: dict[str, Any],
    alerts_data: dict[str, Any],
    window_days: int = 7,
    classify_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not linked:
        raise ValueError("没有消息，无法生成周报")
    end = _ts(linked[-1]["timestamp"])
    start = end - timedelta(days=window_days)
    week = [m for m in linked if start <= _ts(m["timestamp"]) <= end]

    new_subs = [r for r in submissions["rows"] if r["last_ts"] and start <= _ts(r["last_ts"]) <= end]
    week_intents: dict[str, int] = {}
    for m in week:
        week_intents[m["intent"]] = week_intents.get(m["intent"], 0) + 1

    active = [p for p in profiles["profiles"] if p["week_msgs"] > 0]
    total_cells = submissions["cells"]
    filled_cells = submissions["submission_count"]

    top_qa = qa["top_pairs"][:3]
    best = qa["top_pairs"][0] if qa["top_pairs"] else None

    lines: list[str] = []
    A = lines.append
    A(f"# 班级周报 · {start:%Y-%m-%d} ~ {end:%Y-%m-%d}")
    A("")
    A(f"> {cfg.group_name} ｜ 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')} ｜ 数据窗口 {window_days} 天")
    A("")
    A("## 一、一句话结论")
    A("")
    concl = (
        f"本周期 {len(week)} 条消息、{len(active)} 人发声、新增提交 {len(new_subs)} 项；"
        f"提交矩阵覆盖 {filled_cells}/{total_cells} 格（{filled_cells / total_cells:.0%}），"
        f"其中 {submissions['complete_count']} 项四件套齐全，{submissions['needs_revision_count']} 项缺件待补；"
        f"触发 {alerts_data['total']} 条预警，最高优先级 {alerts_data['by_severity']['high']} 条。"
    )
    A(concl)
    A("")

    A("## 二、关键数字")
    A("")
    A("| 指标 | 数值 | 口径 |")
    A("|---|---|---|")
    A(f"| 消息总量 | {len(week)} 条 | 本窗口内全部消息 |")
    A(f"| 发声人数 | {len(active)} / {len(cfg.roster)} | 窗口内至少发 1 条 |")
    A(f"| 提交项 | {filled_cells} 项 / {submissions['artifact_count']} 个文件 | 学生×挑战去重后的提交 |")
    A(f"| 完整提交 | {submissions['complete_count']} 项 | 挑战要求的必备件齐全 |")
    A(f"| 缺件待补 | {submissions['needs_revision_count']} 项 | 至少缺 1 件必备件 |")
    A(f"| Q&A 沉淀 | {qa['kept']} 对（答出率 {qa['answer_rate']:.0%}） | 质量分 ≥ {qa['min_quality']} |")
    A(f"| 预警 | {alerts_data['total']} 条 | 7 条规则命中 |")
    if classify_metrics:
        A(f"| 分类器准确率 | {classify_metrics['accuracy']:.1%} | 在 {classify_metrics['total']} 条标注样本上实测 |")
    A("")

    A("## 三、各挑战提交率")
    A("")
    A("| 挑战 | 名称 | 已交 | 完整 | 提交率 | |")
    A("|---|---|---:|---:|---|---|")
    for cid in cfg.challenge_order:
        st = submissions["by_challenge"][cid]
        if st["submitted"] == 0:
            continue
        A(f"| {cid} | {st['name']} | {st['submitted']} | {st['complete']} | {st['rate_all']:.0%} | `{_bar(st['rate_all'])}` |")
    A("")
    zero = [cid for cid in cfg.challenge_order if submissions["by_challenge"][cid]["submitted"] == 0]
    if zero:
        A(f"未开张的挑战：{'、'.join(zero)}（还没人提交，不一定是问题，但值得确认是不是还没到时间）")
        A("")

    A("## 四、本周最活跃 Top 5")
    A("")
    A("| # | 同学 | 参与分 | 消息 | 回答问题 | 完整提交 |")
    A("|---|---|---:|---:|---:|---:|")
    for p in profiles["profiles"][:5]:
        A(f"| {p['rank']} | {p['nickname']} | {p['engagement_score']} | {p['msg_count']} | {p['answers_given']} | {p['accepted']} |")
    A("")
    A("参与分口径：发言 35 + 助人 25 + 完整提交 30 + 持续性 10（见 `wcm/profile.py::_engagement`）。")
    A("")

    A("## 五、最佳 Q&A")
    A("")
    if best:
        A(f"**Q（{best['asker']['nickname']}，{best['question_ts'][:16]}）**：{best['question']}")
        A("")
        A(f"**A（{best['answerer']['nickname']}）**：{best['answer']}")
        A("")
        A(f"质量分 {best['quality_score']}；响应 {best['latency_seconds'] // 60} 分钟；标签 {'/'.join(best['topic_tags']) or '无'}。")
    else:
        A("本周没有达到质量阈值的问答对。")
    A("")
    if len(top_qa) > 1:
        A("其他值得存档的问答：")
        for p in top_qa[1:]:
            A(f"- {p['asker']['nickname']} → {p['answerer']['nickname']}：{p['question'][:38]}…（{p['quality_score']}）")
        A("")

    A("## 六、需要处理的事")
    A("")
    sev_cn = {"high": "🔴", "medium": "🟡", "low": "⚪"}
    for a in alerts_data["alerts"][:10]:
        A(f"- {sev_cn[a['severity']]} **{a['message']}**  " )
        A(f"  → {a['action']}")
    if not alerts_data["alerts"]:
        A("- 无。")
    A("")

    A("## 七、下周建议")
    A("")
    suggestions: list[str] = []
    if alerts_data["by_type"].get("missing_artifacts"):
        suggestions.append(f"把 {alerts_data['by_type']['missing_artifacts']} 项缺件逐个点名补齐，缺件名单见下方附录")
    if alerts_data["by_type"].get("silent_student"):
        suggestions.append(f"{alerts_data['by_type']['silent_student']} 位沉默同学需要一对一沟通，公开催交会适得其反")
    if qa["unanswered_count"]:
        suggestions.append(f"有 {qa['unanswered_count']} 个问题没人回答，挑 2 个在高频时段集中答，能顺手做成 FAQ")
    weak = [cid for cid in cfg.challenge_order if 0 < submissions["by_challenge"][cid]["rate_all"] < 0.3]
    if weak:
        suggestions.append(f"{'、'.join(weak)} 提交率不到 30%，先确认是难度问题还是通知没触达")
    if not suggestions:
        suggestions.append("保持当前节奏，把已经跑通的流程固化成模板")
    for s in suggestions:
        A(f"1. {s}" if s is suggestions[0] else f"- {s}")
    A("")

    A("## 八、口径与局限")
    A("")
    A("- 提交以**文件**为准，群里的「我交了」不计入。")
    A("- 完成率分母是全班人数，不是报名人数（两种口径都会虚高/虚低，这里固定一种并写明）。")
    A("- 消息来源："
      + ("本机真实提交包（磁盘） + 脱敏回放群消息。" if any(r["sources"] == ["disk"] or "disk" in r["sources"] for r in submissions["rows"]) else "回放群消息。"))
    A("- 分类与关联是规则引擎，误差见 `out/metrics.json` 的混淆矩阵；真实微信群尚未接入，准确率未测。")
    A("")

    if submissions["missing_required"]:
        A("## 附录：缺件清单")
        A("")
        A("| 同学 | 挑战 | 缺什么 |")
        A("|---|---|---|")
        for m in submissions["missing_required"]:
            A(f"| {m['nickname']} | {m['challenge']} | {', '.join(KIND_CN.get(k, k) for k in m['missing'])} |")
        A("")

    markdown = "\n".join(lines)

    snapshot = {
        "period": {"start": start.isoformat(timespec="seconds"), "end": end.isoformat(timespec="seconds"), "days": window_days},
        "messages": len(week),
        "active_students": len(active),
        "class_size": len(cfg.roster),
        "submissions": filled_cells,
        "artifacts": submissions["artifact_count"],
        "complete": submissions["complete_count"],
        "needs_revision": submissions["needs_revision_count"],
        "cells": total_cells,
        "fill_rate": round(filled_cells / total_cells, 3),
        "qa_kept": qa["kept"],
        "qa_answer_rate": qa["answer_rate"],
        "alerts": alerts_data["by_type"],
        "alert_total": alerts_data["total"],
        "intents": dict(sorted(week_intents.items(), key=lambda kv: -kv[1])),
        "top5": [{"nickname": p["nickname"], "score": p["engagement_score"]} for p in profiles["profiles"][:5]],
        "by_challenge": submissions["by_challenge"],
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }
    return {"markdown": markdown, "snapshot": snapshot, "period": snapshot["period"]}
