#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_trace.py — 把「原始 AI 协作记录」解析成结构化 trace.json

作用：AI 日志最怕编造。这个脚本只做一件事——从真实记录里**抽取证据**：
  谁在第几轮说了什么、AI 用了哪些工具、哪些地方报错返工、prompt 是怎么一轮轮改的。
抽取出来的 trace.json 是后面 forge.py 生成日志/AAR 的唯一事实来源。

用法：
  python3 extract_trace.py --input <文件|目录> [--out trace.json] [--markdown]
  python3 extract_trace.py --input ~/.claude/projects/foo/xxx.jsonl

支持的输入格式：
  1. Claude Code 会话文件  *.jsonl   （每行一个 JSON 事件，type=user/assistant/summary）
  2. ChatGPT / Claude 导出 *.json    （递归查找 role + content 结构，兼容 mapping 树）
  3. 聊天记录的 *.md / *.txt          （按 "User:" / "Assistant:" / "我:" 等说话人标记切分）
  4. 目录                            （递归扫描上述类型，按修改时间排序合并）

只依赖 Python 3 标准库，无需 pip install。
输出：trace.json（turns / rounds / tool_events / stats / 迭代与失败信号）
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

MAX_BYTES = 25 * 1024 * 1024  # 单文件超过 25MB 就截断读取，避免卡死

USER_MARKERS = {
    "human", "user", "me", "用户", "我", "提问", "我问", "question",
}
ASSISTANT_MARKERS = {
    "assistant", "claude", "ai", "a.i.", "chatgpt", "gemini", "copilot",
    "gpt", "模型", "助手", "ai助手", "回答", "bot",
}

# 说话人标记行，例如 "## User:" / "**Human:**" / "我：xxx"
HEADER_RE = re.compile(
    r"^\s*(?:#{1,6}\s*)?(?:[*_>\-\s]*)"
    r"(?P<who>Human|User|Me|用户|我|提问|Assistant|Claude|AI|A\.I\.|ChatGPT|Gemini|"
    r"Copilot|GPT|模型|助手|AI助手|回答|Bot)"
    r"\s*(?:[*_#\s]*)\s*[:：]\s*(?P<rest>.*)$",
    re.IGNORECASE,
)

# 迭代 / 返工 / 修正信号：用户说了这类词，说明上一轮结果不满意，这是一次真实迭代
REFINE_RE = re.compile(
    r"再|重新|重做|改成|换成|不要|不对|错了|失败|报错|还是|换个|优化|改进|调整|补齐|"
    r"遗漏|漏了|补上|试一下|重试|修正|but|instead|redo|retry|fix|wrong|again|"
    r"change|refine|improve|update|not what|error|failed",
    re.IGNORECASE,
)

# 失败信号：AI 侧输出里出现这些，说明踩过坑
FAIL_RE = re.compile(
    r"traceback|exception|error:|failed|no such file|not found|permission denied|"
    r"语法错误|报错|失败|无法|缺失|超时|timeout|denied",
    re.IGNORECASE,
)

# 用户亲自动手信号：判断哪些活是人干的，不是 AI 干的
HUMAN_WORK_RE = re.compile(
    r"我(手动|自己|改了|重写|补了|删了|加了|检查|核对|确认|决定|选了|拍板)|"
    r"我(在|用|把)|\bi\s+(manually|edited|rewrote|checked|decided|chose|fixed)\b",
    re.IGNORECASE,
)


# --------------------------------------------------------------------------
# 内容展平：把各种乱七八糟的 content 结构统一成 (文本, 工具调用列表, 是否出错)
# --------------------------------------------------------------------------
def flatten_content(content):
    """返回 (text, tools, has_error)。tools 为工具名列表。"""
    text_parts = []
    tools = []
    has_error = False

    def walk(node):
        nonlocal has_error
        if node is None:
            return
        if isinstance(node, str):
            text_parts.append(node)
            return
        if isinstance(node, list):
            for item in node:
                walk(item)
            return
        if isinstance(node, dict):
            ntype = str(node.get("type", "")).lower()
            # 工具调用
            if ntype == "tool_use" or (ntype == "function_call" and node.get("name")):
                name = node.get("name") or node.get("tool") or "unknown"
                tools.append(str(name))
                return
            # 工具结果（可能带错误标记）
            if ntype in ("tool_result", "function_call_output", "toolresult"):
                if node.get("is_error") or node.get("isError"):
                    has_error = True
                walk(node.get("content"))
                return
            # 思考过程不进正文，避免污染
            if ntype in ("thinking", "redacted_thinking"):
                return
            if "text" in node and isinstance(node["text"], str):
                text_parts.append(node["text"])
                return
            if "parts" in node:
                walk(node["parts"])
                return
            if "content" in node:
                walk(node["content"])
                return
            # 兜底：把字符串类型的字段拼进来
            for k, v in node.items():
                if isinstance(v, str) and k in ("output", "result", "value", "data"):
                    text_parts.append(v)

    walk(content)
    return "\n".join(p for p in text_parts if p).strip(), tools, has_error


def norm_role(raw, fallback=None):
    r = str(raw or "").strip().lower()
    if r in ("user", "human", "用户", "我"):
        return "user"
    if r in ("assistant", "ai", "model", "gpt", "chatgpt", "claude", "助手"):
        return "assistant"
    if r in ("system", "tool", "function"):
        return "system"
    words = set(re.split(r"[\s:：]+", str(raw or "").strip().lower()))
    if words & USER_MARKERS:
        return "user"
    if words & ASSISTANT_MARKERS:
        return "assistant"
    return fallback


# --------------------------------------------------------------------------
# 解析器 1：JSONL（Claude Code 会话日志）
# --------------------------------------------------------------------------
def parse_jsonl(path, turns, sources):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue  # 坏行直接跳过，不中断整个解析
            if not isinstance(obj, dict):
                continue

            ts = obj.get("timestamp") or obj.get("ts") or obj.get("created_at")

            # Claude Code 结构：外层 type + message{role, content}
            msg = obj.get("message") if isinstance(obj.get("message"), dict) else obj
            role = norm_role(msg.get("role") or obj.get("type"))
            if role not in ("user", "assistant"):
                if obj.get("type") == "summary" and obj.get("summary"):
                    turns.append({"role": "system", "text": f"[会话摘要] {obj['summary']}", "ts": ts})
                continue

            content = msg.get("content")
            # 纯 tool_result 事件不是「人说话」，不能算一轮，但它的错误要归到当前轮
            ctypes = [str(c.get("type", "")) for c in content
                      if isinstance(c, dict)] if isinstance(content, list) else []
            is_tool_result = bool(ctypes) and all(
                t in ("tool_result", "function_call_output", "toolresult", "tool") for t in ctypes)

            text, tools, has_error = flatten_content(content)
            # 单独的 tool_result 事件（错误检测主要靠它）
            if not text and obj.get("toolUseResult"):
                _, _, has_error2 = flatten_content(obj.get("toolUseResult"))
                has_error = has_error or has_error2
            if not text and not tools:
                continue

            turns.append({
                "role": role,
                "text": text,
                "tools": tools,
                "error": has_error,
                "is_tool_result": is_tool_result,
                "ts": ts,
                "line": lineno,
            })
    sources.append({"file": str(path), "kind": "jsonl", "turns": len(turns)})


# --------------------------------------------------------------------------
# 解析器 2：JSON（ChatGPT / Claude 导出，递归找消息节点）
# --------------------------------------------------------------------------
def parse_json(path, turns, sources):
    before = len(turns)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        # 有些导出是 JSON Lines 伪装成 .json，退回逐行解析
        parse_jsonl(path, turns, sources)
        return

    found = []

    def walk(node):
        if isinstance(node, dict):
            msg = None
            if isinstance(node.get("message"), dict) and node["message"].get("role"):
                msg = node["message"]
            elif node.get("role") or (isinstance(node.get("author"), dict) and node["author"].get("role")):
                msg = node
            if msg is not None:
                role = norm_role(msg.get("role") or (msg.get("author") or {}).get("role"))
                if role in ("user", "assistant"):
                    content = msg.get("content")
                    if content is None:
                        content = msg.get("text")
                    text, tools, has_error = flatten_content(content)
                    ts = msg.get("create_time") or msg.get("created_at") or msg.get("timestamp")
                    if isinstance(ts, (int, float)):
                        ts = datetime.fromtimestamp(ts).isoformat(timespec="seconds")
                    if text or tools:
                        found.append({"role": role, "text": text, "tools": tools,
                                      "error": has_error, "ts": ts})
                    return  # 已消费，不再往里递归
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    # 去重（mapping 树可能重复引用同一节点）
    seen = set()
    for t in found:
        key = (t["role"], t["text"][:200])
        if key in seen:
            continue
        seen.add(key)
        turns.append(t)
    sources.append({"file": str(path), "kind": "json", "turns": len(turns) - before})


# --------------------------------------------------------------------------
# 解析器 3：Markdown / 纯文本（按说话人标记切分）
# --------------------------------------------------------------------------
def parse_text(path, turns, sources):
    before = len(turns)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw = f.read(MAX_BYTES)

    current_role = None
    buf = []

    def flush():
        if current_role and buf:
            text = "\n".join(buf).strip()
            if text:
                turns.append({"role": current_role, "text": text, "tools": [], "error": False})
        buf.clear()

    for line in raw.splitlines():
        m = HEADER_RE.match(line)
        if m:
            who = m.group("who")
            role = "user" if who.lower() in USER_MARKERS or who in ("我", "用户", "提问") else "assistant"
            if role != current_role:
                flush()
                current_role = role
            rest = m.group("rest").strip()
            if rest:
                buf.append(rest)
            continue
        # 分隔线 / 空行不打断当前段落
        if line.strip() in ("---", "***", "___"):
            continue
        if current_role is not None:
            buf.append(line)
    flush()
    sources.append({"file": str(path), "kind": "text", "turns": len(turns) - before})


# --------------------------------------------------------------------------
# 输入收集
# --------------------------------------------------------------------------
TEXT_EXT = {".jsonl", ".json", ".md", ".markdown", ".txt", ".log"}


def collect_files(target):
    p = Path(target).expanduser()
    if p.is_file():
        return [p]
    if p.is_dir():
        files = [f for f in p.rglob("*")
                 if f.is_file() and f.suffix.lower() in TEXT_EXT
                 and f.stat().st_size <= MAX_BYTES]
        return sorted(files, key=lambda f: f.stat().st_mtime)
    return []


def parse_any(path, turns, sources):
    ext = path.suffix.lower()
    if ext == ".jsonl":
        parse_jsonl(path, turns, sources)
    elif ext == ".json":
        parse_json(path, turns, sources)
    else:
        parse_text(path, turns, sources)


# --------------------------------------------------------------------------
# 统计与信号抽取
# --------------------------------------------------------------------------
def token_set(text, min_len=2, limit=400):
    """中英混排的分词：英文按词，中文按字符二元组（比单字更能反映"是不是在说同一件事"）。"""
    t = (text or "").lower()
    words = set(w for w in re.findall(r"[a-z0-9_]{2,}", t))
    han = re.findall(r"[\u4e00-\u9fff]", t)
    grams = {han[i] + han[i + 1] for i in range(len(han) - 1)} if len(han) > 1 else set(han)
    return (words | grams)


def preview(text, n=90):
    t = re.sub(r"\s+", " ", (text or "")).strip()
    return (t[:n] + "…") if len(t) > n else t


def build_rounds(turns):
    """把线性的 turns 折成「轮次」：一个 user turn 开启一轮，后面跟着的 assistant 归属该轮。"""
    rounds = []
    cur = None
    for t in turns:
        if t["role"] == "user":
            # 工具结果不是人的发言：并进当前轮，只贡献错误/工具证据
            if t.get("is_tool_result"):
                if cur is not None:
                    if t.get("error"):
                        cur["errors"].append(preview(t.get("text", ""), 120))
                    cur["tools"].extend(t.get("tools") or [])
                continue
            if cur:
                rounds.append(cur)
            cur = {
                "index": len(rounds) + 1,
                "ts": t.get("ts"),
                "user_text": t.get("text", ""),
                "user_chars": len(t.get("text", "")),
                "assistant_texts": [],
                "tools": [],
                "errors": [],
                "refine": bool(REFINE_RE.search(t.get("text", "") or "")),
                "human_work": bool(HUMAN_WORK_RE.search(t.get("text", "") or "")),
            }
        elif t["role"] == "assistant":
            if cur is None:  # 记录开头就是 assistant，补一个空轮
                cur = {"index": len(rounds) + 1, "ts": t.get("ts"), "user_text": "",
                       "user_chars": 0, "assistant_texts": [], "tools": [],
                       "errors": [], "refine": False, "human_work": False}
            cur["assistant_texts"].append(t.get("text", ""))
            cur["tools"].extend(t.get("tools", []) or [])
            if t.get("error"):
                cur["errors"].append(preview(t.get("text", ""), 120))
        elif t["role"] == "system":
            continue
    if cur:
        rounds.append(cur)

    # 补充统计字段
    for r in rounds:
        r["assistant_chars"] = sum(len(x) for x in r["assistant_texts"])
        r["tool_calls"] = len(r["tools"])
        r["assistant_preview"] = preview(" ".join(r["assistant_texts"]), 120)
        r["failed"] = bool(r["errors"]) or bool(FAIL_RE.search(" ".join(r["assistant_texts"])))
        # 正文里的工具痕迹（纯文本记录没有结构化工具事件时，从代码块/命令里猜）
        if not r["tools"]:
            cmds = re.findall(r"(?:^|\n)\s*\$\s+([a-zA-Z0-9_./\-]+)", " ".join(r["assistant_texts"]))
            if cmds:
                r["tools"] = [c.split()[0] for c in cmds][:10]
    return rounds


def prompt_evolution(rounds):
    """找出「同一件事反复改 prompt」的证据链：相邻轮 user 输入有中等相似度 = 迭代式追问。"""
    evo = []
    for a, b in zip(rounds, rounds[1:]):
        ta, tb = token_set(a["user_text"]), token_set(b["user_text"])
        if not ta or not tb:
            continue
        inter = len(ta & tb)
        union = len(ta | tb) or 1
        sim = inter / union
        # 判定：后一轮带了「重做/改成/不对」等修正信号，或与前一轮有明显措辞继承
        # 二者都说明「同一个目标被反复改写」，这就是 prompt 优化轨迹
        if b["refine"] or 0.15 <= sim <= 0.90:
            evo.append({
                "from_round": a["index"],
                "to_round": b["index"],
                "similarity": round(sim, 2),
                "kind": "渐进改写" if sim >= 0.15 else "追加新要求",
                "before": preview(a["user_text"], 140),
                "after": preview(b["user_text"], 140),
                # 优先展示英文标识符/报错名（比中文二元组可读），没有再退回二元组
                "new_tokens": ([w for w in sorted(tb - ta) if re.fullmatch(r"[a-z0-9_.]{2,}", w)][:8]
                               or sorted(tb - ta)[:6]),
            })
    return evo


def build_stats(turns, rounds):
    u = [t for t in turns if t["role"] == "user" and not t.get("is_tool_result")]
    a = [t for t in turns if t["role"] == "assistant"]
    tool_events = []
    for t in turns:
        for name in (t.get("tools") or []):
            tool_events.append({"round": None, "name": name})
    # 把工具事件挂回轮次
    for r in rounds:
        for name in r["tools"]:
            tool_events.append({"round": r["index"], "name": name})

    by_name = {}
    for e in tool_events:
        by_name[e["name"]] = by_name.get(e["name"], 0) + 1

    fail_rounds = [r["index"] for r in rounds if r["failed"]]
    refine_rounds = [r["index"] for r in rounds if r["refine"]]
    human_rounds = [r["index"] for r in rounds if r["human_work"]]

    ts_list = sorted([t["ts"] for t in turns if isinstance(t.get("ts"), str)] or [])
    return {
        "user_turns": len(u),
        "assistant_turns": len(a),
        "rounds": len(rounds),
        "user_chars_total": sum(len(t.get("text", "")) for t in u),
        "assistant_chars_total": sum(len(t.get("text", "")) for t in a),
        "avg_user_prompt_chars": round(sum(len(t.get("text", "")) for t in u) / len(u)) if u else 0,
        "tool_calls": len(tool_events),
        "tool_by_name": dict(sorted(by_name.items(), key=lambda kv: -kv[1])),
        "refine_rounds": refine_rounds,
        "failed_rounds": fail_rounds,
        "human_work_rounds": human_rounds,
        "first_ts": ts_list[0] if ts_list else None,
        "last_ts": ts_list[-1] if ts_list else None,
        "prompt_len_trend": [r["user_chars"] for r in rounds],
    }


def main():
    ap = argparse.ArgumentParser(
        description="把原始 AI 协作记录解析成结构化 trace.json（AI 日志的证据层）")
    ap.add_argument("--input", "-i", required=True, help="文件（.jsonl/.json/.md/.txt）或目录")
    ap.add_argument("--out", "-o", default="trace.json", help="输出 trace.json 路径")
    ap.add_argument("--markdown", action="store_true", help="额外打印人类可读的轮次摘要")
    args = ap.parse_args()

    files = collect_files(args.input)
    if not files:
        print(f"[错误] 没找到可解析的文件：{args.input}", file=sys.stderr)
        print("       支持的后缀：.jsonl（Claude Code 会话）、.json（对话导出）、.md / .txt（聊天记录）",
              file=sys.stderr)
        sys.exit(2)

    turns, sources = [], []
    for f in files:
        try:
            parse_any(f, turns, sources)
        except Exception as e:  # 单个文件炸了不能拖垮全局
            print(f"[警告] 跳过 {f}：{type(e).__name__}: {e}", file=sys.stderr)

    if not turns:
        print("[错误] 解析到了 0 条对话。请检查文件格式，或用 --input 指向正确的会话文件。",
              file=sys.stderr)
        sys.exit(3)

    rounds = build_rounds(turns)
    trace = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "input": str(args.input),
        "sources": sources,
        "stats": build_stats(turns, rounds),
        "rounds": rounds,
        "prompt_evolution": prompt_evolution(rounds),
    }

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(trace, f, ensure_ascii=False, indent=2)

    s = trace["stats"]
    print(f"[完成] trace.json -> {args.out}")
    print(f"       源文件 {len(sources)} 个 ｜ 轮次 {s['rounds']} ｜ "
          f"用户发言 {s['user_turns']} ｜ AI 回复 {s['assistant_turns']} ｜ "
          f"工具调用 {s['tool_calls']}")
    if s["tool_by_name"]:
        top = "、".join(f"{k}×{v}" for k, v in list(s["tool_by_name"].items())[:6])
        print(f"       工具分布：{top}")
    print(f"       迭代信号轮次：{s['refine_rounds'] or '无'}")
    print(f"       失败/返工轮次：{s['failed_rounds'] or '无'}")
    print(f"       prompt 优化链：{len(trace['prompt_evolution'])} 条")

    if args.markdown:
        print("\n--- 轮次摘要 ---")
        for r in rounds:
            flag = "🔁迭代" if r["refine"] else ""
            flag += " ❌失败" if r["failed"] else ""
            print(f"#{r['index']}{flag} [{r['tool_calls']} 工具] 我：{preview(r['user_text'], 70)}")


if __name__ == "__main__":
    main()
