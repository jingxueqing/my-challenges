"""AttnScope · 评分模块

设计原则：**不用准确率作为主指标**。

  AES   注意力效率斜率   正确率对 log2(负荷) 的回归斜率
        <- Treisman & Gelade (1980) 的 set-size 斜率
  B70   断点            正确率跌破 70% 时的负荷值（自适应，防天花板/地板）
  Lure  诱饵捕获率       错误中「选中了最相似诱饵」的比例
        —— 区分「没找到」与「被误导」，两种失败机制对应完全不同的修复手段
  d'/c  信号检测论       辨别力与判断标准分离
        <- Green & Swets (1966)；同时是防作弊的关键（堵住「全答一类」刷分）
  信度  分半信度（Spearman-Brown 校正）
"""

from __future__ import annotations

import math
from statistics import NormalDist
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

_ND = NormalDist()


def _z(p: float) -> float:
    """标准正态分位数，带边界裁剪以避免 ±inf。"""
    return _ND.inv_cdf(min(max(p, 0.01), 0.99))


# --------------------------------------------------------------------------
# 信号检测论
# --------------------------------------------------------------------------

def sdt(hits: int, misses: int, false_alarms: int, correct_rejects: int) -> Dict[str, float]:
    """由混淆矩阵计算 d′（辨别力）与 c（判断标准，负=偏向答「有」）。"""
    n_sig = hits + misses
    n_noi = false_alarms + correct_rejects
    hr = hits / n_sig if n_sig else float("nan")
    far = false_alarms / n_noi if n_noi else float("nan")
    if n_sig == 0 or n_noi == 0:
        return {"hr": hr, "far": far, "d_prime": float("nan"),
                "criterion": float("nan"), "beta": float("nan")}
    d_prime = _z(hr) - _z(far)
    criterion = -0.5 * (_z(hr) + _z(far))
    # 似然比 β（Green & Swets 定义）
    beta = math.exp(-d_prime * criterion) if abs(criterion) < 1e9 else float("nan")
    return {"hr": hr, "far": far, "d_prime": d_prime,
            "criterion": criterion, "beta": beta}


# --------------------------------------------------------------------------
# AES 效率斜率 与 B70 断点
# --------------------------------------------------------------------------

def _linregress(xs: Sequence[float], ys: Sequence[float]) -> Tuple[float, float]:
    """最小二乘：返回 (slope, intercept)。样本不足时返回 nan。"""
    n = len(xs)
    if n < 2:
        return float("nan"), float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return float("nan"), my
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    return slope, my - slope * mx


def aes_slope(loads: Sequence[int], acc_by_load: Sequence[float]) -> float:
    """AES：正确率对 log2(负荷) 的回归斜率。

    斜率≈0   -> 类似 pop-out / 并行加工，几乎不受干扰负荷影响
    斜率显著为负 -> 资源受限的序列加工（人类 conjunction 搜索的典型表现）
    """
    xs = [math.log2(max(n, 1)) for n in loads]
    slope, _ = _linregress(xs, list(acc_by_load))
    return slope


def breakpoint_b70(loads: Sequence[int], acc_by_load: Sequence[float],
                   threshold: float = 0.70) -> float:
    """B70：正确率跌破 threshold 时的负荷值（在 log2 刻度上线性插值）。

    若始终未跌破 -> 返回最大负荷（说明该被试/模型在此阶梯上未崩溃）；
    若起点即低于阈值 -> 返回最小负荷。
    """
    pairs = sorted(zip(loads, acc_by_load))
    if not pairs:
        return float("nan")
    if pairs[0][1] < threshold:
        return float(pairs[0][0])
    for (n0, a0), (n1, a1) in zip(pairs, pairs[1:]):
        if a1 < threshold <= a0:
            if a0 == a1:
                return float(n1)
            t = (a0 - threshold) / (a0 - a1)
            return float(n0) * ((float(n1) / float(n0)) ** t)
    return float(pairs[-1][0])


# --------------------------------------------------------------------------
# 诱饵捕获率
# --------------------------------------------------------------------------

def lure_capture_rate(n_lure_errors: int, n_errors: int) -> float:
    """错误作答中「选中了最相似诱饵」的比例。

    高值 = 被显著干扰物捕获（选择性注意失败）
    低值 = 漫无目的地找不到（更接近容量/检索问题）
    """
    return (n_lure_errors / n_errors) if n_errors else float("nan")


# --------------------------------------------------------------------------
# 信度
# --------------------------------------------------------------------------

def split_half_reliability(odd_acc: Sequence[float],
                           even_acc: Sequence[float]) -> float:
    """分半信度：奇偶两半在各条件上的正确率相关，再做 Spearman-Brown 校正。"""
    n = min(len(odd_acc), len(even_acc))
    if n < 3:
        return float("nan")
    xs, ys = list(odd_acc[:n]), list(even_acc[:n])
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if dx == 0 or dy == 0:
        return float("nan")
    r = num / (dx * dy)
    return (2 * r) / (1 + r) if (1 + r) != 0 else float("nan")


# --------------------------------------------------------------------------
# L1 结果聚合
# --------------------------------------------------------------------------

def _extract_id(text: str) -> str:
    """从模型输出中抽取形如 AB-1234 的编号。"""
    import re
    m = re.search(r"\b[A-Z]{2}-\d{4}\b", text or "")
    return m.group(0) if m else ""


def score_l1(results: Iterable[dict]) -> Dict[str, dict]:
    """按 (condition, similarity) 分组汇总 L1 结果。

    results 中每个元素需含：condition, similarity, load_n, correct,
                           chose_lure(bool), response
    """
    buckets: Dict[Tuple[str, float], List[dict]] = {}
    for r in results:
        buckets.setdefault((r["condition"], round(float(r["similarity"]), 2)), []).append(r)

    out: Dict[str, dict] = {}
    for (cond, sim), rows in sorted(buckets.items()):
        by_load: Dict[int, List[dict]] = {}
        for r in rows:
            by_load.setdefault(int(r["load_n"]), []).append(r)
        loads = sorted(by_load)
        accs = [sum(1 for r in by_load[n] if r["correct"]) / len(by_load[n]) for n in loads]

        errs = [r for r in rows if not r["correct"]]
        n_lure_err = sum(1 for r in errs if r.get("chose_lure"))

        # 分半信度：按题目顺序奇偶拆分后逐负荷算正确率
        odd, even = [], []
        for n in loads:
            rs = by_load[n]
            o = rs[0::2]
            e = rs[1::2]
            if o:
                odd.append(sum(1 for r in o if r["correct"]) / len(o))
            if e:
                even.append(sum(1 for r in e if r["correct"]) / len(e))

        out[f"{cond}|sim={sim}"] = {
            "n_items": len(rows),
            "loads": loads,
            "accuracy_by_load": [round(a, 4) for a in accs],
            "overall_accuracy": round(sum(1 for r in rows if r["correct"]) / len(rows), 4),
            "AES_slope": round(aes_slope(loads, accs), 4),
            "B70": round(breakpoint_b70(loads, accs), 2),
            "lure_capture_rate": round(lure_capture_rate(n_lure_err, len(errs)), 4),
            "split_half_reliability": round(split_half_reliability(odd, even), 4),
        }
    return out


def evaluate_l1_response(item, response: str) -> dict:
    """判定单条 L1 作答。"""
    pred = _extract_id(response)
    correct = (pred == item.gold_id)
    chose_lure = (not correct) and bool(item.lure_id) and (pred == item.lure_id)
    return {"condition": item.condition, "similarity": item.similarity,
            "load_n": item.load_n, "correct": correct,
            "chose_lure": chose_lure, "response": response}


# --------------------------------------------------------------------------
# L2 / L3 聚合
# --------------------------------------------------------------------------

def score_l2(results: Iterable[dict], n_bins: int = 10) -> dict:
    """按十分位分箱输出 vigilance 剖面（对标 Liu et al. 2023 的 U 型曲线）。"""
    rows = list(results)
    if not rows:
        return {}
    rows.sort(key=lambda r: r["serial_index"])
    bins: List[List[dict]] = [[] for _ in range(n_bins)]
    for r in rows:
        idx = min(int(r["serial_index"] * n_bins / max(len(rows), 1)), n_bins - 1)
        bins[idx].append(r)

    profile = []
    for i, b in enumerate(bins):
        if not b:
            profile.append({"bin": i + 1, "d_prime": None, "hr": None, "far": None})
            continue
        h = sum(1 for r in b if r["is_signal"] and r["correct"])
        m = sum(1 for r in b if r["is_signal"] and not r["correct"])
        f = sum(1 for r in b if (not r["is_signal"]) and (not r["correct"]))
        c = sum(1 for r in b if (not r["is_signal"]) and r["correct"])
        s = sdt(h, m, f, c)
        profile.append({"bin": i + 1,
                        "d_prime": (round(s["d_prime"], 4) if s["d_prime"] == s["d_prime"] else None),
                        "hr": round(s["hr"], 4) if s["hr"] == s["hr"] else None,
                        "far": round(s["far"], 4) if s["far"] == s["far"] else None})

    valid = [p["d_prime"] for p in profile if p["d_prime"] is not None]
    decrement = (valid[-1] - valid[0]) if len(valid) >= 2 else None

    h = sum(1 for r in rows if r["is_signal"] and r["correct"])
    m = sum(1 for r in rows if r["is_signal"] and not r["correct"])
    f = sum(1 for r in rows if (not r["is_signal"]) and (not r["correct"]))
    c = sum(1 for r in rows if (not r["is_signal"]) and r["correct"])
    overall = sdt(h, m, f, c)

    return {"n_trials": len(rows), "profile": profile,
            "vigilance_decrement": round(decrement, 4) if decrement is not None else None,
            "overall": {k: (round(v, 4) if v == v else None) for k, v in overall.items()}}


def score_l3(results: Iterable[dict]) -> dict:
    """按 salience × doc_len 输出 d′/c，并报告 ΔS cascade 错误率。"""
    rows = list(results)
    buckets: Dict[Tuple[str, str], List[dict]] = {}
    for r in rows:
        buckets.setdefault((r["salience"], r["doc_len"]), []).append(r)

    out = {}
    for (sal, dl), b in sorted(buckets.items()):
        h = sum(1 for r in b if r["has_change"] and r["changed_correct"])
        m = sum(1 for r in b if r["has_change"] and not r["changed_correct"])
        f = sum(1 for r in b if (not r["has_change"]) and (not r["changed_correct"]))
        c = sum(1 for r in b if (not r["has_change"]) and r["changed_correct"])
        s = sdt(h, m, f, c)
        loc_acc = None
        sig = [r for r in b if r["has_change"]]
        if sig:
            loc_acc = sum(1 for r in sig if r.get("line_correct")) / len(sig)
        cascade_err = sum(1 for r in b if not r.get("cascade_correct", False)) / len(b)
        out[f"{sal}|{dl}"] = {
            "n_items": len(b),
            "d_prime": round(s["d_prime"], 4) if s["d_prime"] == s["d_prime"] else None,
            "criterion": round(s["criterion"], 4) if s["criterion"] == s["criterion"] else None,
            "hit_rate": round(s["hr"], 4) if s["hr"] == s["hr"] else None,
            "false_alarm_rate": round(s["far"], 4) if s["far"] == s["far"] else None,
            "localization_accuracy": round(loc_acc, 4) if loc_acc is not None else None,
            "delta_S_cascade_error_rate": round(cascade_err, 4),
        }
    return out
