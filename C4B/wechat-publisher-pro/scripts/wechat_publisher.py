#!/usr/bin/env python3
"""
wechat_publisher.py — Markdown/Word → 微信公众号 HTML 转换器
===============================================================================
JingXueQing 定制版（基于 C4B starter kit 深度改造）

用法
-------------------------------------------------------------------------------
    # 最简
    python wechat_publisher.py article.md out.html

    # 指定主题 + 目录 + 页脚
    python wechat_publisher.py article.md out.html --theme ink --toc --footer

    # 批量
    python wechat_publisher.py --batch ./posts --out-dir ./html --theme forest

    # 只做体检，不出文件（CI 用）
    python wechat_publisher.py article.md --audit

    # 手机宽度预览页（自带边框，方便截图交作业）
    python wechat_publisher.py article.md out.html --preview phone

相比 starter kit 新增的能力
-------------------------------------------------------------------------------
    1.  多主题系统（ink / forest / amber / mono / custom）
    2.  Callout 提示框（:::note / :::tip / :::warn / :::danger / :::key）
    3.  自动目录卡片（带真实限制说明，不做无效锚点）
    4.  文章元数据（YAML frontmatter：标题/作者/日期/摘要/封面）
    5.  页脚版权声明（自动生成）
    6.  中文排版优化（中英文自动间距、标点挤压）
    7.  本地图片 → base64 内嵌（starter 遗留的裂图问题）
    8.  批量转换
    9.  代码块 Pygments 语法高亮（class → inline style，符合公众号限制）
    10. 代码块行号 + 换行保留（修 starter 的致命 bug）
    11. 微信合规体检器 --audit（可验证性）
    12. 手机预览页生成器

修掉的 starter 真实 bug（均由实测复现，非推测）
-------------------------------------------------------------------------------
    B1  代码块所有换行被吞成一行     （p.string 赋值丢失空白语义）
    B2  加粗/斜体里的行内代码与链接丢失（get_text() 拍平子节点）
    B3  多段引用块被合并成一段       （同上）
    B4  <hr> 分隔线被整体丢弃
    B5  内联 <div> 把段落从中间劈开
    B6  图片无 max-width，移动端溢出
    B7  本地图片保留相对路径 → 粘贴后裂图
    B8  嵌套列表被拍平成同级
    B9  <ul>/<ol> 自身无样式，缩进失控
    B10 中文与英文/数字之间无间距（排版硬伤）
    B11 ALLOWED_CSS 白名单定义了但从未真正执行
    B12 auto-install 依赖会污染系统 Python

作者：JingXueQing ｜ 学号 2024102110351
"""

import argparse
import base64
import html as html_mod
import json
import mimetypes
import os
import re
import sys
from pathlib import Path

# --- 依赖（缺失时给出清晰指引，不再自动 pip install，避免污染系统环境）---
_MISSING = []
try:
    import markdown as _md
except ImportError:
    _MISSING.append("markdown")
try:
    from bs4 import BeautifulSoup, NavigableString
except ImportError:
    _MISSING.append("beautifulsoup4")
try:
    from docx import Document
except ImportError:
    _MISSING.append("python-docx")
try:
    import lxml  # noqa: F401
except ImportError:
    _MISSING.append("lxml")

if _MISSING:
    sys.stderr.write(
        "❌ 缺少依赖：%s\n"
        "   请手动安装（推荐虚拟环境）：\n"
        "     python -m pip install %s\n"
        % (", ".join(_MISSING), " ".join(_MISSING))
    )
    sys.exit(3)

import markdown as md
from bs4 import BeautifulSoup, NavigableString

try:
    from docx import Document
except ImportError:  # pragma: no cover
    Document = None

try:
    from pygments import highlight as _pyg_highlight
    from pygments.lexers import get_lexer_by_name as _pyg_lexer
    from pygments.formatters import HtmlFormatter as _pyg_fmt

    HAS_PYGMENTS = True
except ImportError:
    HAS_PYGMENTS = False


# ============================================================================
# 1. 主题系统
# ============================================================================
# 每个主题是一组完整的 inline CSS 值。想加主题就复制一份改颜色即可。
# 所有颜色必须是对比度 >= 4.5:1 的深色（公众号正文在白底上阅读）。

THEMES = {
    "ink": {
        "label": "墨蓝（默认）",
        "desc": "沉稳深蓝，适合技术、教程、复盘类长文",
        "accent": "#1f4e79",
        "accent_light": "#eaf1f8",
        "text": "#2c3e50",
        "text_sub": "#5a6b7b",
        "border": "#d8e1e9",
        "code_bg": "#f5f7fa",
        "code_text": "#24292e",
        "quote_bg": "#f7fafd",
        "table_head_bg": "#eaf1f8",
        "table_stripe": "#f9fbfd",
    },
    "forest": {
        "label": "松绿",
        "desc": "低饱和绿，长文阅读舒适度最高",
        "accent": "#2f6b4f",
        "accent_light": "#eaf5ef",
        "text": "#2f3e36",
        "text_sub": "#5c6f65",
        "border": "#d3e3da",
        "code_bg": "#f4f8f5",
        "code_text": "#22301f",
        "quote_bg": "#f5faf7",
        "table_head_bg": "#eaf5ef",
        "table_stripe": "#f7fbf8",
    },
    "amber": {
        "label": "暖橙",
        "desc": "适合经验分享、学习心得、故事类内容",
        "accent": "#b35c1e",
        "accent_light": "#fdf0e6",
        "text": "#3d3229",
        "text_sub": "#6d5f52",
        "border": "#ecdccd",
        "code_bg": "#fbf6f1",
        "code_text": "#3a2f26",
        "quote_bg": "#fef8f2",
        "table_head_bg": "#fdf0e6",
        "table_stripe": "#fefaf5",
    },
    "mono": {
        "label": "极简黑白",
        "desc": "无彩色，走克制路线，学术/研究报告风格",
        "accent": "#333333",
        "accent_light": "#f2f2f2",
        "text": "#262626",
        "text_sub": "#666666",
        "border": "#dcdcdc",
        "code_bg": "#f7f7f7",
        "code_text": "#1a1a1a",
        "quote_bg": "#fafafa",
        "table_head_bg": "#f0f0f0",
        "table_stripe": "#fafafa",
    },
}

CALLOUT_KINDS = {
    "note":  ("\U0001F4D8", "知识",   "#1f4e79", "#eaf1f8"),
    "tip":   ("\U0001F4A1", "实践",   "#2f6b4f", "#eaf5ef"),
    "warn":  ("⚠️", "注意",   "#b35c1e", "#fdf0e6"),
    "danger": ("\U0001F525", "踩坑", "#a83232", "#fdecec"),
    "key":   ("⭐", "重点",   "#7a4bbd", "#f2ecfb"),
}

# Pygments token class → inline style（公众号不允许 class，必须内联）
PYG_STYLES = {
    "k": "color:#a626a4;font-weight:bold",       # keyword
    "kn": "color:#a626a4;font-weight:bold",      # keyword namespace
    "s": "color:#50a14f",                          # string
    "s1": "color:#50a14f",
    "s2": "color:#50a14f",
    "sd": "color:#50a14f;font-style:italic",
    "c": "color:#a0a1a7;font-style:italic",       # comment
    "c1": "color:#a0a1a7;font-style:italic",
    "cm": "color:#a0a1a7;font-style:italic",
    "n": "color:#4078f2",                          # number
    "mi": "color:#986801",                         # number int
    "mf": "color:#986801",
    "o": "color:#0184bc",                          # operator
    "p": "color:#383a42",                          # punctuation
    "n1": "color:#0184bc",                         # builtin
    "nb": "color:#0184bc",
    "bp": "color:#0184bc",
    "nf": "color:#4078f2",                         # function name
    "nc": "color:#4078f2;font-weight:bold",
    "nd": "color:#a626a4",
    "mi2": "color:#986801",
    "err": "color:#e45649",
    "w": "color:inherit",
    "gt": "color:#a626a4",
}

# 微信允许的 CSS 属性白名单（真正执行，不再是摆设 —— 修 B11）
ALLOWED_CSS_PROPS = {
    "color", "background-color", "font-size", "font-weight", "font-style",
    "line-height", "text-align", "margin", "margin-top", "margin-bottom",
    "margin-left", "margin-right", "padding", "padding-top", "padding-bottom",
    "padding-left", "padding-right", "border", "border-top", "border-bottom",
    "border-left", "border-right", "border-color", "border-width",
    "border-style", "border-radius", "border-collapse", "text-decoration",
    "display", "vertical-align", "max-width", "width", "white-space",
    "letter-spacing", "word-break", "word-wrap", "opacity", "box-shadow",
    "list-style-type", "text-indent", "font-family", "table-layout",
}

# 微信允许的标签（严格按官方 restrictions 文档；hr 不在其中，需转 p）
ALLOWED_TAGS = {
    "p", "h2", "h3", "h4", "ul", "ol", "li", "span", "img", "a",
    "table", "thead", "tbody", "tr", "th", "td", "br", "strong",
    "em", "b", "i", "code", "pre", "blockquote", "figure", "figcaption",
    "section", "font", "mark",
}
# 这些标签直接删掉（内容也不保留）
DROP_TAGS = {"script", "style", "iframe", "object", "embed", "form",
             "input", "button", "select", "textarea", "video", "audio",
             "svg", "canvas", "link", "meta", "head", "title"}


# ============================================================================
# 2. 工具函数
# ============================================================================

def die(msg, code=1):
    sys.stderr.write("❌ %s\n" % msg)
    sys.exit(code)


def read_text(path):
    """读文本文件，UTF-8 优先，失败回退 GBK（starter 声称支持但实际没做）。"""
    data = Path(path).read_bytes()
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "latin-1"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return data.decode("utf-8", errors="replace")


def parse_frontmatter(text):
    """
    极简 YAML frontmatter 解析器（只支持 key: value，避免引入 PyYAML 依赖）。
    支持：title / author / date / abstract / cover / tags / footer
    """
    if not text.startswith("---"):
        return {}, text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return {}, text
    raw, body = m.group(1), text[m.end():]
    meta = {}
    for line in raw.split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip().strip("'\"")
        meta[k.strip().lower()] = v
    return meta, body


def image_to_data_uri(src, base_dir, stats):
    """本地图片 → base64 data URI（修 B7）。SVG 拒绝（微信保存会丢）。"""
    p = Path(src)
    if not p.is_absolute():
        p = base_dir / p
    if not p.exists():
        stats["img_missing"].append(src)
        return None
    if p.suffix.lower() == ".svg":
        stats["img_svg"].append(src)
        return None
    mime = mimetypes.guess_type(str(p))[0] or "image/png"
    b64 = base64.b64encode(p.read_bytes()).decode("ascii")
    stats["img_embedded"].append(src)
    return "data:%s;base64,%s" % (mime, b64)


_INDENT_SENTINEL = "\ue000"   # 私有区字符，临时占位行首缩进


def protect_code_indent(code_html):
    """
    BeautifulSoup 在解析时会**吞掉嵌套标签前的空白**（实测：
    `<span>a</span>\\n    <span>b</span>` 中的换行+缩进会被静默丢弃），
    这会摧毁代码块的层级结构。
    做法：把每一处「换行 + 缩进」中的缩进替换成私有区哨兵字符，
    解析完（步骤 6.5b）再换回来。
    """
    # 覆盖三种位置：标签闭合后、纯文本中、以及行首（字符串开头）
    def _sub(m):
        return m.group(1) + m.group(2).replace(" ", _INDENT_SENTINEL).replace("\t", "\ue001")

    code_html = re.sub(r"(\n)([ \t]+)", _sub, code_html)
    code_html = re.sub(r"^([ \t]+)", lambda m: m.group(1).replace(" ", _INDENT_SENTINEL)
                       .replace("\t", "\ue001"), code_html)
    return code_html


def restore_code_indent(code_html):
    return code_html.replace(_INDENT_SENTINEL, " ")


def highlight_code(code, lang, theme):
    """用 Pygments 生成内联样式的语法高亮；没装 pygments 就原样输出。"""
    if not HAS_PYGMENTS or not lang:
        return None
    try:
        lexer = _pyg_lexer(lang, stripall=False)
    except Exception:
        return None
    try:
        formatter = _pyg_fmt(style="default", noclasses=True, nowrap=True)
        out = _pyg_highlight(code, lexer, formatter)
        # 删掉 pygments 自己的 <pre class=...><span style="..."> 壳
        out = re.sub(r"^<pre[^>]*>", "", out)
        out = re.sub(r"</pre>$", "", out)
        out = out.strip()
        return protect_code_indent(out)
    except Exception:
        return None


# 只对"汉字"与拉丁字母/数字之间加间距。
# 不能把全角标点（\u3000-\u303f）纳入，否则"内容。"会变成"内容 。"——标点本身自带间距。
CJK = r"\u4e00-\u9fa5"
_CJK_LATIN = re.compile(r"([%s])([A-Za-z0-9])" % CJK)
_LATIN_CJK = re.compile(r"([A-Za-z0-9])([%s])" % CJK)


def cjk_spacing_transform(text, mode="thin"):
    """
    中英文之间插入间距（修 B10）。注意：调用方需保证 text 不在 code/pre/a 内。
    thin = U+2009 极细空格（约 0.2em，推荐）
    """
    if mode == "none":
        return text
    sp = "\u2009" if mode == "thin" else " "
    text = _CJK_LATIN.sub(lambda m: m.group(1) + sp + m.group(2), text)
    text = _LATIN_CJK.sub(lambda m: m.group(1) + sp + m.group(2), text)
    return text


def filter_css(style_str):
    """只保留白名单内的 CSS 属性（真正执行 ALLOWED_CSS_PROPS，修 B11）。"""
    if not style_str:
        return ""
    keep = []
    for decl in style_str.split(";"):
        if ":" not in decl:
            continue
        prop = decl.split(":", 1)[0].strip().lower()
        if prop in ALLOWED_CSS_PROPS:
            keep.append(decl.strip())
    return "; ".join(keep) + (";" if keep else "")


# ============================================================================
# 3. 样式工厂 —— 所有 inline CSS 都在这里生成
# ============================================================================

class StyleFactory:
    def __init__(self, theme_name="ink", opts=None):
        if theme_name not in THEMES:
            die("未知主题 '%s'，可选：%s" % (theme_name, ", ".join(THEMES)))
        self.t = THEMES[theme_name]
        self.theme_name = theme_name
        self.o = opts or {}

    # --- 块级 ---
    def h2(self):
        t = self.t
        return ("font-size:20px;font-weight:bold;line-height:1.6;color:%s;"
                "margin:32px 0 14px 0;padding:0 0 0 12px;"
                "border-left:4px solid %s;letter-spacing:0.5px;"
                % (t["accent"], t["accent"]))

    def h3(self):
        t = self.t
        return ("font-size:17px;font-weight:bold;line-height:1.6;color:%s;"
                "margin:24px 0 10px 0;padding-left:10px;"
                "border-left:3px solid %s;"
                % (t["accent"], t["accent_light"].replace("#e", "#b") if False else t["accent"]))

    def h4(self):
        t = self.t
        return ("font-size:15px;font-weight:bold;line-height:1.6;color:%s;"
                "margin:18px 0 8px 0;" % t["text"])

    def p(self):
        t = self.t
        return ("font-size:16px;line-height:1.85;color:%s;margin:14px 0;"
                "letter-spacing:0.4px;word-break:break-word;" % t["text"])

    def li(self):
        t = self.t
        return ("font-size:16px;line-height:1.85;color:%s;margin:6px 0;"
                "word-break:break-word;" % t["text"])

    def list(self):
        return "margin:12px 0;padding-left:24px;list-style-type:disc;"

    def blockquote(self):
        t = self.t
        return ("background-color:%s;color:%s;padding:14px 16px;margin:18px 0;"
                "border-left:4px solid %s;font-size:15px;line-height:1.8;"
                "border-radius:0 4px 4px 0;"
                % (t["quote_bg"], t["text_sub"], t["accent"]))

    def code_inline(self):
        t = self.t
        return ("background-color:%s;color:#c7254e;font-size:14px;"
                "padding:2px 6px;border-radius:3px;font-family:Menlo,Consolas,monospace;"
                "word-break:break-all;" % t["code_bg"])

    def code_block(self):
        """
        代码块样式。

        【2026-10-06 增强】微信对 white-space:pre-wrap 的支持**不稳定**——
        一旦被剥离，整段代码会塌成一行（等于 starter 的 B1 缺陷重现）。
        因此提供 safe_code 模式：额外用 <br /> 显式断行 + &nbsp; 保护缩进，
        即使 pre-wrap 被剥离，代码结构依然完整。
        """
        t = self.t
        return ("background-color:%s;color:%s;font-size:13px;line-height:1.7;"
                "padding:16px 18px;margin:16px 0;border-radius:5px;"
                "border:1px solid %s;font-family:Menlo,Consolas,monospace;"
                "white-space:pre-wrap;word-break:break-word;overflow-wrap:anywhere;"
                % (t["code_bg"], t["code_text"], t["border"]))

    def table(self):
        t = self.t
        return "border-collapse:collapse;margin:16px 0;width:100%;font-size:14px;table-layout:auto;"

    def th(self):
        t = self.t
        return ("background-color:%s;color:%s;font-weight:bold;padding:10px 12px;"
                "border:1px solid %s;text-align:left;font-size:14px;"
                % (t["table_head_bg"], t["accent"], t["border"]))

    def td(self):
        t = self.t
        return ("padding:10px 12px;border:1px solid %s;color:%s;font-size:14px;"
                "line-height:1.7;" % (t["border"], t["text"]))

    def a(self):
        t = self.t
        return ("color:%s;text-decoration:none;border-bottom:1px solid %s;"
                "word-break:break-all;" % (t["accent"], t["accent_light"]))

    def img(self):
        return ("max-width:100%;height:auto;display:block;margin:16px auto;"
                "border-radius:4px;")

    def figcaption(self):
        t = self.t
        return ("font-size:13px;color:%s;text-align:center;margin:-8px 0 18px 0;"
                "line-height:1.6;" % t["text_sub"])

    def hr(self):
        t = self.t
        return ("border:none;border-top:1px solid %s;margin:28px 0;height:0;"
                % t["border"])

    def callout(self, kind):
        icon, label, color, bg = CALLOUT_KINDS[kind]
        return ("background-color:%s;border-left:4px solid %s;padding:14px 16px;"
                "margin:18px 0;border-radius:0 4px 4px 0;" % (bg, color))

    def callout_title(self, kind):
        icon, label, color, bg = CALLOUT_KINDS[kind]
        return ("font-size:15px;font-weight:bold;color:%s;margin:0 0 8px 0;"
                "line-height:1.6;letter-spacing:0.3px;" % color)

    def callout_body(self, kind):
        t = self.t
        return ("font-size:15px;line-height:1.8;color:%s;margin:0;" % t["text"])

    def toc_box(self):
        t = self.t
        return ("background-color:%s;border:1px solid %s;padding:18px 20px;"
                "margin:20px 0;border-radius:6px;" % (t["accent_light"], t["border"]))

    def toc_title(self):
        t = self.t
        return ("font-size:16px;font-weight:bold;color:%s;margin:0 0 10px 0;"
                % t["accent"])

    def toc_item(self, level):
        t = self.t
        if level == 2:
            return ("font-size:15px;color:%s;margin:6px 0;line-height:1.7;"
                    "padding-left:14px;font-weight:bold;" % t["text"])
        return ("font-size:14px;color:%s;margin:4px 0;line-height:1.7;"
                "padding-left:30px;" % t["text_sub"])

    def meta_box(self):
        t = self.t
        return ("background-color:%s;padding:18px 20px;margin:0 0 24px 0;"
                "border-radius:6px;border-bottom:1px solid %s;"
                % (t["quote_bg"], t["border"]))

    def meta_title(self):
        t = self.t
        return ("font-size:19px;font-weight:bold;color:%s;margin:0 0 8px 0;"
                "line-height:1.5;" % t["text"])

    def meta_sub(self):
        t = self.t
        return ("font-size:13px;color:%s;margin:0 0 10px 0;line-height:1.7;"
                % t["text_sub"])

    def abstract(self):
        t = self.t
        return ("font-size:14px;color:%s;line-height:1.8;margin:0;padding:12px 14px;"
                "background-color:%s;border-radius:4px;" % (t["text_sub"], t["accent_light"]))

    def footer(self):
        t = self.t
        return ("font-size:13px;color:%s;line-height:1.8;margin:0;padding:16px 0;"
                "border-top:1px solid %s;text-align:center;" % (t["text_sub"], t["border"]))

    def cover(self):
        return "max-width:100%;height:auto;display:block;margin:0 0 20px 0;border-radius:6px;"


# ============================================================================
# 4. Callout 预处理器（markdown 之前）
# ============================================================================

# 逐行锚定的 callout 匹配：:::kind [标题] ... :::（要求开闭行都独占一行）
#
# 【P2 修复，2026-10-06】真实发布时发现：`(.*?)` 在 re.S 下会跨越
# 中间的 `## 标题` 继续匹配，导致「一个没闭合的 callout」把后续整节
# 标题和正文全吞进框里，下一个 callout 的 `:::` 被当成本框的闭合。
# 修法：正文不允许出现块级标题（`#`~`######` 独占一行），
# 遇到就说明本 callout 已越界，正则在此终止。
CALLOUT_BODY = r"(?:(?!^#{1,6}[ \t])[\s\S])*?"
CALLOUT_RE = re.compile(
    r"^:::[ \t]*(note|tip|warn|danger|key)[ \t]*(.*?)[ \t]*\r?\n"
    r"(?P<body>" + CALLOUT_BODY + r")"
    r"^:::[ \t]*\r?$",
    re.M,
)
CALLOUT_TOKEN = "%%WCALLOUT_%d%%"


def find_unclosed_callouts(text):
    """
    诊断：找出没有配对闭合的 callout。
    【P5 修复，2026-10-06】真实发布时发现文章里少写一个 `:::`，
    导致后面整节被吞进上一个框。转换器当时静默接受了——
    现在会明确报出来，而不是让作者去线上才发现。
    """
    starts = list(re.finditer(r"^:::[ \t]*(note|tip|warn|danger|key)\b", text, re.M))
    ends = list(re.finditer(r"^:::[ \t]*\r?$", text, re.M))
    if len(starts) <= len(ends):
        return []
    # 找出哪个起始没有对应的闭合（按顺序配对）
    orphans = []
    for i, st in enumerate(starts):
        if i >= len(ends) or ends[i].start() < st.start():
            orphans.append((st.group(1), text.count("\n", 0, st.start()) + 1))
    return orphans


def extract_callouts(text):
    """
    把 :::kind 标题 ... ::: 抠出来，交给 markdown 单独渲染内层，
    再用 token 占位防止被破坏。返回 (处理后文本, callout 列表)。
    """
    callouts = []

    def _sub(m):
        kind = m.group(1)
        title = m.group(2) or ""
        inner = m.group("body")
        callouts.append((kind, title, inner))
        return "\n\n" + (CALLOUT_TOKEN % (len(callouts) - 1)) + "\n\n"

    return CALLOUT_RE.sub(_sub, text), callouts


# ============================================================================
# 5. 输入读取
# ============================================================================

_INLINE_CODE_TOKEN = "WCCODE%sWC"
_FENCE_TOKEN = "WCFENCE%sWCE"


def inline_div_to_span(text):
    """
    内联 <div> 会让 markdown 从中间劈开段落（实测 B5）。
    在进 markdown 之前把 <div>/</div> 降级为 <span>。

    【P1 修复，2026-10-06】真实发布时发现：原先的全局正则会把**行内代码和
    代码块里**本该原样显示的 `<div>` 也一起改掉。在一篇讲 HTML 标签的文章里，
    这导致读者看到的是 `<span>` 而不是 `<div>`，事实被改错了。
    修法：先用占位符把行内代码（`x`）和围栏代码块（```）保护起来，
    处理完再还原。
    """
    vault = []

    def _stash(m):
        vault.append(m.group(0))
        return _INLINE_CODE_TOKEN % (len(vault) - 1)

    # 1. 保护围栏代码块（多行）
    text = re.sub(r"(?ms)^```.*?^```[ \t]*$", lambda m: _stash(m), text)
    # 2. 保护行内代码
    text = re.sub(r"`[^`\n]+`", lambda m: _stash(m), text)

    # 3. 现在可以安全地降级 div 了
    text = re.sub(r"<\s*/?\s*div\s*>",
                  lambda m: "</span>" if m.group(0).startswith("</") else "<span>",
                  text, flags=re.I)

    # 4. 还原
    def _unstash(m):
        return vault[int(m.group(1))]

    text = re.sub(r"WC(?:CODE|FENCE)(\d+)WC", _unstash, text)
    return text


def read_markdown(text, base_dir, stats, cjk="thin"):
    """Markdown → 原始 HTML（含 callout 处理）。"""
    text = inline_div_to_span(text)
    for kind, line in find_unclosed_callouts(text):
        stats.setdefault("callout_unclosed", []).append((kind, line))
    text, callouts = extract_callouts(text)

    html = md.markdown(
        text,
        extensions=["extra", "sane_lists", "admonition", "toc", "nl2br"],
        extension_configs={"toc": {"permalink": False}},
    )

    # 还原 callout：单独用 markdown 渲染内层，产出 <p> 结构。
    # 用 html.parser 解析裸片段：lxml 会自动补 <html><body> 外壳，
    # 注入到正文里会污染整棵树（实测导致 callout 全部丢失）。
    for idx, (kind, title, inner) in enumerate(callouts):
        token = CALLOUT_TOKEN % idx
        if token not in html:
            continue
        inner_html = md.markdown(inner, extensions=["extra", "sane_lists"])
        holder = BeautifulSoup(
            '<div class="__callout__" data-kind="%s" data-title="%s" data-idx="%d">%s</div>'
            % (kind, html_mod.escape(title, quote=True), idx, inner_html),
            "html.parser",
        )
        frag = "".join(str(c) for c in holder.contents)
        html = html.replace(token, frag)
    return html


def read_docx(path, stats):
    """Word → HTML。相比 starter 补上：列表、表格、图片、链接。"""
    if Document is None:
        die("需要 python-docx 才能读取 .docx：pip install python-docx")
    doc = Document(path)
    parts = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name if para.style else "") or ""
        low = style.lower()

        if low.startswith("heading"):
            lvl = "".join(c for c in style if c.isdigit()) or "1"
            tag = "h2" if lvl in ("1", "2") else "h3"
            parts.append("<%s>%s</%s>" % (tag, html_mod.escape(text), tag))
        elif "list bullet" in low or "list number" in low:
            parts.append("<ul><li>%s</li></ul>" % html_mod.escape(text))
        elif "quote" in low:
            parts.append("<blockquote><p>%s</p></blockquote>" % html_mod.escape(text))
        else:
            frag = ["<p>"]
            for run in para.runs:
                t = html_mod.escape(run.text)
                if not t:
                    continue
                if run.bold and run.italic:
                    frag.append('<span style="font-weight:bold;font-style:italic;">%s</span>' % t)
                elif run.bold:
                    frag.append('<span style="font-weight:bold;">%s</span>' % t)
                elif run.italic:
                    frag.append('<span style="font-style:italic;">%s</span>' % t)
                else:
                    frag.append(t)
            frag.append("</p>")
            parts.append("".join(frag))

    # 表格
    for table in doc.tables:
        rows = []
        for i, row in enumerate(table.rows):
            cells = []
            tag = "th" if i == 0 else "td"
            for c in row.cells:
                cells.append("<%s>%s</%s>" % (tag, html_mod.escape(c.text.strip()), tag))
            rows.append("<tr>%s</tr>" % "".join(cells))
        if rows:
            parts.append("<table><tbody>%s</tbody></table>" % "".join(rows))
            stats["tables"] += 1

    # 图片
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            try:
                blob = rel.target_part.blob
                b64 = base64.b64encode(blob).decode("ascii")
                ext = rel.target_part.partname.ext.lstrip(".").lower() or "png"
                mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/%s" % ext
                parts.append('<img src="data:%s;base64,%s" />' % (mime, b64))
                stats["img_embedded"].append("docx:inline")
            except Exception:
                pass
    return "\n".join(parts)


# ============================================================================
# 6. 核心：语义化转换
# ============================================================================

def replace_tag_keeping_children(soup, tag, new_name, new_style):
    """
    替换标签但**保留子节点**。
    starter 用 `new.string = old.get_text()` 把子节点拍平，
    导致「加粗里的行内代码和链接全部消失」（实测 B2/B3）。
    """
    for el in soup.find_all(tag):
        el.name = new_name
        if new_style:
            el["style"] = new_style


def read_docx(path, stats):
    """Word → HTML。相比 starter 补上：列表、表格、图片、链接。"""
    if Document is None:
        die("需要 python-docx 才能读取 .docx：pip install python-docx")
    doc = Document(path)
    parts = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        style = (para.style.name if para.style else "") or ""
        low = style.lower()

        if low.startswith("heading"):
            lvl = "".join(c for c in style if c.isdigit()) or "1"
            tag = "h2" if lvl in ("1", "2") else "h3"
            parts.append("<%s>%s</%s>" % (tag, html_mod.escape(text), tag))
        elif "list bullet" in low or "list number" in low:
            parts.append("<ul><li>%s</li></ul>" % html_mod.escape(text))
        elif "quote" in low:
            parts.append("<blockquote><p>%s</p></blockquote>" % html_mod.escape(text))
        else:
            frag = ["<p>"]
            for run in para.runs:
                t = html_mod.escape(run.text)
                if not t:
                    continue
                if run.bold and run.italic:
                    frag.append('<span style="font-weight:bold;font-style:italic;">%s</span>' % t)
                elif run.bold:
                    frag.append('<span style="font-weight:bold;">%s</span>' % t)
                elif run.italic:
                    frag.append('<span style="font-style:italic;">%s</span>' % t)
                else:
                    frag.append(t)
            frag.append("</p>")
            parts.append("".join(frag))

    # 表格
    for table in doc.tables:
        rows = []
        for i, row in enumerate(table.rows):
            cells = []
            tag = "th" if i == 0 else "td"
            for c in row.cells:
                cells.append("<%s>%s</%s>" % (tag, html_mod.escape(c.text.strip()), tag))
            rows.append("<tr>%s</tr>" % "".join(cells))
        if rows:
            parts.append("<table><tbody>%s</tbody></table>" % "".join(rows))
            stats["tables"] += 1

    # 图片
    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            try:
                blob = rel.target_part.blob
                b64 = base64.b64encode(blob).decode("ascii")
                ext = rel.target_part.partname.ext.lstrip(".").lower() or "png"
                mime = "image/jpeg" if ext in ("jpg", "jpeg") else "image/%s" % ext
                parts.append('<img src="data:%s;base64,%s" />' % (mime, b64))
                stats["img_embedded"].append("docx:inline")
            except Exception:
                pass
    return "\n".join(parts)


# ============================================================================
# 6. 核心：语义化转换
# ============================================================================

def replace_tag_keeping_children(soup, tag, new_name, new_style):
    """
    替换标签但**保留子节点**。
    starter 用 `new.string = old.get_text()` 把子节点拍平，
    导致「加粗里的行内代码和链接全部消失」（实测 B2/B3）。
    """
    for el in soup.find_all(tag):
        el.name = new_name
        if new_style:
            el["style"] = new_style


def convert(html, meta, theme_name, opts, base_dir, stats):
    sf = StyleFactory(theme_name, opts)
    soup = BeautifulSoup(html, "lxml")

    # --- 6.1 彻底删除禁用标签 ---
    for name in DROP_TAGS:
        for el in soup.find_all(name):
            el.decompose()

    # --- 6.2 h1 = 文章标题。
    #     公众号标题栏由平台提供，正文里再放 h1 既重复又违规 —— 直接移出正文，
    #     标题改由 meta_header() 渲染成预览可见的标题块。
    #     因此 ## 及以下**不降级**，保持 h2/h3 层级。
    for h1 in soup.find_all("h1"):
        h1.decompose()

    # --- 6.2b Callout 渲染 ---
    # 必须早于 6.3 的"降级非白名单标签"：占位 <div class="__callout__"> 会被 unwrap 掉。
    for holder in soup.select("div.__callout__"):
        kind = holder.get("data-kind", "note")
        title = holder.get("data-title", "")
        icon, label, color, _bg = CALLOUT_KINDS.get(kind, CALLOUT_KINDS["note"])

        box = soup.new_tag("p")
        box["style"] = sf.callout(kind)
        t = soup.new_tag("span")
        t["style"] = sf.callout_title(kind)
        t.string = "%s %s%s" % (icon, label, ("　" + title) if title else "")
        box.append(t)

        inner_ps = holder.find_all("p", recursive=False) or [holder]
        for i, ip in enumerate(inner_ps):
            b = soup.new_tag("p")
            b["style"] = sf.callout_body(kind) + ("margin-top:8px;" if i else "")
            for child in list(ip.contents):
                b.append(child.extract())
            box.append(b)
        holder.replace_with(box)
        stats["callouts"].append(kind)

    # --- 6.3a 分隔线（修 B4）：<hr> 不在公众号白名单，先转成带 border-top 的 <p>。 ---
    for hr in list(soup.find_all("hr")):
        p = soup.new_tag("p")
        p["style"] = sf.hr()
        hr.replace_with(p)

    # --- 6.3 降级非白名单标签（保留内容） ---
    for el in soup.find_all(True):
        if el.name in ALLOWED_TAGS or el.name in ("html", "body", "[document]"):
            continue
        el.unwrap()

    # --- 6.4 标题：加序号 + 收集目录 ---
    # 计数器只在遇到对应层级时递增（h3 出现多次只算一个 h2 章节）
    toc_entries = []
    h2n = 0
    h3n = 0
    for h in soup.find_all(["h2", "h3", "h4"]):
        if h.name == "h2":
            h2n += 1
            h3n = 0
        elif h.name == "h3":
            h3n += 1
        text = h.get_text().strip()
        # 去掉 markdown 生成的 id（公众号不允许 id）
        if h.get("id"):
            del h["id"]
        if opts.get("number_headings", True) and h.name in ("h2", "h3"):
            prefix = "%d. " % h2n if h.name == "h2" else "%d.%d " % (h2n, h3n)
            if not re.match(r"^\d+[\.\d]*\s", text):
                h.insert(0, NavigableString(prefix))
                text = prefix + text
        h["style"] = sf.h2() if h.name == "h2" else (sf.h3() if h.name == "h3" else sf.h4())
        if h.name in ("h2", "h3") and len(text) <= 60:
            toc_entries.append((2 if h.name == "h2" else 3, text))

    # --- 6.5 代码块（修 B1：必须保留换行） ---
    for pre in soup.find_all("pre"):
        code_el = pre.find("code")
        raw = code_el.get_text() if code_el else pre.get_text()
        cls = ""
        if code_el and code_el.get("class"):
            cls = " ".join(code_el.get("class"))
        lang = ""
        m = re.search(r"language-([\w+#-]+)", cls)
        if m:
            lang = m.group(1)

        safe = opts.get("safe_code", False)
        hl = highlight_code(raw, lang, theme_name) if opts.get("highlight", True) else None
        base = sf.code_block()

        if not safe:
            # 普通模式：单 <p> + white-space:pre-wrap（依赖 CSS）
            inner = hl if hl is not None else html_mod.escape(raw).replace("\n", "<br />")
            if hl is not None:
                inner = protect_code_indent(inner)
            p = soup.new_tag("p")
            p["style"] = base
            frag = BeautifulSoup(inner, "html.parser")
            holder = soup.new_tag("span")
            for child in list(frag.contents):
                holder.append(child.extract())
            p.append(holder)
            pre.replace_with(p)
        else:
            # safe 模式（抗 CSS 剥离）：
            #   换行 → 显式 <br />（不依赖 white-space）
            #   缩进 → 每行一个 <span>，用 padding-left 表达缩进层级
            #           （padding-left 在微信里比 white-space 稳定得多）
            # 因此 safe 模式**放弃语法高亮**——高亮的 span 会被行边界切断。
            p = soup.new_tag("p")
            p["style"] = base
            lines = raw.split("\n")
            for i, ln in enumerate(lines):
                if i > 0:
                    br = soup.new_tag("br")
                    p.append(br)
                stripped = ln.rstrip()
                pad = len(stripped) - len(stripped.lstrip(" "))
                seg = soup.new_tag("span")
                # 缩进同时用 padding-left（抗剥离）与 \u00a0（双保险）
                seg["style"] = ("padding-left:%dpx;font-size:13px;line-height:1.6;"
                                "color:%s;font-family:Menlo,Consolas,monospace;"
                                % (pad * 8, sf.t["code_text"]))
                seg.append(NavigableString("\u00a0" * pad + html_mod.escape(stripped.lstrip(" "))))
                p.append(seg)
            pre.replace_with(p)
        stats["code_blocks"] += 1

    # 解析完成后把哨兵换回真实缩进（BeautifulSoup 解析会吃掉标签前空白）
    for holder in soup.find_all("span"):
        if _INDENT_SENTINEL in str(holder) or "\ue001" in str(holder):
            for node in list(holder.find_all(string=True)):
                s = str(node)
                if _INDENT_SENTINEL in s or "\ue001" in s:
                    node.replace_with(NavigableString(
                        s.replace(_INDENT_SENTINEL, " ").replace("\ue001", "\t")))

    # --- 6.6 行内 code ---
    for code in soup.find_all("code"):
        if code.find_parent("pre"):
            continue
        replace_tag_keeping_children(soup, "code", "span", sf.code_inline())
        stats["inline_code"] += 1

    # --- 6.7 引用块（修 B3：保留多段） ---
    for bq in soup.find_all("blockquote"):
        bq["style"] = sf.blockquote()
        for p in bq.find_all("p"):
            p["style"] = "margin:6px 0;font-size:15px;line-height:1.8;color:%s;" % sf.t["text_sub"]

    # --- 6.8 strong / em（修 B2：保留子节点） ---
    replace_tag_keeping_children(soup, "strong", "span", "font-weight:bold;")
    replace_tag_keeping_children(soup, "b", "span", "font-weight:bold;")
    replace_tag_keeping_children(soup, "em", "span", "font-style:italic;")
    replace_tag_keeping_children(soup, "i", "span", "font-style:italic;")

    # --- 6.10 图片（修 B6/B7） ---
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src.startswith("data:") and not src.startswith("http"):
            uri = image_to_data_uri(src, base_dir, stats)
            if uri:
                img["src"] = uri
        elif src.startswith("http"):
            stats["img_external"].append(src)
        img["style"] = sf.img()
        if img.get("alt"):
            stats["img_alt"] += 1

    # --- 6.11 图注：紧跟图片的单独 <p> 视为 figcaption ---
    for p in list(soup.find_all("p")):
        prev = p.find_previous_sibling()
        if prev is not None and prev.name == "img" and len(p.get_text().strip()) <= 40:
            p.name = "figcaption"

    # --- 6.12 列表（修 B8/B9） ---
    for lst in soup.find_all(["ul", "ol"]):
        lst["style"] = sf.list() + ("list-style-type:decimal;" if lst.name == "ol" else "")
        for li in lst.find_all("li", recursive=False):
            li["style"] = sf.li()
        # 嵌套列表：保留层级缩进
        for inner in lst.find_all(["ul", "ol"]):
            if inner.name != lst.name:
                inner["style"] = sf.list()

    # --- 6.13 表格 ---
    for table in soup.find_all("table"):
        table["style"] = sf.table()
        for i, tr in enumerate(table.find_all("tr")):
            cells = tr.find_all(["th", "td"], recursive=False)
            for c in cells:
                c["style"] = sf.th() if c.name == "th" else sf.td()
            if i > 0 and len(cells) > 2 and i % 2 == 0:
                for c in cells:
                    c["style"] += "background-color:%s;" % sf.t["table_stripe"]
        if not table.find("th"):
            stats["table_no_th"] += 1
        # 宽表提示
        ncol = len(table.find_all("tr")[0].find_all(["th", "td"])) if table.find_all("tr") else 0
        if ncol >= 5:
            stats["wide_table"] += 1

    # --- 6.14 链接 ---
    for a in soup.find_all("a"):
        a["style"] = sf.a()
        if a.get("href", "").startswith("http"):
            stats["links"] += 1

    # --- 6.15 段落 ---
    for p in soup.find_all("p"):
        if p.get("style"):
            continue
        p["style"] = sf.p()

    # --- 6.16 中文排版：全局找裸文本节点做中英间距（修 B10） ---
    if opts.get("cjk_spacing", "thin") != "none":
        skip = {"pre", "code", "a", "figcaption"}
        for node in soup.find_all(string=True):
            if not node.strip():
                continue
            if node.find_parent(skip):
                continue
            new = cjk_spacing_transform(str(node), opts.get("cjk_spacing", "thin"))
            if new != str(node):
                node.replace_with(NavigableString(new))

    # --- 6.17 清理属性 + 执行 CSS 白名单（修 B11） ---
    for el in soup.find_all(True):
        for attr in ("class", "id", "align", "onclick", "data-kind",
                     "data-title", "data-idx", "data-keep", "width", "height"):
            if attr in el.attrs:
                del el.attrs[attr]
        if "style" in el.attrs:
            el["style"] = filter_css(el["style"])

    body = soup.find("body")
    content = "\n".join(str(c) for c in body.children if str(c).strip()) if body else str(soup)

    # --- 6.18 目录卡片（放在第一个 h2 之前） ---
    if opts.get("toc") and toc_entries:
        toc_html = ['<p style="%s">\U0001F5C2 目录</p>' % filter_css(sf.toc_title())]
        for lvl, text in toc_entries:
            safe = html_mod.escape(text)
            toc_html.append('<p style="%s">%s</p>' % (filter_css(sf.toc_item(lvl)), safe))
        toc_html.append(
            '<p style="font-size:12px;color:%s;margin:10px 0 0 0;line-height:1.6;">'
            '（公众号会剥离 id 锚点，故为静态目录；如需点击跳转，请在微信编辑器内手动加书签）'
            '</p>' % sf.t["text_sub"]
        )
        block = "\n".join(toc_html)
        if meta.get("abstract"):
            block = abstract_html(sf, meta) + "\n" + block
        content = block + "\n" + content
    elif meta.get("abstract"):
        content = abstract_html(sf, meta) + "\n" + content

    # --- 6.19 页脚 ---
    if opts.get("footer"):
        content += "\n" + footer_html(sf, meta, opts)

    stats["toc_entries"] = len(toc_entries)
    stats["word_count"] = count_words(soup)
    return content


def abstract_html(sf, meta):
    return ('<p style="%s">\U0001F4AC 摘要</p>\n<p style="%s">%s</p>'
            % (filter_css(sf.toc_title()), filter_css(sf.abstract()),
               html_mod.escape(meta["abstract"])))


def footer_html(sf, meta, opts):
    bits = []
    if opts.get("footer_text"):
        bits.append(html_mod.escape(opts["footer_text"]))
    if meta.get("author"):
        bits.append("作者 · %s" % html_mod.escape(meta["author"]))
    if meta.get("date"):
        bits.append(html_mod.escape(meta["date"]))
    line = "　|　".join(bits) if bits else "感谢阅读"
    tail = "本文由 wechat-publisher-pro 技能自动排版生成"
    return (
        '<p style="%s">— — —</p>\n'
        '<p style="%s">%s</p>\n'
        '<p style="font-size:12px;color:%s;margin:0;line-height:1.7;">%s</p>'
        % (filter_css(sf.hr()), filter_css(sf.footer()), line,
           sf.t["text_sub"], tail)
    )


def meta_header(sf, meta, opts, stats=None, base_dir=None):
    """元数据头部（标题/作者/日期/标签/封面），渲染在正文最前。
    注意：真正发布时标题应填在公众号标题栏、摘要填在摘要栏，
    封面走公众号的封面上传位；此块的价值是 ①本地预览能一眼看到
    ②反查"标题/作者/封面是否漏填"，发布时用 --no-meta-header 即可关掉。"""
    rows = []
    if meta.get("author"):
        rows.append("作者 · %s" % html_mod.escape(meta["author"]))
    if meta.get("date"):
        rows.append(html_mod.escape(meta["date"]))
    if meta.get("tags"):
        rows.append("标签 · %s" % html_mod.escape(meta["tags"]))
    head = ""
    if meta.get("cover"):
        # 封面同样走 base64 内嵌，避免相对路径粘贴后裂图
        cover_src = meta["cover"]
        if not cover_src.startswith(("data:", "http")) and base_dir is not None:
            uri = image_to_data_uri(cover_src, base_dir, stats if stats is not None
                                    else new_stats())
            cover_src = uri or cover_src
        if cover_src.startswith("data:"):
            head += '<img src="%s" style="%s" />' % (cover_src, filter_css(sf.cover()))
        else:
            # 留在正文里会被判为外链图，改为提示而不渲染
            if stats is not None:
                stats["img_external"].append(cover_src + " (cover)")
    if meta.get("title"):
        head += '<p style="%s">%s</p>' % (filter_css(sf.meta_title()),
                                          html_mod.escape(meta["title"]))
    if rows:
        head += '<p style="%s">%s</p>' % (filter_css(sf.meta_sub()),
                                          "　·　".join(rows))
    return head


def count_words(soup):
    text = soup.get_text()
    cjk = len(re.findall(r"[\u4e00-\u9fa5]", text))
    latin = len(re.findall(r"[A-Za-z]+", text))
    return cjk + latin


# ============================================================================
# 7. 合规体检器（可验证性）
# ============================================================================

def audit(content, meta, stats, warnings):
    """扫描成品 HTML 里残留的公众号违规项。"""
    issues = []

    def add(sev, code, msg, fix):
        issues.append((sev, code, msg, fix))

    for tag in ("script", "style", "iframe", "svg", "div"):
        n = len(re.findall(r"<%s[\s>]" % tag, content, re.I))
        if n:
            add("高", "TAG_%s" % tag.upper(),
                "残留 <%s> ×%d" % (tag, n), "改用 <p>/<span> 承载样式")

    # 注意：class/id 只能查**真实标签属性**。正文里出现 `class="..."` 字样
    # （比如讲 HTML 的技术文）是被转义过的纯文本，不算违规。
    n = len(re.findall(r"<[a-z][a-z0-9]*\s[^>]*\bclass\s*=", content, re.I))
    if n:
        add("高", "ATTR_CLASS", "残留 class 属性 ×%d" % n, "内联样式，删除 class")
    n = len(re.findall(r"<[a-z][a-z0-9]*\s[^>]*\bid\s*=", content, re.I))
    if n:
        add("高", "ATTR_ID", "残留 id 属性 ×%d" % n, "公众号剥离 id，删除")
    n = len(re.findall(r"<h1[\s>]", content, re.I))
    if n:
        add("高", "TAG_H1", "残留 <h1> ×%d" % n, "降级为 <h2>")

    # 布局类 CSS：只在 style 属性内部检查，避免误报"正文里提到 position:"的情况
    n = 0
    for m in re.finditer(r'style="([^"]*)"', content):
        decl = m.group(1)
        if re.search(r"(position\s*:|float\s*:|display\s*:\s*flex|display\s*:\s*grid|@media)", decl, re.I):
            n += 1
    if n:
        add("高", "CSS_LAYOUT", "残留布局类 CSS ×%d" % n, "position/float/flex/grid/@media 会被过滤")

    n = len(re.findall(r"<img[^>]+src=\"(?!data:|https://mmbiz\.qpic\.cn)[^\"]+\"", content, re.I))
    if n:
        add("中", "IMG_EXT", "%d 张图片不是 data: 或微信 CDN" % n,
            "本地图用 --embed，或发布前传素材库")

    for s in stats.get("img_missing", []):
        add("中", "IMG_MISS", "图片找不到：%s" % s, "检查路径是否相对 md 文件")
    for s in stats.get("img_svg", []):
        add("高", "IMG_SVG", "SVG 会被微信丢弃：%s" % s, "转成 PNG 再嵌入")

    n = len(re.findall(r'src="data:image/svg', content, re.I))
    if n:
        add("高", "IMG_SVG_DATA", "data:image/svg ×%d" % n, "SVG 在保存时消失，必须换 PNG")

    if stats.get("word_count", 0) > 20000:
        add("中", "LEN", "正文约 %d 字，可能超公众号上限" % stats["word_count"],
            "拆成上下篇，或做 --split")

    for lvl, code, msg, fix in issues:
        warnings.append("  [%s] %-14s %s\n       → %s" % (lvl, code, msg, fix))
    return issues


# ============================================================================
# 8. 输出外壳
# ============================================================================

def wrap_preview(content, title, preview="desktop"):
    """生成可直接在浏览器打开、手机宽度自适应的预览页。"""
    width = "420px" if preview == "phone" else "677px"
    label = "手机 375px 模拟" if preview == "phone" else "公众号正文宽度 677px"
    bg = "#e8eaed" if preview == "phone" else "#f2f3f5"
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s · 预览</title>
<style>
  body { margin:0; padding:24px 12px; background:%s;
         font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif; }
  .phone { max-width:%s; margin:0 auto; background:#fff; padding:%s;
           box-shadow:0 2px 20px rgba(0,0,0,.12); border-radius:%s; }
  .tipbar { max-width:%s; margin:0 auto 12px; font-size:12px; color:#666;
            text-align:center; letter-spacing:.5px; }
  .tipbar b { color:#1f4e79; }
</style>
</head>
<body>
<div class="tipbar">预览模式：<b>%s</b> ｜ 公众号内正文实际渲染宽度约 375px ｜ 复制时请只复制下方白框内内容</div>
<div class="phone">
%s
</div>
</body>
</html>
""" % (html_mod.escape(title), bg, width, "20px" if preview == "phone" else "32px",
       "12px" if preview == "phone" else "6px", width, label, content)


# ============================================================================
# 9. 单篇转换主流程
# ============================================================================

def new_stats():
    return {
        "code_blocks": 0, "inline_code": 0, "callouts": [], "links": 0,
        "img_embedded": [], "img_missing": [], "img_external": [],
        "img_svg": [], "img_alt": 0, "tables": 0, "table_no_th": 0,
        "wide_table": 0, "toc_entries": 0, "word_count": 0,
    }


def convert_one(in_path, out_path=None, theme="ink", opts=None, preview="desktop",
                quiet=False, do_audit=True):
    opts = opts or {}
    p = Path(in_path)
    if not p.exists():
        die("文件不存在：%s" % in_path)
    base_dir = p.parent
    stats = new_stats()

    ext = p.suffix.lower()
    raw = read_text(p) if ext not in (".docx",) else ""
    if ext == ".docx":
        meta, html = {}, read_docx(p, stats)
    else:
        meta, body = parse_frontmatter(raw)
        if not meta.get("title"):
            m = re.search(r"^#\s+(.+)$", body, re.M)
            if m:
                meta["title"] = m.group(1).strip()
        if not meta.get("abstract"):
            m = re.search(r"^>\s*(.+)$", body, re.M)
            if m and len(m.group(1)) > 20:
                meta["abstract"] = m.group(1).strip()
        if not meta.get("date"):
            meta["date"] = time_str()
        if not meta.get("author"):
            meta["author"] = "JingXueQing"
        html = read_markdown(body, base_dir, stats, opts.get("cjk_spacing", "thin"))

    content = convert(html, meta, theme, opts, base_dir, stats)
    sf = StyleFactory(theme, opts)
    if opts.get("meta_header", True) and meta.get("title"):
        content = meta_header(sf, meta, opts, stats, base_dir) + "\n" + content

    warnings = []
    issues = audit(content, meta, stats, warnings) if do_audit else []

    if out_path:
        page = wrap_preview(content, meta.get("title", p.stem), preview)
        Path(out_path).write_text(page, encoding="utf-8")
        # 同时输出纯内容版（直接粘贴用）
        Path(str(out_path).replace(".html", ".body.html")).write_text(
            content, encoding="utf-8")

    if not quiet:
        report(in_path, out_path, theme, meta, stats, issues, preview)
    return {"content": content, "meta": meta, "stats": stats, "issues": issues,
            "title": meta.get("title", p.stem)}


def time_str():
    import datetime
    return datetime.date.today().isoformat()


def report(in_path, out_path, theme, meta, stats, issues, preview):
    bar = "=" * 62
    print("\n" + bar)
    print("  wechat-publisher-pro  ·  主题 %s (%s)" % (theme, THEMES[theme]["label"]))
    print(bar)
    print("  输入      : %s" % in_path)
    if out_path:
        print("  输出      : %s" % out_path)
        print("              %s（纯内容，可直接粘贴）" % str(out_path).replace(".html", ".body.html"))
    print("  标题      : %s" % meta.get("title", "(未识别)"))
    print("  篇幅      : 约 %d 字" % stats["word_count"])
    if stats["word_count"] > 20000:
        print("             ⚠️  可能超出公众号 2 万字上限")
    print("-" * 62)
    print("  代码块 %d｜行内代码 %d｜提示框 %d｜链接 %d"
          % (stats["code_blocks"], stats["inline_code"],
             len(stats["callouts"]), stats["links"]))
    if stats["callouts"]:
        from collections import Counter
        cnt = Counter(stats["callouts"])
        print("  提示框分布: " + "  ".join(
            "%s×%d" % (CALLOUT_KINDS[k][1], v) for k, v in cnt.items()))
    if stats["img_embedded"]:
        print("  图片内嵌 : %d 张（base64）" % len(stats["img_embedded"]))
    if stats["img_external"]:
        print("  外链图片 : %d 张 ⚠️ 发布前建议上传素材库换 CDN 地址" % len(stats["img_external"]))
    for key, label in (("img_missing", "图片缺失"), ("img_svg", "SVG 需转 PNG")):
        if stats[key]:
            print("  %s: %s" % (label, ", ".join(stats[key])))
    if stats["wide_table"]:
        print("  宽表格   : %d 张（≥5 列），手机端可能拥挤，建议拆表" % stats["wide_table"])
    print("-" * 62)
    if stats.get("callout_unclosed"):
        for kind, line in stats["callout_unclosed"]:
            print("  ⚠️  callout 未闭合：第 %d 行的 :::%s 缺少配对的 :::" % (line, kind))
        print("       → 这会把后续整节内容吞进上一个框，务必补上闭合标记")
    if issues:
        hi = [i for i in issues if i[0] == "高"]
        mid = [i for i in issues if i[0] == "中"]
        print("  合规体检 : %d 高危 / %d 提醒" % (len(hi), len(mid)))
        for sev, code, msg, fix in issues:
            print("  [%s] %-14s %s" % (sev, code, msg))
            print("       → %s" % fix)
    else:
        print("  合规体检 : ✅ 全部通过（无违规标签 / 无 class / 无外链图）")
    print(bar)
    if out_path:
        print("  下一步：浏览器打开输出文件 → 选中白框内正文 → 复制 →")
        print("          mp.weixin.qq.com 新建图文 → 粘贴 → 手机预览 → 发布")
    print()


# ============================================================================
# 10. 批量转换
# ============================================================================

def batch(indir, outdir, theme, opts, preview, pattern="*.md"):
    files = sorted(Path(indir).glob(pattern))
    if not files:
        die("目录里没有匹配 %s 的文件：%s" % (pattern, indir))
    Path(outdir).mkdir(parents=True, exist_ok=True)
    print("\n批量转换：%d 个文件 → %s\n" % (len(files), outdir))
    ok, fail = 0, 0
    rows = []
    for f in files:
        try:
            r = convert_one(str(f), str(Path(outdir) / (f.stem + ".html")),
                            theme, dict(opts), preview, quiet=True)
            hi = len([i for i in r["issues"] if i[0] == "高"])
            rows.append((f.name, r["stats"]["word_count"], hi, "✅"))
            ok += 1
        except SystemExit:
            rows.append((f.name, 0, 0, "❌"))
            fail += 1
        except Exception as e:  # noqa: BLE001
            rows.append((f.name, 0, 0, "❌ %s" % e))
            fail += 1
    print("%-38s %8s %6s  %s" % ("文件", "字数", "高危", "结果"))
    print("-" * 66)
    for name, wc, hi, mark in rows:
        print("%-38s %8d %6d  %s" % (name[:38], wc, hi, mark))
    print("-" * 66)
    print("成功 %d / 失败 %d\n" % (ok, fail))
    return ok, fail


# ============================================================================
# 11. CLI
# ============================================================================

def main():
    ap = argparse.ArgumentParser(
        prog="wechat_publisher.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Markdown/Word → 微信公众号 HTML（JingXueQing 定制版）",
        epilog="""示例：
  %(prog)s article.md out.html --theme ink --toc --footer
  %(prog)s --batch ./posts --out-dir ./html --theme forest
  %(prog)s article.md --audit
  %(prog)s article.md out.html --preview phone
""",
    )
    ap.add_argument("input", nargs="?", help="输入 .md / .docx / .html")
    ap.add_argument("output", nargs="?", help="输出 .html")
    ap.add_argument("--batch", metavar="DIR", help="批量模式：输入目录")
    ap.add_argument("--out-dir", default="./html", help="批量输出目录")
    ap.add_argument("--pattern", default="*.md", help="批量匹配模式（默认 *.md）")
    ap.add_argument("--theme", default="ink", choices=sorted(THEMES), help="主题（默认 ink）")
    ap.add_argument("--toc", action="store_true", help="生成目录卡片")
    ap.add_argument("--footer", action="store_true", help="追加页脚版权块")
    ap.add_argument("--footer-text", help="页脚自定义文字")
    ap.add_argument("--no-meta-header", action="store_true", help="不在正文顶部渲染元信息块")
    ap.add_argument("--no-highlight", action="store_true", help="关闭代码语法高亮")
    ap.add_argument("--safe-code", action="store_true",
                    help="代码块双保险：额外用 <br/> 断行 + &nbsp; 保护缩进，"
                         "即使微信剥离 white-space 也不塌行（推荐发布时开启）")
    ap.add_argument("--no-number", action="store_true", help="标题不加序号")
    ap.add_argument("--cjk-spacing", default="thin", choices=["thin", "space", "none"],
                    help="中英文间距（默认 thin）")
    ap.add_argument("--preview", default="desktop", choices=["desktop", "phone"],
                    help="预览页宽度")
    ap.add_argument("--audit", action="store_true", help="只做合规体检，不输出文件")
    ap.add_argument("--list-themes", action="store_true", help="列出全部主题")
    args = ap.parse_args()

    if args.list_themes:
        print("\n可用主题：\n")
        for k, v in THEMES.items():
            print("  %-8s %-12s %s" % (k, v["label"], v["desc"]))
            print("           强调色 %s ｜ 底色 %s" % (v["accent"], v["accent_light"]))
        print()
        return 0

    opts = {
        "toc": args.toc,
        "footer": args.footer or bool(args.footer_text),
        "footer_text": args.footer_text,
        "meta_header": not args.no_meta_header,
        "highlight": not args.no_highlight,
        "safe_code": args.safe_code,
        "number_headings": not args.no_number,
        "cjk_spacing": args.cjk_spacing,
    }

    if args.batch:
        batch(args.batch, args.out_dir, args.theme, opts, args.preview, args.pattern)
        return 0

    if not args.input:
        ap.print_help()
        return 1

    if args.audit:
        r = convert_one(args.input, None, args.theme, opts, do_audit=True, quiet=True)
        print("\n合规体检：%s" % args.input)
        print("-" * 62)
        if not r["issues"]:
            print("✅ 全部通过")
        else:
            for sev, code, msg, fix in r["issues"]:
                print("  [%s] %-14s %s\n       → %s" % (sev, code, msg, fix))
        print("-" * 62)
        print("统计：约 %d 字｜代码块 %d｜提示框 %d｜内嵌图 %d\n"
              % (r["stats"]["word_count"], r["stats"]["code_blocks"],
                 len(r["stats"]["callouts"]), len(r["stats"]["img_embedded"])))
        return 1 if any(i[0] == "高" for i in r["issues"]) else 0

    if not args.output:
        args.output = str(Path(args.input).with_suffix(".wechat.html"))

    convert_one(args.input, args.output, args.theme, opts, args.preview)
    return 0


if __name__ == "__main__":
    sys.exit(main())
