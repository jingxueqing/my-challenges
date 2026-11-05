"""核心数据结构：库存条目与保鲜状态。

设计取舍：
- 只用标准库 datetime.date，不引入第三方依赖（部署端零安装成本）。
- 「保质期」只对 track=expiry 的食材有意义；常备品（米面油盐）不算日期，
  只用 min_stock 做「水位」提醒。这是本项目和 Grocy 类方案的第一个分叉点：
  不要求全量录入，只要求录入「娇气的」。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

# 状态机：从「还早」到「过期」的顺序就是消耗优先级顺序
STATUS_ORDER = ["expired", "today", "urgent", "soon", "ok", "none"]
STATUS_LABEL = {
    "expired": "已过期",
    "today": "今天到期",
    "urgent": "3 天内",
    "soon": "7 天内",
    "ok": "还早",
    "none": "常备",
}


def parse_date(s: str | None) -> date | None:
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m-%d", "%m/%d"):
        try:
            d = datetime.strptime(s, fmt).date()
        except ValueError:
            continue
        if fmt in ("%m-%d", "%m/%d"):
            d = d.replace(year=date.today().year)
            if d < date.today() - timedelta(days=200):
                d = d.replace(year=d.year + 1)
        return d
    raise ValueError(f"无法识别的日期：{s}")


@dataclass
class Item:
    name: str
    qty: float = 1.0
    unit: str = ""
    location: str = "冷藏"
    added: date = field(default_factory=date.today)
    expires: date | None = None
    cat: str = "未知"
    note: str = ""
    source: str = "manual"
    id: int | None = None
    track: str = "expiry"

    def days_left(self, today: date | None = None) -> int | None:
        if not self.expires:
            return None
        return (self.expires - (today or date.today())).days

    def status(self, today: date | None = None) -> str:
        dl = self.days_left(today)
        if dl is None:
            return "none"
        if dl < 0:
            return "expired"
        if dl == 0:
            return "today"
        if dl <= 2:
            return "urgent"
        if dl <= 7:
            return "soon"
        return "ok"

    def rank(self, today: date | None = None) -> int:
        return STATUS_ORDER.index(self.status(today))

    def to_dict(self, today: date | None = None) -> dict:
        dl = self.days_left(today)
        return {
            "id": self.id,
            "name": self.name,
            "qty": self.qty,
            "unit": self.unit,
            "location": self.location,
            "added": self.added.isoformat(),
            "expires": self.expires.isoformat() if self.expires else None,
            "days_left": dl,
            "status": self.status(today),
            "status_label": STATUS_LABEL[self.status(today)],
            "cat": self.cat,
            "note": self.note,
            "source": self.source,
            "track": self.track,
        }

    def qty_text(self) -> str:
        q = self.qty
        qs = str(int(q)) if abs(q - round(q)) < 1e-9 else f"{q:g}"
        return f"{qs}{self.unit}"


def sort_for_action(items: list[Item], today: date | None = None) -> list[Item]:
    """按「该先吃谁」排序：过期最久 → 今天到期 → 3 天内 → 7 天内 → 还早 → 常备。"""
    return sorted(
        items,
        key=lambda it: (
            it.rank(today),
            it.days_left(today) if it.days_left(today) is not None else 10**6,
            -it.qty,
            it.name,
        ),
    )
