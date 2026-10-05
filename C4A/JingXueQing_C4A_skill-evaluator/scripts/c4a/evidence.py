"""证据引擎 —— 评审可靠性的地基。

核心约定（这是本评审器区别于"关键词计数脚本"的核心）：

    每一条判定 =一个 CheckResult，它必须携带 Evidence：
        file     命中发生在哪个文件
        line     第几行
        snippet  命中的原文片段（给人看的）
        rule     命中了哪条规则
        polarity 正向 / 负向

    没有 Evidence 的判定不允许进入最终评分。

这样做的三个好处：
    1. 误判可追溯——老师说"这条判错了"，能1 秒定位到原文；
    2. 置信度可量化——证据越多越具体，置信度越高；
    3. 报告天然自带说服力——每个✅/⚠️/❌ 后面都跟着"因为这一行"。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Iterable, Optional

# --------------------------------------------------------------------------
# 哨兵头：extract.content_of 用它标记每个文件的起点
# --------------------------------------------------------------------------
FILE_SENTINEL = re.compile(r"^=== FILE: (.+?) ===$", re.M)


@dataclass
class Evidence:
    """一条可追溯的证据。"""
    rule: str                # 规则 ID，如REUSE.install
    file: str                # 源文件名
    line: int                # 行号（1-based）
    snippet: str             # 命中的原文行（截断）
    polarity: str = "positive"   # positive / negative
    weight: float = 1.0          # 该证据的权重

    def render(self) -> str:
        mark = "➕" if self.polarity == "positive" else "➖"
        return f"{mark} `{self.file}:{self.line}` — {self.snippet}"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CheckResult:
    """单个检查项的结果。"""
    check_id: str
    label: str                # 中文可读名
    passed: bool
    detail: str                    # 人类可读的判定说明
    evidence: list[Evidence] = field(default_factory=list)

    @property
    def confidence(self) -> float:
        """置信度：0.35(裸信号) ~ 1.0(多文件互证)。

        设计：单条弱信号不足以支撑 ✅；需要 ≥2 条互证或1 条强信号。
        """
        n = len(self.evidence)
        if n == 0:
            return 0.0
        if n == 1:
            return min(0.7, 0.45 + 0.25 * self.evidence[0].weight)
        return min(1.0, 0.7 + 0.1 * (n - 1))

    def to_dict(self) -> dict:
        return {
            "check_id": self.check_id, "label": self.label,
            "passed": self.passed, "detail": self.detail,
            "confidence": round(self.confidence, 2),
            "evidence": [e.to_dict() for e in self.evidence],
        }


# --------------------------------------------------------------------------
# 带行号的搜索工具
# --------------------------------------------------------------------------

class TextIndex:
    """把多文件合并文本建成"可按行号回溯"的索引。

    合并文本形如：
        === FILE: a.md ===
        line1
        line2
        === FILE: b.md ===
        line1
    """

    def __init__(self, blob: str):
        self.lines: list[tuple[str, int, str]] = []   # (filename, lineno, line)
        cur_file = "?"
        lineno = 0
        for line in blob.splitlines():
            m = FILE_SENTINEL.match(line.strip())
            if m:
                cur_file = m.group(1)
                lineno = 0
                continue
            lineno += 1
            self.lines.append((cur_file, lineno, line))
        self.blob = blob

    def search(
        self,
        pattern: str | re.Pattern,
        *,
        polarity: str = "positive",
        rule: str = "",
        weight: float = 1.0,
        limit: int = 3,
        exclude: Iterable[str] = (),
        flags: int = re.IGNORECASE,
    ) -> list[Evidence]:
        """正则搜索，返回最多 limit 条证据（取命中行+上下文行）。"""
        rx = pattern if isinstance(pattern, re.Pattern) else re.compile(pattern, flags)
        ex = [e.lower() for e in exclude]
        out: list[Evidence] = []
        for fname, lineno, line in self.lines:
            if any(e in fname.lower() for e in ex):
                continue
            if rx.search(line):
                out.append(Evidence(
                    rule=rule or rx.pattern, file=fname, line=lineno,
                    snippet=line.strip()[:160], polarity=polarity, weight=weight,
                ))
                if len(out) >= limit:
                    break
        return out

    def search_any(
        self,
        patterns: Iterable[str | re.Pattern],
        *,
        polarity: str = "positive",
        rule: str = "",
        weight: float = 1.0,
        limit_each: int = 2,
        exclude: Iterable[str] = (),
        keep: int = 8,
    ) -> list[Evidence]:
        """多模式并集搜索，去重后按文件+行号排序，保留最多 keep 条。

        keep 要给得比limit_each 大：并集里常有几条低价值泛化命中，
        如果早早截断，高特异性的信号（如"预期结果"）反而被挤掉。
        """
        seen: set[tuple[str, int]] = set()
        out: list[Evidence] = []
        for p in patterns:
            for ev in self.search(p, polarity=polarity, rule=rule,
                                   weight=weight, limit=limit_each, exclude=exclude):
                key = (ev.file, ev.line)
                if key in seen:
                    continue
                seen.add(key)
                out.append(ev)
        out.sort(key=lambda e: (e.file, e.line))
        return out[:keep]

    def file_names(self) -> list[str]:
        seen: list[str] = []
        for f, _, _ in self.lines:
            if f not in seen:
                seen.append(f)
        return seen

    def text_for(self, filename: str) -> str:
        return "\n".join(l for f, _, l in self.lines if f == filename)

    def has_file(self, pattern: str) -> bool:
        rx = re.compile(pattern, re.IGNORECASE)
        return any(rx.search(f) for f in self.file_names())


# --------------------------------------------------------------------------
# 判定辅助
# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# 档位判定
# --------------------------------------------------------------------------

# 证据权重阈值（标定说明见 grade() 内注释）
STRONG_W = 0.75   # 一条高特异信号，或两条中等信号
WEAK_W = 0.35     # 一条弱信号


def grade(
    positive: list[Evidence],
    negative: list[Evidence],
    *,
    strong_threshold: int = 2,
    weak_threshold: int = 1,
    absence_is_pass: bool = False,
) -> tuple[str, str, float]:
    """把正负证据收敛成 ✅ / ⚠️ / ❌ 三档。

    规则（负向证据优先否决，这是防误判的关键）：
        有任何负向证据           → ❌（除非正向证据 ≥ strong_threshold*2 强力翻案）
        正向 ≥ strong_threshold  → ✅
        正向 ≥ weak_threshold    → ⚠️
        否则                     → ❌

    absence_is_pass=True 用于「纯负向检查项」——
    例如"无硬编码绝对路径"这类检查，成功形态就是"什么都没找到"。
    若不开启这个开关，一份干净的提交会因为零证据而被误判为❌，
    这是规则式评审最典型的误判来源（第一轮实测已踩到）。

    返回 (等级, 说明, 强度0~1)
    """
    npos, nneg = len(positive), len(negative)
    # 按权重累加，而不是简单数条数。
    # 理由：「预期结果」这种高特异信号命中 1 次，
    # 比「示例」这种泛化词命中 3 次更能说明问题。
    # 金标准测试（LiMing / ZhaoLiu 样本）证明：纯计数会把
    # 写了明确验收标准的好文档判成 ⚠️，误判率 15%。
    wpos = sum(e.weight for e in positive)
    wneg = sum(e.weight for e in negative)
    # 权重标定（v1.3，用 8 份金标准样本反推）：
    #   单条高特异信号（如"**输入**…**输出**"模式权重 1.5）
    #     = 1.0(相对强度) × 0.6(信任) × 1.0(权威) = 0.60
    #   单条中特异信号（如"预期结果"1.3）= 0.78 × 0.6 = 0.47
    # 所以「strong=1」类检查项（存在性检查，命中一条即成立）
    # 阈值应低于单条高特异信号的 0.60；「strong=2」类（质量检查，
    # 要求多条互证）阈值应高于它。
    # 早先版本把 strong_threshold 直接当权重阈值用（strong=1→1.0，
    # strong=2→2.0），导致所有检查项都够不到 ✅，好文档全被判保守。
    strong_w = STRONG_W if strong_threshold >= 2 else (WEAK_W if strong_threshold <= 1 else 0.5)
    weak_w = WEAK_W

    if absence_is_pass and wpos < weak_w:
        if wneg == 0:
            return "✅", "未检出任何问题信号（该项为负向检查，通过）", 0.75
        files = ", ".join(sorted({e.file for e in negative})[:3])
        return "❌", f"检出 {len(negative)} 处问题信号（{files}）", min(1.0, 0.3 + 0.2 * len(negative))

    if wneg and wpos < strong_w * 2:
        files = ", ".join(sorted({e.file for e in negative})[:3])
        return "❌", f"检出 {len(negative)} 处问题信号（{files}）", min(1.0, 0.3 + 0.2 * len(negative))
    if wpos >= strong_w:
        return "✅", f"{len(positive)} 条正向证据（权重 {wpos:.2f}）", min(1.0, 0.6 + 0.2 * wpos)
    if wpos >= weak_w:
        return "⚠️", f"仅 {len(positive)} 条弱信号（权重 {wpos:.2f}），证据不足", 0.45
    if wneg:
        files = ", ".join(sorted({e.file for e in negative})[:3])
        return "❌", f"无正向证据，且检出 {len(negative)} 处问题（{files}）", 0.2
    return "❌", "未检出任何相关信号", 0.15
