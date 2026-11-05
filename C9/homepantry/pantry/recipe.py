"""菜谱匹配（RAG-lite）。

不做向量检索：家庭菜谱的检索单元是「食材集合」，不是语义文本。
用「加权覆盖率 + 主料硬约束 + 临期加成」三件事就够了，而且结果可解释：
    番茄炒蛋 92 分｜有 3/3 样｜会用到：番茄（明天到期）

这才是「清冰箱」真正需要的信息：不是给我 100 道菜，是给我 3 道现在就能做的。
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

from .model import Item

DATA_DIR = Path(__file__).parent / "data"


@lru_cache(maxsize=1)
def load_recipes() -> list[dict]:
    with open(DATA_DIR / "recipes.json", encoding="utf-8") as f:
        return json.load(f)["recipes"]


@dataclass
class IngredientState:
    name: str
    need: float
    unit: str
    main: bool
    optional: bool
    have: float
    state: str  # ok / partial / expired / missing

    def to_dict(self) -> dict:
        return {
            "name": self.name, "need": self.need, "unit": self.unit,
            "main": self.main, "optional": self.optional,
            "have": self.have, "state": self.state,
        }


@dataclass
class RecipeMatch:
    recipe: dict
    coverage: float
    score: float
    ingredients: list[IngredientState] = field(default_factory=list)
    missing: list[IngredientState] = field(default_factory=list)
    uses_expiring: list[str] = field(default_factory=list)

    @property
    def cookable(self) -> bool:
        return not any(m.main and m.state in ("missing", "expired") for m in self.missing)

    def to_dict(self) -> dict:
        return {
            "id": self.recipe["id"],
            "name": self.recipe["name"],
            "time_min": self.recipe["time_min"],
            "difficulty": self.recipe["difficulty"],
            "servings": self.recipe["servings"],
            "tags": self.recipe["tags"],
            "coverage": round(self.coverage, 3),
            "score": round(self.score, 1),
            "cookable": self.cookable,
            "ingredients": [i.to_dict() for i in self.ingredients],
            "missing": [{"name": m.name, "need": m.need, "unit": m.unit,
                         "main": m.main, "state": m.state} for m in self.missing],
            "uses_expiring": self.uses_expiring,
            "steps": self.recipe["steps"],
            "tip": self.recipe.get("tip", ""),
        }


def _stock_map(inventory: list[Item]) -> tuple[dict[str, float], dict[str, float]]:
    """返回 (可用库存, 已过期库存)。"""
    fresh: dict[str, float] = {}
    expired: dict[str, float] = {}
    for it in inventory:
        if it.qty <= 0:
            continue
        st = it.status()
        target = expired if st == "expired" else fresh
        target[it.name] = target.get(it.name, 0.0) + it.qty
    return fresh, expired


def _is_staple(name: str) -> bool:
    from . import lexicon
    return lexicon.track(name) == "level"


def match(inventory: list[Item], limit: int = 5, today: date | None = None) -> list[RecipeMatch]:
    today = today or date.today()
    fresh, expired = _stock_map(inventory)
    # 临期（7 天内）的食材名，用来给菜谱加成
    expiring = {it.name for it in inventory
                if it.qty > 0 and it.status(today) in ("today", "urgent", "soon")}

    matches: list[RecipeMatch] = []
    for r in load_recipes():
        states: list[IngredientState] = []
        total_w = got_w = 0.0
        missing: list[IngredientState] = []
        uses: list[str] = []

        for ing in r["ingredients"]:
            name = ing["name"]
            need = float(ing.get("qty", 1))
            main = bool(ing.get("main"))
            optional = bool(ing.get("optional"))
            w = 0.0 if optional else (3.0 if main else 1.0)
            have = fresh.get(name, 0.0)

            if have <= 0 and expired.get(name, 0.0) > 0:
                state = "expired"
            elif have <= 0 and _is_staple(name):
                # 常备品不在库存表里，按「家里一般都有」处理，不写进缺料清单，
                # 否则清单第一屏永远是「缺盐、缺油、缺糖」，用户三秒就不信了。
                state = "assumed"
            elif have <= 0:
                state = "missing"
            elif have >= need * 0.5:
                state = "ok"
            else:
                state = "partial"

            if state == "ok":
                got = 1.0
                if name in expiring:
                    uses.append(name)
            elif state == "partial":
                got = 0.6
                if name in expiring:
                    uses.append(name)
            elif state == "assumed":
                got = 1.0  # 常备品视为有货；UI 里会标注「未记录，按常备处理」
            else:
                got = 0.0
                if not optional:
                    missing.append(IngredientState(name, need, ing.get("unit", ""), main, optional, have, state))

            total_w += w
            got_w += w * got
            states.append(IngredientState(name, need, ing.get("unit", ""), main, optional, have, state))

        coverage = got_w / total_w if total_w else 0.0
        miss_main = sum(1 for m in missing if m.main)
        miss_other = len(missing) - miss_main
        score = coverage * 100 - miss_main * 22 - miss_other * 5 + min(len(uses) * 8, 24)
        matches.append(RecipeMatch(r, coverage, max(score, 0.0), states, missing, uses))

    matches.sort(key=lambda m: (-m.score, -m.coverage, m.recipe["time_min"]))
    return matches[:limit]


def pick_for(inventory: list[Item], name: str) -> dict | None:
    for m in match(inventory, limit=len(load_recipes())):
        if m.recipe["name"] == name or m.recipe["id"] == name:
            return m.to_dict()
    return None
