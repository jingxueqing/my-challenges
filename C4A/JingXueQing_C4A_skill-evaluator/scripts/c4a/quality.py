"""Level 3 —— 技能质量评审（C4 四条件）。

这是本技能的核心创新点。架构决策：**规则优先 + 可选 LLM 深审**。

为什么不做「纯 LLM」：
    - 评审要可复现。同一个人两次跑，LLM 结论可能不同 → 老师无法采信、
      学生无法申诉「凭什么判我❌」。
    - 评审要可追溯。每条结论必须指向「哪个文件第几行」，
      而 LLM 给不出稳定的行号级引用。
    - 评审要零成本可跑。40 份提交 × 4 维度 × LLM调用 = 慢且贵，
      助教不可能每节课都这么跑。

为什么不只做「纯规则关键词」：
    - starter 的做法（关键词命中即计数）覆盖率低、误判高。
      「作者在文档里写了一句『本技能不依赖我的电脑路径』」会被误判成
      存在硬编码路径。

本模块的做法 —— **三态判定 + 证据强度 + 负向优先否决**：
    1. 每个检查项产出正/负证据，证据带权重与行号；
    2. 负向证据存在时直接压到 ⚠️/❌（防止"多写了几段就洗白"）；
    3. 证据强度决定档位，而非单纯计数——「有安装步骤+ 有 requirements.txt」
       比「顺口提了一句 install」权重更高；
    4. 结论附置信度，报告里明确标出哪些结论需要老师人工复核。

同时提供 extract_signals_for_llm()：把证据打包成结构化上下文，
供可选的 LLM 深审环节使用（架构上预留，本版默认关闭）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from .collect import FileInfo
from .evidence import CheckResult, Evidence, TextIndex, grade
from .rubric import (
    CHECKS_BY_CRITERION, CRITERIA_META, DEFAULT_WEIGHTS, LEVEL_SCORE, Check,
)

# 置信度阈值：低于此值在报告里标注「需人工复核」
LOW_CONFIDENCE = 0.55

# 致命检查项：命中即该维度直接判❌，不允许被其他检查项"洗白"。
# 依据 C4「可复用」的检验方法——"让一个陌生人按你的说明操作，能成功吗？"
# 明文密钥与硬编码个人路径会让陌生人必然失败，因此不是扣分项而是不合格项。
FATAL_CHECKS = {"REUSE.nopath", "REUSE.nosecret"}


@dataclass
class CriterionResult:
    key: str
    label: str
    desc: str
    grade: str                      # ✅ / ⚠️ / ❌
    score: float                    # 0~1
    strength: float
    reason: str
    checks: list[CheckResult] = field(default_factory=list)
    needs_human: bool = False
    evidence_count: int = 0

    def to_dict(self) -> dict:
        return {
            "key": self.key, "label": self.label, "grade": self.grade,
            "score": round(self.score, 3), "strength": round(self.strength, 3),
            "reason": self.reason, "needs_human": self.needs_human,
            "evidence_count": self.evidence_count,
            "checks": [c.to_dict() for c in self.checks],
        }


@dataclass
class QualityResult:
    author: str
    criteria: list[CriterionResult]
    quality_score: float             # 0~1（四条件加权）
    total_points: float# 折算成 4 分制
    needs_human: list[str] = field(default_factory=list)
    advice: list[str] = field(default_factory=list)

    def by_key(self, key: str) -> Optional[CriterionResult]:
        return next((c for c in self.criteria if c.key == key), None)

    def to_dict(self) -> dict:
        return {
            "author": self.author,
            "quality_score": round(self.quality_score, 3),
            "total_points": round(self.total_points, 2),
            "needs_human": self.needs_human,
            "advice": self.advice,
            "criteria": [c.to_dict() for c in self.criteria],
        }


# 一些"噪音文件"不参与内容判定：示例样本、运行产物、交付自检
NOISE_PATTERNS = [
    r"^samples?/", r"/samples?/", r"^demo_run", r"体检报告", r"交付物自检",
    r"__pycache__", r"\.log$", r"\.jsonl$", r"trace\.json",
]

# 证据权威性排序：说明/教学文档是作者为自己撰写的正式说明，
# 优先级高于 AAR / 自检 / 归档包。AAR 里的话往往是"我做了"，不是"我能复用"。
PRIMARY_DOC = re.compile(r"(skill[-_ ]?说明|教学说明|README|使用说明|skill说明)", re.IGNORECASE)
SECONDARY_DOC = re.compile(r"(AAR|reflect|反思|复盘)", re.IGNORECASE)
# .skill/.zip 包内部内容权重降级：包里常含模板与示例，不等于作者的能力
ARCHIVE_MEMBER = re.compile(r"\.skill$|\.zip$", re.IGNORECASE)


def _doc_weight(fname: str) -> float:
    """按文件角色给出证据权重。"""
    if PRIMARY_DOC.search(fname):
        return 1.0
    if SECONDARY_DOC.search(fname):
        return 0.6
    if ARCHIVE_MEMBER.search(fname):
        return 0.75      # 包内是真实技能内容，但含模板，需降权
    return 0.9


def _is_noise(fi: FileInfo) -> bool:
    p = fi.rel_path.lower()
    return any(re.search(pat, p, re.IGNORECASE) for pat in NOISE_PATTERNS)


def build_index(files: list[FileInfo], *, include_noise: bool = False) -> TextIndex:
    """构造可按行号回溯的多文件文本索引。"""
    from .extract import content_of
    paths = [f.abs_path for f in files
             if include_noise or not _is_noise(f)]
    blob, _ = content_of([__import__("pathlib").Path(p) for p in paths])
    return TextIndex(blob)


# 命中行若包含这些词，说明作者是在「讨论/示例」而非「真的没做完」
NEGATION = re.compile(
    r"(没有|无|不要|避免|禁止|不依赖|不存在|不包含|不会|not|never|avoid|without|"
    r"禁止使用|请替换|示例|例如|模板|template|placeholder|待替换|your_)", re.IGNORECASE)
# "元提及"过滤：技能文档在描述「要检查哪些东西」时会列举关键词本身，
# 例如 rubric 里写 `[改进, 下一步, TODO, 优先级]`。
# 这类"提到某个坏味道"不等于"存在坏味道"，必须排除，否则误判率飙升。
# 判据：命中行里同时出现 ≥2 个同类坏味道关键词，或行内是枚举型列表。
META_ENUM = re.compile(
    r"关键词|关键字|信号|列表|如下|字段|正则|regex|pattern|检查项|规则|"
    r"bad\s*signals?|negative\s*signals?|keyword", re.IGNORECASE)
_BAD_TOKENS = re.compile(
    r"(TODO|FIXME|待补充|待完善|占位|placeholder|未填写|填入)", re.IGNORECASE)
# 明显是模板/示例产物的文件名——其内容不作为质量证据
TEMPLATE_FILE = re.compile(
    r"(template|模板|placeholder|占位|未填写|_未|未补写|example|示例|sample|demo_|"
    r"specimen|骨架|skeleton)", re.IGNORECASE)


def _line_of(idx: TextIndex, ev: Evidence) -> str:
    for f, ln, txt in idx.lines:
        if f == ev.file and ln == ev.line:
            return txt
    return ""


def _dedupe_evidence(evs: list[Evidence]) -> list[Evidence]:
    """同文件同行只保留一条证据，避免报告里刷屏。"""
    seen: set[tuple[str, int]] = set()
    out: list[Evidence] = []
    for e in evs:
        k = (e.file, e.line)
        if k in seen:
            continue
        seen.add(k)
        out.append(e)
    return out


# 占位内容特征
PLACEHOLDER_LINE = re.compile(
    r"^\s*(?:[-*>|#\s]*)?(?:TODO|FIXME|待补充|待完善|待填写|填写此处|尚未完成|暂未|敬请期待|"
    r"Coming\s+soon|your\s+\w+\s+here)\b|^\s*[:：\-]\s*$|^\s*待办\s*$", re.IGNORECASE)
# 文档里的小节标题（命中行是标题时，往下看几行判断该节是否为空壳）
SECTION_HEAD = re.compile(r"^\s*#{1,6}\s+\S+")


def _is_placeholder_hit(idx: TextIndex, ev: Evidence) -> bool:
    """判断这条证据是否落在"有标题无内容"的空壳小节里。"""
    line = _line_of(idx, ev)
    if not line:
        return False
    # 证据行本身就是占位内容
    if PLACEHOLDER_LINE.search(line):
        return True
    if not SECTION_HEAD.match(line):
        return False
    # 是标题：向下找该小节的第一行非空正文
    start = _line_index(idx, ev)
    if start < 0:
        return False
    for f, ln, txt in idx.lines[start + 1: start + 6]:
        if SECTION_HEAD.match(txt):
            return False          # 下一节，说明本节确实没内容
        t = txt.strip()
        if not t:
            continue
        return bool(PLACEHOLDER_LINE.search(t))
    return True                   # 小节到文件末尾都没有实质内容


def _line_index(idx: TextIndex, ev: Evidence) -> int:
    """(file, line) → 在 idx.lines 中的下标，带缓存。"""
    cache = getattr(idx, "_pos_cache", None)
    if cache is None:
        cache = {}
        setattr(idx, "_pos_cache", cache)
    key = (ev.file, ev.line)
    if key not in cache:
        cache[key] = next(
            (i for i, (f, ln, _) in enumerate(idx.lines)
             if f == ev.file and ln == ev.line), -1)
    return cache[key]


def _run_check(chk: Check, idx: TextIndex, *, file_names: list[str]) -> CheckResult:
    """执行单个检查项，产出带证据的结果。"""
    pos: list[Evidence] = []
    neg: list[Evidence] = []

    # 模板/示例类文件不参与内容证据（避免 "示例里的 TODO" 被当成真问题，
    # 也避免模板自带的标准段落被当成作者的能力证明）
    tmpl_files = {f for f in file_names if TEMPLATE_FILE.search(f)}

    if chk.positive:
        pats = [(re.compile(p, re.IGNORECASE | re.MULTILINE), w)
                for p, w in chk.positive]
        max_w = max((w for _, w in chk.positive), default=1.0)
        if tmpl_files:
            pos = idx.search_any([p for p, _ in pats], polarity="positive",
                                 rule=chk.id, weight=max_w, limit_each=2,
                                 exclude=tmpl_files)
        if not pos:   # 模板是唯一来源时仍取用，但整体降权
            pos = idx.search_any([p for p, _ in pats], polarity="positive",
                                 rule=chk.id, weight=max_w * 0.6, limit_each=2)
        # 用「命中模式的权重 × 0.6（基础信任系数）× 文档权威系数」重赋权重。
        # 0.6 是信任基线：单一来源的信号不足以单独定论，需与其他证据互证；
        # 高特异性模式（如"预期结果"1.3）因此得到 0.78，能独立支撑 ⚠️~✅。
        for e in pos:
            base = e.weight / max_w if max_w else 1.0     # 还原命中模式的相对强度
            e.weight = round(base * 0.6 * _doc_weight(e.file), 3)
        pos.sort(key=lambda e: -e.weight)
    if chk.negative:
        neg = idx.search_any(
            [re.compile(p, re.IGNORECASE | re.MULTILINE) for p, _ in chk.negative],
            polarity="negative", rule=chk.id, weight=1.2, limit_each=2,
        )

    # 否定语境 + 元提及过滤：
    # 作者在声明"我没有这个问题"时不算问题；在列举"要检查哪些关键词"时也不算问题。
    if neg:
        filtered = []
        for e in neg:
            line = _line_of(idx, e)
            if NEGATION.search(line):
                continue
            if META_ENUM.search(line) and len(_BAD_TOKENS.findall(line)) >= 2:
                continue
            if META_ENUM.search(line) and re.search(r"[\[（(][^\]）)]{0,80}[\]）)]", line) \
                    and _BAD_TOKENS.search(line):
                continue
            filtered.append(e)
        neg = filtered

    pos = _dedupe_evidence(pos)
    neg = _dedupe_evidence(neg)

    # 占位符污染：标题写了「## 安装」，正文却是「TODO: 补充安装步骤」——
    # 这是"有标题无内容"，不能算安装说明。金标准测试（ChenJing 样本）证明，
    # 不做这一步，一份通篇 TODO 的空壳能靠三个空标题把"可复用"洗到及格线。
    # 判据：证据行本身是占位内容，或其所在小节正文首行是占位内容。
    if pos:
        pos = [e for e in pos if not _is_placeholder_hit(idx, e)]

    g, reason, strength = grade(
        pos, neg, strong_threshold=chk.strong, weak_threshold=chk.weak,
        absence_is_pass=chk.absence_is_pass,
    )
    return CheckResult(
        check_id=chk.id, label=chk.label, passed=(g == "✅"),
        detail=f"{reason}｜检查项档位 {g}", evidence=(pos + neg)[:6],
    )


def evaluate_quality(
    author: str,
    files: list[FileInfo],
    *,
    weights: dict[str, float] | None = None,
    include_noise: bool = False,
) -> QualityResult:
    """对单个作者的四条件做质量评审。"""
    w = dict(DEFAULT_WEIGHTS)
    if weights:
        w.update(weights)
    # 归一化
    tot = sum(w.values()) or 1.0
    w = {k: v / tot for k, v in w.items()}

    idx = build_index(files, include_noise=include_noise)
    file_names = idx.file_names()

    criteria: list[CriterionResult] = []
    advice: list[str] = []
    needs_human: list[str] = []

    for key in ("reusable", "executable", "verifiable", "clear_io"):
        checks = CHECKS_BY_CRITERION.get(key, [])
        crs: list[CheckResult] = []
        pos_total = neg_total = 0
        weighted_pass = 0.0
        weight_sum = 0.0
        # 致命负向证据（明文密钥 / 硬编码个人路径）单独收集：
        # 这类问题不是"扣分项"，而是"不合格项"。
        # 金标准测试（SunLi 样本）证明：只要不把它单独拎出来，
        # 一份写了安装说明的提交就能靠其他检查项把可复用洗成 ✅，
        # 放过真正会砸掉别人机器的坑。
        fatal: list[str] = []
        for chk in checks:
            cr = _run_check(chk, idx, file_names=file_names)
            crs.append(cr)
            for e in cr.evidence:
                if e.polarity == "negative" and chk.id in FATAL_CHECKS:
                    fatal.append(f"{e.file}:{e.line}")
            # 权威文档带来的证据权重更高，用它给检查项定权
            best_w = max((e.weight for e in cr.evidence if e.polarity == "positive"),
                         default=0.5)
            # 「没检出问题」是弱通过：它只能证明"没犯错"，
            # 不能证明"写清楚了"。金标准测试（ChenJing / WangXiao 样本）证明，
            # 若与正向检查项等权计算，一份通篇 TODO 的空壳会靠两条
            # "没犯错"白拿 60% 而判成 ✅ —— 这正是"关键词计数式评审"的经典误判。
            # 因此负向检查项的通过只给 0.45 权重。
            cw = (0.45 if chk.absence_is_pass
                  else 0.5 + 0.5 * min(1.0, best_w))      # 正向 0.5~1.0
            weight_sum += cw
            if cr.passed:
                weighted_pass += cw
            for e in cr.evidence:
                if e.polarity == "positive":
                    pos_total += 1
                else:
                    neg_total += 1

        # 维度评级：加权通过率（而非简单计数，避免"低价值检查项凑数"）
        ratio = (weighted_pass / weight_sum) if weight_sum else 0.0
        # 没有任何正向证据时，负向检查的"通过"不足以支撑 ⚠️ 以上——
        # 什么都不写不等于及格。
        if pos_total == 0:
            grade_lvl = "❌"
        else:
            grade_lvl = "✅" if ratio >= 0.6 else ("⚠️" if ratio >= 0.3 else "❌")
        if neg_total >= 3 and grade_lvl == "✅":
            grade_lvl = "⚠️"
        if neg_total >= 6 and grade_lvl == "⚠️":
            grade_lvl = "❌"
        # 致命问题一票否决
        if fatal and grade_lvl != "❌":
            grade_lvl = "❌"

        n_pass = sum(1 for c in crs if c.passed)
        meta = CRITERIA_META[key]
        cr = CriterionResult(
            key=key, label=meta["label"], desc=meta["desc"],
            grade=grade_lvl, score=LEVEL_SCORE[grade_lvl],
            strength=min(1.0, (pos_total + neg_total) / 6.0),
            reason=f"{n_pass}/{len(crs)} 个检查项通过（加权 {ratio:.0%}）"
                   + (f"，检出 {neg_total} 处问题信号" if neg_total else "")
                   + (f"；❗致命问题 {len(fatal)} 处（{'、'.join(fatal[:2])}）"
                      if fatal else ""),
            checks=crs,
            evidence_count=pos_total + neg_total,
        )
        # 注意：负向检查项（absence_is_pass）天然"零证据即通过"，
        # 不能因为零证据就判它需人工复核，否则干净的提交反而全被标黄。
        has_negative_only = all(c.absence_is_pass for c in CHECKS_BY_CRITERION[key])
        eff_evidence = cr.evidence_count if not has_negative_only else max(
            cr.evidence_count, 2 if grade_lvl != "❌" else 0)
        avg_conf = (sum(c.confidence for c in crs) / len(crs)) if crs else 0.0
        cr.needs_human = (eff_evidence < 2) or (avg_conf < LOW_CONFIDENCE and eff_evidence < 3)
        if cr.needs_human:
            needs_human.append(meta["label"])
            cr.reason += "（证据较少，建议人工复核）"
        criteria.append(cr)

        # 未通过且非可选 → 产出建议
        for c in crs:
            if not c.passed:
                chk = next((x for x in CHECKS_BY_CRITERION[key] if x.id == c.check_id), None)
                if chk and chk.advice:
                    advice.append(f"[{meta['label']}] {chk.advice}")

    # 去重建议，最多 6 条
    seen: set[str] = set()
    advice_out: list[str] = []
    for a in advice:
        if a not in seen:
            seen.add(a)
            advice_out.append(a)
    advice = advice_out[:6]

    q = sum(c.score * w[c.key] for c in criteria)
    return QualityResult(
        author=author, criteria=criteria,
        quality_score=round(q, 3), total_points=round(q * 4, 2),
        needs_human=needs_human, advice=advice,
    )


# --------------------------------------------------------------------------
# 可选 LLM 深审：架构预留
# --------------------------------------------------------------------------

def extract_signals_for_llm(q: QualityResult, max_chars: int = 6000) -> str:
    """把规则层的结论打包成结构化上下文，供 LLM 复核/深审。

    本版默认不调用 LLM（保证离线可跑、结论可复现），
    但接口已经留好：任何工具只要能接收这段 prompt 并返回 JSON，
    就能在规则层之上做语义深审，而不必重写整条流水线。
    """
    lines = [f"#评审对象: {q.author}", "## 规则层初判结果"]
    for c in q.criteria:
        lines.append(f"### {c.label}: {c.grade} ({c.reason})")
        for chk in c.checks:
            mark = "✅" if chk.passed else "❌"
            lines.append(f"  - {mark} {chk.label}: {chk.detail}")
            for e in chk.evidence[:2]:
                lines.append(f"      · {e.file}:{e.line} {e.snippet[:80]}")
    lines.append("\n## 待人工确认的低置信度维度")
    lines.extend(q.needs_human or ["无"])
    return "\n".join(lines)[:max_chars]
