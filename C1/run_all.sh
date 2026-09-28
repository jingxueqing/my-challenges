#!/usr/bin/env bash
# run_all.sh — 课程资料获取与翻译流水线（课程无关，换源可复跑）
#
# 用法:
#   1. 把新课的离线包解压到 materials/<课程名>_offline/（含 pages/ 与 pdfs/，可选 page_map.json）
#   2. 修改下方 COURSE 变量与 config（或用环境变量覆盖）
#   3. bash run_all.sh extract        # 抓取/提取正文语料
#      bash run_all.sh translate      # 术语感知分段翻译（engine=skeleton 生成待译模板；engine=api 调 LLM）
#      bash run_all.sh check          # 覆盖度 + 术语一致性质检
#      bash run_all.sh all            # 依序执行全部
set -euo pipefail

COURSE="${COURSE:-CS146S_offline}"                 # 离线包目录名
SRC="${SRC:-materials/$COURSE}"                    # 离线包路径
CORPUS_EN="${CORPUS_EN:-corpus/en}"                # 英文语料输出
CORPUS_PDF="${CORPUS_PDF:-corpus/en-pdfs}"         # PDF 语料输出
DIR_ZH="${DIR_ZH:-course-zh}"                      # 中文译文输出
GLOSSARY="${GLOSSARY:-pipeline/glossary.csv}"      # 术语表（换课程时替换）
ENGINE="${ENGINE:-skeleton}"                       # api = 调 LLM；skeleton = 生成人工翻译模板
PY="${PY:-python3}"

cd "$(dirname "$0")"

extract() {
  echo "==> [1/3] 提取 HTML 正文语料"
  $PY pipeline/extract_text.py --src "$SRC" --out "$CORPUS_EN" \
      ${MAP:+"--map ${MAP}"} || $PY pipeline/extract_text.py --src "$SRC" --out "$CORPUS_EN"
  if [ -d "$SRC/pdfs" ]; then
    echo "==> [1/3] 提取 PDF 语料"
    $PY pipeline/extract_pdf.py --src "$SRC/pdfs" --out "$CORPUS_PDF"
  fi
}

translate() {
  echo "==> [2/3] 翻译（engine=$ENGINE）"
  $PY pipeline/translate.py --in "$CORPUS_EN" --out "$DIR_ZH" --glossary "$GLOSSARY" --engine "$ENGINE"
}

check() {
  echo "==> [3/3] 质检与覆盖度报告"
  $PY pipeline/check_quality.py --src "$CORPUS_EN" --dst "$DIR_ZH" --glossary "$GLOSSARY" \
      --out reports/quality_report.json
}

case "${1:-all}" in
  extract)   extract ;;
  translate) translate ;;
  check)     check ;;
  all)       extract && translate && check ;;
  *) echo "用法: bash run_all.sh [extract|translate|check|all]"; exit 1 ;;
esac
