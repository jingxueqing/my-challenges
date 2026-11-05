"""命令行入口：python -m pantry.cli <命令>

设计原则：每条命令都能在 1 秒内给你一个「今天要不要动手」的答案。
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from . import expire, fuzzy, lexicon, nlparse, recipe, seed as seed_mod, shopping
from .model import STATUS_LABEL, sort_for_action
from .store import Store

BOLD, DIM, RED, YEL, GRN, CYA, OFF = "\033[1m", "\033[2m", "\033[31m", "\033[33m", "\033[32m", "\033[36m", "\033[0m"


def _c(text: str, color: str, on: bool = True) -> str:
    return f"{color}{text}{OFF}" if on else text


def _status_tag(it, today=None, color=True) -> str:
    st = it.status(today)
    dl = it.days_left(today)
    label = STATUS_LABEL[st]
    if dl is not None:
        label = f"{label} {dl:+d}d" if dl else label
    color_map = {"expired": RED, "today": RED, "urgent": YEL, "soon": YEL, "ok": GRN, "none": DIM}
    return _c(f"[{label}]", color_map[st], color)


def _table(rows: list[list[str]], headers: list[str]) -> str:
    widths = [max(len(str(r[i])) for r in rows + [headers]) for i in range(len(headers))]
    lines = ["  ".join(str(h).ljust(widths[i]) for i, h in enumerate(headers))]
    lines.append("  ".join("-" * w for w in widths))
    for r in rows:
        lines.append("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)))
    return "\n".join(lines)


def cmd_add(args, store: Store) -> int:
    text = " ".join(args.text)
    parsed = nlparse.parse_line(text, default_loc=args.loc)
    if not parsed:
        print("没看懂，试着写成：2盒牛奶 冷藏 7天")
        return 1
    for p in parsed:
        p.item.id = store.add(p.item)
        it = p.item
        print(f"{_c('+', GRN)} {_c(it.name, BOLD, not args.no_color)} {it.qty_text()} "
              f"@ {it.location}  到期 {it.expires or '不设'}  "
              f"{_c(f'(置信度 {p.confidence:.0%})', DIM, not args.no_color)}")
        for r in p.reasons:
            print(f"    · {r}")
        if p.needs_review:
            print(f"    {_c('! 这条被标记为待确认，建议在界面里核对一下', YEL, not args.no_color)}")
    return 0


def cmd_ls(args, store: Store) -> int:
    items = store.items()
    if args.loc:
        items = [i for i in items if i.location == args.loc]
    items = sort_for_action(items)
    if not items:
        print("库存是空的。先跑 `python -m pantry.cli seed` 灌一份演示数据。")
        return 0
    rows = [[i.id, i.name, i.qty_text(), i.location, str(i.expires or "-"),
             _status_tag(i, color=not args.no_color)] for i in items]
    print(_table(rows, ["id", "食材", "数量", "位置", "到期", "状态"]))
    print(f"\n共 {len(items)} 条")
    return 0


def cmd_find(args, store: Store) -> int:
    q = " ".join(args.query)
    hits = fuzzy.search(store.items(), q)
    if not hits:
        print(f"没找到「{q}」。试试更短的词，或者只说特征（白色 / 粉末 / 袋装）。")
        return 0
    print(f"搜「{_c(q, BOLD, not args.no_color)}」→ {len(hits)} 条\n")
    for h in hits:
        tag = {"expired": RED, "today": RED, "urgent": YEL, "soon": YEL, "ok": GRN, "none": DIM}[h["status"]]
        score_txt = _c(f"{h['score']:>5.1f}", CYA, not args.no_color)
        print(f"  {score_txt}  {h['name']} "
              f"{h['qty']:g}{h['unit']} @{h['location']}  "
              f"{_c(h['status_label'], tag, not args.no_color)}")
        print(f"         {_c('为什么：' + '；'.join(h['reasons']), DIM, not args.no_color)}")
    return 0


def cmd_brief(args, store: Store) -> int:
    items = store.items()
    b = expire.daily_brief(items)
    print(_c(b["text"], BOLD, not args.no_color))
    if args.verbose and b["total"]:
        print()
        for it in sort_for_action([i for i in items if i.qty > 0])[:12]:
            if it.status() in ("expired", "today", "urgent", "soon"):
                print(f"  {it.name:<8}{it.qty_text():<8}{_status_tag(it, color=not args.no_color)}")
    lows = expire.level_alerts(items)
    if lows:
        print("\n常备品该补了：" + "、".join(f"{a['name']}（{a['have']:g}/{a['min']:g}）" for a in lows))
    return 0


def cmd_cook(args, store: Store) -> int:
    items = store.items()
    matches = recipe.match(items, limit=args.top)
    b = expire.daily_brief(items)
    print(_c(b["text"], BOLD, not args.no_color) + "\n")
    for m in matches:
        flag = _c("可以做", GRN, not args.no_color) if m.cookable else _c("差料", YEL, not args.no_color)
        use = f"  · 会用到临期：{'、'.join(m.uses_expiring)}" if m.uses_expiring else ""
        print(f"{_c(m.recipe['name'], BOLD, not args.no_color)}  "
              f"{m.recipe['time_min']}min  {flag}  覆盖 {m.coverage:.0%}  "
              f"{_c(f'({m.score:.0f}分)', DIM, not args.no_color)}")
        if m.missing:
            print("   缺：" + "、".join(f"{x.name}{x.need:g}{x.unit}" for x in m.missing))
        if use:
            print("   " + use.strip())
    return 0


def cmd_shop(args, store: Store) -> int:
    items = store.items()
    rows = shopping.build(items, recipe.match(items, limit=12))
    if args.sync:
        store.sync_shopping(rows)
        print(f"已同步 {len(rows)} 项到购物清单\n")
    if not rows:
        print("清单是空的：要么冰箱够满，要么常备品都在水位以上。")
        return 0
    for r in rows:
        src = "做菜缺料" if r["source"] == "recipe" else "常备补货"
        print(f"  [ ] {r['name']:<8}{r['qty']:g}{r['unit']:<4}{_c(src, DIM, not args.no_color)}"
              f"  {_c('｜' + '、'.join(r['why']), DIM, not args.no_color)}")
    return 0


def cmd_eat(args, store: Store) -> int:
    res = store.consume(args.id, None if args.all else args.qty)
    print(res)
    return 0 if res.get("ok") else 1


def cmd_trash(args, store: Store) -> int:
    res = store.waste(args.id)
    if res.get("ok"):
        print(f"已记一笔浪费：{res['name']} {res['wasted']:g}（到期日差 {res['days_left']} 天）")
    else:
        print(res)
    return 0 if res.get("ok") else 1


def cmd_stats(args, store: Store) -> int:
    s = store.stats()
    print(f"在库 {s['items']} 条 | 已过期 {s['expired']} | 7 天内到期 {s['soon']} | 常备待补 {s['level_low']}")
    print("位置分布：" + "  ".join(f"{k}{v}" for k, v in s["by_location"].items() if v))
    print(f"近 30 天：用过 {s['use_30d']} 次，扔掉 {s['waste_30d']} 次，"
          f"浪费率 {s['waste_rate_30d']:.0%}（{s['waste_qty_30d']:g} 份）")
    print(f"词典规模 {s['catalog_size']} 种")
    return 0


def cmd_seed(args, store: Store) -> int:
    store.reset()
    n = seed_mod.seed(store)
    print(f"已灌入 {n} 条演示数据 → {store.path}")
    return 0


def cmd_serve(args, store: Store) -> int:
    from .server import serve
    serve(store, host=args.host, port=args.port, open_browser=not args.no_browser)
    return 0


def cmd_export(args, store: Store) -> int:
    items = sort_for_action(store.items())
    lines = ["# 家里有什么 · 库存导出", "", f"导出时间：{date.today().isoformat()}", ""]
    for loc in ["冷藏", "冷冻", "常温", "橱柜", "阳台"]:
        group = [i for i in items if i.location == loc]
        if not group:
            continue
        lines.append(f"## {loc}（{len(group)}）")
        lines.append("")
        lines.append("| 食材 | 数量 | 到期 | 状态 |")
        lines.append("|---|---|---|---|")
        for i in group:
            lines.append(f"| {i.name} | {i.qty_text()} | {i.expires or '-'} | {STATUS_LABEL[i.status()]} |")
        lines.append("")
    out = "\n".join(lines)
    if args.out:
        from pathlib import Path
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(out, encoding="utf-8")
        print(f"已写入 {args.out}")
    else:
        print(out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="pantry", description="家里有什么 —— 冰箱库存 · 模糊记忆检索 · 清冰箱菜谱")
    p.add_argument("--db", default=None, help="SQLite 路径，默认 ~/.homepantry/pantry.db")
    p.add_argument("--no-color", action="store_true", help="关闭终端颜色")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="自然语言入库：add \"2盒牛奶 冷藏 7天\"")
    a.add_argument("text", nargs="+")
    a.add_argument("--loc", default=None, help="默认位置")

    l = sub.add_parser("ls", help="列出库存")
    l.add_argument("--loc", default=None)

    f = sub.add_parser("find", help="模糊检索：find 白色 粉末 / find nn")
    f.add_argument("query", nargs="+")

    b = sub.add_parser("brief", help="今天先吃哪三样")
    b.add_argument("-v", "--verbose", action="store_true")

    c = sub.add_parser("cook", help="用现有食材推荐菜谱")
    c.add_argument("--top", type=int, default=3)

    s = sub.add_parser("shop", help="生成购物清单")
    s.add_argument("--sync", action="store_true", help="写入数据库")

    e = sub.add_parser("eat", help="用掉：eat 12 --all")
    e.add_argument("id", type=int)
    e.add_argument("--qty", type=float, default=None)
    e.add_argument("--all", action="store_true")

    t = sub.add_parser("trash", help="扔掉（记浪费）：trash 12")
    t.add_argument("id", type=int)

    sub.add_parser("stats", help="统计与浪费账本")
    sub.add_parser("seed", help="重置并灌入演示数据")

    sv = sub.add_parser("serve", help="启动本地 Web 界面")
    sv.add_argument("--port", type=int, default=8765)
    sv.add_argument("--host", default="127.0.0.1")
    sv.add_argument("--no-browser", action="store_true")

    ex = sub.add_parser("export", help="导出 Markdown 库存表")
    ex.add_argument("--out", default=None)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.no_color = args.no_color or not sys.stdout.isatty()
    store = Store(args.db)
    handler = {
        "add": cmd_add, "ls": cmd_ls, "find": cmd_find, "brief": cmd_brief,
        "cook": cmd_cook, "shop": cmd_shop, "eat": cmd_eat, "trash": cmd_trash,
        "stats": cmd_stats, "seed": cmd_seed, "serve": cmd_serve, "export": cmd_export,
    }[args.cmd]
    try:
        return handler(args, store)
    finally:
        if args.cmd != "serve":
            store.close()


if __name__ == "__main__":
    raise SystemExit(main())
