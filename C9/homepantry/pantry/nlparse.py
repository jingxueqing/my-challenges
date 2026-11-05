"""中文口语入库解析器（本项目最核心的一段代码）。

目标：让「入库」这件事的成本低到能长期坚持。
    输入 `2盒牛奶 冷藏 7天` / `半颗白菜` / `一袋面粉 放橱柜` / `昨天的排骨汤 剩菜`
    输出 结构化 Item 列表 + 每一条的解析依据（reasons）+ 需要人工确认的项。

为什么自己写规则而不调大模型：
1) 入库是高频动作，一次 1-2 秒的网络往返会直接杀死使用习惯；
2) 家庭食材的说法高度收敛（就那 200 个词、那 6 个量词、那 3 个位置），
   规则足够，且 100% 可解释、可离线、零成本；
3) 解析失败要能告诉用户"我是怎么理解错的"，规则版的 reasons 天然满足这一点。
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date, timedelta

from . import lexicon
from .model import Item, parse_date

UNITS = [
    "千克", "公斤", "毫升", "斤", "两", "克", "升", "个", "只", "袋", "盒", "瓶", "包",
    "根", "颗", "把", "块", "片", "条", "枚", "碗", "杯", "罐", "桶", "朵", "瓣", "打",
    "提", "串", "张", "份", "支", "管", "团", "扎", "箱", "kg", "g", "ml", "L",
]
UNIT_CANON = {
    "公斤": "千克", "千克": "千克", "kg": "千克",
    "g": "克", "克": "克",
    "ml": "毫升", "毫升": "毫升",
    "L": "升", "升": "升", "斤": "斤", "两": "两",
}

CN_DIGIT = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9}

# 结算词/口语填充词：解析前清掉，避免干扰名称识别
FILLERS = [
    "买了", "买回", "刚从", "刚买", "还有", "剩下", "剩了", "剩", "有", "放了", "放在",
    "放", "在", "冰箱里", "里面", "里", "一点", "一些", "大概", "左右", "的", "了",
    "保质期", "到期", "过期", "要", "快", "吃完", "弄", "做了", "用", "到",
]

EXPIRY_KEYWORDS = [
    (re.compile(r"今天(到期|吃完|过期)?|今天就"), 0, "今天到期"),
    (re.compile(r"明天(到期|吃完|过期)?"), 1, "明天到期"),
    (re.compile(r"后天(到期|吃完)?"), 2, "后天到期"),
    (re.compile(r"尽快|这两天|这周吃完|这周内|抓紧"), 2, "尽快吃完"),
    (re.compile(r"下周(吃完)?"), 7, "下周吃完"),
]

DATE_RE = re.compile(r"(?:(?P<y>20\d{2})[-/.年])?(?P<m>\d{1,2})[-/.月](?P<d>\d{1,2})(?:日|号)?")
DAYS_RE = re.compile(r"(?P<n>\d+(?:\.\d+)?|[一二两三四五六七八九十半]+)\s*(?P<unit>个?月|周|星期|天|日)")
_UNITS_RE = "|".join(sorted(UNITS, key=len, reverse=True))
# 关键：量词优先版本。`一两花椒` 必须解析成「1 两花椒」而不是「12 颗花椒」，
# 靠的是"必须有量词"才成立，正则回溯会把 两 让给量词位。
QTY_RE_U = re.compile(
    r"(?<![\d.])(?P<n>\d+(?:\.\d+)?|[一二两三四五六七八九十半]+)\s*(?P<u>" + _UNITS_RE + r")"
)
QTY_RE_N = re.compile(r"(?<![\d.])(?P<n>\d+(?:\.\d+)?|[一二两三四五六七八九十半]+)")
QTY_RE = QTY_RE_U


def cn_to_num(s: str) -> float | None:
    """一 / 十一 / 二十三 / 两 / 半 → 数字。"""
    if not s:
        return None
    if s == "半":
        return 0.5
    if re.fullmatch(r"\d+(?:\.\d+)?", s):
        return float(s)
    if "十" in s:
        left, _, right = s.partition("十")
        tens = CN_DIGIT.get(left, 1) if left else 1
        ones = CN_DIGIT.get(right, 0) if right else 0
        return float(tens * 10 + ones)
    total = 0.0
    for ch in s:
        if ch not in CN_DIGIT:
            return None
        total = total * 10 + CN_DIGIT[ch]
    return total


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("：", " ").replace(":", " ")
    return text.strip()


@dataclass
class Parsed:
    item: Item
    confidence: float
    reasons: list[str] = field(default_factory=list)
    needs_review: bool = False
    raw: str = ""

    def to_dict(self) -> dict:
        d = self.item.to_dict()
        d.update({
            "confidence": round(self.confidence, 2),
            "reasons": self.reasons,
            "needs_review": self.needs_review,
            "raw": self.raw,
        })
        return d


def _split_segments(text: str) -> list[str]:
    """切分多品类输入。

    '和' 的危险在于它也是名词的一部分（和牛、和尚）。规则：
    只有当「和」后面紧跟数字/数量词，或者紧跟一个词典里的食材时，才当分隔符。
    """
    parts: list[str] = []
    for chunk in re.split(r"[、，,;；\n]+", text):
        for piece in re.split(r"以及|加上|还有", chunk):
            buf = ""
            i = 0
            while i < len(piece):
                ch = piece[i]
                if ch == "和" and i > 0:
                    tail = piece[i + 1:].strip()
                    starts_new = bool(re.match(r"^[\d一二两三四五六七八九十半]", tail)) or \
                        lexicon.match_prefix(tail) is not None
                    if starts_new:
                        parts.append(buf)
                        buf = ""
                        i += 1
                        continue
                buf += ch
                i += 1
            parts.append(buf)
    return [p.strip() for p in parts if p and p.strip()]


def _extract_location(seg: str) -> tuple[str | None, str, str]:
    """先长后短匹配位置词，返回 (位置, 剩余文本, 依据)。"""
    locs = sorted(list(lexicon.LOCATIONS) + list(lexicon.location_alias().keys()),
                  key=len, reverse=True)
    for w in locs:
        if w in seg:
            return lexicon.normalize_location(w) or w, seg.replace(w, " ", 1), f"位置：{w}→{lexicon.normalize_location(w) or w}"
    return None, seg, ""


def _extract_expiry(seg: str, today: date) -> tuple[date | None, int | None, str, str]:
    """返回 (到期日, 剩余天数, 剩余文本, 依据)。"""
    m = DATE_RE.search(seg)
    if m:
        mo, dy = int(m.group("m")), int(m.group("d"))
        if 1 <= mo <= 12 and 1 <= dy <= 31:
            year = int(m.group("y")) if m.group("y") else today.year
            try:
                d = date(year, mo, dy)
            except ValueError:
                d = None
            if d:
                if not m.group("y") and d < today - timedelta(days=200):
                    d = date(year + 1, mo, dy)
                return d, None, seg[: m.start()] + " " + seg[m.end():], f"日期：{mo}/{dy}"

    m = DAYS_RE.search(seg)
    if m:
        n = cn_to_num(m.group("n"))
        if n is not None:
            unit = m.group("unit")
            mult = 30 if unit.startswith("个") or unit == "月" else (7 if unit in ("周", "星期") else 1)
            days = int(round(n * mult))
            return today + timedelta(days=days), days, seg[: m.start()] + " " + seg[m.end():], f"保质期：{days} 天"

    for rx, days, label in EXPIRY_KEYWORDS:
        m = rx.search(seg)
        if m:
            return today + timedelta(days=days), days, seg[: m.start()] + " " + seg[m.end():], f"时限：{label}"

    return None, None, seg, ""


def _extract_qty(seg: str) -> tuple[float, str, str, str]:
    m = QTY_RE_U.search(seg)
    if not m:
        m = QTY_RE_N.search(seg)
    if not m:
        return 1.0, "", seg, ""
    n = cn_to_num(m.group("n"))
    if n is None:
        return 1.0, "", seg, ""
    unit = (m.groupdict().get("u") or "")
    unit = UNIT_CANON.get(unit, unit)
    rest = seg[: m.start()] + " " + seg[m.end():]
    return n, unit, rest, f"数量：{n:g}{unit}"


def _clean_name(rest: str) -> str:
    for w in FILLERS:
        rest = rest.replace(w, " ")
    rest = re.sub(r"[（）()【】\[\]《》<>\"'“”‘’]", " ", rest)
    rest = re.sub(r"\s+", " ", rest).strip(" -_/.")
    return rest


def _strip_punct(s: str) -> str:
    s = re.sub(r"[（）()【】\[\]《》<>\"'“”‘’、，,。.;；]", " ", s)
    return re.sub(r"\s+", " ", s).strip(" -_/.")


def default_location(name: str) -> str:
    shelf = lexicon.meta(name).get("shelf") or {}
    if "冷冻" in shelf and len(shelf) == 1:
        return "冷冻"
    if "常温" in shelf and "冷藏" not in shelf:
        return "常温"
    if lexicon.cat(name) in ("主食", "干货", "调味") and "常温" in shelf:
        return "常温"
    return "冷藏"


def parse_line(text: str, today: date | None = None, default_loc: str | None = None) -> list[Parsed]:
    """解析一行自然语言，返回若干条 Parsed。"""
    today = today or date.today()
    text = norm(text)
    if not text:
        return []

    # 行级位置：出现在行尾且不属于某一段的位置词（"… 冷藏" / "… 都放冷冻"）
    line_loc, text, _ = _extract_location(text)

    out: list[Parsed] = []
    for seg in _split_segments(text):
        raw = seg
        seg_loc, seg, loc_reason = _extract_location(seg)
        exp, days, seg, exp_reason = _extract_expiry(seg, today)
        qty, unit, seg, qty_reason = _extract_qty(seg)

        # 名称：先在不删口语词的原串上匹配（否则「剩菜」会被 FILLERS 的「剩」毁掉），
        # 匹配不到再删口语词重试。
        hit = lexicon.match_prefix(_strip_punct(seg)) or lexicon.match_prefix(_clean_name(seg))

        reasons: list[str] = []
        conf = 0.5
        review = False

        if hit:
            name, term = hit
            reasons.append(f"词典命中：{term}→{name}")
            conf = 0.88
        else:
            cand = _clean_name(seg)
            m = re.search(r"[\u4e00-\u9fa5A-Za-z]{1,12}", cand or "")
            name = m.group(0) if m else (cand or "未命名")
            reasons.append(f"未收录词：按原文「{name}」记录，建议补进词典")
            review = True
            conf = 0.45

        trk = lexicon.track(name)
        loc = seg_loc or line_loc or default_loc or default_location(name)
        if not seg_loc and trk == "level" and loc in ("冷藏", "冷冻"):
            # 常备品跟着「冷藏」走没意义：面粉放冷藏是错的，按品类纠正；
            # 但用户明说「橱柜」就要听用户的。
            loc = default_loc or default_location(name)
        if seg_loc:
            reasons.append(loc_reason)
        elif line_loc:
            reasons.append(f"位置：继承行级「{line_loc}」")
        else:
            reasons.append(f"位置：默认「{loc}」（按品类推断，可改）")

        if unit:
            reasons.append(qty_reason)
            conf += 0.07
        else:
            if lexicon.cat(name) in ("调味", "干货", "主食"):
                unit = "袋"
            elif lexicon.tags(name) and "液体" in lexicon.tags(name):
                unit = "瓶"
            else:
                unit = "个"
            reasons.append(f"数量：默认 1{unit}（没说数量）")

        if trk == "level":
            # 常备品：不设到期日，只记水位（反全量录入的关键设计）
            exp = None
            reasons.append("常备品：只记水位，不设保质期，低于阈值才提醒")
        elif exp is None:
            sd = lexicon.shelf_days(name, loc)
            if sd:
                exp = today + timedelta(days=sd)
                reasons.append(f"保质期：按「{name}×{loc}」常识取 {sd} 天")
                conf -= 0.04
            else:
                reasons.append("保质期：未知，不设提醒")
                review = True
        else:
            reasons.append(exp_reason)
            conf += 0.05

        item = Item(
            name=name, qty=qty, unit=unit, location=loc,
            added=today, expires=exp, cat=lexicon.cat(name),
            source="nl", track=trk,
        )
        out.append(Parsed(item=item, confidence=min(conf, 1.0), reasons=reasons,
                          needs_review=review, raw=raw))
    return out


def parse_strict_date(s: str) -> date:
    return parse_date(s)
