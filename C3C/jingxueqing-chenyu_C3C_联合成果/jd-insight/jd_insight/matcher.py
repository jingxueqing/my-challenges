"""
jd_insight.matcher — 需求向量 × 供给向量 → 匹配度与缺口

需求规格提出者：JingXueQing（非 CS 方）
业务校准依据：见 docs/权重校准_工商管理口径.md

打分公式（v1.2 定稿，改动需两人签字）
------------------------------------
    需求侧 w_i  = weight_default × 出现次数增益 × 段落系数，再归一化到 Σw=1
    供给侧 c_i  = 0（未命中）｜0.85（命中 1 次）｜1.0（命中 ≥2 次）
    total      = 100 × Σ(w_i × c_i)

为什么 c_i 要给 0.85 而不是二值：
校园简历里"听过/上过课"和"做过项目"在文本上都只出现一次，二值化会把二者等同；
把单次命中的满分设为 0.85，是为了让"重复出现/多处印证"能拉开差距，
同时又不至于让只写了一次的关键技能被判为零——这是最容易被滥用的地方，
所以我们选择"宁可系统性偏松，也不要系统性误杀"。

为什么段落系数是 0.5：
JD 的"加分项"段落平均只覆盖 15–25% 的实际要求（我们抽了 24 条样例 JD 人工核对），
若给 0.5 以上，会让"加分项齐全但硬门槛缺失"的候选人排名过高。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from . import parser as jd_parser
from .taxonomy import DOMAINS, TAG_INDEX, get_tag

BONUS_FACTOR = 0.5          # 加分段落系数
PRESENCE_ONCE = 0.85        # 命中 1 次的得分系数
HARD_GAP_THRESHOLD = 0.08   # 归一化权重 ≥ 该值的必需项，缺失即「硬缺口」
TECH_ROLE_MIN_ENG = 3       # 命中 ≥3 个工程基础标签即判定为技术岗


@dataclass
class TagScore:
    tag_id: str
    name: str
    domain: str
    weight: float          # 归一化后的需求权重
    coverage: float        # 0 / 0.85 / 1.0
    raw_weight: float      # 加权前的原始需求强度
    required_hits: int
    bonus_hits: int
    have_hits: int
    evidence: List[str] = field(default_factory=list)

    @property
    def is_hard_gap(self) -> bool:
        return self.coverage == 0.0 and self.required_hits > 0 and self.weight >= HARD_GAP_THRESHOLD

    @property
    def contribution(self) -> float:
        return self.weight * self.coverage

    def to_dict(self) -> Dict[str, object]:
        return {
            "tag_id": self.tag_id,
            "name": self.name,
            "domain": self.domain,
            "weight": round(self.weight, 4),
            "coverage": self.coverage,
            "required_hits": self.required_hits,
            "bonus_hits": self.bonus_hits,
            "have_hits": self.have_hits,
            "is_hard_gap": self.is_hard_gap,
            "evidence": self.evidence,
        }


@dataclass
class MatchResult:
    total: float
    role_type: str
    tags: List[TagScore]
    domain_scores: Dict[str, float]
    hard_gaps: List[TagScore]
    strengths: List[TagScore]
    advise: List[str]

    @property
    def grade(self) -> str:
        if self.total >= 80:
            return "强匹配"
        if self.total >= 65:
            return "可投"
        if self.total >= 45:
            return "需补短板"
        return "不建议投"

    def to_dict(self) -> Dict[str, object]:
        return {
            "total": round(self.total, 1),
            "grade": self.grade,
            "role_type": self.role_type,
            "domain_scores": {k: round(v, 1) for k, v in self.domain_scores.items()},
            "tags": [t.to_dict() for t in self.tags],
            "hard_gaps": [t.tag_id for t in self.hard_gaps],
            "strengths": [t.tag_id for t in self.strengths],
            "advise": self.advise,
        }


_ACTION_BY_DOMAIN: Dict[str, str] = {
    "业务与行业": "补一段能说清「这个行业谁付钱、钱怎么分」的 300 字分析，附一句你的判断",
    "数据分析": "用公开数据做一次完整分析（定口径→清洗→结论），把过程写成 1 页说明",
    "产品与需求": "把一个真实的小需求写成 PRD（含验收标准），让对方照着做一次，记录他卡住的地方",
    "沟通协作": "在简历里用「和谁、推进了什么、结果多少」的句式重写一条经历",
    "工程基础": "完成一个最小可运行程序并放进 Git 仓库，简历附仓库链接",
    "工具与平台": "做一次可展示的实操产物（一份看板 / 一个仓库 / 一份排版稿）",
}


def _need_vector(jd_text: str) -> Dict[str, TagScore]:
    """JD → 归一化需求向量。"""
    stats = jd_parser.aggregate(jd_parser.extract(jd_text))
    raw: Dict[str, float] = {}

    for tag_id, st in stats.items():
        tag = get_tag(tag_id)
        req_gain = min(2.0, 1.0 + 0.3 * (st.required_count - 1)) if st.required_count else 0.0
        bonus_gain = min(2.0, 1.0 + 0.3 * (st.bonus_count - 1)) if st.bonus_count else 0.0
        raw[tag_id] = tag.weight_default * (req_gain + BONUS_FACTOR * bonus_gain)

    total_raw = sum(raw.values())
    out: Dict[str, TagScore] = {}
    for tag_id, w in raw.items():
        tag = get_tag(tag_id)
        st = stats[tag_id]
        out[tag_id] = TagScore(
            tag_id=tag_id,
            name=tag.name,
            domain=tag.domain,
            weight=(w / total_raw) if total_raw else 0.0,
            coverage=0.0,
            raw_weight=w,
            required_hits=st.required_count,
            bonus_hits=st.bonus_count,
            have_hits=0,
            evidence=st.sentences[:2],
        )
    return out


def classify_role(jd_text: str) -> str:
    eng = [h for h in jd_parser.extract(jd_text) if TAG_INDEX[h.tag_id].domain == "工程基础"]
    return "技术岗" if len(eng) >= TECH_ROLE_MIN_ENG else "非技术岗/复合岗"


def match(jd_text: str, resume_text: str, explain: bool = True) -> MatchResult:
    """核心入口：单条 JD × 单份简历。"""
    need = _need_vector(jd_text)
    have_stats = jd_parser.aggregate(jd_parser.extract(resume_text))

    tags: List[TagScore] = []
    for tag_id, ts in need.items():
        st = have_stats.get(tag_id)
        hits = st.count if st else 0
        ts.have_hits = hits
        ts.coverage = 0.0 if hits == 0 else (PRESENCE_ONCE if hits == 1 else 1.0)
        if st and explain:
            ts.evidence = ts.evidence + st.sentences[:2]
        tags.append(ts)

    tags.sort(key=lambda t: (-t.weight, t.tag_id))

    total = 100.0 * sum(t.contribution for t in tags)

    domain_scores: Dict[str, float] = {}
    for d in DOMAINS:
        d_tags = [t for t in tags if t.domain == d]
        dw = sum(t.weight for t in d_tags)
        domain_scores[d] = (100.0 * sum(t.contribution for t in d_tags) / dw) if dw else 0.0

    hard_gaps = [t for t in tags if t.is_hard_gap]
    strengths = [t for t in tags if t.coverage == 1.0][:5]

    advise: List[str] = []
    for g in hard_gaps[:3]:
        action = _ACTION_BY_DOMAIN.get(g.domain, "补一份可展示的产出")
        advise.append(f"缺口「{g.name}」：{action}。")
    if not hard_gaps and total < 80:
        advise.append("硬门槛无缺失，分数主要丢在「命中深度」——把已有技能补上项目级证据即可提升。")
    if any(t.domain == "工具与平台" and t.coverage == 0 for t in tags):
        advise.append("工具类要求缺失优先级最低，可在入职后补，不要在简历里编造。")

    return MatchResult(
        total=total,
        role_type=classify_role(jd_text),
        tags=tags,
        domain_scores=domain_scores,
        hard_gaps=hard_gaps,
        strengths=strengths,
        advise=advise,
    )


def rank_jobs(resume_text: str, jobs: List[Dict[str, str]], top: Optional[int] = None) -> List[Dict[str, object]]:
    """简历 × 一批 JD，返回按适合度排序的排名。

    jobs 元素需含: id, company, title, jd_text
    """
    rows: List[Dict[str, object]] = []
    for job in jobs:
        r = match(job["jd_text"], resume_text, explain=False)
        rows.append(
            {
                "id": job.get("id", ""),
                "company": job.get("company", ""),
                "title": job.get("title", ""),
                "total": round(r.total, 1),
                "grade": r.grade,
                "role_type": r.role_type,
                "hard_gaps": [t.name for t in r.hard_gaps],
            }
        )
    rows.sort(key=lambda x: -float(x["total"]))
    return rows[:top] if top else rows
