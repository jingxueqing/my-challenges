"""jd-insight：岗位画像与匹配度分析（WorkBuddy 技能包的代码内核）。

联合产出 · C3C
- JingXueQing：能力标签体系、权重校准口径、验收标准（非 CS 方）
- ChenYu：模块拆分、算法实现、测试与打包（CS 方）

公开 API::

    from jd_insight import match, rank_jobs, render_report

    r = match(jd_text, resume_text)
    print(r.total, r.grade, [t.name for t in r.hard_gaps])
"""

from __future__ import annotations

__version__ = "1.2.0"

from . import matcher, parser, report, taxonomy  # noqa: E402
from .matcher import MatchResult, TagScore, classify_role, match, rank_jobs  # noqa: E402
from .taxonomy import DOMAINS, TAG_INDEX, all_tags, get_tag, stats  # noqa: E402

__all__ = [
    "__version__",
    "matcher",
    "parser",
    "report",
    "taxonomy",
    "MatchResult",
    "TagScore",
    "classify_role",
    "match",
    "rank_jobs",
    "DOMAINS",
    "TAG_INDEX",
    "all_tags",
    "get_tag",
    "stats",
]
