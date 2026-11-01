#!/usr/bin/env python3
"""C4D 本地大模型 Agent 技能 —— 命令行入口。

用法：
  python run_agent.py doctor                     # 检查本地 Ollama 与设备信息
  python run_agent.py map "给我生成一个 SIAS University 周边的地图"
  python run_agent.py chat                       # 多轮对话，交互式增删改标记
  python run_agent.py bench --profiles e2b-q4,e2b-q8   # Level 4 模型对比
  python run_agent.py selftest                   # 工具层单测（无需模型）

所有命令都会把 JSON 报告写到 reports/ 下，作为可复核证据。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from sias_agent import tools as T                              # noqa: E402
from sias_agent.agent import MapAgent                          # noqa: E402
from sias_agent.config import (DATA_DIR, PROFILES, STATE_PATH,  # noqa: E402
                               ModelProfile, collect_server_info,
                               resolve_profile)
from sias_agent.llm import LocalLLM, OllamaUnavailable          # noqa: E402
from sias_agent.map_render import write_map                    # noqa: E402

REPORTS = HERE / "reports"


def _save(name: str, obj: object) -> Path:
    # 沙箱环境下 exist_ok=True 的 mkdir 会抛 EEXIST，先探测再建
    if not REPORTS.is_dir():
        REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), "utf-8")
    return p


def _hdr() -> None:
    print("=" * 72)
    print("C4D · 本地大模型 Agent 技能  |  全部推理在你自己电脑上完成，零 API 费用")
    print("=" * 72)


# ------------------------------------------------------------ doctor
def cmd_doctor(args: argparse.Namespace) -> int:
    _hdr()
    info = collect_server_info()
    d = info.device
    print(f"\n[设备] {d['chip']} / {d['memory_gb']} GB RAM / {d['os']}")
    print(f"       {d['logical_cores']} 逻辑核 · 可用磁盘 {d['disk_avail']} · Python {d['python']}")
    print(f"\n[运行时] Ollama v{info.ollama_version} @ http://127.0.0.1:11434")
    if not info.models:
        print("\n[⚠️] 没有检测到本地模型。请先执行：")
        print("       ollama pull gemma4:e2b-it-q4_K_M")
        _save("doctor.json", info.as_dict())
        return 2
    print("\n[本地已装模型]")
    for m in info.models:
        sz = m.get("size", 0) / 1e9
        det = m.get("details", {}) or {}
        print(f"       · {m['name']:<32} {sz:5.2f} GB  {det.get('quantization_level','-')}"
              f"  {det.get('parameter_size','-')}")
    print("\n[档位预设]")
    for k, p in PROFILES.items():
        print(f"       {k:<10} {p.label}")
    p = _save("doctor.json", info.as_dict())
    print(f"\n报告已写入：{p}")
    return 0


# ------------------------------------------------------------ map
def cmd_map(args: argparse.Namespace) -> int:
    _hdr()
    prof = resolve_profile(args.profile)
    llm = LocalLLM(prof)
    state = T.MapState(STATE_PATH)
    agent = MapAgent(llm, state)

    print(f"\n[模型] {prof.label}")
    print(f"[任务] {args.request}\n")
    try:
        run = agent.run(args.request)
    except OllamaUnavailable as e:
        print(f"\n[✗] {e}")
        return 3

    print("[工具调用轨迹]")
    for i, t in enumerate(run.tool_trace, 1):
        flag = "✓" if t["ok"] else "✗"
        print(f"  {flag} {i}. {t['tool']}({json.dumps(t['args'], ensure_ascii=False)[:70]})"
              f"  {t['latency_ms']}ms")
    print(f"\n[结构化输出] title={run.final['title']!r}")
    print(f"            markers={len(run.final['markers'])} 个")
    print(f"[性能] {run.perf.get('calls')} 次本地调用 · "
          f"平均 {run.perf.get('mean_tok_per_s')} tok/s · 总耗时 {run.wall_seconds}s")

    state.replace_all(run.final["markers"])
    srv = collect_server_info()
    evidence = {
        "模型": prof.ollama_tag,
        "量化": prof.quantization,
        "上下文": f"{prof.num_ctx} tokens",
        "运行时": f"Ollama v{srv.ollama_version}",
        "设备": f"{srv.device['chip']} / {srv.device['memory_gb']}GB / {srv.device['os']}",
        "实测速度": f"{run.perf.get('mean_tok_per_s')} tok/s",
        "工具调用": " → ".join(t["tool"] for t in run.tool_trace) or "（无）",
        "API 费用": "¥0（全程 127.0.0.1 本地推理）",
    }
    out = Path(args.out) if args.out else HERE.parent / f"JingXueQing_C4D_map.html"
    write_map(run.final["markers"], str(out), title=run.final["title"],
              summary=run.final["summary"], evidence=evidence)

    report = {
        "request": args.request, "profile": prof.label,
        "final": run.final, "tool_trace": run.tool_trace,
        "perf": run.perf, "wall_seconds": run.wall_seconds,
        "server": srv.as_dict(), "map_file": str(out),
    }
    p = _save("run_report.json", report)
    print(f"\n[✓] 地图已生成：{out}")
    print(f"[✓] 运行报告：{p}")
    print(f"\n{run.final['summary']}")
    return 0


# ------------------------------------------------------------ chat
def cmd_chat(args: argparse.Namespace) -> int:
    _hdr()
    prof = resolve_profile(args.profile)
    llm = LocalLLM(prof)
    state = T.MapState(STATE_PATH)
    agent = MapAgent(llm, state)
    if len(state) == 0:
        print("\n[提示] 当前地图为空，先执行 `python run_agent.py map \"...\"` 生成初始地图。")

    print("\n进入多轮对话模式。输入 quit 退出。示例：")
    print('  - 把图书馆删掉 / 给地图加一个开封 / 把所有评分提到 4.8 以上\n')
    while True:
        try:
            q = input("你> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            return 0
        if not q:
            continue
        if q.lower() in {"quit", "exit", "q"}:
            print("再见。")
            return 0
        try:
            r = agent.edit(q)
            print(f"Agent> {r['reply']}  (当前 {len(state)} 个标记, {r['perf']} tok/s)\n")
        except OllamaUnavailable as e:
            print(f"[✗] {e}")
            return 3
        except Exception as e:  # noqa: BLE001
            print(f"[✗] 处理失败：{e}\n")


# ------------------------------------------------------------ bench
BENCH_TASK = ("请规划一条从西亚斯学院出发的一日路线，包含至少 4 个地点，"
              "并说明每一段的距离。先调用工具获取真实坐标。")


def cmd_bench(args: argparse.Namespace) -> int:
    _hdr()
    keys = [k.strip() for k in args.profiles.split(",") if k.strip()]
    results = []
    for k in keys:
        prof = resolve_profile(k)
        print(f"\n[{prof.key}] {prof.label} …")
        llm = LocalLLM(prof)
        agent = MapAgent(llm, T.MapState(STATE_PATH))
        row: dict = {"key": k, "model": prof.ollama_tag, "quant": prof.quantization,
                     "num_ctx": prof.num_ctx}
        try:
            t0 = time.perf_counter()
            run = agent.run(BENCH_TASK)
            row.update({
                "ok": True,
                "wall_seconds": run.wall_seconds,
                "tool_calls": len(run.tool_trace),
                "tool_ok": sum(1 for t in run.tool_trace if t["ok"]),
                "markers": len(run.final["markers"]),
                "json_ok": True,
                "mean_tok_per_s": run.perf.get("mean_tok_per_s"),
                "llm_calls": run.perf.get("calls"),
            })
            print(f"      ✓ {row['markers']} markers · {row['tool_ok']}/{row['tool_calls']} 工具成功"
                  f" · {row['mean_tok_per_s']} tok/s · {row['wall_seconds']}s")
        except Exception as e:  # noqa: BLE001 - bench 要记录失败而不是中断
            row.update({"ok": False, "error": f"{type(e).__name__}: {e}"[:200]})
            print(f"      ✗ {row['error']}")
        results.append(row)
    p = _save("bench.json", {"task": BENCH_TASK, "results": results})
    print(f"\n对比报告已写入：{p}")
    return 0


# ------------------------------------------------------------ selftest
def cmd_selftest(args: argparse.Namespace) -> int:
    _hdr()
    print("\n[工具层自测 —— 不依赖模型]\n")
    checks = []

    def ck(label: str, cond: bool, detail: str = "") -> None:
        checks.append((label, cond, detail))
        print(f"  {'✓' if cond else '✗'} {label}  {detail}")

    r = T.call("geocode_local", {"name": "西亚斯学院图书馆"})
    ck("geocode_local 命中", r.get("matched") is True, f"conf={r.get('confidence')}")
    r2 = T.call("reverse_geocode", {"lat": 34.4170, "lng": 113.7535})
    ck("reverse_geocode 合理", "nearest" in r2, str(r2.get("nearest")))
    r3 = T.call("search_poi", {"keyword": "博物馆", "limit": 3})
    ck("search_poi 命中", r3["count"] >= 1, f"count={r3['count']}")
    r4 = T.call("route_plan", {"points": [[34.4166, 113.7530], [34.4270, 113.7620]],
                              "mode": "walking"})
    ck("route_plan 计算", r4["total_distance_km"] > 0,
       f"{r4['total_distance_km']}km / {r4['total_minutes']}min")
    r5 = T.call("score_poi", {"latitude": 34.4166, "longitude": 113.7530, "rating": 4.7})
    ck("score_poi 可解释", "explain" in r5, f"score={r5['score']}")
    # 距离正确性：1° 纬度 ≈ 111.19 km
    d = T.haversine((34.0, 113.0), (35.0, 113.0))
    ck("haversine 精度", abs(d - 111.19) < 1.0, f"实测 {d:.2f}km（理论 111.19）")
    # 错误处理
    try:
        T.call("route_plan", {"points": [[1, 1]]})
        ck("非法参数抛错", False)
    except T.ToolError:
        ck("非法参数抛错", True)

    n_ok = sum(1 for _, c, _ in checks if c)
    print(f"\n结果：{n_ok}/{len(checks)} 通过")
    _save("selftest.json", {"passed": n_ok, "total": len(checks),
                            "checks": [{"label": l, "pass": c, "detail": dt}
                                       for l, c, dt in checks]})
    return 0 if n_ok == len(checks) else 1


# ------------------------------------------------------------ code
def cmd_code(args: argparse.Namespace) -> int:
    _hdr()
    from sias_agent.advanced import CodeGenAgent, map_statistics

    prof = resolve_profile(args.profile)
    llm = LocalLLM(prof)
    print(f"\n[模型] {prof.label}\n[需求] {args.requirement}\n")
    r = CodeGenAgent(llm).generate_and_run(args.requirement)
    print(f"[模型自述] {r.get('explanation', '')[:200]}")
    print(f"[执行] ok={r['ok']}  {r.get('code_lines', '-')} 行  {r.get('latency_ms', '-')}ms"
          f"  自修 {r.get('attempts', 1)} 次")
    if r["ok"]:
        print(f"[stdout] {r['stdout'][:600]}")
    else:
        print(f"[错误] {r.get('error')}")

    # 对照组：不依赖模型、纯本地确定性计算，用来证明代码 Agent 的结果可校验
    if args.compare:
        state = T.MapState(STATE_PATH)
        if len(state):
            print(f"\n[对照组 · 纯本地确定性计算] {map_statistics(state.markers)}")
    _save("codegen.json", {"requirement": args.requirement, "result": r,
                           "perf": llm.perf_summary()})
    return 0 if r["ok"] else 1


# ------------------------------------------------------------ vision
def cmd_vision(args: argparse.Namespace) -> int:
    _hdr()
    from sias_agent.advanced import VisionAgent

    prof = resolve_profile(args.profile)
    llm = LocalLLM(prof)
    print(f"\n[模型] {prof.label}\n[图片] {args.image}\n")
    try:
        r = VisionAgent(llm).describe(args.image, args.question or "")
    except FileNotFoundError:
        print(f"[✗] 图片不存在：{args.image}")
        return 2
    print(f"[本地模型识别]")
    print(f"  是否校园照片 : {r.get('is_campus_photo')}")
    print(f"  场景(中)     : {r.get('scene_zh')}")
    print(f"  场景(英)     : {r.get('scene')}")
    print(f"  推断类别     : {r.get('guess_category')}")
    print(f"  标签         : {r.get('tags')}")
    print(f"  置信度       : {r.get('confidence')}")
    print(f"  推理速度     : {r.get('_stat', {}).get('tok_per_s')} tok/s")
    _save("vision.json", r)
    return 0


# ------------------------------------------------------------ ctxbench
# Level 4「性能调优」：固定模型，只变 context length，测 tok/s 与内存
CTX_LADDER = [1024, 2048, 4096, 8192]


def cmd_ctxbench(args: argparse.Namespace) -> int:
    """在不同 num_ctx 下跑同一个 Agent 任务，量化「性能调优」的真实收益。"""
    _hdr()
    base = resolve_profile(args.profile)
    llm0 = LocalLLM(base)
    rows = []
    print(f"\n固定模型：{base.ollama_tag}（{base.quantization}）")
    print(f"固定任务：{BENCH_TASK[:40]}...\n")
    print(f"{'num_ctx':>8}{'tok/s':>10}{'首字延迟ms':>13}{'标记':>6}{'工具OK':>9}{'总耗时s':>10}")
    print("─" * 60)
    for ctx in CTX_LADDER:
        llm = LocalLLM(ModelProfile(key=f"{base.key}-ctx{ctx}",
                                     ollama_tag=base.ollama_tag,
                                     quantization=base.quantization,
                                     num_ctx=ctx, temperature=base.temperature))
        agent = MapAgent(llm, T.MapState(STATE_PATH))
        row: dict = {"num_ctx": ctx, "model": base.ollama_tag}
        try:
            run = agent.run(BENCH_TASK)
            per = run.perf.get("per_call", [])
            first = per[0]["total_ms"] if per else 0
            row.update({
                "ok": True,
                "mean_tok_per_s": run.perf.get("mean_tok_per_s"),
                "first_call_ms": first,
                "markers": len(run.final["markers"]),
                "tool_ok": sum(1 for t in run.tool_trace if t["ok"]),
                "tool_calls": len(run.tool_trace),
                "wall_seconds": run.wall_seconds,
            })
            print(f"{ctx:>8}{row['mean_tok_per_s']:>10}{first:>13}"
                  f"{row['markers']:>6}{row['tool_ok']}/{row['tool_calls']:<7}{run.wall_seconds:>10}")
        except Exception as e:  # noqa: BLE001
            row.update({"ok": False, "error": f"{type(e).__name__}: {e}"[:160]})
            print(f"{ctx:>8}{'✗ ' + row['error'][:40]}")
        rows.append(row)

    ok = [r for r in rows if r.get("ok")]
    if len(ok) >= 2:
        fast = max(ok, key=lambda r: r["mean_tok_per_s"])
        slow = min(ok, key=lambda r: r["mean_tok_per_s"])
        gain = (fast["mean_tok_per_s"] / slow["mean_tok_per_s"] - 1) * 100
        print("─" * 60)
        print(f"结论：num_ctx {slow['num_ctx']} → {fast['num_ctx']} "
              f"吞吐提升 {gain:.1f}%（{slow['mean_tok_per_s']} → {fast['mean_tok_per_s']} tok/s）")
        print("      ctx 越大，KV cache 占内存越多；8GB 机器建议不超过 8192。")

    _save("ctxbench.json", {"model": base.ollama_tag, "quant": base.quantization,
                            "task": BENCH_TASK, "rows": rows})
    print(f"\n报告已写入：{REPORTS / 'ctxbench.json'}")
    return 0


# ------------------------------------------------------------ main
def main() -> int:
    ap = argparse.ArgumentParser(prog="c4d-agent", description="C4D 本地大模型 Agent 技能")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("doctor", help="检查本地环境与模型")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("map", help="Agent 生成交互式地图")
    p.add_argument("request", nargs="?",
                   default="给我生成一个 SIAS University（郑州西亚斯学院）周边的地图，包含校园与周边地标")
    p.add_argument("--profile", default="e2b-q4")
    p.add_argument("--out", default=None)
    p.set_defaults(func=cmd_map)

    p = sub.add_parser("chat", help="多轮对话编辑地图")
    p.add_argument("--profile", default="e2b-q4")
    p.set_defaults(func=cmd_chat)

    p = sub.add_parser("bench", help="多模型对比（Level 4）")
    p.add_argument("--profiles", default="e2b-q4,e2b-q8")
    p.set_defaults(func=cmd_bench)

    p = sub.add_parser("ctxbench", help="上下文长度调优基准（Level 4）")
    p.add_argument("--profile", default="e2b-q4")
    p.set_defaults(func=cmd_ctxbench)

    p = sub.add_parser("selftest", help="工具层自测（无需模型）")
    p.set_defaults(func=cmd_selftest)

    p = sub.add_parser("code", help="代码生成 Agent（Level 3）")
    p.add_argument("requirement", nargs="?",
                   default="读取标准库 sys，统计 sys.version 的各个数字之和并以 JSON 输出")
    p.add_argument("--profile", default="e2b-q4")
    p.add_argument("--compare", action="store_true", help="附带纯本地确定性对照组")
    p.set_defaults(func=cmd_code)

    p = sub.add_parser("vision", help="视觉理解 Agent（Level 3）")
    p.add_argument("image")
    p.add_argument("--question", default="")
    p.add_argument("--profile", default="e2b-q4")
    p.set_defaults(func=cmd_vision)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
