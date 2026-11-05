"""L4 Nudge：把预警变成「可以直接复制粘贴」的催办草稿。

**默认只生成草稿，不发送。** 原因有三条，都是我自己的判断：
    1. 自动群发/私信需要登录态或第三方协议，违反平台规则的风险落在老师身上；
    2. 催交是有语气的事，机器写的话一旦生硬，学生就不回你了；
    3. 草稿留在文件里，谁发的、发了什么，事后能查——这比"系统自动发了"更负责任。

真要双向写回，把 send 接上 wechaty / 企业微信机器人即可，接口已经留好。
"""

from __future__ import annotations

from typing import Any

from .config import ClassConfig

STATUS_WORD = {"ailog": "AI 日志", "deliverable": "主交付物", "notes": "拿来说明", "demo": "demo", "aar": "AAR"}


def build(cfg: ClassConfig, alerts_data: dict[str, Any], profiles: dict[str, Any] | None = None) -> dict[str, Any]:
    prof = {p["wxid"]: p for p in (profiles or {}).get("profiles", [])}
    private: dict[str, list[dict[str, Any]]] = {}
    group: list[dict[str, Any]] = []

    for a in alerts_data["alerts"]:
        t = a["type"]
        if t in ("silent_student", "engagement_drop"):
            name = a["evidence"].get("nickname", a["subject"])
            days = a["evidence"].get("silence_days")
            if t == "silent_student":
                text = f"{name}，看你有一阵没在群里出现了，是不是课业或者别的事卡住了？有需要跟我说一声，进度可以商量。"
            else:
                text = f"{name}，这周群里没怎么看到你，是不是在做大件？卡在哪可以发出来，别自己闷着。"
            private.setdefault(name, []).append({"channel": "private", "text": text, "reason": a["message"], "alert_id": a["id"]})
        elif t == "missing_artifacts":
            name = a["evidence"]["student"]
            missing = "、".join(STATUS_WORD.get(m, m) for m in a["evidence"]["missing"])
            text = (
                f"{name}，你的 {a['evidence']['challenge']} 我这边只收到 {', '.join(a['evidence']['artifacts'])}，"
                f"还差 {missing}。补齐后按 姓名_{a['evidence']['challenge']}_内容.md 命名发群里就行。"
            )
            private.setdefault(name, []).append({"channel": "private", "text": text, "reason": a["message"], "alert_id": a["id"]})
        elif t == "naming_violation":
            name = a["evidence"]["student"]
            cid = a["evidence"]["challenge"]
            text = f"{name}，{cid} 的文件收到，但命名我这边归档不了。麻烦按 姓名_{cid}_内容.md 重新发一次，内容不用改。"
            private.setdefault(name, []).append({"channel": "private", "text": text, "reason": a["message"], "alert_id": a["id"]})
        elif t == "unanswered_question":
            text = (
                f"【接一下这个问题】{a['evidence']['asker']} 在群里问：「{a['evidence']['question'][:60]}」，"
                f"已经 {a['evidence']['age_hours']} 小时没人回。谁踩过这个坑，帮忙答一句。"
            )
            group.append({"channel": "group", "text": text, "reason": a["message"], "alert_id": a["id"]})
        elif t == "deadline_risk":
            names = "、".join(a["evidence"]["missing"][:8])
            text = (
                f"【提醒】{a['evidence']['challenge']} 还有 {a['evidence']['days_left']} 天截止，目前还没交的：{names}"
                f"{' 等' if a['evidence']['missing_count'] > 8 else ''}。提交前对照一下四件套，别只发主文件。"
            )
            group.append({"channel": "group", "text": text, "reason": a["message"], "alert_id": a["id"]})
        elif t == "low_submission_rate":
            chs = a["evidence"].get("challenges") or []
            head = "、".join(f"{c['challenge']}（{c['rate']:.0%}）" for c in chs[:4])
            text = (
                f"【进度同步】目前提交率偏低的挑战：{head}。"
                "如果大家是卡在同一个点上，明天周会我们集中解决一次。"
            )
            group.append({"channel": "group", "text": text, "reason": a["message"], "alert_id": a["id"]})

    private_items = [
        {"to": name, "items": items, "count": len(items), "wxid": next((w for w, p in prof.items() if p.get("nickname") == name), None)}
        for name, items in sorted(private.items(), key=lambda kv: -len(kv[1]))
    ]

    lines = ["# 催办草稿（未发送）", "", f"> 生成时间：{alerts_data['as_of']} ｜ 共 {len(private_items)} 位同学、{len(group)} 条群消息草稿", ""]
    lines.append("**使用方式**：复制粘贴到微信，自己看一遍再发。系统不会自动发送。")
    lines.append("")
    if group:
        lines.append("## 群消息")
        lines.append("")
        for g in group:
            lines.append(f"```text\n{g['text']}\n```")
            lines.append(f"*依据：{g['reason']}*")
            lines.append("")
    if private_items:
        lines.append("## 私信")
        lines.append("")
        for p in private_items:
            lines.append(f"### {p['to']}（{p['count']} 条）")
            for it in p["items"]:
                lines.append(f"```text\n{it['text']}\n```")
                lines.append(f"*依据：{it['reason']}*")
            lines.append("")
    if not group and not private_items:
        lines.append("本周没有需要催的事。")

    return {"generated_at": alerts_data["as_of"], "private": private_items, "group": group, "markdown": "\n".join(lines)}
