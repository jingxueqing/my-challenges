#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""specs.py —— 挑战规格层：把官方 CHALLENGE.md 变成可执行的校验规则。

三层口径（全部写进 data/specs.json，可逐条追溯）：
  L1 自动抽取：只读官方文档里「交付物 / 需要提交什么」章节的表格行与命名清单行
  L2 归一化  ：把每个交付项映射到「槽位 slot」——同一件事在不同挑战里叫法不同
              （AI日志 / AI协作日志 / AI 使用全过程），统一归到 ai_log
  L3 人工补丁：抽不到或抽错的用 spec_patches.json 覆盖，每条必须写 reason

匹配时：文件名槽位 ∩ 交付项槽位 = 命中；精确 slug 命中优先级最高。
"""
from __future__ import annotations

import difflib
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "JingXueQing_C6A_数据"
CONFIG = json.loads((Path(__file__).resolve().parent / "config.json").read_text(encoding="utf-8"))
CHALLENGE_ROOT = Path(CONFIG["challenge_doc_root"])

NAME_TOKENS = r"(?:姓名|组名|你的名字|名字|YourName|yourname)"
CODE_SPAN = re.compile(r"`([^`]+)`")
LEADING_LINENO = re.compile(r"^(?:\d+\|)+")
SLUG_AFTER_NAME = re.compile(NAME_TOKENS + r"[A-Za-z0-9]*_(C\d+[A-Z]?)_(.+)$")
FILE_LIKE = re.compile(
    r"^[\*A-Za-z0-9_\u4e00-\u9fa5\.\-/]+\.(?:md|markdown|tex|bib|pdf|html|py|ipynb|xlsx|xls|csv|txt|png|jpg|jpeg|mp4|mov|zip|json|skill|docx|mp3|sh)$"
)
SECTION_HEADING = re.compile(r"^(#{1,6})\s*(.*)$")
DELIVERABLE_SECTION = re.compile(r"交付物|需要提交|必须提交|提交的内容|提交清单|要交什么|怎么交")
OPTIONAL_MARKERS = ("可选", "如有", "建议", "额外", "加分", "Level 3", "Level 4", "选做")
GENERIC_LABELS = {"必须", "可选", "建议", "必交", "交付物", "文件", "产出", "内容"}
BAD_PATTERN_MARKERS = ("内容描述", "示例", ".扩展名", "…", "....", "<", ">")

# ---------------------------------------------------------------- 槽位定义
# slot: (中文名, 交付项关键词正则, 文件名正则)   —— 顺序即优先级，具体在前
SLOTS: dict[str, tuple[str, str, str]] = {
    "readme": ("README", r"^readme|资料包说明", r"^readme(\.[a-z]+)?$|readme_提交说明"),
    "ai_log": ("AI日志", r"AI\s*日志|AI协作|AI\s*使用", r"AI\s*[-_]?\s*(协作)?\s*日志|AI_LOG|ai-log|ai_log|ailog"),
    "aar": ("AAR/复盘", r"AAR|复盘|反思报告", r"AAR|复盘|反思报告"),
    "attribution": ("拿来说明", r"拿来|借用说明|参考来源", r"拿来说明|拿来|借用说明|ATTRIBUTION"),
    "skill_doc": ("Skill说明", r"skill\s*说明|技能说明|说明文档", r"skill说明|技能说明"),
    "design": ("方案设计", r"方案(设计|草案)|proposal|架构|proposal", r"方案(设计|草案)|proposal"),
    "teaching": ("教学说明", r"教学(说明|记录)", r"教学(说明|记录)"),
    "validation": ("验证报告", r"验证|测试结果|正确性", r"验证报告|验证|测试结果"),
    "data": ("结构化数据", r"结构化数据|_data|数据（JSON", r"_data$|_data/|submissions\.json"),
    "dashboard": ("网站代码", r"网站代码|dashboard", r"dashboard"),
    "excel": ("Excel报表", r"excel|xlsx|报表", r"\.xlsx$"),
    "screenshots": ("截图", r"截图|screenshots|录屏", r"截图|screenshots|_screenshots$"),
    "demo": ("Demo/演示", r"demo|演示|录屏", r"demo"),
    "skill_pkg": ("技能包/代码", r"技能包|可运行|可安装|可执行|代码|技能文件|agent-skill|可执行内容", r"\.skill$|\.zip$|skill|技能|homework-solver|agent-skill|solver"),
    "output": ("输出产物", r"输出|output|生成的|pdf|地图|map", r"output|输出|map\.html|地图"),
    "paper": ("论文", r"论文|paper|技术报告", r"paper|report\.pdf|tech_report"),
    "bib": ("参考文献", r"bib|参考文献|引用库", r"\.bib$"),
    "article": ("文章/链接", r"文章|链接|repo|url|账号|仓库分析|发布", r"文章|链接|账号|仓库分析|repo"),
    "extra": ("补充材料", r"周产出|MVP|验证物|早期验证|系统架构|使用记录|消融|leaderboard|提交元数据|benchmark|日志|周报", r"mvp|_W\d|架构|usage|消融|leaderboard|submission|benchmark|ablation|统计"),
}


def norm_slot(text: str, kind: str) -> str | None:
    for slot, (_cn, label_re, file_re) in SLOTS.items():
        rx = label_re if kind == "label" else file_re
        if re.search(rx, text, re.IGNORECASE):
            return slot
    return None


def clean_line(line: str) -> str:
    prev = None
    while prev != line:
        prev = line
        line = LEADING_LINENO.sub("", line)
    return line


def challenge_id_from_dir(name: str) -> tuple[str, str] | None:
    m = re.match(r"挑战_(C\d+[A-Z]?)\s*(.*?)_(?:\w{6})?_?完整资料$", name)
    return (m.group(1), m.group(2).strip()) if m else None


def pick_pattern(text: str) -> str | None:
    for span in CODE_SPAN.findall(text):
        span = span.strip()
        if any(bad in span for bad in BAD_PATTERN_MARKERS) or " " in span:
            continue
        if SLUG_AFTER_NAME.search(span) or FILE_LIKE.match(span):
            return span
        if "*" in span and len(span) <= 32 and not span.startswith("*."):
            return span
    m = re.search(r"(" + NAME_TOKENS + r"[A-Za-z0-9]*_C\d+[A-Z]?_[^\s|]+)", text)
    return m.group(1).strip() if m else None


def humanize(slug: str) -> str:
    s = re.sub(r"\.(md|markdown|tex|bib|pdf|html|py|xlsx|txt|png|mp4|zip|json|skill|docx)$", "", slug, flags=re.I)
    return s.strip(" /") or slug


def parse_row(line: str, pattern: str) -> tuple[str, str, str]:
    """返回 (label, desc, raw)。表格取第一列做 label、第二列做 pattern、第三列做 desc。"""
    parts = [c.strip().strip("*` ") for c in line.strip().strip("|").split("|")]
    if "←" in line:
        desc = line.split("←", 1)[1].strip()
        m = SLUG_AFTER_NAME.search(pattern)
        label = humanize(m.group(2)) if m else humanize(pattern)
        return label, desc, line
    label = parts[0] if parts and parts[0] else humanize(pattern)
    desc = parts[-1] if len(parts) >= 3 else ""
    return label, desc, line


def build_item(desc_line: str, pattern: str, line_no: int) -> dict | None:
    label, desc, _ = parse_row(desc_line, pattern)
    label = re.sub(r"^[⚡📛🔗📦✅]\s*", "", label).strip()
    label = re.sub(r"[（(]必须[)）]", "", label).strip() or "交付物"
    if label in GENERIC_LABELS:
        label = humanize(slug or pattern) if (slug or pattern) else label
        if not re.search(r"[\u4e00-\u9fa5]", label) and desc:
            label = re.split(r"[，,（(、]", desc)[0].strip() or label
    slug, match_type = None, "glob"
    m = SLUG_AFTER_NAME.search(pattern)
    if m:
        slug = m.group(2).strip().rstrip("/")
        slug = re.sub(r"[（(]必须[)）]", "", slug).strip()
        slug = re.sub(r"姓名[AB]", "", slug).strip()
        match_type = "slug"
    if not re.search(r"[\u4e00-\u9fa5]", label) and desc:
        # 命名清单行只有英文 slug（data / dashboard / report），用中文说明当前缀更可读
        label = re.split(r"[，,（(、]", desc)[0].strip() or label
    required = not any(marker in desc_line or marker in label for marker in OPTIONAL_MARKERS)
    if "AI日志" in label or "AI 日志" in label:
        required = True
    slot = (norm_slot(slug, "file") if slug else "") or norm_slot(label, "label")
    if match_type == "glob" and slot in ("", "extra"):
        slot = norm_slot(pattern, "file") or slot or "misc"
    # 标签清洗：文件名直接当标签的去掉扩展名；占位符去掉；泛词用槽位中文名
    if label == pattern:
        label = humanize(pattern)
    label = re.sub(r"姓名[AB]", "", label).strip(" _-")
    label = re.sub(r"\.(md|markdown|pdf|png|jpe?g|mp4|xlsx|xls|tex|bib|zip|skill|html|json|txt|py)$", "", label, flags=re.I)
    if not label or label in GENERIC_LABELS:
        label = (SLOTS[slot][0] if slot in SLOTS else "") or humanize(pattern)
    return {
        "label": label[:30],
        "desc": desc[:80],
        "pattern": pattern,
        "match_type": match_type,
        "slug": slug,
        "slot": slot or "misc",
        "required": required,
        "source_line": line_no,
        "origin": "challenge_doc",
    }


def deliverable_sections(lines: list[str]) -> list[tuple[int, int]]:
    """返回交付物章节的行号区间（1-based，闭区间）。找不到就退化为全文。"""
    spans: list[tuple[int, int]] = []
    marks: list[tuple[int, int, str]] = []
    for idx, raw in enumerate(lines, 1):
        m = SECTION_HEADING.match(clean_line(raw).strip())
        if m:
            marks.append((idx, len(m.group(1)), m.group(2)))
    for pos, (idx, level, title) in enumerate(marks):
        if not DELIVERABLE_SECTION.search(title):
            continue
        end = len(lines)
        for nidx, nlevel, _t in marks[pos + 1:]:
            if nlevel <= level:
                end = nidx - 1
                break
        spans.append((idx, end))
    return spans or [(1, len(lines))]


def dedupe_items(items: list[dict]) -> list[dict]:
    """同一挑战内「槽位相同 + 标签近似」的条目只保留首条，避免同义重复计数。"""
    out: list[dict] = []
    for item in items:
        dup = False
        for idx, kept in enumerate(out):
            if kept["slot"] != item["slot"]:
                continue
            if difflib.SequenceMatcher(None, kept["label"], item["label"]).ratio() >= 0.6:
                dup = True
                # 同义条目里优先保留带「姓名_」命名规范的（更能代表该挑战的真实交付）
                if item["match_type"] == "slug" and kept["match_type"] == "glob":
                    out[idx] = item
                break
        if not dup:
            out.append(item)
    return out


def extract_from_markdown(path: Path, cid: str) -> list[dict]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    spans = deliverable_sections(lines)
    items: list[dict] = []
    seen_slug: dict[str, int] = {}
    seen_label: dict[str, int] = {}
    for span_start, span_end in spans:
        in_fence = False
        for line_no in range(span_start, span_end + 1):
            raw = clean_line(lines[line_no - 1])
            stripped = raw.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if not stripped or set(stripped.replace("|", "").strip()) <= set("-: "):
                continue
            if stripped.startswith(">"):
                continue
            pattern = pick_pattern(stripped)
            if not pattern:
                continue
            if not stripped.startswith("|") and not SLUG_AFTER_NAME.search(pattern):
                continue  # 非表格、也无姓名占位 → 多半是示例，跳过
            item = build_item(stripped, pattern, line_no)
            if not item:
                continue
            other = re.search(r"_(C\d+[A-Z]?)_", pattern)
            if other and other.group(1) != cid:
                continue  # 文档里混入了别的挑战的交付清单，丢弃
            key_slug = (item["slug"] or item["pattern"]).lower()
            key_label = item["label"].lower()
            if key_slug in seen_slug or key_label in seen_label:
                # 同名交付项只保留最先出现的一条（表格通常排在示例清单之前）
                continue
            seen_slug[key_slug] = line_no
            seen_label[key_label] = line_no
            items.append(item)
    return dedupe_items(items)


def load_patches() -> dict:
    p = Path(__file__).resolve().parent / "spec_patches.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def apply_patches(specs: dict, patches: dict) -> None:
    for cid, patch in patches.items():
        spec = specs.setdefault(
            cid,
            {"challenge_id": cid, "title": patch.get("title", cid), "source_file": patch.get("source_file", ""),
             "origin": "patch_only", "items": []},
        )
        if patch.get("title"):
            spec["title"] = patch["title"]
        for drop in patch.get("drop_labels", []):
            spec["items"] = [i for i in spec["items"] if i["label"] != drop]
        for extra in patch.get("add_items", []):
            if any((i["slug"] or i["pattern"]).lower() == extra["pattern"].lower() for i in spec["items"]):
                continue
            item = build_item(extra["pattern"], extra["pattern"], extra.get("source_line", 0))
            if not item:
                continue
            item.update({
                "label": extra["label"],
                "desc": extra.get("desc", ""),
                "required": extra.get("required", True),
                "slot": extra.get("slot") or item["slot"],
                "origin": "patch",
                "patch_reason": patch.get("reason", ""),
            })
            spec["items"].append(item)


def main() -> int:
    specs: dict[str, dict] = {}
    for folder in sorted(CHALLENGE_ROOT.glob("挑战_*")):
        doc = folder / "CHALLENGE.md"
        if not doc.exists():
            continue
        parsed = challenge_id_from_dir(folder.name)
        if not parsed:
            continue
        cid, title = parsed
        items = extract_from_markdown(doc, cid)
        if not items:
            continue
        specs[cid] = {"challenge_id": cid, "title": title, "source_file": str(doc),
                      "origin": "auto_extracted", "items": items}
    apply_patches(specs, load_patches())

    for cid, spec in specs.items():
        for item in spec["items"]:
            item["slot_cn"] = SLOTS.get(item["slot"], ("其他",))[0]
        spec["n_required"] = sum(1 for i in spec["items"] if i["required"])
        spec["n_items"] = len(spec["items"])
        if any(i["origin"] == "patch" for i in spec["items"]):
            spec["origin"] = "auto_extracted+patch"

    DATA.mkdir(parents=True, exist_ok=True)
    (DATA / "specs.json").write_text(json.dumps(specs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[specs] {len(specs)} 个挑战规格 → data/specs.json")
    for cid in sorted(specs, key=lambda x: (int(re.sub(r"\D", "", x) or 0), x)):
        s = specs[cid]
        print(f"  {cid:5s} {s['n_items']:2d} 项 / 必填 {s['n_required']:2d} | {s['title'][:30]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
