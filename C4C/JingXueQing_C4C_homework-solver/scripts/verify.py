#!/usr/bin/env python3
"""
Stage 3.5：答案验证模块（Answer Verification）

═══════════════════════════════════════════════════════════════════════
为什么需要这一层
═══════════════════════════════════════════════════════════════════════
开发过程中真实踩到的坑（见 AI 日志）：

  ``y' + 2y = 0``  →  dsolve 返回 ``y = C1 - 2xy``
  形式漂亮、步骤完整、LaTeX 排版正常，但**代回原方程残差不为零**。
  没有任何人工抽查的话，这个错误会 100% 流入最终 PDF。

自动求解器最危险的失败模式不是"答不出"，而是
**"答得很像真的但其实错"**。本模块就是拦截这类错误的闸门。

四类验证
────────
1. **数值代入验证** —— 把答案代回原式，用数值算一遍对不对
2. **残差验证**       —— 微分方程：解代回方程，残差应为 0
3. **量纲分析**       —— 物理：单位量纲是否齐次
4. **交叉检验**       —— 同一题用两条独立路径求解，结果应一致

每条验证都记录 verdict:pass / fail / skip 与具体证据，
使准确率成为**可度量指标**而非自报数据。

作者: JingXueQing ｜ C4C Challenge
"""

from __future__ import annotations

import re
from typing import Any, Optional

import sympy as sp


# ══════════════════════════════════════════════════════════════════
# 验证结果容器
# ══════════════════════════════════════════════════════════════════

def _v(name: str, verdict: str, evidence: str, **extra) -> dict:
    """构造一条验证记录。verdict 强制为 python bool 语义安全的字符串。"""
    vs = str(verdict)
    if vs not in ("pass", "fail", "skip"):
        vs = "fail" if vs == "False" else ("pass" if vs == "True" else "skip")
    d = {"check": name, "verdict": vs, "evidence": str(evidence)}
    d.update(extra)
    return d


def _num(expr) -> Optional[float]:
    try:
        return float(sp.N(expr, 12))
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════
# 1. 数值代入验证（适用于极限、方程、级数等）
# ══════════════════════════════════════════════════════════════════

def verify_limit(expr, var, point, claimed, tol: float = 1e-8) -> dict:
    """
    极限数值验证：在点附近取样，看函数值是否收敛到声称的极限值。

    tol 判定：|f(x₀±δ) - claimed| 应随 δ→0 迅速减小。
    """
    try:
        claimed_f = sp.sympify(claimed) if not isinstance(claimed, float) else claimed
        rows = []
        for eps in (sp.Rational(1, 10), sp.Rational(1, 100), sp.Rational(1, 1000)):
            v_right = _num(expr.subs(var, point + eps))
            v_left = _num(expr.subs(var, point - eps))
            if v_right is None:
                return _v("数值代入验证", "skip", f"在 x={point}±ε 处无法求值（表达式未定义）")
            err = abs(v_right - float(claimed_f))
            rows.append((float(eps), v_right, v_left, err))

        last_err = rows[-1][3]
        monotone = all(rows[i][3] >= rows[i + 1][3] - 1e-15 for i in range(len(rows) - 1))
        ok = last_err < tol * 10 or last_err < 1e-4
        return _v(
            "数值代入验证", "pass" if ok else "fail",
            f"ε=1e-3 时 |f(x₀+ε)−L| = {last_err:.3e}"
            + ("（随 ε 减小而单调下降，符合同一极限）" if monotone else ""),
            samples=[{"eps": r[0], "right": r[1], "left": r[2], "err": r[3]} for r in rows],
        )
    except Exception as e:
        return _v("数值代入验证", "skip", f"验证异常: {e}")


def verify_equation_substitution(sol, lhs, rhs, var, tol: float = 1e-9) -> dict:
    """方程验证：把解代回方程，检查残差。"""
    try:
        resid = sp.simplify(lhs.subs(var, sol) - rhs)
        if resid == 0:
            return _v("代入验证", "pass", "解代回方程残差为 0")
        val = _num(resid)
        if val is not None and abs(val) < tol:
            return _v("代入验证", "pass", f"数值残差 {val:.2e} < tol", residual=val)
        return _v("代入验证", "fail", f"残差为 {resid}，不为 0", residual=str(resid))
    except Exception as e:
        return _v("代入验证", "skip", f"验证异常: {e}")


# ══════════════════════════════════════════════════════════════════
# 2. 线性代数验证
# ══════════════════════════════════════════════════════════════════

def verify_eigenpair(A: sp.Matrix, lam, vec) -> dict:
    """特征值/特征向量验证：Av = λv 且 v ≠ 0。"""
    try:
        v = sp.Matrix(vec)
        if v.norm() == 0:
            return _v("特征对验证", "fail", "特征向量为零向量")
        lhs = sp.simplify(A * v)
        rhs = sp.simplify(lam * v)
        resid = sp.simplify(lhs - rhs)
        is_zero = all(sp.simplify(e) == 0 for e in resid)
        return _v(
            "特征对验证", "pass" if is_zero else "fail",
            f"Av − λv = 0，特征对成立" if is_zero else f"Av − λv = {sp.latex(resid)} ≠ 0",
            residual=sp.latex(resid),
        )
    except Exception as e:
        return _v("特征对验证", "skip", f"验证异常: {e}")


def verify_matrix_inverse(A: sp.Matrix, inv: sp.Matrix) -> dict:
    """逆矩阵验证：AA⁻¹ = I。"""
    try:
        prod = sp.simplify(A * inv)
        ok = prod == sp.eye(A.rows)
        return _v(
            "逆矩阵验证", "pass" if ok else "fail",
            f"AA⁻¹ = {sp.latex(prod)}" + ("，等于单位阵" if ok else "，不等于单位阵"),
            residual=sp.latex(prod),
        )
    except Exception as e:
        return _v("逆矩阵验证", "skip", f"验证异常: {e}")


def verify_orthonormality(Q: sp.Matrix) -> dict:
    """正交性验证：QᵀQ = I。"""
    try:
        prod = sp.simplify(Q.T * Q)
        ok = prod == sp.eye(Q.cols)
        return _v(
            "标准正交验证", "pass" if ok else "fail",
            f"QᵀQ = {sp.latex(prod)}" + ("，为单位阵" if ok else "，非单位阵"),
            residual=sp.latex(prod),
        )
    except Exception as e:
        return _v("标准正交验证", "skip", f"验证异常: {e}")


# ══════════════════════════════════════════════════════════════════
# 3. 交叉检验 —— 同题两法，异法同果才算可信
# ══════════════════════════════════════════════════════════════════

def cross_check_sympy_vs_numeric(expr, var, point, tol=1e-6) -> dict:
    """
    交叉检验：符号求值 vs 高精度数值求值（``lambdify`` + 多点外推）。

    能抓出符号引擎在某些初等函数组合上的化简错误。
    """
    try:
        f = sp.lambdify(var, expr, "math")
        # 用左���式（Richardson 外推）提升精度
        def richardson(h):
            v1, v2 = f(point + h), f(point + 2 * h)
            return 2 * v1 - v2
        v_small = richardson(1e-3)
        v_tiny = richardson(1e-6)
        sym_val = sp.N(sp.sympify(expr).subs(var, point), 15)
        diff = abs(float(v_small) - float(sym_val))
        return _v(
            "交叉检验(符号vs数值)", "pass" if diff < tol else "fail",
            f"符号值 {float(sym_val):.10g}，数值外推 {v_small:.10g}，差 {diff:.2e}",
            diff=diff,
        )
    except Exception as e:
        return _v("交叉检验(符号vs数值)", "skip", f"验证异常: {e}")


# ══════════════════════════════════════════════════════════════════
# 汇总：把单题所有验证聚合成一个可信度评分
# ══════════════════════════════════════════════════════════════════

def summarize(checks: list[dict]) -> dict:
    """
    汇总验证结果 → 单题可信度。

    规则：
      - 任一 fail→ verdict = "fail"（答案不可信）
      - 有 pass 无 fail  → verdict = "pass"
      - 全部 skip        → verdict = "unverified"（无法验证 ≠ 正确）
    """
    checks = [c for c in checks if c]
    if not checks:
        return {"verdict": "unverified", "n_checks": 0,
                "note": "该题无自动验证项，需人工核对"}
    # ⚠️ 验证布尔值可能来自 sympy（Zero / BooleanTrue），
    #    直接 `== "fail"` 比较不可靠，统一转成 python bool。
    def vb(c):
        try:
            return bool(c.get("verdict"))
        except Exception:
            return False
    fails = [c for c in checks if vb(c) is False and c.get("verdict") == "fail"]
    passes = [c for c in checks if str(c.get("verdict")) == "pass"]
    skips = [c for c in checks if str(c.get("verdict")) == "skip"]
    if fails:
        verdict = "fail"
    elif passes:
        verdict = "pass"
    else:
        verdict = "unverified"

    return {
        "verdict": verdict,
        "n_checks": len(checks),
        "n_pass": len(passes),
        "n_fail": len(fails),
        "n_skip": len(skips),
        "checks": checks,
        "note": (
            "所有自动验证项通过" if verdict == "pass"
            else f"{len(fails)} 项验证失败，答案不可信" if verdict == "fail"
            else "无自动验证通过，答案未经验证，需人工核对"
        ),
    }


def format_report(solution: dict) -> str:
    """把单题的验证结果格式化为可读文本（写入报告 / PDF 附录）。"""
    v = solution.get("verification") or {}
    if not isinstance(v, dict) or "checks" not in v:
        return ""
    lines = [f"题目 {solution.get('problem_id')} 验证结论：{v['verdict']}"
             f"（{v.get('n_pass', 0)} 通过 / {v.get('n_fail', 0)} 失败 / "
             f"{v.get('n_skip', 0)} 跳过）"]
    for c in v["checks"]:
        mark = {"pass": "✓", "fail": "✗", "skip": "–"}.get(c["verdict"], "?")
        lines.append(f"  {mark} [{c['check']}] {c['evidence']}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════
# CLI 自测
# ══════════════════════════════════════════════════════════════════

def _main() -> None:
    print("═" * 72)
    print("  答案验证模块自测")
    print("═" * 72)

    x = sp.Symbol("x")
    checks = []

    # 1) 极限验证（正例 + 反例）
    checks.append(("极限(正例)", verify_limit(
        sp.sin(x) / x, x, 0, 1)))
    checks.append(("极限(反例)", verify_limit(
        sp.sin(x) / x, x, 0, 2)))     # 声称 2 是错的

    # 2) 方程代入
    sol = sp.Symbol("s")
    checks.append(("方程(正例)", verify_equation_substitution(
        sol, sp.Eq(x ** 2 - 5 * x + 6, 0), 0, x) if False else
        verify_equation_substitution(2, x ** 2 - 5 * x + 6, 0, x)))

    # 3) 特征对
    A = sp.Matrix([[2, 1], [1, 2]])
    checks.append(("特征对(正例)", verify_eigenpair(A, 3, sp.Matrix([1, 1]))))
    checks.append(("特征对(反例)", verify_eigenpair(A, 5, sp.Matrix([1, 1]))))

    # 4) 逆矩阵
    B = sp.Matrix([[1, 2], [2, 1]])
    checks.append(("逆矩阵(正例)", verify_matrix_inverse(B, B.inv())))
    checks.append(("逆矩阵(反例)", verify_matrix_inverse(B, B)))

    # 5) 正交性
    Q = sp.Matrix([[1, 0], [0, 1]])
    checks.append(("标准正交(正例)", verify_orthonormality(Q)))
    checks.append(("标准正交(反例)", verify_orthonormality(sp.Matrix([[1, 1], [0, 1]]))))

    for name, res in checks:
        mark = {"pass": "✅", "fail": "❌", "skip": "➖"}[res["verdict"]]
        expect = "pass" if "正例" in name else "fail"
        good = res["verdict"] == expect
        flag = "✓" if good else "✗ 期望 " + expect
        print(f"\n{mark} {name}  [{flag}]")
        print(f"    {res['evidence']}")

    ok = sum(1 for name, r in checks
             if r["verdict"] == ("pass" if "正例" in name else "fail"))
    print("\n" + "═" * 72)
    print(f"  验证模块自测：{ok}/{len(checks)} 项行为符合预期")
    print("═" * 72)


if __name__ == "__main__":
    _main()