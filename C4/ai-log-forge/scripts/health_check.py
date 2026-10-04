#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
health_check.py — 给你的《AI 日志 / AAR》做一次交卷前体检

对照评分标准（references/rubric_profile.yaml）逐维度打分，并做三件人容易漏的事：
  1. 红旗检测：比如「一句话指令直接提交」「没有 AI 使用记录」——这些会直接把分数锁死在 5 分。
  2. 硬证据检测：如果给了 trace.json，就用真实数字判（轮次≥3？有失败轮次？动手改过吗？）。
  3. 占位符检测：还有多少 `<!-- LLM-FILL -->` 没填。没填 = 空话 = 扣分。

用法：
  python3 health_check.py --files ZhangSan_C4_AI日志.md ZhangSan_C4_AAR.md --trace trace.json
  python3 health_check.py --files *.md --profile ../references/rubric_profile.yaml --out 体检报告.md

只依赖 Python 3 标准库（内置迷你 YAML 解析器，没装 PyYAML 也能跑）。
"""

import argparse
import json
import re
import sys
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"<!--\s*LLM-FILL:\s*(.*?)\s*-->", re.S)


# --------------------------------------------------------------------------
# 迷你 YAML 解析（够用就好：缩进块 + 行内列表 + 注释）
# --------------------------------------------------------------------------
def parse_scalar(v):
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [x.strip().strip("\"'") for x in inner.split(",") if x.strip()]
    if v.lower() in ("true", "false"):
        return v.lower() == "true"
    try:
        return int(v)
    except ValueError:
        return v


def mini_yaml(text):
    lines = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        lines.append((len(raw) - len(raw.lstrip(" ")), raw.strip()))

    def block(i, indent):
        if lines[i][1].startswith("- "):
            items = []
            while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("- "):
                items.append(parse_scalar(lines[i][1][2:]))
                i += 1
            return items, i
        node = {}
        while i < len(lines) and lines[i][0] == indent:
            key, _, val = lines[i][1].partition(":")
            key, val = key.strip().strip("\"'"), val.strip()
            i += 1
            if val == "":
                if i < len(lines) and lines[i][0] > indent:
                    node[key], i = block(i, lines[i][0])
                else:
                    node[key] = None
            else:
                node[key] = parse_scalar(val)
        return node, i

    if not lines:
        return {}
    node, _ = block(0, lines[0][0])
    return node


def load_profile(path):
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        return yaml.safe_load(text)
    except ImportError:
        return mini_yaml(text)


# --------------------------------------------------------------------------
# 打分
# --------------------------------------------------------------------------
def read_docs(paths):
    buf = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"[警告] 文件不存在，跳过：{p}", file=sys.stderr)
            continue
        buf.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n\n".join(buf)


def trace_evidence(trace_path):
    """从 trace.json 里取硬证据（比关键词可靠）。"""
    if not trace_path:
        return {}
    try:
        t = json.loads(Path(trace_path).read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[警告] trace.json 读取失败：{e}", file=sys.stderr)
        return {}
    s = t.get("stats", {})
    return {
        "rounds": s.get("rounds", 0),
        "tool_calls": s.get("tool_calls", 0),
        "failed_rounds": len(s.get("failed_rounds", []) or []),
        "refine_rounds": len(s.get("refine_rounds", []) or []),
        "prompt_evo": len(t.get("prompt_evolution", []) or []),
    }


def score(docs, profile, ev):
    kw = profile.get("signal_keywords", {}) or {}
    rows = []
    total = 0.0
    max_total = 0.0
    for dim_id, dim in (profile.get("dimensions", {}) or {}).items():
        maxp = float(dim.get("maxPoints", 0) or 0)
        signals = dim.get("signals", []) or []
        hits, misses = [], []
        for sig in signals:
            words = kw.get(sig, []) or [sig]
            ok = False
            for w in words:
                if str(w).lower() in docs.lower():
                    ok = True
                    break
            # 硬证据优先：有真实数字就算命中
            if not ok:
                ok = hard_evidence(sig, ev)
            (hits if ok else misses).append(sig)
        ratio = (len(hits) / len(signals)) if signals else 0
        got = round(maxp * ratio, 1)
        total += got
        max_total += maxp
        rows.append({
            "id": dim_id, "label": dim.get("label", dim_id), "max": maxp,
            "got": got, "hits": hits, "misses": misses, "ratio": ratio,
        })

    # 红旗
    flags = []
    rf = profile.get("red_flags", []) or []
    rf_items = rf.values() if isinstance(rf, dict) else rf  # 兼容「映射」与「列表」两种写法
    for f in rf_items:
        if not isinstance(f, dict):
            continue
        absent = [w for w in (f.get("absent", []) or []) if str(w).lower() not in docs.lower()]
        present = [w for w in (f.get("present", []) or []) if str(w).lower() in docs.lower()]
        cap = f.get("maxScore")
        triggered = False
        if f.get("absent") and len(absent) == len(f["absent"]):
            triggered = True
        if present:
            triggered = True
        if triggered:
            flags.append({"label": f.get("label", f.get("id", "")), "cap": cap,
                          "dim": f.get("affectedDimension", ""),
                          "missing": absent, "found": present})

    # 占位符：没填 = 空话 = 扣分（每处 1 分，上限 20）
    placeholders = [m.group(1) for m in PLACEHOLDER_RE.finditer(docs)]
    penalty = min(20, len(placeholders))
    total = max(0.0, total - penalty)
    return rows, total, max_total, flags, placeholders, penalty


def hard_evidence(sig, ev):
    """用 trace.json 的真实数字判定某些 signal（没有 trace 时全部返回 False）。"""
    if not ev:
        return False
    rules = {
        "多轮迭代": ev.get("rounds", 0) >= 3 or ev.get("refine_rounds", 0) >= 1,
        "prompt优化": ev.get("prompt_evo", 0) >= 1,
        "记录迭代过程": ev.get("refine_rounds", 0) >= 1,
        "含失败经验": ev.get("failed_rounds", 0) >= 1,
        "AI日志佐证": ev.get("tool_calls", 0) > 0 or ev.get("rounds", 0) > 0,
        "可执行": ev.get("tool_calls", 0) > 0,
    }
    return rules.get(sig, False)


def render(rows, total, max_total, flags, placeholders, ev, profile, penalty=0):
    pct = round(total / max_total * 100) if max_total else 0
    out = []
    out.append("# AI 日志 / AAR 体检报告\n")
    out.append(f"**总分：{round(total,1)} / {round(max_total,1)}（{pct}%）**"
               + (f"　_（含未填占位符扣分 −{penalty}）_" if penalty else "") + "\n")
    if ev:
        out.append(f"> 硬证据：{ev.get('rounds',0)} 轮对话 ｜ {ev.get('tool_calls',0)} 次工具调用 ｜ "
                   f"{ev.get('failed_rounds',0)} 个失败轮次 ｜ {ev.get('prompt_evo',0)} 条 prompt 优化链\n")

    out.append("\n## 逐维度得分\n")
    out.append("| 维度 | 得分 | 命中信号 | 缺失信号 |\n|---|---|---|---|")
    for r in rows:
        out.append(f"| {r['label']} | {r['got']}/{r['max']} | {'、'.join(r['hits']) or '—'} | "
                   f"{'、'.join(r['misses']) or '—'} |")

    if flags:
        out.append("\n## 🚩 红旗警告（会把该维度锁死在低分）\n")
        for f in flags:
            cap = f"→ 该维度最高只能拿 **{f['cap']} 分**" if f.get("cap") else ""
            out.append(f"- **{f['label']}** {cap}")
            if f["missing"]:
                out.append(f"  - 全文找不到这些词：{'、'.join(f['missing'])}")
            if f["found"]:
                out.append(f"  - 命中了危险信号：{'、'.join(f['found'])}")

    if placeholders:
        out.append(f"\n## ⚠️ 还有 {len(placeholders)} 处占位符没填\n")
        out.append("没填的占位符 = 空话 = 直接扣分。逐一补上：\n")
        for h in placeholders[:12]:
            out.append(f"- [ ] {h}")
        if len(placeholders) > 12:
            out.append(f"- …… 还有 {len(placeholders)-12} 处")

    out.append("\n## 改进建议（按性价比排序）\n")
    weak = sorted(rows, key=lambda r: (r["ratio"], -r["max"]))[:4]
    n = 1
    for r in weak:
        if r["ratio"] >= 1.0:
            continue
        gain = round(r["max"] - r["got"], 1)
        out.append(f"{n}. **补「{r['label']}」(+{gain} 分可拿)**：缺 "
                   f"{'、'.join(r['misses']) or '—'}。"
                   f"{'其中「含失败经验」最划算——写 1 条真实踩坑就能拿。' if '含失败经验' in r['misses'] else ''}")
        n += 1
    if flags:
        out.append(f"{n}. **先拆红旗**：红旗不解决，写得再好也封顶。")
    out.append("\n---\n_报告由 ai-log-forge / health_check.py 生成。改完重跑一次，看分数有没有涨。_")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="AI 日志 / AAR 交卷前体检打分")
    ap.add_argument("--files", "-f", nargs="+", required=True, help="要体检的 md 文件")
    ap.add_argument("--trace", "-t", help="trace.json（可选，提供硬证据）")
    ap.add_argument("--profile", "-p", default=None, help="评分标准 yaml")
    ap.add_argument("--out", "-o", default=None, help="报告输出路径（默认打印到屏幕）")
    ap.add_argument("--json", action="store_true", help="额外输出机读 JSON")
    args = ap.parse_args()

    here = Path(__file__).resolve().parent
    profile_path = args.profile or (here.parent / "references" / "rubric_profile.yaml")
    if not Path(profile_path).exists():
        print(f"[错误] 找不到评分标准：{profile_path}", file=sys.stderr)
        sys.exit(2)
    profile = load_profile(profile_path)

    docs = read_docs(args.files)
    if not docs.strip():
        print("[错误] 没有可读内容。", file=sys.stderr)
        sys.exit(3)

    ev = trace_evidence(args.trace)
    rows, total, max_total, flags, placeholders, penalty = score(docs, profile, ev)
    report = render(rows, total, max_total, flags, placeholders, ev, profile, penalty)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"[完成] 体检报告 -> {args.out}")
    print(report)

    if args.json:
        print("\n```json")
        print(json.dumps({"total": total, "max": max_total, "placeholder_penalty": penalty,
                          "dimensions": [{k: r[k] for k in ("id", "label", "got", "max")} for r in rows],
                          "flags": [f["label"] for f in flags],
                          "placeholders": len(placeholders)}, ensure_ascii=False, indent=2))
        print("```")

    # 退出码：有红旗或占位符 → 非零，方便做成提交前的 CI 关卡
    sys.exit(1 if (flags or placeholders) else 0)


if __name__ == "__main__":
    main()
