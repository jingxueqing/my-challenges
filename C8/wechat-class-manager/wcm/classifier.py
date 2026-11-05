"""L2 消息分类器（规则 + 上下文 + 可选 LLM 精分类）。

为什么不用纯 LLM：
    群消息一天几百条，全量过 LLM 成本高、还慢；而 80% 的消息靠结构与关键词就能判。
    所以默认走「打分规则 + 上下文」，只有置信度低的消息才建议交给 LLM 复核
    （--llm-review，需要设置 WCM_LLM_BASE / WCM_LLM_KEY）。

为什么用打分而不是 if-else：
    if-else 的判定顺序会成为隐形的优先级，改一条规则经常把别的类改坏。
    每个意图独立累计证据分数再取最大值，加规则时影响面可控，
    而且每条判定都能说出「凭什么」——signals 字段就是给老师看的原因。
"""

from __future__ import annotations

import json
import math
import re
from datetime import datetime
from typing import Any, Iterable

INTENTS = ("submission", "question", "answer", "discussion", "announcement", "resource", "social")

INTENT_CN = {
    "submission": "提交",
    "question": "提问",
    "answer": "回答",
    "discussion": "讨论",
    "announcement": "通知",
    "resource": "资源",
    "social": "闲聊",
}

_QUESTION_MARK = re.compile(r"[？?]\s*$")
_QUESTION_WORDS = (
    "请问", "问一下", "问个", "求助", "不懂", "卡住", "怎么办", "怎么", "如何", "为什么",
    "能不能", "可以吗", "有没有", "是不是", "算不算", "要不要", "到底", "哪个", "哪里", "多少",
)
_ANNOUNCE_WORDS = ("通知", "提醒", "截止", "周会", "预警", "进度", "总结", "规范", "模板", "@所有人", "议题")
_OPINION_WORDS = ("我觉得", "我认为", "我的理解", "其实", "感觉", "原因", "方案", "思路", "结论", "踩过", "试了", "应该是")
_SOCIAL_WORDS = ("收到", "谢谢", "好的", "哈哈", "晚安", "已提交", "懂了", "明白了", "学到了", "先睡", "emmm", "谢谢老师", "收到，", "抄作业")
_ANSWER_STARTS = ("要", "可以", "不行", "别", "用", "换", "大概率", "确实", "是的", "改了", "加了", "建议", "公开的", "私有的", "算", "不用", "得")
_ANSWER_HINTS = ("应该是", "一般来说", "我用的", "改成", "填", "设", "安装", "装", "报错", "配置")
_FILE_EXT = re.compile(r"\.(md|pdf|docx?|xlsx?|pptx?|zip|rar|7z|py|ipynb|mp4|png|jpe?g|skill|tex|json|csv)$", re.I)
_URL = re.compile(r"https?://\S+")
_CHALLENGE_TOKEN = re.compile(r"(?i)(?<![A-Za-z])C\d{1,2}[A-Z]{0,2}(?![A-Za-z])")


def _parse_ts(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return datetime(1970, 1, 1)


def _scores(msg: dict[str, Any], ctx: dict[str, Any]) -> tuple[dict[str, float], list[str]]:
    """返回 {intent: score} 和触发的证据。"""
    content = msg.get("content") or ""
    mtype = msg.get("type") or "text"
    text = content.strip()
    low = text.lower()
    is_teacher = msg["sender"]["wechat_id"] == ctx["teacher_wxid"]
    signals: list[str] = []

    s = {k: 0.0 for k in INTENTS}

    def add(intent: str, score: float, why: str) -> None:
        s[intent] += score
        if why:
            signals.append(f"{intent}:{why}")

    # ---- submission ----
    if mtype == "file":
        name = text
        if ctx["naming_regex"].match(name):
            add("submission", 6, "文件名符合 姓名_挑战ID_内容 规范")
        elif _CHALLENGE_TOKEN.search(name):
            add("submission", 4, "文件名含挑战ID")
        elif _FILE_EXT.search(name):
            add("submission", 2, "文件消息")
        else:
            add("submission", 1, "文件消息")
        if is_teacher:
            add("announcement", 3, "老师发的文件（课件/模板）")
            add("submission", -4, "老师发的文件不算学生提交")
    else:
        add("submission", -3, "非文件消息")
    if "提交" in text and mtype != "file":
        add("submission", 0.5, "提到提交")

    # ---- announcement ----
    if is_teacher:
        if any(w in text for w in _ANNOUNCE_WORDS):
            add("announcement", 6, "老师+通知用语")
        else:
            add("announcement", 2, "老师发言")
        if text.startswith("【"):
            add("announcement", 2, "【】标题")
    else:
        add("announcement", -4, "非老师")
    if mtype == "system":
        add("announcement", 5, "系统消息")

    # ---- question ----
    if _QUESTION_MARK.search(text):
        add("question", 4, "问号结尾")
    elif "？" in text or "?" in text:
        add("question", 2.5, "句中出现问号")
    hits = [w for w in _QUESTION_WORDS if w in text]
    if any(w in text for w in ("一起", "讨论下", "讨论一下")):
        add("question", -1.2, "邀请式讨论")
    if hits:
        add("question", min(1.5 * len(hits), 4.5), f"疑问词 {hits[0]}")
    if text.endswith("吗") or text.endswith("吧？"):
        add("question", 1, "语气疑问")
    if any(w in text for w in ("报错", "找不到", "失败", "装不上", "跑不通", "起不来", "一直提示")):
        add("question", 2.5, "报错求助")
        add("discussion", -1, "报错求助更像提问")
    if is_teacher:
        add("question", -2, "老师提问少见")
    if mtype == "file":
        add("question", -1.5, "文件消息不像提问")

    # ---- answer ----
    parent_is_question = ctx["parent_is_question"].get(msg["msg_id"], False)
    if parent_is_question:
        add("answer", 6, "引用了提问")
    prev_q_same_thread = ctx["after_question"].get(msg["msg_id"], False)
    if prev_q_same_thread:
        add("answer", 3.5, "时间窗内紧跟提问")
    if text.startswith(_ANSWER_STARTS) and len(text) >= 6:
        add("answer", 1.5, "答案式开头")
    if any(h in text for h in _ANSWER_HINTS) and len(text) >= 10:
        add("answer", 1, "含操作建议")
    if _QUESTION_MARK.search(text):
        add("answer", -2.5, "结尾是问号")
    if mtype == "file":
        add("answer", -2, "文件消息")

    # ---- resource ----
    if _URL.search(text):
        add("resource", 5, "含链接")
    if text.startswith("分享") or "分享一个" in text:
        add("resource", 5.5, "分享标记")
    if mtype == "link":
        add("resource", 2, "链接卡片")
    if _QUESTION_MARK.search(text):
        add("resource", -3, "问句里的链接不算资源分享")

    # ---- discussion ----
    if any(w in text for w in _OPINION_WORDS):
        add("discussion", 2.5, "观点标记")
    if len(text) >= 30:
        add("discussion", 1.2, "长文本")
    if msg.get("reply_to") and not parent_is_question:
        add("discussion", 1.5, "接在讨论里")
    if text.startswith("我") and len(text) >= 8:
        add("discussion", 0.8, "第一人称叙述")
    if _QUESTION_MARK.search(text):
        add("discussion", -2, "问号结尾")
    if mtype == "file":
        add("discussion", -2, "文件消息")

    # ---- social ----
    if len(text) <= 10 and any(w in text for w in _SOCIAL_WORDS):
        add("social", 4, "短寒暄")
    elif any(w in text for w in _SOCIAL_WORDS) and len(text) <= 20 and not _QUESTION_MARK.search(text):
        add("social", 2, "寒暄/确认")
    if len(text) <= 6:
        add("social", 1.5, "极短")
    if any(w in text for w in ("潜水", "请假", "家里有事", "考证", "课程冲突", "放慢", "放缓")):
        add("social", 3, "状态说明")
        add("discussion", -1.5, "状态说明不算讨论")
    if any(w in text for w in ("抄作业", "学到了", "收到", "明白了", "懂了", "谢谢")):
        add("social", 3.5, "确认/致谢")
    if "哈哈" in text or "emmm" in text or "～" in text:
        add("social", 1, "语气词")
    if len(text) >= 25:
        add("social", -3, "长文本不是闲聊")

    return s, signals


def _argmax(scores: dict[str, float]) -> tuple[str, float, float]:
    """返回 (intent, confidence, margin)。confidence 用 softmax，margin 是第一名与第二名差。"""
    ordered = sorted(scores.items(), key=lambda kv: -kv[1])
    top, second = ordered[0], ordered[1]
    exps = {k: math.exp(v / 2.0) for k, v in scores.items()}  # 温度 2，避免过度自信
    total = sum(exps.values())
    conf = exps[top[0]] / total
    return top[0], min(conf, 0.99), top[1] - second[1]


def build_context(messages: list[dict[str, Any]], cfg) -> dict[str, Any]:
    """先把上下文建起来：谁引用谁、谁紧跟谁的提问。"""
    by_id = {m["msg_id"]: m for m in messages}
    # 第一遍：只判断"像不像提问"，用来给 answer 提供父消息信息
    rough: dict[str, Any] = {"teacher_wxid": cfg.teacher_wxid, "naming_regex": cfg.naming_regex,
                             "parent_is_question": {}, "after_question": {}}
    question_like: set[str] = set()
    for m in messages:
        s, _ = _scores(m, rough)
        if max(s, key=s.get) == "question" and s["question"] > 0:
            question_like.add(m["msg_id"])

    parent_is_question: dict[str, bool] = {}
    after_question: dict[str, bool] = {}
    prev: dict[str, Any] | None = None
    for m in messages:
        parent = by_id.get(m.get("reply_to") or "")
        parent_is_question[m["msg_id"]] = bool(parent and parent["msg_id"] in question_like)
        if prev is not None:
            gap = (_parse_ts(m["timestamp"]) - _parse_ts(prev["timestamp"])).total_seconds()
            after_question[m["msg_id"]] = (
                prev["msg_id"] in question_like
                and 0 <= gap <= 3600
                and prev["sender"]["wechat_id"] != m["sender"]["wechat_id"]
            )
        else:
            after_question[m["msg_id"]] = False
        prev = m

    return {
        "teacher_wxid": cfg.teacher_wxid,
        "naming_regex": cfg.naming_regex,
        "parent_is_question": parent_is_question,
        "after_question": after_question,
        "question_like": question_like,
    }


def classify_batch(messages: list[dict[str, Any]], cfg, llm_review=None) -> list[dict[str, Any]]:
    ctx = build_context(messages, cfg)
    out: list[dict[str, Any]] = []
    for m in messages:
        scores, signals = _scores(m, ctx)
        intent, conf, margin = _argmax(scores)
        row = {
            **m,
            "intent": intent,
            "intent_cn": INTENT_CN[intent],
            "confidence": round(conf, 3),
            "margin": round(margin, 2),
            "signals": signals,
            "scores": {k: round(v, 2) for k, v in sorted(scores.items(), key=lambda kv: -kv[1]) if v != 0},
            "needs_review": conf < 0.45 or margin < 0.5,
        }
        if llm_review and row["needs_review"]:
            try:
                reviewed = llm_review(m)
                if reviewed in INTENTS:
                    row["intent_rule"] = intent
                    row["intent"] = reviewed
                    row["intent_cn"] = INTENT_CN[reviewed]
                    row["reviewed_by"] = "llm"
            except Exception as exc:  # noqa: BLE001 - LLM 不可用时要能继续跑
                row["review_error"] = str(exc)[:120]
        out.append(row)
    return out


def evaluate(predicted: list[dict[str, Any]], gold: list[dict[str, Any]]) -> dict[str, Any]:
    """对照人工标注算准确率、混淆矩阵、每类 P/R/F1。"""
    gold_map = {g["msg_id"]: g["intent"] for g in gold}
    pairs = [(p["msg_id"], p["intent"], gold_map[p["msg_id"]]) for p in predicted if p["msg_id"] in gold_map]
    total = len(pairs)
    correct = sum(1 for _, p, g in pairs if p == g)
    confusion = {g: {p: 0 for p in INTENTS} for g in INTENTS}
    for _, p, g in pairs:
        confusion[g][p] += 1

    per_class = {}
    for k in INTENTS:
        tp = sum(1 for _, p, g in pairs if p == k and g == k)
        fp = sum(1 for _, p, g in pairs if p == k and g != k)
        fn = sum(1 for _, p, g in pairs if p != k and g == k)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[k] = {
            "support": tp + fn,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
        }

    errors = [
        {
            "msg_id": msg_id,
            "content": next((p["content"][:80] for p in predicted if p["msg_id"] == msg_id), ""),
            "predicted": p,
            "gold": g,
            "confidence": next((p["confidence"] for p in predicted if p["msg_id"] == msg_id), None),
        }
        for msg_id, p, g in pairs
        if p != g
    ]
    metrics = {
        "total": total,
        "correct": correct,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "macro_f1": round(sum(v["f1"] for v in per_class.values()) / len(INTENTS), 3),
        "per_class": per_class,
        "confusion": confusion,
        "errors": errors[:40],
        "error_count": len(errors),
        "note": "在 data/fixtures/labels.jsonl（人工标注的合成回放集）上测量；真实微信群的准确率尚未测量，见 docs/数据说明.md",
    }
    return metrics


def summarize_batch(classified: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(classified)
    dist: dict[str, int] = {}
    for r in rows:
        dist[r["intent"]] = dist.get(r["intent"], 0) + 1
    return {
        "total": len(rows),
        "distribution": dict(sorted(dist.items(), key=lambda kv: -kv[1])),
        "needs_review": sum(1 for r in rows if r.get("needs_review")),
        "avg_confidence": round(sum(r["confidence"] for r in rows) / len(rows), 3) if rows else 0.0,
    }


# ---------------------------- 可选：LLM 精分类 ----------------------------


def make_llm_reviewer(model: str | None = None):
    """返回一个 callable(msg)->intent，只有配好环境变量才生效。

    设计成「只复核低置信度消息」：成本砍到 10% 以内，命中率却最高。
    """
    import os

    base = os.environ.get("WCM_LLM_BASE", "").rstrip("/")
    key = os.environ.get("WCM_LLM_KEY", "")
    if not base or not key:
        return None

    model = model or os.environ.get("WCM_LLM_MODEL", "gpt-4o-mini")
    prompt_head = (
        "你是课程群消息分类器。只输出一个英文标签，不要解释。\n"
        f"可选标签：{', '.join(INTENTS)}\n"
        "判断依据：文件消息且文件名像提交=submission；有疑问词或问号=question；"
        "回应他人提问=answer；表达观点/方案=discussion；老师发的通知=announcement；"
        "分享链接/资料=resource；其余寒暄=social。\n"
    )

    def _call(msg: dict[str, Any]) -> str | None:
        import urllib.request

        payload = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": prompt_head},
                {"role": "user", "content": f"发送者：{msg['sender']['nickname']}\n内容：{msg['content']}"},
            ],
        }
        req = urllib.request.Request(
            f"{base}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"},
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip().lower()
        for k in INTENTS:
            if k in text:
                return k
        return None

    return _call
