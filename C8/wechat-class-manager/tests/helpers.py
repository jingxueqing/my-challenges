"""测试公共工具：都走真实代码路径，不打桩。"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from wcm.bridge import fetch_messages, read_jsonl  # noqa: E402
from wcm.classifier import classify_batch  # noqa: E402
from wcm.config import load_config  # noqa: E402
from wcm.linker import link_messages  # noqa: E402

FIXTURE = os.path.join(ROOT, "data", "fixtures", "messages_raw.jsonl")
LABELS = os.path.join(ROOT, "data", "fixtures", "labels.jsonl")
FS_ROOT = os.path.expanduser("~/Desktop/挑战的产物")

_cache: dict[str, object] = {}


def cfg():
    if "cfg" not in _cache:
        _cache["cfg"] = load_config()
    return _cache["cfg"]


def messages(days: int = 14):
    key = f"msgs{days}"
    if key not in _cache:
        msgs, _ = fetch_messages(cfg(), source_name="replay", days=days, fixture=FIXTURE)
        _cache[key] = msgs
    return _cache[key]


def classified():
    if "classified" not in _cache:
        _cache["classified"] = classify_batch(messages(), cfg())
    return _cache["classified"]


def linked():
    if "linked" not in _cache:
        _cache["linked"] = link_messages(classified(), cfg())
    return _cache["linked"]


def labels():
    return read_jsonl(LABELS)


def msg(msg_id: str, ts: str, sender: str, content: str, mtype: str = "text", reply_to=None, nick=None):
    """手工造一条 UMF 消息，给单元测试用。"""
    return {
        "msg_id": msg_id,
        "timestamp": ts,
        "sender": {"wechat_id": sender, "nickname": nick or sender},
        "type": mtype,
        "content": content,
        "media_ref": "",
        "reply_to": reply_to,
        "group": "测试群",
        "raw_type": 1,
    }
