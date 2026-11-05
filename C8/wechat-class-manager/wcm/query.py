"""L3 自然语言查询：老师用一句话问，Agent 查图后回结构化答案。

不做「大模型自由发挥」的原因：
    老师问的是事实（谁没交、谁最活跃），错一个名字就没人敢用了。
    所以走「意图路由 + 图查询」，答案里的每个数字都能点回节点 id；
    LLM 只在最后一步把结果润色成人话（可选，默认关闭）。

支持的问题类型见 INTENTS。
"""

from __future__ import annotations

import re
from typing import Any

from .config import KIND_CN, ClassConfig
from .store import GraphStore

INTENTS = (
    "missing_for_challenge",
    "student_submissions",
    "challenge_rate",
    "top_active",
    "silent_students",
    "profile",
    "faq",
    "mentoring",
    "deadline",
    "overview",
    "search",
)


def _students(store: GraphStore) -> list[dict[str, Any]]:
    return store.nodes("Student")


def _find_student(store: GraphStore, cfg: ClassConfig, question: str) -> dict[str, Any] | None:
    for st in _students(store):
        name = st["props"].get("name", "")
        if name and name in question:
            return st
        wxid = st["props"].get("wxid", "")
        if wxid and wxid in question:
            return st
    hit = cfg.roster.resolve(question.strip())
    if hit:
        return store.get_node(f"student:{hit.wxid}")
    return None


def _find_challenge(cfg: ClassConfig, question: str) -> str | None:
    m = re.search(r"(?i)(?<![A-Za-z])C(\d{1,2})([A-Z]{0,2})(?![A-Za-z])", question)
    if m:
        cid = f"C{m.group(1)}{m.group(2).upper()}"
        if cid in cfg.challenges:
            return cid
    for cid, ch in cfg.challenges.items():
        if ch.name_cn and ch.name_cn in question:
            return cid
    return None


def route(question: str) -> str:
    q = question.strip()
    if re.search(r"(没交|未提交|谁没|还差谁|还有谁)", q):
        return "missing_for_challenge"
    if re.search(r"(提交率|完成率|交了多|覆盖率)", q):
        return "challenge_rate"
    if re.search(r"(沉默|不活跃|潜水|没发言|零发言)", q):
        return "silent_students"
    if re.search(r"(帮了谁|谁帮|互助|结对)", q):
        return "mentoring"
    if re.search(r"(最活跃|活跃度|排名|top\s*\d*|谁最)", q, re.I):
        return "top_active"
    if re.search(r"(提交了哪些|交了哪些|提交情况|交了什么|进度如何)", q):
        return "student_submissions"
    if re.search(r"(画像|擅长|强项|了解.*同学|这个人)", q):
        return "profile"
    if re.search(r"(常见问题|faq|问得最多|关于.*问题|大家.*问)", q, re.I):
        return "faq"
    if re.search(r"(帮了谁|谁帮|互助|协作|带)", q):
        return "mentoring"
    if re.search(r"(截止|deadline|什么时候交|due)", q, re.I):
        return "deadline"
    if re.search(r"(整体|状态|概况|情况|怎么样|总结|班级)", q):
        return "overview"
    return "search"


def answer(store: GraphStore, cfg: ClassConfig, question: str) -> dict[str, Any]:
    intent = route(question)
    handler = globals()[f"_handle_{intent}"]
    result = handler(store, cfg, question)
    result.setdefault("question", question)
    result["intent"] = intent
    return result


def _subs(store: GraphStore) -> list[dict[str, Any]]:
    return store.nodes("Submission")


def _handle_missing_for_challenge(store, cfg, q) -> dict[str, Any]:
    cid = _find_challenge(cfg, q)
    if not cid:
        return {"answer": "要问哪个挑战？例如「C4B 还有谁没交」。", "data": [], "evidence": [], "confidence": 0.3}
    submitted = {s["props"]["student_id"] for s in _subs(store) if s["props"]["challenge"] == cid}
    missing = [st for st in _students(store) if st["props"]["wxid"] not in submitted]
    names = [st["props"]["name"] for st in missing]
    stat = store.get_node(f"challenge:{cid}")["props"]
    lines = [
        f"**{cid}（{stat.get('name_cn')}）还差 {len(names)} 人**，已交 {len(submitted)}/{len(cfg.roster)}。",
        "",
        "未交名单：" + ("、".join(names) if names else "无"),
        "",
        f"挑战要求：{'、'.join(KIND_CN.get(k, k) for k in (stat.get('required') or []))}",
    ]
    return {
        "answer": "\n".join(lines),
        "data": {"challenge": cid, "missing": names, "submitted": len(submitted)},
        "evidence": [st["id"] for st in missing][:20] + [f"challenge:{cid}"],
        "confidence": 0.95,
    }


def _handle_challenge_rate(store, cfg, q) -> dict[str, Any]:
    cid = _find_challenge(cfg, q)
    rows = [store.get_node(f"challenge:{c}")["props"] for c in cfg.challenge_order]
    if cid:
        p = store.get_node(f"challenge:{cid}")["props"]
        return {
            "answer": f"**{cid}（{p['name_cn']}）** 提交率 {p['rate']:.0%}，已交 {p['submitted']}/{len(cfg.roster)} 人。",
            "data": p,
            "evidence": [f"challenge:{cid}"],
            "confidence": 0.95,
        }
    rows = sorted(rows, key=lambda r: -r["rate"])
    body = "\n".join(f"| {r['id']} | {r['name_cn']} | {r['submitted']} | {r['rate']:.0%} |" for r in rows if r["submitted"])
    return {
        "answer": "| 挑战 | 名称 | 已交 | 提交率 |\n|---|---|---:|---|\n" + body,
        "data": rows,
        "evidence": [f"challenge:{r['id']}" for r in rows if r["submitted"]],
        "confidence": 0.9,
    }


def _handle_top_active(store, cfg, q) -> dict[str, Any]:
    pros = sorted(_students(store), key=lambda s: -s["props"].get("engagement_score", 0))[:5]
    lines = ["| # | 同学 | 参与分 | 消息数 |", "|---|---|---:|---:|"]
    for i, p in enumerate(pros, 1):
        lines.append(f"| {i} | {p['props']['name']} | {p['props']['engagement_score']} | {p['props']['msg_count']} |")
    return {
        "answer": "最活跃 Top 5（参与分：发言 35 + 助人 25 + 提交 30 + 持续性 10）：\n\n" + "\n".join(lines),
        "data": [p["props"] for p in pros],
        "evidence": [p["id"] for p in pros],
        "confidence": 0.92,
    }


def _handle_silent_students(store, cfg, q) -> dict[str, Any]:
    silent = [s for s in _students(store) if s["props"].get("msg_count", 0) == 0] + [
        s for s in _students(store) if (s["props"].get("risk_flags") or []) and any("沉默" in f for f in s["props"]["risk_flags"])
    ]
    seen, uniq = set(), []
    for s in silent:
        if s["id"] not in seen:
            seen.add(s["id"])
            uniq.append(s)
    if not uniq:
        return {"answer": "没有触发沉默预警的同学。", "data": [], "evidence": [], "confidence": 0.8}
    lines = [f"- {s['props']['name']}：{'; '.join(s['props'].get('risk_flags') or ['零发言'])}" for s in uniq]
    return {
        "answer": f"沉默/低活跃 {len(uniq)} 人：\n\n" + "\n".join(lines),
        "data": [s["props"] for s in uniq],
        "evidence": [s["id"] for s in uniq],
        "confidence": 0.9,
    }


def _handle_student_submissions(store, cfg, q) -> dict[str, Any]:
    st = _find_student(store, cfg, q)
    if not st:
        return {"answer": "要查哪位同学？例如「景雪晴提交了哪些挑战」。", "data": [], "evidence": [], "confidence": 0.3}
    wxid = st["props"]["wxid"]
    mine = [s["props"] for s in _subs(store) if s["props"]["student_id"] == wxid]
    mine.sort(key=lambda r: r["challenge"])
    if not mine:
        return {
            "answer": f"{st['props']['name']} 目前没有任何提交记录。",
            "data": [],
            "evidence": [st["id"]],
            "confidence": 0.9,
        }
    lines = [f"{st['props']['name']} 共 {len(mine)} 项提交：", "", "| 挑战 | 状态 | 完整度 | 件数 | 缺什么 |", "|---|---|---|---:|---|"]
    status_cn = {"accepted": "✅ 齐全", "reviewing": "🟡 待复核", "needs_revision": "🔴 缺件"}
    for r in mine:
        lines.append(
            f"| {r['challenge']} | {status_cn.get(r['status'], r['status'])} | {r['completeness']:.0%} | {r['artifact_count']} | {', '.join(r['missing']) or '—'} |"
        )
    return {
        "answer": "\n".join(lines),
        "data": mine,
        "evidence": [f"submission:{wxid}:{r['challenge']}" for r in mine],
        "confidence": 0.93,
    }


def _handle_profile(store, cfg, q) -> dict[str, Any]:
    st = _find_student(store, cfg, q)
    if not st:
        return {"answer": "要查哪位同学？例如「林一舟的画像」。", "data": [], "evidence": [], "confidence": 0.3}
    p = st["props"]
    qa_nodes = store.neighbors(st["id"], "ANSWERED", "out")
    lines = [
        f"**{p['name']}**（{p.get('major') or '专业未填'}）",
        "",
        f"- 消息 {p.get('msg_count')} 条，参与分 {p.get('engagement_score')}",
        f"- 提交 {len([s for s in _subs(store) if s['props']['student_id'] == p['wxid']])} 项，"
        f"回答过 {len(qa_nodes)} 个问题",
        f"- 技能标签：{'、'.join(p.get('skill_tags') or []) or '暂无足够证据'}",
        f"- 风险：{'；'.join(p.get('risk_flags') or []) or '无'}",
    ]
    return {
        "answer": "\n".join(lines),
        "data": p,
        "evidence": [st["id"]] + [n["id"] for n in qa_nodes[:5]],
        "confidence": 0.85,
    }


def _handle_faq(store, cfg, q) -> dict[str, Any]:
    cid = _find_challenge(cfg, q)
    keyword = None
    m = re.search(r"关于\s*([^\s的]+)", q)
    if m:
        keyword = m.group(1)
    pairs = store.nodes("QAPair")
    if cid:
        pairs = [p for p in pairs if p["props"].get("challenge") == cid]
    if keyword:
        pairs = [p for p in pairs if keyword in p["props"].get("question", "") or keyword in p["props"].get("answer", "")]
    if not pairs and keyword:
        pairs = store.search(keyword, "QAPair", limit=10)
    pairs = sorted(pairs, key=lambda p: -p["props"].get("quality_score", 0))[:5]
    if not pairs:
        return {
            "answer": f"没有找到{'关于 ' + keyword + ' 的' if keyword else ''}问答记录。可以先用 `wcm qa` 重新抽一遍。",
            "data": [],
            "evidence": [],
            "confidence": 0.5,
        }
    lines = [f"共找到 {len(pairs)} 条相关问答（按质量分排序）：", ""]
    for p in pairs:
        pr = p["props"]
        lines.append(f"**Q**：{pr['question']}")
        lines.append(f"**A**（{pr['answerer']}）：{pr['answer'][:120]}…")
        lines.append(f"*质量分 {pr['quality_score']} ｜ 标签 {'/'.join(pr.get('tags') or []) or '无'}*")
        lines.append("")
    return {
        "answer": "\n".join(lines),
        "data": [p["props"] for p in pairs],
        "evidence": [p["id"] for p in pairs],
        "confidence": 0.88,
    }


def _handle_mentoring(store, cfg, q) -> dict[str, Any]:
    edges = store.conn.execute("SELECT src, dst FROM edges WHERE type = 'MENTORED'").fetchall()
    counter: dict[tuple[str, str], int] = {}
    for e in edges:
        counter[(e["src"], e["dst"])] = counter.get((e["src"], e["dst"]), 0) + 1
    if not counter:
        return {"answer": "还没有从问答关系里推断出帮助关系。", "data": [], "evidence": [], "confidence": 0.6}
    top = sorted(counter.items(), key=lambda kv: -kv[1])[:5]
    lines = ["| 帮助者 | 被帮助 | 次数 |", "|---|---|---:|"]
    for (src, dst), n in top:
        a = store.get_node(src)
        b = store.get_node(dst)
        if a and b:
            lines.append(f"| {a['props']['name']} | {b['props']['name']} | {n} |")
    return {
        "answer": "互助关系 Top 5（由「回答了谁的问题」推断）：\n\n" + "\n".join(lines),
        "data": [{"from": s, "to": d, "count": n} for (s, d), n in top],
        "evidence": [s for (s, _) in counter][:10],
        "confidence": 0.8,
    }


def _handle_deadline(store, cfg, q) -> dict[str, Any]:
    rows = [store.get_node(f"challenge:{c}")["props"] for c in cfg.challenge_order if cfg.challenges[c].due]
    rows.sort(key=lambda r: r["due_date"])
    if not rows:
        return {"answer": "当前配置里没有设置截止日期的挑战。", "data": [], "evidence": [], "confidence": 0.7}
    lines = ["| 挑战 | 截止 | 已交 |", "|---|---|---:|"]
    for r in rows:
        lines.append(f"| {r['id']} {r['name_cn']} | {r['due_date']} | {r['submitted']} |")
    return {
        "answer": "有截止日期的挑战：\n\n" + "\n".join(lines),
        "data": rows,
        "evidence": [f"challenge:{r['id']}" for r in rows],
        "confidence": 0.95,
    }


def _handle_overview(store, cfg, q) -> dict[str, Any]:
    reports = store.nodes("Report")
    latest = sorted(reports, key=lambda r: r["props"].get("period", {}).get("end", ""))[-1] if reports else None
    students = _students(store)
    subs = _subs(store)
    qa_count = len(store.nodes("QAPair"))
    msgs = len(store.nodes("Message"))
    if latest:
        p = latest["props"]
        body = (
            f"**{p['period']['start'][:10]} ~ {p['period']['end'][:10]}**\n\n"
            f"- 消息 {p['messages']} 条，{p['active_students']}/{p['class_size']} 人发声\n"
            f"- 提交 {p['submissions']} 项（{p['artifacts']} 个文件），完整 {p['complete']} 项，缺件 {p['needs_revision']} 项\n"
            f"- Q&A 沉淀 {p['qa_kept']} 对，答出率 {p['qa_answer_rate']:.0%}\n"
            f"- 预警 {p['alert_total']} 条\n"
            f"- 最活跃：{'、'.join(x['nickname'] for x in p.get('top5') or [])}"
        )
    else:
        body = f"图里有 {len(students)} 位学生、{len(subs)} 项提交、{msgs} 条消息、{qa_count} 对问答。"
    return {
        "answer": body,
        "data": latest["props"] if latest else {},
        "evidence": [latest["id"]] if latest else [],
        "confidence": 0.9,
    }


def _handle_search(store, cfg, q) -> dict[str, Any]:
    nodes = store.search(q, limit=8) or store.search(q.replace("？", ""), limit=8)
    if not nodes:
        return {"answer": f"图里没有和「{q}」直接相关的记录。", "data": [], "evidence": [], "confidence": 0.4}
    lines = [f"检索到 {len(nodes)} 条相关记录：", ""]
    for n in nodes[:8]:
        pr = n["props"]
        snippet = pr.get("question") or pr.get("content") or pr.get("name") or pr.get("name_cn") or str(pr)[:80]
        lines.append(f"- [{n['type']}] {snippet}")
    return {"answer": "\n".join(lines), "data": [n["props"] for n in nodes], "evidence": [n["id"] for n in nodes], "confidence": 0.6}
