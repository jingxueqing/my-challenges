"""本地 HTTP 服务：标准库 http.server，无框架。

接口刻意做成纯 JSON，方便以后被 Agent 直接调用（C4 的技能化预留）。
"""
from __future__ import annotations

import json
import threading
import webbrowser
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import expire, fuzzy, nlparse, recipe, shopping
from .model import STATUS_LABEL, sort_for_action
from .store import Store
from .ui import HTML


def make_handler(store: Store):
    class Handler(BaseHTTPRequestHandler):
        server_version = "HomePantry/1.0"

        def log_message(self, fmt, *args):  # 保持终端干净
            pass

        # ---------- 工具 ----------
        def _json(self, obj, code: int = 200):
            body = json.dumps(obj, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _html(self, text: str):
            body = text.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if not n:
                return {}
            try:
                return json.loads(self.rfile.read(n).decode() or "{}")
            except json.JSONDecodeError:
                return {}

        def _items_json(self):
            return [i.to_dict() for i in sort_for_action(store.items())]

        # ---------- 路由 ----------
        def do_GET(self):
            u = urlparse(self.path)
            q = parse_qs(u.query)
            if u.path in ("/", "/index.html"):
                return self._html(HTML)

            if u.path == "/api/state":
                items = store.items()
                return self._json({
                    "today": date.today().isoformat(),
                    "items": self._items_json(),
                    "brief": expire.daily_brief(items),
                    "counts": expire.counts(items),
                    "level_alerts": expire.level_alerts(items),
                    "stats": store.stats(),
                    "shopping": store.shopping_list(),
                })

            if u.path == "/api/search":
                hits = fuzzy.search(store.items(), (q.get("q") or [""])[0])
                return self._json({"hits": hits})

            if u.path == "/api/recipes":
                top = int((q.get("top") or ["4"])[0])
                items = store.items()
                return self._json({"recipes": [m.to_dict() for m in recipe.match(items, limit=top)]})

            if u.path == "/api/shopping":
                return self._json({"items": store.shopping_list()})

            if u.path == "/api/stats":
                return self._json(store.stats())

            if u.path == "/api/export":
                items = sort_for_action(store.items())
                rows = [{"name": i.name, "qty": i.qty_text(), "location": i.location,
                         "expires": i.expires.isoformat() if i.expires else None,
                         "status": STATUS_LABEL[i.status()]} for i in items]
                return self._json({"count": len(rows), "items": rows})

            return self._json({"error": "not found"}, 404)

        def do_POST(self):
            u = urlparse(self.path)
            data = self._body()

            if u.path == "/api/add":
                text = (data.get("text") or "").strip()
                if not text:
                    return self._json({"ok": False, "error": "空输入"}, 400)
                parsed = nlparse.parse_line(text, default_loc=data.get("loc"))
                out = []
                for p in parsed:
                    store.add(p.item)
                    out.append(p.to_dict())
                return self._json({"ok": bool(out), "items": out})

            if u.path == "/api/consume":
                return self._json(store.consume(int(data["id"]), data.get("qty")))

            if u.path == "/api/waste":
                return self._json(store.waste(int(data["id"])))

            if u.path == "/api/shopping/sync":
                rows = shopping.build(store.items(), recipe.match(store.items(), limit=12))
                store.sync_shopping(rows)
                return self._json({"ok": True, "count": len(rows)})

            if u.path == "/api/shopping/toggle":
                return self._json(store.toggle_shopping(int(data["id"]), bool(data.get("done"))) or {})

            if u.path == "/api/seed":
                from . import seed as seed_mod
                store.reset()
                n = seed_mod.seed(store)
                return self._json({"ok": True, "count": n})

            return self._json({"error": "not found"}, 404)

    return Handler


def serve(store: Store, host: str = "127.0.0.1", port: int = 8765,
          open_browser: bool = True) -> None:
    httpd = ThreadingHTTPServer((host, port), make_handler(store))
    url = f"http://{host}:{port}/"
    print(f"家里有什么 · 已启动 → {url}")
    print(f"数据库：{store.path}")
    print("Ctrl+C 停止")
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        httpd.server_close()
