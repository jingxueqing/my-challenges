"""L4 Dashboard：生成一个「双击就能开」的静态看板。

为什么不是起一个 Web 服务：
    老师要的是「打开就能看」，不是「先装环境再跑服务」。
    所有数据和样式内联到一个 html 里，零依赖、零 CDN、断网也能开，
    发到群里别人下载就能看（和 C6A 的做法一致，也被真实反馈验证过好用）。
"""

from __future__ import annotations

import html
import json
import os
from datetime import datetime
from typing import Any

from .config import ClassConfig

SEV_COLOR = {"high": "#dc2626", "medium": "#d97706", "low": "#64748b"}
STATUS_COLOR = {
    "accepted": "#0f766e",
    "reviewing": "#d97706",
    "needs_revision": "#dc2626",
    "none": "#e5e7eb",
}
STATUS_LABEL = {"accepted": "齐全", "reviewing": "待复核", "needs_revision": "缺件", "none": "未交"}


def _esc(s: Any) -> str:
    return html.escape(str(s or ""))


def _daily_series(linked: list[dict[str, Any]]) -> list[tuple[str, int]]:
    days: dict[str, int] = {}
    for m in linked:
        d = m["timestamp"][:10]
        days[d] = days.get(d, 0) + 1
    return sorted(days.items())


def _sparkline(series: list[tuple[str, int]], width: int = 760, height: int = 120) -> str:
    if not series:
        return ""
    values = [v for _, v in series]
    peak = max(values) or 1
    n = len(series)
    step = width / max(n - 1, 1)
    pad = 18
    pts = []
    for i, (d, v) in enumerate(series):
        x = pad + i * step * (width - 2 * pad) / max(width - 2 * pad, 1) * 1.0
        x = pad + i * (width - 2 * pad) / max(n - 1, 1)
        y = height - pad - (v / peak) * (height - 2 * pad)
        pts.append((x, y, d, v))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in pts)
    area = f"{pad},{height - pad} " + line + f" {width - pad},{height - pad}"
    bars = "".join(
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#2563eb"><title>{d}：{v} 条</title></circle>'
        for x, y, d, v in pts
    )
    labels = "".join(
        f'<text x="{x:.1f}" y="{height - 4}" font-size="9" fill="#94a3b8" text-anchor="middle">{d[5:]}</text>'
        for x, y, d, v in pts[:: max(len(pts) // 7, 1)]
    )
    return (
        f'<svg viewBox="0 0 {width} {height}" width="100%" height="{height}" role="img" aria-label="每日消息量">'
        f'<line x1="{pad}" y1="{height - pad}" x2="{width - pad}" y2="{height - pad}" stroke="#e5e7eb" stroke-width="1"/>'
        f'<polygon points="{area}" fill="#2563eb14"/>'
        f'<polyline points="{line}" fill="none" stroke="#2563eb" stroke-width="2" stroke-linejoin="round"/>'
        f"{bars}"
        f'<text x="{pad}" y="12" font-size="10" fill="#94a3b8">峰值 {peak}</text>'
        f"{labels}</svg>"
    )


def render(
    cfg: ClassConfig,
    linked: list[dict[str, Any]],
    submissions: dict[str, Any],
    qa: dict[str, Any],
    profiles: dict[str, Any],
    alerts_data: dict[str, Any],
    metrics: dict[str, Any] | None = None,
    window_days: int = 7,
) -> str:
    series = _daily_series(linked)
    as_of = linked[-1]["timestamp"][:16] if linked else datetime.now().strftime("%Y-%m-%d %H:%M")
    total_cells = submissions["cells"]
    fill_rate = submissions["submission_count"] / total_cells if total_cells else 0

    kpis = [
        ("消息总量", f"{len(linked)}", f"{len(series)} 天窗口"),
        ("提交矩阵", f"{submissions['submission_count']}/{total_cells}", f"覆盖 {fill_rate:.0%} 的格子"),
        ("完整提交", f"{submissions['complete_count']}", f"缺件 {submissions['needs_revision_count']} 项"),
        ("文件数", f"{submissions['artifact_count']}", "磁盘 + 群文件"),
        ("Q&A 沉淀", f"{qa['kept']}", f"答出率 {qa['answer_rate']:.0%}"),
        ("预警", f"{alerts_data['total']}", f"高优先级 {alerts_data['by_severity']['high']} 条"),
    ]
    kpi_html = "".join(
        f'<div class="kpi"><div class="kpi-label">{_esc(a)}</div><div class="kpi-value">{_esc(b)}</div><div class="kpi-sub">{_esc(c)}</div></div>'
        for a, b, c in kpis
    )

    # 挑战提交率（横轴按本期最高提交率缩放，刻度写在标题里，避免误读）
    rate_rows = []
    rate_max = max((submissions["by_challenge"][c]["rate_all"] for c in cfg.challenge_order), default=0) or 1
    for cid in cfg.challenge_order:
        st = submissions["by_challenge"][cid]
        pct = st["rate_all"] / rate_max * 100
        rate_rows.append(
            f'<div class="rate-row" title="{_esc(cid)} {_esc(st["name"])}：{st["submitted"]}/{st["expected"]}">'
            f'<span class="rate-id">{_esc(cid)}</span>'
            f'<span class="rate-name">{_esc(st["name"])}</span>'
            f'<span class="rate-track"><span class="rate-fill" style="width:{pct:.1f}%"></span></span>'
            f'<span class="rate-num">{st["submitted"]}/{st["expected"]}</span></div>'
        )

    # 学生 × 挑战 矩阵
    header = "".join(f'<div class="m-head">{_esc(c)}</div>' for c in cfg.challenge_order)
    rows_html = []
    matrix = submissions["matrix"]
    for p in profiles["profiles"]:
        cells = []
        for cid in cfg.challenge_order:
            status = matrix.get(p["wxid"], {}).get(cid, "none")
            cells.append(
                f'<div class="m-cell" style="background:{STATUS_COLOR[status]}" '
                f'title="{_esc(p["nickname"])} · {_esc(cid)} · {STATUS_LABEL[status]}"></div>'
            )
        rows_html.append(
            f'<div class="m-row"><div class="m-name">{_esc(p["nickname"])}'
            f'<span class="m-score">{p["engagement_score"]}</span></div>{"".join(cells)}</div>'
        )

    # 意图分布
    intent_count: dict[str, int] = {}
    for m in linked:
        intent_count[m["intent_cn"]] = intent_count.get(m["intent_cn"], 0) + 1
    ipc = [30, 60, 90, 120, 150, 180, 210, 240]
    intent_max = max(intent_count.values()) if intent_count else 1
    intent_html = "".join(
        f'<div class="intent-row"><span class="intent-name">{_esc(k)}</span>'
        f'<span class="intent-track"><span class="intent-fill" style="width:{v / intent_max * 100:.0f}%"></span></span>'
        f'<span class="intent-num">{v}</span></div>'
        for k, v in sorted(intent_count.items(), key=lambda kv: -kv[1])
    )

    # 活跃榜
    top_html = "".join(
        f'<div class="top-row"><span class="top-rank">{i}</span><span class="top-name">{_esc(p["nickname"])}</span>'
        f'<span class="top-meta">{p["msg_count"]} 条 · 答 {p["answers_given"]} · 提交 {p["accepted"]}</span>'
        f'<span class="top-score">{p["engagement_score"]}</span></div>'
        for i, p in enumerate(profiles["profiles"][:8], 1)
    )
    silent = [p for p in profiles["profiles"] if p["silence_days"] >= cfg.rules.silent_days]
    silent_html = (
        "".join(
            f'<div class="silent-row"><span>{_esc(p["nickname"])}</span><span>{p["silence_days"]} 天未发言</span></div>'
            for p in silent
        )
        or '<div class="silent-row"><span>无</span><span>—</span></div>'
    )

    # 告警
    alert_html = "".join(
        f'<div class="alert" style="border-left-color:{SEV_COLOR[a["severity"]]}">'
        f'<div class="alert-msg">{_esc(a["message"])}</div>'
        f'<div class="alert-action">建议：{_esc(a["action"])}</div></div>'
        for a in alerts_data["alerts"][:12]
    ) or '<div class="alert" style="border-left-color:#94a3b8"><div class="alert-msg">本周没有触发预警</div></div>'

    # 最佳问答
    qa_html = ""
    for p in qa["top_pairs"][:4]:
        qa_html += (
            f'<div class="qa-card"><div class="qa-q">Q · {_esc(p["question"])}</div>'
            f'<div class="qa-a">A · {_esc(p["answer"][:160])}</div>'
            f'<div class="qa-meta">{_esc(p["asker"]["nickname"])} → {_esc(p["answerer"]["nickname"])}'
            f' · 响应 {p["latency_seconds"] // 60} 分钟 · 质量 {p["quality_score"]}'
            f' · {"、".join(p["topic_tags"][:3]) or "无标签"}</div></div>'
        )

    acc_line = ""
    if metrics:
        acc_line = (
            f'<span class="badge badge-ok">分类器 {metrics["accuracy"]:.1%}（{metrics["total"]} 条标注样本实测）</span>'
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>班级看板 · {_esc(cfg.group_name)}</title>
<style>
  :root {{
    --bg:#f6f7f9; --card:#ffffff; --ink:#111827; --muted:#6b7280; --line:#e5e7eb;
    --blue:#2563eb; --teal:#0f766e; --amber:#d97706; --red:#dc2626;
    --shadow:0 1px 2px rgba(16,24,40,.04), 0 1px 3px rgba(16,24,40,.06);
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font:14px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
    -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:28px 20px 64px; }}
  header {{ display:flex; flex-wrap:wrap; gap:14px; align-items:flex-end; justify-content:space-between; margin-bottom:22px; }}
  h1 {{ font-size:24px; margin:0 0 6px; letter-spacing:-.02em; }}
  .sub {{ color:var(--muted); font-size:13px; }}
  .badges {{ display:flex; gap:8px; flex-wrap:wrap; }}
  .badge {{ font-size:12px; padding:3px 9px; border-radius:999px; background:#eef2ff; color:#3730a3; border:1px solid #e0e7ff; }}
  .badge-ok {{ background:#ecfdf5; color:#065f46; border-color:#d1fae5; }}
  .badge-warn {{ background:#fffbeb; color:#92400e; border-color:#fde68a; }}
  section {{ margin:26px 0; }}
  h2 {{ font-size:15px; margin:0 0 12px; letter-spacing:.01em; }}
  h2 span {{ font-weight:400; color:var(--muted); font-size:12px; margin-left:8px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(6,1fr); gap:12px; }}
  .kpi {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px 16px; box-shadow:var(--shadow); }}
  .kpi-label {{ font-size:12px; color:var(--muted); }}
  .kpi-value {{ font-size:26px; font-weight:650; letter-spacing:-.02em; margin:2px 0; }}
  .kpi-sub {{ font-size:11px; color:var(--muted); }}
  .grid2 {{ display:grid; grid-template-columns:1.35fr 1fr; gap:16px; }}
  .card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px 18px; box-shadow:var(--shadow); }}
  .rate-row {{ display:grid; grid-template-columns:44px 148px 1fr 52px; align-items:center; gap:10px; padding:3px 0; font-size:12.5px; }}
  .rate-id {{ color:var(--muted); font-variant-numeric:tabular-nums; }}
  .rate-name {{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
  .rate-track {{ height:8px; background:#f1f5f9; border-radius:99px; overflow:hidden; }}
  .rate-fill {{ display:block; height:100%; min-width:2px; background:linear-gradient(90deg,#3b82f6,#0f766e); border-radius:99px; }}
  .rate-num {{ text-align:right; color:var(--muted); font-variant-numeric:tabular-nums; }}
  .matrix {{ overflow-x:auto; }}
  .m-row, .m-head-row {{ display:grid; grid-template-columns:118px repeat(20, 1fr); gap:3px; align-items:center; }}
  .m-head {{ font-size:10px; color:#475569; font-weight:600; text-align:center; writing-mode:vertical-rl; height:48px; letter-spacing:.02em; }}
  .m-name {{ font-size:12px; display:flex; justify-content:space-between; padding-right:6px; }}
  .m-score {{ color:var(--muted); font-size:10.5px; }}
  .m-cell {{ height:15px; border-radius:3px; }}
  .m-row:nth-child(even) {{ background:#fafbfc; }}
  .m-row:nth-child(even) {{ background:#fafbfc; }}
  .legend {{ display:flex; gap:14px; font-size:11.5px; color:var(--muted); margin-top:10px; }}
  .legend i {{ display:inline-block; width:10px; height:10px; border-radius:3px; margin-right:5px; vertical-align:-1px; }}
  .top-row {{ display:grid; grid-template-columns:20px 1fr auto 46px; gap:8px; padding:5px 0; border-bottom:1px dashed #f1f5f9; font-size:13px; }}
  .top-rank {{ color:var(--muted); font-size:11px; }}
  .top-meta {{ color:var(--muted); font-size:11.5px; }}
  .top-score {{ text-align:right; font-variant-numeric:tabular-nums; font-weight:600; color:var(--blue); }}
  .silent-row {{ display:flex; justify-content:space-between; font-size:12.5px; padding:4px 0; color:#7c2d12; }}
  .intent-row {{ display:grid; grid-template-columns:64px 1fr 40px; gap:10px; align-items:center; font-size:12.5px; padding:3px 0; }}
  .intent-track {{ height:8px; background:#f1f5f9; border-radius:99px; overflow:hidden; }}
  .intent-fill {{ display:block; height:100%; background:#6366f1; border-radius:99px; }}
  .intent-num {{ text-align:right; color:var(--muted); }}
  .alert {{ border-left:3px solid #94a3b8; background:#fff; padding:9px 12px; margin-bottom:8px; border-radius:0 8px 8px 0; }}
  .alert-msg {{ font-size:13px; }}
  .alert-action {{ font-size:11.5px; color:var(--muted); margin-top:2px; }}
  .qa-card {{ border:1px solid var(--line); border-radius:10px; padding:10px 12px; margin-bottom:8px; background:#fcfcfd; }}
  .qa-q {{ font-size:13px; font-weight:600; }}
  .qa-a {{ font-size:12.5px; color:#374151; margin:3px 0; }}
  .qa-meta {{ font-size:11px; color:var(--muted); }}
  footer {{ margin-top:34px; font-size:11.5px; color:var(--muted); line-height:1.9; border-top:1px solid var(--line); padding-top:14px; }}
  @media (max-width:900px) {{
    .kpis {{ grid-template-columns:repeat(3,1fr); }}
    .grid2 {{ grid-template-columns:1fr; }}
    .m-row, .m-head-row {{ grid-template-columns:96px repeat(20, 1fr); }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <h1>{_esc(cfg.group_name)}</h1>
      <div class="sub">数据截至 {_esc(as_of)} ｜ 窗口 {window_days} 天 ｜ 生成于 {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
    <div class="badges">
      <span class="badge">真实提交：本机磁盘 {sum(1 for r in submissions['rows'] if 'disk' in r['sources'])} 项</span>
      <span class="badge">群消息：脱敏回放 {len(linked)} 条</span>
      {acc_line}
    </div>
  </header>

  <section class="kpis">{kpi_html}</section>

  <section class="grid2">
    <div class="card">
      <h2>各挑战提交率 <span>分母＝全班 {len(cfg.roster)} 人 ｜ 横轴至 {rate_max:.0%}</span></h2>
      {''.join(rate_rows)}
    </div>
    <div class="card">
      <h2>活跃榜 Top 8 <span>参与分口径见页脚</span></h2>
      {top_html}
      <h2 style="margin-top:16px">沉默预警</h2>
      {silent_html}
    </div>
  </section>

  <section class="card">
    <h2>学生 × 挑战 提交矩阵 <span>悬停看具体状态</span></h2>
    <div class="matrix">
      <div class="m-head-row"><div></div>{header}</div>
      {''.join(rows_html)}
    </div>
    <div class="legend">
      <span><i style="background:#0f766e"></i>齐全</span>
      <span><i style="background:#d97706"></i>待复核（命名问题）</span>
      <span><i style="background:#dc2626"></i>缺件</span>
      <span><i style="background:#e5e7eb"></i>未交</span>
    </div>
  </section>

  <section class="grid2">
    <div class="card">
      <h2>每日消息量 <span>区间 {min((v for _, v in series), default=0)}–{max((v for _, v in series), default=0)} 条/天 ｜ 零基线</span></h2>
      {_sparkline(series)}
      <h2 style="margin-top:18px">消息意图分布 <span>规则分类器，准确率见页脚</span></h2>
      {intent_html}
    </div>
    <div class="card">
      <h2>需要处理的事 <span>按严重度排序</span></h2>
      {alert_html}
    </div>
  </section>

  <section class="card">
    <h2>本周最佳问答 <span>可直接进 FAQ</span></h2>
    {qa_html or '<div class="sub">本周没有达到质量阈值的问答对。</div>'}
  </section>

  <footer>
    <b>口径</b>：提交以文件为准（群里说"我交了"不计入）；完成率分母为全班人数；参与分＝发言 35 + 助人 25 + 完整提交 30 + 持续性 10。
    <br><b>数据来源</b>：真实提交包来自本机磁盘扫描（{sum(1 for r in submissions['rows'] if 'disk' in r['sources'])} 项 / {submissions['artifact_count']} 个文件）；群消息为脱敏回放集，人名除本人外为合成。
    <br><b>已知局限</b>：本机微信 4.x 数据库为 SQLCipher 加密，未接入真实群消息；分类器准确率为回放集实测值，真实群未测。
    <br>生成器：wechat-class-manager ／ 单文件零依赖，可离线打开。
  </footer>
</div>
</body>
</html>
"""


def write(path: str, html_text: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html_text)
    return path
