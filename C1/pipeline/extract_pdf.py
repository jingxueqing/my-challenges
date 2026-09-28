#!/usr/bin/env python3
"""extract_pdf.py — 提取课程 PDF（讲义/报告）文本为 Markdown，供翻译管线消费。

用法:
    python extract_pdf.py --src <pdfs目录> --out corpus/en-pdfs
"""
import argparse
import json
from pathlib import Path

from pdfminer.high_level import extract_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    manifest = []
    for pdf in sorted(Path(args.src).glob("*.pdf")):
        try:
            text = extract_text(str(pdf))
        except Exception as e:
            text = f"[PDF 提取失败: {e}]"
        md = f"---\nsource_file: {pdf.name}\ntype: pdf\n---\n\n" + text
        (out / (pdf.stem + ".md")).write_text(md, encoding="utf-8")
        manifest.append({"file": pdf.name, "slug": pdf.stem, "chars": len(text),
                         "placeholder": len(text) < 500})
        print(f"[pdf] {pdf.name}: {len(text)} 字符")
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2),
                                       encoding="utf-8")


if __name__ == "__main__":
    main()
