#!/usr/bin/env bash
# record.sh — 录一次真实的 KSTAR 循环，产出 transcript（不是模拟输出）
#
# 用法：bash demo/record.sh
# 产物：demo/demo_transcript.txt
#
# 说明：每一段都以 "### 命令" 开头，方便 make_demo.py 切分成可回放的步骤。
set -u
cd "$(dirname "$0")/.." || exit 1
PY="${PY:-python3}"
OUT="demo/demo_transcript.txt"
: > "$OUT"

run() {
  # 打印命令本身，再执行，输出原样进 transcript
  # 展示时把解释器绝对路径换成 python3，transcript 更好读
  printf '\n### %s\n' "${*//$PY/python3}" >> "$OUT"
  if [ "$1" = "$PY" ] && [ "$2" = "scripts/kstar.py" ]; then
    "$@" >> "$OUT" 2>&1
  else
    eval "$@" >> "$OUT" 2>&1
  fi
}

note() { printf '\n--- %s\n' "$1" >> "$OUT"; }

note "第 0 步：系统自检（内核 5 项断言，先过再铺数据）"
run "$PY" scripts/kstar.py selftest

note "第 1 步：K —— 开工前检索，不许凭印象回忆"
run "$PY" scripts/kstar.py recall 移动端 验收 量错 --k 3

note "第 2 步：K —— 检索这一轮实际要用的能力"
run "$PY" scripts/kstar.py recall 交付 打包 复现 --layer skill --k 3

note "第 3 步：R —— 关闭这一轮循环，自动算 ΔR（R̂ 是事前写的 0.88）"
run "$PY" scripts/kstar.py loop close RUN-20261105-2122 --r 0.86 \
  --actual "8 项全达成（五层可跑/四层记忆/6 Skill 有记录/1 个迭代到 v4/distill 提名-裁决闭环/系统级 AAR/拿来说明 6 系统/数据可积累）；2 项打折：demo 无 mp4（沙箱无 ffmpeg，改真实 transcript + HTML 回放，按 0.5 计）、\"提交前已用 2 周\"不成立（系统今天建成，按 0.1 计）。加权 R=(8+0.5+0.1)/10=0.86。" \
  --lesson "系统的第一批数据必须来自真实交付物回填，否则它会有一周的空白期；但回填之后，使用记录必须交给命令写，人不要再碰。"

note "第 4 步：写回 —— 循环自动落了一条 L2 草稿，人工确认后进正式库"
run "$PY" scripts/kstar.py ep list

note "第 5 步：自进化 —— 从经验里提名候选 Skill（只提名，不上线）"
run "$PY" scripts/kstar.py distill --min 3

note "第 6 步：体检 —— 结构 / ΔR / 空壳 Skill / 积压笔记"
run "$PY" scripts/kstar.py doctor

note "第 7 步：看板 —— 由磁盘数据重算，不是截图"
run "$PY" scripts/kstar.py dash

note "第 8 步：使用记录 —— 从 logs/usage.jsonl 流水生成"
run "$PY" scripts/kstar.py report --since 2026-09-01

note "第 9 步：Skill 库快照（提交用，不手改）"
run "$PY" scripts/kstar.py export-skills --out ../JingXueQing_C10_skills

printf '\n'
echo "✓ transcript 已写入 ${OUT}（$(wc -l < "${OUT}") 行）"
