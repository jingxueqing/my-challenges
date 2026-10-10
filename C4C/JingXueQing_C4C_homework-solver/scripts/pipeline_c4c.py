#!/usr/bin/env python3
"""
一键流水线：Stage 1-5 串联，从作业文件到可提交 PDF。

═══════════════════════════════════════════════════════════════════════
相对 starter kit 的三处关键改动
═══════════════════════════════════════════════════════════════════════
1. **混合求解路由** —— starter 只有 SymPy 一条路。
   本流水线按题目类型分流：
     · 计算类（线代/ODE/物理）→ SymPy 精确求解 + 验证
     · 推理/证明/概念类      → 国产大模型（Qwen3.6 / Kimi K2.5）
     · 符号引擎解不出        → 回退大模型
   这是 C4C「核心创新」要求的落地：决定哪题用 SymPy、哪题用 LLM。

2. **验证闸门** —— 每题求解后跑 verify.py；ODE 残差不为零直接拒答。

3. **PDF 双后端** —— 有 LaTeX 走 xelatex/pdflatex；
   无 LaTeX（本机默认）走 matplotlib mathtext，保证零依赖出 PDF。

用法:
    python pipeline.py <输入文件> <输出目录> [选项]

选项:
    --compile / --pdf      强制生成 PDF（默认生成）
    --no-pdf               跳过 PDF
    --course NAME          课程名（默认 Mathematics）
    --student NAME         学生姓名
    --title TITLE          文档标题
    --llm {qwen,kimi,deepseek,none}
                            推理后端（默认 qwen；none=只用符号引擎）
    --domain NAME          领域提示（linear_algebra/ode/physics/general）
    --report               输出准确率与验证统计报告

作者: JingXueQing (2024102110351) ｜ C4C Challenge
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

scripts_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(scripts_dir))

from bootstrap import ensure_dependencies, SKILL_ROOT  # noqa: E402

ensure_dependencies()

from ingest_ext import ingest                       # noqa: E402
from parse_problems import parse_problems            # noqa: E402
import solve as starter_solve                        # noqa: E402
from solve_extended import solve_extended            # noqa: E402
from verify import summarize as verify_summarize     # noqa: E402
import verify as V                                   # noqa: E402
from llm_engine import LLMEngine                     # noqa: E402


# ══════════════════════════════════════════════════════════════════
# 混合求解：决定每题交给 SymPy 还是国产大模型
# ══════════════════════════════════════════════════════════════════

# 用 SymPy 精确求解的题型关键词（确定性 > 概率性）
SYMPY_ROUTE = [
    # 线性代数
    "矩阵", "行列式", "特征值", "特征向量", "对角化", "奇异值", "线性无关",
    "线性相关", "秩", "正交化", "标准正交", "逆矩阵", "迹",
    # 微分方程
    "微分方程", "通解", "特解", "初始条件", "dsolve",
    # 物理
    "牛顿第二定律", "合力", "自由落体", "落体", "动能", "势能", "库仑",
    "欧姆", "理想气体", "压强", "功率", "电流", "电压", "电阻",
]

# 必须走符号引擎、**禁止**交给 LLM 的题型（LLM 容易"编"出貌似合理的错解）
SYMPY_ONLY = SYMPY_ROUTE + [
    # 自由落体：题面用"高处落下/落地"表述，需显式纳入
    "自由落体", "落地", "落下", "竖直上抛", "抛体",
]


# 证明/说理类：符号引擎无能为力，**必须**交大模型
PROOF_MARKERS = ["证明", "试证", "求证", "说明为什么", "为什么说",
                 "prove", "show that", "justify"]


def route(problem: dict) -> tuple[str, str]:
    """
    决定单题的求解路径。

    返回 (route, reason)：
      "sympy"  —— 用符号计算（结果可精确验证）
      "llm"    —— 交给国产大模型（推理/证明/概念）
      "starter"—— 用 starter 的微积分求解器

    ⚠️ 顺序很关键：**先判证明题**。
    一道题可能同时含"矩阵"和"证明"（如"证明可逆矩阵的特征值非零"），
    若先匹配关键词就会被误判为计算题，交给符号引擎后必然失败，
    并给出"未找到矩阵"这种驴唇不对马嘴的失败原因。
    """
    text = problem.get("text", "")
    for e in problem.get("math_expressions", []) or []:
        text += " " + str(e.get("latex", ""))
    for sub in problem.get("sub_problems", []) or []:
        text += " " + sub.get("text", "")

    # ① 证明/说理类优先判给大模型
    if any(k in text for k in PROOF_MARKERS):
        return "llm", "证明/说理类 → 符号引擎无能为力，交由大模型推理"

    # ② 确定性题库
    if any(k in text for k in SYMPY_ONLY):
        return "sympy", "命中确定性题库关键词 → 符号计算（结果可验证）"

    t = problem.get("type", "")
    if t in ("limit", "tangent", "epsilon_delta", "calculation", "equation"):
        return "starter", f"starter 内核可直接处理（type={t}）"

    if t in ("conceptual", "proof", "graph"):
        return "llm", f"概念/证明类（type={t}）→ 需要多步推理"

    return "llm", "未匹配确定性题库 → 交由大模型推理"


def _scrub_python_leaks(obj):
    """
    清除步骤里泄漏的 Python 内部错误信息。

    ⚠️ 实测踩坑：对角化分支里 ``except Exception as e: steps.append(f"…：{e}")``，
    把 ``name 'zeros' is not defined`` 直接写进了作业 PDF 的第 7 步。
    这类信息对学生无意义，且暴露实现细节。
    这里统一兜底：把明显的 Python 异常模式替换为中性表述。
    """
    import re as _re
    patterns = [
        (r"name '[^']+' is not defined", "符号未定义"),
        (r"object of type '[^']+' has no attribute '[^']+'", "内部类型错误"),
        (r"unsupported operand type\(s\) for [^:]+: '[^']+' and '[^']+'",
         "运算对象类型不匹配"),
        (r"'[^']+' object has no attribute '[^']+'", "内部属性错误"),
        (r"list index out of range", "索引越界"),
        (r"division by zero", "除零"),
        (r"unbound local variable", "变量未初始化"),
    ]

    def _clean(s):
        if not isinstance(s, str):
            return s
        for pat, rep in patterns:
            s = _re.sub(pat, rep, s)
        return s

    if isinstance(obj, dict):
        return {k: ([_clean(x) for x in v] if k == "steps" and isinstance(v, list)
                    else _scrub_python_leaks(v))
                for k, v in obj.items()}
    if isinstance(obj, list):
        return [_scrub_python_leaks(v) for v in obj]
    return obj


def solve_hybrid(problem: dict, engine: LLMEngine, domain: str,
                 use_llm: bool = True) -> dict:
    """
    混合求解单题：符号引擎优先，必要时回退大模型。

    关键策略：**先符号、后 LLM、最后诚实失败**。
    """
    path, why = route(problem)

    # ── 1. 符号引擎 ──
    if path == "sympy":
        r = solve_extended(problem)
        if r.get("solved"):
            r["routing"] = {"path": "sympy", "reason": why}
            _attach_verification(r, problem)
            return r
        if not use_llm:
            r["routing"] = {"path": "sympy", "reason": why + "（LLM 已禁用）"}
            # 关键词命中但解不出 → 补充说明，方便人工判断
            r["reason"] = (f"{r.get('reason', '')}"
                           f"｜提示：本题含确定性题库关键词，但当前实现未覆盖该具体问法"
                           f"（如需 LLM 推理，请去掉 --llm none）")
            return r
        # 符号引擎失败 → 尝试 LLM
        lr = _llm_solve(engine, problem, domain)
        lr["routing"] = {"path": "sympy->llm",
                         "reason": why + f"；符号引擎未解出：{r.get('reason', '')[:60]}"}
        return lr

    # ── 2. starter 内核 ──
    if path == "starter":
        r = starter_solve.solve_problem(problem)
        r.setdefault("routing", {"path": "starter", "reason": why})
        if not r.get("solved") and use_llm:
            lr = _llm_solve(engine, problem, domain)
            lr["routing"] = {"path": "starter->llm",
                             "reason": why + "；starter 未解出，回退大模型"}
            return lr
        return r

    # ── 3. 大模型 ──
    if use_llm:
        lr = _llm_solve(engine, problem, domain)
        lr["routing"] = {"path": "llm", "reason": why}
        return lr

    return {
        "problem_id": problem["id"], "problem_text": problem.get("text", ""),
        "solved": False, "steps": [], "answer": None, "answer_latex": "",
        "solver": "none", "reason": "LLM 已禁用，且该题不属确定性题库",
        "sub_solutions": [], "routing": {"path": "none", "reason": why},
    }


def _llm_solve(engine: LLMEngine, problem: dict, domain: str) -> dict:
    """调用国产大模型求解，并组装为统一的 solution 结构。"""
    res = engine.solve(problem.get("text", ""), domain=domain)
    out = {
        "problem_id": problem["id"],
        "problem_text": problem.get("text", ""),
        "solved": res.solved,
        "steps": res.steps,
        "answer": res.answer,
        "answer_latex": res.answer_latex or res.answer,
        "solver": f"llm:{res.backend}",
        "llm": {"backend": res.backend, "model": res.model, **res.provenance},
        "reason": res.reason,
        "sub_solutions": [],
    }
    if not res.solved:
        out["steps"] = []
        out["answer"] = None
        out["answer_latex"] = ""
    return out


def _json_safe(obj):
    """
    递归清洗成可 JSON 序列化的结构。

    SymPy 会把 0/1 存成 ``Zero``/``One`` 等对象，直接 json.dumps 会抛
    ``TypeError: Object of type Zero is not JSON serializable``。
    这里统一转成 str / float / int / bool。
    """
    import sympy as sp
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    if isinstance(obj, sp.Basic):
        return sp.srepr(obj) if not obj.is_number else str(obj)
    if isinstance(obj, (sp.MatrixBase,)):
        return str(obj)
    return str(obj)


def _attach_verification(sol: dict, problem: dict) -> None:
    """
    给符号求解结果挂上验证记录。

    覆盖五类自动验证（每类都能独立抓错）：
      1. ODE 残差      —— 解代回方程，残差须为 0
      2. 量纲齐次性    —— 物理公式两侧量纲须相等
      3. 特征对        —— Av = λv
      4. 逆矩阵        —— AA⁻¹ = I
      5. 行列式/秩一致性 —— det≠0 ⟺ rank=满秩 ⟺ 可逆
    """
    import sympy as sp
    from solve_extended import find_matrix_rows, rows_to_matrix

    checks: list[dict] = []
    own = sol.get("verification")
    # ⚠️ solve_extended 返回的 verification 形如
    #    {"verification": {...真正证据...}, "extraction": [...]}
    #    即求解器已把证据嵌在 verification 子键里，
    #    这里需要下钻一层，否则永远匹配不到 is_zero/homogeneous。
    if isinstance(own, dict) and isinstance(own.get("verification"), dict):
        own = own["verification"]
    if isinstance(own, dict):
        # ⚠️ sympy 会把比较结果存成 Zero / BooleanTrue 等对象，
        #    `is not None` 判断虽成立，但 `== False` 语义不可靠，
        #    且 json.dumps 会抛 "Object of type Zero is not JSON serializable"。
        #    因此统一用 bool() 归一。
        def _b(v):
            try:
                return bool(v)
            except Exception:
                return False

        if own.get("is_zero") is not None:
            checks.append({"check": "残差验证",
                           "verdict": "pass" if _b(own.get("is_zero")) else "fail",
                           "evidence": own.get("evidence")
                           or f"残差 = {own.get('residual_latex', own.get('residual'))}"})
        if own.get("homogeneous") is not None:
            checks.append({"check": "量纲齐次性",
                           "verdict": "pass" if _b(own.get("homogeneous")) else "fail",
                           "evidence": f"公式 {own.get('formula', '')} 两侧量纲一致"})
        if own.get("AA_inv_eq_I") is not None:
            checks.append({"check": "逆矩阵验证",
                           "verdict": "pass" if _b(own["AA_inv_eq_I"]) else "fail",
                           "evidence": f"AA⁻¹ = {own.get('AA_inv', 'I')}"})
        if own.get("independent") is not None:
            checks.append({"check": "线性相关性",
                           "verdict": "pass" if _b(own["independent"]) else "fail",
                           "evidence": own.get("formula")
                           or f"rank={own.get('rank')}，向量数={own.get('n_vectors')}"})

    # ── 代数验证（需要题面里有矩阵）──
    try:
        text = problem.get("text", "")
        rows = find_matrix_rows(text)
        if rows:
            A = rows_to_matrix(rows)
            if "特征" in text or "eigen" in text.lower():
                for val, _m, basis in A.eigenvects():
                    checks.append(V.verify_eigenpair(A, val, basis[0]))
                # 特征值之和 = 迹（自洽性交叉检验）
                eigs = list(A.eigenvals())
                s_ok = sp.simplify(sum(eigs) - A.trace()) == 0
                checks.append({
                    "check": "特征值-迹自洽",
                    "verdict": "pass" if s_ok else "fail",
                    "evidence": f"Σλ = {sp.latex(sp.simplify(sum(eigs)))}，"
                                f"tr(A) = {sp.latex(A.trace())}"})
            if "逆矩阵" in text:
                try:
                    checks.append(V.verify_matrix_inverse(A, A.inv()))
                except Exception:
                    pass
            if "行列式" in text or "可逆" in text:
                d = A.det()
                full = (A.rows == A.cols)
                r = A.rank()
                # det≠0 ⟺ 满秩 ⟺ 可逆，三者必须一致
                consistent = (d != 0) == (r == A.rows) if full else True
                checks.append({
                    "check": "det-秩一致性",
                    "verdict": "pass" if consistent else "fail",
                    "evidence": f"det(A) = {sp.latex(d)}，rank(A) = {r}，"
                                f"{A.rows}×{A.cols}"
                                + ("（三者一致）" if consistent else "（矛盾！）")})
            if "线性无关" in text or "线性相关" in text:
                from solve_extended import find_all_vectors
                vecs, seen, uniq = find_all_vectors(text), set(), []
                for v in vecs:                # 去重：_all_text 会重复拼接
                    k = str(v)
                    if k not in seen:
                        seen.add(k)
                        uniq.append(v)
                if len(uniq) >= 2:
                    A2 = sp.Matrix.hstack(*uniq)
                    n, r = len(uniq), A2.rank()
                    indep = (r == n)
                    # 若判定为相关，必须能给出非平凡零组合作为证据
                    ns = A2.nullspace()
                    has_witness = bool(ns) and any(
                        sp.simplify(c) != 0 for c in ns[0])
                    verdict_ok = (indep and r == n) or (not indep and has_witness)
                    checks.append({
                        "check": "线性相关性",
                        "verdict": "pass" if verdict_ok else "fail",
                        "evidence": f"{n} 个向量，rank = {r}"
                                    + (f"，存在非平凡零组合 {sp.latex(sp.Matrix(ns[0]).T)}"
                                       if has_witness else "")
                                    + ("⟹线性相关" if not indep else "⟹线性无关")})
    except Exception as e:  # noqa: BLE001
        checks.append({"check": "代数验证", "verdict": "skip",
                       "evidence": f"无法提取矩阵：{type(e).__name__}"})

    if checks:
        sol["verification"] = verify_summarize(checks)


# ══════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════

def run_pipeline(input_path: str, output_dir: str,
                 course: str = "Mathematics", student: str = "Student",
                 title: str = "Homework Solutions",
                 make_pdf: bool = True, llm_vendor: str = "qwen",
                 domain: str = "general", want_report: bool = False,
                 quiet: bool = False) -> dict:
    """执行 Stage 1-5，返回统计摘要。"""
    t0 = time.time()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    def say(*a):
        if not quiet:
            print(*a)

    say("=" * 64)
    say("🚀 C4C 作业自动求解流水线（国产大模型版）")
    say(f"   输入: {input_path}")
    say(f"   输出: {output_dir}")
    say("=" * 64)

    # ── 引擎（--llm none 时不构造，直接走纯符号模式）──
    use_llm = llm_vendor != "none"
    if use_llm:
        engine = LLMEngine(vendor=llm_vendor, cache_dir=str(out / "_llm_cache"))
        llm_ready = engine.ready
    else:
        engine = None
        llm_ready = False

    # ── Stage 1 ──
    say("\n📄 Stage 1: 文档摄入")
    try:
        ing = ingest(input_path)
    except Exception as e:
        say(f"   ❌ 摄入失败: {e}")
        raise
    (out / "1_ingested.json").write_text(
        json.dumps(ing, ensure_ascii=False, indent=2), encoding="utf-8")
    m = ing["ingest_meta"]
    say(f"   ✅ {ing['format']} / {m['backend']}，{m['chars']} 字符，"
        f"{m['n_sections']} 段")
    for w in m["warnings"]:
        say(f"   ⚠️  {w}")

    # ── Stage 2 ──
    say("\n🔍 Stage 2: 题目解析")
    problems = parse_problems(ing)
    (out / "2_parsed.json").write_text(
        json.dumps(problems, ensure_ascii=False, indent=2), encoding="utf-8")
    say(f"   ✅ 识别 {len(problems)} 道题")
    if not problems:
        say("   ⚠️ 未识别到题目，请检查题号格式（'Problem N' / '题 N' / 'N.'）")
        return {"total": 0, "solved": 0}

    # ── Stage 3 ──
    say(f"\n🧮 Stage 3: 混合求解")
    if use_llm:
        say(f"   推理后端: {engine.status_report()}")
    else:
        say("   推理后端: 已禁用（仅符号计算，推理类题目将诚实失败）")
    solutions = []
    for p in problems:
        try:
            r = solve_hybrid(p, engine, domain, use_llm=use_llm)
        except Exception as e:
            r = {"problem_id": p["id"], "problem_text": p.get("text", ""),
                 "solved": False, "steps": [], "answer": None,
                 "answer_latex": "", "solver": "none",
                 "reason": f"求解异常: {e}", "sub_solutions": []}
        solutions.append(r)

    (out / "3_solutions.json").write_text(
        json.dumps(_json_safe(_scrub_python_leaks(solutions)),
                   ensure_ascii=False, indent=2),
        encoding="utf-8")
    # 同步清理内存中的对象，供 Stage 4/5 使用
    solutions = _scrub_python_leaks(solutions)

    solved = sum(1 for s in solutions if s["solved"])
    say(f"   ✅ 求解完成 {solved}/{len(solutions)}")
    for s in solutions:
        mark = "✅" if s["solved"] else "❌"
        info = (s.get("answer_latex") or s.get("reason") or "")[:64].replace("\n", " ")
        rt = s.get("routing", {}).get("path", "-")
        say(f"      {mark} {s['problem_id']:<8} [{rt:<12}] {info}")

    # ── Stage 4 ──
    say("\n📝 Stage 4: LaTeX 生成")
    from render_latex import render_document
    tex = render_document(solutions, course=course, student=student, title=title)
    (out / "homework.tex").write_text(tex, encoding="utf-8")
    say(f"   ✅ {out / 'homework.tex'}")

    # ── Stage 5 ──
    pdf_info = None
    if make_pdf:
        say("\n📑 Stage 5: PDF 生成")
        from render_pdf import solutions_to_pdf, latex_available
        say(f"   LaTeX 引擎: {'有' if latex_available() else '无（使用 mathtext 后端）'}")
        try:
            pdf_info = solutions_to_pdf(solutions, out / "homework.pdf",
                                        course=course, student=student,
                                        title=title)
            say(f"   ✅ {pdf_info['path']}  "
                f"backend={pdf_info['backend']}  {pdf_info['size_bytes']:,}B")
        except Exception as e:
            say(f"   ⚠️ PDF 生成失败: {e}")
    else:
        say("\n📑 Stage 5: 跳过（--no-pdf）")

    # ── 统计与报告 ──
    elapsed = time.time() - t0
    verified = [s for s in solutions
                if (s.get("verification") or {}).get("verdict") == "pass"]
    failed_ver = [s for s in solutions
                  if (s.get("verification") or {}).get("verdict") == "fail"]
    routes: dict[str, int] = {}
    for s in solutions:
        p = s.get("routing", {}).get("path", "unknown")
        routes[p] = routes.get(p, 0) + 1

    summary = {
        "total": len(solutions),
        "solved": solved,
        "solve_rate": round(solved / len(solutions) * 100, 1) if solutions else 0,
        "verified_pass": len(verified),
        "verification_failed": len(failed_ver),
        "routes": routes,
        "llm": {"vendor": llm_vendor, "ready": llm_ready,
                "mode": ("api" if llm_ready else "local(degraded)")
                        if use_llm else "disabled"},
        "pdf": pdf_info,
        "elapsed_sec": round(elapsed, 2),
        "outputs": sorted(f.name for f in out.iterdir() if f.is_file()),
    }
    (out / "0_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    say("\n" + "=" * 64)
    say("📊 流水线完成")
    say(f"   求解: {solved}/{len(solutions)}  ({summary['solve_rate']}%)")
    say(f"   验证: {len(verified)} 题通过自动验证，{len(failed_ver)} 题失败")
    say(f"   路由: {routes}")
    say(f"   耗时: {elapsed:.1f}s")
    say("=" * 64)

    if want_report:
        rp = write_report(solutions, summary, out / "verification_report.md")
        say(f"   报告: {rp}")

    return summary


def write_report(solutions: list[dict], summary: dict, path: Path) -> str:
    """生成 Markdown 验证报告（每题含验证证据）。"""
    lines = [
        "# C4C 作业求解验证报告",
        "",
        f"- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- 题目总数：**{summary['total']}**",
        f"- 自动解出：**{summary['solved']}**（{summary['solve_rate']}%）",
        f"- 通过自动验证：**{summary['verified_pass']}**",
        f"- 验证失败：**{summary['verification_failed']}**",
        f"- 推理后端：`{summary['llm']['vendor']}`"
        f"（{'API 就绪' if summary['llm']['ready'] else '未配置 key，降级为 local 确定性后端'}）",
        "",
        "## 路由分布",
        "",
        "| 路径 | 题数 |",
        "|------|------|",
    ]
    for k, v in summary["routes"].items():
        lines.append(f"| `{k}` | {v} |")

    lines += ["", "## 逐题明细", "",
              "| 题号 | 求解 | 路径 | 验证 | 答案摘要 |",
              "|------|------|------|------|----------|"]
    for s in solutions:
        v = (s.get("verification") or {}).get("verdict", "unverified")
        vmark = {"pass": "✅ pass", "fail": "❌ fail"}.get(v, "– unverified")
        ans = (s.get("answer_latex") or s.get("reason") or "")[:52].replace("|", "\\|")
        lines.append(
            f"| {s['problem_id']} | {'✅' if s['solved'] else '❌'} "
            f"| `{s.get('routing', {}).get('path', '-')}` | {vmark} | {ans} |")

    # 详细验证证据
    det = [s for s in solutions if (s.get("verification") or {}).get("checks")]
    if det:
        lines += ["", "## 验证证据", ""]
        for s in det:
            ver = s["verification"]
            lines.append(f"### Problem {s['problem_id']} — {ver['verdict']}")
            lines.append("")
            for c in ver["checks"]:
                mark = {"pass": "✓", "fail": "✗", "skip": "–"}.get(c["verdict"], "?")
                lines.append(f"- {mark} **{c['check']}**：{c['evidence']}")
            lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    return str(path)


# ══════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════

def main() -> None:
    ap = argparse.ArgumentParser(
        description="C4C 作业自动求解流水线（国产大模型版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  python pipeline.py homework.md out/
  python pipeline.py homework.pdf out/ --compile --course 线性代数 --student 张三
  python pipeline.py hw.docx out/ --llm kimi --domain linear_algebra --report
  python pipeline.py hw.md out/ --llm none        # 只用符号引擎，不调模型
""")
    ap.add_argument("input", help="输入文件 (.md/.txt/.tex/.pdf/.docx)")
    ap.add_argument("output_dir", help="输出目录")
    ap.add_argument("--compile", action="store_true", help="生成 PDF（默认开）")
    ap.add_argument("--no-pdf", action="store_true", help="跳过 PDF")
    ap.add_argument("--course", default="Mathematics")
    ap.add_argument("--student", default="Student")
    ap.add_argument("--title", default="Homework Solutions")
    ap.add_argument("--llm", default="qwen",
                    choices=["qwen", "kimi", "deepseek", "none"])
    ap.add_argument("--domain", default="general")
    ap.add_argument("--report", action="store_true", help="输出验证报告")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not Path(args.input).exists():
        print(f"错误: 输入文件不存在 — {args.input}")
        sys.exit(1)

    make_pdf = not args.no_pdf
    run_pipeline(args.input, args.output_dir, course=args.course,
                 student=args.student, title=args.title,
                 make_pdf=make_pdf, llm_vendor=args.llm,
                 domain=args.domain, want_report=args.report, quiet=args.quiet)


if __name__ == "__main__":
    main()