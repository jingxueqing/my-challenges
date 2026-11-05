"""L3 把流水线产物写进 Property Graph。

图结构（与 docs/架构.md 的领域模型一一对应）：
    Student  --SENT-->      Message --TAGGED_WITH--> Challenge
    Student  --SUBMITTED--> Submission --ABOUT-->    Challenge
    Student  --ASKED-->     QAPair
    Student  --ANSWERED-->  QAPair
    Student  --MENTORED-->  Student        （由"回答了谁的问题"推断）
"""

from __future__ import annotations

from typing import Any

from .config import ClassConfig
from .store import GraphStore


def ingest(
    cfg: ClassConfig,
    store: GraphStore,
    linked: list[dict[str, Any]],
    submissions: dict[str, Any],
    qa: dict[str, Any],
    profiles: dict[str, Any],
    report_snapshot: dict[str, Any] | None = None,
    only_message_ids: set[str] | None = None,
) -> dict[str, Any]:
    counts = {"Student": 0, "Challenge": 0, "Message": 0, "Submission": 0, "QAPair": 0, "Report": 0}
    edges = {"SENT": 0, "TAGGED_WITH": 0, "SUBMITTED": 0, "ABOUT": 0, "ASKED": 0, "ANSWERED": 0, "MENTORED": 0}

    # ---- 学生 ----
    prof_by_wxid = {p["wxid"]: p for p in profiles.get("profiles", [])}
    for st in cfg.roster.students.values():
        p = prof_by_wxid.get(st.wxid, {})
        store.upsert_node(
            f"student:{st.wxid}",
            "Student",
            {
                "wxid": st.wxid,
                "name": st.nickname,
                "major": st.major,
                "enrollment_date": st.enrollment,
                "is_real": st.is_real,
                "msg_count": p.get("msg_count", 0),
                "engagement_score": p.get("engagement_score", 0),
                "skill_tags": p.get("skill_tags", []),
                "risk_flags": p.get("risk_flags", []),
            },
        )
        counts["Student"] += 1

    # ---- 老师 ----
    if cfg.teacher_wxid:
        store.upsert_node(
            f"teacher:{cfg.teacher_wxid}",
            "Teacher",
            {"wxid": cfg.teacher_wxid, "name": cfg.teacher_nickname, "role": "班主任"},
        )

    # ---- 挑战 ----
    for cid in cfg.challenge_order:
        ch = cfg.challenges[cid]
        stat = submissions["by_challenge"].get(cid, {})
        store.upsert_node(
            f"challenge:{cid}",
            "Challenge",
            {
                "id": cid,
                "name_cn": ch.name_cn,
                "name_en": ch.name_en,
                "due_date": ch.due,
                "levels": ["Bronze", "Silver", "Gold", "Platinum"],
                "required": list(ch.required),
                "submitted": stat.get("submitted", 0),
                "rate": stat.get("rate_all", 0),
            },
        )
        counts["Challenge"] += 1

    # ---- 消息 ----
    for m in linked:
        if only_message_ids is not None and m["msg_id"] not in only_message_ids:
            continue
        nid = f"message:{m['msg_id']}"
        store.upsert_node(
            nid,
            "Message",
            {
                "msg_id": m["msg_id"],
                "timestamp": m["timestamp"],
                "sender": m["sender"]["nickname"],
                "sender_id": m["sender"]["wechat_id"],
                "type": m["type"],
                "intent": m["intent"],
                "confidence": m["confidence"],
                "challenge": m.get("challenge_ref"),
                "link_method": m.get("link_method"),
                "content": (m.get("content") or "")[:160],
            },
        )
        counts["Message"] += 1
        sid = f"student:{m['sender']['wechat_id']}"
        if m["sender"]["wechat_id"] == cfg.teacher_wxid:
            sid = f"teacher:{cfg.teacher_wxid}"
        if store.get_node(sid):
            store.add_edge("SENT", sid, nid)
            edges["SENT"] += 1
        if m.get("challenge_ref"):
            cid = f"challenge:{m['challenge_ref']}"
            if store.get_node(cid):
                store.add_edge("TAGGED_WITH", nid, cid, {"method": m.get("link_method")})
                edges["TAGGED_WITH"] += 1

    # ---- 提交 ----
    for r in submissions["rows"]:
        nid = r["id"]
        store.upsert_node(
            nid,
            "Submission",
            {
                "student": r["nickname"],
                "student_id": r["student"],
                "challenge": r["challenge"],
                "status": r["status"],
                "completeness": r["completeness"],
                "kinds": r["kinds"],
                "missing": r["missing"],
                "artifact_count": r["artifact_count"],
                "sources": r["sources"],
                "last_ts": r["last_ts"],
            },
        )
        counts["Submission"] += 1
        store.add_edge("SUBMITTED", f"student:{r['student']}", nid)
        edges["SUBMITTED"] += 1
        store.add_edge("ABOUT", nid, f"challenge:{r['challenge']}")
        edges["ABOUT"] += 1

    # ---- Q&A ----
    for p in qa["pairs"]:
        nid = p["qa_id"]
        store.upsert_node(
            nid,
            "QAPair",
            {
                "question": p["question"][:160],
                "answer": p["answer"][:200],
                "quality_score": p["quality_score"],
                "resolved": p["resolved"],
                "tags": p["topic_tags"],
                "challenge": p["challenge"],
                "asker": p["asker"]["nickname"],
                "answerer": p["answerer"]["nickname"],
                "latency_seconds": p["latency_seconds"],
            },
        )
        counts["QAPair"] += 1
        asker, answerer = p["asker"]["wechat_id"], p["answerer"]["wechat_id"]
        if store.get_node(f"student:{asker}"):
            store.add_edge("ASKED", f"student:{asker}", nid)
            edges["ASKED"] += 1
        if store.get_node(f"student:{answerer}"):
            store.add_edge("ANSWERED", f"student:{answerer}", nid)
            edges["ANSWERED"] += 1
            store.add_edge("MENTORED", f"student:{answerer}", f"student:{asker}")
            edges["MENTORED"] += 1

    # ---- 报告快照 ----
    if report_snapshot:
        rid = f"report:{report_snapshot['period']['end'][:10]}"
        store.upsert_node(rid, "Report", {"type": "weekly", **report_snapshot})
        counts["Report"] += 1

    store.set_meta("last_ingest", counts)
    # 报给人看的数字一律以库里为准，不用「写入调用次数」：
    #   边：(type, src, dst) 有唯一索引，同一个学生答同一个人多次只留一条 MENTORED，
    #       逐类相加 711、实际 702，差 9 条（本机实测）；
    #   点：counts 里没有 Teacher，逐类相加 401、实际 402，差 1。
    # 这类「自己和自己对不上账」的数字，一旦被拿去写汇报就没人敢信了，所以直接查库。
    stats = store.stats()
    nodes = {k: v for k, v in stats.items() if k != "_edges"}
    store.vacuum()
    return {"nodes": nodes, "edges": store.counts_by_edge(), "stats": stats}
