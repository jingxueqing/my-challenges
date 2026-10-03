"""AttnScope · 三条阶梯的题目装配

L1 选择性阶梯（过滤）  <- Treisman & Gelade (1980) / Duncan & Humphreys (1989)
L2 持续性阶梯（维持）  <- Mackworth (1948) vigilance；对标 Liu et al. (2023) 的 U 型位置曲线
L3 变化觉察阶梯（更新）<- Rensink et al. (1997) / Simons & Levin (1997) change blindness

本文件负责把 world.py 生成的原子材料装配成可投递的题目（prompt + gold），
并保证 100% 可解性（生成时同步产出答案）。
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from .world import (CATEGORIES, STATUSES, LOCATIONS, Record, _make_record,
                    _rand_id, generate_l1_item, L1Item)

# --------------------------------------------------------------------------
# L2 · 持续性阶梯
# --------------------------------------------------------------------------


@dataclass
class L2Item:
    ladder: str = "L2"
    serial_index: int = 0      # 在 200 个 trial 序列中的序号（用于十分位分箱）
    is_signal: bool = False    # 该 trial 是否真的包含目标事件
    prompt: str = ""
    gold: str = ""             # "有" / "无"
    records: List[Record] = field(default_factory=list)

    def to_dict(self) -> dict:
        d = {"ladder": self.ladder, "serial_index": self.serial_index,
             "is_signal": self.is_signal, "prompt": self.prompt, "gold": self.gold}
        d["records"] = [r.__dict__ for r in self.records]
        return d


def generate_l2_sequence(rng: random.Random,
                         n_trials: int = 400,
                         signal_rate: float = 0.25,
                         n_bins: int = 10) -> List[L2Item]:
    """生成一段 vigilance 序列。目标事件以 signal_rate 的概率稀疏出现。

    人类经典结果（Mackworth, 1948）：命中率随时间下降、误报率上升；
    LLM 侧对标 Liu et al. (2023) 的 U 型位置曲线（首因/近因强、中间弱）。

    **分层布点（重要）：** 若用纯伯努利抽样放置信号，在 10% 信号率下会有多个
    十分位箱内信号数为 0，导致该箱的 d′ 不可估计。因此改为「每个箱内随机放置
    等量信号」——箱内位置仍然随机（保留稀疏、不可预测的主观体验），但保证每一
    个分箱都同时含有信号 trial 与噪声 trial，d′ 可估。实际信号率会略有偏差，
    以返回序列的实际统计为准。
    """
    per_bin = max(1, round(n_trials * signal_rate / n_bins))
    signal_positions = set()
    for b in range(n_bins):
        lo = b * n_trials // n_bins
        hi = (b + 1) * n_trials // n_bins
        slots = list(range(lo, hi))
        rng.shuffle(slots)
        signal_positions.update(slots[:per_bin])

    items: List[L2Item] = []
    for i in range(n_trials):
        is_signal = i in signal_positions
        batch: List[Record] = []
        # 每个 trial 呈现 5 条记录；信号 trial 中恰好 1 条为 CRIT
        for _ in range(5):
            batch.append(_make_record(rng,
                                      status="CRIT" if (is_signal and len(batch) == 0) else
                                      rng.choice([s for s in STATUSES if s != "CRIT"])))
        # 若无信号，重置第一条为非 CRIT
        if not is_signal:
            batch[0] = _make_record(
                rng, status=rng.choice([s for s in STATUSES if s != "CRIT"]))
        rng.shuffle(batch)

        body = "\n".join(r.render() for r in batch)
        prompt = (
            f"第 {i + 1} 批巡检记录：\n\n{body}\n\n"
            "其中是否存在状态为 CRIT 的记录？只回答「有」或「无」。\n"
            "回答："
        )
        items.append(L2Item(serial_index=i, is_signal=is_signal,
                            prompt=prompt, gold="有" if is_signal else "无",
                            records=batch))
    return items


# --------------------------------------------------------------------------
# L3 · 变化觉察阶梯
# --------------------------------------------------------------------------


@dataclass
class L3Item:
    ladder: str = "L3"
    has_change: bool = False
    salience: str = "high"     # high | mid | low（变更显著性）
    doc_len: str = "1k"        # 1k | 2k | 4k（文档长度档位）
    prompt: str = ""
    gold_changed: str = ""     # "有变化" / "无变化"
    gold_line: Optional[int] = None
    lines_v1: List[str] = field(default_factory=list)
    lines_v2: List[str] = field(default_factory=list)
    # ΔS Cascade：变更后执行题（答案依赖 D' 而非 D）
    cascade_prompt: str = ""
    cascade_gold: str = ""

    def to_dict(self) -> dict:
        return {"ladder": self.ladder, "has_change": self.has_change,
                "salience": self.salience, "doc_len": self.doc_len,
                "prompt": self.prompt, "gold_changed": self.gold_changed,
                "gold_line": self.gold_line, "cascade_prompt": self.cascade_prompt,
                "cascade_gold": self.cascade_gold}


_LEN_TO_LINES = {"1k": 12, "2k": 24, "4k": 48}


def _make_config_lines(rng: random.Random, n: int) -> List[str]:
    out = []
    for i in range(n):
        cat = rng.choice(CATEGORIES)
        loc = rng.choice(LOCATIONS)
        val = rng.randint(100, 999)
        out.append(f"{i + 1:02d}. {loc}/{cat} 阈值={val} 单位=kPa")
    return out


def generate_l3_item(rng: random.Random,
                     salience: str = "high",
                     doc_len: str = "1k",
                     has_change: Optional[bool] = None) -> L3Item:
    """生成一道 change-detection 题目。

    salience:
      high = 数值大幅改变（翻倍量级）
      mid  = 数值小幅改变（±10%）
      low  = 仅单位或标点微调（change blindness 的经典触发条件）
    """
    if doc_len not in _LEN_TO_LINES:
        raise ValueError("doc_len 必须是 1k / 2k / 4k")
    if salience not in ("high", "mid", "low"):
        raise ValueError("salience 必须是 high / mid / low")
    if has_change is None:
        has_change = rng.random() < 0.5

    n = _LEN_TO_LINES[doc_len]
    v1 = _make_config_lines(rng, n)
    v2 = list(v1)

    line_no: Optional[int] = None
    if has_change:
        line_no = rng.randrange(n)
        raw = v1[line_no]
        val = int(raw.split("阈值=")[1].split(" ")[0])
        if salience == "high":
            new_val = val * 2
        elif salience == "mid":
            new_val = int(val * 1.1)
        else:
            new_val = val
        if salience == "low":
            # 仅把单位从 kPa 换成 MPa；数值不变
            v2[line_no] = raw.replace("单位=kPa", "单位=MPa")
        else:
            v2[line_no] = raw.replace(f"阈值={val}", f"阈值={new_val}")

    d1 = "\n".join(v1)
    d2 = "\n".join(v2)
    prompt = (
        "【配置清单 · 版本 A】\n" + d1 + "\n\n"
        "【配置清单 · 版本 B】\n" + d2 + "\n\n"
        "版本 B 相对版本 A 是否发生了变化？\n"
        "请严格按以下两行输出：\n"
        "变化：有变化|无变化\n"
        "行号：整数（无变化则填 0）"
    )

    # ΔS Cascade：以「变更后」的情境为准执行一道任务。
    # 若模型未察觉变更，它会基于过期的 S 作答 -> 系统性错误，可量化放大效应。
    if has_change and line_no is not None:
        cascade_prompt = (
            "请**仅依据版本 B**，回答：第 "
            f"{line_no + 1:02d} 行的阈值与单位是什么？\n"
            "格式：阈值=<数字> 单位=<kPa|MPa>"
        )
        target_line = v2[line_no]
        val_b = target_line.split("阈值=")[1].split(" ")[0]
        unit_b = target_line.split("单位=")[1]
        cascade_gold = f"阈值={val_b} 单位={unit_b}"
    else:
        idx = rng.randrange(n)
        cascade_prompt = (
            "请**仅依据版本 B**，回答：第 "
            f"{idx + 1:02d} 行的阈值与单位是什么？\n"
            "格式：阈值=<数字> 单位=<kPa|MPa>"
        )
        target_line = v2[idx]
        val_b = target_line.split("阈值=")[1].split(" ")[0]
        unit_b = target_line.split("单位=")[1]
        cascade_gold = f"阈值={val_b} 单位={unit_b}"

    return L3Item(
        ladder="L3", has_change=has_change, salience=salience, doc_len=doc_len,
        prompt=prompt,
        gold_changed="有变化" if has_change else "无变化",
        gold_line=(line_no + 1) if line_no is not None else 0,
        lines_v1=v1, lines_v2=v2,
        cascade_prompt=cascade_prompt, cascade_gold=cascade_gold,
    )


# --------------------------------------------------------------------------
# 统一入口
# --------------------------------------------------------------------------

def build_l1_suite(seed: int = 20261003,
                   loads: List[int] = None,
                   similarities: List[float] = None,
                   conditions: List[str] = None,
                   items_per_cell: int = 20) -> List[L1Item]:
    """构建 L1 的完整题目集：condition × similarity × load 的网格。"""
    loads = loads or [4, 8, 16, 32, 64]
    similarities = similarities or [0.2, 0.5, 0.9]
    conditions = conditions or ["feature", "conjunction"]
    rng = random.Random(seed)
    out: List[L1Item] = []
    for cond in conditions:
        for sim in similarities:
            for n in loads:
                for _ in range(items_per_cell):
                    out.append(generate_l1_item(rng, load_n=n, similarity=sim,
                                                condition=cond))
    return out
