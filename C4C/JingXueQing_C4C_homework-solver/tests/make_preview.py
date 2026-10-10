#!/usr/bin/env python3
"""排版预览生成器 —— 把示例解答渲染成 PDF 并导出 PNG，供人工目检。

用法:
    python tests/make_preview.py [out_dir]
"""
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from render_pdf import PDFRenderer  # noqa: E402

SAMPLE = [
    {"problem_id": "1",
     "problem_text": "设 A 为 2×2 矩阵，求其特征值与特征向量。",
     "solved": True,
     "steps": [
         "构造特征矩阵 $A - \\lambda I$。",
         "$\\det(A - \\lambda I) = \\lambda^2 - 3\\lambda + 2$。",
         "",   # 空步骤：应被过滤，不占号
         "解得特征值 1 与 2，对应特征向量分别为 $(1,-1)$ 与 $(1,1)$。",
     ],
     "answer_latex": "\\lambda \\in \\{1, 2\\}",
     "answer": "x",
     "verification": {"verdict": "pass", "n_checks": 2, "n_pass": 2,
                      "note": "所有自动验证项通过", "checks": []},
     "sub_solutions": []},
    {"problem_id": "2",
     "problem_text": "用高斯消元法解方程组，并验证解。",
     "solved": True,
     "steps": [
         "写出增广矩阵：",
         "$\\begin{bmatrix} 1 & 2 \\\\ 3 & 4 \\end{bmatrix}$",
         "第二行减去 3 倍第一行得到行阶梯形：",
         "$\\begin{bmatrix} 1 & 2 \\\\ 0 & -2 \\end{bmatrix}$",
         "回代求解得 $x = 2$，再代回第一行求 $y$。",
     ],
     "answer_latex": "\\boxed{x = 2,\\ y = -\\frac{1}{2}}",
     "answer": "x", "sub_solutions": []},
    {"problem_id": "3",
     "problem_text": "求分段函数在分段点的极限，并判断连续性。",
     "solved": True,
     "steps": [
         "分段函数写作：",
         "$\\begin{cases} x^2 & x < 0 \\\\ -x & x \\ge 0 \\end{cases}$",
         "左极限为 0，右极限为 0，两者相等故极限存在；"
         "又因 $f(0) = 0$ 与极限相等，故在该点连续。",
     ],
     "answer_latex": "\\lim_{x \\to 0} f(x) = 0",
     "answer": "x", "sub_solutions": []},
    {"problem_id": "4",
     "problem_text": "求解一阶常微分方程并给出通解。",
     "solved": False,
     "reason": "题面未给出可识别的初值条件，已回退为通解",
     "steps": [], "sub_solutions": []},
]


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/c4c_preview")
    out.mkdir(parents=True, exist_ok=True)
    pdf = out / "typesetting_preview.pdf"
    r = PDFRenderer(course="线性代数与常微分方程", student="JingXueQing",
                    title="作业解答")
    info = r.render(SAMPLE, pdf)
    print(f"PDF: {info['path']}  pages={info['pages']}  {info['size_bytes']:,}B")
    try:
        import pymupdf
        d = pymupdf.open(pdf)
        for i, p in enumerate(d, 1):
            png = out / f"preview_p{i}.png"
            p.get_pixmap(dpi=110).save(png)
            print(f"PNG: {png}")
    except ImportError:
        print("(未安装 pymupdf，跳过 PNG 导出)")


if __name__ == "__main__":
    main()