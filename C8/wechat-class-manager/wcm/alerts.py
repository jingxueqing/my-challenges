"""L4 预警引擎：把「老师凭感觉发现的问题」变成可复现的规则。

七条规则，每条都能说清是拿哪几条数据算出来的（evidence 字段），
也都能在 tests 里用构造数据复现触发。没有证据的预警只会制造噪音。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from .config import KIND_CN, ClassConfig

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# 判「这句话到底像不像在问人」的兜底线索。
# 存在的理由：分类器把个别「分享结论」判成了 question（本机实例：彭心语那条
# 「标题里带具体数字和场景的打开率高很多，我自己测是这样。」），
# 于是催办草稿里出现「某某在群里问：…我自己测是这样。」——这种错一条就够丢人了。
# 说明：这里只挡「催答」这一个下游动作，不动分类器本身（准确率已冻结在 91.8%，
# 为了一个样本改权重会牵动另外 267 条，得不偿失）。
# 「怎么/如何」故意不在线索里：它们出现在陈述句里的频率不比疑问句低
# （本机实例：「我下周开始补，这周确实没怎么动。」），留着反而误催。
_QUESTION_HINTS = (
    "?", "？", "吗", "呢", "为什么", "为啥", "是不是", "有没有",
    "能不能", "可不可以", "哪个", "哪些", "谁", "多少", "几号", "几点", "请问", "求问",
)


def looks_like_question(text: str | None) -> bool:
    t = (text or "").strip()
    if not t:
        return False
    return any(h in t for h in _QUESTION_HINTS)


def _ts(s: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(s))
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=timezone(timedelta(hours=8)))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone(timedelta(hours=8)))


def evaluate(
    cfg: ClassConfig,
    linked: list[dict[str, Any]],
    submissions: dict[str, Any],
    qa: dict[str, Any],
    profiles: dict[str, Any],
    as_of: datetime | None = None,
) -> dict[str, Any]:
    as_of = as_of or (_ts(linked[-1]["timestamp"]) if linked else datetime.now())
    alerts: list[dict[str, Any]] = []
    rules = cfg.rules

    def add(kind: str, severity: str, subject: str, message: str, evidence: dict[str, Any], action: str) -> None:
        alerts.append(
            {
                "id": f"{kind}:{subject}",
                "type": kind,
                "severity": severity,
                "subject": subject,
                "message": message,
                "evidence": evidence,
                "action": action,
            }
        )

    # ---- 1. 截止风险：挑战临近 due，仍有学生没交 ----
    for cid in cfg.challenge_order:
        ch = cfg.challenges[cid]
        if not ch.due:
            continue
        due = date.fromisoformat(ch.due)
        days_left = (due - as_of.date()).days
        if days_left < 0 or days_left > rules.deadline_warn_days:
            continue
        missing = [s.nickname for s in cfg.roster.students.values() if cid not in submissions["matrix"].get(s.wxid, {})]
        if missing:
            add(
                "deadline_risk",
                "high" if days_left <= 1 else "medium",
                cid,
                f"{cid} 还有 {days_left} 天截止，{len(missing)} 人未提交",
                {"challenge": cid, "due": ch.due, "days_left": days_left, "missing": missing[:10], "missing_count": len(missing)},
                "今晚私信未交名单，并在群里发一次截止提醒",
            )

    # ---- 2. 挑战提交率过低（合并成一条，避免同一条规则刷 15 条预警）----
    low = [
        (cid, stat)
        for cid, stat in submissions["by_challenge"].items()
        if 0 < stat["rate_all"] < rules.low_submission_rate and stat["expected"] >= 5
    ]
    if low:
        low.sort(key=lambda kv: kv[1]["rate_all"])
        worst = low[0][1]
        add(
            "low_submission_rate",
            "high",
            "class",
            f"{len(low)} 个挑战提交率低于 {rules.low_submission_rate:.0%}，最低 {low[0][0]}（{worst['rate_all']:.0%}）",
            {
                "challenges": [
                    {"challenge": cid, "submitted": st["submitted"], "expected": st["expected"], "rate": st["rate_all"]}
                    for cid, st in low
                ]
            },
            "先确认是难度问题还是通知没触达，再决定是加提醒还是下调本周要求",
        )

    # ---- 3. 沉默学生 ----
    for p in profiles["profiles"]:
        if p["silence_days"] >= rules.silent_days:
            add(
                "silent_student",
                "high" if p["silence_days"] >= rules.silent_days * 2 else "medium",
                p["wxid"],
                f"{p['nickname']} 已 {p['silence_days']} 天零发言（最后一条 {(p['last_ts'] or '')[:16].replace('T', ' ')}）",
                {"nickname": p["nickname"], "silence_days": p["silence_days"], "last_ts": p["last_ts"], "msg_count": p["msg_count"]},
                "私信问候，先问是不是遇到困难，不要一上来催交",
            )

    # ---- 4. 活跃度下降（ΔE 偏差）----
    for p in profiles["profiles"]:
        if p["prev_week_msgs"] >= 4 and p["week_msgs"] <= p["prev_week_msgs"] * rules.engagement_drop_ratio:
            add(
                "engagement_drop",
                "medium",
                p["wxid"],
                f"{p['nickname']} 本周发言 {p['week_msgs']} 条，上周 {p['prev_week_msgs']} 条，下降 {int((1 - p['week_msgs'] / max(p['prev_week_msgs'], 1)) * 100)}%",
                {"nickname": p["nickname"], "this_week": p["week_msgs"], "last_week": p["prev_week_msgs"]},
                "看看是不是在憋大件，问一句「卡在哪」比催进度有用",
            )

    # ---- 5. 提交缺件 ----
    for r in submissions["rows"]:
        if r["missing"]:
            add(
                "missing_artifacts",
                "medium",
                f"{r['student']}:{r['challenge']}",
                f"{r['nickname']} 的 {r['challenge']} 缺 {len(r['missing'])} 件：{', '.join(KIND_CN.get(k, k) for k in r['missing'])}",
                {"student": r["nickname"], "challenge": r["challenge"], "missing": r["missing"], "artifacts": r["kinds"]},
                "发一条只讲缺件的短消息，不要重复整份规范",
            )

    # ---- 6. 提问无人回答 ----
    for u in qa["unanswered"]:
        age = (as_of - _ts(u["timestamp"])).total_seconds() / 3600
        if age >= rules.question_unanswered_hours and looks_like_question(u["question"]):
            add(
                "unanswered_question",
                "medium",
                u["msg_id"],
                f"{u['asker']['nickname']} 的提问已经 {int(age)} 小时没人回答：「{u['question'][:40]}」",
                {"question": u["question"], "asker": u["asker"]["nickname"], "age_hours": int(age), "challenge": u["challenge"]},
                "要么自己答，要么指定一个懂的人答，别让问题烂在群里",
            )

    # ---- 7. 命名违规（老师手工归档的真实痛点）----
    for r in submissions["rows"]:
        if r["issues"]:
            add(
                "naming_violation",
                "low",
                f"{r['student']}:{r['challenge']}",
                f"{r['nickname']} 的 {r['challenge']} 提交文件命名不规范",
                {"student": r["nickname"], "challenge": r["challenge"], "issues": r["issues"][:3]},
                "退回重发时给一个正确样例，别只说「不规范」",
            )

    alerts.sort(key=lambda a: (SEVERITY_ORDER[a["severity"]], a["type"], a["subject"]))
    by_type: dict[str, int] = {}
    by_sev: dict[str, int] = {"high": 0, "medium": 0, "low": 0}
    for a in alerts:
        by_type[a["type"]] = by_type.get(a["type"], 0) + 1
        by_sev[a["severity"]] += 1

    return {
        "as_of": as_of.isoformat(timespec="seconds"),
        "total": len(alerts),
        "by_severity": by_sev,
        "by_type": dict(sorted(by_type.items(), key=lambda kv: -kv[1])),
        "alerts": alerts,
    }


def digest_markdown(alert_result: dict[str, Any], limit: int = 8) -> str:
    lines = [f"### 预警摘要（{alert_result['as_of'][:10]}）", ""]
    sev_cn = {"high": "🔴 高", "medium": "🟡 中", "low": "⚪ 低"}
    for a in alert_result["alerts"][:limit]:
        lines.append(f"- {sev_cn[a['severity']]} · **{a['message']}**")
        lines.append(f"  - 依据：`{a['evidence']}`")
        lines.append(f"  - 建议：{a['action']}")
    if not alert_result["alerts"]:
        lines.append("- 本周没有触发任何预警，别放松，说明规则还没覆盖到。")
    return "\n".join(lines)
