"""bridge 子系统对外接口。"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from ..config import ClassConfig
from .base import CST, dedupe, filter_window, iso, normalize_message, parse_timestamp
from .sources import ChatlogSource, ReplaySource, SourceError, SqlcipherSource, collect

__all__ = [
    "ChatlogSource",
    "ReplaySource",
    "SqlcipherSource",
    "SourceError",
    "collect",
    "fetch_messages",
    "read_jsonl",
    "write_jsonl",
    "dedupe",
    "filter_window",
]


def fetch_messages(
    cfg: ClassConfig,
    source_name: str = "replay",
    group: str | None = None,
    days: int | None = 7,
    since: str | None = None,
    until: str | None = None,
    fixture: str | None = None,
    url: str = "http://127.0.0.1:5030",
    db_path: str | None = None,
    db_key: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    group_name = group or cfg.group_name
    roster_map = {s.wxid: s.nickname for s in cfg.roster.students.values()}

    if source_name == "replay":
        if not fixture:
            raise SourceError("replay 模式需要 --fixture 指向一个 JSONL 文件")
        source: Any = ReplaySource(fixture)
    elif source_name == "chatlog":
        source = ChatlogSource(url)
    elif source_name == "sqlcipher":
        if not db_path or not db_key:
            raise SourceError("sqlcipher 模式需要 --db 和 --key")
        source = SqlcipherSource(db_path, db_key)
    else:
        raise SourceError(f"未知的 source：{source_name}")

    messages = collect(
        source,
        group=group_name,
        aliases=list(cfg.aliases),
        days=days,
        since=since,
        until=until,
        roster_map=roster_map,
        talker_id=cfg.group_id if source_name != "replay" else None,
    )
    messages = filter_window(messages, days=days, since=since, until=until)

    meta = {
        "source": source_name,
        "group": group_name,
        "days": days,
        "since": since,
        "until": until,
        "count": len(messages),
        "earliest": messages[0]["timestamp"] if messages else None,
        "latest": messages[-1]["timestamp"] if messages else None,
        "types": _count_by(messages, lambda m: m["type"]),
        "senders": len({m["sender"]["wechat_id"] for m in messages}),
        "generated_at": iso(datetime.now(CST)),
    }
    return messages, meta


def _count_by(rows: list[dict[str, Any]], key) -> dict[str, int]:
    out: dict[str, int] = {}
    for r in rows:
        k = key(r)
        out[k] = out.get(k, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def write_jsonl(path: str, rows: list[dict[str, Any]]) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return path


def read_jsonl(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"找不到输入文件：{path}（先跑 wechat_bridge.py）")
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out
