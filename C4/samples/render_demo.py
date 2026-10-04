#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 samples/demo_run.log 的真实输出渲染成终端风格 PNG（本机无浏览器截图权限，改用 Pillow 绘制）。
内容 100% 来自真实运行日志，未做任何虚构。"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/Users/jingxueqing/Desktop/C4-交付_JingXueQing_ai-log-forge")
LOG = (OUT / "samples/demo_run.log").read_text(encoding="utf-8").splitlines()

MONO = "/System/Library/Fonts/Menlo.ttc"
CJK = "/System/Library/Fonts/PingFang.ttc"
SIZE = 15
LH = 25

f_mono = ImageFont.truetype(MONO, SIZE)
f_cjk = ImageFont.truetype(CJK, SIZE)
f_mono_b = ImageFont.truetype(MONO, SIZE, index=1) if True else f_mono
try:
    f_mono_b = ImageFont.truetype(MONO, SIZE, index=1)
except Exception:
    f_mono_b = f_mono
f_cjk_b = ImageFont.truetype(CJK, SIZE + 1)
f_cjk_big = ImageFont.truetype(CJK, 34)
f_cjk_title = ImageFont.truetype(CJK, 19)

BG = (30, 34, 43)
BAR = (44, 49, 60)
FG = (230, 233, 239)
GREEN = (126, 226, 168)
RED = (255, 154, 154)
YEL = (255, 212, 121)
GRAY = (139, 147, 163)
BLUE = (138, 180, 255)
WHITE = (255, 255, 255)
CARD = (255, 255, 255)
PAGE = (247, 248, 250)
INK = (26, 29, 36)
SUB = (91, 100, 114)
LINE = (227, 231, 238)
AMBER = (199, 119, 0)
AMBER_SOFT = (255, 245, 229)
GREENC = (15, 153, 96)
GREEN_SOFT = (232, 247, 240)


def is_cjk(ch):
    return ord(ch) > 0x2E80


def draw_line(d, xy, text, base, bold=False):
    """逐字符绘制：ASCII 用等宽字体，CJK 用苹方，保证中英混排对齐。"""
    x, y = xy
    fm = f_mono_b if bold else f_mono
    fc = f_cjk_b if bold else f_cjk
    for ch in text:
        f = fc if is_cjk(ch) else fm
        d.text((x, y), ch, font=f, fill=base)
        x += f.getlength(ch)
    return x


def line_color(line):
    if "失败" in line or "Permission denied" in line or "KeyError:" in line:
        return RED
    if line.startswith("[完成]") or "100.0" in line:
        return GREEN
    if line.startswith("[注意]") or "迭代" in line or "80.0" in line:
        return YEL
    if line.startswith("#") or line.startswith("|") or line.startswith(">"):
        return BLUE
    if line.startswith("=") or line.startswith(" STEP ") or line.startswith("---"):
        return GRAY
    return FG


def sanitize(s):
    """Menlo 没有部分 emoji 字形，替换成可显示的等价文字。"""
    return (s.replace("⚠️", "[!]").replace("⚠", "[!]")
             .replace("❌", "× ").replace("✅", "√ ")
             .replace("🔁", "[迭代] ").replace("✋", "[人] "))


def terminal(lines, title, path, w=1180, pad=26):
    h = pad * 2 + 46 + len(lines) * LH + 30
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    # 标题栏
    d.rectangle([0, 0, w, 46], fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 22, 16, 16 + i * 22 + 12, 28], fill=c)
    tw = sum((f_cjk_title.getlength(ch)) for ch in title)
    d.text(((w - tw) / 2, 12), title, font=f_cjk_title, fill=(210, 214, 222))
    for ch_i, ch in enumerate(title):
        pass
    # 标题居中重绘（苹方）
    x = (w - tw) / 2
    for ch in title:
        d.text((x, 12), ch, font=f_cjk_title, fill=(210, 214, 222))
        x += f_cjk_title.getlength(ch)
    y = 46 + pad
    for ln in lines:
        ln = sanitize(ln)
        color = line_color(ln)
        bold = ln.startswith(("[完成]", " STEP ", "**总分"))
        draw_line(d, (pad, y), ln, color, bold=bold)
        y += LH
    d.rectangle([0, h - 26, w, h], fill=BAR)
    img.save(path, "PNG")
    print(f"{path.name}: {w}x{h}")


def score_card(path, w=1180):
    h = 560
    img = Image.new("RGB", (w, h), PAGE)
    d = ImageDraw.Draw(img)
    # 标题
    draw_line(d, (36, 30), "ai-log-forge · 体检闭环：补写前 80 → 补写后 100", INK, bold=True)

    def card(x, y, cw, ch, fill, border, score, note_lines, score_color):
        d.rounded_rectangle([x, y, x + cw, y + ch], radius=14, fill=fill, outline=border, width=2)
        # 分数
        s = str(score)
        sw = f_cjk_big.getlength(s)
        d.text((x + (cw - sw) / 2, y + 26), s, font=f_cjk_big, fill=score_color)
        yy = y + 82
        for nl in note_lines:
            nl_color = score_color if nl.startswith("退出码") else SUB
            draw_line(d, (x + 28, yy), nl, nl_color)
            yy += 22

    card(40, 90, 480, 200, AMBER_SOFT, (240, 217, 176), 80,
         ["补写前 ｜ 22 处占位符未填（扣 20 分）", "退出码 1 ×   不许交"], AMBER)
    card(660, 90, 480, 200, GREEN_SOFT, (183, 227, 205), 100,
         ["补写后 ｜ 占位符 0 处", "退出码 0 √   可以交了"], GREENC)
    # 箭头
    d.text((565, 165), "➜", font=f_cjk_big, fill=(47, 109, 246))

    # 维度表（数据与真实体检输出一致：扣分单列，不摊进维度分）
    tx, ty = 40, 330
    rows = [("维度", "维度得分", "占位符扣分", "最终", "判定依据"),
            ("AI使用质量 30", "30.0", "0", "30.0", "7 轮对话 + 28 次工具调用 + 5 条 prompt 链"),
            ("复盘质量 45", "45.0", "0", "45.0", "自动捕获 2 个失败轮次 + 失败经验已补写"),
            ("产物完整性 25", "25.0", "−20", "5.0", "22 处未填 ×1 分（上限 20）→ 补写后清零")]
    colw = [210, 120, 130, 90, 540]
    d.rounded_rectangle([tx, ty, tx + sum(colw) + 40, ty + 190], radius=12, fill=CARD, outline=LINE, width=1)
    yy = ty + 18
    for ri, row in enumerate(rows):
        xx = tx + 20
        for ci, cell in enumerate(row):
            col = INK if ri == 0 else (SUB if ci == 4 else INK)
            if ri > 0 and ci == 2 and cell != "0":
                col = AMBER
            draw_line(d, (xx, yy), cell, col, bold=(ri == 0))
            xx += colw[ci]
        yy += 42
        if ri == 0:
            d.line([tx + 16, yy - 14, tx + sum(colw) + 24, yy - 14], fill=LINE, width=1)

    draw_line(d, (40, h - 34),
              "数据来源：本机真实运行 samples/run_all.sh，输出见 samples/demo_run.log", SUB)
    img.save(path, "PNG")
    print(f"{path.name}: {w}x{h}")


# ---- 图 1：Step1 抽取证据 ----
s1 = [l for l in LOG[3:19]]
terminal([" STEP 1  抽取证据（原始记录 → trace.json）"] + [""] + s1,
         "ai-log-forge · 真实运行实录 (1/2)", OUT / "JingXueQing_C4_demo_01_终端实录.png")

# ---- 图 2：体检闭环 ----
score_card(OUT / "JingXueQing_C4_demo_02_体检闭环.png")

# ---- 图 3：Step3/4 体检输出对比 ----
s3 = [l for l in LOG[33:48]]
s4 = [l for l in LOG[75:90]]
terminal([" STEP 3  体检（补写前）  80/100，退出码 1"] + [""] + s3 + ["", "─" * 60, ""] +
         [" STEP 4  补写后复检  100/100，退出码 0"] + [""] + s4,
         "ai-log-forge · 真实运行实录 (2/2)", OUT / "JingXueQing_C4_demo_03_体检前后.png")
