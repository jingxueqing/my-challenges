#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pipeline.py —— 扫描 + 归属 + 匹配 + 统计，一条命令产出全部结构化数据。

流程：
  1. discover_packages()  找出「提交包」目录（一次提交的最小单位）
  2. collect_candidates()  收集包内候选文件/目录（限制深度，跳过内部工程目录）
  3. attribute()           从文件名/路径判定 学生 + 挑战，并记录判定方式（可追溯）
  4. match_items()         与 specs.json 的交付项匹配（slug > glob > 槽位）
  5. quality()             命名合规、AI日志可读性、版本噪声、重复包
  6. enrich_review()       挂载 C4A 评审结果（评审集成）
  7. insights()            从数据里算出结论（不是堆图表）
  8. write_outputs()       JSON / CSV

口径约定（全部体现在输出字段里，评审可复核）：
  * 「提交时间」= 该提交包内文件的最大修改时间（本地无平台时间戳，见 provenance）
  * 「状态」complete=必填项全齐 / partial=缺必填项但有产出 / missing=无记录
  * 一个文件只满足一个交付项（贪心最优分配），避免一份文件被重复算作多项
"""
from __future__ import annotations

import csv
import fnmatch
import json
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import specs as spec_mod

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "JingXueQing_C6A_数据"
CONFIG = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))
SPECS = json.loads((DATA / "specs.json").read_text(encoding="utf-8"))

NAME_CH_RE = r"[\u4e00-\u9fa5A-Za-z][^_/]*"
NAME_RE = re.compile(rf"^({NAME_CH_RE})_(C\d+[A-Z]?)_(.+)$")
PKG_PREFIX = re.compile(r"^(C\d+[A-Z]?)-(交付|提交|提交数据仪表盘)_?(.*)$")
REVIEW_PKG = re.compile(r"^([A-Za-z\u4e00-\u9fa5][A-Za-z0-9\u4e00-\u9fa5]*)_(C\d+[A-Z]?)_(.+)$")
VERSION_SUFFIX = re.compile(r"(_v\d+|_V\d+|v\d+)$")


# ------------------------------------------------------------------ 基础工具
def canon_student(raw: str) -> str:
    aliases = CONFIG["student_aliases"]
    return aliases.get(raw, aliases.get(raw.lower(), raw))


def split_name(name: str) -> tuple[str, str] | None:
    m = NAME_RE.match(name)
    if not m:
        return None
    return m.group(1), m.group(2)


def slug_of(name: str) -> str | None:
    m = NAME_RE.match(name)
    return m.group(3) if m else None


def norm_slug(text: str) -> str:
    text = text.strip().lower().rstrip("/")
    text = re.sub(r"\s+", "", text)
    text = VERSION_SUFFIX.sub("", text)
    return text


def chal_key(cid: str) -> tuple[int, str]:
    """挑战排序：C1 < C2 < C2A < C2G < C3 < C3C < C4 …（数字优先，字母后缀其次）"""
    digits = re.sub(r"\D", "", cid) or "0"
    return int(digits), cid


def ts(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


# ------------------------------------------------------------------ 1. 发现提交包
def discover_packages() -> list[dict]:
    packages: list[dict] = []
    seen: set[str] = set()
    for root in CONFIG["roots"]:
        root_path = Path(root["path"])
        if not root_path.exists():
            print(f"[warn] 数据根不存在，跳过：{root_path}")
            continue
        children = sorted([p for p in root_path.iterdir() if p.is_dir() and not p.name.startswith(".")])
        only = root.get("include_only")  # 白名单：只认这几个子目录，避免把桌面上的杂项当成提交包
        if only:
            children = [c for c in children if c.name in only]
        for child in children:
            if child.name in CONFIG["ignore_dirs"]:
                continue
            if str(child) in seen:  # 内层根目录可能重复出现
                continue
            seen.add(str(child))
            challenge, student, method = None, None, ""
            patch = CONFIG["folder_owner_patches"].get(child.name, {})
            m = PKG_PREFIX.match(child.name)
            r = REVIEW_PKG.match(child.name)
            if m:
                challenge = m.group(1)
                tail = m.group(3)
                guess = tail.split("_")[0] if tail else ""
                student = canon_student(guess) if guess else None
                method = "folder_name"
            elif r:
                student = canon_student(r.group(1))
                challenge = r.group(2)
                method = "folder_name"
            if patch:
                student = patch.get("student", student)
                challenge = patch.get("challenge", challenge)
                method = "manual_patch"
            files = [p for p in child.rglob("*") if p.is_file()]
            if not files:
                continue
            if student is None:
                # 用包内文件名投票决定归属
                votes = Counter()
                for f in files[:400]:
                    parsed = split_name(f.name)
                    if parsed:
                        votes[canon_student(parsed[0])] += 1
                if votes:
                    student = votes.most_common(1)[0][0]
                    method = "filename_vote"
            packages.append({
                "path": str(child),
                "name": child.name,
                "root_label": root["label"],
                "root_kind": root["kind"],
                "student": student,
                "challenge": challenge,
                "attribution": method,
                "patch_reason": patch.get("reason", ""),
                "file_count": len(files),
            })
    return packages


# ------------------------------------------------------------------ 2. 收集候选
def collect_candidates(pkg: dict) -> tuple[list[dict], int]:
    root = Path(pkg["path"])
    ignore_dirs = set(CONFIG["ignore_dirs"])
    ignore_globs = CONFIG["ignore_file_globs"]
    max_depth = CONFIG["max_depth"]
    candidates: list[dict] = []
    deep = 0
    for current, dirs, files in os.walk(root):
        rel_dir = Path(current).relative_to(root)
        depth = 0 if rel_dir == Path(".") else len(rel_dir.parts)
        dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
        if depth + 1 > max_depth + 1:
            deep += len(files)
            dirs[:] = []
            continue
        for d in dirs:
            full = Path(current) / d
            candidates.append({
                "name": d, "rel_path": str(full.relative_to(root)), "is_dir": True,
                "size": 0, "mtime": ts(full),
                "file_count": sum(1 for _ in full.rglob("*") if _.is_file()),
            })
        # 跳过「嵌套的提交包」：里面的文件属于那个包，不属于当前包
        nested = [part for part in rel_dir.parts if REVIEW_PKG.match(part)]
        if nested:
            continue
        for f in files:
            if f.startswith("."):
                continue
            if any(fnmatch.fnmatch(f, g) for g in ignore_globs):
                continue
            full = Path(current) / f
            try:
                st = full.stat()
            except OSError:
                continue
            if depth + 1 > max_depth:
                deep += 1
                continue
            candidates.append({
                "name": f, "rel_path": str(full.relative_to(root)), "is_dir": False,
                "size": st.st_size, "mtime": ts(full), "file_count": 1,
            })
    return candidates, deep


# ------------------------------------------------------------------ 3. 归属
def attribute(pkg: dict, cand: dict) -> tuple[str | None, str | None, str]:
    parsed = split_name(cand["name"])
    if parsed:
        return canon_student(parsed[0]), parsed[1], "filename"
    # 目录里的文件名也可能带归属（如 真实评审输入/Elite20TA_C4_x/...）
    for part in Path(cand["rel_path"]).parts[:-1]:
        p2 = split_name(part)
        if p2:
            return canon_student(p2[0]), p2[1], "parent_dir"
    return pkg["student"], pkg["challenge"], pkg["attribution"] or "package"


# ------------------------------------------------------------------ 4. 匹配
def item_slot_for_file(fname: str) -> str | None:
    return spec_mod.norm_slot(fname, "file")


def score_match(item: dict, cand: dict) -> int:
    name = cand["name"]
    file_slug = slug_of(name)
    spec_slug = item.get("slug")
    if spec_slug:
        a, b = norm_slug(file_slug or ""), norm_slug(spec_slug)
        if a and b:
            if a == b:
                return 100
            if spec_slug.endswith("_") and a.startswith(b):
                return 92
            if a.rsplit(".", 1)[0] == b.rsplit(".", 1)[0]:
                return 96
            if a.startswith(b.rsplit(".", 1)[0]):
                return 88
    pat = item["pattern"]
    if item["match_type"] == "glob":
        base = pat.strip()
        if fnmatch.fnmatch(name.lower(), base.lower()):
            return 85
        if base.startswith("*") and base.endswith("*") and base.strip("*").lower() in name.lower():
            return 84
    slot = item_slot_for_file(name)
    if slot and slot == item["slot"]:
        return 60
    if cand["is_dir"] and slot and slot == item["slot"]:
        return 62
    return 0


def match_items(items: list[dict], cands: list[dict]) -> dict:
    triples = []
    for i_idx, item in enumerate(items):
        for c_idx, cand in enumerate(cands):
            s = score_match(item, cand)
            if s:
                triples.append((s, not item["required"], i_idx, c_idx))
    triples.sort(key=lambda t: (-t[0], t[1], t[2]))
    used_items, used_cands, assign = set(), set(), {}
    for score, _opt, i_idx, c_idx in triples:
        if i_idx in used_items or c_idx in used_cands:
            continue
        used_items.add(i_idx)
        used_cands.add(c_idx)
        assign[i_idx] = (c_idx, score)
    for c_idx, cand in enumerate(cands):
        cand["matched_item"] = None
        cand["match_score"] = 0
    for i_idx, (c_idx, score) in assign.items():
        cands[c_idx]["matched_item"] = items[i_idx]["label"]
        cands[c_idx]["match_score"] = score
    return assign


# ------------------------------------------------------------------ 5. 质量
def quality_flags(record: dict, cands: list[dict], assigned: dict, items: list[dict]) -> dict:
    matched = [c for c in cands if c.get("matched_item")]
    named = [c for c in matched if split_name(c["name"])]
    ai_item = next((i for i, it in enumerate(items) if it["slot"] == "ai_log"), None)
    ai_ok, ai_size = False, 0
    if ai_item is not None and ai_item in assigned:
        c = cands[assigned[ai_item][0]]
        ai_size = c["size"] or 0
        ai_ok = (not c["is_dir"]) and ai_size >= 300
    empty = [c["rel_path"] for c in cands if not c["is_dir"] and c["size"] == 0]
    versions = [c["rel_path"] for c in cands if VERSION_SUFFIX.search(slug_of(c["name"]) or c["name"].rsplit(".", 1)[0])]
    return {
        "naming_compliance": round(len(named) / len(matched), 3) if matched else 0.0,
        "n_matched": len(matched),
        "unnamed_files": [c["rel_path"] for c in cands if not c["is_dir"] and not split_name(c["name"])][:8],
        "ai_log_ok": ai_ok,
        "ai_log_size": ai_size,
        "empty_files": empty,
        "version_files": versions,
    }


# ------------------------------------------------------------------ 6. 评审集成
def load_review_scores() -> dict[str, dict]:
    cfg = CONFIG.get("review_integration", {})
    if not cfg.get("enabled"):
        return {}
    path = Path(cfg["source"])
    if not path.exists():
        print(f"[warn] 评审结果不存在：{path}")
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, dict] = {}
    for author in data.get("authors", []):
        key = canon_student(author["author"])
        out[key] = {
            "source": str(path),
            "rubric": data.get("rubric_version"),
            "composite": author.get("composite"),
            "rank": author.get("rank"),
            "file_count": author.get("file_count"),
            "completeness_score": author.get("completeness", {}).get("score"),
            "verdict": author.get("completeness", {}).get("verdict"),
            "missing_labels": author.get("completeness", {}).get("missing_labels", []),
        }
    return out


# ------------------------------------------------------------------ 7. 主流程
def build_records() -> tuple[list[dict], list[dict], list[dict]]:
    packages = discover_packages()
    print(f"[scan] 提交包 {len(packages)} 个")
    grouped: dict[tuple[str, str], dict] = {}
    pkg_rows: list[dict] = []
    for pkg in packages:
        cands, deep = collect_candidates(pkg)
        # 按 (学生, 挑战) 再分组：同一包里可能混有多人/多挑战
        buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
        for cand in cands:
            student, challenge, how = attribute(pkg, cand)
            if not student or not challenge or challenge not in SPECS:
                cand["attribution"] = how
                continue
            cand["attribution"] = how
            buckets[(student, challenge)].append(cand)
        pkg_rows.append({**pkg, "candidates": len(cands), "deep_files": deep,
                         "buckets": {f"{k[0]}|{k[1]}": len(v) for k, v in buckets.items()}})
        for (student, challenge), items_cand in buckets.items():
            key = (student, challenge)
            rec = grouped.setdefault(key, {"student": student, "challenge": challenge,
                                           "candidates": [], "packages": [], "deep": 0})
            rec["candidates"].extend(items_cand)
            rec["packages"].append(pkg["name"])
            rec["deep"] += deep

    rows: list[dict] = []
    for (student, challenge), rec in sorted(grouped.items()):
        spec = SPECS[challenge]
        items = spec["items"]
        cands = rec["candidates"]
        assigned = match_items(items, cands)
        missing = [it["label"] for i, it in enumerate(items) if it["required"] and i not in assigned]
        present_req = [it["label"] for i, it in enumerate(items) if it["required"] and i in assigned]
        opt_present = [it["label"] for i, it in enumerate(items) if not it["required"] and i in assigned]
        n_req = sum(1 for it in items if it["required"])
        completeness = round(len(present_req) / n_req, 3) if n_req else 0.0
        status = "complete" if not missing else ("partial" if present_req else "missing")
        times = sorted(c["mtime"] for c in cands)
        files = []
        for c in cands:
            files.append({
                "filename": c["name"],
                "rel_path": c["rel_path"],
                "is_dir": c["is_dir"],
                "size": c["size"],
                "mtime": c["mtime"],
                "category": spec_mod.SLOTS.get(item_slot_for_file(c["name"]) or "", ("未归类",))[0],
                "matched_item": c["matched_item"],
                "attribution": c["attribution"],
            })
        rows.append({
            "student": student,
            "challenge_id": challenge,
            "challenge_title": spec["title"],
            "submitted_at": times[-1],
            "first_file_at": times[0],
            "n_files": len(cands),
            "packages": rec["packages"],
            "duplicate_package": len(rec["packages"]) > 1,
            "items": [
                {
                    "label": it["label"],
                    "slot": it["slot"],
                    "slot_cn": it["slot_cn"],
                    "required": it["required"],
                    "present": i in assigned,
                    "file": cands[assigned[i][0]]["rel_path"] if i in assigned else None,
                    "confidence": assigned[i][1] if i in assigned else 0,
                    "origin": it["origin"],
                }
                for i, it in enumerate(items)
            ],
            "present_required": present_req,
            "optional_present": opt_present,
            "missing": missing,
            "completeness": completeness,
            "status": status,
            "quality": quality_flags(rec, cands, assigned, items),
            "files": files,
            "deep_files_not_counted": rec["deep"],
            "review": None,
        })
    return rows, packages, pkg_rows


def attach_reviews(rows: list[dict]) -> None:
    scores = load_review_scores()
    if not scores:
        return
    chal = CONFIG["review_integration"].get("challenge", "C4")
    for row in rows:
        if row["challenge_id"] == chal and row["student"] in scores:
            row["review"] = scores[row["student"]]


# ------------------------------------------------------------------ 8. 统计与洞察
def build_matrix(rows: list[dict], students: list[str]) -> dict:
    chals = sorted(SPECS.keys(), key=chal_key)
    index = {(r["student"], r["challenge_id"]): r for r in rows}
    matrix = []
    for s in students:
        cells = []
        for c in chals:
            r = index.get((s, c))
            cells.append({
                "challenge": c,
                "status": r["status"] if r else "missing",
                "completeness": r["completeness"] if r else 0.0,
                "submitted_at": r["submitted_at"] if r else None,
                "missing": r["missing"] if r else [i["label"] for i in SPECS[c]["items"] if i["required"]],
            })
        matrix.append({"student": s, "cells": cells})
    return {"challenges": [{"id": c, "title": SPECS[c]["title"], "n_required": SPECS[c]["n_required"]} for c in chals],
            "rows": matrix}


def build_insights(rows: list[dict], students: list[str], matrix: dict) -> list[dict]:
    n_students, n_chals = len(students), len(matrix["challenges"])
    total_cells = n_students * n_chals
    have = len(rows)
    complete = sum(1 for r in rows if r["status"] == "complete")
    partial = sum(1 for r in rows if r["status"] == "partial")
    all_missing_slots = Counter()
    for r in rows:
        for m in r["missing"]:
            all_missing_slots[m] += 1
    ai_missing = sum(1 for r in rows if any("AI日志" in m for m in r["missing"]))
    ai_bad = sum(1 for r in rows if not r["quality"]["ai_log_ok"] and not any("AI日志" in m for m in r["missing"]))
    naming = [r["quality"]["naming_compliance"] for r in rows]
    avg_naming = round(sum(naming) / len(naming), 3) if naming else 0
    dup = [r for r in rows if r["duplicate_package"]]
    versioned = sum(1 for r in rows if r["quality"]["version_files"])
    per_chal = Counter(r["challenge_id"] for r in rows)
    zero_chals = [c["id"] for c in matrix["challenges"] if per_chal.get(c["id"], 0) == 0]
    review_rows = [r for r in rows if r.get("review")]
    insights = [
        {
            "id": "coverage",
            "level": "warn",
            "title": f"覆盖率 {have}/{total_cells}：数据只覆盖 {n_students} 位提交者，不是全班",
            "evidence": f"{n_students} 位提交者 × {n_chals} 个挑战 = {total_cells} 个格子，实际有数据 {have} 个（{have/total_cells:.0%}）",
            "implication": "本机可核验的只有这些真实提交；缺的格子是「无数据」而不是「判定未交」，看板上必须区分，否则会误伤同学。",
        },
        {
            "id": "completeness",
            "level": "info",
            "title": f"有提交的 {have} 条记录里，{complete} 条必填项全齐（{complete/have:.0%}），{partial} 条缺件",
            "evidence": "按 CHALLENGE.md 抽取的必填项逐条比对得出",
            "implication": "缺件不是「没交」，而是「交了但少一样」——这才是最该被提醒的部分。",
        },
        {
            "id": "ai_log",
            "level": "danger" if (ai_missing or ai_bad) else "ok",
            "title": f"AI 日志是最硬的卡口：{ai_missing} 条记录缺 AI 日志，{ai_bad} 条 AI 日志过短（<300B）",
            "evidence": f"红线规则：无 AI 日志 → 复盘质量直接 ≤5 分；统计口径为文件大小与命中情况",
            "implication": "自动校验应该第一时间卡 AI 日志，而不是最后才查。",
        },
        {
            "id": "naming",
            "level": "warn" if avg_naming < 0.9 else "ok",
            "title": f"命名规范平均符合率 {avg_naming:.0%}，{len(dup)} 条记录存在重复提交包",
            "evidence": "重复包：" + ("、".join(f"{d['student']}/{d['challenge_id']}" for d in dup) or "无"),
            "implication": "命名不规范会让自动收集器漏人漏件，必须靠人工补丁兜底并留痕。",
        },
        {
            "id": "blind_spots",
            "level": "info",
            "title": f"{len(zero_chals)} 个挑战在本机零数据（{'、'.join(zero_chals[:8])}）",
            "evidence": "规格已抽取，但没有对应提交包",
            "implication": "规格是可以先建好的——数据可以后到，规则不该等数据。",
        },
    ]
    if review_rows:
        best = max(review_rows, key=lambda r: r["review"].get("composite") or 0)
        insights.append({
            "id": "review_integration",
            "level": "ok",
            "title": f"已接入 C4A 评审分：{len(review_rows)} 份 C4 提交有质量分，最高 {best['review'].get('composite')}",
            "evidence": "复用 C4A 技能输出的 评审结果.json（rubric " + str(best["review"].get("rubric")) + "）",
            "implication": "「交没交」和「交得好不好」是两个维度，接上评审分才敢给学生排名。",
        })
    return insights


# ------------------------------------------------------------------ 9. 输出
def write_outputs(rows: list[dict], packages: list[dict], pkg_rows: list[dict]) -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    students = sorted({r["student"] for r in rows} | set(CONFIG["students"].keys()))
    matrix = build_matrix(rows, students)
    insights = build_insights(rows, students, matrix)
    now = datetime.now().astimezone().isoformat(timespec="seconds")

    payload = {
        "schema_version": CONFIG["schema_version"],
        "generated_at": now,
        "provenance": {
            "roots": CONFIG["roots"],
            "challenge_doc_root": CONFIG["challenge_doc_root"],
            "scan_rules": {
                "max_depth": CONFIG["max_depth"],
                "ignore_dirs": CONFIG["ignore_dirs"],
                "submitted_at": "包内文件最大修改时间（本地无平台时间戳，属于近似口径）",
                "status_rule": "complete=必填全齐；partial=有产出但缺必填；missing=本机无该记录",
                "one_file_one_item": True,
            },
            "specs_origin": {cid: SPECS[cid]["origin"] for cid in SPECS},
            "review_integration": CONFIG.get("review_integration", {}),
            "caveats": [
                "只统计本机磁盘上真实存在的提交包，未包含群文件里未下载的提交",
                "WeChatGroup / Elite20TA 是提交包里的账号名，不是真实姓名，已原样保留",
                "C1 的提交包文件夹名不含姓名，归属用 folder_owner_patches 人工补丁，理由已记录",
            ],
        },
        "students": [
            {
                "name": s,
                **CONFIG["students"].get(s, {}),
                "n_submitted": sum(1 for r in rows if r["student"] == s),
                "n_complete": sum(1 for r in rows if r["student"] == s and r["status"] == "complete"),
                "avg_completeness": round(
                    sum(r["completeness"] for r in rows if r["student"] == s) /
                    max(1, sum(1 for r in rows if r["student"] == s)), 3),
            }
            for s in students
        ],
        "challenges": [
            {
                "id": cid,
                "title": SPECS[cid]["title"],
                "n_required": SPECS[cid]["n_required"],
                "n_items": SPECS[cid]["n_items"],
                "origin": SPECS[cid]["origin"],
                "source_file": SPECS[cid]["source_file"],
                "items": SPECS[cid]["items"],
                "n_submitters": sum(1 for r in rows if r["challenge_id"] == cid),
            }
            for cid in sorted(SPECS.keys(), key=chal_key)
        ],
        "matrix": matrix,
        "records": sorted(rows, key=lambda r: (r["student"], r["challenge_id"])),
        "packages": pkg_rows,
        "insights": insights,
        "stats": {
            "n_students": len(students),
            "n_challenges": len(SPECS),
            "n_packages": len(packages),
            "n_records": len(rows),
            "n_files": sum(r["n_files"] for r in rows),
            "n_complete": sum(1 for r in rows if r["status"] == "complete"),
            "n_partial": sum(1 for r in rows if r["status"] == "partial"),
            "avg_completeness": round(sum(r["completeness"] for r in rows) / max(1, len(rows)), 3),
        },
    }
    (DATA / "submissions.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # matrix.csv
    with (DATA / "matrix.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["学生"] + [c["id"] for c in matrix["challenges"]] + ["已提交", "完整", "平均完整度"])
        for row in matrix["rows"]:
            marks = [{"complete": "✅", "partial": "⚠️", "missing": "❌"}[c["status"]] for c in row["cells"]]
            recs = [r for r in rows if r["student"] == row["student"]]
            w.writerow([row["student"]] + marks + [
                len(recs), sum(1 for r in recs if r["status"] == "complete"),
                round(sum(r["completeness"] for r in recs) / max(1, len(recs)), 3)])

    # records.csv / files.csv
    with (DATA / "records.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["学生", "挑战", "挑战名", "状态", "完整度", "必填项数", "已交必填项", "缺失项",
                    "文件数", "提交时间(近似)", "提交包数", "命名合规率", "AI日志可用", "评审分"])
        for r in sorted(rows, key=lambda r: (r["student"], r["challenge_id"])):
            w.writerow([r["student"], r["challenge_id"], r["challenge_title"], r["status"], r["completeness"],
                        len(r["items"]), len(r["present_required"]), " / ".join(r["missing"]) or "-",
                        r["n_files"], r["submitted_at"], len(r["packages"]),
                        r["quality"]["naming_compliance"], "是" if r["quality"]["ai_log_ok"] else "否",
                        (r["review"] or {}).get("composite", "-")])
    with (DATA / "files.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["学生", "挑战", "文件名", "相对路径", "类型", "大小(字节)", "修改时间", "归类", "命中的交付项"])
        for r in rows:
            for f in r["files"]:
                w.writerow([r["student"], r["challenge_id"], f["filename"], f["rel_path"],
                            "目录" if f["is_dir"] else "文件", f["size"], f["mtime"],
                            f["category"], f["matched_item"] or "-"])

    # challenge_stats.csv
    with (DATA / "challenge_stats.csv").open("w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["挑战", "标题", "必填项数", "提交人数", "完整条数", "平均完整度", "规格来源"])
        for c in payload["challenges"]:
            recs = [r for r in rows if r["challenge_id"] == c["id"]]
            w.writerow([c["id"], c["title"], c["n_required"], len(recs),
                        sum(1 for r in recs if r["status"] == "complete"),
                        round(sum(r["completeness"] for r in recs) / max(1, len(recs)), 3), c["origin"]])

    print(f"[data] 记录 {len(rows)} 条 / 学生 {len(students)} 位 / 挑战 {len(SPECS)} 个 / 文件 {payload['stats']['n_files']} 个")
    print(f"[data] 状态：完整 {payload['stats']['n_complete']} / 缺件 {payload['stats']['n_partial']} / 平均完整度 {payload['stats']['avg_completeness']:.0%}")
    return payload


def main() -> int:
    rows, packages, pkg_rows = build_records()
    attach_reviews(rows)
    write_outputs(rows, packages, pkg_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
