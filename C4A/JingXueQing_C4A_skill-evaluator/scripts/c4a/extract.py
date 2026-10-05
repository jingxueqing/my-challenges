"""文本抽取层——把各种格式的提交文件变成可检索的纯文本。

只用标准库实现，覆盖 C4 常见提交格式：
    .md/.txt/.py/.json/.yaml/.html/.tex/.csv  → 直接解码
    .docx                → zipfile + XML 文本抽取（标准库即可）
    .pptx                → 同上，抽取 <a:t> 文本
    .pdf                 → 优先 pypdf；无 pypdf 时降级为"仅文件名/元数据"
    .skill / .zip        →视为 tar.gz 包，抽取内部 SKILL.md / 源码
    图片/视频            → 不抽内容，只登记元数据

所有函数都返回 ExtractResult(text, ok, note)，
失败不抛异常——评审器必须在任何输入下都跑得完。
"""

from __future__ import annotations

import io
import json
import re
import tarfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# 单文件最多读多少字符进内存（防止极端大文件拖垮评审）
MAX_CHARS = 400_000
# 超过这个体积的文件跳过内容分析，只看文件名
MAX_BYTES = 20 * 1024 * 1024

TEXTLIKE = {
    ".md", ".markdown", ".txt", ".text", ".py", ".json", ".yaml", ".yml",
    ".html", ".htm", ".tex", ".bib", ".csv", ".tsv", ".log", ".jsonl",
    ".sh", ".js", ".ts", ".toml", ".cfg", ".ini", ".xml",
}
DOCLIKE = {".docx", ".pptx", ".docm"}
MEDIALIKE = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".mp3", ".wav", ".m4a"}
IMAGELIKE = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".tiff"}
ARCHIVELIKE = {".skill", ".zip", ".tar", ".gz", ".tgz", ".tar.gz"}

DECODE_CANDIDATES = ("utf-8", "utf-8-sig", "gb18030", "gbk", "big5", "latin-1")


@dataclass
class ExtractResult:
    """一次内容抽取的结果。ok=False 时 text 为空，note 说明原因。"""
    text: str = ""
    ok: bool = False
    note: str = ""
    kind: str = ""            # 归一化后的类型：md / docx / pdf / image / archive ...
    n_chars: int = 0
    meta: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "ok": self.ok, "note": self.note, "kind": self.kind,
            "n_chars": self.n_chars, **{f"meta_{k}": v for k, v in self.meta.items()},
        }


def _decode_bytes(raw: bytes) -> str:
    """多编码尝试解码。中文提交场景下 GB18030 兜底很关键。"""
    for enc in DECODE_CANDIDATES:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def _from_xml_zip(path: Path, member_globs: tuple[str, ...], tag_re: str) -> str:
    """从 OOXML 包（docx/pptx）里抽纯文本。标准库 zipfile + 正则即可。"""
    chunks: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        targets: list[str] = []
        for g in member_globs:
            targets.extend(n for n in names if g in n)
        for name in sorted(set(targets))[:40]:
            try:
                xml = zf.read(name).decode("utf-8", errors="replace")
            except KeyError:
                continue
            # 把段落/换行处塞进分隔符，避免相邻段落粘连成一个词
            xml = re.sub(r"</w:p>|</a:p>|</w:tr>", "\n", xml)
            texts = re.findall(tag_re, xml)
            if texts:
                chunks.append("\n".join(texts))
    return "\n".join(chunks)


def _docx_text(path: Path) -> str:
    # w:t = 文档文本 run；w:br = 换行
    return _from_xml_zip(path, ("word/document.xml", "word/footnotes.xml"), r"<w:t[^>]*>([^<]*)</w:t>")


def _pptx_text(path: Path) -> str:
    # a:t = 幻灯片文本
    return _from_xml_zip(path, ("ppt/slides/slide", "ppt/notesSlides/"), r"<a:t[^>]*>([^<]*)</a:t>")


def _pdf_text(path: Path) -> tuple[str, str]:
    """返回 (text, note)。优先 pypdf；没有就诚实降级。"""
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception:
        return "", "pypdf 未安装，PDF 仅按文件名/大小评估内容维度"
    try:
        reader = PdfReader(str(path))
        n = min(len(reader.pages), 30)
        parts = []
        for i in range(n):
            parts.append(reader.pages[i].extract_text() or "")
        meta = {}
        try:
            if reader.metadata:
                meta = {k.lstrip("/"): str(v) for k, v in reader.metadata.items() if v}
        except Exception:
            pass
        return "\n".join(parts)[:MAX_CHARS], f"pypdf 抽取 {n} 页"
    except Exception as exc:  # 损坏的 PDF 不应中断整体评审
        return "", f"PDF 解析失败({type(exc).__name__})，降级为仅文件名评估"


def _archive_text(path: Path) -> tuple[str, str, dict]:
    """解开 .skill / .zip 包，抽取内部文档与源码。返回 (text, note, meta)。"""
    meta: dict = {}
    chunks: list[str] = []
    names: list[str] = []
    try:
        if tarfile.is_tarfile(path):
            with tarfile.open(path) as tf:
                for m in tf.getmembers():
                    if not m.isfile():
                        continue
                    names.append(m.name)
                    if m.size > MAX_BYTES:
                        continue
                    if not Path(m.name).suffix.lower() in TEXTLIKE | {".skill"}:
                        continue
                    f = tf.extractfile(m)
                    if f is None:
                        continue
                    chunks.append(f"--- [{m.name}] ---\n" + _decode_bytes(f.read())[:MAX_CHARS])
            note = f"tar 包，{len(names)} 个成员"
        elif zipfile.is_zipfile(path):
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                for name in names[:80]:
                    if Path(name).suffix.lower() not in TEXTLIKE:
                        continue
                    try:
                        data = zf.read(name)
                    except Exception:
                        continue
                    if len(data) > MAX_BYTES:
                        continue
                    chunks.append(f"--- [{name}] ---\n" + _decode_bytes(data)[:MAX_CHARS])
            note = f"zip 包，{len(names)} 个成员"
        else:
            return "", "非tar/zip 格式，按文件名评估", meta
    except Exception as exc:
        return "", f"包解析失败({type(exc).__name__})，降级为仅文件名评估", meta

    meta["archive_members"] = names[:60]
    meta["has_skill_md"] = any(Path(n).name == "SKILL.md" for n in names)
    meta["member_count"] = len(names)
    return "\n".join(chunks)[:MAX_CHARS], note, meta


def extract(path: Path) -> ExtractResult:
    """抽取单个文件的内容。任何异常都不外抛。"""
    path = Path(path)
    ext = path.suffix.lower()
    # 复合扩展名 .tar.gz
    if path.name.lower().endswith(".tar.gz"):
        ext = ".tar.gz"

    try:
        size = path.stat().st_size
    except OSError as exc:
        return ExtractResult(note=f"无法访问({type(exc).__name__})", kind=ext)

    if size > MAX_BYTES:
        return ExtractResult(
            note=f"文件过大({size/1024/1024:.1f}MB)，跳过内容分析", kind=ext
        )

    try:
        # --- 媒体/图片：只登记，不抽内容 ---
        if ext in MEDIALIKE or ext in IMAGELIKE:
            kind = "video" if ext in MEDIALIKE else "image"
            dim = ""
            if ext in IMAGELIKE and ext != ".svg":
                dim = _image_size(path)
            return ExtractResult(
                ok=True, kind=kind, note=f"{kind} 文件，{size/1024:.0f}KB{dim}",
                meta={"size_kb": round(size / 1024, 1), **( {"dim": dim} if dim else {} )},
            )

        # --- 包 ---
        if ext in ARCHIVELIKE:
            text, note, meta = _archive_text(path)
            kind = "archive"
            return ExtractResult(
                text=text, ok=bool(text), kind=kind, note=note,
                n_chars=len(text), meta=meta,
            )

        # --- Office ---
        if ext in DOCLIKE:
            text = _docx_text(path) if ext == ".docx" else _pptx_text(path)
            text = text[:MAX_CHARS]
            return ExtractResult(
                text=text, ok=bool(text.strip()),
                kind="docx" if ext == ".docx" else "pptx",
                note=f"OOXML 抽取 {len(text)} 字符", n_chars=len(text),
            )

        # --- PDF ---
        if ext == ".pdf":
            text, note = _pdf_text(path)
            return ExtractResult(
                text=text, ok=bool(text.strip()), kind="pdf",
                note=note, n_chars=len(text),
            )

        # --- 纯文本家族 ---
        if ext in TEXTLIKE or ext == "":
            raw = path.read_bytes()
            text = _decode_bytes(raw)[:MAX_CHARS]
            kind = ext.lstrip(".") or "txt"
            return ExtractResult(
                text=text, ok=bool(text.strip()), kind=kind,
                note=f"文本抽取 {len(text)} 字符", n_chars=len(text),
            )

        # --- 未知二进制：只登记 ---
        return ExtractResult(
            ok=False, kind="binary",
            note=f"未知二进制格式 {ext or '(无扩展名)'}，仅按文件名评估",
            meta={"size_kb": round(size / 1024, 1)},
        )
    except Exception as exc:  # 兜底：任何单文件失败都不应中断整体评审
        return ExtractResult(note=f"抽取异常({type(exc).__name__})", kind=ext)


def _image_size(path: Path) -> str:
    """只读文件头拿宽高，不引入 PIL 依赖。"""
    try:
        with open(path, "rb") as f:
            head = f.read(32)
            if head[:8] == b"\x89PNG\r\n\x1a\n":
                w = int.from_bytes(head[16:20], "big")
                h = int.from_bytes(head[20:24], "big")
                return f" {w}x{h}"
            if head[:2] == b"\xff\xd8":
                return " (jpeg)"
    except Exception:
        pass
    return ""


def content_of(paths: list[Path]) -> tuple[str, list[ExtractResult]]:
    """批量抽取，返回 (合并文本, 逐文件结果)。

    合并文本里每个文件都带一个哨兵头，这样上层能把"命中信号"
    精确定位回源文件与行号。
    """
    results: list[ExtractResult] = []
    blocks: list[str] = []
    for p in paths:
        r = extract(p)
        results.append(r)
        if r.text.strip():
            blocks.append(f"\n=== FILE: {p.name} ===\n{r.text}")
    return "\n".join(blocks), results
