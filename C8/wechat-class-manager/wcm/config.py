"""配置加载：把 config/*.yaml 变成强类型对象，并统一路径。"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from .yamlite import load_file

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


KIND_CN = {
    "deliverable": "主交付物",
    "proposal": "项目申请书",
    "ailog": "AI 日志",
    "notes": "拿来说明",
    "aar": "AAR",
    "demo": "早期验证物",
}


def project_path(*parts: str) -> str:
    return os.path.join(ROOT, *parts)


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


@dataclass(frozen=True)
class Challenge:
    id: str
    name_cn: str
    name_en: str
    due: str | None = None
    required: tuple[str, ...] = ("deliverable", "ailog")
    keywords: tuple[str, ...] = ()

    @property
    def due_date(self) -> date | None:
        return date.fromisoformat(self.due) if self.due else None


@dataclass(frozen=True)
class Student:
    wxid: str
    nickname: str
    major: str = ""
    enrollment: str = ""
    is_real: bool = False
    aliases: tuple[str, ...] = ()


@dataclass
class Roster:
    students: dict[str, Student]

    def get(self, wxid: str) -> Student | None:
        return self.students.get(wxid)

    def by_nickname(self, nickname: str) -> Student | None:
        for s in self.students.values():
            if s.nickname == nickname:
                return s
        return None

    def resolve(self, key: str) -> Student | None:
        low = (key or "").strip().lower()
        for s in self.students.values():
            if low in {s.wxid.lower(), s.nickname.lower(), *[a.lower() for a in s.aliases]}:
                return s
        for s in self.students.values():
            if low and (low in s.nickname.lower() or s.nickname.lower() in low):
                return s
        return None

    def __len__(self) -> int:
        return len(self.students)


@dataclass
class Rules:
    silent_days: int = 7
    deadline_warn_days: int = 3
    low_submission_rate: float = 0.3
    question_unanswered_hours: int = 48
    engagement_drop_ratio: float = 0.5
    qa_min_quality: float = 0.35


@dataclass
class ClassConfig:
    group_name: str
    group_id: str
    aliases: tuple[str, ...]
    teacher_wxid: str
    teacher_nickname: str
    semester_start: str
    semester_end: str
    timezone: str
    rules: Rules
    roster: Roster
    challenges: dict[str, Challenge]
    challenge_order: tuple[str, ...]
    naming_regex: re.Pattern[str]
    kind_aliases: dict[str, set[str]] = field(default_factory=dict)

    def challenge(self, cid: str) -> Challenge | None:
        return self.challenges.get(cid)

    def resolve_challenge(self, text: str) -> Challenge | None:
        """把 'C4B' / 'c4b' / 'C4B 公众号' 解析成挑战。"""
        if not text:
            return None
        m = re.search(r"(?i)\bC(\d{1,2})([A-Z]{0,2})\b", text)
        if not m:
            return None
        cid = f"C{m.group(1)}{m.group(2).upper()}"
        return self.challenges.get(cid)

    def normalize_kind(self, raw: str) -> str:
        low = raw.strip().lower()
        for kind, aliases in self.kind_aliases.items():
            if low in {a.lower() for a in aliases}:
                return kind
        if "aar" in low:
            return "aar"
        if "ai" in low and "日志" in low:
            return "ailog"
        return "deliverable"


def load_config(config_dir: str | None = None) -> ClassConfig:
    cdir = config_dir or project_path("config")
    ch_raw = load_file(os.path.join(cdir, "challenges.yaml")) or {}
    g_raw = load_file(os.path.join(cdir, "group_config.yaml")) or {}

    challenges: dict[str, Challenge] = {}
    order: list[str] = []
    for item in ch_raw.get("challenges") or []:
        if not isinstance(item, dict) or "id" not in item:
            continue
        c = Challenge(
            id=str(item["id"]),
            name_cn=str(item.get("name_cn") or ""),
            name_en=str(item.get("name_en") or ""),
            due=item.get("due"),
            required=tuple(item.get("required") or ("deliverable", "ailog")),
            keywords=tuple(str(k) for k in (item.get("keywords") or ())),
        )
        challenges[c.id] = c
        order.append(c.id)

    naming = ch_raw.get("naming") or {}
    aliases_raw = naming.get("kind_aliases") or {}
    kind_aliases = {str(k): {str(x) for x in (v or [])} for k, v in aliases_raw.items()}

    g_group = g_raw.get("group") or {}
    teacher = g_raw.get("teacher") or {}
    sem = g_raw.get("semester") or {}
    rules_raw = g_raw.get("rules") or {}

    students: dict[str, Student] = {}
    for s in g_raw.get("roster") or []:
        if not isinstance(s, dict) or not s.get("wxid"):
            continue
        st = Student(
            wxid=str(s["wxid"]),
            nickname=str(s.get("nickname") or s["wxid"]),
            major=str(s.get("major") or ""),
            enrollment=str(s.get("enrollment") or ""),
            is_real=bool(s.get("is_real")),
            aliases=tuple(str(a) for a in (s.get("aliases") or ())),
        )
        students[st.wxid] = st

    return ClassConfig(
        group_name=str(g_group.get("name") or "群"),
        group_id=str(g_group.get("id") or "group"),
        aliases=tuple(str(a) for a in (g_group.get("aliases") or ())),
        teacher_wxid=str(teacher.get("wxid") or ""),
        teacher_nickname=str(teacher.get("nickname") or "老师"),
        semester_start=str(sem.get("start") or ""),
        semester_end=str(sem.get("end") or ""),
        timezone=str(sem.get("timezone") or "Asia/Shanghai"),
        rules=Rules(**{k: v for k, v in rules_raw.items() if hasattr(Rules, k)}),
        roster=Roster(students=students),
        challenges=challenges,
        challenge_order=tuple(order),
        naming_regex=re.compile(str(naming.get("regex") or r"^(?P<student>[^_/]+)_(?P<challenge>C\d+[A-Z]{0,2})_(?P<kind>[^_/]+)$")),
        kind_aliases=kind_aliases,
    )


def as_dict(obj: Any) -> Any:
    """给 JSON 输出用的轻量序列化。"""
    if hasattr(obj, "__dataclass_fields__"):
        return {k: as_dict(getattr(obj, k)) for k in obj.__dataclass_fields__}
    if isinstance(obj, (list, tuple)):
        return [as_dict(x) for x in obj]
    if isinstance(obj, dict):
        return {k: as_dict(v) for k, v in obj.items()}
    return obj
