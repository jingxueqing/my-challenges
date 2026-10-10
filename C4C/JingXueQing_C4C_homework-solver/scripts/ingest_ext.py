#!/usr/bin/env python3
"""
Stage 1 扩展：多格式文档摄入（Markdown / PDF / Word / LaTeX / 纯文本）

starter kit 的 ingest.py 只实现了 Markdown，其余三种格式都是
`raise NotImplementedError`。本模块补齐这些扩展点。

新增能力
────────
| 格式 | 实现 | 备注 |
|------|------|------|
| .md/.txt | 直接读取 | 沿用 starter |
| .tex  | 去注释 + 提取题目环境 | 新增：LaTeX 作业稿 |
| .pdf  | pdfplumber 提取文本；无文本层时尝试 OCR | Level 2 要求 |
| .docx | python-docx 提取段落（含表格） | Level 2 要求 |

PDF 的真实困难（实测记录）
─────────────────────────
数学作业 PDF 常见两种形态：
  1. 文本型 —— pdfplumber 直接拿到文字，但**公式会变成乱码**
     （如 `lim x → 0` 变成 `lim—x!——0`），需要清洗
  2. 扫描型 —— 完全无文本层，必须 OCR，而 Tesseract 对数学公式
     识别率极低（实测约 30~50%），**不应假装能搞定**

因此本模块对扫描型 PDF 明确返回"需人工/需 OCR"，
而不是丢一堆乱码进流水线假装成功。

作者: JingXueQing ｜ C4C Challenge
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


# ══════════════════════════════════════════════════════════════════
# 文本清洗
# ══════════════════════════════════════════════════════════════════

# pdfplumber 在数学 PDF 上常见的碎片化替换
_FRAGMENT_FIXES = [
    (r"ﬁ", "fi"), (r"ﬂ", "fl"), (r"ﬀ", "ff"),
    (r"ﬃ", "ffi"), (r"ﬄ", "ffl"),
    # 连字符断词（行末连字符 + 换行）
    (r"(\w)-\n(\w)", r"\1\2"),
    # 极端空白
    (r"[ \t]{3,}", "  "),
    # 零宽字符
    (r"[-‍﻿]", ""),
]


def clean_pdf_text(text: str) -> str:
    """清洗 PDF 提取出的碎片化文本。"""
    s = text
    for pat, rep in _FRAGMENT_FIXES:
        s = re.sub(pat, rep, s)
    # 保留段落结构：连续空行压缩为最多一个
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


# ══════════════════════════════════════════════════════════════════
# 各格式读取器
# ══════════════════════════════════════════════════════════════════

def read_markdown(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def read_latex(filepath: str) -> str:
    """
    读取 .tex 作业稿 → 转成可解析的 Markdown 风格文本。

    处理：去掉 preamble、注释，把 ``\\begin{enumerate}`` 里的
    ``\\item`` 转成 markdown 题目标记，让 Stage 2 的解析器能识别。
    """
    with open(filepath, "r", encoding="utf-8") as f:
        src = f.read()

    # 去掉注释（注意 \% 是转义）
    src = re.sub(r"(?<!\\)%.*", "", src)
    # 去掉 document 环境与 preamble
    src = re.sub(r"\\documentclass.*?\n", "", src)
    src = re.sub(r"\\begin\{document\}", "", src)
    src = re.sub(r"\\end\{document\}", "", src)
    src = re.sub(r"\\begin\{center\}.*?\\end\{center\}", "", src,
                 flags=re.DOTALL)
    # \item → markdown 题号
    src = re.sub(r"\\item\s*", "\n\nProblem: ", src)
    # 常见数学命令转 markdown 行内公式
    src = re.sub(r"\\\[(.*?)\\\]", r"$$\1$$", src, flags=re.DOTALL)
    src = re.sub(r"\\\((.*?)\\\)", r"$\1$", src, flags=re.DOTALL)
    src = re.sub(r"\\textbf\{(.*?)\}", r"**\1**", src)
    return src.strip()


def read_pdf_text(filepath: str) -> tuple[str, dict]:
    """
    读取文本型 PDF。返回 (text, meta)。

    meta 包含是否检测到文本层、页数、字符数，供上层判断可信度。
    """
    meta = {"backend": "pdfplumber", "has_text_layer": True,
            "pages": 0, "chars": 0, "warnings": []}

    try:
        import pdfplumber
    except ImportError:
        raise RuntimeError(
            "PDF 摄入需要 pdfplumber：pip install pdfplumber"
        )

    chunks = []
    with pdfplumber.open(filepath) as pdf:
        meta["pages"] = len(pdf.pages)
        for i, page in enumerate(pdf.pages, start=1):
            txt = page.extract_text() or ""
            # 表格内容也要（部分作业用表格排版）
            try:
                for tbl in page.extract_tables() or []:
                    for row in tbl:
                        cells = [c for c in row if c]
                        if cells:
                            txt += "\n" + " | ".join(cells)
            except Exception:
                pass
            if txt.strip():
                chunks.append(f"\n\n--- Page {i} ---\n{txt}")

    text = clean_pdf_text("".join(chunks))
    meta["chars"] = len(text)

    # ── 无文本层 → 扫描型 ──
    if meta["chars"] < 40:
        meta["has_text_layer"] = False
        ocr = try_ocr(filepath, meta)
        if ocr is None:
            meta["warnings"].append(
                "该 PDF 无文本层（扫描件），且本机未安装 Tesseract。"
                "数学公式的 OCR 识别率很低（Tesseract 实测约 30~50%），"
                "强行 OCR 会产出大量错误公式 —— 与其给出错答案，"
                "不如明确失败。请改用 Markdown/Word 输入，"
                "或手动转录题目。"
            )
            raise RuntimeError(
                "扫描型 PDF 无法可靠摄入。\n"
                + "\n".join(meta["warnings"])
            )

    # ── 公式碎片告警 ──
    if meta["chars"] > 0:
        # 统计疑似乱码（大量单字符 + 破折号组合）
        suspicious = len(re.findall(r"[—–]{2,}", text))
        if suspicious > 3:
            meta["warnings"].append(
                f"检测到 {suspicious} 处疑似公式碎片（连续破折号），"
                f"PDF 中的公式可能已被破坏，建议核对题面。"
            )
    return text, meta


def try_ocr(filepath: str, meta: dict) -> Optional[str]:
    """尝试用 Tesseract OCR。不可用时返回 None。"""
    if not (shutil.which("tesseract")):
        return None
    try:
        import pytesseract  # noqa: F401
        from PIL import Image
        try:
            import pdf2image  # noqa: F401
        except ImportError:
            meta["warnings"].append("OCR 需要 pdf2image：pip install pdf2image")
            return None
        # 逐页转图再 OCR
        import pdf2image
        pages = pdf2image.convert_from_path(filepath, dpi=300, first_page=1,
                                            last_page=min(6, meta["pages"] or 6))
        outs = [pytesseract.image_to_string(im, lang="chi_sim+eng")
                for im in pages]
        meta["backend"] = "tesseract"
        meta["has_text_layer"] = False
        return clean_pdf_text("\n".join(outs))
    except Exception as e:
        meta["warnings"].append(f"OCR 失败: {e}")
        return None


def read_docx(filepath: str) -> tuple[str, dict]:
    """读取 Word 文档（含表格）。"""
    meta = {"backend": "python-docx", "paragraphs": 0, "tables": 0,
            "warnings": []}
    try:
        import docx
    except ImportError:
        raise RuntimeError("Word 摄入需要 python-docx：pip install python-docx")

    d = docx.Document(filepath)
    parts = []
    for p in d.paragraphs:
        if p.text.strip():
            parts.append(p.text)
    meta["paragraphs"] = len(d.paragraphs)

    for t in d.tables:
        meta["tables"] += 1
        for row in t.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))

    if meta["tables"] and not any(re.search(r"(Problem|题|Q)\s*\d", p)
                                  for p in parts):
        meta["warnings"].append(
            "文档主要内容在表格中，且未识别到题号标记；"
            "请确认表格里是否含 'Problem N' / '题 N' 格式。"
        )
    return "\n\n".join(parts), meta


# ══════════════════════════════════════════════════════════════════
# 统一入口
# ══════════════════════════════════════════════════════════════════

FORMAT_HANDLERS = {
    ".md": lambda p: (read_markdown(p), {"backend": "markdown"}),
    ".markdown": lambda p: (read_markdown(p), {"backend": "markdown"}),
    ".txt": lambda p: (read_markdown(p), {"backend": "text"}),
    ".tex": lambda p: (read_latex(p), {"backend": "latex"}),
    ".latex": lambda p: (read_latex(p), {"backend": "latex"}),
    ".pdf": read_pdf_text,
    ".docx": read_docx,
    ".png": lambda p: (_image_unsupported(p), {}),
    ".jpg": lambda p: (_image_unsupported(p), {}),
    ".jpeg": lambda p: (_image_unsupported(p), {}),
}

SUPPORTED_FORMATS = [".md", ".txt", ".tex", ".pdf", ".docx"]


def _image_unsupported(path: str) -> str:
    raise RuntimeError(
        "图片输入需要视觉模型（OCR / VLM）。\n"
        "本项目未接入视觉能力，且 Tesseract 对手写数学公式识别率极低。\n"
        "建议：用 Markdown/LaTeX 录入题目，或直接把题目文本粘贴给我。\n"
        "（若要接入，可在此处调用 Qwen-VL / Kimi-VL 接口。）"
    )


def ingest(filepath: str) -> dict:
    """
    读取任意格式作业文件，返回结构化结果。

    返回结构在 starter 基础上增加了 `ingest_meta`，记录摄入方式、
    页数、告警等，便于溯源与排错。
    """
    filepath = str(filepath)
    ext = Path(filepath).suffix.lower()
    if ext not in FORMAT_HANDLERS:
        raise ValueError(
            f"不支持的文件格式: {ext}\n"
            f"支持: {', '.join(SUPPORTED_FORMATS)}"
        )

    raw_text, meta = FORMAT_HANDLERS[ext](filepath)
    sections = split_into_sections(raw_text)

    return {
        "source_file": Path(filepath).name,
        "format": ext,
        "raw_text": raw_text,
        "sections": sections,
        "ingest_meta": {
            "backend": meta.get("backend", "unknown"),
            "pages": meta.get("pages"),
            "chars": len(raw_text),
            "n_sections": len(sections),
            "warnings": meta.get("warnings", []),
        },
    }


def split_into_sections(text: str) -> list:
    """按 Markdown 标题分段（沿用 starter 逻辑）。"""
    sections: list = []
    current_title = "Untitled"
    current_lines: list[str] = []

    for line in text.split("\n"):
        m = re.match(r"^(#{1,4})\s+(.+)", line)
        if m:
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append({"title": current_title, "content": content})
            current_title = m.group(2).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append({"title": current_title, "content": content})

    return sections


# ══════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════

def _main() -> None:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="Stage 1: 多格式文档摄入")
    ap.add_argument("input")
    ap.add_argument("output")
    args = ap.parse_args()

    print(f"[Stage 1] 摄入: {args.input}")
    res = ingest(args.input)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(
        json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")

    m = res["ingest_meta"]
    print(f"  格式      : {res['format']}（{m['backend']}）")
    print(f"  字符数    : {m['chars']}")
    print(f"  分段      : {m['n_sections']}")
    for w in m["warnings"]:
        print(f"  ⚠️{w}")
    print(f"  输出      : {args.output}")


if __name__ == "__main__":
    _main()