#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C7 封面图生成器（本地 Pillow 渲染，零外部依赖调用）

用法:
    python make_cover.py            # 生成全部封面
输出:
    ../02_发布稿/封面_A1.png  (900x383, 公众号头条 2.35:1)
    ../02_发布稿/封面_A2.png
    ../02_发布稿/封面_A1_square.png (383x383, 公众号次条/分享缩略)
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "02_发布稿")
os.makedirs(OUT, exist_ok=True)

FONT_PATH = "/System/Library/Fonts/PingFang.ttc"
BG = (247, 245, 242)
INK = (26, 26, 26)
SUB = (110, 108, 104)
ACCENT = (198, 74, 58)      # 朱红，单色点缀
RULE = (214, 210, 204)


def load(size, weight="semibold"):
    """从 PingFang.ttc 里挑 SC 字重，找不到就退回 index 0。"""
    want = {"bold": ["PingFang SC Semibold", "PingFang SC Bold"],
            "semibold": ["PingFang SC Semibold", "PingFang SC Medium"],
            "regular": ["PingFang SC Regular", "PingFang SC" ]}[weight]
    for idx in range(0, 24):
        try:
            f = ImageFont.truetype(FONT_PATH, size, index=idx)
        except Exception:
            break
        name = f.getname()[0] + " " + f.getname()[1]
        for w in want:
            if name.startswith(w):
                return f
    return ImageFont.truetype(FONT_PATH, size, index=0)


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=font) <= max_w:
            cur += ch
        else:
            lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines


def cover(path, title, kicker, tag, w=900, h=383, square=False):
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)

    # 左下角色块作为锚点（不放装饰性噪点，保持干净）
    d.rectangle([0, h - 8, w, h], fill=ACCENT)
    d.rectangle([0, 0, 6, h], fill=ACCENT)

    pad = 56
    inner_w = w - pad * 2 - 40

    f_kick = load(22 if not square else 20, "regular")
    f_title = load(56 if not square else 40, "bold")
    f_tag = load(20 if not square else 18, "regular")

    y = pad - 6
    d.text((pad, y), kicker, font=f_kick, fill=SUB)
    y += 40

    lines = wrap(d, title, f_title, inner_w)
    if square:
        lines = lines[:3]
    else:
        lines = lines[:2]
    for ln in lines:
        d.text((pad, y), ln, font=f_title, fill=INK)
        y += int(f_title.size * 1.42)

    # 分隔细线 + 标签
    y += 6
    d.line([pad, y, pad + 56, y], fill=ACCENT, width=3)
    y += 14
    d.text((pad, y), tag, font=f_tag, fill=SUB)

    img.save(path, "PNG", optimize=True)
    print("saved", os.path.relpath(path, HERE), f"{w}x{h}")


if __name__ == "__main__":
    cover(
        os.path.join(OUT, "封面_A1.png"),
        "我做完 16 个交付物，只有 3 个被别人看见过",
        "C7 · 内容传播 / 第一篇",
        "个人影响力 · 复盘 · 附自查清单",
    )
    cover(
        os.path.join(OUT, "封面_A2.png"),
        "我把公众号写作拆成 7 步，AI 只负责 3 步",
        "C7 · 内容传播 / 第二篇",
        "提示词全文可复制 · 一套能直接用的流程",
    )
    cover(
        os.path.join(OUT, "封面_A1_square.png"),
        "我做完 16 个交付物，只有 3 个被看见",
        "C7 内容传播",
        "复盘",
        w=383, h=383, square=True,
    )
    cover(
        os.path.join(OUT, "封面_A2_square.png"),
        "公众号写作拆成 7 步，AI 只干 3 步",
        "C7 内容传播",
        "提示词",
        w=383, h=383, square=True,
    )
