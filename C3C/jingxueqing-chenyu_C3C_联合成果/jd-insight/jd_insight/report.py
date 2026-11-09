"""
jd_insight.report — 单文件 HTML 报告（无外部依赖、可直接邮件发给导师）

实现者：ChenYu（CS 方），版式需求提出者：JingXueQing
设计原则：报告必须能"脱离工具单独阅读"——评委/HR 不会为了看一份报告去装 Python。
所以所有样式内联、不引用 CDN、不依赖 JS 渲染（纯静态 DOM）。
"""

from __future__ import annotations

import html
import json
from datetime import datetime
from typing import Dict, List, Optional

from .matcher import MatchResult
from .taxonomy import DOMAIN_DESC, DOMAINS

_CSS = """
:root{
  --ink:#152238; --ink-2:#4a5a75; --line:#dfe5ee; --bg:#f6f8fb; --card:#ffffff;
  --accent:#1c4e8a; --accent-soft:#e8f0fa; --warn:#b4471f; --warn-soft:#fbeee9;
  --ok:#1f6b4a; --ok-soft:#e7f4ee;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font:15px/1.7 -apple-system,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;}
.wrap{max-width:960px;margin:0 auto;padding:40px 28px 72px}
h1{font-size:26px;margin:0 0 6px;letter-spacing:-.3px}
h2{font-size:18px;margin:40px 0 14px;padding-bottom:8px;border-bottom:2px solid var(--ink)}
.sub{color:var(--ink-2);font-size:13px}
.hero{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:26px 28px;
 display:flex;gap:28px;align-items:center;flex-wrap:wrap;margin-top:22px}
.score{font-size:56px;font-weight:700;line-height:1;letter-spacing:-2px}
.score small{font-size:16px;color:var(--ink-2);font-weight:400;margin-left:4px}
.badge{display:inline-block;padding:3px 11px;border-radius:999px;font-size:12.5px;
 background:var(--accent-soft);color:var(--accent);border:1px solid #cfe0f2;margin-right:6px}
.badge.warn{background:var(--warn-soft);color:var(--warn);border-color:#f0d3c8}
.badge.ok{background:var(--ok-soft);color:var(--ok);border-color:#cfe8dc}
.hero-meta{flex:1;min-width:220px}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);
 border-radius:10px;overflow:hidden;font-size:13.5px}
th{text-align:left;background:#eef2f8;color:var(--ink-2);font-weight:600;padding:9px 12px;font-size:12.5px}
td{padding:9px 12px;border-top:1px solid var(--line);vertical-align:top}
tr:hover td{background:#fafbfd}
.bar{height:9px;border-radius:5px;background:#e9eef6;overflow:hidden;min-width:90px}
.bar i{display:block;height:100%;background:var(--accent);border-radius:5px}
.bar i.low{background:var(--warn)}
.bar i.mid{background:#c98a2e}
.num{font-variant-numeric:tabular-nums;font-weight:600}
.muted{color:var(--ink-2);font-size:12.5px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px;margin-bottom:12px}
.card.gap{border-left:4px solid var(--warn)}
.card.tip{border-left:4px solid var(--accent)}
.card h3{margin:0 0 6px;font-size:15px}
ul{margin:6px 0 0;padding-left:20px}
li{margin:3px 0}
pre{background:#0f1826;color:#d8e2f0;padding:14px 16px;border-radius:10px;overflow:auto;font-size:12.5px;line-height:1.6}
.footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:var(--ink-2);font-size:12px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}
"""


def _esc(v: object) -> str:
    return html.escape(str(v))


def _bar(pct: float) -> str:
    p = max(0.0, min(100.0, pct))
    cls = "low" if p < 45 else ("mid" if p < 70 else "")
    return f'<div class="bar"><i class="{cls}" style="width:{p:.1f}%"></i></div>'


def _domain_block(result: MatchResult) -> str:
    rows = []
    for d in DOMAINS:
        s = result.domain_scores.get(d, 0.0)
        rows.append(
            f"<tr><td><strong>{_esc(d)}</strong><div class='muted'>{_esc(DOMAIN_DESC[d])}</div></td>"
            f"<td style='width:120px'>{_bar(s)}</td>"
            f"<td class='num' style='width:56px'>{s:.0f}</td></tr>"
        )
    return (
        "<table><thead><tr><th>能力域</th><th>覆盖度</th><th>得分</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _tag_table(result: MatchResult, limit: int = 14) -> str:
    rows = []
    for t in result.tags[:limit]:
        if t.coverage >= 1.0:
            flag = "<span class='badge ok'>已具备</span>"
        elif t.coverage > 0:
            flag = "<span class='badge'>单次佐证</span>"
        else:
            flag = "<span class='badge warn'>缺失</span>"
        ev = _esc(t.evidence[0]) if t.evidence else "<span class='muted'>—</span>"
        rows.append(
            f"<tr><td><strong>{_esc(t.name)}</strong><div class='muted'>{_esc(t.domain)} · {_esc(t.tag_id)}</div></td>"
            f"<td class='num'>{t.weight * 100:.1f}%</td>"
            f"<td>{flag}</td>"
            f"<td class='muted'>{ev}</td></tr>"
        )
    return (
        "<table><thead><tr><th>能力项</th><th>需求权重</th><th>状态</th><th>证据句（JD / 简历）</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def _gaps(result: MatchResult) -> str:
    if not result.hard_gaps:
        return "<div class='card tip'><h3>硬门槛无缺失</h3><p class='muted'>本次 JD 的必需项均已命中至少一次。</p></div>"
    cards = []
    for g in result.hard_gaps[:5]:
        cards.append(
            f"<div class='card gap'><h3>{_esc(g.name)} · 权重 {g.weight * 100:.1f}%</h3>"
            f"<div class='muted'>JD 原句：{_esc(g.evidence[0]) if g.evidence else '—'}</div></div>"
        )
    return "".join(cards)


def _rank_table(ranked: Optional[List[Dict[str, object]]]) -> str:
    if not ranked:
        return "<p class='muted'>未提供岗位库，跳过横向排名。</p>"
    rows = []
    for i, r in enumerate(ranked[:10], 1):
        gaps = "、".join(r.get("hard_gaps") or []) or "—"
        rows.append(
            f"<tr><td class='num'>{i}</td><td><strong>{_esc(r['title'])}</strong>"
            f"<div class='muted'>{_esc(r['company'])}</div></td>"
            f"<td>{_esc(r['role_type'])}</td>"
            f"<td class='num'>{r['total']}</td><td>{_esc(r['grade'])}</td>"
            f"<td class='muted'>{_esc(gaps)}</td></tr>"
        )
    return (
        "<table><thead><tr><th>#</th><th>岗位</th><th>类型</th><th>分数</th><th>结论</th><th>主要缺口</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def render(
    result: MatchResult,
    resume_name: str = "候选人",
    jd_title: str = "目标岗位",
    ranked: Optional[List[Dict[str, object]]] = None,
    data_note: str = "样例数据为合成数据，仅用于演示与回归测试，不代表真实招聘市场。",
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    advise_items = "".join(f"<li>{_esc(a)}</li>" for a in result.advise) or "<li>无需额外建议。</li>"

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>岗位匹配报告 · {_esc(jd_title)}</title>
<style>{_CSS}</style></head>
<body><div class="wrap">

<h1>岗位匹配度报告</h1>
<div class="sub">候选人：{_esc(resume_name)} ｜ 目标岗位：{_esc(jd_title)} ｜ 生成时间：{now}</div>

<div class="hero">
  <div><div class="score">{result.total:.0f}<small>/100</small></div></div>
  <div class="hero-meta">
    <div style="margin-bottom:10px">
      <span class="badge">{_esc(result.grade)}</span>
      <span class="badge">{_esc(result.role_type)}</span>
      <span class="badge warn">硬缺口 {len(result.hard_gaps)} 项</span>
    </div>
    <div class="muted">总分 = 100 × Σ(需求权重 × 覆盖系数)。覆盖系数：未命中 0，命中 1 次 0.85，命中 ≥2 次 1.0。</div>
  </div>
</div>

<h2>一、六域覆盖度</h2>
{_domain_block(result)}

<h2>二、需求项明细（按权重降序）</h2>
{_tag_table(result)}

<h2>三、硬缺口</h2>
{_gaps(result)}

<h2>四、改进建议</h2>
<div class="card tip"><ul>{advise_items}</ul></div>

<h2>五、岗位横向排名</h2>
{_rank_table(ranked)}

<div class="footer">
  <p><strong>方法与局限</strong>：标签体系为 44 项自建 KSAO-lite 体系（见 taxonomy.py），关键词匹配不处理否定句与被动语义，
  例如"未使用过 Python"会被判为命中。因此本工具定位是<strong>投递前的自查清单</strong>，不是自动筛选器。</p>
  <p>{_esc(data_note)}</p>
  <p>jd-insight · 联合产出 · JingXueQing（业务与标签体系）× ChenYu（工程实现）</p>
</div>

</div></body></html>
"""


def write_html(path: str, content: str) -> str:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def write_json(path: str, obj: object) -> str:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return path
