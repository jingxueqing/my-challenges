"""L3 Q&A 沉淀：从聊天流里抽出「问题 → 回答」对，做成课程 FAQ 的原料。

为什么值得单独做：
    群里最有价值的资产是「有人问过、有人答了」的那些对子，
    但它们埋在消息流里，三天后就翻不到了。抽出来 + 打分 + 打标签，
    就变成可检索、可复用的 FAQ，也是学生画像里「谁在帮谁」的证据。
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from .config import ClassConfig

ANSWER_WINDOW_SECONDS = 2 * 3600
THANKS_WINDOW_SECONDS = 30 * 60
_THANKS = ("谢谢", "感谢", "懂了", "明白了", "解决了", "可以了", "学到了", "好的谢谢")
_STEP_MARKERS = re.compile(r"(首先|然后|步骤|第一步|1\.|2\.|①|②|：.*：)", re.S)
_CODE_HINT = re.compile(r"(`|pip |npm |python |import |sudo |\\usepackage|\$ |git )")


def _ts(s: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(s))
    except (ValueError, TypeError):
        return datetime(1970, 1, 1, tzinfo=timezone(timedelta(hours=8)))
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone(timedelta(hours=8)))


def _qa_id(q_msg_id: str) -> str:
    return "qa:" + hashlib.sha1(q_msg_id.encode("utf-8")).hexdigest()[:10]


def _score(question: dict[str, Any], answer: dict[str, Any] | None, thanks: bool, responders: int) -> float:
    score = 0.2
    if answer:
        score += 0.25
        alen = len(answer.get("content") or "")
        if alen >= 30:
            score += 0.1
        if alen >= 60:
            score += 0.05
        if _CODE_HINT.search(answer.get("content") or ""):
            score += 0.1
        if _STEP_MARKERS.search(answer.get("content") or ""):
            score += 0.05
    if len(question.get("content") or "") >= 15:
        score += 0.05
    if thanks:
        score += 0.1
    if responders >= 2:
        score += 0.05
    return round(min(score, 1.0), 2)


def extract(linked: list[dict[str, Any]], cfg: ClassConfig, min_quality: float | None = None) -> dict[str, Any]:
    min_quality = cfg.rules.qa_min_quality if min_quality is None else min_quality
    by_id = {m["msg_id"]: m for m in linked}
    idx = {m["msg_id"]: i for i, m in enumerate(linked)}

    pairs: list[dict[str, Any]] = []
    unanswered: list[dict[str, Any]] = []

    for i, msg in enumerate(linked):
        if msg.get("intent") != "question":
            continue
        q_ts = _ts(msg["timestamp"])
        answer = None
        responder_ids: set[str] = set()

        # 1) 显式引用：最可信
        for cand in linked[i + 1:]:
            if cand.get("reply_to") == msg["msg_id"] and cand["sender"]["wechat_id"] != msg["sender"]["wechat_id"]:
                if cand.get("intent") in ("answer", "discussion"):
                    answer = cand
                    responder_ids.add(cand["sender"]["wechat_id"])
                    break

        # 2) 时间窗内的回答
        if answer is None:
            for cand in linked[i + 1:]:
                gap = (_ts(cand["timestamp"]) - q_ts).total_seconds()
                if gap > ANSWER_WINDOW_SECONDS:
                    break
                if cand["sender"]["wechat_id"] == msg["sender"]["wechat_id"]:
                    continue
                if cand.get("intent") == "answer":
                    answer = cand
                    responder_ids.add(cand["sender"]["wechat_id"])
                    break

        # 3) 追问者说"谢谢/解决了"也算一个问题被解决了
        thanks = False
        anchor_ts = _ts(answer["timestamp"]) if answer else q_ts
        for cand in linked[i + 1:]:
            gap = (_ts(cand["timestamp"]) - anchor_ts).total_seconds()
            if gap > THANKS_WINDOW_SECONDS:
                break
            if cand["sender"]["wechat_id"] != msg["sender"]["wechat_id"]:
                continue
            if any(w in (cand.get("content") or "") for w in _THANKS):
                thanks = True
                break

        if answer is None:
            unanswered.append(
                {
                    "msg_id": msg["msg_id"],
                    "question": msg["content"],
                    "asker": msg["sender"],
                    "timestamp": msg["timestamp"],
                    "challenge": msg.get("challenge_ref"),
                    "age_hours": None,
                }
            )
            continue

        tags = []
        if msg.get("challenge_ref"):
            tags.append(msg["challenge_ref"])
        text = (msg.get("content") or "") + (answer.get("content") or "")
        for cid in cfg.challenge_order:
            for kw in cfg.challenges[cid].keywords:
                if kw and kw in text and kw not in tags:
                    tags.append(kw)
                    break
        latency = int((_ts(answer["timestamp"]) - q_ts).total_seconds())
        pairs.append(
            {
                "qa_id": _qa_id(msg["msg_id"]),
                "question": msg["content"],
                "question_ts": msg["timestamp"],
                "question_msg_id": msg["msg_id"],
                "asker": msg["sender"],
                "answer": answer["content"],
                "answer_ts": answer["timestamp"],
                "answer_msg_id": answer["msg_id"],
                "answerer": answer["sender"],
                "latency_seconds": latency,
                "challenge": msg.get("challenge_ref") or answer.get("challenge_ref"),
                "topic_tags": tags[:5],
                "quality_score": _score(msg, answer, thanks, len(responder_ids)),
                "resolved": thanks or (answer.get("intent") == "answer"),
                "evidence": {
                    "cited_by_reply": answer.get("reply_to") == msg["msg_id"],
                    "thanks_from_asker": thanks,
                    "index_gap": idx[answer["msg_id"]] - i,
                },
            }
        )

    kept = [p for p in pairs if p["quality_score"] >= min_quality]
    kept.sort(key=lambda p: (-p["quality_score"], p["question_ts"]))
    unanswered.sort(key=lambda u: u["timestamp"])

    top = kept[:5]
    by_tag: dict[str, int] = {}
    for p in kept:
        for t in p["topic_tags"]:
            by_tag[t] = by_tag.get(t, 0) + 1

    return {
        "total_questions": len(pairs) + len(unanswered),
        "answered": len(pairs),
        "kept": len(kept),
        "unanswered_count": len(unanswered),
        "answer_rate": round(len(pairs) / (len(pairs) + len(unanswered)), 3) if (pairs or unanswered) else 0.0,
        "avg_quality": round(sum(p["quality_score"] for p in kept) / len(kept), 3) if kept else 0.0,
        "top_tags": dict(sorted(by_tag.items(), key=lambda kv: -kv[1])[:10]),
        "pairs": kept,
        "top_pairs": top,
        "unanswered": unanswered,
        "min_quality": min_quality,
    }
