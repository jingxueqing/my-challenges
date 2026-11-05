"""L3 学生画像：从群互动 + 提交记录里长出「这个人擅长什么、卡在哪」。

画像不是给人贴标签，而是回答老师三个具体问题：
    1. 他这周还在吗？（活跃度、沉默天数）
    2. 他在哪些挑战上有产出？（提交覆盖、完整度）
    3. 他在帮谁？（回答了谁的问题，被感谢过没有）

engagement_score 的口径写死在下面，改口径只改这一个函数。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .config import ClassConfig

CST_OFFSET_HOURS = 8


def _ts(s: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(s))
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=timezone(timedelta(hours=8)))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone(timedelta(hours=8)))


def _engagement(msg_count: int, answer_count: int, accepted: int, active_days: int) -> float:
    """0-100 的口径分：发言 35 + 助人 25 + 提交 30 + 持续性 10。"""
    msg_score = min(msg_count / 40, 1.0) * 35
    answer_score = min(answer_count / 6, 1.0) * 25
    submit_score = min(accepted / 6, 1.0) * 30
    habit_score = min(active_days / 10, 1.0) * 10
    return round(msg_score + answer_score + submit_score + habit_score, 1)


def build(
    cfg: ClassConfig,
    linked: list[dict[str, Any]],
    submissions: dict[str, Any],
    qa: dict[str, Any],
    window_days: int = 7,
) -> dict[str, Any]:
    if not linked:
        return {"profiles": [], "note": "没有消息，无法生成画像"}
    end = _ts(linked[-1]["timestamp"])
    week_start = end - timedelta(days=window_days)
    prev_start = week_start - timedelta(days=window_days)

    by_student: dict[str, list[dict[str, Any]]] = {}
    for m in linked:
        by_student.setdefault(m["sender"]["wechat_id"], []).append(m)

    rows_by_student: dict[str, list[dict[str, Any]]] = {}
    for r in submissions["rows"]:
        rows_by_student.setdefault(r["student"], []).append(r)

    qa_by_answerer: dict[str, list[dict[str, Any]]] = {}
    for p in qa["pairs"]:
        qa_by_answerer.setdefault(p["answerer"]["wechat_id"], []).append(p)

    profiles: list[dict[str, Any]] = []
    for st in cfg.roster.students.values():
        mine = by_student.get(st.wxid, [])
        intents: dict[str, int] = {}
        for m in mine:
            intents[m["intent"]] = intents.get(m["intent"], 0) + 1
        days = sorted({m["timestamp"][:10] for m in mine})
        week_msgs = sum(1 for m in mine if _ts(m["timestamp"]) >= week_start)
        prev_msgs = sum(1 for m in mine if prev_start <= _ts(m["timestamp"]) < week_start)
        delta = 0.0
        if prev_msgs:
            delta = round((week_msgs - prev_msgs) / prev_msgs, 2)
        elif week_msgs:
            delta = 1.0
        silence = int((end - _ts(mine[-1]["timestamp"])).days) if mine else 999

        subs = rows_by_student.get(st.wxid, [])
        accepted = [r for r in subs if r["status"] == "accepted"]
        answered = qa_by_answerer.get(st.wxid, [])
        helped_thanks = sum(1 for p in answered if p["evidence"]["thanks_from_asker"])

        skill_tags: list[str] = []
        for r in accepted:
            if r["challenge"] not in skill_tags:
                skill_tags.append(r["challenge"])
        for p in answered:
            for t in p["topic_tags"]:
                if not t.startswith("C") and t not in skill_tags:
                    skill_tags.append(t)
        skill_tags = skill_tags[:8]

        risk: list[str] = []
        if silence >= cfg.rules.silent_days:
            risk.append(f"沉默 {silence} 天")
        if prev_msgs and week_msgs <= prev_msgs * cfg.rules.engagement_drop_ratio:
            risk.append(f"活跃度下降 {int((1 - week_msgs / max(prev_msgs, 1)) * 100)}%")
        rev = [r for r in subs if r["status"] == "needs_revision"]
        if rev:
            risk.append(f"{len(rev)} 项提交缺件：" + "、".join(r["challenge"] for r in rev))
        if mine and intents.get("question", 0) >= 3 and not answered:
            risk.append("只问不答")

        profiles.append(
            {
                "id": f"student:{st.wxid}",
                "wxid": st.wxid,
                "nickname": st.nickname,
                "major": st.major,
                "is_real": st.is_real,
                "msg_count": len(mine),
                "week_msgs": week_msgs,
                "prev_week_msgs": prev_msgs,
                "delta_ratio": delta,
                "intents": dict(sorted(intents.items(), key=lambda kv: -kv[1])),
                "active_days": len(days),
                "active_dates": days,
                "first_ts": mine[0]["timestamp"] if mine else None,
                "last_ts": mine[-1]["timestamp"] if mine else None,
                "silence_days": silence,
                "questions_asked": intents.get("question", 0),
                "answers_given": intents.get("answer", 0),
                "qa_answered": len(answered),
                "helped_and_thanked": helped_thanks,
                "submissions": len(subs),
                "accepted": len(accepted),
                "needs_revision": len(rev),
                "challenges": sorted(r["challenge"] for r in subs),
                "missing_items": sum(len(r["missing"]) for r in subs),
                "skill_tags": skill_tags,
                "engagement_score": _engagement(len(mine), intents.get("answer", 0), len(accepted), len(days)),
                "risk_flags": risk,
            }
        )

    ranked = sorted(profiles, key=lambda p: -p["engagement_score"])
    for i, p in enumerate(ranked, 1):
        p["rank"] = i

    return {
        "window_days": window_days,
        "as_of": linked[-1]["timestamp"],
        "profiles": ranked,
        "active_count": sum(1 for p in profiles if p["msg_count"] > 0),
        "silent_count": sum(1 for p in profiles if p["silence_days"] >= cfg.rules.silent_days),
        "top5": [{"nickname": p["nickname"], "score": p["engagement_score"], "msgs": p["msg_count"], "answers": p["answers_given"]} for p in ranked[:5]],
    }
