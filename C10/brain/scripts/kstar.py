#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kstar.py — 第二大脑 / Agent OS 的命令行内核

设计约束（刻意为之）：
1. 只用 Python 标准库，零安装、离线可跑，随包可迁移。
2. Markdown 是唯一真相源，SQLite 只是可重建的索引（删了不影响数据）。
3. 每个命令都往 logs/usage.jsonl 追加一行，使用记录不靠人回忆。

五层架构对应关系：
  Layer 1 Memory  -> memory/L1_raw/ memory/L2_episodes/ skills/ config/identity.md
  Layer 2 Skill   -> skills/<name>/SKILL.md
  Layer 3 Loop    -> `loop start` / `loop close`
  Layer 4 Tool    -> config/tools.md + 本脚本调用的能力
  Layer 5 Interface -> 本 CLI + reports/dashboard.html + AGENT.md（Markdown 驱动）

用法：python3 scripts/kstar.py --help
"""

import argparse
import json
import math
import os
import re
import shutil
import sqlite3
import statistics
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = ROOT / "memory" / "L1_raw"
EP_DIR = ROOT / "memory" / "L2_episodes"
SKILL_DIR = ROOT / "skills"
CFG_DIR = ROOT / "config"
RUN_DIR = ROOT / "logs" / "runs"
INBOX = ROOT / "inbox"
CAND_DIR = INBOX / "candidates"
REPORT_DIR = ROOT / "reports"
INDEX_DB = ROOT / "index" / "brain.db"
USAGE = ROOT / "logs" / "usage.jsonl"

CJK_RE = re.compile(r"[\u4e00-\u9fff]+")
WORD_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_+#.\-]*")
TODAY = lambda: date.today().isoformat()  # noqa: E731


# ---------------------------------------------------------------- 基础设施


def die(msg, code=1):
    print("✗ " + msg, file=sys.stderr)
    sys.exit(code)


def ensure_dirs():
    for d in (RAW_DIR, EP_DIR, SKILL_DIR, CFG_DIR, RUN_DIR, CAND_DIR,
              INBOX / "unsorted", REPORT_DIR, ROOT / "index"):
        d.mkdir(parents=True, exist_ok=True)


def log_usage(cmd, argv, ok=True, note=""):
    ensure_dirs()
    rec = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "cmd": cmd,
        "argv": argv,
        "ok": ok,
        "note": note,
        "cwd": str(Path.cwd()),
    }
    with USAGE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ------------------------------------------------------- frontmatter 解析


def _coerce(v):
    v = v.strip()
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_coerce(x) for x in inner.split(",")]
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v in ("true", "false"):
        return v == "true"
    for cast in (int, float):
        try:
            return cast(v)
        except ValueError:
            pass
    return v


def parse_front(text):
    """极简 YAML frontmatter：只支持 key: 标量 / [列表]。够用即可。"""
    if not text.startswith("---"):
        return {}, text
    lines = text.split("\n")
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text
    fm = {}
    for line in lines[1:end]:
        s = line.strip()
        if not s or s.startswith("#") or ":" not in s:
            continue
        k, v = s.split(":", 1)
        fm[k.strip()] = _coerce(v)
    return fm, "\n".join(lines[end + 1:])


def dump_front(fm):
    out = ["---"]
    for k, v in fm.items():
        if isinstance(v, list):
            out.append("%s: [%s]" % (k, ", ".join(str(x) for x in v)))
        elif isinstance(v, bool):
            out.append("%s: %s" % (k, "true" if v else "false"))
        else:
            out.append("%s: %s" % (k, v))
    out.append("---")
    return "\n".join(out) + "\n"


def read_doc(path):
    text = path.read_text(encoding="utf-8")
    fm, body = parse_front(text)
    return fm, body


def write_doc(path, fm, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_front(fm) + body, encoding="utf-8")


def append_under_section(body, heading, row):
    """把一行内容插到指定二级标题所在小节的末尾（下一个 ## 之前）。"""
    lines = body.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == heading.strip():
            start = i
            break
    if start is None:
        return body.rstrip("\n") + "\n\n" + heading + "\n\n" + row + "\n"
    stop = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("## "):
            stop = j
            break
    # 回退跳过尾部空行
    k = stop
    while k > start + 1 and not lines[k - 1].strip():
        k -= 1
    lines.insert(k, row)
    return "\n".join(lines)


# ------------------------------------------------------------- 检索与打分


def tokenize(text):
    text = text.lower()
    toks = []
    for w in WORD_RE.findall(text):
        toks.append(("w", w))
    for run in CJK_RE.findall(text):
        for ch in run:
            toks.append(("c1", ch))
        for i in range(len(run) - 1):
            toks.append(("c2", run[i:i + 2]))
    return toks


def term_weight(kind):
    return {"c1": 0.35, "c2": 1.0, "w": 1.0}[kind]


def iter_docs():
    """产出 (layer, path, fm, body)。layer: raw / episode / skill。"""
    for p in sorted(RAW_DIR.rglob("*.md")):
        fm, body = read_doc(p)
        yield "raw", p, fm, body
    for p in sorted(EP_DIR.glob("*.md")):
        fm, body = read_doc(p)
        yield "episode", p, fm, body
    for p in sorted(SKILL_DIR.glob("*/SKILL.md")):
        fm, body = read_doc(p)
        yield "skill", p, fm, body


def build_index(verbose=True):
    ensure_dirs()
    if INDEX_DB.exists():
        INDEX_DB.unlink()
    con = sqlite3.connect(INDEX_DB)
    con.execute("CREATE TABLE docs(id INTEGER PRIMARY KEY, layer TEXT, path TEXT, "
                "title TEXT, tags TEXT, body TEXT, mtime REAL)")
    n = 0
    for layer, p, fm, body in iter_docs():
        title = fm.get("title") or fm.get("name") or p.stem
        tags = fm.get("tags") or fm.get("tag") or []
        if isinstance(tags, str):
            tags = [tags]
        con.execute("INSERT INTO docs(layer,path,title,tags,body,mtime) VALUES(?,?,?,?,?,?)",
                    (layer, str(p.relative_to(ROOT)), title,
                     " ".join(str(t) for t in tags), body, p.stat().st_mtime))
        n += 1
    con.commit()
    con.close()
    if verbose:
        print("✓ 索引重建完成：%d 篇（%s）" % (n, INDEX_DB.relative_to(ROOT)))
    return n


def index_is_stale():
    if not INDEX_DB.exists():
        return True
    db_m = INDEX_DB.stat().st_mtime
    for layer, p, fm, body in iter_docs():
        if p.stat().st_mtime > db_m:
            return True
    return False


def ensure_index():
    if index_is_stale():
        build_index(verbose=False)


def load_corpus():
    ensure_index()
    con = sqlite3.connect(INDEX_DB)
    rows = con.execute("SELECT layer,path,title,tags,body FROM docs").fetchall()
    con.close()
    docs = []
    for layer, path, title, tags, body in rows:
        d_tokens = tokenize(title + " " + tags + " " + body)
        tf = {}
        for kind, t in d_tokens:
            tf[t] = tf.get(t, 0) + term_weight(kind)
        docs.append({
            "layer": layer, "path": path, "title": title,
            "tags": str(tags).split(), "body": body,
            "tf": tf, "len": max(1, sum(tf.values())),
            "title_tokens": {t for _, t in tokenize(title)},
            "tag_tokens": {t for _, t in tokenize(tags)},
        })
    return docs


def recall(query, k=5, layer=None):
    docs = load_corpus()
    if layer and layer != "all":
        docs = [d for d in docs if d["layer"] == layer]
    if not docs:
        return []
    q_tokens = tokenize(query)
    q_terms = {}
    for kind, t in q_tokens:
        q_terms[t] = max(q_terms.get(t, 0), term_weight(kind))
    N = len(docs)
    avgdl = sum(d["len"] for d in docs) / N
    df = {}
    for t in q_terms:
        df[t] = sum(1 for d in docs if t in d["tf"])
    k1, b = 1.4, 0.7
    scored = []
    for d in docs:
        s = 0.0
        hits = []
        for t, w in q_terms.items():
            tf = d["tf"].get(t, 0)
            if not tf:
                continue
            idf = math.log(1 + (N - df[t] + 0.5) / (df[t] + 0.5))
            s += w * idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * d["len"] / avgdl))
            hits.append(t)
            if t in d["title_tokens"]:
                s += 1.2 * w
            if t in d["tag_tokens"]:
                s += 2.0 * w
        if s > 0:
            # 展示层过滤单字噪声：单字命中对排序有贡献，但对"为什么命中"没有解释力
            show = [t for t in hits if len(t) > 1] or hits
            why = "命中 " + "、".join(sorted(show)[:6])
            if [t for t in hits if t in d["tag_tokens"]]:
                why += "（标签命中）"
            scored.append((s, d, why))
    scored.sort(key=lambda x: -x[0])
    return scored[:k]


# -------------------------------------------------------------- 数据读取


def all_episodes():
    eps = []
    for p in sorted(EP_DIR.glob("*.md")):
        fm, body = read_doc(p)
        fm["_path"] = p
        fm["_body"] = body
        eps.append(fm)
    return eps


def all_skills():
    out = []
    for p in sorted(SKILL_DIR.glob("*/SKILL.md")):
        fm, body = read_doc(p)
        fm["_path"] = p
        fm["_body"] = body
        out.append(fm)
    return out


def all_runs():
    out = []
    for p in sorted(RUN_DIR.glob("*.md")):
        fm, body = read_doc(p)
        fm["_path"] = p
        fm["_body"] = body
        out.append(fm)
    return out


def num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def verdict_of(dr):
    if dr is None:
        return "未评"
    if dr <= -0.05:
        return "低估"
    if dr <= 0.05:
        return "命中"
    if dr <= 0.2:
        return "轻度高估"
    return "显著高估"


def skill_avg_dr(name):
    ds = [num(e.get("dr")) for e in all_episodes()
          if name in (e.get("skills") or []) and num(e.get("dr")) is not None]
    if not ds:
        return None, 0
    return round(sum(ds) / len(ds), 3), len(ds)


def next_id(prefix, path, pad=2):
    """生成 EP-YYYY-MM-DD-NN 形式的编号（与手工命名保持一致，便于按日期排序）。"""
    pat = re.compile(r"^%s-(\d{4})-(\d{2})-(\d{2})-(\d+)" % re.escape(prefix))
    n = 0
    today = TODAY()
    for p in path.glob("*.md"):
        m = pat.match(p.name)
        if m and "%s-%s-%s" % (m.group(1), m.group(2), m.group(3)) == today:
            n = max(n, int(m.group(4)))
    return "%s-%s-%0*d" % (prefix, today, pad, n + 1)


def body_section(body, prefix):
    """从 run 文件里取出一节正文（用于 loop close 时继承 S / Â）。"""
    lines = body.split("\n")
    start = None
    for i, ln in enumerate(lines):
        if ln.startswith(prefix):
            start = i
            break
    if start is None:
        return ""
    out = []
    for ln in lines[start + 1:]:
        if ln.startswith("## "):
            break
        out.append(ln)
    return "\n".join(out).strip()


def slugify(text, maxlen=28):
    s = re.sub(r"[^\w\u4e00-\u9fff\-]+", "-", text.strip().lower())
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return (s[:maxlen] or "note")


# ---------------------------------------------------------------- 命令实现


def cmd_init(a):
    ensure_dirs()
    (ROOT / "memory" / "README.md").write_text(
        "# memory/ 说明\n\n"
        "- `L1_raw/`：原始输入（笔记、对话、灵感），未结构化。\n"
        "- `L2_episodes/`：KSTAR 结构化经验，一条经验一个文件。\n"
        "- L3 Skill 不在本目录，落在 `../skills/`（可被 Agent 直接加载）。\n"
        "- L4 Identity 落在 `../config/identity.md`。\n",
        encoding="utf-8")
    print("✓ 目录结构就绪：%s" % ROOT)
    for d in ("memory/L1_raw", "memory/L2_episodes", "skills", "config",
              "logs/runs", "inbox/candidates", "reports", "index"):
        print("  -", d)


def cmd_add(a):
    ensure_dirs()
    text = " ".join(a.text) if a.text else ""
    if not text and not sys.stdin.isatty():
        text = sys.stdin.read()
    if not text.strip():
        die("内容为空：kstar.py add \"一段笔记\" [--tag x]")
    d = date.fromisoformat(a.date) if a.date else date.today()
    slug = slugify(a.title or text)
    path = RAW_DIR / d.strftime("%Y") / d.strftime("%m") / ("%s-%s.md" % (d.isoformat(), slug))
    i = 2
    while path.exists():
        path = path.with_name("%s-%s-%d.md" % (d.isoformat(), slug, i))
        i += 1
    fm = {
        "id": "L1-" + d.strftime("%Y%m%d") + "-" + slug[:12],
        "date": d.isoformat(),
        "layer": "L1_raw",
        "tags": a.tag or [],
        "source": a.source or "terminal",
        "processed": False,
    }
    body = "\n# " + (a.title or slug) + "\n\n" + text.strip() + "\n"
    write_doc(path, fm, body)
    print("✓ L1 已入库：%s" % path.relative_to(ROOT))
    print("  下一个动作：kstar.py ep new --from-note %s ..." % path.stem)
    return path


def cmd_note_processed(a):
    """把 L1 笔记标记为已转 L2（回填场景：经验是手写的，需要补标这一步）。"""
    n = 0
    for name in a.names:
        hits = list(RAW_DIR.rglob(name + "*.md"))
        if not hits:
            print("  ! 未找到：%s" % name)
        for p in hits:
            fm, body = read_doc(p)
            fm["processed"] = True
            write_doc(p, fm, body)
            print("✓ processed → %s" % p.name)
            n += 1
    if not n:
        die("没有匹配到任何 L1 笔记")


def cmd_recall(a):
    res = recall(" ".join(a.query), k=a.k, layer=a.layer)
    if not res:
        print("（没有命中。可能是新领域——这条空白本身就是值得记的信号。）")
        return
    print("K（Knowledge）检索结果 · query=%s · 层=%s" % (" ".join(a.query), a.layer))
    for i, (s, d, why) in enumerate(res, 1):
        print("%d. [%s] %-46s  score=%.2f" % (i, d["layer"], d["title"][:46], s))
        print("   %s" % d["path"])
        print("   %s" % why)


def cmd_ep_new(a):
    ensure_dirs()
    eid = next_id("EP", EP_DIR)
    dr = None
    if a.rhat is not None and a.r is not None:
        dr = round(a.rhat - a.r, 3)
    fm = {
        "id": eid, "date": a.date or TODAY(), "layer": "L2_episode",
        "title": a.title, "status": a.status,
        "tags": a.tag or [], "skills": a.skills or [],
        "r_hat": a.rhat, "r": a.r, "dr": dr,
        "verdict": verdict_of(dr),
        "source": a.source or "手动录入",
        "evidence": a.evidence or "",
        "from_notes": a.from_note or [],
    }
    body = "\n# %s\n\n## S（Situation）\n\n%s\n\n## T（Task）\n\n%s\n\n## A（Action）\n\n%s\n\n## R（Result）\n\n%s\n\n" \
           "## ΔR（R̂ − R）\n\n- R̂ = %s ｜ R = %s ｜ **ΔR = %s**\n- 判定：%s\n- 解释：%s\n\n" \
           "## 可复用的一句\n\n%s\n" % (
               a.title, a.situation, a.task, a.action, a.result,
               a.rhat, a.r, dr, verdict_of(dr), a.dr_note or "（待补）",
               a.lesson or "（还没提炼出来——写一句能复用的结论，否则这条经验只是日记。）")
    path = EP_DIR / (eid + "-" + slugify(a.title, 24) + ".md")
    write_doc(path, fm, body)
    for n in (a.from_note or []):
        np = RAW_DIR.rglob(n + ".md")
        for q in np:
            f2, b2 = read_doc(q)
            f2["processed"] = True
            write_doc(q, f2, b2)
    print("✓ L2 经验已写入：%s" % path.name)
    print("  ΔR = %s → %s" % (dr, verdict_of(dr)))
    return path


def cmd_ep_list(a):
    eps = all_episodes()
    if a.tag:
        eps = [e for e in eps if a.tag in (e.get("tags") or [])]
    if a.status:
        eps = [e for e in eps if e.get("status") == a.status]
    if not eps:
        print("（还没有 L2 经验。先 add 几条 L1，再 ep new。）")
        return
    print("%-18s %-10s %-5s %-6s %-6s %-8s %s" % ("ID", "date", "R̂", "R", "ΔR", "判定", "标题"))
    for e in eps:
        print("%-18s %-10s %-5s %-6s %-6s %-8s %s" % (
            e.get("id", "?"), e.get("date", ""), e.get("r_hat", "-"),
            e.get("r", "-"), e.get("dr", "-"), e.get("verdict", "-"),
            str(e.get("title", ""))[:38]))
    drs = [num(e.get("dr")) for e in eps if num(e.get("dr")) is not None]
    if drs:
        print("\n共 %d 条｜平均 ΔR=%.3f｜最大高估=%.3f｜最大低估=%.3f" % (
            len(eps), statistics.mean(drs), max(drs), min(drs)))


def cmd_ep_promote(a):
    p = find_ep(a.id)
    fm, body = read_doc(p)
    fm["status"] = "confirmed"
    write_doc(p, fm, body)
    print("✓ %s → confirmed（进入可检索的正式经验库）" % a.id)


def cmd_ep_show(a):
    p = find_ep(a.id)
    print(p.read_text(encoding="utf-8"))


def find_ep(eid):
    for p in EP_DIR.glob(eid + "*.md"):
        return p
    for e in all_episodes():
        if str(e.get("id")) == eid:
            return e["_path"]
    die("找不到经验：%s（用 ep list 看 ID）" % eid)


def cmd_loop_start(a):
    ensure_dirs()
    rid = "RUN-" + datetime.now().strftime("%Y%m%d-%H%M")
    i = 2
    base = rid
    while (RUN_DIR / (rid + ".md")).exists():
        rid = "%s-%d" % (base, i)
        i += 1
    hits = recall(a.task, k=3)
    k_block = ["| # | 层 | 标题 | 分数 | 为什么 |", "|---|---|---|---|---|"]
    for i, (s, d, why) in enumerate(hits, 1):
        k_block.append("| %d | %s | %s | %.2f | %s |" % (i, d["layer"], d["title"], s, why))
    if not hits:
        k_block.append("| - | - | （无命中，属于新情境） | - | - |")
    skills = a.skills or [d["title"] for (s, d, _) in hits if d["layer"] == "skill"][:2]
    fm = {
        "id": rid, "type": "KSTAR-run",
        "start": datetime.now().isoformat(timespec="seconds"),
        "end": "", "status": "open",
        "task": a.task, "tags": a.tag or [],
        "skills": skills, "r_hat": a.rhat, "r": None, "dr": None,
    }
    body = """
# {rid} · {task}

## K（Knowledge：检索到了什么）

{ktable}

- 载入 Skill：{skills}

## S（Situation：我面对什么）

{sit}

## T（Task：我要做什么）

{task}

## Â（Action Plan）+ R̂（预期结果）

{plan}

- R̂ = {rhat}

## A（Action：实际做了什么）

（执行中……）

## R（Result：实际结果）

（待填）

## ΔR = R̂ − R

（待算）

## 教训

（待提炼）
""".format(rid=rid, task=a.task, ktable="\n".join(k_block),
           skills=", ".join(skills) if skills else "（无）",
           sit=a.situation or "（待填：约束、时间、可用工具、上次同类经验）",
           plan=a.plan or "（待填：分几步、每步调用哪个 Skill/工具）",
           rhat=a.rhat if a.rhat is not None else "（待填）")
    path = RUN_DIR / (rid + ".md")
    write_doc(path, fm, body)
    print("✓ 循环已开启：%s" % path.relative_to(ROOT))
    print("\n── K 步（自动检索） ──")
    for i, (s, d, why) in enumerate(hits, 1):
        print("%d. [%s] %s  (%.2f)  %s" % (i, d["layer"], d["title"], s, why))
    print("\n下一步：补 S / Â / R̂ → 干活 → kstar.py loop close %s --actual \"...\" --r 0.8" % rid)
    return rid


def cmd_loop_close(a):
    p = RUN_DIR / (a.run + ".md")
    if not p.exists():
        cands = sorted(RUN_DIR.glob(a.run + "*.md"))
        if not cands:
            die("找不到 run：%s" % a.run)
        p = cands[0]
    fm, body = read_doc(p)
    fm["status"] = "closed"
    fm["end"] = datetime.now().isoformat(timespec="seconds")
    fm["r"] = a.r
    if a.rhat is not None:
        fm["r_hat"] = a.rhat
    rhat = num(fm.get("r_hat"))
    rv = num(a.r)
    dr = round(rhat - rv, 3) if (rhat is not None and rv is not None) else None
    fm["dr"] = dr
    body = body.replace("## A（Action：实际做了什么）\n\n（执行中……）",
                        "## A（Action：实际做了什么）\n\n" + a.actual)
    body = body.replace("## R（Result：实际结果）\n\n（待填）",
                        "## R（Result：实际结果）\n\n" + a.actual)
    body = body.replace("## ΔR = R̂ − R\n\n（待算）",
                        "## ΔR = R̂ − R\n\n- R̂ = %s ｜ R = %s ｜ **ΔR = %s**\n- 判定：%s\n- 解释：%s" % (
                            fm.get("r_hat"), a.r, dr, verdict_of(dr), a.dr_note or "（待补）"))
    body = body.replace("## 教训\n\n（待提炼）", "## 教训\n\n" + (a.lesson or "（待提炼）"))
    write_doc(p, fm, body)
    print("✓ 循环关闭：%s" % p.name)
    print("  ΔR = %s（R̂=%s − R=%s）→ %s" % (dr, fm.get("r_hat"), a.r, verdict_of(dr)))
    # 自动落一条 L2 草稿，避免"跑完就忘"。
    # S 与 Â 从 run 文件里继承（不然草稿只有一句"从 run 继承，待补"，等于没记）。
    sit = body_section(body, "## S（") or "（待补）"
    plan = body_section(body, "## Â（")
    action = (plan + "\n\n**实际执行**\n\n" + a.actual) if plan else a.actual
    ep = cmd_ep_new(argparse.Namespace(
        title=fm.get("task"), situation=sit, task=fm.get("task"),
        action=action, result=a.actual, rhat=num(fm.get("r_hat")), r=rv,
        dr_note=a.dr_note, lesson=a.lesson, tag=fm.get("tags") or [],
        skills=fm.get("skills") or [], source="loop " + p.stem,
        evidence="logs/runs/" + p.name, status="draft", from_note=None,
        date=TODAY()))
    print("  → 已生成 L2 草稿（status=draft）：%s" % ep.name)
    if dr is not None and abs(dr) > 0.2:
        print("  ⚠ |ΔR|>0.2：这是校准信号。跑 `kstar.py skill iterate <name> --note \"...\"`")


def cmd_skill_new(a):
    ensure_dirs()
    d = SKILL_DIR / slugify(a.name)
    d.mkdir(parents=True, exist_ok=True)
    p = d / "SKILL.md"
    if p.exists():
        die("Skill 已存在：%s" % p.relative_to(ROOT))
    fm = {
        "name": slugify(a.name), "description": a.desc,
        "status": a.status, "version": 1,
        "created": TODAY(), "updated": TODAY(),
        "tags": a.tag or [], "uses_system": 0, "uses_backfilled": 0,
        "last_used": "", "owner": "JingXueQing",
    }
    body = """
# %s

## What（做什么）

%s

## When to Use（什么时候用）

%s

## Input（输入）

%s

## Steps（步骤）

1. （待填）
2. （待填）
3. （待填）

## Tools（需要什么工具）

- （待填）

## Output（输出）

%s

## 使用记录

| 日期 | 场景 | 结果 | ΔR | 来源 |
|---|---|---|---|---|

## 迭代史

| 版本 | 日期 | 改了什么 | 触发原因 |
|---|---|---|---|
| v1 | %s | 初版 | — |
""" % (a.name, a.desc, a.when or "（待填：触发条件）", a.input or "（待填）",
       a.output or "（待填）", TODAY())
    write_doc(p, fm, body)
    print("✓ Skill 已创建：%s" % p.relative_to(ROOT))


def find_skill(name):
    p = SKILL_DIR / name / "SKILL.md"
    if p.exists():
        return p
    for q in SKILL_DIR.glob("*/SKILL.md"):
        fm, _ = read_doc(q)
        if fm.get("name") == name or q.parent.name == name:
            return q
    die("找不到 Skill：%s（kstar.py skill list 查看）" % name)


def cmd_skill_use(a):
    p = find_skill(a.name)
    fm, body = read_doc(p)
    fm["uses_system"] = int(fm.get("uses_system") or 0) + 1
    fm["last_used"] = TODAY()
    fm["updated"] = TODAY()
    dr = "-" if a.dr is None else "%.2f" % a.dr
    row = "| %s | %s | %s | %s | %s |" % (
        TODAY(), a.note or "（未说明）", a.result or "成功", dr, a.source or "CLI")
    body = append_under_section(body, "## 使用记录", row)
    write_doc(p, fm, body)
    avg, n = skill_avg_dr(fm.get("name"))
    print("✓ %s 使用次数 → %d（关联经验 %d 条，平均 ΔR=%s）" % (
        fm.get("name"), fm["uses_system"], n, avg if avg is not None else "-"))


def cmd_skill_iterate(a):
    p = find_skill(a.name)
    fm, body = read_doc(p)
    v = int(fm.get("version") or 1) + 1
    fm["version"] = v
    fm["updated"] = TODAY()
    row = "| v%d | %s | %s | %s |" % (v, TODAY(), a.note, a.trigger or "ΔR 偏大 / 复盘发现")
    body = append_under_section(body, "## 迭代史", row)
    write_doc(p, fm, body)
    print("✓ %s 升到 v%d：%s" % (fm.get("name"), v, a.note))


def cmd_skill_deprecate(a):
    p = find_skill(a.name)
    fm, body = read_doc(p)
    fm["status"] = "deprecated"
    fm["deprecated_reason"] = a.reason
    fm["updated"] = TODAY()
    body = append_under_section(body, "## 迭代史",
                                "| — | %s | 标记 deprecated | %s |" % (TODAY(), a.reason))
    write_doc(p, fm, body)
    print("✓ %s 已淘汰：%s（文件保留，历史可追溯）" % (fm.get("name"), a.reason))


def cmd_skill_list(a):
    sks = all_skills()
    if not sks:
        print("（还没有 Skill）")
        return
    print("%-24s %-10s %-4s %-6s %-6s %-11s %s" % (
        "name", "status", "ver", "系统用", "回填", "最近使用", "平均ΔR"))
    for s in sks:
        avg, n = skill_avg_dr(s.get("name"))
        print("%-24s %-10s v%-3s %-6s %-6s %-11s %s" % (
            s.get("name"), s.get("status"), s.get("version"),
            s.get("uses_system") or 0, s.get("uses_backfilled") or 0,
            s.get("last_used") or "-",
            ("%.2f (n=%d)" % (avg, n)) if avg is not None else "-"))


def cmd_skill_stats(a):
    sks = all_skills()
    act = [s for s in sks if s.get("status") == "active"]
    print("Skill 总数 %d｜active %d｜candidate %d｜deprecated %d" % (
        len(sks), len(act),
        sum(1 for s in sks if s.get("status") == "candidate"),
        sum(1 for s in sks if s.get("status") == "deprecated")))
    print("系统内调用合计 %d 次｜回填历史使用 %d 次" % (
        sum(int(s.get("uses_system") or 0) for s in sks),
        sum(int(s.get("uses_backfilled") or 0) for s in sks)))
    print("\n按调用次数排序：")
    for s in sorted(sks, key=lambda x: -int(x.get("uses_system") or 0)):
        avg, n = skill_avg_dr(s.get("name"))
        print("  %-24s %2d 次  v%s  %-9s 平均ΔR=%s" % (
            s.get("name"), int(s.get("uses_system") or 0), s.get("version"),
            s.get("status"), avg if avg is not None else "-"))


def cmd_distill(a):
    eps = [e for e in all_episodes() if e.get("status") == "confirmed"]
    skills = all_skills()
    covered = set()
    for s in skills:
        if s.get("status") != "deprecated":
            for t in (s.get("tags") or []):
                covered.add(str(t))
    buckets = {}
    for e in eps:
        for t in (e.get("tags") or []):
            buckets.setdefault(str(t), []).append(e)
    cands = []
    for tag, es in buckets.items():
        if len(es) >= a.min:
            cands.append((tag, es))
    if not cands:
        print("没有满足条件的候选（阈值 ≥%d 条同类经验）。继续积累。\n"
              "提示：这也是一个信号——要么经验还不够，要么 tag 打得太散。" % a.min)
        return
    cands.sort(key=lambda x: -len(x[1]))
    print("候选 Skill（同一标签下 ≥%d 条经验）：" % a.min)
    for tag, es in cands:
        flag = "已有 Skill 覆盖" if tag in covered else "★ 未覆盖"
        print("\n- [%s] %d 条  %s" % (tag, len(es), flag))
        for e in es:
            print("    %s  ΔR=%s  %s" % (e.get("id"), e.get("dr"), str(e.get("title"))[:40]))
        if tag not in covered and a.write:
            p = CAND_DIR / ("CAND-" + slugify(tag) + ".md")
            lines = ["# 候选 Skill：%s" % tag, "",
                     "> 由 `kstar.py distill` 在 %s 自动生成。证据：%d 条 L2 经验。" % (TODAY(), len(es)),
                     "> 状态：候选。**必须手动执行验证一次，才能 skill new 上线。**", "",
                     "## 支撑经验", ""]
            for e in es:
                lines.append("- %s（%s，ΔR=%s）：%s" % (
                    e.get("id"), e.get("date"), e.get("dr"), e.get("title")))
                lines.append("  - 路径：%s" % e["_path"].relative_to(ROOT))
            lines += ["", "## 从经验里抽出的一致做法", "",
                      "（手工填写：这几条经验的 Action 里重复出现的步骤是什么？）", "",
                      "## 差异点（必须保留的分叉）", "",
                      "（手工填写：什么情况下这套步骤不适用？）", ""]
            p.write_text("\n".join(lines), encoding="utf-8")
            print("    → 已写入 %s" % p.relative_to(ROOT))
    if not a.write:
        print("\n（加 --write 可落盘候选文件）")


def cmd_doctor(a):
    problems, warns = [], []
    needed = ["memory/L1_raw", "memory/L2_episodes", "skills", "config",
              "logs/runs", "inbox/candidates", "reports", "index"]
    for d in needed:
        if not (ROOT / d).is_dir():
            problems.append("缺目录：%s" % d)
    eps = all_episodes()
    sks = all_skills()
    runs = all_runs()
    for e in eps:
        if num(e.get("dr")) is None:
            problems.append("%s 没有 ΔR（R̂/R 缺失）" % e.get("id"))
        if not (e.get("skills") or []):
            warns.append("%s 没关联任何 Skill（可能漏了一次抽象）" % e.get("id"))
        if e.get("status") == "draft":
            warns.append("%s 仍是 draft（未确认的经验不进正式检索）" % e.get("id"))
    for s in sks:
        if not (s.get("tags") or []):
            warns.append("Skill %s 没有 tags（无法被 distill 覆盖判断）" % s.get("name"))
        if int(s.get("uses_system") or 0) + int(s.get("uses_backfilled") or 0) == 0:
            problems.append("Skill %s 从未被使用（空壳）" % s.get("name"))
        lu = s.get("last_used")
        if s.get("status") == "active" and lu:
            try:
                days = (date.today() - date.fromisoformat(str(lu))).days
                if days > 30:
                    warns.append("Skill %s 已 %d 天未用 → 考虑 deprecate" % (s.get("name"), days))
            except ValueError:
                pass
    unprocessed = []
    for p in RAW_DIR.rglob("*.md"):
        fm, _ = read_doc(p)
        if not fm.get("processed"):
            try:
                days = (date.today() - date.fromisoformat(str(fm.get("date")))).days
            except (ValueError, TypeError):
                days = 0
            unprocessed.append((days, p))
    for days, p in unprocessed:
        if days > 7:
            warns.append("L1 笔记 %d 天未转 L2：%s" % (days, p.name))

    print("── doctor ──")
    print("L1 原始 %d 篇｜L2 经验 %d 条（confirmed %d / draft %d）｜Skill %d 个｜Run %d 次" % (
        len(list(RAW_DIR.rglob("*.md"))), len(eps),
        sum(1 for e in eps if e.get("status") == "confirmed"),
        sum(1 for e in eps if e.get("status") == "draft"),
        len(sks), len(runs)))
    if problems:
        print("\n✗ 必须修（%d）：" % len(problems))
        for x in problems:
            print("  -", x)
    if warns:
        print("\n⚠ 建议看（%d）：" % len(warns))
        for x in warns:
            print("  -", x)
    if not problems and not warns:
        print("\n✓ 全部检查通过")
    print("\n结论：%s" % ("有硬问题，先修" if problems else "结构健康"))
    return 1 if problems else 0


def _svg_spark(values, w=640, h=110, pad=18):
    if not values:
        return ""
    mn, mx = min(values), max(values)
    rng = (mx - mn) or 1
    n = len(values)
    step = (w - 2 * pad) / max(1, n - 1)
    pts = []
    for i, v in enumerate(values):
        x = pad + i * step
        y = h - pad - (v - mn) / rng * (h - 2 * pad)
        pts.append("%.1f,%.1f" % (x, y))
    zero_y = h - pad - (0 - mn) / rng * (h - 2 * pad)
    return ('<svg viewBox="0 0 %d %d" width="100%%" height="%d">'
            '<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#c9d1d9" stroke-dasharray="4 3"/>'
            '<polyline fill="none" stroke="#2f6feb" stroke-width="2" points="%s"/>%s</svg>') % (
        w, h, h, pad, zero_y, w - pad, zero_y, " ".join(pts),
        "".join('<circle cx="%s" cy="%s" r="3" fill="#2f6feb"/>' % tuple(p.split(",")) for p in pts))


def cmd_dash(a):
    ensure_dirs()
    eps = all_episodes()
    sks = all_skills()
    runs = all_runs()
    drs = [num(e.get("dr")) for e in eps if num(e.get("dr")) is not None]
    per_skill = []
    for s in sks:
        avg, n = skill_avg_dr(s.get("name"))
        per_skill.append((s, avg, n))
    per_skill.sort(key=lambda x: -int(x[0].get("uses_system") or 0))

    def bar_rows():
        out = []
        for s, avg, n in per_skill:
            st = s.get("status")
            cls = {"active": "ok", "candidate": "warn", "deprecated": "off"}.get(st, "")
            out.append("<tr><td><code>%s</code></td><td><span class='tag %s'>%s</span></td>"
                       "<td>v%s</td><td class='num'>%s</td><td class='num'>%s</td>"
                       "<td class='num'>%s</td><td>%s</td></tr>" % (
                           s.get("name"), cls, st, s.get("version"),
                           s.get("uses_system") or 0, s.get("uses_backfilled") or 0,
                           ("%.2f" % avg) if avg is not None else "—",
                           s.get("last_used") or "—"))
        return "\n".join(out)

    def ep_rows():
        out = []
        for e in sorted(eps, key=lambda x: str(x.get("date"))):
            dr = num(e.get("dr"))
            cls = "ok" if dr is not None and abs(dr) <= 0.05 else "warn" if dr is not None and abs(dr) <= 0.2 else "bad"
            out.append("<tr><td>%s</td><td>%s</td><td>%s</td><td class='num'>%s</td>"
                       "<td class='num'>%s</td><td class='num'><span class='tag %s'>%s</span></td>"
                       "<td>%s</td></tr>" % (
                           e.get("id"), e.get("date"), str(e.get("title"))[:44],
                           e.get("r_hat"), e.get("r"), cls,
                           ("%.2f" % dr) if dr is not None else "—", e.get("verdict")))
        return "\n".join(out)

    avg_dr = statistics.mean(drs) if drs else None
    over = sum(1 for d in drs if d > 0.2)
    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>第二大脑 · 运行看板</title>
<style>
:root{--bg:#f6f7f9;--card:#fff;--ink:#1f2328;--mut:#6b7280;--line:#e5e7eb;--blue:#2f6feb}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.65 -apple-system,"PingFang SC","Helvetica Neue",Arial,sans-serif}
.wrap{max-width:1060px;margin:0 auto;padding:32px 20px 60px}
h1{font-size:22px;margin:0 0 4px}h2{font-size:15px;margin:28px 0 10px;color:#111}
.sub{color:var(--mut);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px}
.card .k{color:var(--mut);font-size:12px}.card .v{font-size:24px;font-weight:600;margin-top:2px}
table{width:100%%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
border-radius:10px;overflow:hidden}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;font-size:13px;vertical-align:top}
th{background:#fafbfc;color:var(--mut);font-weight:500}
tr:last-child td{border-bottom:0}.num{text-align:right;font-variant-numeric:tabular-nums}
.tag{display:inline-block;padding:1px 8px;border-radius:999px;font-size:12px;background:#eef1f5;color:#475569}
.tag.ok{background:#e7f6ec;color:#137333}.tag.warn{background:#fff4e5;color:#a15c00}
.tag.bad{background:#fdeceb;color:#b3261e}.tag.off{background:#f1f2f4;color:#8b8f96}
code{background:#f1f3f5;padding:1px 5px;border-radius:4px;font-size:12.5px}
.note{background:#eef4ff;border:1px solid #d5e2ff;border-radius:10px;padding:12px 14px;margin-top:22px;font-size:13px}
footer{margin-top:28px;color:var(--mut);font-size:12px}
</style></head><body><div class="wrap">
<h1>第二大脑 · 运行看板</h1>
<div class="sub">KSTAR Agent OS ｜ 生成时间 %(now)s ｜ 数据源：memory/ + skills/ + logs/</div>
<div class="grid">
<div class="card"><div class="k">L1 原始笔记</div><div class="v">%(n1)d</div></div>
<div class="card"><div class="k">L2 KSTAR 经验</div><div class="v">%(n2)d</div></div>
<div class="card"><div class="k">L3 Skill（active）</div><div class="v">%(n3)d</div></div>
<div class="card"><div class="k">KSTAR 循环执行</div><div class="v">%(n4)d</div></div>
<div class="card"><div class="k">平均 ΔR</div><div class="v">%(avg)s</div></div>
<div class="card"><div class="k">高估次数（ΔR&gt;0.2）</div><div class="v">%(over)d</div></div>
</div>
<h2>ΔR 走势（左→右按日期）</h2>
<div class="card" style="padding:8px 10px">%(spark)s
<div class="sub" style="margin-top:6px">虚线 = ΔR 0 轴。点在 0 上方 = 我高估了自己；下方 = 低估。</div></div>
<h2>Skill 健康度</h2>
<table><thead><tr><th>Skill</th><th>状态</th><th>版本</th><th class="num">系统内调用</th>
<th class="num">回填使用</th><th class="num">平均 ΔR</th><th>最近使用</th></tr></thead>
<tbody>%(skills)s</tbody></table>
<h2>KSTAR 经验库</h2>
<table><thead><tr><th>ID</th><th>日期</th><th>情境</th><th class="num">R̂</th><th class="num">R</th>
<th class="num">ΔR</th><th>判定</th></tr></thead><tbody>%(eps)s</tbody></table>
<div class="note">这份看板由 <code>python3 scripts/kstar.py dash</code> 从磁盘上的 Markdown 实时生成，
不是手工维护的截图。删掉本文件、重跑命令，内容会原样重建。</div>
<footer>%(footer)s</footer>
</div></body></html>""" % {
        "now": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "n1": len(list(RAW_DIR.rglob("*.md"))), "n2": len(eps),
        "n3": sum(1 for s in sks if s.get("status") == "active"),
        "n4": len(runs),
        "avg": ("%+.3f" % avg_dr) if avg_dr is not None else "—",
        "over": over,
        "spark": _svg_spark(drs),
        "skills": bar_rows(), "eps": ep_rows(),
        "footer": "skills: " + " · ".join(str(s.get("name")) for s in sks),
    }
    out = REPORT_DIR / "dashboard.html"
    out.write_text(html, encoding="utf-8")
    print("✓ 看板已生成：%s（%d KB，离线可开）" % (out.relative_to(ROOT), out.stat().st_size // 1024))


def cmd_report(a):
    since = a.since or "1970-01-01"
    eps = [e for e in all_episodes() if str(e.get("date")) >= since]
    runs = [r for r in all_runs() if str(r.get("start", ""))[:10] >= since]
    lines = ["# 使用记录（自动生成）", "",
             "> 生成命令：`python3 scripts/kstar.py report --since %s`" % since,
             "> 生成时间：%s" % datetime.now().strftime("%Y-%m-%d %H:%M"), ""]
    lines += ["## 一、KSTAR 循环执行（%d 次）" % len(runs), "",
              "| Run | 开始 | 任务 | Skill | R̂ | R | ΔR |", "|---|---|---|---|---|---|---|"]
    for r in runs:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            r.get("id"), str(r.get("start"))[:16], str(r.get("task"))[:40],
            ", ".join(r.get("skills") or []) or "—", r.get("r_hat"), r.get("r"), r.get("dr")))
    lines += ["", "## 二、经验与 ΔR（%d 条）" % len(eps), "",
              "| ID | 日期 | 标题 | R̂ | R | ΔR | 判定 |", "|---|---|---|---|---|---|---|"]
    for e in sorted(eps, key=lambda x: str(x.get("date"))):
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" % (
            e.get("id"), e.get("date"), str(e.get("title"))[:40],
            e.get("r_hat"), e.get("r"), e.get("dr"), e.get("verdict")))
    lines += ["", "## 三、Skill 使用", "",
              "| Skill | 状态 | 版本 | 系统内调用 | 回填使用 | 最近使用 |", "|---|---|---|---|---|---|"]
    for s in all_skills():
        lines.append("| %s | %s | v%s | %s | %s | %s |" % (
            s.get("name"), s.get("status"), s.get("version"),
            s.get("uses_system") or 0, s.get("uses_backfilled") or 0,
            s.get("last_used") or "—"))
    lines += ["", "## 四、CLI 调用流水（evidence）", "",
              "来源：`logs/usage.jsonl`（每次命令自动追加一行，无法事后编造）。", ""]
    if USAGE.exists():
        recs = [json.loads(x) for x in USAGE.read_text(encoding="utf-8").splitlines() if x.strip()]
        recs = [r for r in recs if r["ts"][:10] >= since]
        lines += ["共 %d 次调用，按命令统计：" % len(recs), "", "| 命令 | 次数 |", "|---|---|"]
        cnt = {}
        for r in recs:
            cnt[r["cmd"]] = cnt.get(r["cmd"], 0) + 1
        for c, n in sorted(cnt.items(), key=lambda x: -x[1]):
            lines.append("| %s | %d |" % (c, n))
    out = REPORT_DIR / "usage_log_auto.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("✓ 使用记录已生成：%s" % out.relative_to(ROOT))
    print("\n".join(lines[:26]))


def cmd_export_skills(a):
    out = Path(a.out).expanduser()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(SKILL_DIR, out)
    n = len(list(out.glob("*/SKILL.md")))
    print("✓ 已导出 %d 个 Skill → %s" % (n, out))


def cmd_selftest(a):
    fails = []

    def check(cond, msg):
        if not cond:
            fails.append(msg)

    fm, body = parse_front("---\na: 1\nb: [x, y]\nc: \"q\"\n---\n正文")
    check(fm["a"] == 1 and fm["b"] == ["x", "y"] and fm["c"] == "q" and "正文" in body,
          "frontmatter 解析")
    check("c9" in [t for _, t in tokenize("C9 家里有什么")], "分词包含拉丁词")
    check(("c2", "家里") in tokenize("家里有什么"), "分词包含中文二元组")
    check(verdict_of(0.0) == "命中" and verdict_of(0.5) == "显著高估" and verdict_of(-0.2) == "低估",
          "ΔR 判定")
    b = "## 使用记录\n\n| a |\n|---|---|\n\n## 迭代史\n\nx\n"
    b2 = append_under_section(b, "## 使用记录", "| new |")
    check("| new |" in b2 and b2.index("| new |") < b2.index("## 迭代史"), "小节插入位置")
    d = recall("家里有什么 搜索", k=3)
    check(isinstance(d, list), "检索可执行")
    print("selftest: %d 项通过，%d 项失败" % (5 - len(fails), len(fails)))
    for f in fails:
        print("  ✗", f)
    return 1 if fails else 0


# ------------------------------------------------------------------- 入口


def build_parser():
    p = argparse.ArgumentParser(
        prog="kstar.py", description="第二大脑 / Agent OS 内核（Markdown 为真相源 + SQLite 索引）")
    sub = p.add_subparsers(dest="cmd")

    s = sub.add_parser("init", help="初始化目录结构")
    s.set_defaults(func=cmd_init)

    s = sub.add_parser("add", help="写入一条 L1 原始笔记")
    s.add_argument("text", nargs="*")
    s.add_argument("--title")
    s.add_argument("--tag", action="append")
    s.add_argument("--source")
    s.add_argument("--date")
    s.set_defaults(func=cmd_add)

    s = sub.add_parser("note", help="L1 笔记状态维护")
    nsub = s.add_subparsers(dest="op")
    q = nsub.add_parser("processed", help="标记 L1 已转 L2（回填场景补标）")
    q.add_argument("names", nargs="+")
    q.set_defaults(func=cmd_note_processed)

    s = sub.add_parser("recall", help="K 步：跨四层检索（带命中理由）")
    s.add_argument("query", nargs="+")
    s.add_argument("--k", type=int, default=5)
    s.add_argument("--layer", default="all", choices=["all", "raw", "episode", "skill"])
    s.set_defaults(func=cmd_recall)

    s = sub.add_parser("ep", help="L2 经验（KSTAR）")
    esub = s.add_subparsers(dest="op")
    q = esub.add_parser("new")
    q.add_argument("--title", required=True)
    q.add_argument("--situation", default="（待补）")
    q.add_argument("--task", default="（待补）")
    q.add_argument("--action", default="（待补）")
    q.add_argument("--result", default="（待补）")
    q.add_argument("--rhat", type=float)
    q.add_argument("--r", type=float)
    q.add_argument("--dr-note")
    q.add_argument("--lesson")
    q.add_argument("--tag", action="append")
    q.add_argument("--skills", action="append")
    q.add_argument("--source")
    q.add_argument("--evidence")
    q.add_argument("--from-note", action="append")
    q.add_argument("--status", default="confirmed", choices=["draft", "confirmed"])
    q.add_argument("--date")
    q.set_defaults(func=cmd_ep_new)
    q = esub.add_parser("list")
    q.add_argument("--tag")
    q.add_argument("--status")
    q.set_defaults(func=cmd_ep_list)
    q = esub.add_parser("show")
    q.add_argument("id")
    q.set_defaults(func=cmd_ep_show)
    q = esub.add_parser("promote")
    q.add_argument("id")
    q.set_defaults(func=cmd_ep_promote)

    s = sub.add_parser("loop", help="L3 Agent Loop：KSTAR 完整循环")
    lsub = s.add_subparsers(dest="op")
    q = lsub.add_parser("start")
    q.add_argument("--task", required=True)
    q.add_argument("--situation")
    q.add_argument("--plan")
    q.add_argument("--rhat", type=float)
    q.add_argument("--skills", action="append")
    q.add_argument("--tag", action="append")
    q.set_defaults(func=cmd_loop_start)
    q = lsub.add_parser("close")
    q.add_argument("run")
    q.add_argument("--actual", required=True)
    q.add_argument("--r", type=float, required=True)
    q.add_argument("--rhat", type=float)
    q.add_argument("--dr-note")
    q.add_argument("--lesson")
    q.set_defaults(func=cmd_loop_close)

    s = sub.add_parser("skill", help="L3 Skill 生命周期")
    ssub = s.add_subparsers(dest="op")
    q = ssub.add_parser("new")
    q.add_argument("--name", required=True)
    q.add_argument("--desc", required=True)
    q.add_argument("--when")
    q.add_argument("--input")
    q.add_argument("--output")
    q.add_argument("--tag", action="append")
    q.add_argument("--status", default="active", choices=["candidate", "active"])
    q.set_defaults(func=cmd_skill_new)
    q = ssub.add_parser("use")
    q.add_argument("name")
    q.add_argument("--note")
    q.add_argument("--result")
    q.add_argument("--dr", type=float)
    q.add_argument("--source")
    q.set_defaults(func=cmd_skill_use)
    q = ssub.add_parser("iterate")
    q.add_argument("name")
    q.add_argument("--note", required=True)
    q.add_argument("--trigger")
    q.set_defaults(func=cmd_