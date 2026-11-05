"""过期预警：把「逐条推送」改成「一条聚合」。

行业里最被低估的失败原因不是功能不够，是通知太多被静音。
所以这里只输出一句话：今天该先吃哪三样。剩下的细节留给用户点开看。
"""
from __future__ import annotations

from datetime import date

from .model import Item, sort_for_action

BUCKETS = [
    ("expired", "已过期", "该扔了，别再犹豫"),
    ("today", "今天到期", "今天就吃掉"),
    ("urgent", "3 天内", "排进这两天"),
    ("soon", "7 天内", "本周内用掉"),
]


def buckets(items: list[Item], today: date | None = None) -> dict[str, list[dict]]:
    today = today or date.today()
    out: dict[str, list[dict]] = {k: [] for k, _, _ in BUCKETS}
    for it in sort_for_action(items, today):
        st = it.status(today)
        if st in out and it.qty > 0:
            out[st].append(it.to_dict(today))
    return out


def counts(items: list[Item], today: date | None = None) -> dict[str, int]:
    return {k: len(v) for k, v in buckets(items, today).items()}


def daily_brief(items: list[Item], today: date | None = None, max_show: int = 3) -> dict:
    """一句话简报 + 可选的完整列表。"""
    today = today or date.today()
    ordered = [it for it in sort_for_action(items, today)
               if it.qty > 0 and it.status(today) in ("expired", "today", "urgent", "soon")]
    if not ordered:
        return {
            "text": "今天没有要抢的食材。冰箱状态良好。",
            "show": [],
            "total": 0,
        }

    def label(it: Item) -> str:
        dl = it.days_left(today)
        if dl is None:
            return it.name
        if dl < 0:
            return f"{it.name}（已过期 {-dl} 天）"
        if dl == 0:
            return f"{it.name}（今天到期）"
        return f"{it.name}（{dl} 天后）"

    show = [label(it) for it in ordered[:max_show]]
    head = "今天先吃：" + "、".join(show)
    if len(ordered) > max_show:
        head += f"，另外还有 {len(ordered) - max_show} 样在 7 天内到期"
    return {"text": head, "show": show, "total": len(ordered)}


def level_alerts(items: list[Item]) -> list[dict]:
    """常备品水位不足：米面油盐这类不需要记日期，但需要知道快没了。

    只对「用户真的录过」的常备品报警——否则会变成一份 12 项全红的清单，
    用户三次之后就再也不看它了。
    """
    from . import lexicon

    stock: dict[str, float] = {}
    seen: set[str] = set()
    for it in items:
        if lexicon.track(it.name) != "level":
            continue
        seen.add(it.name)
        if it.qty > 0:
            stock[it.name] = stock.get(it.name, 0.0) + it.qty

    out = []
    for name in sorted(seen):
        need = lexicon.min_stock(name)
        have = stock.get(name, 0.0)
        if have < need:
            out.append({"name": name, "have": have, "min": need,
                        "reason": f"低于常备水位（{have:g}/{need:g}）"})
    return out
