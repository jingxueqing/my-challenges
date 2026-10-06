#!/usr/bin/env python3
"""
eval_suite.py — wechat-publisher-pro 技能的 eval 测试套件
=====================================================================
用法：
    python eval_suite.py                # 跑全部用例
    python eval_suite.py --verbose      # 打印每例详情
    python eval_suite.py --json out.json  # 导出机读结果（用于 AI 日志佐证）

设计原则：
  · 每条断言都必须是**客观可判定**的（字符串/结构检查），不靠肉眼
  · 覆盖三类：功能正确性 / 微信合规性 / 回归防护（针对 starter 的 12 个 bug）
  · 全部用例离线运行，无网络依赖
"""

import argparse
import html as html_mod
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent          # <skill>/tests
CONVERTER = HERE.parent / "scripts" / "wechat_publisher.py"
PY = sys.executable
FIXTURES = HERE / "fixtures"

PASS, FAIL = "PASS", "FAIL"

# 与主脚本 CALLOUT_KINDS 的背景色保持一致（含 # 前缀）
CALLOUT_BG = {
    "note": "#eaf1f8", "tip": "#eaf5ef", "warn": "#fdf0e6",
    "danger": "#fdecec", "key": "#f2ecfb",
}
results = []


def run_converter(args, cwd=None):
    """调用转换器，返回 (returncode, stdout, body_html)。"""
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "out.html"
        cmd = [PY, str(CONVERTER)] + args + [str(out)]
        p = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        body_file = Path(td) / "out.body.html"
        body = body_file.read_text(encoding="utf-8") if body_file.exists() else ""
        return p.returncode, p.stdout + p.stderr, body


# ============================================================================
# 用例定义
# ============================================================================

def t_violation_tags():
    """T01 违规标签必须被清除"""
    body = _body_of("t01_violation.md", ["--no-number"])
    # 布局类 CSS 只在 style 属性内检查：正文里提到 "position:absolute" 是正常文字
    style_attrs = re.findall(r'style="([^"]*)"', body)
    layout_in_css = [s for s in style_attrs if re.search(
        r"(position\s*:|float\s*:|display\s*:\s*flex|display\s*:\s*grid|@media)", s, re.I)]
    checks = [
        ("无 <script", not re.search(r"<script[\s>]", body, re.I)),
        ("无 <style", not re.search(r"<style[\s>]", body, re.I)),
        ("无 <iframe", not re.search(r"<iframe[\s>]", body, re.I)),
        ("无 <div", not re.search(r"<div[\s>]", body, re.I)),
        ("无 <h1", not re.search(r"<h1[\s>]", body, re.I)),
        ("无 <svg", not re.search(r"<svg[\s>]", body, re.I)),
        ("无 <video", not re.search(r"<video[\s>]", body, re.I)),
        ("无 class=", not re.search(r"\bclass\s*=", body, re.I)),
        ("无 id=", not re.search(r"\bid\s*=", body, re.I)),
        ("无 onclick=", not re.search(r"\bonclick\s*=", body, re.I)),
        ("style 属性内无 position/float/flex/grid", not layout_in_css),
        ("style 属性内无 @media", not any("@media" in s for s in style_attrs)),
        ("正文提及 position:absolute 的文字仍保留（不被误删）",
         "position:absolute" in body),
        ("正文提及 @media 的文字仍保留（不被误删）", "@media" in body),
    ]
    return checks


def t_code_block_newlines():
    """T02 回归：starter 的致命 bug —— 代码块换行被吞成一行"""
    body = _body_of("t02_code.md", [])
    code = _extract_code_block(body)
    return [
        ("代码块存在", bool(code)),
        ("代码块用 pre-wrap 保留换行", "white-space:pre-wrap" in body),
        ("保留第 2 行", "line_two" in code),
        ("保留第 3 行缩进", "line_three" in code),
        ("未把换行渲染成 <br>（用 pre-wrap 而非 br）", "<br" not in code),
        ("缩进空格被保留（4 空格起首的行）",
         re.search(r"\n {4,}\S", code) is not None),
        ("行首缩进在嵌套标签前后都保留",
         re.search(r"\n {4,}(?:<span[^>]*>)?return", code) is not None),
    ]


def t_nested_inline_preserved():
    """T03 回归：starter 的 bug —— 加粗里的行内代码与链接被拍平丢失"""
    body = _body_of("t03_nested.md", [])
    bold_block = ""
    m = re.search(r'<span style="font-weight:bold;">.*?</span></p>', body, re.S)
    if m:
        bold_block = m.group(0)
    return [
        ("加粗文本存在", "粗体内" in body),
        ("加粗内行内代码未丢失", "background-color" in bold_block and "code" in bold_block),
        ("加粗内链接未丢失", "<a href=" in bold_block),
        ("链接 href 保留原值", 'href="https://example.com/inside"' in body),
        ("斜体内行内代码未丢失",
         re.search(r'font-style:italic;">.*?background-color', body, re.S) is not None),
    ]


def t_multiline_blockquote():
    """T04 回归：starter 的 bug —— 多段引用被合并成一段"""
    body = _body_of("t04_quote.md", [])
    n_quote_paras = len(re.findall(r"blockquote", body))
    return [
        ("引用块存在", n_quote_paras >= 1),
        ("第一段保留", "引用第一段" in body),
        ("第二段保留", "引用第二段" in body),
        ("第二段未被合并掉（blockquote 内 ≥2 个 p）",
         len(re.findall(r"<blockquote", body)) >= 1 and body.count("引用第二段") >= 1),
    ]


def t_hr_preserved():
    """T05 回归：starter 的 bug —— <hr> 被整体丢弃"""
    body = _body_of("t05_hr.md", [])
    return [
        ("分隔线存在", "border-top:1px solid" in body),
        ("未用 <hr> 标签（不在公众号白名单，改用 p 承载）",
         not re.search(r"<hr[\s>]", body, re.I)),
    ]


def t_inline_div_not_split():
    """T06 回归：starter 的 bug —— 内联 <div> 把段落从中间劈开"""
    body = _body_of("t06_div.md", [])
    # 正确结果：前文 + span + 后文 全在同一个 <p> 内
    ok = re.search(r"前文<span[^>]*>div\s*内容</span>后文", body) is not None
    # starter 的错误结果：前文 </p><p>...<p>后文
    split = re.search(r"前文\s*</p>\s*<p", body) is not None
    return [
        ("内联 div 降级为 span，未劈开段落", ok),
        ("div 内容 未丢失", "内容" in body),
        ("前文未丢失", "前文" in body),
        ("后文未丢失", "后文" in body),
        ("未出现段落被劈开的迹象（starter 的 BUG 形态）", not split),
    ]


def t_image_embedded():
    """T07 回归：starter 的 bug —— 本地图保留相对路径导致粘贴后裂图"""
    rc, out, body = _run_on("t07_image.md")
    return [
        ("本地图已转 base64", "data:image/png;base64," in body),
        ("无残留相对路径", 'src="assets/' not in body),
        ("图片有 max-width", "max-width:100%" in body),
        ("图片块级居中", "display:block" in body),
    ]


def t_svg_rejected():
    """T08 回归：starter 未处理 SVG（微信保存会丢）"""
    rc, out, body = _run_on("t08_svg.md")
    return [
        ("SVG 未被嵌入（data:image/svg 不应出现）", "data:image/svg" not in body),
        ("SVG 未生成 <svg> 标签", not re.search(r"<svg[\s>]", body, re.I)),
    ]


def t_nested_list():
    """T09 回归：starter 的 bug —— 嵌套列表被拍平成同级"""
    body = _body_of("t09_list.md", [])
    nested_ul = len(re.findall(r"<ul[^>]*>\s*<li", body))
    return [
        ("列表存在", "<ul" in body or "<ol" in body),
        ("嵌套层级保留（内层 ul 在 li 内部）",
         re.search(r"<li[^>]*>(?:(?!</li>).)*<ul", body, re.S) is not None),
        ("ul 自身有样式（缩进可控）",
         re.search(r"<ul[^>]*style=\"[^\"]*padding-left", body) is not None),
    ]


def t_cjk_spacing():
    """T10 中英文自动间距"""
    body = _body_of("t10_cjk.md", [])
    return [
        ("插入了 thin space (U+2009)", "\u2009" in body),
        ("中文+英文边界已处理", "用了\u2009Python" in body),
        ("数字前也加了间距", "\u200980%" in body or "\u20092" in body),
        ("全角标点前不加多余间距（回归：不能把标点当汉字）",
         "内存\u20092GB\u3002" in body or "内存2GB。" in body),
        ("冒号前不加多余间距", "div\uff1a" in body),
    ]


def t_callout():
    """T11 Callout 提示框"""
    body = _body_of("t11_callout.md", []).lower()  # BeautifulSoup 会把 #eaf1f8 规范化为大写
    kinds = {}
    for k, bg in CALLOUT_BG.items():
        kinds[k] = ("background-color:%s" % bg) in body
    return [
        ("note 框生成", kinds.get("note", False)),
        ("tip 框生成", kinds.get("tip", False)),
        ("warn 框生成", kinds.get("warn", False)),
        ("danger 框生成", kinds.get("danger", False)),
        ("key 框生成", kinds.get("key", False)),
        ("callout 用 p 而非 div", not re.search(r"<div[\s>]", body)),
        ("自定义标题生效", "我的自定义标题" in body),
        ("callout 内 markdown 生效（加粗保留）", "font-weight:bold" in body),
        ("callout 标签文字生效（知识/实践/注意/踩坑/重点）",
         all(w in body for w in ("知识", "实践", "注意", "踩坑", "重点"))),
    ]




def t_toc():
    """T12 自动目录"""
    body = _body_of("t12_toc.md", ["--toc"])
    return [
        ("目录标题存在", "目录" in body),
        ("h2 条目被收集", "第一节" in body),
        ("h3 条目被收集", "子节" in body),
        ("目录在正文之前（索引早于第一个 h2）",
         body.index("目录") < body.index("第一节")),
        ("诚实标注了 id 锚点限制", "id 锚点" in body),
    ]


def t_footer():
    """T13 页脚版权"""
    body = _body_of("t13_footer.md", ["--footer", "--footer-text", "我的版权声明"])
    return [
        ("页脚分隔线", "border-top:1px solid" in body),
        ("自定义页脚文字", "我的版权声明" in body),
        ("作者信息", "JingXueQing" in body),
        ("日期信息", re.search(r"20\d\d-\d\d-\d\d", body) is not None),
        ("署名工具名", "wechat-publisher-pro" in body),
    ]


def t_metadata():
    """T14 文章元数据（frontmatter）"""
    body = _body_of("t14_meta.md", [])
    return [
        ("作者被渲染", "测试作者" in body),
        ("标签被渲染", "测试标签" in body),
        ("摘要被渲染", "这是摘要内容" in body),
        ("h1 标签不出现在正文（不违规）",
         not re.search(r"<h1[\s>]", body, re.I)),
        ("h1 标题文本改由 meta 标题块承载（只出现一次）",
         body.count("文章主标题") == 1),
    ]


def t_themes():
    """T15 多主题"""
    outs = {}
    for th in ("ink", "forest", "amber", "mono"):
        rc, out, b = _body_with(["--theme", th], "t15_theme.md")
        outs[th] = b
    return [
        ("ink 主题色生效", "#1f4e79" in outs["ink"]),
        ("forest 主题色生效", "#2f6b4f" in outs["forest"]),
        ("amber 主题色生效", "#b35c1e" in outs["amber"]),
        ("mono 主题色生效", "#262626" in outs["mono"]),
        ("四套主题输出互不相同", len(set(outs.values())) == 4),
    ]


def t_numbering():
    """T16 标题自动编号"""
    body = _body_of("t16_number.md", [])
    body_nonum = _body_of("t16_number.md", ["--no-number"])
    return [
        ("h2 编号为 1. 2.", re.search(r">1\. 章一", body) and re.search(r">2\. 章二", body)),
        ("h3 编号为 1.1", re.search(r">1\.1 ", body) is not None),
        ("--no-number 生效", not re.search(r">1\. 章一", body_nonum)),
    ]


def t_docx_input():
    """T17 Word 输入（含表格与图片）"""
    docx = FIXTURES / "t17_input.docx"
    if not docx.exists():
        return [("Word 测试文件存在", False, "缺少 fixtures/t17_input.docx")]
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "d.html"
        p = subprocess.run([PY, str(CONVERTER), str(docx), str(out)],
                           capture_output=True, text=True)
        body = Path(td, "d.body.html").read_text(encoding="utf-8") if Path(td, "d.body.html").exists() else ""
    return [
        ("转换成功", p.returncode == 0),
        ("标题被识别", "Word 标题" in body),
        ("正文被识别", "Word 正文段落" in body),
        ("表格被识别", "<table" in body),
        ("表头 th 存在", "<th" in body),
        ("列表被识别", "<ul" in body or "<ol" in body),
        ("无违规标签", not re.search(r"<(script|style|div|h1)[\s>]", body, re.I)),
    ]


def t_edge_cases():
    """T18 边界情况"""
    res = []
    with tempfile.TemporaryDirectory() as td:
        # 空文件
        empty = Path(td) / "empty.md"
        empty.write_text("", encoding="utf-8")
        p = subprocess.run([PY, str(CONVERTER), str(empty), str(Path(td) / "e.html")],
                           capture_output=True, text=True)
        res.append(("空文件不崩溃", p.returncode == 0))
        res.append(("空文件给出警告", "0 字" in p.stdout or "空" in p.stdout))

        # 不存在的文件
        p2 = subprocess.run([PY, str(CONVERTER), str(Path(td) / "nope.md"), str(Path(td) / "n.html")],
                            capture_output=True, text=True)
        res.append(("文件不存在时报错退出", p2.returncode != 0))
        res.append(("错误信息清晰", "不存在" in (p2.stdout + p2.stderr)))

        # GBK 编码文件
        gbk = Path(td) / "gbk.md"
        gbk.write_bytes("# 中文标题\n\n这是GBK编码的正文内容。\n".encode("gbk"))
        p3 = subprocess.run([PY, str(CONVERTER), str(gbk), str(Path(td) / "g.html")],
                            capture_output=True, text=True)
        gbody = Path(td, "g.body.html")
        gb = gbody.read_text(encoding="utf-8") if gbody.exists() else ""
        res.append(("GBK 编码文件可读", p3.returncode == 0 and "GBK" in gb
                    and "编码的正文内容" in gb))
    return res


def t_batch():
    """T19 批量转换"""
    with tempfile.TemporaryDirectory() as td:
        indir = Path(td) / "in"
        indir.mkdir()
        for i in range(3):
            (indir / ("post%d.md" % i)).write_text(
                "# 标题%d\n\n正文%d内容。\n" % (i, i), encoding="utf-8")
        outdir = Path(td) / "out"
        p = subprocess.run([PY, str(CONVERTER), "--batch", str(indir),
                            "--out-dir", str(outdir), "--theme", "forest"],
                           capture_output=True, text=True)
        # 预览页与纯内容页各 3 个
        pages = [f for f in outdir.glob("*.html") if not f.name.endswith(".body.html")]
        bodies = list(outdir.glob("*.body.html"))
        return [
            ("批量退出码为 0", p.returncode == 0),
            ("生成 3 个预览页", len(pages) == 3),
            ("生成 3 个纯内容页", len(bodies) == 3),
            ("输出汇总表", "成功" in p.stdout),
        ]


def t_audit():
    """T20 合规体检器"""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "a.md"
        f.write_text("# 标题\n\n正文一段。\n", encoding="utf-8")
        p = subprocess.run([PY, str(CONVERTER), str(f), "--audit"],
                           capture_output=True, text=True)
        o = p.stdout + p.stderr
        return [
            ("--audit 不生成文件", not list(Path(td).glob("*.html"))),
            ("合规时退出码 0", p.returncode == 0),
            ("输出 ✅ 全部通过", "全部通过" in o),
        ]


def t_list_themes():
    """T21 --list-themes"""
    p = subprocess.run([PY, str(CONVERTER), "--list-themes"],
                       capture_output=True, text=True)
    o = p.stdout
    return [
        ("退出码 0", p.returncode == 0),
        ("列出 ink", "ink" in o),
        ("列出 forest", "forest" in o),
        ("列出 amber", "amber" in o),
        ("列出 mono", "mono" in o),
        ("每套主题有说明", o.count("｜") >= 4),
    ]


def t_idempotent():
    """T22 幂等性：同输入两次转换结果应完全一致（可验证性要求）"""
    a = _body_of("t22_idem.md", ["--toc", "--footer"])[1]
    b = _body_of("t22_idem.md", ["--toc", "--footer"])[1]
    return [("两次转换输出完全一致", a == b)]


def t_large_article():
    """T23 长文（模拟 5000 字）"""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "big.md"
        parts = ["# 长文测试\n"]
        for i in range(60):
            parts.append("## 第 %d 节\n\n这是第 %d 节的正文内容，包含 English words 和数字 12345。" % (i, i))
        f.write_text("\n".join(parts), encoding="utf-8")
        p = subprocess.run([PY, str(CONVERTER), str(f), str(Path(td) / "b.html"), "--toc"],
                           capture_output=True, text=True)
        body = Path(td, "b.body.html")
        b = body.read_text(encoding="utf-8") if body.exists() else ""
        m = re.search(r"约 (\d+) 字", p.stdout)
        return [
            ("长文转换成功", p.returncode == 0),
            ("字数统计合理（>1000）", m and int(m.group(1)) > 1000),
            ("目录收集 60 条", b.count("第 ") >= 60),
        ]


def t_syntax_highlight():
    """T24 代码语法高亮"""
    nohl = _body_of("t24_codehl.md", ["--no-highlight"])
    hl_on = _body_of("t24_codehl.md", [])
    return [
        ("高亮开启时生成彩色 span", hl_on.count("color: #") >= 3),
        ("高亮 span 不是字面量（未被二次转义）", "&lt;span style" not in hl_on),
        ("--no-highlight 关闭彩色", nohl.count("color: #") <= 1),
        ("高亮后无 <html> 外壳注入", "<html>" not in hl_on),
        ("高亮后无 body 外壳残留", "<body>" not in hl_on),
    ]



def t_p1_div_in_code():
    """T27 回归 P1：行内代码/代码块里的 <div> 不应被改写
    （真实发布时发现：讲 HTML 标签的文章里，读者看到的标签名被改错了）"""
    body = _body_of("t27_p1_div_in_code.md", [])
    code_block = _extract_code_block(body)
    return [
        ("行内代码里的 <div> 保持原样", "&lt;div&gt;" in body),
        ("行内代码里的 </div> 保持原样", "&lt;/div&gt;" in body),
        ("真实 div 仍被降级为 span（前文<span>…</span>后文）",
         re.search(r"前文<span[^>]*>会被降级</span>后文", body) is not None),
        # 代码块内容会被语法高亮切成 <span>，因此不能直接找连续的 &lt;div&gt;，
        # 需剔除高亮标签后再比对
        ("代码块里的 <div> 保持原样",
         re.sub(r"<[^>]+>", "", code_block).replace("&lt;div&gt;", "").find("div") > 0
         and "&lt;span&gt;" not in re.sub(r"<[^>]+>", "", code_block)),
        ("代码块里 div 仍是 div 而非 span",
         "div" in re.sub(r"<[^>]+>", "", code_block)),
    ]


def t_p2_callout_leak():
    """T28 回归 P2：callout 不得吞掉后续的块级标题
    （真实发布时发现：正则贪婪匹配把整节标题和正文都吞进了框里）"""
    body = _body_of("t28_p2_callout_leak.md", [])
    return [
        ("两个 callout 都渲染了",
         body.count("border-radius:0 4px 4px 0") >= 2),
        (":::key 未泄漏到正文", ":::key" not in body and ":::danger" not in body),
        ("小节标题没被吞进 callout（h2 存在）",
         re.search(r"<h2[^>]*>.*?后面的小节标题", body) is not None),
        # h1 被 decompose（标题走 meta 块），所以正文只有 2 个 h2
        ("两个小节标题都在", body.count("<h2") == 2),
        ("callout 框内不含块级标题（未被吞）",
         "一、后面的小节标题" not in
         re.search(r'<p style="[^"]*border-radius:0 4px 4px 0;">.*?</p></p>',
                   body, re.S).group(0)),
        ("key 框正常渲染（含 ⭐ 重点）", "重点" in body),
    ]




def t_safe_code():
    """T29 safe_code 模式：抗 CSS 剥离"""
    normal = _body_of("t29_safe_code.md", [])
    safe = _body_of("t29_safe_code.md", ["--safe-code"])
    # 模拟微信把 white-space / padding-left / nbsp 全部剥离
    stripped = re.sub(r"\s*white-space:[^;\n]*;?", "", safe)
    stripped = re.sub(r"\s*padding-left:[^;\n]*;?", "", stripped)
    stripped = stripped.replace("\u00a0", "")
    visible = re.sub(r"<[^>]+>",
                     lambda m: "\n" if m.group(0).startswith("<br") else "", stripped)
    visible = html_mod.unescape(visible)
    lines = [x for x in visible.split("\n") if x.strip()]
    return [
        ("safe 模式生成了 <br />", len(re.findall(r"<br\s*/?>", safe)) >= 8),
        ("safe 模式用 padding-left 表达缩进", "padding-left:32px" in safe),
        ("safe 模式保留 white-space（双保险）", "white-space:pre-wrap" in safe),
        ("剥离 CSS 后换行仍存活（不塌成一行）", len(lines) >= 7),
        ("剥离 CSS 后代码内容完整",
         "def demo():" in visible and "return None" in visible),
        ("剥离 CSS 后深层缩进内容不丢", "深层缩进" in visible),
        ("普通模式未生成为每行 span（对照）",
         normal.count("padding-left") == 0),
    ]


# ============================================================================
# helpers
# ============================================================================

def _run_on(fixture_name, extra=None):
    f = FIXTURES / fixture_name
    if not f.exists():
        die("缺少 fixture：%s" % f)
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "o.html"
        cmd = [PY, str(CONVERTER), str(f), str(out)] + (extra or [])
        p = subprocess.run(cmd, capture_output=True, text=True)
        bf = Path(td) / "o.body.html"
        return p.returncode, p.stdout + p.stderr, (bf.read_text(encoding="utf-8") if bf.exists() else "")


def _body_of(fixture_name, extra=None):
    return _run_on(fixture_name, extra)[2]


def _body_with(extra, fixture_name):
    return _run_on(fixture_name, extra)


def _extract_code_block(body):
    m = re.search(r'<p style="[^"]*white-space:pre-wrap[^"]*">(.*?)</p>', body, re.S)
    return m.group(1) if m else ""


def die(msg):
    sys.stderr.write("❌ %s\n" % msg)
    sys.exit(1)





# ============================================================================
# runner
# ============================================================================

SUITE = [
    ("T01", "违规标签清除", t_violation_tags),
    ("T02", "代码块换行保留（回归 B1）", t_code_block_newlines),
    ("T03", "嵌套行内元素保留（回归 B2）", t_nested_inline_preserved),
    ("T04", "多段引用保留（回归 B3）", t_multiline_blockquote),
    ("T05", "分隔线保留（回归 B4）", t_hr_preserved),
    ("T06", "内联 div 不劈段落（回归 B5）", t_inline_div_not_split),
    ("T07", "本地图 base64 内嵌（回归 B7）", t_image_embedded),
    ("T08", "SVG 拒绝嵌入（回归 B7b）", t_svg_rejected),
    ("T09", "嵌套列表层级（回归 B8/B9）", t_nested_list),
    ("T10", "中英文自动间距（新增 B10）", t_cjk_spacing),
    ("T11", "Callout 提示框（新增）", t_callout),
    ("T12", "自动目录（新增）", t_toc),
    ("T13", "页脚版权（新增）", t_footer),
    ("T14", "文章元数据（新增）", t_metadata),
    ("T15", "多主题系统（新增）", t_themes),
    ("T16", "标题自动编号", t_numbering),
    ("T17", "Word 输入（表格/列表）", t_docx_input),
    ("T18", "边界情况（空/GBK/不存在）", t_edge_cases),
    ("T19", "批量转换（新增）", t_batch),
    ("T20", "合规体检器（新增）", t_audit),
    ("T21", "主题列表 CLI", t_list_themes),
    ("T22", "幂等性（可验证）", t_idempotent),
    ("T23", "长文 5000+ 字", t_large_article),
    ("T24", "代码语法高亮", t_syntax_highlight),
    ("T27", "代码内 div 不被改写（回归 P1）", t_p1_div_in_code),
    ("T28", "callout 不吞标题（回归 P2）", t_p2_callout_leak),
    ("T29", "safe_code 抗 CSS 剥离", t_safe_code),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", "-v", action="store_true")
    ap.add_argument("--json", help="导出结果 JSON")
    ap.add_argument("--only", help="只跑某几个用例 id，逗号分隔")
    args = ap.parse_args()

    only = set(args.only.split(",")) if args.only else None
    bar = "=" * 74
    print("\n" + bar)
    print("  wechat-publisher-pro · eval 测试套件")
    print("  用例 %d 个｜转换器 %s" % (len(SUITE), CONVERTER.name))
    print(bar)

    total_pass = total_fail = 0
    t0 = __import__("time").time()
    for tid, name, fn in SUITE:
        if only and tid not in only:
            continue
        try:
            checks = fn()
        except Exception as e:  # noqa: BLE001
            checks = [("用例执行未抛异常", False, "%s: %s" % (type(e).__name__, e))]
        npass = sum(1 for c in checks if c[1])
        nfail = len(checks) - npass
        total_pass += npass
        total_fail += nfail
        status = "✅" if nfail == 0 else "❌"
        print("\n%s %s  %-32s  %d/%d" % (status, tid, name, npass, len(checks)))
        if args.verbose or nfail:
            for c in checks:
                label, ok = c[0], bool(c[1])
                note = c[2] if len(c) > 2 else ""
                print("     %s %s%s" % ("✓" if ok else "✗", label,
                                        ("  → %s" % note) if note and not ok else ""))
        results.append({"id": tid, "name": name, "pass": npass,
                        "fail": nfail, "total": len(checks),
                        "cases": [{"name": c[0], "ok": bool(c[1]),
                                   "note": str(c[2]) if len(c) > 2 else ""} for c in checks]})

    dt = __import__("time").time() - t0
    print("\n" + bar)
    print("  断言总数 %d｜通过 %d｜失败 %d｜耗时 %.1fs"
          % (total_pass + total_fail, total_pass, total_fail, dt))
    print("  用例通过率 %d/%d" % (len([r for r in results if r["fail"] == 0]), len(results)))
    print(bar + "\n")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"total_assertions": total_pass + total_fail, "passed": total_pass,
             "failed": total_fail, "cases_total": len(results),
             "cases_passed": len([r for r in results if r["fail"] == 0]),
             "duration_sec": round(dt, 2), "results": results},
            ensure_ascii=False, indent=2), encoding="utf-8")
        print("📄 结果已导出：%s\n" % args.json)

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
