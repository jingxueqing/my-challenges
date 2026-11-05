"""fs_scan —— 把磁盘上的真实提交包扫成 Submission 记录。

为什么需要这个 adapter：
    群消息里的「提交」只是一条文件消息，附件本身不在消息库里。
    真正能验收的东西在磁盘上：19 个提交包、几百个文件。
    这个 adapter 直接对文件夹做扫描，把「真实提交」变成图里的节点，
    这样即使群消息还没有接上，提交矩阵也已经是真实数据。

扫描规则（与 config/challenges.yaml 的 naming.regex 一致）：
    1. 目录名以 C4A- / C4A_ 开头 → 整个目录归到该挑战
    2. 目录内文件名符合 姓名_C4A_内容.ext → 该文件是一个 artifact
    3. 同一 (学生, 挑战) 下的文件聚合成一条 Submission
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import Any

from ..config import ClassConfig

_DIR_CID = re.compile(r"^(?P<cid>C\d{1,2}[A-Z]{0,2})[\-_]")
MAX_DEPTH = 3
SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".idea", ".vscode"}


def _student_for(filename: str, cfg: ClassConfig) -> str | None:
    """从文件名（或任意路径片段）猜学生（返回 wxid）。"""
    base = os.path.basename(filename)
    for token in re.split(r"[_\-./\\]", base) + [base]:
        if not token:
            continue
        low = token.lower()
        for st in cfg.roster.students.values():
            names = {st.nickname, st.wxid, *st.aliases}
            if any(low == n.lower() for n in names if n):
                return st.wxid
    return None


def _student_for_path(dirpath: str, cfg: ClassConfig) -> str | None:
    """目录名里出现学生名（如 C2-交付_JingXueQing_AI4Math论文）也能认出来。"""
    for seg in reversed(dirpath.split(os.sep)):
        if not seg or seg in ("", ".", ".."):
            continue
        for token in re.split(r"[_\-]", seg):
            hit = _student_for(token, cfg)
            if hit:
                return hit
    return None


def _challenge_for(name: str, cfg: ClassConfig) -> str | None:
    m = _DIR_CID.match(name) or re.search(r"(?i)(?<![A-Za-z])(C\d{1,2}[A-Z]{0,2})(?![A-Za-z])", name)
    if not m:
        return None
    cid = m.group("cid") if "cid" in m.groupdict() else m.group(1)
    cid = cid.upper()
    return cid if cid in cfg.challenges else None


def _kind_for(filename: str, cfg: ClassConfig) -> str:
    parts = re.split(r"[_]", os.path.splitext(filename)[0])
    for part in reversed(parts):
        kind = cfg.normalize_kind(part)
        if kind != "deliverable" or part.lower() in {"交付物", "report"}:
            return kind
    return "deliverable"


def scan(root: str, cfg: ClassConfig, student_hint: str | None = None) -> list[dict[str, Any]]:
    """扫描 root，返回 Submission dict 列表。"""
    root = os.path.abspath(os.path.expanduser(root))
    if not os.path.isdir(root):
        raise FileNotFoundError(f"目录不存在：{root}")

    buckets: dict[tuple[str, str], dict[str, Any]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        depth = dirpath[len(root):].count(os.sep)
        if depth >= MAX_DEPTH:
            dirnames[:] = []
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        dir_cid = _challenge_for(os.path.basename(dirpath), cfg) if depth >= 0 else None
        for fname in filenames:
            if fname.startswith("."):
                continue
            path = os.path.join(dirpath, fname)
            # 学生归属：文件名 → 路径里任意一级目录名 → --owner 兜底
            wxid = _student_for(fname, cfg) or _student_for_path(dirpath, cfg) or student_hint
            cid = None
            m = cfg.naming_regex.match(fname)
            if m:
                cid = m.group("challenge").upper()
                wxid = wxid or _student_for(m.group("student"), cfg)
            cid = cid or dir_cid or _challenge_for(os.path.basename(dirpath), cfg)
            if not wxid or not cid or cid not in cfg.challenges:
                continue
            try:
                stat = os.stat(path)
            except OSError:
                continue
            kind = _kind_for(fname, cfg)
            key = (wxid, cid)
            bucket = buckets.setdefault(
                key,
                {"student": wxid, "challenge": cid, "artifacts": [], "root": root},
            )
            bucket["artifacts"].append(
                {
                    "kind": kind,
                    "file": os.path.relpath(path, root),
                    "bytes": stat.st_size,
                    "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

    out: list[dict[str, Any]] = []
    for (wxid, cid), bucket in sorted(buckets.items()):
        arts = sorted(bucket["artifacts"], key=lambda a: a["file"])
        kinds = {a["kind"] for a in arts}
        out.append(
            {
                "student": wxid,
                "student_nickname": (cfg.roster.get(wxid).nickname if cfg.roster.get(wxid) else wxid),
                "challenge": cid,
                "artifact_kinds": sorted(kinds),
                "artifact_count": len(arts),
                "bytes": sum(a["bytes"] for a in arts),
                "artifacts": arts,
                "source": "fs_scan",
                "root": bucket["root"],
                "latest_mtime": max(a["mtime"] for a in arts),
            }
        )
    return out


def real_students(submissions: list[dict[str, Any]]) -> set[str]:
    return {s["student"] for s in submissions}
