#!/usr/bin/env python3
"""家里有什么 · C9 MVP（单文件，零依赖，直接运行）

    python3 JingXueQing_C9_mvp.py

这个文件是第一周「先证明闭环成立」的产物：输入一句话 → 存下来 → 忘名字也能查回来
→ 告诉你今天先吃哪样 → 用剩下的做一道菜。全部在内存里跑完，不联网、不装包。

它与同目录 homepantry/ 的关系：
  · 这里是 200 行的最小闭环，规则只有 6 条，词表只有 10 个食材、4 道菜。
  · homepantry/ 是同一套规则做扎实后的版本（78 个食材、22 道菜谱、54 个测试、
    Web 界面、SQLite 持久化、浪费账本）。
  · 两版共用同一套设计判断，MVP 不是废稿，是 V1 的骨架被抽出来跑了一遍。
"""
from __future__ import annotations

import re
import sqlite3
from datetime import date, timedelta

TODAY = date.today()

# ---------------------------------------------------------------- 1. 词典
# 名字 → (别名, 冷藏保质天数, 拼音首字母, 特征标签)
LEX = {
    "牛奶": (["鲜奶"], 7, "nn", ["白色", "液体"]),
    "鸡蛋": (["蛋"], 30, "jd", ["椭圆"]),
    "番茄": (["西红柿"], 7, "fq", ["红色", "圆"]),
    "白菜": (["大白菜"], 14, "bc", ["白色", "叶菜"]),
    "豆腐": (["嫩豆腐"], 3, "df", ["白色", "方块"]),
    "猪肉": (["瘦肉"], 3, "zr", ["红色", "生"]),
    "面粉": (["白面"], 180, "mf", ["白色", "粉末", "袋装"]),
    "盐": (["食盐"], 365, "y", ["白色", "粉末"]),
    "葱": (["小葱"], 7, "c", ["绿色", "叶菜"]),
    "剩菜": (["剩饭"], 2, "sc", ["熟食", "碗装"]),
}

# ---------------------------------------------------------------- 2. 菜谱
RECIPES = [
    ("番茄炒蛋", [("番茄", 2, True), ("鸡蛋", 3, True), ("葱", 1, False)]),
    ("麻婆豆腐", [("豆腐", 1, True), ("猪肉", 100, True), ("葱", 1, False)]),
    ("醋溜白菜", [("白菜", 1, True), ("葱", 1, False)]),
    ("牛奶蒸蛋", [("牛奶", 1, True), ("鸡蛋", 2, True)]),
]

CN_NUM = {"一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "半": 0.5}
UNIT = r"(个|只|盒|袋|瓶|包|根|颗|把|块|碗|斤|两|克|g|ml)"


# ---------------------------------------------------------------- 3. 入库解析
def parse(line: str) -> dict:
    """把「2盒牛奶 冷藏 7天」拆成结构化的一条。只有 4 步，但覆盖 80% 的说法。"""
    text = line.strip()
    reasons = []

    # 位置：词表里出现了哪个就用哪个（默认冷藏）
    loc = "冷藏"
    for word, canon in (("冷冻", "冷冻"), ("冰柜", "冷冻"), ("橱柜", "橱柜"),
                        ("常温", "常温"), ("冷藏", "冷藏"), ("冰箱", "冷藏")):
        if word in text:
            loc = canon
            break
    reasons.append(f"位置 {loc}")

    # 保质期：说「N天」就按 N 天
    m = re.search(r"(\d+)\s*天", text)
    days = int(m.group(1)) if m else None

    # 数量 + 量词：量词位优先，所以「一两花椒」不会变成 12
    qty, unit = 1.0, ""
    mq = re.search(r"(\d+(?:\.\d+)?|[一二两三四五六七八九十半])\s*" + UNIT, text)
    if mq:
        raw = mq.group(1)
        qty = float(raw) if re.fullmatch(r"[\d.]+", raw) else CN_NUM.get(raw, 1)
        unit = mq.group(2)

    # 名称：在文本里找最长命中的词典词
    name, alias_index = None, {a: k for k, v in LEX.items() for a in v[0]}
    for word in sorted(list(LEX) + list(alias_index), key=len, reverse=True):
        if word in text:
            name = alias_index.get(word, word)
            break

    if name is None:
        name = re.sub(r"[\d\s]|" + UNIT, "", text)[:6] or "未识别"
        reasons.append("未收录词，已标注待确认")
    else:
        reasons.append(f"识别为 {name}")

    if days is None:
        days = LEX.get(name, ("", 7))[1]
        reasons.append(f"没说到期，按品类常识给 {days} 天")

    return {"name": name, "qty": qty, "unit": unit, "loc": loc,
            "exp": TODAY + timedelta(days=days), "reasons": reasons}


# ---------------------------------------------------------------- 4. 存储
def db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE item(name TEXT, qty REAL, unit TEXT, loc TEXT, exp TEXT)")
    return conn


def add(conn, row):
    conn.execute("INSERT INTO item VALUES(?,?,?,?,?)",
                 (row["name"], row["qty"], row["unit"], row["loc"], row["exp"].isoformat()))


def all_items(conn):
    return [dict(zip(["name", "qty", "unit", "loc", "exp"], r))
            for r in conn.execute("SELECT * FROM item")]


# ---------------------------------------------------------------- 5. 忘记名字也能搜
def search(conn, query):
    """三路合一的打分：名称包含 / 拼音首字母 / 特征标签。"""
    hits = []
    for it in all_items(conn):
        meta = LEX.get(it["name"])
        aliases, _, ini, tags = (meta if meta else ([], 0, "", []))
        score, why = 0, []
        if query in it["name"] or it["name"] in query:
            score += 90; why.append("名称命中")
        if query in aliases:
            score += 85; why.append("别名命中")
        if ini and query.lower() == ini:
            score += 80; why.append(f"拼音首字母 {ini}")
        for tag in tags:
            if query in tag or tag in query:
                score += 55; why.append(f"特征「{tag}」")
        if score:
            hits.append({**it, "score": score, "why": why})
    return sorted(hits, key=lambda h: -h["score"])


# ---------------------------------------------------------------- 6. 今天先吃 / 做什么
def brief(conn):
    rows = []
    for it in all_items(conn):
        left = (date.fromisoformat(it["exp"]) - TODAY).days
        if left <= 7:
            rows.append((left, it["name"]))
    rows.sort()
    if not rows:
        return "今天没有要抢的食材。"
    head = "、".join(f"{n}（{'已过期' if d < 0 else str(d) + ' 天后'}）" for d, n in rows[:3])
    return "今天先吃：" + head


def cook(conn):
    have = {i["name"]: i["qty"] for i in all_items(conn)}
    out = []
    for name, ings in RECIPES:
        main_ok = all(have.get(n, 0) >= q * 0.5 for n, q, main in ings if main)
        got = sum(1 for n, q, main in ings if have.get(n, 0) >= q * 0.5)
        if main_ok:
            out.append((got / len(ings), name, [n for n, q, main in ings if have.get(n, 0) < q * 0.5]))
    return sorted(out, reverse=True)


# ---------------------------------------------------------------- 7. 跑一次完整闭环
def main():
    print("=" * 62)
    print("家里有什么 · MVP 演示（单文件 / 零依赖 / 不联网）")
    print("=" * 62)

    conn = db()
    for line in ["2盒牛奶 冷藏 7天", "3个鸡蛋 冷藏 20天", "两个西红柿 冷藏 5天",
                 "一盒豆腐 冷藏 3天", "半颗白菜", "一碗剩菜 冷藏 1天", "一袋面粉 橱柜 30天"]:
        row = parse(line)
        add(conn, row)
        print(f"\n[入库] {line}")
        print(f"       → {row['name']} {row['qty']:g}{row['unit']} 放{row['loc']}，{row['exp']} 到期")
        print(f"       依据：{'；'.join(row['reasons'])}")

    print("\n" + "-" * 62)
    print("[忘了名字] 搜「粉末」——我记得是一袋白色的粉，忘了叫什么")
    for h in search(conn, "粉末"):
        print(f"       {h['score']:>3} 分  {h['name']:<4} {h['qty']:g}{h['unit']}  ({'、'.join(h['why'])})")

    print("\n[忘了名字] 搜「nn」（拼音首字母）")
    for h in search(conn, "nn"):
        print(f"       {h['score']:>3} 分  {h['name']:<4} {h['qty']:g}{h['unit']}  ({'、'.join(h['why'])})")

    print("\n" + "-" * 62)
    print("[预警] " + brief(conn))

    print("\n[现在能做什么]（按现有食材覆盖率）")
    for cover, name, miss in cook(conn):
        tail = f" 缺 {'、'.join(miss)}" if miss else ""
        print(f"       {cover:>4.0%}  {name}{tail}")

    print("\n" + "=" * 62)
    print("闭环成立：一句话进得去，一句话问得出来，剩下的菜能被吃掉。")
    print("下一版把它做扎实 → 见同目录 homepantry/（78 食材 / 22 菜谱 / 54 测试 / Web 界面）")


if __name__ == "__main__":
    main()
