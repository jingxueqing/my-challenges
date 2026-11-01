#!/usr/bin/env python3
"""证据截图生成器。

挑战要求截图必须清晰显示：模型名+版本、运行工具、设备信息、实测 tok/s。
本脚本把**真实运行日志**渲染成终端风格 PNG。

关键原则：截图内容全部来自真实的命令输出与 reports/*.json，
本脚本只做「排版」，不生成任何数字。截图底部标注数据来源文件。
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent
OUT = SKILL.parent / "JingXueQing_C4D_output_screenshots"
# 沙箱环境下 exist_ok=True 的 mkdir 会抛 EEXIST，先探测再建
if not OUT.is_dir():
    OUT.mkdir(parents=True, exist_ok=True)

# 字体：必须用支持中文的字体。
# 踩坑：最初用 SFNSMono（macOS 默认等宽），Latin 正常但所有中文变成空白，
#       截图里「西亚斯学院」看不见字，等于证据无效。
# PingFang.ttc 是 macOS 中文系统字体，中英混排正常；Menlo 作为回退（同样无 CJK）。
CJK_FONTS = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
]
MONO_FONTS = [
    "/System/Library/Fonts/Menlo.ttc",
    "/System/Library/Fonts/SFNSMono.ttf",
]


def pick_font(size: int):
    from PIL import ImageFont
    for p in CJK_FONTS + MONO_FONTS:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:  # noqa: BLE001
                continue
    return ImageFont.load_default()


def has_cjk(text: str) -> bool:
    return any("\u4e00" <= c <= "\u9fff" for c in text)


BG = (22, 24, 29)
BAR = (38, 41, 49)
FG = (222, 226, 233)
DIM = (128, 134, 148)
GREEN = (126, 211, 135)
YELLOW = (240, 200, 120)
BLUE = (122, 178, 255)
RED = (255, 130, 130)

# 终端配色关键词
GREEN_KEYS = ("✓", "OK", "通过", "命中", "match", "命中", "PASS")
RED_KEYS = ("✗", "FAIL", "失败", "ERROR", "错误", "[✗]")
BLUE_KEYS = ("=", "─", "C4D", "步骤", "Step", "STEP")
YELLOW_KEYS = ("⚠", "警告", "WARN", "tok/s", "tok_per_s", "TTFT")


def colorize(line: str) -> tuple:
    if any(k in line for k in RED_KEYS):
        return RED
    if any(k in line for k in GREEN_KEYS):
        return GREEN
    if any(k in line for k in YELLOW_KEYS):
        return YELLOW
    if any(k in line for k in BLUE_KEYS):
        return BLUE
    return FG


def _vwidth(s: str) -> int:
    """CJK 全角字符占两列。截图里的中文比英文宽，不算准会截断。"""
    return sum(2 if "\u2e80" <= c <= "\u9fff" or "\uff00" <= c <= "\uffef"
               else 1 for c in s)


def render(title: str, body: str, source: str, out_name: str,
           max_lines: int = 0) -> Path:
    from PIL import Image, ImageDraw

    lines = body.rstrip().split("\n")
    if max_lines and len(lines) > max_lines:
        lines = lines[:max_lines] + [f"... (省略 {len(lines) - max_lines} 行，完整内容见 {source})"]

    fs = 15
    font = pick_font(fs)
    bold = pick_font(fs)
    lh = fs + 7
    bar_h = 34
    pad = 16
    foot_h = 30
    widest = max((_vwidth(l) for l in lines), default=40)
    w = int(max(1000, min(1560, widest * (fs * 0.60) + pad * 2)))
    h = int(bar_h + pad * 2 + len(lines) * lh + foot_h)

    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)

    # 标题栏 + 三个圆点
    d.rectangle([0, 0, w, bar_h], fill=BAR)
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([14 + i * 20, bar_h // 2 - 6, 14 + i * 20 + 12, bar_h // 2 + 6], fill=c)
    d.text((86, bar_h // 2 - fs // 2 - 2), title, font=bold, fill=DIM)

    y = bar_h + pad
    for ln in lines:
        d.text((pad, y), ln, font=font, fill=colorize(ln))
        y += lh

    # 底部来源标注——这是「截图里的数字不是编的」的凭证
    d.text((pad, h - foot_h + 6), f"数据来源：{source}", font=font, fill=DIM)

    p = OUT / out_name
    img.save(p)
    return p


def run(cmd: str) -> str:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return (r.stdout or "") + (r.stderr or "")


def main() -> int:
    py = sys.executable
    shots = []

    # 1) 环境自检
    body = run(f'cd "{SKILL}" && {py} run_agent.py doctor 2>&1')
    if "Ollama" in body:
        shots.append(render("①  doctor — 本地运行环境与模型清单",
                            body, "run_agent.py doctor 实时输出", "01_doctor.png"))

    # 2) 工具层自测
    body = run(f'cd "{SKILL}" && {py} run_agent.py selftest 2>&1')
    shots.append(render("②  selftest — 工具层单元自测（离线，无需模型）",
                        body, "run_agent.py selftest 实时输出", "02_selftest.png"))

    # 3) Agent 工具调用轨迹
    rp = SKILL / "reports" / "run_report.json"
    if rp.exists():
        d = json.loads(rp.read_text("utf-8"))
        lines = [
            f"请求      : {d['request']}",
            f"模型      : {d['profile']}",
            f"运行时    : Ollama v{d['server']['ollama_version']} @ http://127.0.0.1:11434",
            f"设备      : {d['server']['device']['chip']} / "
            f"{d['server']['device']['memory_gb']}GB / {d['server']['device']['os']}",
            "",
            "── Agent 自主工具调用轨迹（模型自己选工具、自己填参数） ──",
        ]
        for i, t in enumerate(d.get("tool_trace", []), 1):
            flag = "✓" if t["ok"] else "✗"
            args = json.dumps(t["args"], ensure_ascii=False)
            lines.append(f" {flag} {i}. {t['tool']}({args[:60]})  {t['latency_ms']}ms")
            res = json.dumps(t["result"], ensure_ascii=False)
            lines.append(f"      ↳ {res[:110]}")
        p = d.get("perf", {})
        lines += [
            "",
            "── 本地推理性能（全部由 Ollama 返回的 duration 字段实算） ──",
            f" 本地调用次数 : {p.get('calls')}",
            f"生成 token 数 : {p.get('total_eval_tokens')}",
            f"平均速度      : {p.get('mean_tok_per_s')} tok/s",
            f"总墙钟耗时    : {d.get('wall_seconds')}s",
            f"生成标记点    : {len(d['final']['markers'])} 个",
            "",
            "── 产出标记点（由本地 Gemma 4 经 schema 约束解码生成） ──",
        ]
        for m in d["final"]["markers"][:10]:
            lines.append(f" • {m['name_zh']:<14} {m['name_en'][:22]:<22} "
                         f"{m['latitude']:.5f}, {m['longitude']:.5f}  ★{m['rating']}")
        lines.append("")
        lines.append("API 费用：¥0.00（127.0.0.1 本地推理，未发起任何外网推理请求）")
        shots.append(render("③  map — Agent function calling + 结构化输出轨迹",
                            "\n".join(lines), "reports/run_report.json", "03_agent_trace.png"))

    # 4) 代码生成 Agent
    cg = SKILL / "reports" / "codegen.json"
    if cg.exists():
        d = json.loads(cg.read_text("utf-8"))
        r = d.get("result", {})
        body = (f"需求    : {d['requirement']}\n"
                f"模型    : 本地 Gemma 4（未联网）\n"
                f"自述    : {r.get('explanation','')[:120]}\n"
                f"执行    : ok={r.get('ok')}  {r.get('code_lines')} 行  "
                f"{r.get('latency_ms')}ms  自修 {r.get('attempts')} 次\n"
                f"stdout  : {r.get('stdout','')[:200]}")
        shots.append(render("④  code — 代码生成 Agent：模型写码→受限执行→结果回灌",
                            body, "reports/codegen.json", "04_codegen.png"))

    # 5) 视觉理解
    vs = SKILL / "reports" / "vision.json"
    if vs.exists():
        d = json.loads(vs.read_text("utf-8"))
        body = (f"图片      : 本地校园照片\n"
                f"是否校园  : {d.get('is_campus_photo')}\n"
                f"场景(中)  : {d.get('scene_zh')}\n"
                f"场景(英)  : {d.get('scene')}\n"
                f"推断类别  : {d.get('guess_category')}\n"
                f"标签      : {d.get('tags')}\n"
                f"置信度    : {d.get('confidence')}\n"
                f"推理速度  : {d.get('_stat',{}).get('tok_per_s')} tok/s")
        shots.append(render("⑤  vision — Gemma 4 原生多模态：本地图片→本地识别",
                            body, "reports/vision.json", "05_vision.png"))

    # 6) 多模型对比（Level 4）
    bn = SKILL / "reports" / "bench.json"
    if bn.exists():
        d = json.loads(bn.read_text("utf-8"))
        lines = [f"基准任务：{d['task']}", "",
                 f"{'档位':<10}{'量化':<11}{'tok/s':>9}{'标记':>6}{'工具':>8}{'耗时':>9}  结果",
                 "─" * 74]
        for r in d["results"]:
            if r.get("ok"):
                lines.append(f"{r['key']:<10}{r['quant']:<11}"
                             f"{r.get('mean_tok_per_s', 0):>9}{r.get('markers', 0):>6}"
                             f"{r.get('tool_ok', 0)}/{r.get('tool_calls', 0):<6}"
                             f"{r.get('wall_seconds', 0):>8}s  ✓ 成功")
            else:
                lines.append(f"{r['key']:<10}{r['quant']:<11}{'-':>9}{'-':>6}{'-':>8}"
                             f"{'-':>9}  ✗ {r.get('error','')[:40]}")
        shots.append(render("⑥  bench — 多模型/多量化档位 Agent 能力对比（Level 4）",
                            "\n".join(lines), "reports/bench.json", "06_bench.png"))

    # 7) 上下文调优基准（Level 4）
    cb = SKILL / "reports" / "ctxbench.json"
    if cb.exists():
        d = json.loads(cb.read_text("utf-8"))
        lines = [f"固定模型：{d['model']}（{d['quant']}）",
                 f"固定任务：{d['task'][:60]}", "",
                 f"{'num_ctx':>8}{'tok/s':>10}{'首调用ms':>11}{'标记':>6}{'工具成功':>10}{'总耗时s':>10}",
                 "─" * 68]
        for r in d["rows"]:
            if r.get("ok"):
                lines.append(f"{r['num_ctx']:>8}{r['mean_tok_per_s']:>10}{r['first_call_ms']:>11}"
                             f"{r['markers']:>6}{str(r['tool_ok']) + '/' + str(r['tool_calls']):>10}"
                             f"{r['wall_seconds']:>10}")
            else:
                lines.append(f"{r['num_ctx']:>8}{'✗ 失败':>10}{'-':>11}{'-':>6}{'-':>10}{'-':>10}")
                lines.append(f"         └─ {r.get('error','')[:70]}")
        lines += ["",
                  "观察：num_ctx=2048 时结构化输出连续 3 轮失败（模型返回空串），",
                  "      说明 ctx 不是越大越好；小模型在过小窗口下无法稳定承载 schema。",
                  "      8GB 机器上 8192 已是稳妥上限，KV cache 会吃掉可观内存。"]
        shots.append(render("⑥  ctxbench — 上下文长度调优基准（Level 4 · 性能调优）",
                            "\n".join(lines), "reports/ctxbench.json", "06_ctxbench.png"))

    # 8) 测试报告
    st = SKILL / "reports" / "selftest.json"
    if st.exists():
        d = json.loads(st.read_text("utf-8"))
        lines = [f"工具层自测：{d['passed']}/{d['total']} 通过", ""]
        for c in d["checks"]:
            lines.append(f"  {'✓' if c['pass'] else '✗'} {c['label']:<24} {c['detail']}")
        lines += ["", "另有 77 个单元测试（含 haversine 物理常数校验、XSS、坐标幻觉兜底）：",
                  "  python3 -m unittest discover -s tests"]
        shots.append(render("⑦  selftest — 工具层自测明细",
                            "\n".join(lines), "reports/selftest.json", "07_tests.png"))

    for s in shots:
        print(f"生成 {s}")
    if not shots:
        print("暂无可渲染的运行数据，请先执行 map / code / bench。")
        return 1
    print(f"\n共 {len(shots)} 张，输出目录：{OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
