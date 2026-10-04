#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
forge.py — 把 trace.json 锻造成可提交的《AI 日志》和《AAR 复盘》

分工原则（这是本技能的核心设计）：
  · 脚本负责「事实」——轮次、时间、工具、失败点、prompt 改动，全部来自真实记录，不编造。
  · LLM 负责「叙事」——那些需要判断的部分（我为什么这么决策、学到了什么）由模型补写，
    脚本用 `<!-- LLM-FILL: 提示 -->` 标记占位，绝不替用户瞎编反思。

用法：
  python3 forge.py --trace trace.json --name JingXueQing --challenge C4 \
                   --title "ai-log-forge 技能开发" --out-dir .
  python3 forge.py --interview --name JingXueQing --challenge C4 --out-dir .   # 没有记录时的访谈模式

输出：
  <姓名>_<挑战号>_AI日志.md
  <姓名>_<挑战号>_AAR.md
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

PLACEHOLDER = "<!-- LLM-FILL: {hint} -->"


def preview(text, n=100):
    t = " ".join((text or "").split())
    return (t[:n] + "…") if len(t) > n else t


def load_trace(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# --------------------------------------------------------------------------
# 《AI 日志》
# --------------------------------------------------------------------------
def build_log(trace, name, challenge, title):
    s = trace["stats"]
    rounds = trace["rounds"]
    evo = trace["prompt_evolution"]
    src_files = "、".join(f"`{Path(x['file']).name}`" for x in trace["sources"][:5])
    tool_rows = "\n".join(
        f"| {k} | {v} |" for k, v in list(s["tool_by_name"].items())[:10]
    ) or "| （无结构化工具事件） | 0 |"

    # 轮次时间线（表格只放事实，判断部分单独列在下方，避免表格出现空行）
    tl_rows = []
    for r in rounds:
        flags = []
        if r["refine"]:
            flags.append("🔁迭代")
        if r["failed"]:
            flags.append("❌失败")
        if r["human_work"]:
            flags.append("✋我动手")
        tl_rows.append(
            f"| {r['index']} | {r.get('ts') or '—'} | {preview(r['user_text'], 80) or '—'} "
            f"| {preview(r['assistant_preview'], 80) or '—'} | {r['tool_calls']} "
            f"| {' '.join(flags) or '正常'} |"
        )
    timeline = "\n".join(tl_rows)
    tl_notes = "\n".join(
        f"- **第 {r['index']} 轮**：{PLACEHOLDER.format(hint='这一轮我做了什么判断 / 手动改了什么（没有就写“交给 AI，我只验收”）')}"
        for r in rounds
    )

    # prompt 优化轨迹
    if evo:
        evo_rows = "\n".join(
            f"| #{e['from_round']} → #{e['to_round']} | {e['before']} | {e['after']} "
            f"| {('、'.join(e['new_tokens']) or '—')} | {e.get('kind', '迭代')} |" for e in evo[:12]
        )
        evo_block = (
            "| 轮次跨度 | 改之前的说法 | 改之后的说法 | 新增关键词 | 判定 |\n"
            "|---|---|---|---|---|\n" + evo_rows
        )
    else:
        evo_block = "_（记录中未检测到相邻的渐进式改写，可能是一次成型，或记录不完整）_"

    # 失败与返工
    fail_rounds = [r for r in rounds if r["failed"]]
    if fail_rounds:
        fail_block = "\n".join(
            f"- **第 {r['index']} 轮**：{preview(r['errors'][0] if r['errors'] else (r['assistant_preview'] or r['user_text']), 160)}\n"
            f"  - 触发方式：{'工具/输出报错' if r['errors'] else '输出不符合预期'}\n"
            f"  - {PLACEHOLDER.format(hint='第' + str(r['index']) + '轮：我是怎么定位并修掉的')}"
            for r in fail_rounds[:10]
        )
    else:
        fail_block = "_（记录中未捕获到失败事件。如果你的真实过程里踩过坑，请在这里手动补上——没有失败经验的复盘会被判为“敷衍了事”）_"

    return f"""# {name}_{challenge}_AI日志

> **任务**：{title}
> **生成方式**：`ai-log-forge` 从真实协作记录自动抽取证据 → 叙事部分由 AI 补写并经本人核对
> **证据源**：{src_files}
> **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 0. 一页速览

| 指标 | 数值 | 说明 |
|---|---|---|
| 总轮次 | {s['rounds']} | 我发起的指令轮数（≥3 轮才算有迭代） |
| 我的输入字数 | {s['user_chars_total']} | 平均每条指令 {s['avg_user_prompt_chars']} 字 |
| AI 输出字数 | {s['assistant_chars_total']} | |
| 工具调用次数 | {s['tool_calls']} | AI 实际动手的次数 |
| 迭代信号轮次 | {s['refine_rounds'] or '无'} | 出现“重做/改成/不对”等修正指令的轮次 |
| 失败/返工轮次 | {s['failed_rounds'] or '无'} | 报错或输出不达标的轮次 |
| prompt 优化链 | {len(evo)} 条 | 同一目标被反复改写 prompt 的证据 |

---

## 1. 我用了什么 AI、怎么指挥的

**AI 工具**：{PLACEHOLDER.format(hint='例如 Claude Code / ChatGPT / Cursor，版本号')}
**我的指挥方式**：{PLACEHOLDER.format(hint='一句话概括你的用法：是“一句话丢过去”，还是“拆步骤+给约束+验收”？')}

### 分工表

| 谁 | 干了什么 |
|---|---|
| 我（人） | {PLACEHOLDER.format(hint='判断、决策、验收、手动修改的部分，越具体越好')} |
| AI | 见下方工具分布 —— {s['tool_calls']} 次工具调用，产出 {s['assistant_chars_total']} 字 |

**AI 工具调用分布**（自动统计）

| 工具 | 次数 |
|---|---|
{tool_rows}

---

## 2. 迭代全时间线（{s['rounds']} 轮）

| 轮次 | 时间 | 我的指令 | AI 产出 | 工具调用 | 状态 |
|---|---|---|---|---|---|
{timeline}

**逐轮判断（这部分必须自己写，AI 替不了）**

{tl_notes}

---

## 3. Prompt 优化轨迹

{evo_block}

{PLACEHOLDER.format(hint='用 2-3 句话说明：prompt 是怎么一步步变好的？哪次改写带来了质变？')}

---

## 4. 失败与返工（评分最看重的一节）

{fail_block}

---

## 5. 我做了什么（AI 没做的部分）

{PLACEHOLDER.format(hint='列 3-5 条：你的判断、取舍、手动改动、验收标准。这是“AI 使用质量”得分的关键')}

---

## 6. 产物与验证

| 产物 | 怎么验证它是对的 |
|---|---|
{PLACEHOLDER.format(hint='逐条列出交付物 + 验证方式（命令/操作/结果）')}

---

## 7. 复现信息

```bash
# 任何人都能用这条命令从同一份原始记录复现本日志
python3 extract_trace.py --input <原始记录> --out trace.json --markdown
python3 forge.py --trace trace.json --name {name} --challenge {challenge} --title "{title}"
```
"""


# --------------------------------------------------------------------------
# 《AAR 复盘》
# --------------------------------------------------------------------------
def build_aar(trace, name, challenge, title):
    s = trace["stats"]
    rounds = trace["rounds"]
    fail_rounds = [r for r in rounds if r["failed"]]
    fail_evidence = "\n".join(
        f"- 第 {r['index']} 轮：{preview(r['assistant_preview'] or r['user_text'], 150)}"
        for r in fail_rounds[:8]
    ) or "- 记录中未捕获失败事件（建议手动补充，否则本节为空）"

    return f"""# {name}_{challenge}_AAR

> AAR = After Action Review。对照「目标 / 实际 / 差距 / 改进」四问复盘，失败经验必须写。

## 1. 原定目标

{PLACEHOLDER.format(hint='最初想达成什么？量化标准是什么')}

## 2. 实际结果

- 轮次：{s['rounds']} ｜ 工具调用：{s['tool_calls']} ｜ 迭代轮次：{len(s['refine_rounds'])}
- 失败/返工：{len(fail_rounds)} 轮
{PLACEHOLDER.format(hint='最终交付了什么？和目标的差距在哪')}

## 3. 差距分析

| 维度 | 目标 | 实际 | 差距原因 |
|---|---|---|---|
{PLACEHOLDER.format(hint='至少 3 行，写真实原因，不要写“时间不够”这种废话')}

## 4. 失败经验（本节不能空）

**自动捕获的失败证据：**

{fail_evidence}

**我的复盘：**
{PLACEHOLDER.format(hint='每个失败点：为什么会错？我当时误判了什么？下次怎么提前发现')}

## 5. 做对了什么（可复用）

{PLACEHOLDER.format(hint='哪些做法值得下次照抄？越具体越可迁移')}

## 6. 改进方案（带优先级）

| 优先级 | 改什么 | 怎么改 | 什么时候做 |
|---|---|---|---|
{PLACEHOLDER.format(hint='P0/P1/P2 各至少一条')}

## 7. 下一步

{PLACEHOLDER.format(hint='接下来 24 小时 / 一周分别做什么')}
"""


# --------------------------------------------------------------------------
# 访谈模式（没有原始记录时）
# --------------------------------------------------------------------------
INTERVIEW = """# AI 日志访谈提纲（无记录模式）

> 没有原始记录也能写日志——按顺序回答下面 8 个问题，再让我生成《AI 日志》+《AAR》。
> 每个问题 1-3 句话即可，**第 5、6 题必须写失败经验**，否则会被判为「敷衍了事」。

1. **任务是什么？** 你想让 AI 帮你做成什么事？
2. **用了什么 AI 工具？**（Claude Code / ChatGPT / Cursor / 其他）+ 大概几轮对话？
3. **第一轮你怎么说的？** 把原始指令贴出来（越原始越好）。
4. **中间改过几次指令？** 每次改成什么？为什么改？
5. **哪里失败了？** 报错、返工、AI 理解错的地方 —— 至少写 1 条。
6. **你是怎么修的？** 自己改的，还是重新指挥 AI？
7. **你亲手做了哪些 AI 做不了的事？**（判断 / 决策 / 验收 / 手动编辑）
8. **最终产物是什么？** 你怎么确认它是对的？

---
回答完直接说「按访谈生成日志」，我会套用同一套模板输出 `姓名_挑战_AI日志.md` 和 `姓名_挑战_AAR.md`。
"""


def main():
    ap = argparse.ArgumentParser(description="把 trace.json 锻造成 AI 日志 + AAR 复盘")
    ap.add_argument("--trace", "-t", help="extract_trace.py 产出的 trace.json")
    ap.add_argument("--name", "-n", default="YourName", help="姓名 / 昵称（用于文件命名）")
    ap.add_argument("--challenge", "-c", default="C0", help="挑战号或项目代号")
    ap.add_argument("--title", default="（未命名任务）", help="一句话任务标题")
    ap.add_argument("--out-dir", "-o", default=".", help="输出目录")
    ap.add_argument("--mode", choices=["log", "aar", "both"], default="both")
    ap.add_argument("--interview", action="store_true", help="无原始记录时，输出访谈提纲")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.interview or not args.trace:
        p = out_dir / f"{args.name}_{args.challenge}_访谈提纲.md"
        p.write_text(INTERVIEW, encoding="utf-8")
        print(f"[完成] 无记录模式，访谈提纲 -> {p}")
        print("       回答后把答案给我，我会生成完整日志+AAR。")
        return

    trace = load_trace(args.trace)
    written = []

    if args.mode in ("log", "both"):
        p = out_dir / f"{args.name}_{args.challenge}_AI日志.md"
        p.write_text(build_log(trace, args.name, args.challenge, args.title), encoding="utf-8")
        written.append(p)

    if args.mode in ("aar", "both"):
        p = out_dir / f"{args.name}_{args.challenge}_AAR.md"
        p.write_text(build_aar(trace, args.name, args.challenge, args.title), encoding="utf-8")
        written.append(p)

    print(f"[完成] 已生成 {len(written)} 个文件：")
    for p in written:
        print(f"       - {p}  ({p.stat().st_size} 字节)")
    print(f"       共 {trace['stats']['rounds']} 轮 ｜ "
          f"{len(trace['stats']['failed_rounds'])} 个失败轮次 ｜ "
          f"{len(trace['prompt_evolution'])} 条 prompt 优化链")
    print("[注意] 文件里带 `<!-- LLM-FILL: ... -->` 标记的地方需要补写（可让我代写后你核对）。")


if __name__ == "__main__":
    main()
