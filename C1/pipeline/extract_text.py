#!/usr/bin/env python3
"""extract_text.py — 从课程离线包提取正文文本（HTML → Markdown）。

用法:
    python extract_text.py --src <离线包目录> --out <输出目录> [--map page_map.json]

设计为课程无关（course-agnostic）：只要换一门课的离线包（HTML 页面 + page_map 映射），
重跑本脚本即可得到同一格式的英文语料，供后续 translate.py 消费。

输出:
    <out>/<slug>.md      每页一个 Markdown 文件（正文 + 元信息头）
    <out>/manifest.json  语料清单（页名、来源 URL、字符数），供覆盖度统计
"""
import argparse
import json
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("缺少依赖：请先 pip install beautifulsoup4 lxml")

# 噪声元素：导航/脚本/样式/页眉页脚，全部剔除
NOISE_TAGS = ["script", "style", "noscript", "nav", "footer", "header",
              "aside", "form", "iframe", "svg", "button", "select"]

# 常见 CMS 文章容器的候选选择器（按优先级）
CONTENT_SELECTORS = [
    "article", "main", '[role="main"]', ".post-content", ".article-content",
    ".entry-content", ".markdown-body", "#content", ".content", "body",
]

HEADING_MAP = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}


def clean_soup(soup):
    for t in soup.find_all(NOISE_TAGS):
        t.decompose()
    for t in soup.find_all(attrs={"aria-hidden": "true"}):
        t.decompose()


def pick_container(soup):
    for sel in CONTENT_SELECTORS:
        node = soup.select_one(sel)
        if node and len(node.get_text(strip=True)) > 400:
            return node
    return soup.body or soup


def html_to_markdown(node):
    """轻量 DOM→Markdown：只保留标题/段落/列表/代码/引用/链接文本。"""
    lines = []

    def emit(el, depth=0):
        if isinstance(el, str):
            text = re.sub(r"\s+", " ", el).strip()
            if text:
                lines.append(text)
            return
        name = el.name
        if name in HEADING_MAP:
            text = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
            if text:
                lines.append("\n" + HEADING_MAP[name] + " " + text + "\n")
        elif name in ("p", "section", "div", "figure", "td", "th"):
            for child in el.children:
                emit(child, depth)
            if name in ("p",) and lines and lines[-1] != "":
                lines.append("")
        elif name in ("ul", "ol"):
            idx = 0
            for li in el.find_all("li", recursive=False):
                idx += 1 if name == "ol" else 0
                bullet = f"{idx}. " if name == "ol" else "- "
                text = re.sub(r"\s+", " ", li.get_text(" ", strip=True)).strip()
                if text:
                    lines.append(bullet + text)
            lines.append("")
        elif name in ("pre",):
            code = el.get_text().strip("\n")
            lang = ""
            cls = (el.code.get("class") if el.code else None) or []
            for c in cls:
                if c.startswith("language-"):
                    lang = c.replace("language-", "")
            lines.append(f"\n```{lang}\n{code}\n```\n")
        elif name == "blockquote":
            text = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
            lines.append("\n> " + text + "\n")
        elif name == "table":
            for tr in el.find_all("tr"):
                cells = [re.sub(r"\s+", " ", c.get_text(" ", strip=True)).strip()
                         for c in tr.find_all(["th", "td"])]
                lines.append("| " + " | ".join(cells) + " |")
            lines.append("")
        elif name == "br":
            lines.append("")
        else:
            for child in el.children:
                emit(child, depth)

    emit(node)
    # 压缩多余空行
    out, blank = [], 0
    for ln in lines:
        if ln.strip() == "":
            blank += 1
            if blank > 1:
                continue
        else:
            blank = 0
        out.append(ln.rstrip())
    return "\n".join(out).strip() + "\n"


def extract_page(html_path: Path) -> str:
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(html, "lxml")
    clean_soup(soup)
    title = ""
    if soup.title:
        title = soup.title.get_text(strip=True)
    container = pick_container(soup)
    md = html_to_markdown(container)
    header = f"---\nsource_file: {html_path.name}\ntitle: {title}\n---\n\n"
    return header + md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="课程离线包目录（含 pages/ 子目录）")
    ap.add_argument("--out", required=True, help="语料输出目录")
    ap.add_argument("--map", default=None, help="page_map.json（可选，来源 URL 映射）")
    args = ap.parse_args()

    src = Path(args.src) / "pages"
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    url_map = {}
    if args.map and Path(args.map).exists():
        url_map = json.loads(Path(args.map).read_text(encoding="utf-8"))
        inv = {v: k for k, v in url_map.items()}
    else:
        inv = {}

    manifest = []
    for html_path in sorted(src.glob("*.html")):
        if html_path.stat().st_size < 1024:  # 占位页（如被 Medium 拦截）
            manifest.append({"file": html_path.name, "chars": 0,
                             "url": inv.get(html_path.name, ""), "placeholder": True})
            continue
        md = extract_page(html_path)
        (out / (html_path.stem + ".md")).write_text(md, encoding="utf-8")
        manifest.append({"file": html_path.name, "slug": html_path.stem,
                         "chars": len(md), "url": inv.get(html_path.name, ""),
                         "placeholder": False})

    (out / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = [m for m in manifest if not m.get("placeholder")]
    print(f"[extract] 完成：{len(ok)} 页正文 + {len(manifest)-len(ok)} 占位页 → {out}")
    print(f"[extract] 总正文字符数：{sum(m['chars'] for m in ok)}")


if __name__ == "__main__":
    main()
