"""
jd_insight.parser — JD 文本 → 能力标签命中

实现者：ChenYu（CS 方）
需求规格提出者：JingXueQing（非 CS 方）——见 docs/需求规格_v1.md

三个关键设计决策（都来自「踩过的坑」，见 AAR）
---------------------------------------------
1) 最长匹配优先 + 位置占用
   'Python' 既是 ENG01 也是 DAT06 的关键词，'数据分析' 是 DAT01 的上级词。
   若逐关键词独立扫描，'Python 数据分析' 会让两个标签双计并把总分虚高。
   做法：按关键词长度倒序遍历，命中后占用 [start, end) 区间，后续短关键词跳过已占区间。

2) 歧义消解靠「共现域信号」
   同一个关键词可能指向多个标签时，看句内还出现了哪些其他域的信号词：
   "用 Python 做数据清洗" → DAT06；"用 Python 写后端服务" → ENG01。
   这是 v0.3 才加上的，v0.2 用「谁 id 小算谁」导致 30% 的简历被误判为后端能力缺失。

3) 加分项降权在 parser 层完成，而不是 matcher 层
   因为「这句话在加分段落」是文本结构信息，parser 最清楚；
   matcher 只负责加权求和，不应关心段落。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from .taxonomy import KEYWORD_INDEX, TAG_INDEX, long_keywords

# 句子切分：中英文句末标点 + 分号 + 换行
_SENT_SPLIT = re.compile(r"[。！？!?；;\n\r]+")

# 加分段落信号：命中这些词的句子，其所含标签权重 ×0.5
_BONUS_MARKERS = ("加分", "优先", "更佳", "者优先", "尤佳", "nice to have", "plus")

# 歧义消解用的域信号词
_DOMAIN_HINTS: Dict[str, Tuple[str, ...]] = {
    "数据分析": ("数据", "清洗", "分析", "报表", "指标", "统计", "可视化", "pandas", "excel", "sql"),
    "工程基础": ("后端", "前端", "开发", "服务", "接口", "框架", "系统", "工程", "架构", "部署", "flask", "django"),
    "工具与平台": ("工具", "平台", "系统", "软件"),
}


@dataclass
class Hit:
    """一次关键词命中。保留原句是为了让报告可溯源——评审最反感"黑箱打分"。"""

    tag_id: str
    keyword: str
    sentence: str
    section: str  # "required" | "bonus"
    pos: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "tag_id": self.tag_id,
            "keyword": self.keyword,
            "sentence": self.sentence,
            "section": self.section,
            "pos": self.pos,
        }


@dataclass
class TagStat:
    tag_id: str
    count: int = 0
    required_count: int = 0
    bonus_count: int = 0
    sentences: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

    @property
    def weight_multiplier(self) -> float:
        """出现次数带来的边际增益，上限 2.0。第 4 次重复基本不再增加信息量。"""
        return min(2.0, 1.0 + 0.3 * (self.count - 1)) if self.count else 0.0

    def to_dict(self) -> Dict[str, object]:
        return {
            "tag_id": self.tag_id,
            "count": self.count,
            "required_count": self.required_count,
            "bonus_count": self.bonus_count,
            "sentences": self.sentences,
            "keywords": sorted(set(self.keywords)),
        }


def split_sentences(text: str) -> List[str]:
    """切成句子并去掉空句。保留标点前的序号用于稳定排序。"""
    if not text:
        return []
    parts = [p.strip() for p in _SENT_SPLIT.split(text)]
    return [p for p in parts if p]


def is_bonus_sentence(sentence: str) -> bool:
    low = sentence.lower()
    return any(m in low for m in _BONUS_MARKERS)


def _resolve_ambiguity(candidate_ids: List[str], sentence: str) -> str:
    """同一个关键词对应多个标签时，用句内共现信号投票。

    投票规则：每个候选标签所在域，若该句出现了域信号词则 +1 票。
    平票时退回 weight_default 最高者，再平票退回 id 字典序（保证确定性，便于测试）。
    """
    if len(candidate_ids) == 1:
        return candidate_ids[0]

    low = sentence.lower()
    votes: Dict[str, int] = {}
    for tid in candidate_ids:
        domain = TAG_INDEX[tid].domain
        hints = _DOMAIN_HINTS.get(domain, ())
        votes[tid] = sum(1 for h in hints if h in low)

    best = max(votes.values())
    tied = [tid for tid, v in votes.items() if v == best]
    if len(tied) == 1:
        return tied[0]

    tied.sort(key=lambda t: (-TAG_INDEX[t].weight_default, t))
    return tied[0]


def _accept_spans(low: str, sorted_kws: List[str]) -> List[Tuple[int, str]]:
    """同起点长词优先的贪心区间占用。

    为什么不能按关键词长度全局排序后再 find：那会让 pos 顺序丢失，
    报告里的证据句就会乱序，评审无法顺着 JD 原句核对。
    这里先把所有候选 span 找出来，再按 (start 升序, 长度降序) 贪心接受：
    同一位置必然先接受最长的词，跨位置的接受先出现者（阅读顺序友好）。
    """
    cands: List[Tuple[int, int, str]] = []
    for kw in sorted_kws:
        start = low.find(kw)
        while start != -1:
            cands.append((start, start + len(kw), kw))
            start = low.find(kw, start + 1)

    cands.sort(key=lambda c: (c[0], -(c[1] - c[0])))

    accepted: List[Tuple[int, int, str]] = []
    for start, end, kw in cands:
        if any(not (end <= s or start >= e) for s, e, _ in accepted):
            continue
        accepted.append((start, end, kw))

    accepted.sort(key=lambda c: c[0])
    return [(start, kw) for start, _end, kw in accepted]


def extract(text: str) -> List[Hit]:
    """抽取全部命中。返回按出现位置排序的列表。"""
    hits: List[Hit] = []
    sentences = split_sentences(text)
    sorted_kws = long_keywords(min_len=2)

    cursor = 0  # 全局字符偏移，用于跨句稳定排序
    for sentence in sentences:
        low = sentence.lower()
        ordered = _accept_spans(low, sorted_kws)
        section = "bonus" if is_bonus_sentence(sentence) else "required"

        for start, kw in ordered:
            candidates = KEYWORD_INDEX.get(kw, [])
            if not candidates:
                continue  # 被更长关键词覆盖，属预期内的丢弃
            tag_id = _resolve_ambiguity(candidates, sentence)
            hits.append(
                Hit(
                    tag_id=tag_id,
                    keyword=kw,
                    sentence=sentence,
                    section=section,
                    pos=cursor + start,
                )
            )

        cursor += len(sentence) + 1

    hits.sort(key=lambda h: h.pos)
    return hits


def aggregate(hits: List[Hit]) -> Dict[str, TagStat]:
    """把命中列表汇总成 tag_id -> TagStat。"""
    stats: Dict[str, TagStat] = {}
    for h in hits:
        st = stats.setdefault(h.tag_id, TagStat(tag_id=h.tag_id))
        st.count += 1
        if h.section == "bonus":
            st.bonus_count += 1
        else:
            st.required_count += 1
        st.keywords.append(h.keyword)
        if h.sentence not in st.sentences:
            st.sentences.append(h.sentence)
    return stats


def tag_ids(text: str) -> Set[str]:
    """只关心"有没有"时用这个，比 aggregate 快。"""
    return {h.tag_id for h in extract(text)}
