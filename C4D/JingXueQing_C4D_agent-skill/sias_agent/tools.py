"""工具注册表 + 工具实现。

设计原则：每个工具都必须是**真实可执行**的，而不是给模型看的空壳。
- `geocode_local`  : 内置坐标库 + 模糊匹配 + 距离估算（离线可用）
- `search_poi`     : 按关键词/类别在本地知识库检索（离线可用）
- `route_plan`     : 多点路径规划 + haversine 里程/时长（离线可用）
- `add_marker`     : 修改 Agent 状态（地图标记），Agent 记忆的核心
- `list_markers`   : 读回状态，支撑多轮对话
- `score_poi`      : 对候选点做可解释打分（离线可用）
- `reverse_geocode`: 反查（基于本地坐标库最近邻）

在线能力（腾讯地图地点搜索/路线规划）通过 tools/online.py 可选接入，
默认关闭，保证「断网也能跑」这一 C4D 核心主张。
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable

EARTH_R = 6371.0088  # km, IUGG 平均半径


def haversine(a: tuple[float, float], b: tuple[float, float]) -> float:
    """两点大圆距离（km）。输入为 (lat, lng)。"""
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_R * math.asin(math.sqrt(h))


# ---------------------------------------------------------------- 知识库
@dataclass
class POI:
    key: str
    name_zh: str
    name_en: str
    category: str
    lat: float
    lng: float
    desc_zh: str
    desc_en: str
    rating: float = 4.0
    tags: list[str] = field(default_factory=list)


# 西亚斯学院（SIAS University，郑州·新郑）为核心，附带周边真实地标
# 坐标为 GCJ-02（WGS84 偏移后），量级与真实位置一致。
KNOWLEDGE_BASE: list[POI] = [
    POI("sias_main", "西亚斯学院-图书馆", "SIAS Library", "campus", 34.4166, 113.7530,
        "学校标志性建筑，馆藏丰富，安静的自习与查阅空间。",
        "The landmark library of campus, quiet for study and research.",
        4.7, ["地标", "自习"]),
    POI("sias_gate", "西亚斯学院-南门", "SIAS South Gate", "campus", 34.4150, 113.7510,
        "主入口，进出校园与访客登记处。",
        "Main entrance and visitor registration point.", 4.2, ["入口"]),
    POI("sias_arts", "西亚斯学院-艺术中心", "SIAS Arts Center", "campus", 34.4175, 113.7545,
        "演出与展览空间，常有学生社团活动。",
        "Performance and exhibition space for student clubs.", 4.5, ["演出", "社团"]),
    POI("sias_dorm", "西亚斯学院-学生公寓", "SIAS Dormitories", "campus", 34.4142, 113.7548,
        "住宿区，靠近生活超市与食堂。",
        "Housing area near dining hall and supermarket.", 4.1, ["住宿"]),
    POI("huanghe", "黄河故里旅游区", "Yellow River Hometown", "sight", 34.4520, 113.7180,
        "黄河文化主题景区，冬季有民俗活动。",
        "Yellow River culture theme scenic area.", 4.4, ["自然", "文化"]),
    POI("zhengzhou_museum", "郑州博物馆", "Zhengzhou Museum", "museum", 34.4270, 113.7620,
        "了解中原历史与商都脉络的首选。",
        "Top pick for Henan history and Shang dynasty heritage.", 4.6, ["博物馆"]),
    POI("erqi_tower", "二七纪念塔", "Erqi Memorial Tower", "heritage", 34.7460, 113.6650,
        "郑州地标，纪念京汉铁路工人大罢工。",
        "Landmark commemorating the 1923 railway workers' strike.", 4.5, ["历史"]),
    POI("xinzheng_rail", "新郑北站", "Xinzheng North Station", "transit", 34.4275, 113.7530,
        "高铁站，可直达郑州东站与郑州航空港。",
        "HSR station linking Zhengzhou East and the airport zone.", 4.0, ["交通"]),
    POI("hongshan", "嵩山", "Mount Song", "nature", 34.4800, 113.0500,
        "少林寺所在地，中岳嵩山，世界文化遗产。",
        "Home of Shaolin Temple, a UNESCO World Heritage mountain.",
        4.9, ["世界遗产", "少林寺", "Shaolin"]),
    POI("kaifeng", "开封", "Kaifeng", "city", 34.7970, 114.3070,
        "八朝古都，清明上河园与美食。",
        "Eight-dynasty ancient capital, famous for cuisine.", 4.7, ["古城", "美食"]),
]


def _to_dict(p: POI) -> dict[str, Any]:
    d = asdict(p)
    d["latitude"], d["longitude"] = d.pop("lat"), d.pop("lng")
    return d


# ---------------------------------------------------------------- 工具实现
class ToolError(RuntimeError):
    pass


_SEP = re.compile(r"[\s\-_·、，,。/()（）\[\]]+")


def _normalize(s: str) -> str:
    """归一化：去分隔符 + 小写。让「西亚斯学院图书馆」能命中「西亚斯学院-图书馆」。"""
    return _SEP.sub("", (s or "").lower())


def _ngrams(s: str, n: int = 2) -> set[str]:
    return {s[i:i + n] for i in range(max(0, len(s) - n + 1))}


def t_geocode_local(name: str, **_: Any) -> dict[str, Any]:
    """在本地坐标库中做模糊地理编码。三级匹配：精确包含 → 字符 bigram 相似度 → 兜底。"""
    q = _normalize(name)
    if not q:
        raise ToolError("name 不能为空")
    scored: list[tuple[float, POI]] = []
    for p in KNOWLEDGE_BASE:
        hay_raw = f"{p.key} {p.name_zh} {p.name_en} {p.category} {' '.join(p.tags)}"
        hay = _normalize(hay_raw)
        s = 1.0 if q in hay else 0.0
        s += sum(0.3 for t in re.split(r"[\s,，、]+", (name or "").strip().lower()) if t and t in hay_raw.lower())
        # bigram 相似度：处理语序变化与部分命中
        if s == 0.0 and len(q) >= 2:
            a, b = _ngrams(q), _ngrams(hay)
            if a and b:
                s = 0.8 * len(a & b) / len(a)
        if s:
            scored.append((s, p))
    if not scored or max(s for s, _ in scored) < 0.25:
        # 兜底：以西亚斯学院为参照点给一个合理默认区域，避免链路中断
        return {
            "matched": False,
            "query": name,
            "latitude": 34.4166,
            "longitude": 113.7530,
            "confidence": 0.0,
            "note": "本地库未命中，已回落到 SIAS 校园中心点",
        }
    scored.sort(key=lambda x: -x[0])
    s, p = scored[0]
    return {"matched": True, "query": name, "latitude": p.lat, "longitude": p.lng,
            "confidence": round(min(s / 2.0, 1.0), 2), "place": p.name_zh}


def t_reverse_geocode(lat: float | None = None, lng: float | None = None, **kw: Any) -> dict[str, Any]:
    """反查最近地标。

    同时接受 lat/lng 与 latitude/longitude 两种命名——小模型经常混用，
    工具层应当吸收这种噪声，而不是把一次调用变成一次失败。
    """
    lat = lat if lat is not None else kw.get("latitude")
    lng = lng if lng is not None else kw.get("longitude", kw.get("lng"))
    if lat is None or lng is None:
        raise ToolError("缺少坐标参数（lat/lng 或 latitude/longitude）")
    lat, lng = float(lat), float(lng)
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ToolError(f"坐标非法: ({lat}, {lng})")
    best = min(KNOWLEDGE_BASE, key=lambda p: haversine((lat, lng), (p.lat, p.lng)))
    d = haversine((lat, lng), (best.lat, best.lng))
    return {"nearest": best.name_zh, "name_en": best.name_en,
            "latitude": best.lat, "longitude": best.lng,
            "distance_km": round(d, 3)}


def t_search_poi(keyword: str = "", category: str = "", limit: int = 6, **_: Any) -> dict[str, Any]:
    """按关键词/类别检索本地 POI 库。

    关键词与类别是 AND 关系。但实测发现模型经常传入
    「类别=景点 + 关键词=某地名」这种组合（如 category=sight, keyword="SIAS University"），
    严格 AND 会返回空列表，导致 Agent 认为"周边没有景点"而提前收工。
    因此：严格 AND 无结果时，退化为「仅按类别」再试一次，并在返回值里
    显式标注 relaxed=true，让模型知道这是放宽后的结果。
    """
    kws = [k for k in re.split(r"[\s,，、]+", (keyword or "").strip().lower()) if k]

    def run(kw_filter: list[str], cat: str) -> list[dict[str, Any]]:
        hits = []
        for p in KNOWLEDGE_BASE:
            if cat and p.category != cat:
                continue
            hay = (f"{p.name_zh} {p.name_en} {p.desc_zh} {p.desc_en} "
                   f"{' '.join(p.tags)}").lower()
            if kw_filter and not any(k in hay for k in kw_filter):
                continue
            hits.append(_to_dict(p))
        return hits

    strict = run(kws, category)
    relaxed = False
    hits = strict
    if not hits and kws and category:
        hits = run([], category)      # 放宽：只要类别
        relaxed = True
    if not hits and kws and not category:
        hits = run([], "")            # 再放宽：全库
        relaxed = True

    hits.sort(key=lambda x: -float(x.get("rating", 0)))
    return {"count": len(hits), "results": hits[: max(1, int(limit))],
            "relaxed": relaxed,
            "note": ("关键词与类别组合无结果，已放宽为仅按类别/全库检索"
                     if relaxed else "")}


def t_route_plan(points: list[list[float]], mode: str = "walking", **_: Any) -> dict[str, Any]:
    """按顺序串联多点，返回逐段里程与总时长（haversine + 速度模型）。"""
    if not points or len(points) < 2:
        raise ToolError("points 至少需要 2 个 [lat, lng]")
    speed = {"walking": 4.8, "cycling": 14.0, "driving": 26.0}.get(mode, 4.8)
    legs, total = [], 0.0
    for i in range(len(points) - 1):
        d = haversine(tuple(points[i]), tuple(points[i + 1]))
        total += d
        legs.append({"from": points[i], "to": points[i + 1],
                     "distance_km": round(d, 3), "minutes": round(d / speed * 60, 1)})
    return {"mode": mode, "legs": legs, "total_distance_km": round(total, 3),
            "total_minutes": round(total / speed * 60, 1)}


def t_score_poi(latitude: float, longitude: float, rating: float = 4.0,
                category: str = "sight", **_: Any) -> dict[str, Any]:
    """可解释打分：评分权重 + 距 SIAS 中心的可达性权重。"""
    center = (34.4166, 113.7530)
    d = haversine((latitude, longitude), center)
    access = max(0.0, 1.0 - d / 60.0)          # 60km 外归零
    r = max(0.0, min(5.0, float(rating)))
    score = 0.65 * (r / 5.0) + 0.35 * access
    return {"score": round(score * 100, 1), "distance_km": round(d, 2),
            "explain": {"rating_component": round(0.65 * r / 5, 3),
                        "access_component": round(0.35 * access, 3)}}


@dataclass
class ToolSpec:
    name: str
    fn: Callable[..., Any]
    description: str
    schema: dict[str, Any]

    def ollama_tool(self) -> dict[str, Any]:
        return {"type": "function",
                "function": {"name": self.name,
                             "description": self.description,
                             "parameters": self.schema}}


TOOLS: list[ToolSpec] = [
    ToolSpec("geocode_local", t_geocode_local,
             "把地名/关键词解析为坐标(纬度,经度)，离线可用。",
             {"type": "object",
              "properties": {"name": {"type": "string", "description": "地点名称或关键词"}},
              "required": ["name"]}),
    ToolSpec("reverse_geocode", t_reverse_geocode,
             "给定坐标，返回最近的地标名称与距离。",
             {"type": "object",
              "properties": {"lat": {"type": "number", "description": "纬度"},
                             "lng": {"type": "number", "description": "经度"}},
              "required": ["lat", "lng"]}),
    ToolSpec("search_poi", t_search_poi,
             "在本地知识库中检索地点，可按关键词或类别过滤。",
             {"type": "object",
              "properties": {"keyword": {"type": "string"},
                             "category": {"type": "string",
                                          "enum": ["campus", "sight", "museum",
                                                   "heritage", "transit", "nature", "city"]},
                             "limit": {"type": "integer", "description": "返回数量，默认6"}},
              "required": ["keyword"]}),
    ToolSpec("route_plan", t_route_plan,
             "对多个坐标做顺序路线规划，返回每段距离、时长和总计。",
             {"type": "object",
              "properties": {"points": {"type": "array", "items": {"type": "array",
                                "items": {"type": "number"}, "minItems": 2, "maxItems": 2},
                                "description": "[[lat,lng], ...]"},
                             "mode": {"type": "string",
                                      "enum": ["walking", "cycling", "driving"]}},
              "required": ["points"]}),
    ToolSpec("score_poi", t_score_poi,
             "对候选地点做可解释打分（评分 + 可达性）。",
             {"type": "object",
              "properties": {"latitude": {"type": "number"}, "longitude": {"type": "number"},
                             "rating": {"type": "number"}, "category": {"type": "string"}},
              "required": ["latitude", "longitude", "rating"]}),
]

BY_NAME = {t.name: t for t in TOOLS}


def call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    spec = BY_NAME.get(name)
    if not spec:
        raise ToolError(f"未知工具: {name}（可用: {list(BY_NAME)}）")
    try:
        return spec.fn(**(args or {}))
    except TypeError as e:
        raise ToolError(f"工具 {name} 参数不匹配: {e}") from e


def ollama_schemas() -> list[dict[str, Any]]:
    return [t.ollama_tool() for t in TOOLS]


# ---------------------------------------------------------------- 记忆
class MapState:
    """Agent 的可变状态：地图标记。多轮对话靠它保持上下文。"""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self.markers: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            try:
                self.markers = json.loads(self.path.read_text("utf-8")).get("markers", [])
            except Exception:  # noqa: BLE001
                self.markers = []

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"markers": self.markers}, ensure_ascii=False, indent=2), "utf-8")

    def add(self, m: dict[str, Any]) -> dict[str, Any]:
        mid = m.get("id") or f"m{len(self.markers) + 1}"
        m["id"] = mid
        if not any(x["id"] == mid for x in self.markers):
            self.markers.append(m)
        self.save()
        return m

    def remove(self, mid: str) -> bool:
        n = len(self.markers)
        self.markers = [x for x in self.markers if x["id"] != mid]
        self.save()
        return len(self.markers) < n

    def replace_all(self, ms: list[dict[str, Any]]) -> None:
        self.markers = ms
        self.save()

    def __len__(self) -> int:
        return len(self.markers)
