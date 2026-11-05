"""Property Graph 存储层。

设计取舍（见 docs/架构.md 第 4 节）：
    - 需求是「20 学生 × 8 挑战 + 上千条消息」的量级，Neo4j 属于杀鸡用牛刀，
      而且要求客户机器上再装一个服务，交付成本高。
    - 所以用 SQLite 实现 property graph：nodes / edges 两张表 + props 存 JSON，
      外加 FTS5 全文索引做「关于 GitHub 的常见问题有哪些」这类检索。
    - 接口保持图语义（add_node / add_edge / neighbors / path），
      换后端只要重写这个类，上层 skill 不用改。
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

CST = timezone(timedelta(hours=8))

_SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id         TEXT PRIMARY KEY,
    type       TEXT NOT NULL,
    props      TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);

CREATE TABLE IF NOT EXISTS edges (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    type       TEXT NOT NULL,
    src        TEXT NOT NULL,
    dst        TEXT NOT NULL,
    props      TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_uniq ON edges(type, src, dst);
CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src, type);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst, type);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def now_iso() -> str:
    return datetime.now(CST).isoformat(timespec="seconds")


class GraphStore:
    def __init__(self, path: str):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        # 这个库是「可重建的派生数据」：源真相在 out/*.jsonl，graph.db 随时能 rm 重跑。
        # 所以把回滚日志放内存、关掉逐次 fsync——upsert_node/add_edge 每条都 commit，
        # 默认配置下一次重建要 ~1100 次 fsync；关掉后既快一个数量级，
        # 也不会因为磁盘瞬时 IO 抖动导致整条流水线失败（本机实测踩过一次 disk I/O error）。
        # 代价：进程被 kill 时可能留下半截库。删掉重跑几秒的事，不值得为它付 fsync 的钱。
        self.conn.execute("PRAGMA journal_mode=MEMORY")
        self.conn.execute("PRAGMA synchronous=OFF")
        self.conn.executescript(_SCHEMA)
        self.has_fts = self._init_fts()
        self.conn.commit()

    # ---------- 初始化 ----------
    def _init_fts(self) -> bool:
        try:
            self.conn.execute(
                "CREATE VIRTUAL TABLE IF NOT EXISTS node_fts "
                "USING fts5(id UNINDEXED, type UNINDEXED, text)"
            )
            return True
        except sqlite3.OperationalError:
            return False

    # ---------- 节点 / 边 ----------
    def upsert_node(self, node_id: str, node_type: str, props: dict[str, Any] | None = None) -> None:
        props = props or {}
        row = self.conn.execute("SELECT props FROM nodes WHERE id = ?", (node_id,)).fetchone()
        merged: dict[str, Any] = {}
        if row:
            try:
                merged = json.loads(row["props"])
            except json.JSONDecodeError:
                merged = {}
        merged.update(props)
        payload = json.dumps(merged, ensure_ascii=False, sort_keys=True)
        self.conn.execute(
            "INSERT INTO nodes(id, type, props, updated_at) VALUES(?,?,?,?) "
            "ON CONFLICT(id) DO UPDATE SET type=excluded.type, props=excluded.props, updated_at=excluded.updated_at",
            (node_id, node_type, payload, now_iso()),
        )
        if self.has_fts:
            text = " ".join(str(v) for v in merged.values() if isinstance(v, (str, int, float)))
            self.conn.execute("DELETE FROM node_fts WHERE id = ?", (node_id,))
            self.conn.execute(
                "INSERT INTO node_fts(id, type, text) VALUES(?,?,?)", (node_id, node_type, text)
            )
        self.conn.commit()

    def upsert_many(self, rows: Iterable[tuple[str, str, dict[str, Any]]]) -> int:
        n = 0
        for node_id, node_type, props in rows:
            self.upsert_node(node_id, node_type, props)
            n += 1
        return n

    def add_edge(self, edge_type: str, src: str, dst: str, props: dict[str, Any] | None = None) -> None:
        self.conn.execute(
            "INSERT INTO edges(type, src, dst, props, created_at) VALUES(?,?,?,?,?) "
            "ON CONFLICT(type, src, dst) DO UPDATE SET props=excluded.props",
            (edge_type, src, dst, json.dumps(props or {}, ensure_ascii=False), now_iso()),
        )
        self.conn.commit()

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        row = self.conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        return self._row_to_node(row) if row else None

    def nodes(self, node_type: str | None = None) -> list[dict[str, Any]]:
        if node_type:
            rows = self.conn.execute("SELECT * FROM nodes WHERE type = ? ORDER BY id", (node_type,))
        else:
            rows = self.conn.execute("SELECT * FROM nodes ORDER BY type, id")
        return [self._row_to_node(r) for r in rows]

    def neighbors(self, node_id: str, edge_type: str | None = None, direction: str = "out") -> list[dict[str, Any]]:
        sql, args = "", ()
        if direction == "out":
            sql = "SELECT dst AS nid, type, props FROM edges WHERE src = ?"
        elif direction == "in":
            sql = "SELECT src AS nid, type, props FROM edges WHERE dst = ?"
        else:
            sql = (
                "SELECT dst AS nid, type, props FROM edges WHERE src = ? "
                "UNION ALL SELECT src AS nid, type, props FROM edges WHERE dst = ?"
            )
        if edge_type:
            sql += " AND type = ?"
            args = (node_id, edge_type)
        else:
            args = (node_id,) if direction != "both" else (node_id, node_id)
        out = []
        for r in self.conn.execute(sql, args):
            node = self.get_node(r["nid"])
            if node:
                out.append({**node, "edge": r["type"], "edge_props": json.loads(r["props"] or "{}")})
        return out

    def search(self, text: str, node_type: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        """全文检索，失败时退化为 LIKE。"""
        query = (text or "").strip()
        if not query:
            return []
        if self.has_fts:
            try:
                tokens = [t for t in query.replace("\"", " ").split() if t]
                match = " AND ".join(tokens)
                sql = "SELECT id FROM node_fts WHERE node_fts MATCH ?"
                args: list[Any] = [match]
                if node_type:
                    sql += " AND type = ?"
                    args.append(node_type)
                sql += " LIMIT ?"
                args.append(limit)
                ids = [r["id"] for r in self.conn.execute(sql, args)]
                return [n for n in (self.get_node(i) for i in ids) if n]
            except sqlite3.OperationalError:
                pass
        sql = "SELECT * FROM nodes WHERE props LIKE ?"
        args = [f"%{query}%"]
        if node_type:
            sql += " AND type = ?"
            args.append(node_type)
        sql += " LIMIT ?"
        args.append(limit)
        return [self._row_to_node(r) for r in self.conn.execute(sql, args)]

    # ---------- meta / checkpoint ----------
    def set_meta(self, key: str, value: Any) -> None:
        self.conn.execute(
            "INSERT INTO meta(key, value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, json.dumps(value, ensure_ascii=False)),
        )
        self.conn.commit()

    def get_meta(self, key: str, default: Any = None) -> Any:
        row = self.conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    # ---------- 统计 ----------
    def stats(self) -> dict[str, int]:
        out = {r["type"]: r["c"] for r in self.conn.execute("SELECT type, COUNT(*) AS c FROM nodes GROUP BY type")}
        out["_edges"] = self.conn.execute("SELECT COUNT(*) AS c FROM edges").fetchone()["c"]
        return out

    def counts_by_edge(self) -> dict[str, int]:
        return {r["type"]: r["c"] for r in self.conn.execute("SELECT type, COUNT(*) AS c FROM edges GROUP BY type")}

    def vacuum(self) -> None:
        """整理碎片：反复 ingest 会留下空闲页，文件只涨不缩。

        实测：同一个库连跑多次涨到 836K，整理后回到 520K（全新重建）/ 656K（原地重写）。
        每次重建都调一次，免得同一份数据跑十次十个体积，看的人以为里面多了东西。
        """
        self.conn.execute("VACUUM")

    @staticmethod
    def _row_to_node(row: sqlite3.Row) -> dict[str, Any]:
        try:
            props = json.loads(row["props"])
        except json.JSONDecodeError:
            props = {}
        return {"id": row["id"], "type": row["type"], "props": props, "updated_at": row["updated_at"]}

    def close(self) -> None:
        self.conn.close()
