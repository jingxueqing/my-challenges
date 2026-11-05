"""L4 Watcher：增量拉取 + 增量入库，不重复处理。

为什么强调"不重复"：
    如果每次跑都把 268 条消息重新入库，消息节点会被反复 upsert，
    看起来没坏，但会把「本周新增」的统计口径搞乱，
    更严重的是告警会重复推送——老师会直接关掉通知。

checkpoint 存在 graph 的 meta 表里（last_msg_id + 时间戳），
第 2 次运行必须返回 new=0，这一点有测试守着。
"""

from __future__ import annotations

from typing import Any

from .bridge import fetch_messages
from .classifier import classify_batch
from .config import ClassConfig
from .ingest import ingest
from .linker import link_messages
from .store import GraphStore


def processed_ids(store: GraphStore) -> set[str]:
    return {n["props"].get("msg_id") for n in store.nodes("Message") if n["props"].get("msg_id")}


def watch_once(
    cfg: ClassConfig,
    store: GraphStore,
    source_name: str = "replay",
    days: int | None = 14,
    fixture: str | None = None,
    url: str = "http://127.0.0.1:5030",
    dry_run: bool = False,
) -> dict[str, Any]:
    messages, meta = fetch_messages(cfg, source_name=source_name, days=days, fixture=fixture, url=url)
    classified = classify_batch(messages, cfg)
    linked = link_messages(classified, cfg)

    seen = processed_ids(store)
    new = [m for m in linked if m["msg_id"] not in seen]
    checkpoint = store.get_meta("checkpoint", {})

    result = {
        "source": source_name,
        "fetched": len(linked),
        "already_processed": len(linked) - len(new),
        "new": len(new),
        "new_types": _count(new, lambda m: m["intent"]),
        "previous_checkpoint": checkpoint,
        "checkpoint": {
            "last_msg_id": linked[-1]["msg_id"] if linked else None,
            "last_ts": linked[-1]["timestamp"] if linked else None,
            "total_processed": len(seen) + len(new),
        },
        "dry_run": dry_run,
    }

    if dry_run or not new:
        return result

    ingest(cfg, store, new, _empty_submissions(cfg), _empty_qa(), {"profiles": []}, None,
           only_message_ids={m["msg_id"] for m in new})
    store.set_meta("checkpoint", result["checkpoint"])
    store.set_meta("watch_log", [*store.get_meta("watch_log", []), result["checkpoint"]][-20:])
    return result


def _count(rows: list[dict[str, Any]], key) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        k = key(r)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _empty_submissions(cfg: ClassConfig) -> dict[str, Any]:
    return {
        "class_size": len(cfg.roster),
        "student_count": 0,
        "submission_count": 0,
        "artifact_count": 0,
        "complete_count": 0,
        "needs_revision_count": 0,
        "rows": [],
        "matrix": {},
        "by_challenge": {c: {"name": cfg.challenges[c].name_cn, "submitted": 0, "complete": 0,
                             "expected": len(cfg.roster), "rate_all": 0, "due": cfg.challenges[c].due}
                         for c in cfg.challenge_order},
        "by_student": {},
        "missing_required": [],
        "cells": len(cfg.roster) * len(cfg.challenge_order),
    }


def _empty_qa() -> dict[str, Any]:
    return {"pairs": [], "top_pairs": [], "unanswered": [], "kept": 0, "total_questions": 0,
            "answered": 0, "unanswered_count": 0, "answer_rate": 0, "avg_quality": 0, "top_tags": {}, "min_quality": 0}
