"""模糊记忆检索：忘了名字也能搜到。

真实对话长这样：
    「我记得有一袋白色的粉」→ 面粉/淀粉/糖/盐
    「nn」→ 牛奶
    「那袋冻的 半月形」→ 饺子
    「牛乃」→ 牛奶（错别字）

所以分数 = 多种弱信号的叠加，且每个结果必须给出「为什么匹配」的理由，
让用户一眼判断对不对——这比给出一个黑箱 score 有用得多。
"""
from __future__ import annotations

from . import lexicon
from .model import Item, sort_for_action


def _edit_distance(a: str, b: str, cap: int = 2) -> int:
    """带上限的 Levenshtein，超过 cap 直接返回 cap+1（省时间也够用）。"""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > cap:
        return cap + 1
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i] + [0] * lb
        best = cur[0]
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
            best = min(best, cur[j])
        if best > cap:
            return cap + 1
        prev = cur
    return prev[lb]


def _score_token(item: Item, token: str) -> tuple[float, str]:
    """单个 token 对一个条目的匹配分。返回 (分数, 理由)。"""
    t = token.strip()
    if not t:
        return 0.0, ""
    name = item.name
    tl = t.lower()

    if name == t:
        return 100.0, "名称完全一致"

    aliases = lexicon.meta(name).get("aliases") or []
    if t in aliases:
        return 95.0, f"别名「{t}」→ {name}"

    if t in name or (len(name) >= 2 and name in t):
        return 88.0, "名称包含"

    py = lexicon.pinyin(name)
    ini = lexicon.initials(name)
    if py and tl.isascii():
        if py == tl:
            return 90.0, f"全拼 {tl} → {py}"
        if py.startswith(tl) and len(tl) >= 2:
            return 82.0, f"全拼前缀 {tl} → {py}"
    if ini and tl.isascii() and tl == ini:
        return 85.0, f"拼音首字母 {tl.upper()} → {name}"
    if ini and tl.isascii() and len(tl) >= 2 and ini.startswith(tl):
        return 74.0, f"首字母前缀 {tl.upper()} → {ini.upper()}"

    if len(t) >= 2 and len(name) >= 2:
        d = _edit_distance(t, name)
        if d <= 1:
            return 70.0, f"疑似错别字（编辑距离 {d}）"
        if py and tl.isascii():
            dp = _edit_distance(tl, py)
            if dp <= 1:
                return 66.0, f"拼写近似（{tl} ≈ {py}）"

    tags = lexicon.tags(name)
    for tag in tags:
        if t in tag or tag in t:
            return 60.0, f"特征标签「{tag}」"
    if t == lexicon.cat(name):
        return 50.0, f"分类「{t}」"
    if t and t in (item.note or ""):
        return 45.0, "备注命中"
    if t and t in (item.location or ""):
        return 30.0, f"位置「{item.location}」"
    return 0.0, ""


QUERY_STOP = [
    "我记得", "好像", "有一个", "有个", "那袋", "那个", "那盒", "一袋", "一包", "一盒",
    "一瓶", "一根", "一颗", "一把", "放在", "在", "里面", "大概", "应该", "的", "是", "有",
]


def tokenize(query: str) -> list[str]:
    q = (query or "").replace("　", " ")
    for w in QUERY_STOP:
        q = q.replace(w, " ")
    q = q.replace("，", " ").replace(",", " ").replace("、", " ")
    return [t for t in q.split() if t]


def search(items: list[Item], query: str, limit: int = 20) -> list[dict]:
    """多 token 采用 AND 语义，逐 token 取最高分，最终分取均值。"""
    tokens = tokenize(query)
    if not tokens:
        return [
            {**it.to_dict(), "score": 0.0, "reasons": ["（无关键词，按紧迫度排序）"]}
            for it in sort_for_action(items)[:limit]
        ]

    hits: list[dict] = []
    for it in items:
        total, ok, reasons = 0.0, True, []
        for tok in tokens:
            s, why = _score_token(it, tok)
            if s <= 0:
                ok = False
                break
            total += s
            reasons.append(why)
        if not ok:
            continue
        score = total / len(tokens)
        # 越紧急越靠前：同为 88 分时，明天到期的排在还早的前面
        bonus = {0: 6, 1: 5, 2: 4, 3: 2}.get(it.rank(), 0)
        hits.append({**it.to_dict(), "score": round(score + bonus, 1),
                     "reasons": reasons + [f"紧迫度加分 +{bonus}"] if bonus else reasons})

    hits.sort(key=lambda d: (-d["score"], d["days_left"] if d["days_left"] is not None else 10**6))
    return hits[:limit]


def why_text(hit: dict) -> str:
    return "；".join(hit.get("reasons") or [])
