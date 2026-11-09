#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ask_checker —— 群内提问质量自检器

设计原则（三条，写死了）：
1. 打分必须可解释：每个维度不仅给分，还要回引原文片段（hits）。没有命中的片段就是缺失项。
2. 只做减法不做加法：默认 0 分，命中一条加一条。宁可低估，也不虚构"看起来很专业"的分。
3. 不联网、不调用大模型：纯规则。因为"提问质量"这件事我要能复现，不能靠抽卡。

四个维度（各 25 分，合计 100）：
  上下文 context   —— 别人要知道你在什么环境、做什么事、走到哪一步
  已尝试 attempted —— 别人要知道你已经排除了什么，不然会重复建议
  卡点   blocker   —— 别人要知道具体是"什么现象对不上什么预期"
  证据   evidence  —— 别人要能自己看到日志/命令/报错，而不是听你转述

用法：
  python3 ask_checker.py samples/good_01_C4D_ollama_cpu.txt
  python3 ask_checker.py -                 # 从 stdin 读
  python3 ask_checker.py q.txt --min 85 --json
退出码：0 = 达到 --min（默认 70）；1 = 未达到；2 = 输入错误
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple

VERSION = "1.0"

# ---------------------------------------------------------------------------
# 维度定义：每个维度 3 个子检查，各 1/3 权重。
# required_hint 用于缺项时给"补什么"的具体指引，不给空话。
# ---------------------------------------------------------------------------

DIMENSIONS = [
    {
        "id": "context",
        "name": "上下文",
        "max": 25,
        "checks": [
            {
                "id": "env",
                "label": "环境",
                "patterns": [
                    r"macOS|mac os|Windows|Linux|Ubuntu|M1|M2|M3|M4|Intel",
                    r"\d+\s*GB|\d+\s*G内存|内存|显存|VRAM",
                    r"Python\s*\d|Node\s*\d|Python3|pip|npm|npx",
                    r"ollama|Ollama|llama|Gemma|Qwen|Transformer|Chrome|Safari|Edge",
                    r"v?\d+\.\d+(\.\d+)?",  # 版本号
                ],
                "hint": "补一句你的环境（机器/系统/语言版本/关键软件版本）",
            },
            {
                "id": "task",
                "label": "在做什么",
                "patterns": [
                    r"C\d[A-Z]?(?![\d])",            # 挑战编号 C4D / C6A
                    r"SKILL\.md|skill|技能|技能包",
                    r"仓库|repo|项目|脚本|看板|小程序|网页|应用|Agent|agent",
                    r"我正在|我在做|我的目标|想实现|要求是|需要实现",
                ],
                "hint": "补一句你在做什么（哪个挑战/哪个文件/要达到什么效果）",
            },
            {
                "id": "stage",
                "label": "走到哪一步",
                "patterns": [
                    r"第\s*[Nn\d一二三四五六七八九十]+\s*(轮|次|步)|阶段",
                    r"已经(装|拉|跑|写完|改完|到)|刚(装|拉|跑|改)",
                    r"放到|迁移到|移植到|从.{0,8}(换成|改到|迁到)",
                    r"之前(能|正常|可以)|原来(能|正常)|昨天|昨晚|今天|刚才|刚刚",
                ],
                "hint": "补一句进度（做到哪一步了/之前是否正常）",
            },
        ],
    },
    {
        "id": "attempted",
        "name": "已尝试",
        "max": 25,
        "checks": [
            {
                "id": "tried",
                "label": "试过什么",
                "patterns": [
                    r"试过|尝试过|我试|已经试|跑过|执行过|写过|改过|换过|装过|重装",
                    r"换(了|成|到|个)|重跑|改成|去掉|删了|关掉|跑通",
                    r"按.{0,12}(文档|教程|示例|README)|照.{0,8}(文档|教程)写的|照.{0,8}(做|来)",
                    r"也(试|改|换|查)过|我(没|不)?敢",
                ],
                "hint": "补一句你试过什么（哪怕失败也要写，别人才不会重复建议）",
            },
            {
                "id": "excluded",
                "label": "排除了什么",
                "patterns": [
                    r"排除|不是.{0,10}问题|应该不是|已确认不是|可以确认",
                    r"说明.{0,12}(不是|没问题|正常)|证明|核对|对比了|验证了",
                    r"但是|然而|可是|结果还是|仍然|依然",
                ],
                "hint": "补一句你已经排除了什么（这一步最能帮别人省时间）",
            },
            {
                "id": "command",
                "label": "可复现的命令",
                "patterns": [
                    r"`[^`\n]{3,}`",              # 行内代码
                    r"\$\s+\S+",                  # $ 开头的命令行
                    r"^\s{0,4}(python3?|pip3?|npm|npx|curl|ollama|git|cd|ls|cat)\b",
                ],
                "hint": "补一条能复现的命令（用反引号包起来，别人能直接复制）",
            },
        ],
    },
    {
        "id": "blocker",
        "name": "具体卡点",
        "max": 25,
        "checks": [
            {
                "id": "error",
                "label": "真实报错",
                "patterns": [
                    # 只认「具体到什么错了」的写法。光说「报错了」不算 —— 这是 bad_01 抓出来的假分。
                    r"Traceback|Exception|Error|error:|ERROR|Fatal|failed",
                    r"ModuleNotFoundError|ImportError|TypeError|SyntaxError|KeyError|EEXIST|ENOENT",
                    r"\b4\d{2}\b|\b5\d{2}\b|timeout|超时|refused|denied",
                    r"tag 不存在|不存在|undefined|null|NaN",
                    # 回复型：引用别人的具体判定也算「具体依据」
                    r"⚠️|❌|✅\s*[01]\.\d{2}|\d\.\d{2}\s*/\s*\d",
                ],
                "gated": {
                    "codeblock": [r"报错|报.{0,2}错|失败|崩|挂了|不工作|不能用"],
                },
                "hint": "补上完整报错（含最后一行 + 关键中间行），不要只说「报错了」",
            },
            {
                "id": "phenomenon",
                "label": "具体现象",
                "patterns": [
                    r"卡在|停(在|住)|不动|没反应|无响应|闪退|白屏|空白|崩了|挂了",
                    r"很慢|变慢|慢到|退化成|变成了|只有.{0,6}(帧|条|个)|跑满|占满",
                    r"起不来|跑不起来|跑不通|不能用|不生效|没生效|不刷新|读不到|拿不到|输出为空|是空的",
                ],
                "hint": "补一句具体现象（不是「不行」，而是「卡在第几行/停在什么状态」）",
            },
            {
                "id": "expectation",
                "label": "预期 vs 实际",
                "patterns": [
                    r"期望|预期|应该(是|能|会)|按理|理论上",
                    r"我以为|原以为|以为|本想|本来想",
                    r"实际(上|是|只|看|跑)|结果是|但结果|却|反而|结果还是",
                    r"差(在|距)|对不上|不一致|不符合",
                ],
                "hint": "补一句「我以为会怎样，实际怎样」——这是卡点的定义",
            },
        ],
    },
    {
        "id": "evidence",
        "name": "证据",
        "max": 25,
        "checks": [
            {
                "id": "log",
                "label": "日志/代码块",
                "patterns": [
                    r"```",                        # 围栏代码块
                    r"^\s{4}\S",                   # 缩进代码块
                    r"\|.*\|",                     # 表格（现象对照表）
                ],
                "hint": "把日志/配置/代码贴成代码块（截图之外再给文字，方便别人搜）",
            },
            {
                "id": "path",
                "label": "路径/文件名",
                "patterns": [
                    r"/Users/|~/|/Applications/|C:\\\\",
                    r"[\w\u4e00-\u9fa5-]+\.(py|js|ts|tsx|md|json|yaml|yml|sh|html|css|jsonl|skill|txt)\b",
                    r"[Ll]ine\s*\d+|第\s*\d+\s*行|L\d{1,4}\b",
                ],
                "hint": "补上出问题的文件路径和行号（有行号，别人才能直接跳到那里）",
            },
            {
                "id": "visual",
                "label": "截图/可核对物",
                "patterns": [
                    r"截图|见图|下图|上图|如图所示|附图",
                    r"[Pp][Nn][Gg]|[Jj][Pp][Gg]|\.mov|录屏",
                    r"https?://\S+",
                ],
                "hint": "补一张截图或链接（图形界面问题，文字永远说不清）",
            },
        ],
    },
]

# 灌水判定：命中即 0 分。这是 C3 rubric 里明确写死的红线（纯表情灌水凑数）。
SLACK_PATTERNS = [
    r"^\s*[+＋]?\s*1\s*$",
    r"^\s*(收到|好的|好|ok|OK|OK的|同问|同上|一样|我也是|蹲|求|顶|mark)\s*[!！。.~]*\s*$",
    r"^\s*[\U0001F300-\U0001FAFF\u2600-\u27BF\s]+$",   # 纯 emoji
    r"^\s*[?？!！。.…\s]{0,6}$",
]

CJK = re.compile(r"[\u4e00-\u9fa5]")


# ---------------------------------------------------------------------------
@dataclass
class CheckResult:
    id: str
    label: str
    hit: bool
    snippets: List[str] = field(default_factory=list)
    hint: str = ""


@dataclass
class DimensionResult:
    id: str
    name: str
    max: int
    score: int
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def missed(self) -> List[CheckResult]:
        return [c for c in self.checks if not c.hit]


@dataclass
class Report:
    text: str
    total: int
    verdict: str
    is_slack: bool
    dimensions: List[DimensionResult]
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": VERSION,
            "total": self.total,
            "verdict": self.verdict,
            "is_slack": self.is_slack,
            "notes": self.notes,
            "chars": len(self.text),
            "dimensions": [
                {
                    "id": d.id,
                    "name": d.name,
                    "score": d.score,
                    "max": d.max,
                    "hit": [c.id for c in d.checks if c.hit],
                    "missed": [{"id": c.id, "label": c.label, "hint": c.hint}
                               for c in d.missed],
                }
                for d in self.dimensions
            ],
        }


def _snippet(text: str, pattern: str, width: int = 18) -> List[str]:
    """返回命中片段的原文摘引（最多 2 条），保证「为什么加分」可核对。"""
    out: List[str] = []
    for m in re.finditer(pattern, text, flags=re.MULTILINE):
        s = m.group(0).strip()
        if not s:
            continue
        # 扩一点上下文，让摘引像人话
        start = max(0, m.start() - width // 3)
        end = min(len(text), m.end() + width)
        ctx = text[start:end].replace("\n", " ").strip()
        ctx = re.sub(r"\s{2,}", " ", ctx)
        if ctx not in out:
            out.append(ctx)
        if len(out) >= 2:
            break
    return out


def _is_slack(text: str) -> bool:
    stripped = text.strip()
    for p in SLACK_PATTERNS:
        if re.match(p, stripped):
            return True
    # 少于 6 个中文字、且没有任何代码/报错 → 也是灌水
    if len(CJK.findall(stripped)) < 6 and "`" not in stripped and "Error" not in stripped:
        return True
    return False


def analyze(text: str) -> Report:
    text = text or ""
    slack = _is_slack(text)
    has_codeblock = "```" in text

    dims: List[DimensionResult] = []
    for spec in DIMENSIONS:
        checks: List[CheckResult] = []
        for cs in spec["checks"]:
            pats = list(cs["patterns"])
            gated = cs.get("gated") or {}
            # 只有满足前置条件（例如贴了代码块），宽泛措辞才算证据
            if gated.get("codeblock") and has_codeblock:
                pats.extend(gated["codeblock"])
            hits: List[str] = []
            for p in pats:
                hits.extend(_snippet(text, p))
                if hits:
                    break
            checks.append(CheckResult(id=cs["id"], label=cs["label"],
                                      hit=bool(hits), snippets=hits[:2],
                                      hint=cs["hint"]))
        got = sum(1 for c in checks if c.hit)
        score = round(spec["max"] * got / len(checks))
        dims.append(DimensionResult(id=spec["id"], name=spec["name"],
                                    max=spec["max"], score=score, checks=checks))

    total = sum(d.score for d in dims)
    notes: List[str] = []

    if slack:
        total = 0
        for d in dims:
            d.score = 0
        notes.append("命中灌水规则：本条不构成提问，按 C3 rubric 直接记 0 分。")

    # 甩问题：三样都没有 → 封顶 25
    ctx_ok = dims[0].score > 0
    att_ok = dims[1].score > 0
    blk_ok = dims[2].score > 0
    if not slack and not (ctx_ok and blk_ok) and len(text) < 40:
        total = min(total, 25)
        notes.append("疑似「甩问题」：篇幅过短且上下文/卡点缺失，总分封顶 25。")

    if slack:
        verdict = "灌水（不要发）"
    elif total >= 85:
        verdict = "可以直接发"
    elif total >= 70:
        verdict = "补一条就能发"
    elif total >= 50:
        verdict = "群友很难帮上"
    else:
        verdict = "属于「甩问题」，重写"

    return Report(text=text, total=total, verdict=verdict, is_slack=slack,
                  dimensions=dims, notes=notes)


# ---------------------------------------------------------------------------
BAR = "─" * 62


def render(rep: Report) -> str:
    lines: List[str] = []
    lines.append(f"提问质量自检 · ask_checker v{VERSION}")
    lines.append(BAR)
    lines.append(f"总分 {rep.total}/100   判定：{rep.verdict}   （{len(rep.text)} 字）")
    for n in rep.notes:
        lines.append(f"⚠️  {n}")
    lines.append(BAR)

    for d in rep.dimensions:
        marks = "  ".join(("✅ " + c.label) if c.hit else ("❌ " + c.label)
                          for c in d.checks)
        lines.append(f"{d.name:<6} {d.score:>3}/{d.max:<3} {marks}")
        for c in d.checks:
            if c.hit and c.snippets:
                for s in c.snippets[:1]:
                    lines.append(f"          命中「{c.label}」：…{s}…")
            if not c.hit:
                lines.append(f"          缺「{c.label}」→ {c.hint}")
        lines.append("")

    missed = [c for d in rep.dimensions for c in d.missed]
    if missed:
        lines.append(BAR)
        lines.append("照抄填空（把下面每行补成一句话，分数会涨到 85+）：")
        for i, c in enumerate(missed[:8], 1):
            lines.append(f"  {i}. 【{c.label}】{c.hint}")
    else:
        lines.append(BAR)
        lines.append("四个维度全中。发之前再做一件事：把「我不能公开的信息」删掉。")

    lines.append(BAR)
    lines.append("提醒：这个分数只代表「结构完整」，不代表「问题有价值」。")
    lines.append("      有价值的问题 = 别人看完能立刻动手；结构只是保证别人看得懂。")
    return "\n".join(lines)


def main(argv: List[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="群内提问质量自检器")
    ap.add_argument("input", help="提问文本文件路径，或 - 表示 stdin")
    ap.add_argument("--min", type=int, default=70, help="通过阈值（默认 70）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    try:
        if args.input == "-":
            text = sys.stdin.read()
        else:
            text = Path(args.input).read_text(encoding="utf-8")
    except OSError as e:
        print(f"读不到输入：{e}", file=sys.stderr)
        return 2

    rep = analyze(text)
    if args.json:
        print(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(render(rep))
    return 0 if rep.total >= args.min else 1


if __name__ == "__main__":
    raise SystemExit(main())
