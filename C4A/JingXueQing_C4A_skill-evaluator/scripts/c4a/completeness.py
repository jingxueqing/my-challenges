"""Level 2 —— 提交完整性检查（5 个必须文件）。

与starter 的差别（这是「误判率低」的关键）：
    starter 只做「文件名 or 内容，二选一命中即算✅」——极易误判，
    例如 README.md 里恰好出现"prompt"两个字就算有 AI 日志。

    本实现用「分层证据 + 阈值 + 冲突消解」：
        1. 逐文件先算出每个槽位的证据强度（文件名信号 1.0 / 内容信号 0.5-0.7）；
        2. 每个槽位取该作者所有文件里的**最强**证据，而不是任意命中；
        3. 强度 ≥0.9 →✅；≥0.6 → ⚠️（弱证据，可能误判，报告里提示人工确认）；
        4. 只有一个文件同时承担多个槽位时（典型：一份 README 什么都提），
           引入「槽位独占性」惩罚——同一文件命中 ≥3 个槽位时，
           除最强槽位外其余降级为 ⚠️，这解决了 README 一稿通吃的经典误判。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Optional

from .collect import FileInfo
from .rubric import COMPLETENESS_SPEC, COMPLETENESS_ORDER


@dataclass
class SlotResult:
    key: str
    label: str
    status: str                 # ✅ / ⚠️ / ❌
    strength: float             # 0~1+
    matched_files: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CompletenessResult:
    author: str
    slots: list[SlotResult]
    n_present: int              # ✅ 计数
    n_partial: int              # ⚠️ 计数
    n_missing: int              # ❌ 计数
    score: float                # 0~1
    verdict: str                # 齐全 / 部分缺失 / 严重缺失
    missing_labels: list[str] = field(default_factory=list)
    partial_labels: list[str] = field(default_factory=list)
    ambiguous: bool = False     # 是否有 ⚠️（需要人工确认）

    def to_dict(self) -> dict:
        return {
            "author": self.author,
            "n_present": self.n_present, "n_partial": self.n_partial,
            "n_missing": self.n_missing, "score": round(self.score, 3),
            "verdict": self.verdict,
            "missing_labels": self.missing_labels,
            "partial_labels": self.partial_labels,
            "ambiguous": self.ambiguous,
            "slots": [s.to_dict() for s in self.slots],
        }


PASS_STRONG = 0.90
PASS_PARTIAL = 0.60
# 一个文件最多能"顶"的槽位数，超出则降级
MAX_SLOTS_PER_FILE = 3

# 空壳信号：文件在，但正文是占位内容。
# 金标准测试（ChenJing 样本）证明：只看文件名会把
# "skill说明.md" 里通篇「待补充」的空壳判成 ✅ 齐全，
# 让真正没写内容的提交蒙混过关。命名合规 ≠ 内容合规。
SHELL_SIGNALS = re.compile(
    r"(待补充|待完善|待填写|TODO|填写此处|尚未完成|暂未|敬请期待|Coming\s+soon)", re.IGNORECASE)
# 篇幅阈值：低于此值仍算偏短，但只轻微降级（不排除"教学说明本来就短"的情况）
SHORT_DOC_CHARS = 80


def _read_text(fi: FileInfo) -> str:
    from . import extract as extractor
    from pathlib import Path
    if not fi.extract_ok:
        return ""
    r = extractor.extract(Path(fi.abs_path))
    return r.text if r.ok else ""


def _slot_evidence(fi: FileInfo, spec: dict, slot: str) -> tuple[float, list[dict]]:
    """对单个文件算它对某个槽位的证据强度。"""
    best = 0.0
    ev: list[dict] = []

    for pat, w in spec.get("filename_signals", []):
        if re.search(pat, fi.name, re.IGNORECASE) or re.search(pat, fi.rel_path, re.IGNORECASE):
            s = w * 1.0
            if s > best:
                best = s
            ev.append({"type": "filename", "pattern": pat, "weight": w,
                       "detail": f"文件名命中 {pat}"})

    # 扩展名作为次级佐证（0.35封顶，绝不足以单独判✅）
    if fi.ext in spec.get("extensions", []):
        s = 0.35
        if s > best:
            best = s
        ev.append({"type": "ext", "pattern": fi.ext, "weight": 0.35,
                   "detail": f"扩展名 {fi.ext} 属于推荐类型"})

    if best < PASS_PARTIAL:
        text = _read_text(fi)
        if text:
            for pat, w in spec.get("content_signals", []):
                m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
                if m:
                    s = w
                    if s > best:
                        best = s
                    line_no = text[:m.start()].count("\n") + 1
                    snippet = m.group(0).replace("\n", " ")[:60]
                    ev.append({"type": "content", "pattern": pat, "weight": w,
                               "detail": f"内容第 {line_no} 行命中「{snippet}」"})
                    break  # 每个槽位只取第一条内容信号，避免堆砌
    return best, ev


def _shell_penalty(fi: FileInfo, strength: float) -> tuple[float, str]:
    """检测"文件在但内容是空壳"，用于把命名合规降级为内容不足。

    返回 (调整后强度, 说明)。只对文档类文件生效——
    .py/.skill 等可执行内容的判定交给 Level 3，这里不越权。
    """
    if fi.ext not in (".md", ".txt", ".pdf", ".docx", ""):
        return strength, ""
    text = _read_text(fi)
    if not text.strip():
        return strength, ""
    hits = len(SHELL_SIGNALS.findall(text))
    lines = text.splitlines()
    ratio = hits / max(1, len(lines))
    note = ""
    # 只有"占位信号密集"才判定为空壳。
    # 阈值 0.15 的依据：ChenJing 空壳样本的占位行占比约 30%，
    # 而正常文档里偶然提到一次"待补充"占比通常 < 5%。
    if ratio > 0.15 and hits >= 2:
        note = f"正文含 {hits} 处占位信号（占 {ratio:.0%} 行），内容疑似空壳"
        strength *= 0.5
    elif len(text.strip()) < SHORT_DOC_CHARS and not lines:
        note = "正文为空"
        strength *= 0.5
    return strength, note


def check_author(author: str, files: list[FileInfo]) -> CompletenessResult:
    """对单个作者做 5槽位完整性检查。"""
    per_file: dict[str, list[tuple[float, list[dict]]]] = {
        k: [] for k in COMPLETENESS_ORDER
    }
    # 只用「带 C4 标记的正式交付文件」占槽位。
    # 附属源码（scripts/xxx.py、包内SKILL.md）参与质量评审，
    # 但不能拿来证明"交了教学说明"——否则一个空壳提交会被自己的源码文件凑成齐全。
    c4_files = [f for f in files if f.is_c4] or list(files)
    for fi in c4_files:
        for slot in COMPLETENESS_ORDER:
            s, ev = _slot_evidence(fi, COMPLETENESS_SPEC[slot], slot)
            if s > 0:
                per_file[slot].append((s, ev, fi))  # type: ignore[arg-type]

    # 独占性分析：计算每个文件命中了几个槽位
    # 只统计「有实义证据」的命中（strength >= 0.6），
    # 否则像 skill说明.md 这种既满足命名又碰巧提到 "安装" 的文件
    # 会虚增自己的槽位数，把自己也判成"身兼多职"。
    file_hits: dict[str, int] = {}
    for slot in COMPLETENESS_ORDER:
        for s, _ev, fi in per_file[slot]:
            if s >= PASS_PARTIAL:
                file_hits[fi.rel_path] = file_hits.get(fi.rel_path, 0) + 1

    results: list[SlotResult] = []
    for slot in COMPLETENESS_ORDER:
        # 附件文件（samples/ 模板等）降权：作者交了模板 ≠ 作者交了产物
        items = sorted(
            per_file[slot],
            key=lambda x: (-(x[0] * (0.5 if x[2].is_attachment else 1.0)), -x[0]),
        )
        if not items:
            results.append(SlotResult(
                key=slot, label=COMPLETENESS_SPEC[slot]["label"],
                status="❌", strength=0.0,
                reason="未找到任何对应文件",
            ))
            continue

        raw_strength, top_ev, top_file = items[0]
        # 附件文件的强度直接砍半（仍可能过弱证据线，但不会拿满✅）
        if top_file.is_attachment:
            raw_strength = round(raw_strength * 0.5, 3)
        # 空壳检测：命名合规但正文是占位内容 → 降级为 ⚠️
        shell_note = ""
        if raw_strength >= PASS_PARTIAL:
            adj, shell_note = _shell_penalty(top_file, raw_strength)
            raw_strength = round(adj, 3)
        top_strength = raw_strength
        status = "✅" if top_strength >= PASS_STRONG else (
            "⚠️" if top_strength >= PASS_PARTIAL else "❌")
        matched = [it[2].rel_path for it in items[:4]]
        ev_out = [{"file": it[2].rel_path, **e} for it in items[:2] for e in it[1][:2]]

        # 独占性惩罚：只有当「主要证据来自一个身兼多职的文件」时才降级。
        # 注意 file_hits 已只统计 >=0.6 的实义命中，所以正常一稿一文件不会触发。
        if top_strength < PASS_STRONG and \
                file_hits.get(top_file.rel_path, 0) > MAX_SLOTS_PER_FILE:
            if status == "✅":
                status = "⚠️"
            top_ev = top_ev + [{
                "type": "penalty",
                "detail": f"该文件同时是 {file_hits[top_file.rel_path]} 个槽位的主要证据，"
                          f"槽位归属存在歧义，需人工确认",
            }]
        elif status == "✅" and file_hits.get(top_file.rel_path, 0) > MAX_SLOTS_PER_FILE:
            # 命名级强证据（≥0.9）优先，歧义只作提示，不降级
            top_ev = top_ev + [{
                "type": "note",
                "detail": f"提示：该文件亦为其他 {file_hits[top_file.rel_path]-1} 个槽位的候选，"
                          f"但命名证据强，判定为✅",
            }]

        results.append(SlotResult(
            key=slot, label=COMPLETENESS_SPEC[slot]["label"],
            status=status, strength=round(top_strength, 2),
            matched_files=matched,
            evidence=ev_out[:6] + ([{"file": top_file.rel_path, "type": "shell",
                                    "detail": shell_note}] if shell_note else []),
            reason=shell_note or next((e["detail"] for e in top_ev
                                      if e.get("type") not in ("penalty", "note")), ""),
        ))

    n_ok = sum(1 for s in results if s.status == "✅")
    n_part = sum(1 for s in results if s.status == "⚠️")
    n_miss = sum(1 for s in results if s.status == "❌")
    score = (n_ok + 0.5 * n_part) / len(COMPLETENESS_ORDER)
    verdict = "✅ 齐全" if n_miss == 0 and n_part == 0 else (
        "⚠️ 部分缺失" if (n_ok + n_part) >= 3 else "❌ 严重缺失")

    return CompletenessResult(
        author=author, slots=results,
        n_present=n_ok, n_partial=n_part, n_missing=n_miss,
        score=round(score, 3), verdict=verdict,
        missing_labels=[s.label for s in results if s.status == "❌"],
        partial_labels=[s.label for s in results if s.status == "⚠️"],
        ambiguous=n_part > 0,
    )
