#!/usr/bin/env python3
"""render_pdf 模块单元测试 —— LaTeX→mathtext 方言转换 + PDF 产出。"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from render_pdf import (  # noqa: E402
    parse_latex_block, strip_unsupported, split_top_level,
    _extract_env, PDFRenderer, solutions_to_pdf, latex_available,
)

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not cond else ""))


def test_env_extract():
    print("\n[1] 环境提取")
    s = r"\begin{aligned} a &= b \\ c &= d \end{aligned}"
    got = _extract_env(s, "aligned")
    check("aligned 环境被提取", len(got) == 1, f"got={got}")
    if got:
        check("aligned body 正确", "b" in got[0][2] and "d" in got[0][2], got[0][2])


def test_split_rows():
    print("\n[2] 顶层分行")
    body = "a &= b \\\\ c &= d"
    rows = split_top_level(body)
    check("按 \\\\ 分成 2 行", len(rows) == 2, f"got={rows}")
    body2 = r"\frac{1}{2} \\ x"
    check("花括号内不误切", len(split_top_level(body2)) == 2, split_top_level(body2))


def test_parse_blocks():
    print("\n[3] 渲染块解析")
    cases = [
        (r"\boxed{x = 2}", "boxed", None),
        (r"\begin{aligned} a &= b \\ c &= d \end{aligned}", "lines", 2),
        (r"\begin{cases} 1 & x>0 \\ 0 & x<=0 \end{cases}", "cases", 2),
        (r"\begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}", "matrix", 2),
        (r"\frac{1}{2}", "inline", None),
    ]
    for src, kind, n in cases:
        blocks = parse_latex_block(src)
        kinds = [b.kind for b in blocks]
        check(f"{kind}: 识别", kind in kinds, f"kinds={kinds}")
        if n is not None:
            blk = next((b for b in blocks if b.kind == kind), None)
            if blk:
                val = blk.lines if kind == "lines" else (blk.rows if kind in ("cases", "matrix") else None)
                check(f"{kind}: 行数={n}", len(val) == n, f"got={len(val)}: {val}")


def test_strip():
    print("\n[4] 不支持命令降级")
    check("\\text → \\mathrm", "\\mathrm" in strip_unsupported(r"\text{hi}"))
    check("\\dfrac → \\frac", "dfrac" not in strip_unsupported(r"\dfrac{1}{2}"))
    check("\\tfrac → \\frac", "tfrac" not in strip_unsupported(r"\tfrac{1}{2}"))
    check("删除 \\!", "\\!" not in strip_unsupported(r"a\\!b"))
    check("删除 \\displaystyle", "displaystyle" not in strip_unsupported(r"\displaystyle x"))


def test_pdf_production():
    print("\n[5] PDF 产出（无 LaTeX 环境）")
    sols = [
        {
            "problem_id": "1",
            "problem_text": "求矩阵 A 的特征值。",
            "solved": True,
            "steps": [
                "构造特征矩阵 $A - \\lambda I$。",
                "$\\det(A - \\lambda I) = \\lambda^2 - 3\\lambda + 2$。",
            ],
            "answer": r"\lambda \in \{1, 2\}",
            "answer_latex": r"\lambda \in \{1, 2\}",
            "verification": {"verdict": "pass", "n_checks": 2, "n_pass": 2,
                             "note": "所有自动验证项通过",
                             "checks": [{"check": "特征对验证", "verdict": "pass",
                                         "evidence": "Av − λv = 0"}]},
            "sub_solutions": [],
        },
        {
            "problem_id": "2",
            "problem_text": "求二重积分区域。",
            "solved": True,
            "steps": ["区域可写为 $D = \\begin{cases} 0 \\le x \\le 1 \\\\ 0 \\le y \\le x \\end{cases}$。"],
            "answer": r"\iint_D f\,dA",
            "answer_latex": r"\iint_D f\,dA",
            "sub_solutions": [],
        },
        {
            "problem_id": "3",
            "problem_text": "这题超出支持范围。",
            "solved": False,
            "reason": "未匹配到已支持模型",
            "steps": [],
            "sub_solutions": [],
        },
    ]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "t.pdf"
        info = solutions_to_pdf(sols, out, course="线性代数", student="JingXueQing",
                               title="作业解答", prefer="mathtext")
        check("PDF 已生成", out.exists(), str(info))
        if out.exists():
            size = out.stat().st_size
            check(f"PDF 体积合理 ({size} B)", size > 3000)
            head = out.read_bytes()[:5]
            check("是合法 PDF", head == b"%PDF-", repr(head))
            check("backend=mathtext", info.get("backend") == "mathtext")
            check("页数 >= 1", info.get("pages", 0) >= 1, str(info.get("pages")))


def test_backend_detection():
    print("\n[6] 后端探测")
    check("latex_available() 返回 bool", isinstance(latex_available(), bool))
    print(f"    （本机 LaTeX: {'有' if latex_available() else '无'} → 走 mathtext）")


def main():
    print("═" * 66)
    print("  render_pdf 单元测试")
    print("═" * 66)
    test_env_extract()
    test_split_rows()
    test_parse_blocks()
    test_strip()
    test_pdf_production()
    test_backend_detection()
    print("\n" + "═" * 66)
    print(f"  通过 {len(PASS)} / {len(PASS) + len(FAIL)}")
    if FAIL:
        print(f"  ❌ 失败: {', '.join(FAIL)}")
    print("═" * 66)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())