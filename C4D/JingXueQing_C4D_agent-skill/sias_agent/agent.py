"""Agent 核心：ReAct 式工具循环 + 地图状态记忆 + 多轮对话。

这是一个真实可运行的 Agent，不是 demo 空壳：
- 模型自己决定调用哪个工具、带什么参数（原生 function calling）
- 工具返回真实计算结果，回灌给模型做下一步推理（多步）
- 落盘状态 → 支持后续「删掉图书馆」「换成 5 个点」这类多轮指令
- 每一步都写 trajectory.jsonl，作为可复核的证据
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import tools as T
from .config import ModelProfile, TRAJECTORY_PATH, DEFAULT_PROFILE
from .llm import LocalLLM, LLMResponse

SYSTEM = """你是一个运行在用户自己电脑上的离线地图助手 Agent。你的知识来源只有三个：
1) 你自己掌握的地理常识；2) 你调用工具拿到的真实计算结果；3) 当前对话历史。

铁律：
- 任何坐标、距离、时长都必须来自工具返回，禁止编造数字。
- 需要坐标就调用 geocode_local；需要周边地点就调用 search_poi；需要顺序路线就调用 route_plan。
- 一次可以连续调用多个工具，直到信息足够。
- 最后用中文给出简明结论，并说明哪些数据来自工具。
- 你完全离线运行，不依赖任何云端 API。

收集数据的正确方式：
- search_poi 的 category 要**分多次换不同类别**调用（例如先 campus，再 sight，再 museum），
  这样才能覆盖周边不同类型的地标。只查一个类别会漏掉大量地点。
- search_poi 的 keyword 不要填地名，地名用 geocode_local 查。
  若返回 relaxed=true，说明关键词与类别不匹配，此时应采纳放宽后的结果。
- markers 里不要放"中心点""定位点"这类没有信息量的占位条目，
  只放工具返回的真实地点。"""

# 西亚斯学院参照点（GCJ-02），用于幻觉坐标回拉与可达性计算
SIAS_CENTER = (34.4166, 113.7530)

FINAL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "地图标题"},
        "summary": {"type": "string", "description": "中文总结，2-4 句"},
        "markers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name_zh": {"type": "string"},
                    "name_en": {"type": "string"},
                    "category": {"type": "string",
                                 "enum": ["campus", "sight", "museum", "heritage",
                                          "transit", "nature", "city", "poi"]},
                    "latitude": {"type": "number"},
                    "longitude": {"type": "number"},
                    "desc_zh": {"type": "string"},
                    "desc_en": {"type": "string"},
                    "rating": {"type": "number"},
                },
                "required": ["name_zh", "name_en", "category",
                             "latitude", "longitude", "desc_zh", "desc_en", "rating"],
            },
        },
    },
    "required": ["title", "summary", "markers"],
}


@dataclass
class Turn:
    role: str
    content: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)
    stat: dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentRun:
    """一次完整任务的结果，含完整证据链。"""

    user_request: str
    profile_label: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    tool_trace: list[dict[str, Any]] = field(default_factory=list)
    final: dict[str, Any] = field(default_factory=dict)
    perf: dict[str, Any] = field(default_factory=dict)
    wall_seconds: float = 0.0
    state_diffs: list[str] = field(default_factory=list)


class MapAgent:
    def __init__(self, llm: LocalLLM, state: T.MapState,
                 trajectory: Path = TRAJECTORY_PATH,
                 max_tool_rounds: int = 4) -> None:
        self.llm = llm
        self.state = state
        self.trajectory = Path(trajectory)
        self.max_tool_rounds = max_tool_rounds
        # 记录几何自检的纠正动作，作为「模型幻觉被代码拦住」的可读证据
        self.grounding_fixes: list[str] = []

    # ------------------------------------------------------------ 工具循环
    def _tool_round(self, messages: list[dict[str, Any]],
                    run: AgentRun) -> list[dict[str, Any]]:
        """执行一轮工具调用。返回本轮产生的 observation 消息。"""
        resp: LLMResponse = self.llm.chat(messages, tools=T.ollama_schemas())
        run.steps.append({"kind": "llm", "text": resp.text[:800],
                          "tool_calls": resp.tool_calls, "stat": resp.stat.as_dict()})

        if not resp.tool_calls:
            return [{"role": "assistant", "content": resp.text}]

        messages.append({"role": "assistant", "content": resp.text or " ",
                         "tool_calls": resp.tool_calls})
        observations: list[dict[str, Any]] = []
        for tc in resp.tool_calls:
            fn = (tc.get("function") or {})
            name = fn.get("name", "")
            try:
                args = fn.get("arguments")
                args = json.loads(args) if isinstance(args, str) else (args or {})
            except json.JSONDecodeError:
                args = {"_raw": fn.get("arguments")}
            t0 = time.perf_counter()
            try:
                out = T.call(name, args)
                ok, err = True, None
            except Exception as e:  # noqa: BLE001 - 工具失败要回灌给模型让它自愈
                out, ok, err = {"error": str(e)}, False, str(e)
            dt = int((time.perf_counter() - t0) * 1000)
            rec = {"tool": name, "args": args, "ok": ok, "error": err,
                   "latency_ms": dt, "result": out}
            run.tool_trace.append(rec)
            observations.append({
                "role": "tool", "tool_name": name,
                "content": json.dumps(out, ensure_ascii=False)[:1200],
            })
        return observations

    # ------------------------------------------------------------ 主任务
    def run(self, user_request: str, *, force_new_map: bool = True) -> AgentRun:
        t_start = time.perf_counter()
        p: ModelProfile = self.llm.profile
        run = AgentRun(user_request=user_request, profile_label=p.label)

        before = {m["id"] for m in self.state.markers}
        if force_new_map:
            self.state.replace_all([])

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"用户需求：{user_request}\n\n"
                "请先调用工具收集真实数据（至少一次 geocode_local 或 search_poi），"
                "然后完成需求。")},
        ]

        # ---- 阶段一：Agent 自主工具循环（最多 max_tool_rounds 轮）
        for _ in range(self.max_tool_rounds):
            obs = self._tool_round(messages, run)
            messages.extend(obs)
            if not any(o.get("role") == "tool" for o in obs):
                break  # 模型不再要工具，进入结构化产出

        # ---- 阶段二：结构化产出（喂入全部工具观测，强制 JSON schema）
        obs_dump = json.dumps(run.tool_trace, ensure_ascii=False)[:2500]
        messages.append({"role": "user", "content": (
            "现在基于以上工具返回的真实数据，输出最终 JSON。\n"
            "markers 至少 5 个，每个都要有中英文名称、类别、经纬度、中英文描述、评分。\n"
            "经纬度直接引用工具结果，不要改动。\n\n"
            f"工具观测记录：{obs_dump}")})
        data = self.llm.json_chat(messages, FINAL_SCHEMA)

        # ---- 阶段三：几何自检（把模型的坐标拉回真实范围）
        markers = self._sanitize(data.get("markers") or [])
        run.final = {
            "title": (data.get("title") or "SIAS 周边地图")[:80],
            "summary": data.get("summary") or "",
            "markers": markers,
        }
        run.wall_seconds = round(time.perf_counter() - t_start, 2)
        run.perf = self.llm.perf_summary()
        self._log(run, before)
        return run

    # ------------------------------------------------------------ 几何自检
    def _sanitize(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """模型输出的几何与内容自检。

        三道闸，任何一道都能拦住一类真实踩过的坑：
        1. 坐标非法（非数字 / 越界）→ 丢弃该点。
        2. 名称能匹配本地知识库 → **强制吸附到知识库坐标**。
           实测踩坑：让模型"加一个开封"，它给出 34.509,113.405，
           而知识库里开封是 34.797,114.307 —— 偏差约 50km，JSON 合法、描述通顺，
           肉眼极难发现。凡是知识库里有这个名字，就必须用知识库的坐标。
        3. 名称不在知识库且离郑州 >500km → 判定为幻觉，拉回校园附近。
        """
        out: list[dict[str, Any]] = []
        for i, m in enumerate(raw[:12]):
            try:
                lat = float(m.get("latitude"))
                lng = float(m.get("longitude"))
            except (TypeError, ValueError):
                continue
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                continue

            name = str(m.get("name_zh") or "")
            orig = (lat, lng)
            grounded, drift = self._ground(name, lat, lng)
            if grounded is not None:
                lat, lng = grounded
            elif T.haversine((lat, lng), SIAS_CENTER) > 500:
                lat, lng = SIAS_CENTER[0] + 0.002 * i, SIAS_CENTER[1] + 0.002 * i
                drift = T.haversine(orig, SIAS_CENTER)

            out.append({
                "id": m.get("id") or f"m{i + 1}",
                "name_zh": name[:40] or "未命名",
                "name_en": str(m.get("name_en") or "Unnamed")[:60],
                "category": str(m.get("category") or "poi")[:24],
                "latitude": round(lat, 6),
                "longitude": round(lng, 6),
                "desc_zh": str(m.get("desc_zh") or "")[:180],
                "desc_en": str(m.get("desc_en") or "")[:220],
                "rating": round(float(m.get("rating") or 4.0), 1),
                "source": "local-gemma4" + ("+grounded" if grounded is not None else ""),
            })
            if drift and drift > 0.5:
                self.grounding_fixes.append(
                    f"{name}: 模型输出 ({orig[0]:.4f},{orig[1]:.4f}) 被纠正为 "
                    f"权威坐标 ({lat:.4f},{lng:.4f})，偏差 {drift:.1f}km")
        return out

    @staticmethod
    def _ground(name: str, lat: float, lng: float) -> tuple[tuple[float, float] | None, float]:
        """名称命中知识库则返回权威坐标 + 原始偏差(km)。"""
        if not name:
            return None, 0.0
        q = T._normalize(name)
        if not q:
            return None, 0.0
        best, best_s = None, 0.0
        for p in T.KNOWLEDGE_BASE:
            hay = T._normalize(f"{p.name_zh} {p.name_en} {' '.join(p.tags)}")
            s = 1.0 if q in hay or hay in q else 0.0
            if not s and len(q) >= 2:
                a, b = T._ngrams(q), T._ngrams(hay)
                if a and b:
                    s = 0.9 * len(a & b) / len(a)
            if s > best_s:
                best, best_s = p, s
        if best is None or best_s < 0.6:
            return None, 0.0
        drift = T.haversine((lat, lng), (best.lat, best.lng))
        return (best.lat, best.lng), drift

    def _log(self, run: AgentRun, before: set[str]) -> None:
        after = {m["id"] for m in self.state.markers}
        run.state_diffs = [f"+{i}" for i in sorted(after - before)] + \
                          [f"-{i}" for i in sorted(before - after)]
        self.trajectory.parent.mkdir(parents=True, exist_ok=True)
        with self.trajectory.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                "request": run.user_request,
                "profile": run.profile_label,
                "tool_trace": run.tool_trace,
                "marker_count": len(run.final.get("markers", [])),
                "perf": run.perf.get("mean_tok_per_s"),
                "wall_seconds": run.wall_seconds,
            }, ensure_ascii=False) + "\n")

    # ------------------------------------------------------------ 多轮编辑
    def edit(self, instruction: str) -> dict[str, Any]:
        """多轮对话：让模型把指令翻译成对地图状态的操作（增/删/改）。"""
        current = json.dumps(self.state.markers, ensure_ascii=False)[:2500]
        schema = {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["add", "remove", "update", "regenerate"]},
                "target_id": {"type": "string", "description": "remove/update 时使用"},
                "marker": {
                    "type": "object",
                    "properties": {
                        "name_zh": {"type": "string"}, "name_en": {"type": "string"},
                        "category": {"type": "string"},
                        "latitude": {"type": "number"}, "longitude": {"type": "number"},
                        "desc_zh": {"type": "string"}, "desc_en": {"type": "string"},
                        "rating": {"type": "number"},
                    },
                },
                "reply_zh": {"type": "string", "description": "给用户的中文回复"},
            },
            "required": ["action", "reply_zh"],
        }
        resp = self.llm.json_chat(
            [{"role": "system", "content": SYSTEM},
             {"role": "user", "content": (
                 f"当前地图标记：{current}\n\n用户修改指令：{instruction}\n"
                 "输出 JSON：action 为 add/remove/update/regenerate 之一；"
                 "remove/update 时给出 target_id；add 时给出完整 marker。")}],
            schema)

        act = resp.get("action", "update")
        reply = resp.get("reply_zh", "已处理")
        target = str(resp.get("target_id") or "")
        if act == "add" and resp.get("marker"):
            self.state.add(self._sanitize([resp["marker"]])[0])
            reply += f"（已添加 {resp['marker'].get('name_zh')}）"
        elif act == "remove":
            ok = self.state.remove(target)
            reply += "（已删除）" if ok else f"（未找到 id={target}）"
        elif act == "update" and resp.get("marker"):
            for m in self.state.markers:
                if m["id"] == target:
                    new = self._sanitize([{**m, **resp["marker"]}])[0]
                    m.update(new)
                    self.state.save()
                    break
            reply += "（已更新）"
        elif act == "regenerate":
            reply += "（请用 run 重新生成）"
        return {"action": act, "reply": reply,
                "perf": self.llm.perf_summary()["mean_tok_per_s"]}
