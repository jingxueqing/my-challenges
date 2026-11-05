"""L2/L3 提交检测器：消息里的提交 + 磁盘上的真实文件 → 一张学���×挑战矩阵。

判定逻辑（和老师手工验收的顺序一致）：
    1. 这是一条文件消息吗？→ 是，才可能是提交
    2. 文件名能解析出挑战 ID 吗？→ 能，归属该挑战；不能，用消息的 challenge_ref
    3. 必备件齐吗？（挑战配置里的 required）→ 缺件就标 needs_revision，并列出缺什么
    4. 命名规范吗？→ 不规范单独记一条 issue（这是老师最常打回的原因）

关键取舍：以文件为准，消息只补时间线。
    因为「在群里说交了」不等于交了，能验收的只有文件。
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .config import ClassConfig

_KIND_HINTS = (
    ("proposal", ("proposal", "申请书")),
    ("demo", ("demo", "原型", "prototype")),
    ("ailog", ("AI日志", "ai日志", "ailog", "AI协作日志", "AI_LOG")),
    ("notes", ("拿来说明", "参考", "引用")),
    ("aar", ("AAR", "aar", "复盘")),
    ("deliverable", ("交付物", "方案设计", "教学说明", "数据说明", "report", "报告")),
)


def _kind_from_name(name: str, cfg: ClassConfig) -> str:
    low = name.lower()
    for kind, hints in _KIND_HINTS:
        if any(h.lower() in low for h in hints):
            return kind
    return "deliverable"


def _artifact_id(student: str, cid: str, name: str) -> str:
    digest = hashlib.sha1(f"{student}|{cid}|{name}".encode("utf-8")).hexdigest()[:10]
    return f"artifact:{digest}"


def build(
    linked: list[dict[str, Any]],
    cfg: ClassConfig,
    fs_submissions: list[dict[str, Any]] | None = None,
    class_size: int | None = None,
) -> dict[str, Any]:
    class_size = class_size or len(cfg.roster)
    buckets: dict[tuple[str, str], dict[str, Any]] = {}

    def bucket(student: str, cid: str) -> dict[str, Any]:
        key = (student, cid)
        if key not in buckets:
            buckets[key] = {
                "student": student,
                "nickname": cfg.roster.get(student).nickname if cfg.roster.get(student) else student,
                "challenge": cid,
                "challenge_name": cfg.challenges[cid].name_cn if cid in cfg.challenges else cid,
                "artifacts": [],
                "issues": [],
                "first_ts": None,
                "last_ts": None,
                "sources": set(),
            }
        return buckets[key]

    # ---- 1. 消息里的提交 ----
    for msg in linked:
        if msg.get("intent") != "submission" or msg.get("type") != "file":
            continue
        student = msg["sender"]["wechat_id"]
        if student not in cfg.roster.students:
            continue  # 老师或其他人的文件不算学生提交
        name = (msg.get("content") or "").strip()
        m = cfg.naming_regex.match(name)
        cid = None
        if m and m.group("challenge").upper() in cfg.challenges:
            cid = m.group("challenge").upper()
            kind = cfg.normalize_kind(m.group("kind"))
        else:
            cid = msg.get("challenge_ref")
            kind = _kind_from_name(name, cfg)
        if not cid or cid not in cfg.challenges:
            continue
        b = bucket(student, cid)
        b["sources"].add("wechat")
        b["artifacts"].append(
            {
                "id": _artifact_id(student, cid, name),
                "kind": kind,
                "file": name,
                "source": "wechat",
                "msg_id": msg["msg_id"],
                "ts": msg["timestamp"],
                "naming_ok": bool(m),
            }
        )
        if not m:
            b["issues"].append(f"命名不规范：{name}（应为 姓名_{cid}_内容.md）")
        ts = msg["timestamp"]
        if b["first_ts"] is None or ts < b["first_ts"]:
            b["first_ts"] = ts
        if b["last_ts"] is None or ts > b["last_ts"]:
            b["last_ts"] = ts

    # ---- 2. 磁盘上的真实提交包 ----
    for fs in fs_submissions or []:
        student, cid = fs["student"], fs["challenge"]
        if student not in cfg.roster.students or cid not in cfg.challenges:
            continue
        b = bucket(student, cid)
        b["sources"].add("disk")
        for art in fs.get("artifacts", []):
            b["artifacts"].append(
                {
                    "id": _artifact_id(student, cid, art["file"]),
                    "kind": art["kind"],
                    "file": art["file"],
                    "source": "disk",
                    "bytes": art.get("bytes"),
                    "ts": art.get("mtime"),
                    "naming_ok": any(art["file"].startswith(prefix) for prefix in ("JingXueQing", "景雪晴"))
                    or "_" in art["file"],
                }
            )
        if fs.get("latest_mtime"):
            if b["last_ts"] is None or fs["latest_mtime"] > b["last_ts"]:
                b["last_ts"] = fs["latest_mtime"]

    # ---- 3. 汇总：缺件、状态、完整度 ----
    rows: list[dict[str, Any]] = []
    for (student, cid), b in sorted(buckets.items()):
        required = cfg.challenges[cid].required
        kinds = {a["kind"] for a in b["artifacts"]}
        missing = [k for k in required if k not in kinds]
        completeness = round((len(required) - len(missing)) / len(required), 3) if required else 1.0
        if missing:
            status = "needs_revision"
        elif any(not a["naming_ok"] for a in b["artifacts"]):
            status = "reviewing"
        else:
            status = "accepted"
        rows.append(
            {
                "id": f"submission:{student}:{cid}",
                "student": student,
                "nickname": b["nickname"],
                "major": cfg.roster.get(student).major if cfg.roster.get(student) else "",
                "challenge": cid,
                "challenge_name": b["challenge_name"],
                "required": list(required),
                "kinds": sorted(kinds),
                "missing": missing,
                "completeness": completeness,
                "status": status,
                "artifact_count": len(b["artifacts"]),
                "artifacts": sorted(b["artifacts"], key=lambda a: (a["kind"], a["file"])),
                "issues": b["issues"],
                "sources": sorted(b["sources"]),
                "first_ts": b["first_ts"],
                "last_ts": b["last_ts"],
            }
        )

    # ---- 4. 矩阵与按挑战统计 ----
    matrix: dict[str, dict[str, str]] = {s.wxid: {} for s in cfg.roster.students.values()}
    for r in rows:
        matrix[r["student"]][r["challenge"]] = r["status"]

    by_challenge: dict[str, dict[str, Any]] = {}
    for cid in cfg.challenge_order:
        submitted = sum(1 for r in rows if r["challenge"] == cid)
        complete = sum(1 for r in rows if r["challenge"] == cid and r["status"] == "accepted")
        by_challenge[cid] = {
            "name": cfg.challenges[cid].name_cn,
            "zone": cfg.challenges[cid].name_en,
            "submitted": submitted,
            "complete": complete,
            "expected": class_size,
            "rate_all": round(submitted / class_size, 3) if class_size else 0,
            "due": cfg.challenges[cid].due,
        }

    by_student: dict[str, dict[str, Any]] = {}
    for st in cfg.roster.students.values():
        mine = [r for r in rows if r["student"] == st.wxid]
        by_student[st.wxid] = {
            "nickname": st.nickname,
            "challenge_count": len(mine),
            "accepted": sum(1 for r in mine if r["status"] == "accepted"),
            "needs_revision": sum(1 for r in mine if r["status"] == "needs_revision"),
        }

    missing_items = [
        {
            "student": r["student"],
            "nickname": r["nickname"],
            "challenge": r["challenge"],
            "missing": r["missing"],
            "status": r["status"],
        }
        for r in rows
        if r["missing"]
    ]

    return {
        "class_size": class_size,
        "student_count": len({r["student"] for r in rows}),
        "submission_count": len(rows),
        "artifact_count": sum(r["artifact_count"] for r in rows),
        "complete_count": sum(1 for r in rows if r["status"] == "accepted"),
        "needs_revision_count": sum(1 for r in rows if r["status"] == "needs_revision"),
        "rows": rows,
        "matrix": matrix,
        "by_challenge": by_challenge,
        "by_student": by_student,
        "missing_required": missing_items,
        "cells": len(cfg.roster) * len(cfg.challenge_order),
    }
