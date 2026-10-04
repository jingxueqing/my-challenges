#!/bin/bash
# ============================================================
# ai-log-forge 一键跑通（把下面 PY 换成你自己的 python3 即可）
# 从「原始 AI 协作记录」到「体检报告」，三条命令，全程离线、零依赖。
# ============================================================
set -e
PY=${PY:-python3}
SKILL="$(cd "$(dirname "$0")/../ai-log-forge" && pwd)"

echo "============================================================"
echo " STEP 1  抽取证据（原始记录 -> trace.json）"
echo "============================================================"
$PY "$SKILL/scripts/extract_trace.py" \
    --input "$(dirname "$0")/demo_session.jsonl" \
    --out   "$(dirname "$0")/trace.json" --markdown

echo
echo "============================================================"
echo " STEP 2  锻造文档（trace.json -> AI日志 + AAR）"
echo "============================================================"
$PY "$SKILL/scripts/forge.py" \
    --trace "$(dirname "$0")/trace.json" \
    --name Demo --challenge C4 \
    --title "销售数据汇总脚本开发" \
    --out-dir "$(dirname "$0")"

echo
echo "============================================================"
echo " STEP 3  交卷前体检（先看分数，再补占位符）"
echo "============================================================"
$PY "$SKILL/scripts/health_check.py" \
    --files "$(dirname "$0")/Demo_C4_AI日志.md" "$(dirname "$0")/Demo_C4_AAR.md" \
    --trace "$(dirname "$0")/trace.json" \
    --profile "$SKILL/references/rubric_ai_log.yaml" \
    --out "$(dirname "$0")/体检报告_未填写.md" || true

echo
echo "============================================================"
echo " STEP 4  补写占位符后复检（分数应明显上涨，退出码变 0）"
echo "============================================================"
$PY "$SKILL/scripts/health_check.py" \
    --files "$(dirname "$0")/Demo_C4_AI日志_已补写.md" "$(dirname "$0")/Demo_C4_AAR_已补写.md" \
    --trace "$(dirname "$0")/trace.json" \
    --profile "$SKILL/references/rubric_ai_log.yaml" \
    --out "$(dirname "$0")/体检报告_已补写.md"
echo "退出码=$? （0 = 无红旗、无未填占位符，可以交了）"
