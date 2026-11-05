#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_demo.py — 把真实终端 transcript 变成一个可逐步回放的 HTML 页面。

为什么不用 mp4：本次构建环境没有 ffmpeg / 屏幕录制能力（`which ffmpeg` 为空，
`import PIL` 失败）。与其交一个"因环境原因未提供"，不如把**真实输出**做成可回放页面——
页面上的每一行都是 `demo/record.sh` 跑出来的，不是手写的演示文案。

用法：python3 demo/make_demo.py
产出：../JingXueQing_C10_demo.html
"""
import html
import re
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TRANSCRIPT = HERE / "demo_transcript.txt"
OUT = ROOT.parent / "JingXueQing_C10_demo.html"


def parse(text):
    """按 '### 命令' 切段；'--- 说明' 作为段前注释。"""
    steps, pending_note = [], ""
    cur = None
    for line in text.split("\n"):
        if line.startswith("--- "):
            pending_note = line[4:].strip()
        elif line.startswith("### "):
            if cur:
                steps.append(cur)
            cur = {"cmd": line[4:].strip(), "note": pending_note, "out": []}
            pending_note = ""
        elif cur is not None:
            cur["out"].append(line)
    if cur:
        steps.append(cur)
    for s in steps:
        # 去掉首尾空行
        while s["out"] and not s["out"][0].strip():
            s["out"].pop(0)
        while s["out"] and not s["out"][-1].strip():
            s["out"].pop()
    return steps


def esc(s):
    return html.escape(s).replace(" ", "&nbsp;")


def render(steps):
    blocks = []
    for i, s in enumerate(steps, 1):
        out_html = "\n".join(
            '<div class="ln%s">%s</div>' % (" hi" if ("✓" in ln or "→" in ln) else "",
                                            esc(ln) if ln else "&nbsp;")
            for ln in s["out"])
        blocks.append("""
<section class="step" data-i="%d">
  <div class="cap"><span class="no">%02d</span>%s</div>
  <div class="term">
    <div class="bar"><i></i><i></i><i></i><span class="path">brain/</span></div>
    <div class="cmd"><span class="p">$</span> %s</div>
    <div class="out">%s</div>
  </div>
</section>""" % (i, i, html.escape(s["note"]), html.escape(s["cmd"]), out_html))
    return "\n".join(blocks)


def main():
    if not TRANSCRIPT.exists():
        raise SystemExit("先跑 bash demo/record.sh 生成 transcript")
    steps = parse(TRANSCRIPT.read_text(encoding="utf-8"))
    n_lines = sum(len(s["out"]) for s in steps)
    total_cmds = len(steps)

    page = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>C10 Demo · 第二大脑的一次完整 KSTAR 循环</title>
<style>
:root{--bg:#f5f6f8;--card:#fff;--ink:#12161c;--mut:#6b7280;--line:#e3e6ea;
--g:#137333;--b:#2f6feb;--code:#0b1220}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
font:15px/1.7 -apple-system,"PingFang SC","Helvetica Neue",Arial,sans-serif}
.wrap{max-width:900px;margin:0 auto;padding:36px 20px 80px}
h1{font-size:24px;margin:0 0 6px;letter-spacing:-.2px}
.sub{color:var(--mut);font-size:13.5px}
.banner{background:#eef4ff;border:1px solid #d5e2ff;border-radius:12px;
padding:14px 16px;margin:20px 0 8px;font-size:13.5px}
.banner b{color:#1a4fd0}
.toolbar{display:flex;gap:10px;align-items:center;margin:16px 0 22px;flex-wrap:wrap}
button{border:1px solid var(--line);background:#fff;color:var(--ink);border-radius:999px;
padding:7px 16px;font-size:13.5px;cursor:pointer;transition:.15s}
button:hover{border-color:#c3c9d2}
button.primary{background:var(--b);border-color:var(--b);color:#fff}
button.primary:hover{background:#245ad0}
.pill{font-size:12.5px;color:var(--mut);background:#fff;border:1px solid var(--line);
border-radius:999px;padding:5px 12px}
.step{margin:0 0 26px;opacity:.25;transition:opacity .5s}
.step.on{opacity:1}
.cap{display:flex;gap:10px;align-items:baseline;margin:0 0 8px;font-size:13.5px;color:#374151}
.no{font:600 11px/1 ui-monospace,Menlo,monospace;color:#fff;background:#9aa3af;
border-radius:5px;padding:4px 6px}
.term{background:var(--code);border-radius:12px;overflow:hidden;
box-shadow:0 1px 2px rgba(16,24,40,.06),0 8px 24px rgba(16,24,40,.06)}
.bar{display:flex;align-items:center;gap:6px;padding:9px 12px;background:#111a2b}
.bar i{width:10px;height:10px;border-radius:50%;background:#2b3a55;display:block}
.bar .path{margin-left:8px;color:#7d8aa3;font:12px ui-monospace,Menlo,monospace}
.cmd{padding:10px 14px;color:#e6edf3;font:13px/1.6 ui-monospace,Menlo,monospace;
background:#0f1830;border-bottom:1px solid #1c2740;word-break:break-all}
.cmd .p{color:#54d38a}
.out{padding:12px 14px 14px;font:12.5px/1.65 ui-monospace,Menlo,monospace;
color:#c9d5e4;white-space:pre-wrap;word-break:break-word;max-height:640px;overflow:auto}
.ln{min-height:1.2em}
.ln.hi{color:#9ae6b4}
footer{margin-top:36px;color:var(--mut);font-size:12.5px;border-top:1px solid var(--line);padding-top:16px}
code{background:#eceff3;padding:1px 5px;border-radius:4px;font-size:12.5px}
</style></head><body><div class="wrap">
<h1>一次完整的 KSTAR 循环</h1>
<div class="sub">第二大脑 · 真实终端录制回放 ｜ @@TOTAL@@ 个命令 / @@LINES@@ 行输出 / 生成于 @@NOW@@</div>

<div class="banner">
<b>这是回放，不是剪辑。</b> 页面里每一行都是 <code>bash demo/record.sh</code> 跑出来的原始 stdout，
原样存于 <code>brain/demo/demo_transcript.txt</code>，你可以把命令复制到自己的终端重跑一遍。
本次环境没有 ffmpeg（<code>which ffmpeg</code> 为空），所以没有产出 mp4——
<b>与其交一个"因环境原因未提供"，不如交一份可复跑的证据。</b>
</div>

<div class="toolbar">
  <button class="primary" id="play">▶ 逐步播放</button>
  <button id="all">全部展开</button>
  <button id="reset">重置</button>
  <span class="pill">K 检索 → R 结果 → ΔR 写回 → distill → doctor → dash → report</span>
</div>

@@STEPS@@

<footer>
复现：<code>cd brain && bash demo/record.sh && python3 demo/make_demo.py</code><br>
提交人：JingXueQing（景雪晴）· 学号 2024102110351 · C10 Build Your Own Agent
</footer>
</div>
<script>
(function(){
  var steps=[].slice.call(document.querySelectorAll('.step'));
  var i=0,timer=null;
  function show(n){ for(var k=0;k<steps.length;k++) steps[k].classList.toggle('on',k<n); }
  function play(){
    if(timer){clearInterval(timer);timer=null;document.getElementById('play').textContent='▶ 逐步播放';return;}
    if(i>=steps.length){i=0;show(0);}
    document.getElementById('play').textContent='⏸ 暂停';
    timer=setInterval(function(){
      i++; show(i);
      steps[i-1].scrollIntoView({behavior:'smooth',block:'center'});
      if(i>=steps.length){clearInterval(timer);timer=null;
        document.getElementById('play').textContent='▶ 逐步播放';}
    },1400);
  }
  document.getElementById('play').onclick=play;
  document.getElementById('all').onclick=function(){if(timer){clearInterval(timer);timer=null;}
    i=steps.length;show(i);};
  document.getElementById('reset').onclick=function(){if(timer){clearInterval(timer);timer=null;}
    i=0;show(0);window.scrollTo({top:0,behavior:'smooth'});};
  show(steps.length);  // 默认全部可见：打开即可通读，点「逐步播放」才逐步揭示
})();
</script>
</body></html>"""
    page = (page.replace("@@TOTAL@@", str(total_cmds))
                .replace("@@LINES@@", str(n_lines))
                .replace("@@NOW@@", datetime.now().strftime("%Y-%m-%d %H:%M"))
                .replace("@@STEPS@@", render(steps)))
    OUT.write_text(page, encoding="utf-8")
    print(