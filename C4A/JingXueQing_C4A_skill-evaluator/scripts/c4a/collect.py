"""Level 1 —— 文件采集与作者识别。

从 wechat-doc-mapper 拿来的部分：
    - 递归 inventory（rglob + 相对路径 + 大小 + 修改时间）
    - `^(Author)_(C\\d+)_(Part)$` 命名解析
    - 父文件夹名兜底
    - 未识别作者单列出来，不污染主流程

改造的部分：
    1. 只聚焦 C4（可--challenge 改），过滤掉无关文件但单独列进「非C4 文件」；
    2. 作者名支持中文（`姓名拼音_C4_xxx` 与 `张伟_C4_xxx` 都要认）；
    3. 识别 `_v2/_v3/最终版/final` 版本号，为 Level 4 的版本追踪做准备；
    4. 作者名归一化（去空格、大小写、常见变体合并）——原技能明确不合并，
       这里改进为「归一化 + 保留别名列表」，避免把一个人拆成三个人。
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from . import extract as extractor

# 姓名支持中英文；Challenge 支持 C4 / C4A / c4
# 作者段用「非贪婪 + 后顾」写法：作者名本身可能含连字符（Li-Ming），
# 但不能含下划线（下划线是字段分隔符）。
# 早先用贪婪的 [A-Za-z\-_.]{0,30}，遇到 Elite20TA_C4_skill-explainer 时
# 会一路吃到末尾导致整条正则失配（实测踩到，作者退化为 Unknown）。
NAMING_RE = re.compile(
    r"^(?P<author>[A-Za-z](?:[A-Za-z\-.]?[A-Za-z0-9]){0,29}|[\u4e00-\u9fff]{2,8})"
    r"[-_](?P<challenge>C\d{1,2}[A-Z]?)[-_](?P<part>.+)$",
    re.IGNORECASE,
)
# 文件名里任意位置出现 C4 标记（宽松召回）
LOOSE_C4_RE = re.compile(r"(^|[-_ ])C4[A-Z]?([-_ ]|$)", re.IGNORECASE)
VERSION_RE = re.compile(r"(?:^|[-_ ])v(?P<n>\d{1,2})(?=$|[-_ .])|第(?P<cn>[一二三四五六七八九十\d]+)版|final|最终版|终版", re.IGNORECASE)
SKIP_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

# 不值得做内容分析的后缀
NOISE_EXT = {".tmp", ".log", ".bak", ".swp", ".part", ".crdownload"}

# 附件型目录名：这些目录下的文件属于「提交的附属产物」，
# 不是独立作者。误判来源举例：samples/Demo_C4_AAR.md 里"Demo" 会被
# 当成作者名，凭空多出一位「demo 同学」。
ATTACHMENT_DIRS = {
    "samples", "sample", "demo", "demos", "example", "examples",
    "assets", "output", "outputs", "dist", "build", "reports",
    "docs", "doc", "reference", "references", "templates", "template",
    "截图", "录屏", "附件", "素材",
}

# 常见的"示例人名"——这些前缀出现在 _C4_ 前时，多半是模板而非真人
SAMPLE_AUTHOR_HINTS = {
    "demo", "sample", "example", "test", "testing", "user", "username",
    "yourname", "your", "name", "someone", "student", "template",
    "张三", "李四", "王五", "某某",
}

# 技能包内部的标准目录名（Claude Skill 规范：scripts/ references/ assets/）。
# 这些绝不可能是作者名——第一轮实测里"scripts" 凭空变成了四位作者。
STRUCTURE_DIRS = {
    "scripts", "references", "assets", "templates", "template", "bin", "lib",
    "src", "source", "docs", "doc", "images", "img", "media", "resources",
    "node_modules", "__pycache__", ".git", "tests", "test", "examples",
    "工作流", "脚本", "参考资料", "素材",
}

# 不可作为作者声明来源的扩展名
MEDIA_EXT = extractor.MEDIALIKE | extractor.IMAGELIKE
ARCHIVE_EXT = {".skill", ".zip", ".tar", ".gz", ".tgz"}


@dataclass
class FileInfo:
    rel_path: str
    abs_path: str
    name: str
    ext: str
    size_kb: float
    modified: str
    author: str = "Unknown"
    author_source: str = "未识别"
    part: str = ""
    version: Optional[int] = None
    is_c4: bool = False
    is_attachment: bool = False      # samples/ assets/ 等附属产物
    extract_kind: str = ""
    extract_ok: bool = False
    extract_note: str = ""
    n_chars: int = 0
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("abs_path", None)
        return d


@dataclass
class ScanResult:
    folder: str
    all_files: list[FileInfo]
    c4_files: list[FileInfo]
    by_author: dict[str, list[FileInfo]]
    unknown: list[FileInfo]
    non_c4: list[FileInfo]

    @property
    def n_authors(self) -> int:
        return len(self.by_author)

    def summary(self) -> dict:
        return {
            "folder": self.folder,
            "total_files": len(self.all_files),
            "c4_files": len(self.c4_files),
            "authors": self.n_authors,
            "unknown": len(self.unknown),
            "non_c4": len(self.non_c4),
        }


def normalize_author(name: str) -> str:
    """作者名归一化：去空格/全角、统一大小写、中文保持原样。"""
    if not name:
        return "Unknown"
    n = unicodedata.normalize("NFKC", name).strip()
    n = re.sub(r"\s+", "", n)
    n = re.sub(r"[_\-.]+$", "", n)
    if re.fullmatch(r"[A-Za-z\-]+", n):
        n = n.lower()
    return n or "Unknown"


def parse_version(part: str) -> Optional[int]:
    m = VERSION_RE.search(part)
    if not m:
        return None
    if m.group("n"):
        return int(m.group("n"))
    cn = m.group("cn")
    if cn:
        table = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                 "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
        if cn in table:
            return table[cn]
        if cn.isdigit():
            return int(cn)
    return 1  # final / 最终版


def is_c4_file(rel_path: str) -> bool:
    """宽松判断是否与 C4 相关。"""
    stem = Path(rel_path).stem
    return bool(LOOSE_C4_RE.search(stem) or LOOSE_C4_RE.search(rel_path))


def parse_filename(stem: str) -> dict | None:
    """解析 `姓名_挑战号_描述` 命名规范。

    注意：作者段用了贪婪的 `[A-Za-z\\-_.]{0,30}`，会把分隔用的 `_` 一起吃掉
    （`Demo_C4_AAR` → author=`Demo_`）。所以这里统一 strip 掉尾部 `_-.`，
    否则 `demo_` 匹配不上示例人名黑名单，会凭空多出一位「demo 同学」。
    这是第一轮实测抓到的真实bug。
    """
    m = NAMING_RE.match(stem)
    if not m:
        return None
    author = m.group("author").strip("_-.")
    if not author:
        return None
    return {
        "author": author,
        "challenge": m.group("challenge").upper(),
        "part": m.group("part"),
    }


def _is_sample_author(name: str) -> bool:
    n = name.strip("_-.").lower()
    return n in SAMPLE_AUTHOR_HINTS or n in _KNOWN_SKILL_NAMES


# 已知技能包名（运行时填充）：像 ai-log-forge/ 这种"以技能命名的目录"
# 不是人名。它是从 .skill 包名 / frontmatter name / 包内顶层目录收集来的。
_KNOWN_SKILL_NAMES: set[str] = set()


def register_skill_names(names) -> None:
    """把技能包名登记为「非人名」，供作者识别时排除。"""
    for n in names:
        if n:
            _KNOWN_SKILL_NAMES.add(str(n).strip().lower())


def _author_from_parent(rel_path: str) -> Optional[str]:
    """子文件夹按作者分组的情况：`ZhangWei/C4_xxx.md` 或 `张伟/C4_xxx.md`。

    两条排除规则（都是实测踩出来的坑）：
    1. 跳过技能包内部的标准目录名（scripts/ references/ assets/）——
       否则"scripts" 会被当成作者名，凭空多出 4 位"scripts 同学"。
    2. 目录名带 _src / _副本 / _v2 / -copy 等后缀的，是"某人的目录"而非"某人"，
       例如 wechat-doc-mapper_src。第一轮实测里它被当成了独立作者。
       真正的作者文件夹通常就是光杆的姓名（ZhangWei/、张伟/）。
    """
    parts = Path(rel_path).parts
    if len(parts) >= 2:
        # 从最靠近文件的一层往上找，跳过结构目录
        for parent in reversed(parts[:-1]):
            pl = parent.lower()
            if pl in STRUCTURE_DIRS:
                continue
            # 疑似"某人的副本目录"而非"某人"
            if re.search(r"[_\-](src|source|copy|副本|备份|backup|v\d+|final|"
                         r"old|tmp|temp)$", pl):
                break
            if re.fullmatch(r"[A-Za-z][A-Za-z\-_.]{0,30}", parent) or \
               re.fullmatch(r"[\u4e00-\u9fff]{2,8}", parent):
                if not _is_sample_author(parent):
                    return parent
            break   # 只看最近的一个非结构目录
    return None


def _author_from_header(rel_path: str, abs_path: str) -> tuple[Optional[str], str]:
    """从文件头部找作者：只认显式的「作者：/Author:」行，避免误伤。

    v1.1 修正：第一轮实测中，.skill 包内部的 YAML frontmatter `name: ai-log-forge`
    被当成了作者名，凭空造出「ai-log-forge 同学」。
    教训：技能包的 name字段是"技能叫什么"，不是"谁提交的"。
    所以这里只认带「作者/提交人/姓名/Author/Submitted by」字样的显式声明，
    且排除出现在包内部（路径含 .skill/.zip）的情况。
    """
    p = Path(abs_path)
    if p.suffix.lower() in MEDIA_EXT:
        return None, ""
    try:
        if p.stat().st_size > 2 * 1024 * 1024:
            return None, ""
        # 包内部的声明不可信——包内文档常是上游作者的
        if p.suffix.lower() in ARCHIVE_EXT or p.name.lower().endswith(".tar.gz"):
            return None, ""
        res = extractor.extract(p)
        if not res.ok:
            return None, ""
        for line in res.text.splitlines()[:12]:
            m = re.match(
                r"^\s*(?:作者|提交人|姓名|投稿人|Author|Submitted\s+by|Name)\s*[：:]\s*(.{1,30})$",
                line.strip(), re.IGNORECASE)
            if m:
                cand = m.group(1).strip().strip("*_# `-")
                if 1 < len(cand) <= 30 and not cand.startswith("http") \
                        and not _is_sample_author(cand):
                    return cand, f"文件头声明（{res.kind}）"
    except Exception:
        return None, ""
    return None, ""


def _in_attachment_dir(rel_path: str) -> bool:
    """判断文件是否位于 samples/ assets/ 这类附件目录下。"""
    parts = Path(rel_path).parts[:-1]
    return any(p.lower() in ATTACHMENT_DIRS for p in parts)


def scan(
    folder: str | Path,
    *,
    challenge: str = "C4",
    do_extract: bool = True,
    max_file_mb: int = 20,
) -> ScanResult:
    """扫描目录，按作者分组 C4 提交。"""
    folder = Path(folder).expanduser().resolve()
    if not folder.is_dir():
        raise NotADirectoryError(f"不是目录: {folder}")

    all_files: list[FileInfo] = []
    for f in sorted(folder.rglob("*")):
        if not f.is_file() or f.name.startswith(".") or f.name in SKIP_NAMES:
            continue
        if f.suffix.lower() in NOISE_EXT:
            continue
        rel = str(f.relative_to(folder))
        ext = f.suffix.lower()
        if f.name.lower().endswith(".tar.gz"):
            ext = ".tar.gz"
        try:
            st = f.stat()
        except OSError:
            continue
        fi = FileInfo(
            rel_path=rel, abs_path=str(f), name=f.name, ext=ext,
            size_kb=round(st.st_size / 1024, 1),
            modified=datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d"),
        )
        all_files.append(fi)

    c4_files: list[FileInfo] = []
    non_c4: list[FileInfo] = []
    attached: list[FileInfo] = []      # 归属明确但无 C4 标记的附属源码
    by_author: dict[str, list[FileInfo]] = defaultdict(list)
    unknown: list[FileInfo] = []
    # 记录「疑似真作者」线索，用于把附件目录归给正确的人
    author_evidence: dict[str, int] = defaultdict(int)

    # 预扫描：把 .skill 包名与包内 frontmatter 的 name 收集为「技能名」。
    # 目录名等于技能名时（ai-log-forge/），那是技能目录不是人。
    # 只收「像技能标识符」的名字（含连字符/下划线且不含 C4 标记）——
    # 早先版本把完整文件名也登记进去，结果 Elite20TA_C4_skill-explainer.skill
    # 自己把自己的作者给否掉了（实测踩到）。
    skill_names: set[str] = set()
    for fi in all_files:
        if fi.ext not in ARCHIVE_EXT and not fi.name.lower().endswith(".tar.gz"):
            continue
        try:
            r = extractor.extract(Path(fi.abs_path))
            for m in re.finditer(r"^name:\s*[\"']?([A-Za-z0-9_\-]{2,40})", r.text, re.M):
                cand = m.group(1)
                if not LOOSE_C4_RE.search(cand):
                    skill_names.add(cand)
            for member in r.meta.get("archive_members", []):
                top = Path(member).parts[0] if Path(member).parts else ""
                # 包内顶层目录名：像 wechat-doc-mapper / ai-log-forge
                if top and not LOOSE_C4_RE.search(top) and \
                        re.fullmatch(r"[A-Za-z][A-Za-z0-9_\-]{2,40}", top):
                    skill_names.add(top)
        except Exception:
            pass
    register_skill_names(skill_names)

    # 第一轮：先确定所有真作者（顶层规范命名文件的作者）
    prelim: list[tuple[FileInfo, str, str]] = []   # (fi, author, source)
    for fi in all_files:
        stem = Path(fi.name).stem
        parsed = parse_filename(stem)
        author = author_source = ""
        part = ""
        if parsed:
            got = parsed["challenge"]
            author_source = "文件名规范匹配"
            fi.is_c4 = got == challenge.upper() or got.startswith(challenge.upper())
            # 命中示例人名（Demo_C4_xxx）→ 不作为作者线索，但保留文件，
            # 交给附件目录归属逻辑处理（不能直接丢弃，否则文件凭空消失）。
            if not _is_sample_author(parsed["author"]):
                author, part = parsed["author"], parsed["part"]
        else:
            fi.is_c4 = is_c4_file(fi.rel_path)
            if fi.is_c4 and not _in_attachment_dir(fi.rel_path):
                pa = _author_from_parent(fi.rel_path)
                if pa:
                    author, author_source = pa, "父文件夹名"
        if author:
            author_evidence[normalize_author(author)] += 1
        prelim.append((fi, author, author_source))

    # 附件目录归属：samples/xxx.md → 归属于该目录下最可能的真作者
    # 规则：取「非附件目录下」出现次数最多的作者；只有一位时才归属，
    # 否则留在Unknown 交人工判断（宁可漏判，不可错判）。
    real_authors = [a for a, n in author_evidence.items() if n >= 2]
    fallback_author = max(real_authors, key=lambda a: author_evidence[a]) \
        if len(real_authors) == 1 else None

    # 提交目录归属：真实群文件夹里，每个人通常把交付物放进一个以自己命名的
    # 子目录（哪怕目录里的脚本/SKILL.md 没带 _C4_ 标记）。
    # 规则：若某个顶层子目录下的**带标记文件**明确指向同一位作者，
    # 则该目录下的无标记文件全部归给这位作者。
    # 这解决了「wechat-doc-mapper_src/scripts/xxx.py」这类源码目录的归属问题，
    # 避免 scripts / SKILL.md 变成独立"作者"。
    dir_owner: dict[str, str] = defaultdict(Counter)
    for fi, author, _src in prelim:
        if not author or not fi.is_c4:
            continue
        parts = Path(fi.rel_path).parts
        if len(parts) >= 2:
            dir_owner[parts[0]][author] += 1
    top_owner = {d: c.most_common(1)[0][0] for d, c in dir_owner.items()
                 if c and c.most_common(1)[0][1] >= 1}

    for fi, author, author_source in prelim:
        if not fi.is_c4:
            # 无标记文件：若它所在的顶层目录已明确属于某位作者，则继承该归属。
            # 这类文件不计入 c4_files（它们不是"五件套"候选），
            # 但会作为该作者的附属源码参与质量评审。
            parts = Path(fi.rel_path).parts
            if parts and parts[0] in top_owner:
                fi.author = normalize_author(top_owner[parts[0]])
                fi.author_source = "提交目录归属（按同目录带标记文件推断）"
                fi.is_c4 = False
                attached.append(fi)
            non_c4.append(fi)
            continue

        if not author and _in_attachment_dir(fi.rel_path) and fallback_author:
            # 沿用父目录所属作者（附件）
            author, author_source = fallback_author, "附件目录归属（按主提交推断）"

        if not author:
            # 提交目录归属：ai-log-forge/SKILL.md 这类"技能包目录下的文件"，
            # 其作者 = 该目录里带标记文件所指认的作者。
            parts = Path(fi.rel_path).parts
            if len(parts) >= 2:
                owner = dir_owner.get(parts[0])
                if owner:
                    author = owner.most_common(1)[0][0]
                    author_source = "提交目录归属（按同目录带标记文件推断）"

        if not author:
            author, note = _author_from_header(fi.rel_path, fi.abs_path)
            if author and not _is_sample_author(author):
                author_source = note
            else:
                author = ""

        if not author:
            author, author_source = "Unknown", "未识别（需人工确认）"
            unknown.append(fi)

        norm = normalize_author(author)
        fi.author = norm
        fi.author_source = author_source
        fi.part = part or Path(fi.name).stem
        fi.version = parse_version(fi.part)
        # 附件标记：samples/ 下的 Demo_C4_AAR.md 虽然属于该作者，
        # 但它不能充当「他交了AI 日志」的证据——那是模板不是他的产出。
        fi.is_attachment = _in_attachment_dir(fi.rel_path) or \
            bool(_is_sample_author(Path(fi.name).stem.split("_")[0]
                                   if "_" in fi.name else ""))
        c4_files.append(fi)
        by_author[norm].append(fi)

    # 合并 Unknown 到 by_author（不丢弃，只标记）
    if "unknown" not in by_author and unknown:
        by_author["unknown"] = unknown

    # 把归属明确的附属源码并入对应作者（参与质量评审，但不占五件套槽位）
    for fi in attached:
        by_author[fi.author].append(fi)

    if do_extract:
        for fi in c4_files + attached:
            if fi.size_kb > max_file_mb * 1024:
                fi.extract_note = f"文件 >{max_file_mb}MB，跳过内容分析"
                continue
            r = extractor.extract(Path(fi.abs_path))
            fi.extract_kind = r.kind
            fi.extract_ok = r.ok
            fi.extract_note = r.note
            fi.n_chars = r.n_chars
            fi.meta = r.meta

    return ScanResult(
        folder=str(folder), all_files=all_files, c4_files=c4_files,
        by_author={k: sorted(v, key=lambda x: x.name) for k, v in by_author.items()},
        unknown=unknown, non_c4=non_c4,
    )
