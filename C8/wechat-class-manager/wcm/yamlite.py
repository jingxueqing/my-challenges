"""yamlite — 一个零依赖的 YAML 子集解析器。

为什么自己写：
    项目要求 config/ 用 .yaml 给人手改（挑战定义、群配置），但整条流水线
    要能在「只有 Python 标准库」的机器上一键跑起来。为了不引入 PyYAML，
    这里只实现我们实际用到的那部分语法：

    支持：嵌套 map（缩进）、- 列表、列表内联 map、[a, b] 内联列表、
          引号字符串、int/float/bool/null、行内 # 注释
    不支持：锚点/别名、多文档、块标量（| >）、复杂 key

用法：
    from wcm.yamlite import load_file
    cfg = load_file("config/challenges.yaml")
"""

from __future__ import annotations

import re
from typing import Any


class YamlError(ValueError):
    pass


_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?$")


def _strip_comment(line: str) -> str:
    """去掉行内注释，但不动引号里的 #。"""
    out: list[str] = []
    quote: str | None = None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _split_inline(text: str) -> list[str]:
    """按逗号切分内联列表，忽略引号/括号里的逗号。"""
    parts: list[str] = []
    buf: list[str] = []
    depth = 0
    quote: str | None = None
    for ch in text:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch in "[{":
            depth += 1
            buf.append(ch)
        elif ch in "]}":
            depth -= 1
            buf.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    tail = "".join(buf).strip()
    if tail:
        parts.append(tail)
    return parts


def _scalar(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    low = text.lower()
    if low in ("null", "~"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        return [_scalar(p) for p in _split_inline(inner)] if inner else []
    if _INT_RE.match(text):
        return int(text)
    if _FLOAT_RE.match(text):
        return float(text)
    return text


def _is_pair(text: str) -> bool:
    """判断这段文本是不是 `key: value` 形式（排除 URL 之类）。"""
    if text.startswith(("[", "{", '"', "'")):
        return False
    idx = text.find(":")
    if idx <= 0:
        return False
    # `http://x` 这种冒号后面紧跟 // 的不算
    return not text[idx + 1:].startswith("//")


def _parse_block(lines: list[tuple[int, str]], i: int, indent: int) -> tuple[Any, int]:
    if i >= len(lines):
        return None, i
    if lines[i][1].startswith("-"):
        return _parse_list(lines, i, indent)
    return _parse_map(lines, i, indent)


def _parse_list(lines: list[tuple[int, str]], i: int, indent: int) -> tuple[list[Any], int]:
    items: list[Any] = []
    while i < len(lines) and lines[i][0] == indent and lines[i][1].startswith("-"):
        content = lines[i][1][1:].strip()
        if not content:
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                val, i = _parse_block(lines, i, lines[i][0])
            else:
                val = None
            items.append(val)
        elif _is_pair(content):
            # `- id: C1` → 把这一行改写成缩进 +2 的 map 首行
            lines[i] = (indent + 2, content)
            val, i = _parse_map(lines, i, indent + 2)
            items.append(val)
        else:
            items.append(_scalar(content))
            i += 1
    return items, i


def _parse_map(lines: list[tuple[int, str]], i: int, indent: int) -> tuple[dict[str, Any], int]:
    out: dict[str, Any] = {}
    while i < len(lines) and lines[i][0] == indent and not lines[i][1].startswith("-"):
        content = lines[i][1]
        key, _, rest = content.partition(":")
        key = key.strip().strip("\"'")
        rest = rest.strip()
        if not key:
            raise YamlError(f"第 {i + 1} 个有效行缺少 key：{content!r}")
        if rest:
            out[key] = _scalar(rest)
            i += 1
        else:
            i += 1
            if i < len(lines) and (lines[i][0] > indent or (lines[i][0] == indent and lines[i][1].startswith("-"))):
                val, i = _parse_block(lines, i, lines[i][0])
                out[key] = val
            else:
                out[key] = None
    return out, i


def load(text: str) -> Any:
    lines: list[tuple[int, str]] = []
    for raw in text.splitlines():
        cleaned = _strip_comment(raw)
        if not cleaned.strip():
            continue
        if cleaned.strip() in ("---", "..."):
            continue
        indent = len(cleaned) - len(cleaned.lstrip(" "))
        lines.append((indent, cleaned.strip()))
    if not lines:
        return None
    value, _ = _parse_block(lines, 0, lines[0][0])
    return value


def load_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return load(fh.read())
