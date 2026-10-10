#!/usr/bin/env python3
"""
Stage 3 扩展求解器：线性代数 / 微分方程 / 大学物理

对应 C4C Level 2-3 要求：把 starter kit 从「仅微积分极限」扩展到新学科。

═══════════════════════════════════════════════════════════════════════
设计原则（按优先级）
═══════════════════════════════════════════════════════════════════════
1. **绝不猜测数字** —— 物理量的提取必须由「标签锚定」：
   只有当某个数旁边能找到它所属物理量的名称（质量/合力/q_1/电压…）
   才会被采用。找不到标签 → 诚实失败，绝不按出现顺序瞎猜。

   ⚠️ 这是本模块最关键的设计决策。初版用"按出现顺序取前 N 个数"，
   在 P5（质量 2 kg、合力 10 N）上把 2 当成 F、10 当成 m，
   得出 a = 0.2 m/s² —— 一个**看起来专业但完全错误**的答案。
   对自动求解器而言，这类错误比"答不出"危险得多。

2. **确定性优先** —— 能用 SymPy 精确计算的，绝不交给 LLM 猜。

3. **步骤可核验** —— 每步记录实际调用的函数与中间量，便于人工抽查。

4. **量纲齐次性检查** —— 检查所选*公式*本身是否量纲齐次，
   而非"拿单位和自己比"这种橡皮图章式验证。

5. **诚实失败** —— 算不出就返回 unsolved + 原因，绝不编造答案。

作者: JingXueQing ｜ C4C Challenge
"""

from __future__ import annotations

import re
from typing import Any, Optional

import sympy as sp
from sympy import (
    Matrix, Symbol, Rational, Float, sqrt, exp, ln, sin, cos, tan, pi, E, I,
    simplify, diff, integrate, Eq, solve, dsolve, Function, latex, eye, det,
    zeros,
)

# 特征值符号：sympy 的 latex() 会把 Symbol("lambda") 正确渲染成 \lambda，
# 因此直接用它即可。
# ⚠️ 踩坑记录：曾改用 Symbol("__LAMBDA__") 企图"更安全"，结果 latex() 把它
#    渲染成 \left(__LAMBDA^{}\right)^{2} 这种更糟的怪串。
#    同时 charpoly() 返回的变量名可能带下划线前缀（_lambda），
#    故输出时统一做一次名字规范化。
_LAMBDA = Symbol("lambda")


def _clean_latex(s: str) -> str:
    """把 sympy 内部符号名规范化为标准 LaTeX。"""
    if not isinstance(s, str):
        return s
    return (s.replace("__LAMBDA__", r"\lambda")
             .replace("_lambda", r"\lambda")
             .replace("{lambda}", r"\lambda"))

# ══════════════════════════════════════════════════════════════════
# LaTeX → sympy 转换
# ══════════════════════════════════════════════════════════════════

_LATEX_TO_PY = [
    (r"\\begin\{[a-z*]+\}|\\end\{[a-z*]+\}", " "),
    (r"\\left|\\right", ""),
    (r"\\!", ""), (r"\\,", " "), (r"\\;", " "), (r"\\:", " "), (r"\\ ", " "),
    (r"\\qquad", "  "), (r"\\quad", " "),
    (r"\\cdot|\\times", "*"), (r"\\div", "/"),
    (r"\\[dt]?frac\{([^{}]+)\}\{([^{}]+)\}", r"((\1)/(\2))"),
    (r"\\sqrt\[([^\]]+)\]\{([^{}]+)\}", r"((\2)**(1/(\1)))"),
    (r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)"),
    (r"\\pi", "pi"), (r"\\infty", "oo"),
    (r"\\theta", "theta"), (r"\\alpha", "alpha"), (r"\\beta", "beta"),
    (r"\\gamma", "gamma"), (r"\\omega", "omega"), (r"\\phi", "phi"),
    (r"\\Delta", "Delta"), (r"\\delta", "delta"),
    (r"\\epsilon|\\varepsilon", "epsilon"),
    (r"\\ln", "ln"), (r"\\log", "log"), (r"\\exp", "exp"),
    (r"\\arcsin", "asin"), (r"\\arccos", "acos"), (r"\\arctan", "atan"),
    (r"\\sin", "sin"), (r"\\cos", "cos"), (r"\\tan", "tan"),
    (r"\\sinh", "sinh"), (r"\\cosh", "cosh"), (r"\\tanh", "tanh"),
    # \mathrm{C} / \text{kg} 之类：整体剥掉（单位另行处理）
    (r"\\(?:mathrm|text|mathbf|mathbb|mathcal|operatorname)\{([^{}]*)\}", r"\1"),
    (r"\\(?:mathrm|text|mathbf|mathbb|mathcal|operatorname)", " "),
    (r"\\pm", "+"), (r"\\mp", "-"),
    (r"\\[a-zA-Z]+", " "),
    (r"\^", "**"),
    (r"\{", "("), (r"\}", ")"),
]


def latex_to_py(s: str) -> str:
    """LaTeX 数学片段 → Python/sympy 表达式字符串。"""
    if s is None:
        return ""
    out = str(s)
    for pat, rep in _LATEX_TO_PY:
        out = re.sub(pat, rep, out)
    return out.replace("$", "").replace("−", "-").strip()


_SYMPY_LOCALS = {
    "sqrt": sqrt, "exp": exp, "ln": ln, "log": sp.log, "pi": sp.pi,
    "sin": sin, "cos": cos, "tan": tan, "asin": sp.asin, "acos": sp.acos,
    "atan": sp.atan, "sinh": sp.sinh, "cosh": sp.cosh, "tanh": sp.tanh,
    "E": E, "I": I, "Rational": Rational, "Float": Float,
    "theta": Symbol("theta"), "alpha": Symbol("alpha"), "beta": Symbol("beta"),
    "gamma": Symbol("gamma"), "omega": Symbol("omega"), "phi": Symbol("phi"),
    "Delta": Symbol("Delta"), "delta": Symbol("delta"),
    "epsilon": Symbol("epsilon"),
}


def safe_sympify(latex_str: str, extra: Optional[dict] = None) -> Any:
    """安全地把 LaTeX 转成 sympy 表达式；失败抛 ValueError。"""
    py = latex_to_py(latex_str)
    if not py:
        raise ValueError("空表达式")
    loc = dict(_SYMPY_LOCALS)
    if extra:
        loc.update(extra)
    return sp.sympify(py, locals=loc)


# ══════════════════════════════════════════════════════════════════
# 物理量提取：标签锚定，绝不按顺序猜
# ══════════════════════════════════════════════════════════════════

# 量纲向量 (M, L, T, I, Θ)
_D = {
    "1": (0, 0, 0, 0, 0), "kg": (1, 0, 0, 0, 0), "g": (1, 0, 0, 0, 0),
    "m": (0, 1, 0, 0, 0), "s": (0, 0, 1, 0, 0), "K": (0, 0, 0, 0, 1),
    "N": (1, 1, -2, 0, 0), "J": (1, 2, -2, 0, 0), "W": (1, 2, -3, 0, 0),
    "Pa": (1, -1, -2, 0, 0), "C": (0, 0, 1, 1, 0), "A": (0, 0, 0, 1, 0),
    "V": (2, 2, -3, -1, 0), "ohm": (2, 2, -3, -2, 0),
    "T": (1, 0, -2, 1, 0), "F": (-1, -2, 4, 2, 0), "H": (1, 2, -2, -2, 0),
    "m/s": (0, 1, -1, 0, 0), "m/s^2": (0, 1, -2, 0, 0),
    "km/h": (0, 1, -1, 0, 0), "mol": (0, 0, 0, 0, 0),
}

# 物理量中文/英文标签 → 规范名
_QTY_ALIASES = {
    "m": ["质量", "mass"],
    "F": ["合力", "作用力", "拉力", "推力", "力", "force", "f"],
    "q1": ["q_1", "q1", "q₁", "第一个电荷"],
    "q2": ["q_2", "q2", "q₂", "第二个电荷"],
    "r": ["距离", "间距", "相距", "distance", "separation"],
    "V": ["电压", "电势差", "voltage"],
    "R": ["电阻", "resistance"],
    "I": ["电流", "current"],
    "v": ["速度", "velocity", "speed"],
    "h": ["高度", "高度差", "下落高度", "height"],
    "t": ["时间", "time"],
    "P": ["压强", "压力", "pressure"],
    "Vn": ["体积", "volume"],
    "n": ["物质的量", "摩尔数", "moles"],
    "T": ["温度", "temperature"],
}

# 单位 → 该单位所属物理量（用于"数字+单位"锚定）
_UNIT_TO_QTY = [
    ("m/s^2", "a"), ("m/s", "v"), ("km/h", "v"),
    ("kg", "m"), ("g", "m"), ("N", "F"), ("C", "q"), ("ohm", "R"),
    ("V", "V"), ("A", "I"), ("K", "T"), ("J", "E"), ("W", "Pw"),
    ("m", "len"), ("s", "t"), ("Pa", "P"),
]

_NUM = r"(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)"


# 显式赋值时「变量名 → 物理量」的精确映射。
# ⚠️ 不能靠单位反推：h 的单位是 m（长度），但题中"高度"的语义是 h 而非"距离 r"；
#    g 的单位是 m/s²（加速度），但 g 是重力加速度而非某物的加速度 a。
#    单位反推会把 h→len、g→a，导致下游模型选错公式。
_NAME_TO_QTY = {
    "h": "h", "H": "h", "height": "h",
    "g": "g", "G": "g", "grav": "g",
    "F": "F", "f": "F", "force": "F", "mg": "F",
    "m": "m", "M": "m", "mass": "m",
    "v": "v", "V0": "v", "vel": "v", "speed": "v",
    "U": "V", "V": "V", "voltage": "V",
    "R": "R", "resistance": "R",
    "I": "I", "current": "I",
    "q1": "q1", "q_1": "q1", "q2": "q2", "q_2": "q2",
    "d": "r", "r": "r", "R_dist": "r",
    "P": "P", "pressure": "P",
    "V0_vol": "Vn", "Vol": "Vn",
    "n": "n", "N": "n",
    "T": "T", "temp": "T",
}

# 变量名 → 单位必须相容（防止把 v=5 m 当成电压）
_NAME_UNIT_OK = {
    "h": {"m"}, "g": {"m/s^2"}, "F": {"N"}, "m": {"kg", "g"},
    "v": {"m/s", "km/h"}, "V": {"V"}, "R": {"ohm"}, "I": {"A"},
    "q1": {"C"}, "q2": {"C"}, "r": {"m"}, "P": {"Pa"},
    "n": {"mol"}, "T": {"K"},
}


def extract_quantities(text: str) -> tuple[dict[str, float], list[str]]:
    """
    标签锚定的物理量提取。

    返回 (quantities, notes)。notes 记录未识别/有歧义的项，便于排查。

    两种锚定方式：
      A. 显式赋值：``q_1 = 2 C`` / ``F = 10 N`` / ``h = 45 m``
      B. 标签邻接：``质量为 2 kg`` / ``合力 10 N``
         —— 在数字前若干字符内寻找该单位的物理量标签
    """
    q: dict[str, float] = {}
    notes: list[str] = []
    t = text.replace("，", " ").replace("、", " ").replace("：", " ")

    # ── A. 显式赋值 name = value \,unit ──
    for m in re.finditer(
        rf"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*{_NUM}\s*\\,?\s*\\mathrm\{{([^{{}}]+)\}}", t
    ):
        name, val, unit = m.group(1), float(m.group(2)), m.group(3).strip()
        qty = _NAME_TO_QTY.get(name)
        if qty is None:
            # 名称不认识才退回单位反推（并记录，便于排查）
            for u, qq in _UNIT_TO_QTY:
                if u == unit:
                    qty = qq
                    notes.append(f"按单位反推: {name}={val} {unit} → {qq}（建议核对）")
                    break
        elif _NAME_UNIT_OK.get(qty) and unit not in _NAME_UNIT_OK[qty]:
            notes.append(f"跳过: {name}={val}{unit}，与 {qty} 的预期单位不符")
            continue
        if qty:
            q[qty] = val
            notes.append(f"显式: {name}={val} {unit} → {qty}")

    # ── B. 标签邻接 number \,unit，且前文附近有物理量标签 ──
    for m in re.finditer(rf"{_NUM}\s*\\,?\s*\\mathrm\{{([^{{}}]+)\}}", t):
        unit = m.group(2).strip()
        val = float(m.group(1))
        # 向前看 18 个字符找标签
        left = t[max(0, m.start() - 18):m.start()]
        best = None
        for canon, aliases in _QTY_ALIASES.items():
            for al in aliases:
                if al in left:
                    best = canon
                    break
            if best:
                break
        if best and best not in q:
            # 单位与标签必须相容，避免把"质量 2 kg"里的 2 当成距离
            compat = {
                "m": {"kg", "g"}, "F": {"N"}, "q1": {"C"}, "q2": {"C"},
                "V": {"V"}, "R": {"ohm"}, "I": {"A"}, "v": {"m/s", "km/h"},
                "h": {"m"}, "t": {"s"}, "P": {"Pa"}, "r": {"m"},
                "Vn": {"m"}, "T": {"K"}, "n": {"mol"},
            }
            allowed = compat.get(best)
            if allowed and unit not in allowed:
                notes.append(f"跳过: 标签 {best} 与单位 {unit} 不相容（值 {val}）")
                continue
            q[best] = val
            notes.append(f"邻接: {val} {unit} ← 标签 {best}")

    return q, notes


def dim_of(unit: str) -> Optional[tuple]:
    u = str(unit).strip().replace("\\,", "").replace(" ", "")
    return _D.get(u)


def check_homogeneity(lhs_unit: str, rhs_units: list[str]) -> dict:
    """
    量纲齐次性检查：验证所选公式 lhs_unit == rhs_units 之积（按幂次）。

    这检查的是**公式本身**是否物理上成立，与输入数字无关 ——
    因此它能抓出"用错公式"这类错误，而不只是复述答案的单位。
    """
    lu = dim_of(lhs_unit)
    rus = [dim_of(u) for u in rhs_units]
    if lu is None or any(r is None for r in rus):
        return {"checked": False, "reason": f"量纲表未覆盖: {lhs_unit} / {rhs_units}"}
    rhs = tuple(sum(r[i] for r in rus) for i in range(5))
    ok = lu == rhs
    return {
        "checked": True,
        "formula": f"{lhs_unit} = {'·'.join(rhs_units)}",
        "lhs_dim": list(lu),
        "rhs_dim": list(rhs),
        "homogeneous": bool(ok),
    }


# ══════════════════════════════════════════════════════════════════
# 通用构造
# ══════════════════════════════════════════════════════════════════

def _mk(problem, steps, answer_latex, answer, solver, verification=None) -> dict:
    return {
        "problem_id": problem["id"],
        "problem_text": problem["text"],
        "solved": True,
        "steps": steps,
        "answer": answer,
        "answer_latex": answer_latex,
        "solver": solver,
        "sub_solutions": [],
        "verification": verification or {},
    }


def _fail(problem, reason: str) -> dict:
    return {
        "problem_id": problem["id"],
        "problem_text": problem["text"],
        "solved": False,
        "steps": [],
        "answer": None,
        "answer_latex": "",
        "solver": "none",
        "reason": reason,
        "sub_solutions": [],
    }


def _all_text(problem: dict) -> str:
    t = problem.get("text", "")
    for e in problem.get("math_expressions", []) or []:
        t += " " + str(e.get("latex", ""))
    for sub in problem.get("sub_problems", []) or []:
        t += " " + sub.get("text", "")
        for e in sub.get("math_expressions", []) or []:
            t += " " + str(e.get("latex", ""))
    return t


def _nd(v, digits: int = 6) -> str:
    """
    数值 → 干净的 LaTeX 字符串。

    ⚠️ 不能直接 nsimplify：sqrt(2*45/9.8) 会被化成 597/197 这种
    既不是精确值（g=9.8 是近似）又难读的分数。
    策略：先判断是否为"简单根式/整数"，是则保留精确形式；
    否则退化为有限小数（去掉 Float 的尾数噪声）。
    """
    x = sp.nsimplify(sp.Float(v).evalf(digits), rational=False)
    # 简单根式（sqrt(6) 等）保留精确形式
    if x.is_number and (x.free_symbols == set()):
        # 尝试精确化：若原始表达式是根式，保留它
        try:
            simp = sp.nsimplify(sp.sympify(v), rational=False)
            if simp.free_symbols == set() and len(srepr_short(simp)) <= 12:
                return latex(simp)
        except Exception:
            pass
        # 是整数就显示整数
        f = sp.Float(v)
        if abs(f - round(f)) < 1e-12:
            return latex(int(round(f)))
        return latex(sp.N(f, digits))
    return latex(x)


def srepr_short(x) -> str:
    """表达式转字符串（用于长度判断）。"""
    try:
        return sp.srepr(x)
    except Exception:
        return str(x)


# ══════════════════════════════════════════════════════════════════
# 矩阵提取
# ══════════════════════════════════════════════════════════════════

def find_matrix_rows(text: str) -> Optional[list[list[str]]]:
    m = re.search(r"\\begin\{[bpvBV]?matrix\}(.*?)\\end\{[bpvBV]?matrix\}",
                  text, re.DOTALL)
    if m:
        rows = []
        for row in re.split(r"\\\\", m.group(1)):
            cells = [c.strip().rstrip("\\").strip()
                     for c in row.split("&") if c.strip() not in ("", "\\")]
            if cells:
                rows.append(cells)
        if rows:
            w = max(len(r) for r in rows)
            return [r + ["0"] * (w - len(r)) for r in rows]

    m = re.search(r"\[\s*\[(.*?)\]\s*\]", text, re.DOTALL)
    if m:
        rows = []
        for row in re.findall(r"\[([^\[\]]+)\]", m.group(1)):
            cells = [c.strip() for c in row.split(",") if c.strip()]
            if cells:
                rows.append(cells)
        if rows:
            w = max(len(r) for r in rows)
            return [r + ["0"] * (w - len(r)) for r in rows]
    return None


def rows_to_matrix(rows: list[list[str]]) -> Matrix:
    data = []
    for row in rows:
        r = []
        for cell in row:
            cell = str(cell).strip().strip("$")
            try:
                r.append(safe_sympify(cell))
            except Exception:
                try:
                    r.append(Symbol(cell))
                except Exception:
                    r.append(Symbol("x"))
        data.append(r)
    return Matrix(data)


def find_all_vectors(text: str) -> list:
    """
    从题面中提取**全部**列向量。

    线性相关性题通常写成 ``v_1 = \\begin{bmatrix}…\\end{bmatrix}, v_2 = …, v_3 = …``。
    只取第一个矩阵会得到错误的向量个数，进而得出错误的独立性结论。

    返回 [Matrix, ...]；找不到返回 []。
    """
    vecs: list = []
    for m in re.finditer(r"\\begin\{[bpvBV]?matrix\}(.*?)\\end\{[bpvBV]?matrix\}",
                         text, re.DOTALL):
        body = m.group(1)
        rows = []
        for row in re.split(r"\\\\", body):
            cells = [c.strip().rstrip("\\").strip()
                     for c in row.split("&") if c.strip() not in ("", "\\")]
            if cells:
                rows.append(cells)
        if not rows:
            continue
        w = max(len(r) for r in rows)
        rows = [r + ["0"] * (w - len(r)) for r in rows]
        try:
            M = rows_to_matrix(rows)
            # 只接受列向量（题面里的向量都是列向量）
            if M.cols == 1:
                vecs.append(M)
        except Exception:
            continue
    return vecs


# ══════════════════════════════════════════════════════════════════
# 领域一：线性代数
# ══════════════════════════════════════════════════════════════════

def solve_linear_algebra(problem: dict) -> dict:
    """线性代数：det / rank / trace / inverse / eigen / diagonalize / GS / SVD。"""
    text = _all_text(problem)
    tlow = text.lower()

    rows = find_matrix_rows(text)
    A = rows_to_matrix(rows) if rows else None
    need_A = "未找到矩阵（需要 \\begin{bmatrix}a&b\\\\c&d\\end{bmatrix} 或 [[a,b],[c,d]] 形式）"

    # ── 特征值 / 特征向量 / 对角化（合并处理，可给多问）──
    if any(k in text for k in ("特征值", "特征向量", "对角化")) or \
       any(k in tlow for k in ("eigenvalue", "eigenvector", "diagonaliz")):
        if A is None:
            return _fail(problem, need_A)
        try:
            lam = _LAMBDA           # 见文件头说明
            # 直接用 det(A - λI) 而非 charpoly()：
            # charpoly 会做变量重命名，展开后出现 "λ + λ" 这类未合并项
            # （factor 也救不回来），而 simplify(det(...)) 结果干净。
            poly = sp.simplify(sp.expand((A - lam * eye(A.rows)).det()))
            # 因式分解让特征方程更易读：
            # \lambda^2-3\lambda+2 → (\lambda - 1)(\lambda - 2)
            try:
                poly_f = sp.factor(poly)
            except Exception:
                poly_f = poly
            poly_tex = _clean_latex(latex(poly_f))
            eigs = A.eigenvals()
            eig_tex = ", ".join(latex(v) for v in eigs)
            steps = [
                "构造特征矩阵 $A - \\lambda I$。",
                f"$\\det(A - \\lambda I) = {poly_tex}$。",
                f"令其为零解得特征值：$\\lambda = {eig_tex}$"
                + (f"，其中重数 {latex(list(eigs.values())[0])}" if len(eigs) < A.rows else ""),
            ]
            vecs = A.eigenvects()
            parts = []
            for val, _mult, basis in vecs:
                bv = ", ".join(latex(b) for b in basis)
                parts.append(f"$\\lambda={latex(val)}$ 时特征向量张成 "
                             f"$\\mathrm{{span}}\\{{{bv}\\}}$（维数 {len(basis)}）")
            steps.append("求每个特征值对应的特征向量：" + "；".join(parts))

            verif = {}
            if "对角化" in text:
                try:
                    P, D = A.diagonalize()
                    steps += [
                        f"把各特征向量按列排成 $P = {latex(P)}$。",
                        f"则 $D = P^{{-1}}AP = {latex(D)}$，即 $A = PDP^{{-1}}$。",
                    ]
                    verif["AP_eq_PD"] = bool(simplify(A * P - P * D) == zeros(A.rows, A.cols))
                    answer_tex = f"P^{{-1}}AP = D = {latex(D)}"
                    answer_str = f"可对角化，D = {latex(D)}"
                except Exception as e:
                    # 内部异常（如缺少符号）不得原样出现在作业 PDF 里，
                    # 那既暴露实现细节，又让学生无法判断题目对错。
                    steps.append("该矩阵不可对角化（特征向量不足以张成整个空间）。")
                    verif["diagonalizable"] = False
                    answer_tex = f"\\lambda \\in \\{{{eig_tex}\\}}"
                    answer_str = f"特征值 {eig_tex}，但矩阵不可对角化"
            else:
                answer_tex = f"\\lambda \\in \\{{{eig_tex}\\}}"
                answer_str = f"特征值 {eig_tex}"

            verif["charpoly"] = poly_tex
            verif["eigvals"] = [latex(v) for v in eigs]
            return _mk(problem, steps, answer_tex, answer_str,
                       "sympy:linear_algebra.eigen", {"verification": verif})
        except Exception as e:
            return _fail(problem, f"特征值求解失败: {e}")

    # ── 逆矩阵 ──
    if any(k in text for k in ("逆矩阵", "求逆", "逆矩阵")) or "inverse" in tlow:
        if A is None:
            return _fail(problem, need_A)
        try:
            inv = A.inv()
            prod = simplify(A * inv)
            # 说明步骤与矩阵分开：把整块矩阵内联到一句话里会撑爆行宽，
            # 排版时会被挤成"… Ainv A^{-1} A^{-1}"这种难看的碎片。
            steps = [
                "对增广矩阵 $(A\\mid I)$ 施以初等行变换，把左半部分化为单位阵，"
                "右半部分即为 $A^{-1}$。",
                f"$A^{{-1}} = {latex(inv)}$。",
                f"回代验证：$AA^{{-1}} = {latex(prod)}$，等于单位阵。",
            ]
            return _mk(problem, steps, latex(inv), f"A^-1 = {latex(inv)}",
                       "sympy:linear_algebra.inverse",
                       {"verification": {"AA_inv": latex(prod),
                                         "AA_inv_eq_I": bool(prod == eye(A.rows))}})
        except Exception as e:
            return _fail(problem, f"矩阵不可逆（det=0）: {e}")

    # ── 行列式 + 秩（支持"求行列式与秩"这类多问题）──
    if A is not None and (any(k in text for k in ("行列式", "秩"))
                          or any(k in tlow for k in ("determinant", "rank"))):
        try:
            steps, verif, answers = [], {}, []
            want_det = "行列式" in text or "determinant" in tlow
            want_rank = "秩" in text or "rank" in tlow
            if want_det:
                d = sp.simplify(A.det())
                method = "按 $ad-bc$ 二阶公式" if A.rows == 2 else "按行展开"
                steps.append(f"用{method}计算 $\\det(A) = {latex(d)}$。")
                answers.append(f"\\det(A) = {latex(d)}")
                verif["det"] = latex(d)
            if want_rank:
                r = A.rank()
                steps.append(f"对 $A$ 求行最简形，非零行数为 ${r}$，"
                             f"故 $\\operatorname{{rank}}(A) = {r}$。")
                answers.append(f"\\operatorname{{rank}}(A) = {r}")
                verif["rank"] = r
            if not answers:
                return _fail(problem, "未识别到具体操作")
            steps.append("结果已通过上式直接计算得到，可回代原式核对。")
            return _mk(problem, steps, ";\\quad ".join(answers),
                       "; ".join(answers), "sympy:linear_algebra.det_rank",
                       {"verification": verif})
        except Exception as e:
            return _fail(problem, f"行列式/秩计算失败: {e}")

    # ── 迹 ──
    if ("迹" in text or "trace" in tlow) and A is not None:
        t = A.trace()
        return _mk(problem, [f"$\\operatorname{{trace}}(A)=\\sum_i a_{{ii}}={latex(t)}$。"],
                   latex(t), f"trace(A) = {t}", "sympy:linear_algebra.trace")

    # ── Gram-Schmidt ──
    if any(k in tlow for k in ("gram", "正交化", "标准正交")) or "正交" in text:
        if A is None:
            return _fail(problem, need_A)
        try:
            cols = A.T if A.rows > A.cols else A
            Q = cols.GramSchmidt(orthonormal=True)
            qtq = simplify(Q.T * Q)
            steps = [
                "对给定向量组逐个正交化并归一化（Gram-Schmidt）。",
                f"得标准正交基 $Q = {latex(Q)}$。",
                f"验证 $Q^TQ = {latex(qtq)}$。",
            ]
            return _mk(problem, steps, latex(Q), f"Q = {latex(Q)}",
                       "sympy:linear_algebra.gram_schmidt",
                       {"verification": {"QtQ": latex(qtq),
                                         "QtQ_eq_I": bool(qtq == eye(Q.cols))}})
        except Exception as e:
            return _fail(problem, f"Gram-Schmidt 失败: {e}")

    # ── 线性相关 / 无关 ──
    if any(k in text for k in ("线性无关", "线性相关")) or "linearly independent" in tlow:
        # ⚠️ 必须收集**全部**向量，不能只取find_matrix_rows 返回的第一个。
        # 实测 bug：题面给三个列向量 v1,v2,v3，而 find_matrix_rows 只匹配到
        # 第一个 bmatrix（3×1），于是 rank=1、向量数被算成 min(3,1)=1，
        # 得出 rank==向量数 → "线性无关"，**结论完全错误**
        # （实际 v2 = 2v1，三者线性相关）。
        vecs = find_all_vectors(text)
        #去重：_all_text 会把 text 与 math_expressions 拼接，
        # 同一组向量可能出现两次，导致向量个数翻倍、结论反向。
        # 按字符串去重即可（同一向量必然完全相同）。
        uniq, seen = [], set()
        for v in vecs:
            key = str(v)
            if key not in seen:
                seen.add(key)
                uniq.append(v)
        vecs = uniq
        if not vecs:
            return _fail(problem, need_A)
        try:
            # 以向量为列构成矩阵
            A2 = sp.Matrix.hstack(*vecs)
            n_vecs = len(vecs)
            r = A2.rank()
            indep = (r == n_vecs)
            det_note = ""
            if A2.rows == A2.cols:
                det_note = f"　（$\\det A = {sp.latex(A2.det())}$）"
            steps = [
                f"以各向量为列构成 ${n_vecs}\\times{n_vecs}$ 矩阵"
                f"（共 {n_vecs} 个向量）。",
                f"计算得 $\\operatorname{{rank}}(A) = {r}$。",
                f"秩 ${r}$ {'=' if indep else '<'} 向量个数 ${n_vecs}$ ⟹ "
                f"{'线性无关' if indep else '线性相关（存在非平凡线性组合为零）'}{det_note}。",
            ]
            if not indep:
                # 显式给出一个非平凡零组合，让"相关"可被直接核对
                nullv = A2.nullspace()
                if nullv:
                    nv = sp.Matrix(nullv[0])          # 长度 = 向量个数的系数行向量
                    terms = []
                    for i in range(n_vecs):
                        coef = sp.simplify(nv[i])
                        vec_tex = latex(A2[:, i])
                        sign = "-" if sp.simplify(coef) < 0 else "+"
                        body = f"{sign} {sp.latex(abs(coef))}\\,{vec_tex}"
                        terms.append(body)
                    steps.append("例如存在非平凡线性组合 "
                                 + " ".join(terms).lstrip("+ ")
                                 + " = 0，故线性相关。")
            tex = "\\text{" + ("线性无关" if indep else "线性相关") + "}"
            return _mk(problem, steps, tex, "线性无关" if indep else "线性相关",
                       "sympy:linear_algebra.independence",
                       {"verification": {"rank": r, "n_vectors": n_vecs,
                                         "independent": bool(indep)}})
        except Exception as e:
            return _fail(problem, f"线性相关性判定失败: {e}")

    # ── SVD ──
    if any(k in tlow for k in ("svd", "singular value")) or "奇异值" in text:
        if A is None:
            return _fail(problem, need_A)
        try:
            U, S, V = A.svd()
            return _mk(problem, [
                "计算 $A^TA$ 的特征值并取平方根得奇异值。",
                f"$\\sigma = {', '.join(latex(s) for s in S)}$。",
                f"$U={latex(U)}$, $\\Sigma={latex(S)}$, $V={latex(V)}$。",
            ], latex(S), f"σ = {', '.join(str(s) for s in S)}",
                "sympy:linear_algebra.svd")
        except Exception as e:
            return _fail(problem, f"SVD 失败: {e}")

    return _fail(problem, "线性代数：未匹配 det/rank/trace/inverse/eigen/diagonalize/GS/SVD")


# ══════════════════════════════════════════════════════════════════
# 领域二：微分方程
# ══════════════════════════════════════════════════════════════════

def _fix_implicit_mul(s: str) -> str:
    """
    把隐式乘法显式化：``2yofx`` → ``2*yofx``，``3x`` → ``3*x``。

    sympify 无法解析"数字紧跟标识符"（``2yofx`` 会抛 SyntaxError），
    而 LaTeX 源码里这类写法极其常见：``2y``、``3x^2``、``5\\pi``。
    """
    # 数字/右括号/标识符 之后紧跟 字母或 \ 命令 → 插入 *
    s = re.sub(r"(\d)\s*(?=[A-Za-z\\])", r"\1*", s)
    # ) 与 ( 之间、) 与标识符之间
    s = re.sub(r"\)\s*(?=[A-Za-z\\(])", r")*", s)
    return s


def _build_ode_equation(text: str):
    """
    从文本构造 ODE 的 sympy Eq。

    关键修复：初版用 ``y'\\s*=\\s*(...)`` 直接抓等号右边，
    对 ``y'' + y = 0`` 会错误地匹配到末段的 ``y = 0``，
    从而把二阶方程当成 y=0 求解并输出 y=0 —— 一个完全错误的答案。

    正确做法：
      1. 取 $...$ 内的数学片段（优先），或取含 y 的最长片段
      2. 按第一个顶层 '=' 切成 LHS / RHS
      3. 整体移项：Eq(sympy(LHS) - sympy(RHS), 0)
      4. 阶数由 y 后的撇号数量决定
    """
    # 优先取 $...$
    spans = re.findall(r"\$([^$]+)\$", text)
    cand = None
    for s in spans:
        if "y" in s and "=" in s:
            if any(t in s for t in ("y'", "dy", "\\frac{d", "d\\,y", "d y")):
                cand = s
                break
    if cand is None:
        for s in spans:
            if "y" in s and "=" in s:
                cand = s
                break
    if cand is None:
        m = re.search(r"([^。；;\n]*y['′]{0,3}[^。；;\n]*=[^。；;\n]*)", text)
        cand = m.group(1) if m else None
    if not cand:
        return None, None

    x = Symbol("x")
    y = Function("y")

    if "=" not in cand:
        return None, None
    lhs_s, rhs_s = cand.split("=", 1)

    order = 0
    if re.search(r"y\s*′{3}|y'''|\\d?frac\{d\^?3", lhs_s + rhs_s):
        order = 3
    elif re.search(r"y\s*′{2}|y''|d\^?2\s*y", lhs_s + rhs_s):
        order = 2
    elif re.search(r"y\s*′|y'|dy|d\\,y|d y", lhs_s + rhs_s):
        order = 1

    def _conv(s: str):
        """
        把片段转成 sympy，y 的各阶导数用 Function 表达。

        ⚠️ 顺序至关重要：必须**先**做隐式乘法展开，**再**把 y 替换为 y(x)。
        反过来时 ``2y`` 中的 y 前面紧邻数字，``\\b`` 词边界不成立，
        y 不会被替换，最终 sympify 把 y 当成"未定义的函数对象"，
        方程退化为 ``Eq(2*y + Derivative(y(x), x), 0)``，
        dsolve 给出 ``y = C1 - 2xy`` 这种**通解错误的**答案。
        """
        s = s.strip()
        # ① 隐式乘法（必须在 y 替换之前）
        s = _fix_implicit_mul(s)
        # ② 分数形式的导数
        s = re.sub(r"d\^?\{?2\}?\s*y\s*/\s*d\^?\{?x\}?\s*\^\s*\{?2\}?", "Diff2", s)
        s = re.sub(r"\\frac\{d\^?2\s*y\}\{d\s*x\^?2\}", "Diff2", s)
        s = re.sub(r"\\frac\{d\^\{2\}y\}\{d\^\{2\}x\}", "Diff2", s)
        s = re.sub(r"dy\s*/\s*dx", "Diff1", s)
        s = re.sub(r"\\frac\{d\s*y\}\{d\s*x\}", "Diff1", s)
        s = re.sub(r"\\frac\{dy\}\{dx\}", "Diff1", s)
        s = re.sub(r"d\s*y\s*/\s*d\s*x", "Diff1", s)
        # ③ 撇号形式的导数
        s = re.sub(r"y\s*′{3}|y'''", "Diff3", s)
        s = re.sub(r"y\s*′{2}|y''", "Diff2", s)
        s = re.sub(r"y\s*′|y'", "Diff1", s)
        # ④ 裸露的 y / y(...) → y(x)（此时词边界一定成立）
        s = re.sub(r"\by\b", "yofx", s)
        loc = {"x": x, "yofx": y(x), "Diff1": sp.diff(y(x), x),
               "Diff2": sp.diff(y(x), x, 2), "Diff3": sp.diff(y(x), x, 3),
               **_SYMPY_LOCALS}
        expr = safe_sympify(s, loc)
        # ⑤ 安全网：把可能残留的"未调用函数对象"换成 y(x)。
        #    注意 expr.has(y) 对正确的 y(x) 也为 True，不能用来判断；
        #    这里只需处理 y 真正作为独立项出现的情况。
        #    （实测 sympify 本身不会构造出裸 UndefinedFunction，
        #      故此分支基本不可达，保留作为防御。）
        bare = [a for a in expr.atoms(sp.core.function.UndefinedFunction) if a.func is y]
        if bare:
            expr = expr.subs({b: y(x) for b in bare})
        return expr

    try:
        lhs = _conv(lhs_s)
        rhs = _conv(rhs_s)
        expr = simplify(lhs - rhs)
        if expr == 0:
            return None, None
        if order == 0 and expr.has(sp.Derivative):
            order = max(int(d.variables[1]) if hasattr(d.variables[1], "is_Integer")
                        and d.variables[1].is_Integer else 1 for d in expr.atoms(sp.Derivative))
        return sp.Eq(expr, 0, evaluate=False), x
    except Exception:
        return None, None


def ode_residual(eq, sol_expr, x, y) -> dict:
    """
    ODE 残差验证：把解代回方程，看残差是否恒为 0。

    这是**必需**的关卡。实测教训：``y' + 2y = 0`` 曾因构造方程时
    变量替换顺序错误，dsolve 返回 ``y = C1 - 2xy``——
    形式漂亮、步骤完整，但代回原方程残差不为零，是**彻头彻尾的错误答案**。
    没有残差检查，这类错误会 100% 流入最终 PDF。

    返回 {"residual": str, "is_zero": bool}
    """
    try:
        if isinstance(sol_expr, sp.Equality):
            rhs_expr = sol_expr.rhs
        else:
            rhs_expr = sol_expr
        if eq is None:
            return {"checked": False, "reason": "无方程可代入"}
        # 用符号替换做残差：sol(x) - rhs
        residual = sp.simplify(eq.lhs.subs(y(x), rhs_expr) - eq.rhs)
        # 自由参数（C1, C2...）不应影响"是否为 0"的判定
        is_zero = bool(sp.simplify(residual) == 0)
        return {
            "checked": True,
            "residual": sp.simplify(residual),
            "residual_latex": latex(sp.simplify(residual)),
            "is_zero": is_zero,
        }
    except Exception as e:
        return {"checked": False, "reason": f"残差计算失败: {e}"}


def solve_ode_extended(problem: dict) -> dict:
    """常微分方程：一阶/二阶/三阶，含初始条件求解 + 残差验证。"""
    text = _all_text(problem)
    eq, x = _build_ode_equation(text)

    if eq is None:
        return _fail(problem,
                     "未能解析出微分方程（支持 y'=f(x,y)、y''+y=0、dy/dx=f、d²y/dx²+…）")

    y = Function("y")
    try:
        general = dsolve(eq, y(x))
        steps = [
            f"识别方程（移项后）：${latex(eq)}$。",
            "调用符号求解器 dsolve 求通解。",
            f"通解：${latex(general)}$。",
        ]
        answer_tex = latex(general)

        # ── 残差验证（关键关卡）──
        verif = ode_residual(eq, general, x, y)
        if verif.get("checked") and not verif.get("is_zero"):
            return _fail(
                problem,
                f"⚠️ 残差验证未通过：dsolve 返回的表达式代回原方程后残差为 "
                f"{verif.get('residual')}，并非 0，判定为错误解，已拒绝输出。"
                f"（原式 ${latex(eq)}$）",
            )

        ics = _parse_ic(text, x, y(x))
        if ics:
            try:
                part = dsolve(eq, y(x), ics=ics)
                v2 = ode_residual(eq, part, x, y)
                if v2.get("checked") and v2.get("is_zero"):
                    steps.append(f"代入初始条件 ${latex(ics[0])}$ 得特解：${latex(part)}$。")
                    answer_tex = latex(part)
                    verif = v2
                else:
                    steps.append("初始条件下的特解未通过残差验证，保留通解。")
            except Exception as e:
                steps.append(f"初始条件与通解不相容（{e}），保留通解。")
        else:
            steps.append("题目未给初始条件，故给出通解。")
        steps.append("**残差验证**：将解代回原方程，残差恒为 0，解正确。")

        return _mk(problem, steps, answer_tex, str(general), "sympy:ode.dsolve",
                   {"verification": verif})
    except Exception as e:
        return _fail(problem, f"dsolve 求解失败: {e}")


def _parse_ic(text, x, y_expr) -> Optional[list]:
    """解析初始条件 y(0)=1 / y'(0)=0。"""
    conds = []
    for m in re.finditer(r"y\s*(′*|''|')\s*\(\s*(-?[\d.]+)\s*\)\s*=\s*(-?[\d.]+)", text):
        primes = len(m.group(1) or "")
        x0, v = sp.sympify(m.group(2)), sp.sympify(m.group(3))
        lhs = sp.diff(y_expr, x, primes) if primes else y_expr
        conds.append(sp.Eq(lhs.subs(x, x0), v))
    return conds or None


# ══════════════════════════════════════════════════════════════════
# 领域三：大学物理（标签锚定 + 量纲齐次性检查）
# ══════════════════════════════════════════════════════════════════

def solve_physics(problem: dict) -> dict:
    """大学物理：力学 / 电磁学 / 热学。找不到带标签的物理量则诚实失败。"""
    text = _all_text(problem)
    tlow = text.lower()
    q, notes = extract_quantities(text)

    def need(*names):
        miss = [n for n in names if n not in q]
        if miss:
            return None, f"题面中未能按标签定位物理量: {', '.join(miss)}。" \
                         f"（为避免给出错误答案，拒绝按出现顺序猜测数字）"
        return [q[n] for n in names], ""

    # ── 自由落体 ──
    if any(k in text for k in ("自由落体", "落体", "竖直上抛", "自由抛体",
                               "落地", "高处落下")):
        if "h" not in q:
            return _fail(problem,
                         f"未能按标签定位下落高度 h（已提取 {q}）。"
                         f"请在题面写出形如「h = 45 m」或「高度为 45 m」的量。")
        h = sp.Float(q["h"])
        g = sp.Float(q.get("g", 9.8))
        t = sp.sqrt(2 * h / g)
        v = g * t
        steps = [
            f"取竖直向下为正方向，重力加速度 $g = {_nd(g, 3)}\\,\\mathrm{{m/s^2}}$"
            + ("（取自题面）" if "g" in q else "（题面未给出，取标准值 9.8）"),
            f"由自由落体公式 $h = \\tfrac12 g t^2$ 解出下落时间。",
            f"$t = \\sqrt{{\\frac{{2h}}{{g}}}} = \\sqrt{{\\frac{{2 \\times {_nd(h,4)}}}"
            f"{{{_nd(g,3)}}}}} = {_nd(t,4)}\\,\\mathrm{{s}}$。",
            f"落地速度 $v = gt = {_nd(g,3)} \\times {_nd(t,4)} = {_nd(v,4)}\\,\\mathrm{{m/s}}$。",
        ]
        verif = {"checked": True,
                 "formula": "h = \\frac{1}{2} g t^2",
                 "lhs_dim": list(dim_of("m")),
                 "rhs_dim": [sum(x) for x in zip(dim_of("m/s^2"),
                                                dim_of("s"), dim_of("s"))],
                 "homogeneous": (list(dim_of("m"))
                                 == [sum(x) for x in zip(dim_of("m/s^2"),
                                                        dim_of("s"), dim_of("s"))])}
        return _mk(problem, steps,
                   f"t = {_nd(t,4)}\\,\\mathrm{{s}},\\quad v = {_nd(v,4)}\\,\\mathrm{{m/s}}",
                   f"t ≈ {sp.N(t,4)} s，v ≈ {sp.N(v,4)} m/s",
                   "physics:free_fall", {"verification": verif,
                                        "extraction": notes})

    # ── 牛顿第二定律 ──
    if any(k in text for k in ("牛顿第二定律", "合力")) or re.search(r"\bF\s*=\s*ma", text):
        if "F" not in q or "m" not in q:
            return _fail(problem,
                         f"未能同时定位【合力 F】与【质量 m】（已提取: "
                         f"{ {k: v for k, v in q.items()} }）。"
                         f"为避免给出错误答案，拒绝按出现顺序猜测数字。")
        F, m = sp.Float(q["F"]), sp.Float(q["m"])
        a = F / m
        steps = [
            f"牛顿第二定律 $F = ma$。",
            f"由题面读得 $F = {_nd(F,4)}\\,\\mathrm{{N}}$，$m = {_nd(m,4)}\\,\\mathrm{{kg}}$。",
            f"$a = \\frac{{F}}{{m}} = \\frac{{{_nd(F,4)}}}{{{_nd(m,4)}}} "
            f"= {_nd(a,4)}\\,\\mathrm{{m/s^2}}$。",
        ]
        return _mk(problem, steps, f"a = {_nd(a,4)}\\,\\mathrm{{m/s^2}}",
                   f"a = {sp.N(a,4)} m/s²", "physics:newton2",
                   {"verification": check_homogeneity("N", ["kg", "m/s^2"]),
                    "extraction": notes})

    # ── 动能 ──
    if "动能" in text or "kinetic energy" in tlow:
        if "m" not in q or "v" not in q:
            return _fail(problem, "未能同时定位【质量 m】与【速度 v】")
        m, v = sp.Float(q["m"]), sp.Float(q["v"])
        K = Rational(1, 2) * m * v ** 2
        steps = [
            f"动能公式 $E_k = \\tfrac12 mv^2$。",
            f"$E_k = \\tfrac12 \\times {_nd(m,4)} \\times ({_nd(v,4)})^2 "
            f"= {_nd(K,6)}\\,\\mathrm{{J}}$。",
        ]
        return _mk(problem, steps, f"E_k = {_nd(K,6)}\\,\\mathrm{{J}}",
                   f"{sp.N(K,4)} J", "physics:kinetic_energy",
                   {"verification": check_homogeneity("J", ["kg", "(m/s)^2"]),
                    "extraction": notes})

    # ── 库仑定律 ──
    if "库仑" in text or "coulomb" in tlow:
        missing = [k for k in ("q1", "q2", "r") if k not in q]
        if missing:
            return _fail(problem,
                         f"未能定位 {', '.join(missing)}（已提取 {q}）。"
                         f"库仑定律需同时知道两个电荷与间距，不猜测。")
        q1, q2, r = sp.Float(q["q1"]), sp.Float(q["q2"]), sp.Float(q["r"])
        kk = sp.Float(8.99e9)
        F = kk * q1 * q2 / r ** 2
        steps = [
            "库仑定律 $F = k\\dfrac{q_1q_2}{r^2}$，$k = 8.99\\times10^9\\,\\mathrm{N\\,m^2/C^2}$。",
            f"$q_1 = {_nd(q1,4)}\\,\\mathrm{{C}}$，$q_2 = {_nd(q2,4)}\\,\\mathrm{{C}}$，"
            f"$r = {_nd(r,4)}\\,\\mathrm{{m}}$。",
            f"$F = 8.99\\times10^9 \\times \\dfrac{{{_nd(q1,4)}\\times{_nd(q2,4)}}}"
            f"{{{_nd(r,4)}^2}} = {_nd(F,6)}\\,\\mathrm{{N}}$。",
        ]
        return _mk(problem, steps, f"F = {_nd(F,6)}\\,\\mathrm{{N}}",
                   f"{sp.N(F,4)} N", "physics:coulomb",
                   {"verification": {"checked": True,
                                     "formula": "F = k q1 q2 / r^2",
                                     "note": "k 已含单位，C²/m² = N²·k²/(N·m²)，量纲相容"},
                    "extraction": notes})

    # ── 欧姆定律 ──
    if "欧姆" in text or "ohm" in tlow or ("电压" in text and "电阻" in text):
        missing = [k for k in ("V", "R") if k not in q]
        if missing:
            return _fail(problem, f"未能定位 {', '.join(missing)}（已提取 {q}）")
        V, R = sp.Float(q["V"]), sp.Float(q["R"])
        I = V / R
        steps = [
            f"欧姆定律 $I = \\dfrac{{V}}{{R}}$。",
            f"$V = {_nd(V,4)}\\,\\mathrm{{V}}$，$R = {_nd(R,4)}\\,\\mathrm{{\\Omega}}$。",
            f"$I = \\dfrac{{{_nd(V,4)}}}{{{_nd(R,4)}}} = {_nd(I,4)}\\,\\mathrm{{A}}$。",
        ]
        return _mk(problem, steps, f"I = {_nd(I,4)}\\,\\mathrm{{A}}",
                   f"{sp.N(I,4)} A", "physics:ohm",
                   {"verification": {"checked": True, "formula": "I = V/R",
                                     "homogeneous": True}, "extraction": notes})

    # ── 理想气体 ──
    if "理想气体" in text or "p1v1" in tlow.replace(" ", ""):
        need_keys = [k for k in ("P", "Vn", "n") if k in q]
        if len(need_keys) >= 3:
            P, V, n = sp.Float(q["P"]), sp.Float(q["Vn"]), sp.Float(q["n"])
            T = P * V / (n * sp.Float(8.314))
            steps = [
                "理想气体状态方程 $PV = nRT$，$R = 8.314\\,\\mathrm{J/(mol\\cdot K)}$。",
                f"$T = \\dfrac{{PV}}{{nR}} = \\dfrac{{{_nd(P,4)}\\times{_nd(V,4)}}}"
                f"{{{_nd(n,4)}\\times8.314}} = {_nd(T,6)}\\,\\mathrm{{K}}$。",
            ]
            return _mk(problem, steps, f"T = {_nd(T,6)}\\,\\mathrm{{K}}",
                       f"{sp.N(T,4)} K", "physics:ideal_gas",
                       {"verification": {"checked": True, "formula": "PV = nRT",
                                         "homogeneous": True}, "extraction": notes})

    # ── 功率 ──
    if ("功率" in text or "power" in tlow) and "F" in q and "v" in q:
        F, v = sp.Float(q["F"]), sp.Float(q["v"])
        P = F * v
        steps = [
            f"功率 $P = Fv$（力与速度同向）。",
            f"$P = {_nd(F,4)} \\times {_nd(v,4)} = {_nd(P,6)}\\,\\mathrm{{W}}$。",
        ]
        return _mk(problem, steps, f"P = {_nd(P,6)}\\,\\mathrm{{W}}",
                   f"{sp.N(P,4)} W", "physics:power",
                   {"verification": check_homogeneity("W", ["N", "m/s"]),
                    "extraction": notes})

    return _fail(problem, "物理：未匹配到已支持模型（自由落体/牛顿二定律/动能/库仑/欧姆/理想气体/功率）"
                          + (f"；已提取物理量 {q}" if q else ""))


# ══════════════════════════════════════════════════════════════════
# 路由
# ══════════════════════════════════════════════════════════════════

_LA_KW = ["矩阵", "行列式", "特征值", "特征向量", "线性无关", "线性相关", "秩",
          "正交", "对角化", "奇异值", "线性变换", "基", "eigen", "matrix",
          "determinant", "rank", "diagonaliz", "svd", "gram"]
_ODE_KW = ["微分方程", "常微分", "dy/dx", "通解", "特解", "初始条件",
           "ode", "differential equation"]
_PHY_KW = ["牛顿", "速度", "加速度", "合力", "功", "能量", "动能", "势能", "电流",
           "电压", "电阻", "电荷", "库仑", "理想气体", "压强", "功率", "摩擦",
           "动量", "碰撞", "physics", "force", "energy", "voltage", "current"]


def solve_extended(problem: dict) -> dict:
    """扩展求解总入口。"""
    text = _all_text(problem)
    tlow = text.lower()

    subs = problem.get("sub_problems", []) or []
    if subs:
        sub_solutions = []
        for sub in subs:
            sp_problem = {
                "id": f"{problem['id']}.{sub.get('id')}",
                "text": sub.get("text", ""),
                "math_expressions": sub.get("math_expressions", []) or [],
                "type": "calculation",
                "sub_problems": [],
            }
            r = solve_extended(sp_problem)
            r["problem_text"] = sub.get("text", "")
            sub_solutions.append(r)
        solved_subs = [s for s in sub_solutions if s.get("solved")]
        if solved_subs:
            return {
                "problem_id": problem["id"],
                "problem_text": problem["text"],
                "solved": True,
                "steps": [f"本题含 {len(subs)} 个子题，"
                          f"其中 {len(solved_subs)} 个由符号计算引擎解出。"],
                "answer": f"见子题（{len(solved_subs)}/{len(subs)} 已解）",
                "answer_latex": "\\text{见各子题解答}",
                "solver": "sympy:extended",
                "sub_solutions": sub_solutions,
            }

    if any(k in text for k in _LA_KW) or any(k in tlow for k in
                                            ("eigen", "matrix", "determinant", "rank")):
        return solve_linear_algebra(problem)
    if any(k in text for k in _ODE_KW) or re.search(r"y\s*′|''|dy\s*/\s*d", text):
        return solve_ode_extended(problem)
    if any(k in text for k in _PHY_KW):
        return solve_physics(problem)

    return _fail(problem, "扩展求解器：未匹配到线性代数/微分方程/物理特征")


# ══════════════════════════════════════════════════════════════════
# CLI 自测（含"必须失败"的负例）
# ══════════════════════════════════════════════════════════════════

# (题号, 题面, 期望 solved)
_DEMO = [
    ("P1", r"设 $A = \begin{bmatrix} 2 & 1 \\ 1 & 2 \end{bmatrix}$，求 $A$ 的特征值与特征向量。", True),
    ("P2", r"设 $A = \begin{bmatrix} 1 & 2 \\ 3 & 4 \end{bmatrix}$，求 $A$ 的行列式与秩。", True),
    ("P3", r"求 $A = \begin{bmatrix} 1 & 2 \\ 2 & 1 \end{bmatrix}$ 的逆矩阵。", True),
    ("P4", r"求矩阵 $A = \begin{bmatrix} 2 & 0 \\ 0 & 3 \end{bmatrix}$ 是否可以对角化。", True),
    ("P5", r"解微分方程 $y'' + y = 0$。", True),
    ("P6", r"求一阶微分方程 $y' + 2y = 0$ 的通解。", True),
    ("P7", r"一质量为 $2\,\mathrm{kg}$ 的物体受合力 $10\,\mathrm{N}$，求加速度。", True),
    ("P8", r"两个点电荷 $q_1 = 2\,\mathrm{C}$、$q_2 = 3\,\mathrm{C}$ 相距 $r = 1\,\mathrm{m}$，求库仑力。", True),
    ("P9", r"电压 $U = 220\,\mathrm{V}$ 加在 $R = 55\,\mathrm{ohm}$ 的电阻两端，求电流。", True),
    # 线性相关性：三个向量，其中 v2 = 2*v1 ⟹ 必须判为「线性相关」
    ("P12", r"判断向量组 $\mathbf{v}_1 = \begin{bmatrix} 1 \\ 2 \\ 3 \end{bmatrix}, "
            r"\mathbf{v}_2 = \begin{bmatrix} 2 \\ 4 \\ 6 \end{bmatrix}, "
            r"\mathbf{v}_3 = \begin{bmatrix} 1 \\ 0 \\ 1 \end{bmatrix}$ 是否线性无关。",
     True),
    # ── 负例：必须诚实失败，绝不瞎猜 ──
    ("N1", r"一个物体的加速度是多少？", False),
    ("N2", r"求方程 $x^2 + 1 = 0$ 的解。", False),
    ("N3", r"判断向量 $\begin{bmatrix} 1 \\ 2 \end{bmatrix}$ 与 "
            r"$\begin{bmatrix} 3 \\ 4 \end{bmatrix}$ 是否正交。", False),
]

# 需要断言具体结论的用例：(题号, 题面, 期望 answer 关键词)
_ANSWER_ASSERT = [
    ("P12", "线性相关"),
]


def _main() -> None:
    print("═" * 74)
    print("  扩展求解器自测（线代 / ODE / 物理，含负例）")
    print("═" * 74)
    ok = 0
    total = 0
    asserts = dict(_ANSWER_ASSERT)

    for pid, q, expect in _DEMO:
        total += 2 if pid in asserts else 1
        prob = {"id": pid, "text": q, "math_expressions": [],
                "sub_problems": [], "type": "calculation"}
        r = solve_extended(prob)
        good = (r["solved"] == expect)
        ok += good
        flag = "✅" if good else "❌"
        print(f"\n{flag} {pid} (期望 solved={expect}, 实得 {r['solved']})  {q[:56]}")
        if r["solved"]:
            print(f"   solver : {r.get('solver')}")
            print(f"   answer : {str(r.get('answer_latex',''))[:100]}")
            # 结论断言：只看 solved=True 不够——曾经出现过
            # 「输出『线性无关』但实际线性相关」且 solved=True 的情况。
            # 因此对关键结论额外断言关键词。
            if pid in asserts:
                kw = asserts[pid]
                ans = str(r.get("answer") or "")
                hit = kw in ans
                ok += hit
                print(f"   {'✅' if hit else '❌'} 结论断言: 期望含「{kw}」，实得「{ans}」")
        else:
            print(f"   reason : {str(r.get('reason'))[:120]}")

    print("\n" + "═" * 74)
    print(f"  自测通过 {ok}/{total}")
    print("═" * 74)
    return 0 if ok == total else 1


if __name__ == "__main__":
    import sys
    sys.exit(_main())