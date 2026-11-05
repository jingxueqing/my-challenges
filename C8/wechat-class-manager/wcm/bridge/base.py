"""消息标准化（UMF = Unified Message Format）。

所有 adapter 的产出都必须经过这里，产出同一种 message dict：

    {
      "msg_id": "unique_id",
      "timestamp": "2026-04-10T14:30:00+08:00",
      "sender": {"wechat_id": "xxx", "nickname": "张三"},
      "type": "text|image|file|voice|link|system",
      "content": "消息文本内容",
      "media_ref": "path/to/attachment_if_any",
      "reply_to": "parent_msg_id_if_any",
      "group": "群名",
      "raw_type": 49
    }
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable
from xml.etree import ElementTree as ET

CST = timezone(timedelta(hours=8))

RAW_TYPE_MAP = {
    1: "text",
    3: "image",
    34: "voice",
    37: "system",      # 好友请求
    42: "link",        # 名片
    43: "image",       # 视频按图片处理（有媒体引用）
    47: "image",       # 表情
    48: "link",        # 位置
    49: "link",        # app 消息，下面按子类型细化
    10000: "system",
    10002: "system",
}

APP_SUBTYPE = {
    5: "link", 6: "file", 8: "image", 19: "link", 33: "link", 36: "link", 57: "link", 74: "file",
}

_TS_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
)


def parse_timestamp(value: Any) -> datetime:
    """把 unix 秒/毫秒 或各种字符串时间转成 +08:00 的 datetime（失败则用现在）。"""
    if value is None or value == "":
        return datetime.now(CST)
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:  # 毫秒
            ts /= 1000.0
        return datetime.fromtimestamp(ts, CST)
    text = str(value).strip()
    if re.fullmatch(r"\d{10,13}", text):
        return parse_timestamp(int(text))
    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=CST)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt.astimezone(CST) if dt.tzinfo else dt.replace(tzinfo=CST)
    except ValueError:
        return datetime.now(CST)


def iso(dt: datetime) -> str:
    return dt.astimezone(CST).isoformat(timespec="seconds")


def _xml_field(xml: str, tag: str) -> str:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        m = re.search(rf"<{tag}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", xml, re.S)
        return (m.group(1).strip() if m else "")
    node = root.find(f".//{tag}")
    return (node.text or "").strip() if node is not None and node.text else ""


def _parse_refer(xml: str) -> str | None:
    """引用的消息 id（<refermsg><msgid>…）。"""
    for key in ("msgid", "svrid"):
        val = _xml_field(xml, key)
        if val:
            return val
    return None


def normalize_message(raw: dict[str, Any], default_group: str = "", roster_map: dict[str, str] | None = None) -> dict[str, Any] | None:
    """把一条原始记录转成 UMF。返回 None 表示应该丢弃（空内容/无 id）。"""
    roster_map = roster_map or {}
    raw_type = raw.get("type", raw.get("msgType", 1))
    try:
        raw_type = int(raw_type)
    except (TypeError, ValueError):
        raw_type = 1

    contents = raw.get("contents") or raw.get("content_parsed") or {}
    if isinstance(contents, str):
        try:
            contents = json.loads(contents)
        except json.JSONDecodeError:
            contents = {}

    content = raw.get("content") or raw.get("strContent") or ""
    media_ref = raw.get("media_ref") or ""
    reply_to = raw.get("reply_to") or None
    msg_type = RAW_TYPE_MAP.get(raw_type, "text")

    if raw_type == 49:
        subtype = contents.get("type") if isinstance(contents, dict) else None
        try:
            subtype = int(subtype) if subtype is not None else None
        except (TypeError, ValueError):
            subtype = None
        msg_type = APP_SUBTYPE.get(subtype or 0, "link")
        if isinstance(contents, dict):
            title = contents.get("title") or contents.get("fileName") or ""
            url = contents.get("url") or contents.get("fileUrl") or ""
            if msg_type == "file":
                media_ref = media_ref or url
                content = content or title
            elif msg_type == "link":
                content = content or f"{title} {url}".strip()
            if not reply_to:
                refer = contents.get("refer") or contents.get("refermsg")
                if isinstance(refer, dict):
                    reply_to = str(refer.get("msgid") or refer.get("svrid") or "") or None
                elif isinstance(refer, str) and "<refermsg>" in refer:
                    reply_to = _parse_refer(refer)
    elif raw_type == 1 and "<refermsg>" in content:
        reply_to = reply_to or _parse_refer(content)
        content = re.sub(r"<refermsg>.*?</refermsg>", "", content, flags=re.S).strip()

    if raw_type in (10000, 10002):
        content = re.sub(r"<[^>]+>", "", content).strip()
        if "撤回" in content and not content:
            return None

    if isinstance(content, str) and content.startswith("<"):
        stripped = re.sub(r"<[^>]+>", "", content).strip()
        if stripped:
            content = stripped

    sender_id = str(raw.get("sender") or raw.get("senderName") or raw.get("strTalker") or "")
    nickname = (
        raw.get("senderName")
        or roster_map.get(sender_id)
        or raw.get("nickname")
        or sender_id
    )

    msg_id = str(raw.get("msgId") or raw.get("msg_id") or raw.get("MsgSvrID") or raw.get("localId") or "")
    if not msg_id:
        msg_id = f"auto-{abs(hash((sender_id, raw.get('time') or raw.get('createTime'), content))) % 10**12}"
    if not str(content).strip() and msg_type in ("text", "system") and not media_ref:
        return None

    dt = parse_timestamp(raw.get("time") or raw.get("createTime") or raw.get("CreateTime"))
    return {
        "msg_id": msg_id,
        "timestamp": iso(dt),
        "sender": {"wechat_id": sender_id, "nickname": nickname},
        "type": msg_type,
        "content": str(content).strip(),
        "media_ref": media_ref,
        "reply_to": reply_to,
        "group": raw.get("talkerName") or raw.get("group") or default_group,
        "raw_type": raw_type,
    }


def dedupe(messages: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for m in messages:
        if m["msg_id"] in seen:
            continue
        seen.add(m["msg_id"])
        out.append(m)
    out.sort(key=lambda m: (m["timestamp"], m["msg_id"]))
    return out


def filter_window(
    messages: Iterable[dict[str, Any]],
    days: int | None = None,
    since: str | None = None,
    until: str | None = None,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """按时间窗过滤。days 表示「最近 N 天」（以数据里最新一条为基准，而不是机器当前时间），
    这样回放历史数据时行为也可预测。"""
    msgs = list(messages)
    if not msgs:
        return []
    lower = upper = None
    if days:
        anchor = parse_timestamp(until) if until else parse_timestamp(max(m["timestamp"] for m in msgs))
        lower = anchor - timedelta(days=days)
        upper = anchor
    if since:
        lower = parse_timestamp(since)
    if until:
        upper = parse_timestamp(until)
    out = []
    for m in msgs:
        ts = parse_timestamp(m["timestamp"])
        if lower and ts < lower:
            continue
        if upper and ts > upper:
            continue
        out.append(m)
    return out


def is_group_name_match(candidate: str, group: str, aliases: Iterable[str]) -> bool:
    cand = (candidate or "").strip()
    targets = [group] + list(aliases)
    for t in targets:
        if not t:
            continue
        if cand == t or t in cand or cand in t:
            return True
    return False
