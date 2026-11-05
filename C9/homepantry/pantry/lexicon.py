"""食材词典：别名、拼音、特征标签、默认保质期。

为什么要有「特征标签」：真实场景里人忘记的往往不是"有没有"，而是"叫什么"。
我妈说「那一袋白色的粉」，我需要能反查到面粉/淀粉/糖/盐。标签就是为这一句话准备的。
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

LOCATIONS = ["冷藏", "冷冻", "常温", "橱柜", "阳台"]


@lru_cache(maxsize=1)
def raw() -> dict:
    with open(DATA_DIR / "lexicon.json", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def entries() -> list[dict]:
    return raw()["items"]


@lru_cache(maxsize=1)
def by_name() -> dict[str, dict]:
    return {e["name"]: e for e in entries()}


@lru_cache(maxsize=1)
def alias_index() -> dict[str, str]:
    """别名 / 规范名 → 规范名。"""
    idx: dict[str, str] = {}
    for e in entries():
        idx[e["name"]] = e["name"]
        for a in e.get("aliases") or []:
            idx.setdefault(a, e["name"])
    return idx


@lru_cache(maxsize=1)
def longest_first_terms() -> list[str]:
    """按长度降序排列的所有可匹配词，保证「五花肉」优先于「猪肉」这类重叠。"""
    return sorted(alias_index().keys(), key=len, reverse=True)


def resolve(term: str) -> str | None:
    """把任意说法归一到规范名，支持在长句里做最长前缀扫描。

    返回规范名或 None。
    """
    term = term.strip()
    if not term:
        return None
    if term in alias_index():
        return alias_index()[term]
    best: tuple[int, str] | None = None
    for name in longest_first_terms():
        if term.startswith(name) and (best is None or len(name) > best[0]):
            best = (len(name), alias_index()[name])
    if best and best[0] >= 2:
        return best[1]
    return None


def match_prefix(text: str) -> tuple[str, str] | None:
    """在文本开头找词典词（允许前面有空格/标点），返回 (规范名, 命中的原词)。"""
    s = text.strip()
    if not s:
        return None
    for name in longest_first_terms():
        if s.startswith(name):
            return alias_index()[name], name
    return None


def find_longest(text: str) -> tuple[str, int, int] | None:
    """在文本中找最靠前、最长的词典词，返回 (规范名, start, end)。"""
    best: tuple[int, int, str] | None = None
    for name in longest_first_terms():
        pos = text.find(name)
        if pos < 0:
            continue
        cand = (pos, -len(name), alias_index()[name])
        if best is None or cand < best:
            best = cand
    if best is None:
        return None
    pos, neg_len, canon = best
    return canon, pos, pos - neg_len


def meta(name: str) -> dict:
    return by_name().get(name, {})


def pinyin(name: str) -> str:
    return meta(name).get("pinyin", "")


def initials(name: str) -> str:
    return meta(name).get("ini", "")


def tags(name: str) -> list[str]:
    return meta(name).get("tags", [])


def cat(name: str) -> str:
    return meta(name).get("cat", "未知")


def track(name: str) -> str:
    return meta(name).get("track", "expiry")


def min_stock(name: str) -> float:
    return float(meta(name).get("min_stock", 1))


def shelf_days(name: str, location: str = "冷藏") -> int | None:
    shelf = meta(name).get("shelf") or {}
    if location in shelf:
        return shelf[location]
    if "常温" in shelf:  # 阳台/橱柜这类位置按常温估
        return shelf["常温"]
    if shelf:
        return shelf[sorted(shelf, key=lambda k: shelf[k])[-1]]
    return None


def default_unit(name: str) -> str:
    t = tags(name)
    if "液体" in t or "瓶装" in t:
        return "瓶"
    if "袋装" in t:
        return "袋"
    if "盒装" in t:
        return "盒"
    return "个"


def all_names() -> list[str]:
    return [e["name"] for e in entries()]


def location_alias() -> dict[str, str]:
    return raw().get("location_alias", {})


def normalize_location(word: str) -> str | None:
    if word in LOCATIONS:
        return word
    return location_alias().get(word)
