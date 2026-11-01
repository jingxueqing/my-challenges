"""腾讯地图 GL JS 交互式地图渲染（合规）。

合规要点（依据 geo-map-compliance-guard）：
- 只用腾讯地图，不用 Google/OSM/Mapbox/Leaflet。
- 默认场景走 _TMapSecurityConfig 密钥代理，前端零密钥。
- 坐标使用 GCJ-02。
- 不传 mapStyleId（默认 key 未开通自定义样式，传了会灰屏）。
- MultiMarker / MarkerStyle 类名规范。
"""
from __future__ import annotations

import html
import json
from typing import Any

CENTER = (34.4166, 113.7530)  # 西亚斯学院

CATEGORY_STYLE: dict[str, dict[str, Any]] = {
    "campus":  {"color": "#1a73e8", "label": "校园", "icon": "M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"},
    "sight":   {"color": "#e8710a", "label": "景点", "icon": "M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"},
    "museum":  {"color": "#8e44ad", "label": "博物馆", "icon": "M3 21h18M5 21V10l7-5 7 5v11M10 21v-6h4v6"},
    "heritage":{"color": "#c5221f", "label": "古迹", "icon": "M12 2l9 5v3H3V7zM5 10v8m4-8v8m6-8v8m4-8v8M3 21h18"},
    "transit": {"color": "#00838f", "label": "交通", "icon": "M4 16V6c0-1 1-2 2-2h12c1 0 2 1 2 2v10M4 16h16M4 16v3h3v-3m10 0v3h3v-3M7 9h10"},
    "nature":  {"color": "#188038", "label": "自然", "icon": "M12 3L4 20h16zM12 3v17"},
    "city":    {"color": "#5f6368", "label": "城市", "icon": "M3 21h18M5 21V8l7-5 7 5v13"},
}
DEFAULT_STYLE = {"color": "#5f6368", "label": "其他", "icon": "M12 2a7 7 0 100 14 7 7 0 000-14z"}


def _svg_icon(color: str, path_d: str, size: int = 28) -> str:
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2.1" '
        f'stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{path_d}"/></svg>'
    )
    return "data:image/svg+xml;charset=UTF-8," + svg.replace("#", "%23").replace('"', "'").replace("<", "%3C").replace(">", "%3E").replace(" ", "%20")


def build_html(markers: list[dict[str, Any]], *, title: str, summary: str,
               evidence: dict[str, Any] | None = None,
               center: tuple[float, float] = CENTER) -> str:
    """生成自包含的单文件交互式地图 HTML。"""
    evidence = evidence or {}
    cats = sorted({m.get("category", "poi") for m in markers})
    styles = {c: CATEGORY_STYLE.get(c, DEFAULT_STYLE) for c in cats}

    geometries = []
    for i, m in enumerate(markers):
        c = m.get("category", "poi")
        st = CATEGORY_STYLE.get(c, DEFAULT_STYLE)
        geometries.append({
            "id": m.get("id", f"m{i+1}"),
            "styleId": c,
            "position": {"lat": float(m["latitude"]), "lng": float(m["longitude"])},
            "properties": {
                # 同样要转义：这些值最终会被 innerHTML 渲染
                "title": html.escape(m.get("name_zh", "")),
                "desc": html.escape(m.get("desc_zh", "")),
                "desc_en": html.escape(m.get("desc_en", "")),
                "name_en": html.escape(m.get("name_en", "")),
                "rating": html.escape(str(m.get("rating", ""))),
                "category": html.escape(st["label"]),
                "coord": f"{float(m['latitude']):.6f}, {float(m['longitude']):.6f}",
                "idx": i + 1,
            },
        })

    legend = "".join(
        f'<span class="lg"><i style="background:{styles[c]["color"]}"></i>'
        f'{html.escape(styles[c]["label"])}</span>' for c in cats)

    marker_styles = {c: {"color": st["color"], "icon": _svg_icon(st["color"], st["icon"])}
                     for c, st in styles.items()}

    # 侧栏卡片
    cards = []
    for i, m in enumerate(markers):
        c = m.get("category", "poi")
        st = CATEGORY_STYLE.get(c, DEFAULT_STYLE)
        cards.append(f"""<li class="card" data-id="{m.get('id','')}" data-lat="{m['latitude']}" data-lng="{m['longitude']}">
  <div class="row"><span class="idx">{i+1}</span>
    <div><h3>{html.escape(m.get('name_zh',''))}</h3>
    <p class="en">{html.escape(m.get('name_en',''))}</p></div>
    <span class="rate">★ {html.escape(str(m.get('rating','')))}</span></div>
  <span class="tag" style="background:{st['color']}1a;color:{st['color']}">{html.escape(st['label'])}</span>
  <p class="desc">{html.escape(m.get('desc_zh',''))}</p>
  <p class="desc en">{html.escape(m.get('desc_en',''))}</p>
  <code>{float(m['latitude']):.6f}, {float(m['longitude']):.6f}</code>
</li>""")

    ev = ""
    if evidence:
        rows = "".join(
            f"<tr><td>{html.escape(str(k))}</td><td>{html.escape(str(v))}</td></tr>"
            for k, v in evidence.items())
        ev = f'<details class="ev"><summary>本地运行证据（由本地 Gemma 4 生成）</summary><table>{rows}</table></details>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<style>
  *{{box-sizing:border-box}}
  html,body{{margin:0;padding:0;height:100%;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:#202124}}
  #map{{position:absolute;inset:0;height:100vh;width:100%}}
  #panel{{position:absolute;top:0;left:0;bottom:0;width:390px;background:#fff;z-index:10;
    box-shadow:2px 0 18px rgba(0,0,0,.14);display:flex;flex-direction:column;
    transition:transform .28s ease}}
  header{{padding:18px 20px 12px;border-bottom:1px solid #eceff1}}
  header h1{{margin:0 0 6px;font-size:19px;line-height:1.35}}
  header .sub{{margin:0;font-size:13px;color:#5f6368;line-height:1.6}}
  #legend{{display:flex;flex-wrap:wrap;gap:10px;margin-top:10px}}
  .lg{{font-size:12px;color:#5f6368;display:inline-flex;align-items:center;gap:5px}}
  .lg i{{width:10px;height:10px;border-radius:50%;display:inline-block}}
  #list{{list-style:none;margin:0;padding:12px;overflow-y:auto;flex:1}}
  .card{{border:1px solid #e8eaed;border-radius:12px;padding:13px 14px;margin-bottom:11px;cursor:pointer;transition:.18s}}
  .card:hover{{border-color:#1a73e8;box-shadow:0 2px 10px rgba(26,115,232,.13)}}
  .card.on{{border-color:#1a73e8;background:#f5f9ff}}
  .card .row{{display:flex;align-items:flex-start;gap:10px}}
  .card .idx{{flex:none;width:22px;height:22px;border-radius:50%;background:#1a73e8;color:#fff;
    font-size:12px;display:flex;align-items:center;justify-content:center;margin-top:2px}}
  .card h3{{margin:0;font-size:15px}}
  .card .en{{margin:2px 0 0;font-size:11.5px;color:#80868b}}
  .card .rate{{margin-left:auto;font-size:12.5px;color:#e8710a;white-space:nowrap}}
  .tag{{display:inline-block;font-size:11px;padding:2px 8px;border-radius:20px;margin:8px 0 6px}}
  .desc{{margin:4px 0 0;font-size:13px;line-height:1.65;color:#3c4043}}
  .desc.en{{color:#80868b;font-size:12px}}
  .card code{{display:inline-block;margin-top:8px;font-size:11px;color:#5f6368;background:#f1f3f4;padding:2px 7px;border-radius:5px}}
  .ev{{padding:12px 20px 20px;border-top:1px solid #eceff1;font-size:12px;color:#5f6368}}
  .ev summary{{cursor:pointer;font-weight:600}}
  .ev table{{width:100%;border-collapse:collapse;margin-top:8px}}
  .ev td{{border-top:1px solid #f1f3f4;padding:5px 4px;word-break:break-all}}
  #toggle{{position:absolute;top:14px;left:404px;z-index:11;background:#fff;border:none;
    border-radius:9px;width:38px;height:38px;font-size:19px;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.2);color:#202124}}
  @media(max-width:760px){{
    #panel{{width:100%;height:46vh;bottom:auto;transform:translateY(0)}}
    #panel.hide{{transform:translateY(-100%)}}
    #toggle{{left:12px;top:calc(46vh + 12px)}}
  }}
</style>
<script type="text/javascript">
  window._TMapSecurityConfig = {{
    serviceHost: 'http://127.0.0.1:__WB_HTTP_PORT__/_TMapService/_wbt/__WB_TMAP_SECRET__',
  }};
</script>
<script src="https://map.qq.com/api/gljs?v=1.exp"></script>
</head>
<body>
<div id="map"></div>
<aside id="panel">
  <header>
    <h1>{html.escape(title)}</h1>
    <p class="sub">{html.escape(summary)}</p>
    <div id="legend">{legend}</div>
  </header>
  <ul id="list">{"".join(cards)}</ul>
  {ev}
</aside>
<button id="toggle" title="收起/展开">☰</button>

<script>
const CENTER = new TMap.LatLng({center[0]}, {center[1]});
const map = new TMap.Map('map', {{ center: CENTER, zoom: 13.6, pitch: 0 }});

const DATA = {json.dumps(geometries, ensure_ascii=False)};
const STYLES = {json.dumps(marker_styles, ensure_ascii=False)};

const styleObj = {{}};
for (const k in STYLES) {{
  styleObj[k] = new TMap.MarkerStyle({{
    width: 30, height: 30, anchor: {{x: 15, y: 30}},
    src: STYLES[k].icon
  }});
}}

const markers = new TMap.MultiMarker({{
  map: map, styles: styleObj, geometries: DATA
}});

function infoWin(p) {{
  return `<div style="max-width:270px;font-family:-apple-system,'PingFang SC',sans-serif">
    <div style="font-size:14px;font-weight:700;margin-bottom:3px">${{p.title}}</div>
    <div style="font-size:11.5px;color:#80868b;margin-bottom:6px">${{p.name_en}}</div>
    <div style="font-size:12.5px;line-height:1.6;color:#3c4043">${{p.desc}}</div>
    <div style="font-size:11.5px;color:#80868b;margin-top:6px;font-style:italic">${{p.desc_en}}</div>
    <div style="margin-top:7px;font-size:11px;color:#5f6368">
      <span style="color:#e8710a">★ ${{p.rating}}</span> · ${{p.category}} · ${{p.coord}}</div>
  </div>`;
}}

map.addEventListener('click', e => {{
  const hit = markers.getGeometries().find(g => g.properties.id === e.geometry.id);
  if (hit) {{
    map.setCenter(hit.position); map.setZoom(15.4);
    new TMap.InfoWindow({{ position: hit.position, content: infoWin(hit.properties),
                           offset: {{x: 0, y: -34}} }}).open(map);
  }}
}});

document.querySelectorAll('.card').forEach(el => el.addEventListener('click', () => {{
  document.querySelectorAll('.card').forEach(x => x.classList.remove('on'));
  el.classList.add('on');
  const p = new TMap.LatLng(+el.dataset.lat, +el.dataset.lng);
  map.setCenter(p); map.setZoom(15.4);
  new TMap.InfoWindow({{ position: p, offset: {{x: 0, y: -34}},
    content: `<div style="font-family:-apple-system,'PingFang SC',sans-serif;font-size:13.5px;
      font-weight:700">${{el.querySelector('h3').textContent}}</div>` }}).open(map);
}}));

const panel = document.getElementById('panel');
document.getElementById('toggle').addEventListener('click', () => panel.classList.toggle('hide'));
</script>
</body>
</html>"""


def write_map(markers: list[dict[str, Any]], out_path: str, *, title: str,
              summary: str, evidence: dict[str, Any] | None = None) -> str:
    html_text = build_html(markers, title=title, summary=summary, evidence=evidence)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_text)
    return out_path
