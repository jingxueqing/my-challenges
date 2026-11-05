"""L2 挑战关联器：把一条消息挂到具体挑战上（C1..C10H）。

三种证据，按可信度排序：
    1. 显式挑战 ID（"C4B 的样式…" / 文件名里的 JingXueQing_C4B_交付物.md）
    2. 文件名 / 卡片标题
    3. 挑战配置里的 signal_keywords 命中数
    都没有则继承同一讨论线程里最近一条有归属的消息（标记 inherited，可信度低）。
"""

from __future__ import annotations

import re
from typing import Any

from .config import ClassConfig

_CID = re.compile(r"(?i)(?<![A-Za-z])C(\d{1,2})([A-Z]{0,2})(?![A-Za-z])")
THREAD_GAP_SECONDS = 1800


def _keyword_hits(text: str, cfg: ClassConfig) -> tuple[str | None, float, list[str]]:
    low = text.lower()
    best: tuple[str | None, float, list[str]] = (None, 0.0, [])
    for cid in cfg.challenge_order:
        ch = cfg.challenges[cid]
        hits = [kw for kw in ch.keywords if kw and kw.lower() in low]
        if not hits:
            continue
        score = len(hits) + min(len(hits), 3) * 0.5
        if score > best[1]:
            best = (cid, score, hits)
    return best


def link_messages(messages: list[dict[str, Any]], cfg: ClassConfig) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    last_cid: str | None = None
    from .bridge.base import parse_timestamp

    prev_ts = None
    for msg in messages:
        text = msg.get("content") or ""
        cid: str | None = None
        method = "none"
        score = 0.0
        evidence: list[str] = []

        # 1. 显式 ID（注意：文件名里的 C4B 也算）
        m = _CID.search(text)
        if m:
            cand = f"C{m.group(1)}{m.group(2).upper()}"
            if cand in cfg.challenges:
                cid, method, score = cand, "explicit_id", 1.0
                evidence.append(f"文本含 {cand}")

        # 2. 文件名规范
        if not cid and msg.get("type") == "file":
            nm = cfg.naming_regex.match(text)
            if nm and nm.group("challenge").upper() in cfg.challenges:
                cid = nm.group("challenge").upper()
                method, score = "filename", 1.0
                evidence.append("文件名含挑战ID")

        # 3. 关键词
        if not cid:
            kw_cid, kw_score, hits = _keyword_hits(text, cfg)
            if kw_cid and kw_score >= 1.5:
                cid, method, score = kw_cid, "keyword", round(min(kw_score / 5, 0.85), 2)
                evidence.append("关键词 " + "/".join(hits[:3]))

        # 4. 线程继承
        ts = parse_timestamp(msg["timestamp"])
        if not cid and last_cid and prev_ts and (ts - prev_ts).total_seconds() <= THREAD_GAP_SECONDS:
            cid, method, score = last_cid, "inherited", 0.35
            evidence.append("延续上文话题")

        row = {
            **msg,
            "challenge_ref": cid,
            "challenge_name": cfg.challenges[cid].name_cn if cid else None,
            "link_method": method,
            "link_score": score,
            "link_evidence": evidence,
        }
        out.append(row)

        if cid and method != "inherited":
            last_cid = cid
        elif cid is None and prev_ts and (ts - prev_ts).total_seconds() > 4 * THREAD_GAP_SECONDS:
            last_cid = None
        prev_ts = ts
    return out


def link_summary(linked: list[dict[str, Any]]) -> dict[str, Any]:
    by_method: dict[str, int] = {}
    by_challenge: dict[str, int] = {}
    for r in linked:
        by_method[r["link_method"]] = by_method.get(r["link_method"], 0) + 1
        if r["challenge_ref"]:
            by_challenge[r["challenge_ref"]] = by_challenge.get(r["challenge_ref"], 0) + 1
    return {
        "total": len(linked),
        "linked": sum(1 for r in linked if r["challenge_ref"]),
        "coverage": round(sum(1 for r in linked if r["challenge_ref"]) / len(linked), 3) if linked else 0,
        "by_method": dict(sorted(by_method.items(), key=lambda kv: -kv[1])),
        "by_challenge": dict(sorted(by_challenge.items(), key=lambda kv: -kv[1])),
    }
