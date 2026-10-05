#!/usr/bin/env python3
"""自检 / 准确率测量 —— 用带金标准的测试集检验评审器本身。

这是 C4A 评分表里"评审准确性 30%"与"误判率低"两项的举证材料。
没有这一步，评审器的准确率只是自我宣称。

判定档位的宽松口径（金标准三档 vs 预测三档）：
    完全一致        → 记为正确
    预测比金标准更保守（⚠️→❌ 或✅→⚠️/❌）→ 记为"保守"，单独统计
    预测比金标准更宽松（❌→✅/⚠️ 或⚠️→✅）→ 记为"误判"（危险）
    金标准是 ⚠️ 的不算对错，只看预测是否也在 ⚠️/❌ 区间

用法：
    python3 tests/run_selftest.py
    python3 tests/run_selftest.py --verbose
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from c4a import collect, completeness, quality  # noqa: E402
from c4a.rubric import CRITERIA_META                # noqa: E402

FIX = HERE / "fixtures"
# 金标准里的作者键 → fixtures 里的目录名
DIRMAP = {
    "LiMing": "LiMing_C4", "WangXiao": "WangXiao_C4", "ZhangWei": "ZhangWei_C4",
    "SunLi": "SunLi_C4", "ChenJing": "ChenJing_C4", "ZhaoLiu": "ZhaoLiu_C4",
    "ZhangLei": "TeamAlpha", "WuYang": "WuYang_C4",
}
ORDER = {"✅": 2, "⚠️": 1, "❌": 0}


def classify(pred: str, gold: str) -> str:
    """把一次预测分为 正确 / 保守 / 误判 / 待定。"""
    if gold == "⚠️":
        return "正确" if pred in ("⚠️", "❌") else "误判"
    if pred == gold:
        return "正确"
    if ORDER[pred] < ORDER[gold]:
        return "保守"      # 判得更保守：安全，但会让人白跑一趟
    return "误判"           # 判得更宽松：危险，放过了真问题


def run(verbose: bool = False) -> int:
    if not (FIX / "gold.json").exists():
        print("测试集不存在，请先运行：python3 tests/make_fixtures.py")
        return 2
    gold = json.loads((FIX / "gold.json").read_text(encoding="utf-8"))

    stats = {"正确": 0, "保守": 0, "误判": 0, "待定": 0}
    comp_stats = {"正确": 0, "保守": 0, "误判": 0}
    details: list[str] = []
    misjudged: list[str] = []

    for author, g in gold.items():
        folder = FIX / DIRMAP[author]
        if not folder.is_dir():
            details.append(f"⚠️ 缺少测试目录：{folder}")
            continue
        scan = collect.scan(folder)
        # 该目录只有一个作者，强制归到金标准作者名下
        files = [f for fs in scan.by_author.values() for f in fs]
        files = [f for f in files if f.is_c4]
        if not files:
            details.append(f"❌ {author}: 扫描到 0 个 C4 文件")
            continue

        comp = completeness.check_author(author, files)
        qual = quality.evaluate_quality(author, files)

        # ---- 完整性 ----
        got_slots = {s.key: s.status for s in comp.slots}
        for key, gstat in g["completeness"].items():
            pred = got_slots.get(key, "❌")
            kind = classify(pred, gstat)
            comp_stats[kind] = comp_stats.get(kind, 0) + 1
            if kind == "误判":
                misjudged.append(f"[完整性] {author}.{key}: 预测 {pred} / 金标准 {gstat}")
            if verbose:
                details.append(f"  完整性 {author}.{key:12s} 预测 {pred} 金标准 {gstat} → {kind}")

        # ---- 质量四条件 ----
        for key, gstat in g["quality"].items():
            cr = qual.by_key(key)
            pred = cr.grade if cr else "❌"
            kind = classify(pred, gstat)
            stats[kind] += 1
            label = CRITERIA_META[key]["label"]
            if kind == "误判":
                misjudged.append(f"[质量] {author}.{label}: 预测 {pred} / 金标准 {gstat}")
            if verbose:
                details.append(f"  质量   {author}.{label:6s} 预测 {pred} 金标准 {gstat} → {kind}")

    # ---- 汇总 ----
    n_c = sum(v for k, v in comp_stats.items() if k in ("正确", "保守", "误判"))
    n_q = sum(stats[k] for k in ("正确", "保守", "误判"))
    n_all = n_c + n_q

    print("=" * 66)
    print("C4A 评审器自检报告（金标准测试集）")
    print("=" * 66)
    print(f"测试样本：{len(gold)} 份提交（含 3 份对抗样本），"
          f"判定点 {n_all} 个（完整性 {n_c} + 质量 {n_q}）")
    print()
    print("【完整性判定】")
    for k in ("正确", "保守", "误判"):
        v = comp_stats.get(k, 0)
        pct = f"{v/n_c*100:.1f}%" if n_c else "—"
        print(f"  {k}：{v:>3} （{pct}）")
    print()
    print("【质量四条件判定】")
    for k in ("正确", "保守", "误判"):
        v = stats[k]
        pct = f"{v/n_q*100:.1f}%" if n_q else "—"
        print(f"  {k}：{v:>3} （{pct}）")
    print()
    strict_acc = (comp_stats.get("正确", 0) + stats["正确"]) / n_all if n_all else 0
    loose_acc = ((comp_stats.get("正确", 0) + comp_stats.get("保守", 0)
                  + stats["正确"] + stats["保守"]) / n_all) if n_all else 0
    print(f"严格准确率（完全一致）：{strict_acc:.1%}")
    print(f"宽松准确率（一致+保守）：{loose_acc:.1%}")
    print(f"误判率（放过真问题）：  {(comp_stats.get('误判',0)+stats['误判'])/n_all:.1%}")

    if misjudged:
        print()
        print("❌ 误判明细（必须逐条修掉）：")
        for m in misjudged:
            print(f"  - {m}")
    else:
        print()
        print("✅ 无误判：所有「危险方向的放宽」都没有发生。")

    if verbose and details:
        print()
        print("逐条明细：")
        for d in details:
            print("  " + d)

    # 误判 > 0 视为不达标
    return 0 if not misjudged else 1


def main() -> int:
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    return run(verbose)


if __name__ == "__main__":
    raise SystemExit(main())
