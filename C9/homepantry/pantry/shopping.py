"""购物清单：只由两件事生成——「做菜的缺料」和「常备品跌破水位」。

刻意不做「用户手动加购物清单」以外的花活，因为清单的价值在于可信：
如果清单里出现你其实还有的东西，你就会开始不信它，然后弃用。
"""
from __future__ import annotations

from . import expire, lexicon
from .model import Item
from .recipe import RecipeMatch


def from_recipes(matches: list[RecipeMatch], top: int = 3) -> list[dict]:
    """挑「差一两样就能做」的菜，把缺料合并去重。

    不做「全库菜谱缺料汇总」——那样会生成一张 40 项的清单，
    用户只会看一眼就关掉。只补当前最想做的那几道菜缺的东西。
    """
    candidates = [m for m in matches if m.missing and m.coverage >= 0.55]
    candidates.sort(key=lambda m: (-m.coverage, -m.score))
    merged: dict[str, dict] = {}
    for m in candidates[:top]:
        for miss in m.missing:
            key = miss.name
            if key in merged:
                merged[key]["qty"] = max(merged[key]["qty"], miss.need)
                if m.recipe["name"] not in merged[key]["why"]:
                    merged[key]["why"].append(m.recipe["name"])
            else:
                merged[key] = {
                    "name": miss.name,
                    "qty": miss.need,
                    "unit": miss.unit or lexicon.default_unit(miss.name),
                    "source": "recipe",
                    "why": [m.recipe["name"]],
                }
    return list(merged.values())


def from_level(items: list[Item]) -> list[dict]:
    out = []
    for a in expire.level_alerts(items):
        out.append({
            "name": a["name"],
            "qty": round(a["min"] - a["have"], 2),
            "unit": lexicon.default_unit(a["name"]),
            "source": "level",
            "why": [a["reason"]],
        })
    return out


def build(items: list[Item], matches: list[RecipeMatch]) -> list[dict]:
    """recipe 缺料优先级高于水位补货（前者有明确用途）。"""
    seen: dict[str, dict] = {}
    for row in from_recipes(matches) + from_level(items):
        if row["name"] in seen:
            seen[row["name"]]["why"] += row["why"]
            seen[row["name"]]["qty"] = max(seen[row["name"]]["qty"], row["qty"])
        else:
            seen[row["name"]] = row
    for row in seen.values():
        row["why"] = list(dict.fromkeys(row["why"]))
    order = {"recipe": 0, "level": 1}
    return sorted(seen.values(), key=lambda r: (order.get(r["source"], 9), r["name"]))
