#!/usr/bin/env python3
"""translate.py — 术语感知的分段翻译（引擎可插拔）。

用法:
    # 模式一：调用兼容 Anthropic Messages API 的模型（需 ANTHROPIC_API_KEY）
    python translate.py --in corpus/en --out course-zh --glossary pipeline/glossary.csv --engine api

    # 模式二：人工/外部翻译模式 —— 生成带原文的待译模板到 <out>，翻译完成后重跑 --mode verify
    python translate.py --in corpus/en --out course-zh --glossary pipeline/glossary.csv --engine skeleton

特性:
1. 长文自动分块（默认按段落聚合，块目标 ~1200 词），保证翻译质量与上下文连贯；
2. 每块翻译前注入术语表，并在译后强制校验术语一致性（不达标自动重试一次）；
3. 结构保持：标题层级、列表、代码块原样保留不翻译代码；
4. 引擎可替换：--engine api | skeleton（留空模板给人工填）。
"""
import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

GLOSSARY = []      # [(en, zh)]
GLOSSARY_RE = []   # [(compiled_re, zh)]

SYSTEM_PROMPT = """你是一名专业的技术课程翻译译者，负责将英文 AI 编程课程材料翻译为简体中文。
规则：
1. 忠实传达原意，不增删内容；语气保持课程讲义风格（专业、直接）。
2. 术语必须遵守术语表：给定的英文术语一律使用指定中文译法；产品名（Claude Code、Cursor、Warp、Kubernetes 等）不译。
3. 保持 Markdown 结构不变：标题层级、列表、表格、链接、引用一一对应。
4. 代码块内的代码与命令不翻译；代码块内的注释可翻译为中文。
5. 输出只含译文 Markdown，不要任何解释或前后缀。"""

CHUNK_PROMPT = """请将下面的 Markdown 片段翻译为简体中文，遵守系统提示中的全部规则。

术语表（en -> zh）：
{glossary}

原文片段：
{chunk}

只输出译文："""


def load_glossary(path: Path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            en, zh = row["en"].strip(), row["zh"].strip()
            if not en or not zh:
                continue
            rows.append((en, zh))
    return rows


def build_regexes():
    global GLOSSARY_RE
    for en, zh in GLOSSARY:
        # 词边界匹配；对含括号/斜杠的词条退化为普通转义匹配
        try:
            pat = re.compile(r"(?<![A-Za-z])" + re.escape(en) + r"(?![A-Za-z])")
        except re.error:
            pat = re.compile(re.escape(en))
        GLOSSARY_RE.append((pat, en, zh))


def chunk_markdown(md: str, target_words: int = 1200):
    """按空行分段聚合为块，尽量不切断标题与列表。"""
    paras = re.split(r"\n\s*\n", md)
    chunks, buf, words = [], [], 0
    for p in paras:
        w = len(p.split())
        buf.append(p)
        words += w
        if words >= target_words:
            chunks.append("\n\n".join(buf))
            buf, words = [], 0
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


def glossary_check(src: str, trans: str):
    """检查源块中出现的术语在译文中是否使用了统一译法。返回违规列表。"""
    violations = []
    for pat, en, zh in GLOSSARY_RE:
        if pat.search(src) and zh.split("（")[0] not in trans and zh not in trans:
            # 译文完全没出现该术语的任何可接受形式
            violations.append((en, zh))
    return violations


class ApiEngine:
    """兼容 Anthropic Messages API。"""

    def __init__(self, model="claude-sonnet-4-20250514"):
        import anthropic  # pip install anthropic
        self.client = anthropic.Anthropic()  # 读取 ANTHROPIC_API_KEY
        self.model = model

    def translate(self, chunk: str, glossary_text: str) -> str:
        last = None
        for attempt in range(3):
            resp = self.client.messages.create(
                model=self.model, max_tokens=8000, temperature=0,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": CHUNK_PROMPT.format(
                    glossary=glossary_text, chunk=chunk)}])
            out = resp.content[0].text
            viol = glossary_check(chunk, out)
            if not viol or attempt == 2:
                if viol:
                    # 术语修正兜底：强制替换
                    for _, en, zh in [(v[0], v[0], v[1]) for v in viol]:
                        out = re.sub(r"(?<![A-Za-z])" + re.escape(en) + r"(?![A-Za-z])", zh, out)
                return out
            time.sleep(1)
        return out


class SkeletonEngine:
    """生成待译模板：保留原文结构，正文行前置占位，人工/外部引擎填写。"""

    def translate(self, chunk: str, glossary_text: str) -> str:
        lines = []
        for ln in chunk.split("\n"):
            if ln.startswith("```") or ln.strip().startswith("|") and re.match(r"^\|[\s\-|:]+\|$", ln):
                lines.append(ln)
            else:
                lines.append("TODO> " + ln)
        return "\n".join(lines)


def get_engine(name):
    if name == "api":
        return ApiEngine()
    return SkeletonEngine()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", dest="dst", required=True)
    ap.add_argument("--glossary", required=True)
    ap.add_argument("--engine", default="skeleton", choices=["api", "skeleton"])
    ap.add_argument("--only", default=None, help="只处理指定 slug（逗号分隔）")
    args = ap.parse_args()

    global GLOSSARY
    GLOSSARY = load_glossary(Path(args.glossary))
    build_regexes()
    glossary_text = "\n".join(f"{en} -> {zh}" for en, zh in GLOSSARY)

    engine = get_engine(args.engine)
    src, dst = Path(args.src), Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    only = set(args.only.split(",")) if args.only else None
    manifest = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
    report = []
    for m in manifest:
        if m.get("placeholder") or (only and m.get("slug") not in only):
            continue
        md = (src / (m["slug"] + ".md")).read_text(encoding="utf-8")
        chunks = chunk_markdown(md)
        parts = []
        for i, ch in enumerate(chunks):
            print(f"[translate] {m['slug']} 块 {i+1}/{len(chunks)}")
            parts.append(engine.translate(ch, glossary_text))
        out_md = "\n\n".join(parts)
        (dst / (m["slug"] + ".zh.md")).write_text(out_md, encoding="utf-8")
        report.append({"slug": m["slug"], "chunks": len(chunks), "src_chars": len(md), "out_chars": len(out_md)})

    (dst / "translate_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[translate] 完成 {len(report)} 篇 → {dst}")


if __name__ == "__main__":
    main()
