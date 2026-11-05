"""演示 / 初始化数据。

刻意用「自然语言原句」而不是结构化记录来播种：
播种过程本身就把解析器跑了一遍，等于顺手做了一次端到端自检。
里面故意留了两样已过期的和一样明天到期的，用来展示预警长什么样。
"""
from __future__ import annotations

from datetime import date, timedelta

from . import nlparse
from .store import Store


def demo_lines(today: date | None = None) -> list[str]:
    today = today or date.today()
    d = lambda n: (today + timedelta(days=n)).isoformat()
    return [
        # 乳制品 / 蛋
        "2盒牛奶 冷藏 7天",
        "一盒酸奶 冷藏 5天",
        "3个鸡蛋 冷藏 20天",
        # 蔬菜
        "半颗白菜 冷藏",
        "一把青菜 冷藏",
        "三个番茄 冷藏 6天",
        "两个土豆 常温 12天",
        "两根胡萝卜 冷藏 15天",
        "一颗洋葱 常温 20天",
        "一个青椒 冷藏 5天",
        "一把韭菜 冷藏 3天",
        "5朵香菇 冷藏 4天",
        "两根玉米 冷藏 5天",
        # 肉 / 水产 / 豆制品
        "200g猪肉 冷藏 2天",
        "300g虾仁 冷冻 30天",
        "一盒豆腐 冷藏 3天",
        "200g豆干 冷藏 10天",
        "一根香肠 冷藏 15天",
        # 主食 / 冷冻
        "一袋速冻饺子 冷冻",
        "一袋面包 常温 4天",
        # 常备品（只记水位）
        "一袋面粉 放橱柜",
        "一袋大米 橱柜",
        "一瓶酱油 橱柜",
        "一袋盐 橱柜",
        "一两花椒 橱柜",
        "一袋粉条 橱柜",
        "一瓶可乐 常温",
        "4瓣大蒜 冷藏",
        "一块姜 冷藏",
        # 剩菜（最容易忘、也最该被提醒的一类）
        "一碗剩菜 冷藏 2天",
        # 故意留的过期样本
        f"一盒豆腐 冷藏 到{d(-3)}",
        f"一盒草莓 冷藏 到{d(-1)}",
        f"一袋菠菜 冷藏 到{d(1)}",
    ]


def seed(store: Store, today: date | None = None) -> int:
    n = 0
    for line in demo_lines(today):
        for p in nlparse.parse_line(line, today=today):
            store.add(p.item)
            n += 1
    return n
