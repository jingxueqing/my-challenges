#!/usr/bin/env python3
"""
Stage 4/5 增强：LaTeX 生成 + 无 TeX 环境的 PDF 产出

═══════════════════════════════════════════════════════════════════════
解决的真实工程障碍
═══════════════════════════════════════════════════════════════════════
本机（以及大量学生机）**没有安装 LaTeX**：
    $ which pdflatex xelatex tectonic → 全部 not found
starter kit 的 ``--compile`` 因此形同虚设，只能得到 .tex 文件，
而 C4C 要求"生成可提交的 PDF"。

同时 GitHub 在本网络下不可达，无法下载 tectonic 单文件二进制，
brew 也不存在 —— 常规"装个 TeX 发行版"的路线全部封死。

本模块的解法：**双后端**
────────────────────
  backend="latex"    有 TeX 时走 pdflatex/xelatex（starter 原路径）
  backend="mathtext" 无 TeX 时用 matplotlib mathtext 直接渲染 PDF

mathtext 后端的关键工程量在于 LaTeX→mathtext 方言转换。
实测 matplotlib mathtext **不支持**：
    \\boxed  \\begin{aligned}  \\begin{cases}  \\begin{pmatrix}
    \\fbox   \\stackrel         \\tfrac          \\textcolor
因此需要 `LatexToMathtext` 逐条降级这些构造：
    aligned → 逐行渲染（真正的多行对齐）
    boxed   → 渲染后叠加矩形边框
    cases   → 渲染为多行并加左侧大括号
    pmatrix → 逐元素网格 + 括号
这比"直接报错"复杂得多，但它让**零依赖出 PDF** 成为可能。

作者: JingXueQing ｜ C4C Challenge
"""

from __future__ import annotations

import html
import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Any, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import sympy as sp

# 中文字体候选（macOS 优先）
_CJK_CANDIDATES = [
    "Songti SC", "STSong", "SimSun", "Heiti SC", "STHeiti",
    "PingFang SC", "Arial Unicode MS", "LiSong Pro", "STKaiti",
]
_LATIN_CANDIDATES = ["STIX Two Text", "DejaVu Serif", "STIXGeneral", "Times New Roman"]


def _pick_font(candidates: list[str]) -> Optional[str]:
    import matplotlib.font_manager as fm
    available = {f.name for f in fm.fontManager.ttflist}
    for c in candidates:
        if c in available:
            return c
    return None


CJK_FONT = _pick_font(_CJK_CANDIDATES)
LATIN_FONT = _pick_font(_LATIN_CANDIDATES)


def latex_available() -> bool:
    """检测本机是否有可用的 LaTeX 引擎。"""
    return any(shutil.which(x) for x in ("pdflatex", "xelatex", "lualatex", "tectonic"))


# ══════════════════════════════════════════════════════════════════
# LaTeX → mathtext 方言转换
# ══════════════════════════════════════════════════════════════════

_MT_SUPPORTED = {
    "frac": True, "dfrac": True, "sqrt": True, "binom": True,
    "mathbb": True, "mathcal": True, "boldsymbol": True, "mathbf": True,
    "mathrm": True, "mathit": True, "operatorname": True, "overline": True,
    "underline": True, "hat": True, "tilde": True, "vec": True, "bar": True,
    "dot": True, "ddot": True, "partial": True, "nabla": True, "infty": True,
    "sum": True, "prod": True, "int": True, "oint": True, "lim": True,
    "log": True, "ln": True, "exp": True, "sin": True, "cos": True, "tan": True,
    "arcsin": True, "arccos": True, "arctan": True, "sinh": True, "cosh": True,
    "alpha": True, "beta": True, "gamma": True, "delta": True, "epsilon": True,
    "theta": True, "lambda": True, "mu": True, "pi": True, "rho": True,
    "sigma": True, "tau": True, "phi": True, "omega": True, "psi": True,
    "quad": True, "qquad": True, "cdot": True, "times": True, "pm": True,
    "leq": True, "geq": True, "neq": True, "approx": True, "equiv": True,
    "in": True, "notin": True, "subset": True, "cup": True, "cap": True,
    "rightarrow": True, "leftarrow": True, "Rightarrow": True, "forall": True,
    "exists": True, "infinity": True, "prime": True, "circ": True,
}


def _extract_env(text: str, env: str):
    """
    提取 \\begin{env}...\\end{env} 内容（支持嵌套计数）。

    返回 [(start, end, body), ...]，按出现顺序。
    """
    out = []
    token = f"\\begin{{{env}}}"
    close = f"\\end{{{env}}}"
    pos = 0
    while True:
        i = text.find(token, pos)
        if i == -1:
            break
        depth, j = 1, i + len(token)
        while j < len(text) and depth:
            nxt_open = text.find(token, j)
            nxt_close = text.find(close, j)
            if nxt_close == -1:
                break
            if nxt_open != -1 and nxt_open < nxt_close:
                depth += 1
                j = nxt_open + len(token)
            else:
                depth -= 1
                j = nxt_close + len(close)
                if depth == 0:
                    out.append((i, j, text[i + len(token):j - len(close)]))
                    pos = j
                    break
        else:
            break
        if depth != 0:
            break
    return out


# LaTeX 命令别名 → mathtext 实际支持的拼写
# ⚠️ 这些差异是实测踩出来的：sympy 的 latex() 会输出 \le、\ge、\to、
#    \neq 等，而 mathtext 只认 \leq、\geq、\rightarrow、\ne。
#    不做这层映射，PDF 渲染会在最后一步抛 ParseFatalException。
_ALIASES = {
    r"\le": r"\leq", r"\leq": r"\leq",
    r"\ge": r"\geq", r"\geq": r"\geq",
    r"\to": r"\rightarrow", r"\rightarrow": r"\rightarrow",
    r"\ne": r"\neq", r"\neq": r"\neq",
    r"\gets": r"\leftarrow",
    r"\land": r"\wedge", r"\lor": r"\vee",
    r"\iff": r"\Leftrightarrow",
    r"\dots": r"\ldots", r"\cdots": r"\cdots",
    r"\degree": r"^{\circ}",
    r"\celsius": r"^{\circ}",
    r"\percent": r"\%",
    r"\lbrace": r"\{", r"\rbrace": r"\}",
    r"\vert": r"|", r"\Vert": r"\|",
    r"\dotsc": r"\ldots",
    r"\tfrac": r"\frac", r"\dfrac": r"\frac",
    r"\big": "", r"\Big": "", r"\bigg": "", r"\Bigg": "",
    r"\bigl": "", r"\Bigl": "", r"\bigr": "", r"\Bigr": "",
    r"\displaystyle": "", r"\textstyle": "",
    r"\limits": "", r"\nolimits": "",
    r"\colon": r":",
    r"\mid": r"|",
    r"\lvert": r"|", r"\rvert": r"|",
}


def apply_aliases(s: str) -> str:
    """把 LaTeX 命令别名映射到 mathtext 支持的拼写。"""
    out = s
    # 先处理带参数的 \lvert| 内层
    for src in sorted(_ALIASES, key=len, reverse=True):
        dst = _ALIASES[src]
        if src != dst:
            out = re.sub(re.escape(src) + r"(?![a-zA-Z])", lambda m, d=dst: d, out)
    return out


def strip_unsupported(text: str) -> str:
    """把 mathtext 不支持的命令降级为可渲染形式。"""
    s = text

    # ⚠️ 先剥离 $$...$$ / $...$ 定界符。
    #    mathtext 只接受我们传入时自己加的 $...$，若内容里再带 $$
    #    会直接抛 ParseException("Expected end of text, found '$'")。
    s = re.sub(r"\$\$(.*?)\$\$", r" \1 ", s, flags=re.DOTALL)
    s = s.replace("$$", " ").replace("$", " ")

    # \text{...} / \mathrm{...} → mathtext 支持 \mathrm；\text 不支持
    s = re.sub(r"\\text\s*\{([^{}]*)\}", r"\\mathrm{\1}", s)
    # \textbf/\textit/\emph → \mathbf/\mathit
    s = re.sub(r"\\textbf\s*\{([^{}]*)\}", r"\\mathbf{\1}", s)
    s = re.sub(r"\\textit\s*\{([^{}]*)\}", r"\\mathit{\1}", s)
    s = re.sub(r"\\emph\s*\{([^{}]*)\}", r"\\mathit{\1}", s)
    # \tfrac/\dfrac → \frac
    s = re.sub(r"\\[dt]frac", r"\\frac", s)
    # ⚠️ \frac12 / \frac1{2} 这类省略花括号的写法 mathtext 不认，
    #    必须补成 \frac{1}{2}（sympy 的 latex() 常输出这种简写）。
    s = re.sub(r"\\frac\s*(\d|[a-zA-Z])\s*(\d|[a-zA-Z])", r"\\frac{\1}{\2}", s)
    s = re.sub(r"\\frac\s*(\d|[a-zA-Z])\s*\{", r"\\frac{\1}{", s)
    s = re.sub(r"\\frac\s*\{([^{}]+)\}\s*(\d|[a-zA-Z])(?![a-zA-Z0-9])",
               r"\\frac{\1}{\2}", s)
    # \sqrt2 → \sqrt{2}
    s = re.sub(r"\\sqrt\s*(\d|[a-zA-Z])(?![a-zA-Z0-9])", r"\\sqrt{\1}", s)
    # \operatorname → \mathrm
    s = re.sub(r"\\operatorname\s*\{([^{}]*)\}", r"\\mathrm{\1}", s)
    # \mathbb{R} → \mathrm{R}（mathtext 黑板粗体支持有限，退化为正体）
    s = re.sub(r"\\mathbb\s*\{([^{}]*)\}", r"\\mathrm{\1}", s)
    # \cdotp, \, \! 等
    s = s.replace("\\cdotp", "\\cdot").replace("\\!", "").replace("\\,", " ")
    s = s.replace("\\;", " ").replace("\\:", " ").replace("\\!", "")
    # \displaystyle / \limits / \nolimits
    s = re.sub(r"\\(?:displaystyle|limits|nolimits|big|Big|bigg|Bigg)\b", "", s)
    # \hspace{..} \vspace{..}
    s = re.sub(r"\\(?:hspace|vspace)\s*\{[^{}]*\}", "", s)
    # \label/\ref
    s = re.sub(r"\\(?:label|ref|index)\s*\{[^{}]*\}", "", s)
    # \mathrm{ } 内的空格
    return apply_aliases(s.strip())


def split_top_level(body: str, sep: str = "\\\\") -> list[str]:
    """按顶层分隔符切分（忽略花括号/括号内部的同名符号）。"""
    rows, buf, depth, i = [], [], 0, 0
    while i < len(body):
        ch = body[i]
        if ch in "{(":
            depth += 1
        elif ch in "})":
            depth -= 1
        if depth == 0 and body[i:i + len(sep)] == sep:
            rows.append("".join(buf).strip())
            buf = []
            i += len(sep)
            continue
        buf.append(ch)
        i += 1
    rows.append("".join(buf).strip())
    return [r for r in rows if r]


# ══════════════════════════════════════════════════════════════════
# 渲染块：从 LaTeX 片段提取可渲染的行
# ══════════════════════════════════════════════════════════════════

class RenderBlock:
    """一类可渲染内容：普通行 / 对齐行组 / 矩阵 / cases / boxed"""

    def __init__(self, kind: str, **kw):
        self.kind = kind
        self.__dict__.update(kw)


def parse_latex_block(latex_str: str) -> list[RenderBlock]:
    """
    把一段 LaTeX 解析成渲染块列表。

    处理顺序很重要：先抽环境（aligned/cases/pmatrix/boxed），
    再对剩余文本做行切分。

    ⚠️ 必须保持**源码顺序**。
    形如 ``A = \\begin{bmatrix}…\\end{bmatrix}`` 的片段，"A = "
    在源码中位于矩阵**之前**。初版"先抽环境、后处理剩余文本"依次 append，
    输出会变成「矩阵 → A = → 求 A 的行列式」，语义完全错乱。
    做法：抽环境时把原位替换成等长空格（保持后续下标有效），
    记录每个块的起始位置，最后统一按位置排序。
    """
    s = latex_str.strip()
    found: list[tuple[int, "RenderBlock"]] = []   # (源码位置, 块)

    # ── boxed / fbox（注意：这是单命令 \boxed{x}，不是环境）──
    for cmd in ("boxed", "fbox"):
        while True:
            m = re.search(r"\\" + cmd + r"\s*\{", s)
            if not m:
                break
            start = m.start()
            j = m.end() - 1
            depth = 0
            while j < len(s):
                if s[j] == "{":
                    depth += 1
                elif s[j] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            if j >= len(s):
                break
            found.append((start, RenderBlock("boxed",
                                      content=strip_unsupported(s[m.end():j]))))
            s = s[:start] + " " * (j + 1 - start) + s[j + 1:]

    # ── aligned / align / align* / gathered ──
    for env in ("aligned", "align*", "align", "gathered", "split"):
        for (i, j, body) in _extract_env(s, env):
            rows = []
            for row in split_top_level(body):
                # aligned 里 & 是对齐点，mathtext 不支持，去掉保留右侧内容
                parts = [p.strip() for p in row.split("&")]
                row_tex = parts[-1] if len(parts) > 1 else parts[0]
                if row_tex:
                    rows.append(strip_unsupported(row_tex))
            if rows:
                found.append((i, RenderBlock("lines", lines=rows, env=env)))
            s = s[:i] + " " * (j - i) + s[j:]

    # ── cases ──
    for (i, j, body) in _extract_env(s, "cases"):
        rows = []
        for row in split_top_level(body):
            parts = [p.strip() for p in row.split("&")]
            cond = parts[1] if len(parts) > 1 else ""
            rows.append((strip_unsupported(parts[0]), strip_unsupported(cond)))
        if rows:
            found.append((i, RenderBlock("cases", rows=rows)))
        s = s[:i] + " " * (j - i) + s[j:]

    # ── 矩阵环境 ──
    for env in ("pmatrix", "bmatrix", "vmatrix", "matrix", "Bmatrix"):
        for (i, j, body) in _extract_env(s, env):
            rows = []
            for row in split_top_level(body):
                cells = [strip_unsupported(c) for c in row.split("&")]
                if any(cells):
                    rows.append(cells)
            if rows:
                found.append((i, RenderBlock(
                    "matrix", rows=rows,
                    delim="bracket" if env in ("pmatrix", "bmatrix") else "paren")))
            s = s[:i] + " " * (j - i) + s[j:]

    # ── 剩余普通文本：按 $$…$$ 与换行切分 ──
    rest = s.strip()
    if rest:
        for piece in re.split(r"\$\$\s*\$\$|\n", rest):
            piece = piece.strip()
            if piece:
                found.append((s.find(piece), RenderBlock(
                    "inline", content=strip_unsupported(piece))))

    # 按源码位置排序（未能定位的排最后）
    found.sort(key=lambda t: t[0] if t[0] >= 0 else 10 ** 9)
    return [b for _pos, b in found]


# ══════════════════════════════════════════════════════════════════
# mathtext 安全渲染
# ══════════════════════════════════════════════════════════════════

def mathtext_size(expr: str) -> float:
    """估算渲染宽度（单位：字符数），用于自适应缩放。"""
    return len(expr)


def render_expr(fig, x, y, expr: str, fontsize: float, color: str = "black",
                ha: str = "left") -> float:
    """
    在 figure 上渲染一个 mathtext 表达式，返回实际占用宽度（图坐标）。

    失败时抛异常，由try_render_expr 逐级降级。
    """
    # 防御：内容里不应含 $ 定界符（由本函数自己添加），
    # 否则 mathtext 会抛 ParseException("Expected end of text, found '$'")。
    expr = re.sub(r"\$\$?", " ", expr)
    txt = f"${expr}$"
    t = fig.text(x, y, txt, fontsize=fontsize, color=color, ha=ha, va="baseline")
    fig.canvas.draw()
    try:
        bbox = t.get_window_extent()
        w = bbox.width / (fig.get_size_inches()[0] * fig.dpi)
        fig._c4c_last_h = bbox.height / (fig.get_size_inches()[1] * fig.dpi)
    except Exception:
        w = len(expr) * fontsize / 200.0
        fig._c4c_last_h = fontsize / 100.0
    return w


def _char_w(ch: str, fontsize: float, fig_w: float) -> float:
    """
    单字符宽度（**图坐标**，即页宽的比例）。

    ⚠️ 两次踩坑记录：
      1. 早先用 `len(text) * fontsize / 190` 估算整段宽度，
         对中文严重低估（一个汉字 ≈ 0.95em），导致混排段不换行、
         数学片段被甩到行右侧与文字错位。
      2. 修正为按字符计宽后，单位又与 x 坐标不一致 ——
         本函数返回英寸，而 x 是页宽比例（0~1），
         结果 limit 被算成 0.836 英寸 ≈ 6 个汉字就换行。
         因此这里必须除以 fig_w 归一到图坐标。

    fig_w: 图宽度（英寸），用于单位换算。
    """
    o = ord(ch)
    if o > 0x2E80:                      # CJK / 全角
        em = 0.95
    elif ch in "iljt.,:;'|!":
        em = 0.30
    elif ch in "mwMW—…":
        em = 0.85
    elif ch.isupper():
        em = 0.68
    else:
        em = 0.52
    return fontsize / 72.0 * em / fig_w


def _text_w(s: str, fontsize: float, fig_w: float) -> float:
    """字符串宽度（图坐标）。"""
    return sum(_char_w(c, fontsize, fig_w) for c in s)


def _sanitize_plain(s: str) -> str:
    """
    清洗"作为普通文本绘制"的字符串。

    ⚠️ 关键坑：matplotlib 的 fig.text 会**自动识别** $...$ 为数学模式。
    若题面里含未配对的单个 $（例如 `$$A = x$$` 被换行拆开，
    或 `价格 $5 与 $8`），它会尝试按数学解析并抛 ParseException，
    导致整个 PDF 生成失败。

    因此所有走普通文本路径的内容都必须先去掉 $ 定界符。
    """
    return re.sub(r"\$\$?", " ", str(s))


def has_cjk(s: str) -> bool:
    """是否含中日韩字符。"""
    return any(0x2E80 <= ord(c) <= 0x9FFF or 0xFF00 <= ord(c) <= 0xFFEF
               or 0x3000 <= ord(c) <= 0x303F for c in s)


def try_render_expr(fig, x, y, expr, fontsize, color="black", ha="left") -> float:
    """
    渲染并在失败时逐级降级，**保证永不抛异常**。

    ⚠️ 关键坑：mathtext 用 STIX 数学字体，**不含中文字形**。
       若把含中文的片段当数学渲染，matplotlib 只会发 UserWarning
       然后**静默丢字**——PDF 上会出现莫名其妙的空白。
       因此含 CJK 的片段一律走普通文本 + 中文字体路径。

    降级链：含中文 → 普通文本；否则 完整 mathtext → 去未知命令 → 纯文本。
    """
    # 含中文：绝不走 mathtext
    if has_cjk(expr):
        clean = re.sub(r"\\[a-zA-Z]+", "", expr)
        clean = clean.replace("{", "").replace("}", "").replace("$", "").strip()
        try:
            t = fig.text(x, y, clean, fontsize=fontsize, color=color,
                         ha=ha, va="baseline", family=CJK_FONT or LATIN_FONT)
            fig.canvas.draw()
            bbox = t.get_window_extent()
            w = bbox.width / (fig.get_size_inches()[0] * fig.dpi)
            fig._c4c_last_h = bbox.height / (fig.get_size_inches()[1] * fig.dpi)
            return w
        except Exception:
            return len(clean) * fontsize / 190.0

    attempts = [
        expr,
        re.sub(r"\\[a-zA-Z]+", "", expr),
        re.sub(r"\\[a-zA-Z]+", "", re.sub(r"[{}$]", "", expr)),
    ]
    last = len(expr) * fontsize / 200.0
    for cand in attempts:
        try:
            return render_expr(fig, x, y, cand, fontsize, color, ha)
        except Exception:
            last = len(cand) * fontsize / 190.0
            continue
    # 最终兜底：纯 ASCII 文本
    clean = re.sub(r"\\[a-zA-Z]+", "", expr)
    clean = clean.replace("{", "").replace("}", "").replace("$", "")
    try:
        fig.text(x, y, clean, fontsize=fontsize * 0.75, color=color,
                 ha=ha, va="baseline")
    except Exception:
        pass
    fig._c4c_last_h = fontsize / 90.0
    return last


# ══════════════════════════════════════════════════════════════════
# 文档渲染器
# ══════════════════════════════════════════════════════════════════

class PDFRenderer:
    """
    分页 PDF 渲染器（matplotlib 后端）。

    采用"测量—排版—绘制"两遍走：
      1. 先用临时figure 测量每段高度，确定分页点
      2. 再正式绘制，避免内容溢出页边
    """

    def __init__(self, course: str, student: str, title: str,
                 subject: str = "", figsize=(8.27, 11.69), dpi=150):
        self.course = course
        self.student = student
        self.title = title
        self.subject = subject
        self.figsize = figsize
        self.dpi = dpi
        self.margin = 0.075
        self.body_size = 10.5
        # 版面常量（两遍法中作为起止基准）
        self._top = 1 - 0.085          # 正文起始 y
        self._bottom_limit = 0.085     # 正文下边界（页脚之上）
        self._title_reserve = 0.012    # 标题块额外留白

    # ── 低层绘制原语 ──

    def _new_fig(self):
        fig = plt.figure(figsize=self.figsize)
        fig.patch.set_facecolor("white")
        fig._c4c_last_h = 0.02
        return fig

    def _rule(self, fig, y, x0, x1, lw=0.8, color="0.35"):
        fig.add_artist(plt.Line2D([x0, x1], [y, y], lw=lw, color=color,
                                  transform=fig.transFigure))

    def _fam(self, text: str) -> str:
        """按文本内容选字体：含中文用中文字体，否则用拉丁字体。"""
        return (CJK_FONT or LATIN_FONT) if has_cjk(text) else (LATIN_FONT or "sans-serif")

    def _header(self, fig, y=None):
        if y is None:
            y = 1 - 0.045
        fig.text(self.margin, y, _sanitize_plain(self.course), fontsize=9,
                 color="0.35", ha="left", va="center", family=self._fam(self.course))
        fig.text(1 - self.margin, y, _sanitize_plain(self.student), fontsize=9,
                 color="0.35", ha="right", va="center", family=self._fam(self.student))
        self._rule(fig, y - 0.016, self.margin, 1 - self.margin, lw=0.6, color="0.75")

    def _footer(self, fig, pageno, total):
        y = 0.032
        self._rule(fig, y + 0.018, self.margin, 1 - self.margin, lw=0.6, color="0.75")
        fig.text(0.5, y, f"— {pageno} / {total} —", fontsize=8.5,
                 color="0.45", ha="center", va="center", family=LATIN_FONT)

    # ── 内容绘制 ──

    def _draw_title_block(self, fig, y):
        fig.text(0.5, y, _sanitize_plain(self.title), fontsize=17, weight="bold",
                 ha="center", va="center", family=self._fam(self.title))
        y -= 0.032
        fig.text(0.5, y, _sanitize_plain(self.course), fontsize=12.5,
                 ha="center", va="center", color="0.25", family=self._fam(self.course))
        y -= 0.028
        sub = self.student + "　|　" + date.today().strftime("%Y-%m-%d")
        fig.text(0.5, y, sub, fontsize=10.5, ha="center", va="center",
                 color="0.45", family=self._fam(sub))
        y -= 0.022
        self._rule(fig, y, 0.30, 0.70, lw=1.1, color="0.25")
        return y - 0.035

    def _draw_problem_head(self, fig, y, pid):
        fig.text(self.margin, y, f"Problem {pid}", fontsize=12, weight="bold",
                 ha="left", va="center", family=LATIN_FONT)
        self._rule(fig, y - 0.016, self.margin, 1 - self.margin, lw=0.7, color="0.55")
        return y - 0.032

    def _draw_problem_text(self, fig, y, text: str, indent=0.014) -> float:
        r"""
        绘制**题面**。

        题面常混排「中文 + $$矩阵$$」。不能整段当纯文本画：
       那样 $$…$$ 里的 LaTeX 会以源码形态糊在页面上。
        正确做法：把 $$…$$ / $…$ 段抽出来单独按数学渲染。

        分段策略：
          · 行内数学与中文 → 进缓冲区，合并成连续段落
          · 块级结构（矩阵/cases/boxed/aligned）→ 先冲缓冲，再独占若干行
          · 块级结构之后的中文 → 下压半行另起（避免挂在矩阵右侧）
        """
        text = str(text or "").strip()
        if not text:
            return y
        # 清掉 PDF 摄入留下的分页标记（"--- Page 3 ---" 之类）
        text = re.sub(r"-{2,}\s*Page\s+\d+\s*-{2,}", " ", text)
        text = re.sub(r"\n-{3,}\s*$", "", text).strip()

        parts = re.split(r"(\$\$.*?\$\$|\$[^$]+\$)", text, flags=re.DOTALL)
        has_math = any(p and p.strip().startswith("$") for p in parts)

        if not has_math:
            return self._draw_text(fig, y, _sanitize_plain(text), indent=indent)

        # ── 逐段处理，维护一个"行内混排缓冲区" ──
        # 规则：
        #   · 行内数学与中文 → 进缓冲区，合并成连续段落排版
        #   · 块级结构（矩阵/cases/boxed/aligned）→ 先冲缓冲，再独占若干行
        #   · 块级结构**之后**的中文 → 下压半行另起（避免挂在矩阵右侧）
        #   · 首段（矩阵之前）的中文直接起一行，不进缓冲
        buf: list[str] = []
        after_block = False

        def flush():
            nonlocal y, buf
            if buf:
                y = self._draw_inline_paragraph(
                    fig, y, " ".join(buf), fontsize=self.body_size,
                    indent=indent + 0.010)
                buf = []

        for idx, p in enumerate(parts):
            if not p or not p.strip():
                continue

            if p.startswith("$"):
                expr = p[2:-2] if p.startswith("$$") else p[1:-1]
                blocks = parse_latex_block(expr)
                if any(b.kind in ("matrix", "cases", "boxed", "lines")
                       for b in blocks):
                    flush()
                    y = self._draw_blocks(fig, y, blocks,
                                          fontsize=self.body_size,
                                          indent=indent + 0.016)
                    after_block = True
                else:
                    buf.append(f"${expr}$")
                continue

            # 普通文本片段
            txt = _sanitize_plain(p).strip()
            if not txt:
                continue
            if idx == 0 and not buf and not after_block:
                # 题面开头（如"设矩阵"）独占一行
                y = self._draw_text(fig, y, txt, indent=indent)
            elif after_block:
                # 矩阵之后的第一段中文：下压半行另起
                y -= self._lh(self.body_size) * 0.9
                y = self._draw_text(fig, y, txt, indent=indent + 0.010)
                after_block = False
            else:
                # 其余中文并入混排缓冲，与后续行内数学连成一句
                buf.append(txt)

        flush()
        return y

    def _draw_label(self, fig, y, label, color="#1a6b3c"):
        fig.text(self.margin + 0.012, y, _sanitize_plain(label), fontsize=10, weight="bold",
                 ha="left", va="center", color=color, family=LATIN_FONT)
        return y - 0.024

    def _wrap_text(self, text: str, width_chars: int) -> list[str]:
        """按显示宽度换行（中文字符按 2 个单位宽计）。"""
        out, line, w = [], "", 0
        for ch in text:
            cw = 2 if ord(ch) > 0x2E80 else 1
            if w + cw > width_chars and line:
                out.append(line)
                line, w = "", 0
            line += ch
            w += cw
        if line:
            out.append(line)
        return out

    def _draw_text(self, fig, y, text, fontsize=10.5, indent=0.0,
                   color="black", italic=False):
        """绘制普通段落（自动换行 + 中英文混排）。"""
        if not str(text).strip():
            return y
        text = _sanitize_plain(text)
        avail = 1 - 2 * self.margin - indent
        for ln in self._wrap_by_width(text, fontsize, avail):
            fam = self._fam(ln)
            fig.text(self.margin + indent, y, ln, fontsize=fontsize, ha="left",
                     va="baseline", color=color, family=fam,
                     style="italic" if italic else "normal")
            y -= self._lh(fontsize)
        return y

    def _wrap_by_width(self, text: str, fontsize: float,
                       avail: float) -> list[str]:
        """按真实字宽换行（中文按 0.95em，拉丁按字符类别）。"""
        lines, cur, w = [], "", 0.0
        for ch in text:
            if ch == "\n":
                lines.append(cur)
                cur, w = "", 0.0
                continue
            cw = _char_w(ch, fontsize, self.figsize[0])
            if cur and w + cw > avail:
                lines.append(cur)
                cur, w = "", 0.0
            cur += ch
            w += cw
        if cur:
            lines.append(cur)
        return lines or [""]

    def _draw_blocks(self, fig, y, blocks, fontsize=None, color="black",
                     indent=0.0):
        """绘制解析出的 LaTeX 渲染块。"""
        fs = fontsize or self.body_size
        x0 = self.margin + indent
        for blk in blocks:
            if blk.kind == "inline":
                y = self._draw_inline_latex(fig, y, blk.content, fs, color, x0)
            elif blk.kind == "lines":
                for ln in blk.lines:
                    y = self._draw_inline_latex(fig, y, ln, fs, color, x0 + 0.018)
                    y -= 0.004
                y -= 0.006
            elif blk.kind == "boxed":
                y -= 0.006
                w = try_render_expr(fig, x0 + 0.02, y, blk.content, fs + 0.5, "#0b3d91")
                # 叠加边框
                fig.patches.append(Rectangle(
                    (x0 + 0.014, y - 0.011), w + 0.012, 0.026,
                    transform=fig.transFigure, fill=False,
                    edgecolor="#0b3d91", linewidth=0.9, zorder=5))
                y -= 0.026
            elif blk.kind == "cases":
                y = self._draw_cases(fig, y, blk.rows, fs, color, x0)
            elif blk.kind == "matrix":
                y = self._draw_matrix(fig, y, blk.rows, fs, color, x0,
                                      paren=blk.delim == "paren")
        return y

    def _draw_inline_latex(self, fig, y, expr, fs, color, x0) -> float:
        """渲染单行数学；过长时自动缩放字号（1.0 → 0.9 → 0.8 → 0.7）。"""
        e = strip_unsupported(expr)
        if not e:
            return y - self._lh(fs) * 0.4
        for scale in (1.0, 0.9, 0.8, 0.7):
            w = try_render_expr(fig, x0 + 0.012, y, e, fs * scale, color)
            if w < (1 - self.margin - x0 - 0.05):
                return y - self._lh(fs * scale) * 1.28
        return y - self._lh(fs * 0.7) * 1.28

    # ── 分隔符绘制（用线段而非字体大括号，避免对不齐）──

    def _bracket(self, fig, x, y_top, y_bot, color="black", lw=1.1,
                 shape="[", flip=False):
        """
        画括号骨架（方括号 / 圆括号 / 大括号）。

        flip=True 时左右镜像，用于右括号。

        实现说明：全部用水平/竖直线段拼装，**不用字体大符号**——
        字体里的括号是按字号等比的，矩阵有多行时永远对不齐，
        而拼线可以精确匹配矩阵的上下边界。
        """
        x0, x1 = x, x + 0.011          # 括号水平跨度
        ymid = (y_top + y_bot) / 2
        h = abs(y_top - y_bot)
        kw = dict(transform=fig.transFigure, color=color, linewidth=lw,
                  solid_capstyle="butt", solid_joinstyle="miter", zorder=6)

        def L(xa, ya, xb, yb):
            fig.add_artist(plt.Line2D([xa, xb], [ya, yb], **kw))

        if shape in "({|":
            # ── 圆角：两端短竖 + 中间向内凹的弧（用两段折线近似）──
            span = h * 0.42
            # 上半：从中点向右上弯曲
            L(x0, y_top, x0, y_top - span * 0.55)
            L(x0, y_top - span * 0.55, x0 + (x1 - x0) * 0.62, ymid + span * 0.16)
            L(x0 + (x1 - x0) * 0.62, ymid + span * 0.16, x1 * 0.5 + x0 * 0.5, ymid)
            # 下半：镜像
            L(x0 + (x1 - x0) * 0.62, ymid - span * 0.16, x0, y_bot + span * 0.55)
            L(x0, y_bot + span * 0.55, x0, y_bot)
            if shape == "|":
                L(x0, y_top, x0, y_bot)
            if shape == "{":       # 大括号中段的尖角
                L(x1 * 0.5 + x0 * 0.5, ymid, x0 + (x1 - x0) * 0.62, ymid + span * 0.16)
                L(x1 * 0.5 + x0 * 0.5, ymid, x0 + (x1 - x0) * 0.62, ymid - span * 0.16)
            return

        # ── 方括号：两短横 + 一竖干 ──
        tick = min(0.012, h * 0.30)
        xv = x1 if flip else x0
        s = -1 if flip else 1
        L(xv, y_top, xv + s * tick, y_top)
        L(xv, y_bot, xv + s * tick, y_bot)
        L(xv, y_top, xv, y_bot)

    def _draw_cases(self, fig, y, rows, fs, color, x0) -> float:
        """cases：左侧大括号 + 条件列（带精确垂直居中）。"""
        y -= 0.006
        top = y
        for expr, cond in rows:
            y = self._draw_inline_latex(fig, y, expr, fs, color, x0 + 0.062)
            if cond:
                try_render_expr(fig, x0 + 0.42, y + 0.0095, cond, fs * 0.9, color)
            y -= 0.004
        bot = y + 0.008
        self._bracket(fig, x0 + 0.026, top + 0.004, bot, color=color, shape="{")
        return y - 0.014

    def _draw_matrix(self, fig, y, rows, fs, color, x0, paren=False) -> float:
        """矩阵：逐元素网格 + 线段括号。"""
        nr, nc = len(rows), max(len(r) for r in rows)
        cw = 0.082 if nc <= 3 else (0.060 if nc <= 5 else 0.048)
        rh = fs / 72.0 / self.figsize[1] * 2.05
        top = y
        for r in rows:
            for c, cell in enumerate(r):
                if cell:
                    try_render_expr(fig, x0 + 0.055 + c * cw, y, cell, fs * 0.92, color)
            y -= rh
        bot = y + rh * 0.42
        shape = "(" if paren else "["
        close = ")" if paren else "]"
        self._bracket(fig, x0 + 0.042, top + 0.012, bot, color=color, shape=shape)
        self._bracket(fig, x0 + 0.055 + (nc - 1) * cw + 0.028, top + 0.012, bot,
                      color=color, shape=close, flip=True)
        return y - 0.012

    # ── 主入口 ──

    def render(self, solutions: list[dict], out_pdf: str | Path,
               include_unsolved: bool = True) -> dict:
        """
        渲染 PDF —— 两遍法（measure → place）。

        第一遍：把内容画到一个临时 figure 上，**实测**每一段消耗的高度；
        第二遍：按实测高度做贪心分页并正式绘制。

        为什么不用"估算高度"：初版用固定常数估算每类内容的高度
        （steps 按 0.020/行、answer 按 0.042），结果出现
        「答案压到下一题标题上」「空步骤占一行」等错版。
        公式高度依赖实际字号与内容，必须实测。
        """
        out_pdf = Path(out_pdf)
        items = [s for s in solutions if s.get("solved") or include_unsolved]

        # ── Pass 1: 实测高度 ──
        #按"题目组"为单位测量：整道题（题号+题面+解答）作为一个不可拆单位，
        # 避免出现「题号在上一页、解答在下一页」的断裂。
        probe = self._new_fig()
        groups: list[list[RenderBlock]] = [list(self._title_group())]
        for sol in items:
            groups.append(list(self._layout_one(sol)))
        heights = [[self._measure_block(probe, b) for b in g] for g in groups]
        plt.close(probe)

        # ── Pass 2: 分页（贪心，整组不拆）──
        pages: list[list[tuple]] = [[]]
        y = self._top
        first_page = True
        for gi, (grp, hs) in enumerate(zip(groups, heights)):
            gh = sum(hs)
            reserve = self._title_reserve if (first_page and gi == 0) else 0.0
            # 整组放不下 → 换页（但首页无论如何都放标题）
            if not first_page and y - gh < self._bottom_limit:
                pages.append([])
                y = self._top
            elif first_page and y - gh < self._bottom_limit and gi > 0:
                # 首页放不下整题也开新页，标题留在首页
                pages.append([])
                y = self._top
            yy = y
            for blk, h in zip(grp, hs):
                pages[-1].append((yy, blk))
                yy -= h
            y = yy
            first_page = False

        # ── Pass 3: 正式绘制 ──
        total = len(pages)
        figs = []
        for idx, page in enumerate(pages, start=1):
            fig = self._new_fig()
            self._header(fig)
            for yy, blk in page:
                self._draw_block(fig, yy, blk)
            self._footer(fig, idx, total)
            figs.append(fig)

        out_pdf.parent.mkdir(parents=True, exist_ok=True)
        from matplotlib.backends.backend_pdf import PdfPages
        with PdfPages(out_pdf) as pdf:
            for fig in figs:
                pdf.savefig(fig, facecolor="white")
                plt.close(fig)

        return {"pages": total, "path": str(out_pdf),
                "size_bytes": out_pdf.stat().st_size}

    # ── 内容分块：把 solution 拆成可测量、可绘制的块 ──

    def _title_group(self) -> list["RenderBlock"]:
        """首页标题块组（单独成组，永远留在首页）。"""
        return [RenderBlock("title"), RenderBlock("gap", h=0.030)]

    def _layout_one(self, sol: dict) -> list["RenderBlock"]:
        """把**一道题**展开为内容块序列（整组不拆页）。"""
        blocks: list[RenderBlock] = []
        blocks.append(RenderBlock("phead", pid=sol["problem_id"]))
        blocks.append(RenderBlock("text", text=sol.get("problem_text", ""),
                                  indent=0.014, color="black"))
        if not sol.get("solved"):
            blocks.append(RenderBlock("warn",
                                      text=str(sol.get("reason", "未解出"))[:90]))
            for sub in sol.get("sub_solutions", []) or []:
                blocks.extend(self._layout_solution(
                    sub, label=f"Solution ({sub.get('problem_id')})."))
            blocks.append(RenderBlock("gap", h=0.014))
            return blocks

        blocks.extend(self._layout_solution(sol, label="Solution."))
        blocks.append(RenderBlock("gap", h=0.018))
        return blocks

    def _layout_solution(self, sol: dict, label: str) -> list["RenderBlock"]:
        out = [RenderBlock("solabel", text=label, color="#1a6b3c")]
        # ⚠️ 在此过滤空步骤，而非绘制时过滤。
        #    否则序号已按原始列表分配（1,2,3,5），空步骤留白导致跳号。
        steps = [s for s in (sol.get("steps") or []) if str(s).strip()]
        if steps:
            out.append(RenderBlock("steps", items=steps))
        ans = sol.get("answer_latex") or sol.get("answer")
        if ans:
            out.append(RenderBlock("answer", text=str(ans)))
        v = sol.get("verification") or {}
        if isinstance(v, dict) and v.get("checks"):
            out.append(RenderBlock("verify", data=v))
        return out

    # ── Pass 1 支撑：在探针 figure 上实测块高度 ──

    def _measure_block(self, fig, blk) -> float:
        """把块画到探针 figure 上，返回它消耗的 y 高度（正数）。"""
        y = 0.9
        y2 = self._draw_block(fig, y, blk)
        return max(0.0, y - y2)

    # ── Pass 3 支撑：真正绘制一个块 ──

    def _draw_block(self, fig, y, blk) -> float:
        """
        绘制单个内容块，返回新的 y。

        ⚠️ 单块失败绝不能中断整篇文档：
        捕获异常后在该位置输出占位提示，保证其余题目正常排版。
        """
        k = blk.kind
        try:
            return self._dispatch(fig, y, blk, k)
        except Exception as e:  # noqa: BLE001
            try:
                fig.text(self.margin + 0.014, y,
                         f"[此段落排版失败：{type(e).__name__}]",
                         fontsize=8.5, color="#a03030", ha="left", va="baseline",
                         family=LATIN_FONT)
            except Exception:
                pass
            return y - self._lh(9.5)

    def _dispatch(self, fig, y, blk, k: str) -> float:
        if k == "title":
            return self._draw_title_block(fig, y)
        if k == "phead":
            return self._draw_problem_head(fig, y, blk.pid)
        if k == "text":
            return self._draw_problem_text(fig, y, blk.text, indent=blk.indent)
        if k == "solabel":
            return self._draw_label(fig, y, blk.text, color=blk.color)
        if k == "warn":
            fig.text(self.margin + 0.014, y, "⚠ 本题未自动解出：" + _sanitize_plain(blk.text),
                     fontsize=9.5, color="#a03030", ha="left", va="baseline",
                     family=self._fam(blk.text))
            return y - self._lh(9.5) * 1.25
        if k == "steps":
            for i, s in enumerate(blk.items, start=1):
                y = self._draw_step(fig, y, i, s)
            return y - 0.005
        if k == "answer":
            return self._draw_answer(fig, y, blk.text)
        if k == "verify":
            return self._draw_verify(fig, y, blk.data)
        if k == "gap":
            return y - blk.h
        return y

    def _lh(self, fontsize: float) -> float:
        """给定字号对应的行高（图坐标）。"""
        return fontsize / 72.0 / self.figsize[1] * 1.42

    def _draw_step(self, fig, y, idx: int, text: str) -> float:
        """
        绘制一步。区分三种情形：

        1. 纯文字              → 直接排版
        2. 文字 + 简单行内公式 → 文字与公式**同行**排版（最常见）
        3. 含块级结构          → 文字一行，公式块另起（矩阵/cases/boxed）

        ⚠️ 初版把行内公式也拆到独立行，导致一句完整的话被撕成
        "构造特征矩阵。" / "A − λI" 两行，视觉上像两个步骤。
        """
        text = str(text).strip()
        if not text:
            return y
        m = re.findall(r"\$([^$]+)\$", text)
        plain = re.sub(r"\$[^$]+\$", "", text).strip()
        plain = re.sub(r"^\*\*|\*\*$", "", plain).strip()

        if not m:
            return self._draw_text(fig, y, f"{idx}. {plain}",
                                   indent=0.014) - 0.003

        # 判断是否含块级结构
        blocky = False
        for e in m:
            if any(b.kind in ("matrix", "cases", "boxed", "lines")
                   for b in parse_latex_block(e)):
                blocky = True
                break

        if blocky:
            # 即使本步没有文字（如纯矩阵），也必须画出序号，
            # 否则序号会出现 1,2,3,5 这种跳号。
            head = f"{idx}. {plain}" if plain else f"{idx}."
            y = self._draw_text(fig, y, head, indent=0.014) - 0.003
            for expr in m:
                y = self._draw_blocks(fig, y, parse_latex_block(expr),
                                      fontsize=10.0, indent=0.030)
            return y

        # ── 行内：文字与公式同行，用空格衔接 ──
        merged = f"{idx}. {plain} " if plain else f"{idx}. "
        merged += " ".join(f"${e}$" for e in m)
        return self._draw_inline_paragraph(fig, y, merged, fontsize=10.0,
                                          indent=0.014)

    def _draw_inline_paragraph(self, fig, y, text: str, fontsize=10.0,
                               indent=0.0, color="black") -> float:
        """
        排版"文字 + 行内公式"混排的段落。

        把字符串切成 (文字 | 公式) 片段，逐片在**同一基线**上绘制，
        用实测宽度推进 x 坐标 —— 这样公式不会另起一行，
        且整段仍会自动换行。
        """
        parts = re.split(r"(\$[^$]+\$)", text)
        x = self.margin + indent
        avail = 1 - self.margin - x
        line_h = self._lh(fontsize)
        gap = fontsize / 72.0 * 0.30 / self.figsize[0]   # 片段间空格宽（图坐标）

        for part in parts:
            if not part:
                continue
            if part.startswith("$") and part.endswith("$") and len(part) > 2:
                expr = part[1:-1]
                placed = False
                for sc in (1.0, 0.92, 0.84):
                    w = try_render_expr(fig, x, y, strip_unsupported(expr),
                                        fontsize * sc, color)
                    if x + w < 1 - self.margin:
                        x += w + gap
                        placed = True
                        break
                    # 放不下：若行首已有内容则换行后重试
                    if x > self.margin + indent + 0.004:
                        y -= line_h
                        x = self.margin + indent
                        w = try_render_expr(fig, x, y, strip_unsupported(expr),
                                            fontsize * sc, color)
                        x += w + gap
                        placed = True
                        break
                if not placed:
                    # 极端长公式：缩到最小并强制放置
                    y -= line_h
                    x = self.margin + indent
                    try_render_expr(fig, x, y, strip_unsupported(expr),
                                    fontsize * 0.75, color)
                continue
            else:
                fam = self._fam(part)
                # 按真实字宽切分（CJK 计0.95em，拉丁约 0.52em）
                cur, cur_w = "", 0.0
                limit = 1 - self.margin - x
                for ch in part:
                    w = _char_w(ch, fontsize, self.figsize[0])
                    if cur and cur_w + w > limit:
                        fig.text(x, y, cur, fontsize=fontsize, ha="left",
                                 va="baseline", color=color, family=fam)
                        y -= line_h
                        x = self.margin + indent
                        limit = 1 - self.margin - x
                        cur, cur_w = "", 0.0
                    cur += ch
                    cur_w += w
                if cur:
                    fig.text(x, y, cur, fontsize=fontsize, ha="left",
                             va="baseline", color=color, family=fam)
                    x += cur_w
        return y - line_h

    def _draw_answer(self, fig, y, ans: str) -> float:
        """
        绘制答案行。

        布局：标签与公式同基线；若公式是块级结构（矩阵/cases/boxed），
        则标签独占一行、公式另起一行缩进，避免标签与公式错位。
        """
        x0 = self.margin + 0.014
        blocks = parse_latex_block(ans)
        blocky = any(b.kind in ("matrix", "cases", "boxed", "lines") for b in blocks)

        if blocky:
            fig.text(x0, y, "Answer:", fontsize=10, weight="bold",
                     ha="left", va="baseline", color="#0b3d91", family=LATIN_FONT)
            y -= self._lh(10) * 1.15
            return self._draw_blocks(fig, y, blocks, fontsize=10.5,
                                      color="#0b3d91", indent=0.026) - 0.004

        fig.text(x0, y, "Answer:", fontsize=10, weight="bold",
                 ha="left", va="baseline", color="#0b3d91", family=LATIN_FONT)
        w = try_render_expr(fig, x0 + 0.058, y, strip_unsupported(ans), 10.5, "#0b3d91")
        # 极长答案换行
        if w > (1 - self.margin - x0 - 0.06):
            y -= self._lh(10.5) * 1.2
            return self._draw_blocks(fig, y, blocks, fontsize=10.5,
                                      color="#0b3d91", indent=0.026) - 0.004
        return y - self._lh(10.5) * 1.75

    def _draw_verify(self, fig, y, v: dict) -> float:
        verdict = v.get("verdict")
        color = {"pass": "#1a6b3c", "fail": "#a03030",
                 "unverified": "#8a6d1f"}.get(verdict, "#444")
        mark = {"pass": "✓", "fail": "✗", "unverified": "?"}.get(verdict, "?")
        n = f"{v.get('n_pass', 0)}/{v.get('n_checks', 0)}"
        txt = f"{mark} 验证 {n} 项通过：{v.get('note', '')}"
        fig.text(self.margin + 0.014, y, _sanitize_plain(txt[:96]),
                 fontsize=8.8, color=color, ha="left", va="baseline",
                 family=self._fam(txt))
        return y - self._lh(8.8) * 1.35


# ══════════════════════════════════════════════════════════════════
# LaTeX 后端（保留 starter 路径，有 TeX 时使用）
# ══════════════════════════════════════════════════════════════════

def compile_with_latex(tex_path: str | Path, out_dir: str | Path,
                       engine: Optional[str] = None) -> Optional[Path]:
    """用 pdflatex/xelatex 编译（3 遍）。无 TeX 返回 None。"""
    tex_path = Path(tex_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cands = [engine] if engine else ["xelatex", "pdflatex", "lualatex", "tectonic"]
    exe = next((shutil.which(c) for c in cands if c and shutil.which(c)), None)
    if not exe:
        return None
    for _ in range(3):
        subprocess.run([exe, "-interaction=nonstopmode", "-halt-on-error",
                        "-output-directory", str(out_dir), str(tex_path)],
                       capture_output=True, text=True)
    pdf = out_dir / (tex_path.stem + ".pdf")
    return pdf if pdf.exists() else None


# ══════════════════════════════════════════════════════════════════
# 统一入口
# ══════════════════════════════════════════════════════════════════

def solutions_to_pdf(solutions: list[dict], out_pdf: str | Path,
                     course: str = "Mathematics", student: str = "Student",
                     title: str = "Homework Solutions",
                     prefer: str = "auto") -> dict:
    """
    生成 PDF。prefer: auto / latex / mathtext

    auto：优先用真实 LaTeX（排版质量更好），失败则回退 mathtext。
    """
    out_pdf = Path(out_pdf)
    use_latex = latex_available() if prefer == "auto" else (prefer == "latex")

    if use_latex:
        # 生成 .tex 再编译
        from render_latex import render_document
        tex = out_pdf.with_suffix(".tex")
        tex.write_text(render_document(solutions, course=course,
                                       student=student, title=title),
                       encoding="utf-8")
        got = compile_with_latex(tex, out_pdf.parent)
        if got and got.stat().st_size > 1000:
            return {"backend": "latex", "path": str(got),
                    "pages": None, "size_bytes": got.stat().st_size}

    r = PDFRenderer(course=course, student=student, title=title)
    res = r.render(solutions, out_pdf)
    res["backend"] = "mathtext"
    return res


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("用法: python render_pdf.py <solutions.json> [output.pdf]")
        sys.exit(1)
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sols = data if isinstance(data, list) else data.get("solutions", [])
    out = sys.argv[2] if len(sys.argv) > 2 else "homework.pdf"
    info = solutions_to_pdf(sols, out)
    print(json.dumps(info, ensure_ascii=False, indent=2))