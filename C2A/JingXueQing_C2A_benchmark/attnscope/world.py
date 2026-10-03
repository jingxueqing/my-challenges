"""AttnScope · 合成世界生成器 (Synthetic World Generator)

程序化生成一个虚构的「仓库巡检日志」世界。所有实体名、编号、数值均为随机
组合，因此任何一道题目的正确答案都不可能出现在预训练语料中（防污染，
借鉴 ARC 的程序化生成原则与 CogBench 的 data-leakage 最小化做法）。

字段设计对应 Treisman & Gelade (1980) 的 feature / conjunction 搜索：
  - feature 条件：目标在**单一字段**上独一无二  -> 人类应表现出 pop-out（斜率≈0）
  - conjunction 条件：目标只在**字段组合**上唯一，而干扰项各自满足其中一个条件
    -> 需要逐个做特征绑定，效率随 set size 下降（Duncan & Humphreys, 1989）
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field, asdict
from typing import List, Optional

CATEGORIES = ["阀门", "泵机", "传感器", "管线", "继电箱", "传送带", "储罐", "过滤器"]
STATUSES = ["OK", "WARN", "CRIT", "HOLD"]
LOCATIONS = ["A区", "B区", "C区", "D区", "E区", "F区"]
FIELDS = ["id", "category", "value", "status", "ts", "location"]


def _rand_id(rng: random.Random) -> str:
    """形如 KX-4821 的实体编号。"""
    letters = "".join(rng.choice(string.ascii_uppercase) for _ in range(2))
    digits = "".join(rng.choice(string.digits) for _ in range(4))
    return f"{letters}-{digits}"


@dataclass
class Record:
    id: str
    category: str
    value: int
    status: str
    ts: str          # 形如 14:07 的时间戳
    location: str

    def render(self) -> str:
        return (
            f"[{self.id}] 类别={self.category} 读数={self.value} "
            f"状态={self.status} 时间={self.ts} 库位={self.location}"
        )


@dataclass
class L1Item:
    """L1 选择性阶梯的一道题目。"""

    ladder: str = "L1"
    condition: str = "conjunction"   # "feature" | "conjunction"
    load_n: int = 8                  # 干扰负荷（条目总数）
    similarity: float = 0.5          # 目标-干扰相似度（诱饵占比）
    prompt: str = ""
    gold_id: str = ""
    lure_id: str = ""                # 最相似的诱饵（用于 Lure Capture 指标）
    records: List[Record] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["records"] = [asdict(r) for r in self.records]
        return d


def _make_record(rng: random.Random,
                 category: Optional[str] = None,
                 status: Optional[str] = None) -> Record:
    return Record(
        id=_rand_id(rng),
        category=category if category is not None else rng.choice(CATEGORIES),
        value=rng.randint(100, 999),
        status=status if status is not None else rng.choice(STATUSES),
        ts=f"{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}",
        location=rng.choice(LOCATIONS),
    )


def _ensure_unique(records: List[Record], used: set) -> None:
    """保证实体编号互不相同（否则题目会有歧义）。"""
    rng = random.Random(len(used))
    for r in records:
        while r.id in used:
            r.id = _rand_id(rng)
        used.add(r.id)


def generate_l1_item(rng: random.Random,
                     load_n: int = 8,
                     similarity: float = 0.5,
                     condition: str = "conjunction") -> L1Item:
    """生成 L1 的一道题目。

    Args:
        load_n: 干扰负荷，即日志中的条目总数 N ∈ {4,8,16,32,64}。
        similarity: 0.2~0.9，干扰项中「满足目标条件之一」的诱饵占比。
                    越高 => 目标-干扰越相似 => 搜索效率越低。
        condition: "feature"（目标在单字段上唯一）或 "conjunction"（组合唯一）。
    """
    if load_n < 2:
        raise ValueError("load_n 至少为 2")
    if condition not in ("feature", "conjunction"):
        raise ValueError("condition 必须是 'feature' 或 'conjunction'")

    tgt_cat = rng.choice(CATEGORIES)
    tgt_status = rng.choice(STATUSES)

    # 1) 目标记录
    target = _make_record(rng, category=tgt_cat, status=tgt_status)

    # 2) 诱饵：满足目标条件的「一半」——这正是 conjunction 搜索里最难排除的项
    n_lures = max(1, int(round((load_n - 1) * similarity)))
    n_plain = (load_n - 1) - n_lures

    lures: List[Record] = []
    for i in range(n_lures):
        if condition == "conjunction":
            # 一半满足类别、一半满足状态，但绝不同时满足
            if i % 2 == 0:
                r = _make_record(rng, category=tgt_cat,
                                 status=rng.choice([s for s in STATUSES if s != tgt_status]))
            else:
                r = _make_record(rng,
                                 category=rng.choice([c for c in CATEGORIES if c != tgt_cat]),
                                 status=tgt_status)
        else:
            # feature 条件：诱饵在其它字段上与目标接近，但关键字段不同
            r = _make_record(rng,
                             category=rng.choice([c for c in CATEGORIES if c != tgt_cat]),
                             status=rng.choice([s for s in STATUSES if s != tgt_status]))
        lures.append(r)

    # 3) 普通干扰项：与目标条件无关
    plains = [
        _make_record(rng,
                     category=rng.choice([c for c in CATEGORIES if c != tgt_cat]),
                     status=rng.choice([s for s in STATUSES if s != tgt_status]))
        for _ in range(n_plain)
    ]

    records = [target] + lures + plains
    rng.shuffle(records)
    _ensure_unique(records, used=set())

    if condition == "conjunction":
        rule = f"类别={tgt_cat} 且 状态={tgt_status}"
    else:
        rule = f"状态={tgt_status}"

    body = "\n".join(r.render() for r in records)
    prompt = (
        "以下是某仓库的巡检日志。\n\n"
        f"{body}\n\n"
        f"请找出唯一满足【{rule}】的记录，只输出它的编号（形如 AB-1234），不要解释。\n"
        "编号："
    )

    # 最相似诱饵 = 与目标共享字段最多的干扰项（此处等价于第一个诱饵）
    lure_id = lures[0].id if lures else ""

    return L1Item(
        ladder="L1",
        condition=condition,
        load_n=load_n,
        similarity=similarity,
        prompt=prompt,
        gold_id=target.id,
        lure_id=lure_id,
        records=records,
    )
