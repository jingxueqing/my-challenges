"""消息来源适配器：replay / chatlog / sqlcipher。

为什么做成适配器而不是只写一个脚本：
    课程给的 wechat-cli / chatlog 都能导出数据，但不同机器的导出格式不一样。
    把「取数」和「标准化」拆开，换工具只加一个 adapter，下游 skill 一行不改。
"""

from __future__ import annotations

import json
import os
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from typing import Any, Iterator

from .base import CST, is_group_name_match, normalize_message, parse_timestamp


class SourceError(RuntimeError):
    """取数失败（附可操作的下一步提示）。"""


class ReplaySource:
    """回放本地导出的 JSONL（chatlog --format json / 自建导出都行）。

    这是团队协作里最重要的一个 adapter：评审、测试、A/B 都不要碰别人真实的微信数据，
    拿一份脱敏 JSONL 就能复现全链路。
    """

    name = "replay"

    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        if not os.path.exists(self.path):
            raise SourceError(f"找不到回放文件：{self.path}")

    def raw_records(self) -> Iterator[dict[str, Any]]:
        with open(self.path, "r", encoding="utf-8") as fh:
            for lineno, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise SourceError(f"{self.path} 第 {lineno} 行不是合法 JSON：{exc}") from exc


class ChatlogSource:
    """通过 chatlog 的 HTTP API 取数（sjzar/chatlog，默认 127.0.0.1:5030）。

    用法：
        chatlog server                # 另一个终端
        wechat_bridge.py --source chatlog --url http://127.0.0.1:5030 --group Elite20 --days 7
    chatlog 的返回格式在不同版本间略有差异，这里按「字段存在即取」的方式兼容。
    """

    name = "chatlog"

    def __init__(self, base_url: str = "http://127.0.0.1:5030", token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token or os.environ.get("CHATLOG_TOKEN", "")

    def _get(self, path: str, params: dict[str, str]) -> Any:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise SourceError(
                f"连不上 chatlog（{self.base_url}）：{exc}。"
                "先在另一个终端跑 `chatlog server`，或改用 --source replay 走离线文件。"
            ) from exc

    def raw_records(self, talker: str, start: date, end: date) -> Iterator[dict[str, Any]]:
        # chatlog 支持按天切片拉取，避免一次拉太多
        day = start
        while day <= end:
            time_range = f"{day.isoformat()}~{day.isoformat()}"
            payload = self._get("/api/v1/chatlog", {"talker": talker, "time": time_range, "format": "json"})
            rows = payload.get("messages") if isinstance(payload, dict) else payload
            for row in rows or []:
                yield row
            day += timedelta(days=1)


class SqlcipherSource:
    """直连本地 WeChat 4.x 的 SQLCipher 数据库。

    现实约束（必须说清楚）：
        macOS 上 WeChat 4.x 的 message_*.db 是 SQLCipher 加密的，密钥只在微信进程内存里，
        取出密钥需要 attach 到运行中的进程（root + task_for_pid），属于侵入式操作。
        本机实测：数据库头不是 "SQLite format 3"，无密钥无法读取。
        因此这个 adapter 是「可接入口」而不是「已验证路径」——有 key 的同学可以直接用。

        python wechat_bridge.py --source sqlcipher --db <message_0.db> --key <hex或明文>
    """

    name = "sqlcipher"

    def __init__(self, db_path: str, key: str):
        self.db_path = os.path.abspath(db_path)
        self.key = key

    def _connect(self) -> sqlite3.Connection:
        try:
            import sqlcipher3  # type: ignore
        except ImportError as exc:
            raise SourceError(
                "缺少 sqlcipher3：`pip install sqlcipher3-binary`。"
                "或者更省事：用 chatlog 导出一次 JSON，再 --source replay。"
            ) from exc
        conn = sqlcipher3.connect(self.db_path)
        conn.execute(f"PRAGMA key = '{self.key}'")
        try:
            conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
        except Exception as exc:  # noqa: BLE001 - 密钥错误/文件腐蚀都从这里冒出来
            raise SourceError(f"打不开加密库（key 不对或文件被占用）：{exc}") from exc
        return conn

    def raw_records(self, talker_name: str, start: date, end: date) -> Iterator[dict[str, Any]]:
        conn = self._connect()
        try:
            # WeChat 4.x：Name2Id 把 talker 映射成 id，消息在 Msg_<md5(talker)> 表里
            row = conn.execute("SELECT rowid FROM Name2Id WHERE user_name = ?", (talker_name,)).fetchone()
            if not row:
                raise SourceError(f"库里没有这个会话：{talker_name}")
            import hashlib

            digest = hashlib.md5(talker_name.encode("utf-8")).hexdigest()
            table = f"Msg_{digest}"
            lo = int(datetime.combine(start, datetime.min.time()).replace(tzinfo=CST).timestamp())
            hi = int(datetime.combine(end + timedelta(days=1), datetime.min.time()).replace(tzinfo=CST).timestamp())
            sql = (
                f"SELECT localId, MsgSvrID, Type, SubType, IsSender, CreateTime, StrTalker, StrContent "
                f"FROM {table} WHERE CreateTime >= ? AND CreateTime < ? ORDER BY CreateTime"
            )
            for r in conn.execute(sql, (lo, hi)):
                yield {
                    "localId": r[0],
                    "MsgSvrID": r[1],
                    "type": r[2],
                    "subType": r[3],
                    "isSender": r[4],
                    "createTime": r[5],
                    "sender": r[6] if not r[4] else "me",
                    "senderName": "" if not r[4] else "我",
                    "content": r[7],
                    "talkerName": talker_name,
                }
        finally:
            conn.close()


def collect(
    source: Any,
    group: str,
    aliases: list[str],
    days: int | None = None,
    since: str | None = None,
    until: str | None = None,
    roster_map: dict[str, str] | None = None,
    talker_id: str | None = None,
) -> list[dict[str, Any]]:
    """从任意 source 取数 → 过滤群 → 标准化，返回 UMF 列表（已去重）。"""
    from .base import dedupe

    if isinstance(source, ReplaySource):
        raw_iter = source.raw_records()
    else:
        end = parse_timestamp(until).date() if until else date.today()
        if days:
            start = end - timedelta(days=days)
        elif since:
            start = parse_timestamp(since).date()
        else:
            start = end - timedelta(days=7)
        raw_iter = source.raw_records(talker_id or group, start, end)

    out: list[dict[str, Any]] = []
    for raw in raw_iter:
        talker_name = raw.get("talkerName") or raw.get("group") or ""
        if isinstance(source, ReplaySource) and talker_name and not is_group_name_match(talker_name, group, aliases):
            continue
        msg = normalize_message(raw, default_group=group, roster_map=roster_map)
        if msg:
            out.append(msg)
    return dedupe(out)
