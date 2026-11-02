#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_site.py —— 把 submissions.json 注入静态站点模板，产出可直接双击打开的仪表盘。

为什么内嵌 JSON：file:// 下 fetch/XHR 会被浏览器拦，内嵌数据才能「零依赖离线打开」。
产出：
  JingXueQing_C6A_仪表盘/index.html       （模板 + 数据）
  JingXueQing_C6A_仪表盘/assets/app.js     （从 templates 拷过来）
  JingXueQing_C6A_仪表盘/assets/styles.css
  JingXueQing_C6A_仪表盘/data.json         （同一份数据，供二次开发）
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "JingXueQing_C6A_数据"
TPL = Path(__file__).resolve().parent / "templates"
OUT = BASE / "JingXueQing_C6A_仪表盘"


def main() -> int:
    payload = json.loads((DATA / "submissions.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "assets").mkdir(parents=True, exist_ok=True)

    shutil.copy2(TPL / "app.js", OUT / "assets" / "app.js")
    shutil.copy2(TPL / "styles.css", OUT / "assets" / "styles.css")

    blob = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    blob = blob.replace("</script>", "<\\/script>")  # 防内嵌 HTML 提前闭合
    html = (TPL / "index.template.html").read_text(encoding="utf-8").replace("/*__C6A_DATA__*/", blob)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    (OUT / "data.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    kb = len(html.encode("utf-8")) / 1024
    print(f"[site] index.html 生成完成（{kb:.0f} KB，内嵌 {payload['stats']['n_records']} 条记录）")
    print(f"[site] 打开方式：open '{OUT / 'index.html'}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
