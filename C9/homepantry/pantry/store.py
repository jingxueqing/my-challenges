"""存储层：单文件 SQLite，数据不出设备。

选 SQLite 而不是 JSON 文件：需要「用过/扔过」的事件流来算浪费账本，
也需要并发读（手机开着页面、CLI 同时在跑）。
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from . import lexicon
from .model import Item, parse_date

DEFAULT_DB = Path(os.environ.get("PANTRY_DB", Path.home() / ".homepantry" / "pantry.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  qty REAL NOT NULL DEFAULT 1,
  unit TEXT DEFAULT '',
  location TEXT DEFAULT '冷藏',
  added TEXT NOT NULL,
  expires TEXT,
  cat TEXT DEFAULT '未知',
  note TEXT DEFAULT '',
  source TEXT DEFAULT 'manual',
  track TEXT DEFAULT 'expiry',
  state TEXT DEFAULT 'in'
);
CREATE INDEX IF NOT EXISTS idx_items_name ON items(name);
CREATE INDEX IF NOT EXISTS idx_items_state ON items(state);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  kind TEXT NOT NULL,
  item_id INTEGER,
  name TEXT NOT NULL,
  qty REAL,
  unit TEXT,
  days_left INTEGER
);

CREATE TABLE IF NOT EXISTS shopping (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  qty REAL DEFAULT 1,
  unit TEXT DEFAULT '',
  source TEXT DEFAULT '',
  why TEXT DEFAULT '[]',
  done INTEGER DEFAULT 0,
  created TEXT NOT NULL
);
"""


def _row_to_item(r: sqlite3.Row) -> Item:
    return Item(
        id=r["id"], name=r["name"], qty=r["qty"], unit=r["unit"] or "",
        location=r["location"] or "冷藏",
        added=parse_date(r["added"]) or date.today(),
        expires=parse_date(r["expires"]) if r["expires"] else None,
        cat=r["cat"] or "未知", note=r["note"] or "", source=r["source"] or "manual",
        track=r["track"] or "expiry",
    )


class Store:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else DEFAULT_DB
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # ---------- 写入 ----------
    def add(self, item: Item) -> int:
        cur = self.conn.execute(
            "INSERT INTO items(name,qty,unit,location,added,expires,cat,note,source,track,state)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,'in')",
            (item.name, item.qty, item.unit, item.location, item.added.isoformat(),
             item.expires.isoformat() if item.expires else None,
             item.cat, item.note, item.source, item.track),
        )
        self._event("add", item.name, item.qty, item.unit, item.days_left())
        self.conn.commit()
        return int(cur.lastrowid)

    def add_many(self, items: list[Item]) -> list[int]:
        return [self.add(i) for i in items]

    def _event(self, kind: str, name: str, qty: float, unit: str,
               days_left: int | None = None, item_id: int | None = None) -> None:
        self.conn.execute(
            "INSERT INTO events(ts,kind,item_id,name,qty,unit,days_left) VALUES(?,?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), kind, item_id, name, qty, unit, days_left),
        )

    def consume(self, item_id: int, amount: float | None = None) -> dict:
        it = self.get(item_id)
        if not it:
            return {"ok": False, "error": "没有这个条目"}
        take = it.qty if amount is None else min(amount, it.qty)
        left = max(it.qty - take, 0.0)
        self.conn.execute("UPDATE items SET qty=?, state=? WHERE id=?",
                          (left, "gone" if left <= 0 else "in", item_id))
        self._event("use", it.name, take, it.unit, it.days_left(), item_id)
        self.conn.commit()
        return {"ok": True, "name": it.name, "used": take, "left": left}

    def waste(self, item_id: int, today: date | None = None) -> dict:
        it = self.get(item_id)
        if not it:
            return {"ok": False, "error": "没有这个条目"}
        left = it.days_left(today)
        self.conn.execute("UPDATE items SET state='gone' WHERE id=?", (item_id,))
        self._event("waste", it.name, it.qty, it.unit, left, item_id)
        self.conn.commit()
        return {"ok": True, "name": it.name, "wasted": it.qty, "days_left": left}

    def remove(self, item_id: int) -> None:
        self.conn.execute("UPDATE items SET state='gone' WHERE id=?", (item_id,))
        self.conn.commit()

    # ---------- 读取 ----------
    def items(self, include_gone: bool = False) -> list[Item]:
        q = "SELECT * FROM items WHERE state='in' ORDER BY id DESC"
        if include_gone:
            q = "SELECT * FROM items ORDER BY id DESC"
        return [_row_to_item(r) for r in self.conn.execute(q)]

    def get(self, item_id: int) -> Item | None:
        r = self.conn.execute("SELECT * FROM items WHERE id=? AND state='in'", (item_id,)).fetchone()
        return _row_to_item(r) if r else None

    def events(self, kind: str | None = None, days: int = 30) -> list[dict]:
        since = (date.today() - timedelta(days=days)).isoformat()
        if kind:
            rows = self.conn.execute(
                "SELECT * FROM events WHERE kind=? AND ts>=? ORDER BY id DESC", (kind, since))
        else:
            rows = self.conn.execute("SELECT * FROM events WHERE ts>=? ORDER BY id DESC", (since,))
        return [dict(r) for r in rows]

    # ---------- 购物清单 ----------
    def sync_shopping(self, rows: list[dict]) -> None:
        for r in rows:
            exist = self.conn.execute("SELECT id,done FROM shopping WHERE name=?", (r["name"],)).fetchone()
            if exist:
                if exist["done"]:
                    continue
                self.conn.execute("UPDATE shopping SET qty=?,unit=?,source=?,why=? WHERE id=?",
                                  (r["qty"], r["unit"], r["source"], json.dumps(r["why"], ensure_ascii=False),
                                   exist["id"]))
            else:
                self.conn.execute(
                    "INSERT INTO shopping(name,qty,unit,source,why,done,created) VALUES(?,?,?,?,?,0,?)",
                    (r["name"], r["qty"], r["unit"], r["source"],
                     json.dumps(r["why"], ensure_ascii=False), date.today().isoformat()),
                )
        self.conn.commit()

    def shopping_list(self, include_done: bool = True) -> list[dict]:
        q = "SELECT * FROM shopping ORDER BY done, id"
        if not include_done:
            q = "SELECT * FROM shopping WHERE done=0 ORDER BY id"
        out = []
        for r in self.conn.execute(q):
            d = dict(r)
            d["why"] = json.loads(d["why"] or "[]")
            out.append(d)
        return out

    def toggle_shopping(self, sid: int, done: bool) -> dict | None:
        self.conn.execute("UPDATE shopping SET done=? WHERE id=?", (1 if done else 0, sid))
        self.conn.commit()
        r = self.conn.execute("SELECT * FROM shopping WHERE id=?", (sid,)).fetchone()
        return dict(r) if r else None

    # ---------- 统计 ----------
    def stats(self, today: date | None = None) -> dict:
        today = today or date.today()
        items = self.items()
        live = [i for i in items if i.qty > 0]
        expired = [i for i in live if i.status(today) == "expired"]
        waste_events = self.events("waste", days=30)
        use_events = self.events("use", days=30)
        from . import expire as _expire
        return {
            "items": len(live),
            "by_location": {loc: len([i for i in live if i.location == loc])
                            for loc in ["冷藏", "冷冻", "常温", "橱柜", "阳台"]},
            "expired": len(expired),
            "soon": len([i for i in live if i.status(today) in ("today", "urgent", "soon")]),
            "level_low": len(_expire.level_alerts(items)),
            "waste_30d": len(waste_events),
            "waste_qty_30d": round(sum(e["qty"] or 0 for e in waste_events), 2),
            "use_30d": len(use_events),
            "waste_rate_30d": round(len(waste_events) / max(len(use_events) + len(waste_events), 1), 3),
            "catalog_size": len(lexicon.all_names()),
        }

    def reset(self) -> None:
        self.conn.executescript("DELETE FROM items; DELETE FROM events; DELETE FROM shopping;")
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
