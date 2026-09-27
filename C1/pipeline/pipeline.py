#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C1 · 课程资料获取与翻译 —— 可复跑管线（纯标准库，零第三方依赖）

子命令
  sync      归档源文件到 sources/，记录名称/字节/SHA-256（sources/manifest.json）
  extract   源文件 -> 纯文本 -> 定长分段（build/segments.jsonl）
  batch     按每批 N 段生成待译批次（build/batches/batch-NN.md + index.json）
  glossary  由 glossary/术语表.json 渲染 glossary/术语表.md（人读版）
  collect   汇总翻译产物 translation/out/*.md -> build/zh/<doc>.md（按文档归位）
  assemble  回填译文，产出 translation/<doc>.zh.md 与 <doc>.bi.md（中英对照）
  verify    复跑校验：源哈希、段落覆盖度、术语命中

约定
  - 译文由翻译单元产出到 translation/out/<batch>.md，段前标记 `<!-- seg:<doc>#<NNN> -->`
  - collect 归位后 build/zh/<doc>.md 使用 `<!-- seg:NNN -->`（doc 内编号）
示例
  python3 pipeline.py sync && python3 pipeline.py extract && python3 pipeline.py batch --size 16
  python3 pipeline.py collect && python3 pipeline.py assemble && python3 pipeline.py verify
"""
import hashlib, html as H, json, re, shutil, sys, zipfile, zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATS = ROOT / "挑战_C1 课程资料获取与翻译_pxzwy0_材料"
if not MATS.is_dir():
    MATS = ROOT.parent / "挑战_C1 课程资料获取与翻译_pxzwy0_材料"
SRC, BUILD, TRANS = ROOT/"sources", ROOT/"build", ROOT/"translation"
ZH, OUT = BUILD/"zh", TRANS/"out"
GLOS_JSON = ROOT/"glossary"/"术语表.json"
GLOS_MD = ROOT/"glossary"/"术语表.md"
SEG_CHARS = 1200
DROP = re.compile(r"(?is)<(script|style|nav|header|footer|svg|form)\b.*?</\1>")
HEAD = re.compile(r"(?is)<h([1-6])[^>]*>(.*?)</h\1>")


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def html_text(p):
    s = p.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"(?is)<(main|article)[^>]*>(.*?)</\1>", s)
    s = m.group(2) if m else s
    s = DROP.sub(" ", s)
    s = HEAD.sub(lambda x: "\n\n" + "#"*int(x.group(1)) + " " + re.sub(r"<[^>]+>", " ", x.group(2)) + "\n", s)
    s = re.sub(r"(?is)</p>|</li>|<br\s*/?>|</div>|</tr>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = re.sub(r"[ \t\xa0]+", " ", H.unescape(s))
    return re.sub(r"\n\s*\n\s*\n+", "\n\n", s).strip()


def looks_text(s):
    """质量闸门：图片流被误抽成"文本"时整段丢弃（要求可打印占比与字母占比双高）。"""
    if len(s) < 200:
        return False
    printable = sum(1 for c in s if c.isprintable() or c in "\n\t")
    letters = sum(1 for c in s if c.isalpha() or c.isspace())
    return printable / len(s) > 0.95 and letters / len(s) > 0.7


def pdf_text(p):
    """极简 PDF 文本抽取：解压 FlateDecode 流，取 Tj/TJ 字串（无 ToUnicode 时按 latin-1 兜底）。
    图片型 PDF / 无字体表 PDF 会抽不出可用文本，此处返回空串，交由 work/ocr/ 的 OCR 产物接管。"""
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", p.read_bytes(), re.S):
        try:
            raw = zlib.decompress(m.group(1))
        except Exception:
            continue
        if b"Tj" not in raw and b"TJ" not in raw:
            continue
        for t in re.findall(rb"\((?:[^()\\]|\\.)*\)", raw):
            out.append(t[1:-1].decode("latin-1", "ignore"))
    s = re.sub(r"\s+", " ", " ".join(out)).strip()
    return s if looks_text(s) else ""


def pack(doc, kind, path, text):
    paras = [x.strip() for x in re.split(r"\n{2,}", text) if x.strip()]
    out, buf, n = [], [], 0
    for x in paras:
        if n + len(x) > SEG_CHARS and buf:
            out.append("\n\n".join(buf)); buf, n = [], 0
        buf.append(x); n += len(x)
    if buf:
        out.append("\n\n".join(buf))
    return [{"doc": doc, "kind": kind, "source": str(path.relative_to(ROOT)),
             "seg": i + 1, "chars": len(t), "text": t} for i, t in enumerate(out)]


def cmd_sync():
    SRC.mkdir(parents=True, exist_ok=True)
    man = {"materials": [], "note": "由 pipeline.py sync 生成；extract 前请先 sync"}
    for f in sorted(MATS.glob("*")):
        if f.is_dir() or f.name.startswith("._"):
            continue
        dst = SRC / f.name
        shutil.copy2(f, dst)
        man["materials"].append({"name": f.name, "bytes": dst.stat().st_size, "sha256": sha256(dst)})
    off = SRC / "offline"
    for z in sorted(SRC.glob("*.zip")):
        with zipfile.ZipFile(z) as zf:
            zf.extractall(off)
        man["offline_files"] = len([p for p in off.rglob("*") if p.is_file()])
    (SRC / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(man, ensure_ascii=False))


def cmd_extract():
    BUILD.mkdir(parents=True, exist_ok=True)
    rows = []
    for p in sorted((SRC / "offline").rglob("*.html")):
        rows += pack(p.stem, "html", p, html_text(p))
    for pat in ("*.txt", "*.md"):
        for p in sorted((SRC / "offline").rglob(pat)):
            rows += pack(p.stem, pat[2:], p, p.read_text(encoding="utf-8", errors="ignore"))
    pdfs = sorted((SRC / "offline").rglob("*.pdf")) + sorted(SRC.glob("*.pdf"))
    for p in pdfs:
        rows += pack(p.stem, "pdf", p, pdf_text(p))
    # OCR 兜底产物：work/ocr/<doc>.txt（图片型 PDF 经本地 OCR 后落盘）
    for p in sorted((ROOT / "work" / "ocr").glob("*.txt")):
        rows += pack(p.stem, "pdf-ocr", p, p.read_text(encoding="utf-8", errors="ignore"))
    with open(BUILD / "segments.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    docs = sorted({r["doc"] for r in rows})                 # 全部文档（与 verify 分母口径一致）
    docs_gt200 = sorted({r["doc"] for r in rows if r["chars"] > 200})
    print(json.dumps({"segments": len(rows), "chars": sum(r["chars"] for r in rows),
                      "docs": len(docs), "docs_gt200": len(docs_gt200),
                      "pdf_segments": sum(1 for r in rows if r["kind"].startswith("pdf"))},
                     ensure_ascii=False))


def cmd_batch(size=16):
    rows = [json.loads(l) for l in open(BUILD / "segments.jsonl", encoding="utf-8")]
    (BUILD / "batches").mkdir(parents=True, exist_ok=True)
    for stale in (BUILD / "batches").glob("batch-*.md"):  # 先清陈旧批次，避免上一轮残留混入翻译输入
        stale.unlink()
    idx = []
    for i in range(0, len(rows), size):
        grp, name = rows[i:i + size], "batch-%02d.md" % (i // size + 1)
        body = ["# 待译批次 %02d" % (i // size + 1), "",
                "> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。",
                "> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。",
                "> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。",
                "> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。", ""]
        for r in grp:
            body += ["## %s#%03d" % (r["doc"], r["seg"]), "", r["text"], ""]
        (BUILD / "batches" / name).write_text("\n".join(body), encoding="utf-8")
        idx.append({"batch": name, "segments": len(grp), "chars": sum(r["chars"] for r in grp),
                    "docs": sorted({r["doc"] for r in grp})})
    (BUILD / "batches" / "index.json").write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"batches": len(idx), "segments": len(rows),
                      "avg_chars": round(sum(r["chars"] for r in rows) / max(1, len(idx)))},
                     ensure_ascii=False))


def cmd_glossary():
    g = json.loads(GLOS_JSON.read_text(encoding="utf-8"))
    lines = ["# C1 术语表（中英对照）", "", "> 全量翻译统一口径；`术语表.json` 为机读版，本文件由管线渲染。", "",
             "| 英文 | 中文 | 处理口径 |", "|---|---|---|"]
    for t in g["terms"]:
        lines.append("| %s | %s | %s |" % (t["en"], t["zh"], t.get("note", "")))
    if g.get("keep_en"):
        lines += ["", "**保留英文不译**：" + "、".join(g["keep_en"])]
    GLOS_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"terms": len(g["terms"]), "rendered": str(GLOS_MD.relative_to(ROOT))}, ensure_ascii=False))


def parse_zh(text):
    parts = re.split(r"<!--\s*seg:(\d+)\s*-->", text)
    return {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def parse_collect(text):
    """解析跨文档译文：`<!-- seg:doc#NNN -->` -> {doc: {seg: 译文}}"""
    out = {}
    parts = re.split(r"<!--\s*seg:\s*([^#\s]+)#(\d+)\s*-->", text)
    for i in range(1, len(parts) - 2, 3):
        doc, seg, body = parts[i].strip(), int(parts[i + 1]), parts[i + 2].strip()
        if body:
            out.setdefault(doc, {})[seg] = body
    return out


def cmd_collect():
    ZH.mkdir(parents=True, exist_ok=True)
    files = sorted(OUT.glob("*.md")) if OUT.is_dir() else []
    merged, conflicts = {}, []
    for f in files:
        for doc, segs in parse_collect(f.read_text(encoding="utf-8")).items():
            bucket = merged.setdefault(doc, {})
            for k, v in segs.items():
                if k in bucket and bucket[k] != v:
                    conflicts.append("%s#%03d" % (doc, k))
                bucket[k] = v
    for doc, segs in merged.items():
        (ZH / (doc + ".md")).write_text(
            "\n\n".join("<!-- seg:%03d -->\n\n%s" % (k, segs[k]) for k in sorted(segs)),
            encoding="utf-8")
    print(json.dumps({"files": len(files), "docs": len(merged),
                      "segments": sum(len(v) for v in merged.values()),
                      "conflicts": conflicts[:10]}, ensure_ascii=False))


def cmd_assemble():
    TRANS.mkdir(parents=True, exist_ok=True)
    docs = {}
    for s in (json.loads(l) for l in open(BUILD / "segments.jsonl", encoding="utf-8")):
        docs.setdefault(s["doc"], []).append(s)
    made = 0
    for doc, items in sorted(docs.items()):
        f = ZH / (doc + ".md")
        if not f.exists():
            continue
        zh = parse_zh(f.read_text(encoding="utf-8"))
        (TRANS / (doc + ".zh.md")).write_text(
            "# %s（中文）\n\n%s\n" % (doc, "\n\n".join(zh.get(s["seg"], "") for s in items)), encoding="utf-8")
        bi = []
        for s in items:
            bi += ["### seg %03d" % s["seg"], "", s["text"], "",
                   "> " + zh.get(s["seg"], "（未译）").replace("\n", "\n> "), ""]
        (TRANS / (doc + ".bi.md")).write_text("# %s（中英对照）\n\n%s\n" % (doc, "\n".join(bi)), encoding="utf-8")
        made += 1
    print(json.dumps({"docs": len(docs), "assembled": made}, ensure_ascii=False))


def cmd_verify():
    man = json.loads((SRC / "manifest.json").read_text(encoding="utf-8"))
    bad = [m["name"] for m in man["materials"] if sha256(SRC / m["name"]) != m["sha256"]]
    segs = [json.loads(l) for l in open(BUILD / "segments.jsonl", encoding="utf-8")]
    # 分母 = segments.jsonl 里的全部段（与 batch 分批口径一致）。
    # 不再跳过 chars<=200 的短片段：批次文件里分了多少段就要核多少段，
    # 否则短片段会成为免检区，出现「实际漏译却报 100%」的假绿。
    tot, done, miss_seg, tiny, tiny_done = {}, {}, [], {}, {}
    for s in segs:
        tot[s["doc"]] = tot.get(s["doc"], 0) + 1
        f = ZH / (s["doc"] + ".md")
        ok = bool(f.exists() and parse_zh(f.read_text(encoding="utf-8")).get(s["seg"]))
        if ok:
            done[s["doc"]] = done.get(s["doc"], 0) + 1
        else:
            miss_seg.append("%s#%03d" % (s["doc"], s["seg"]))
        if s["chars"] <= 200:  # 单独统计，不再排除
            tiny[s["doc"]] = tiny.get(s["doc"], 0) + 1
            if ok:
                tiny_done[s["doc"]] = tiny_done.get(s["doc"], 0) + 1
    g = json.loads(GLOS_JSON.read_text(encoding="utf-8"))
    # 术语未命中在「已存在的译文文件」上计算，避免只用部分文档而误报
    blob = "\n".join((ZH / (d + ".md")).read_text(encoding="utf-8")
                     for d in sorted(tot) if (ZH / (d + ".md")).exists())
    unused = [t["zh"] for t in g["terms"] if t["zh"] not in blob]
    t_tot, t_done = sum(tot.values()), sum(done.values())
    rep = {"source_hash_ok": not bad, "hash_mismatch": bad,
           "coverage_by_doc": {d: "%d/%d" % (done.get(d, 0), tot[d]) for d in sorted(tot)},
           "coverage": "%d/%d = %.1f%%" % (t_done, t_tot, 100.0 * t_done / max(1, t_tot)),
           "tiny_segments_le200": sum(tiny.values()),
           "tiny_translated": sum(tiny_done.values()),
           "untranslated": miss_seg[:20], "untranslated_count": len(miss_seg),
           "glossary_terms": len(g["terms"]), "glossary_unused": unused[:20]}
    print(json.dumps(rep, ensure_ascii=False))


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    size = 16
    if "--size" in a:
        size = int(a[a.index("--size") + 1])
    cmd = a[0]
    if cmd == "batch":
        cmd_batch(size)
    else:
        {"sync": cmd_sync, "extract": cmd_extract, "glossary": cmd_glossary,
         "collect": cmd_collect, "assemble": cmd_assemble, "verify": cmd_verify}.get(cmd, lambda: print(__doc__))()


if __name__ == "__main__":
    main()
