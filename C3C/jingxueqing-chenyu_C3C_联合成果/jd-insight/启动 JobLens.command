#!/bin/bash
# JobLens · 岗位镜 —— 双击启动
# 做的事情：找 Python → 自检 → 重算两份示例报告 → 用浏览器打开
# 不装任何第三方库，不联网。

cd "$(dirname "$0")" || { echo "无法进入程序目录"; exit 1; }

echo "================================================"
echo "  JobLens · 岗位镜"
echo "  岗位画像与匹配度分析"
echo "================================================"
echo

# ---- 1. 找一个可用的 Python 3.9+ ----
PY=""
for c in "$(command -v python3)" "/opt/homebrew/bin/python3" \
         "/usr/local/bin/python3" "/usr/bin/python3" \
         "$HOME/.workbuddy/binaries/python/versions/3.13.12/bin/python3"; do
  [ -n "$c" ] && [ -x "$c" ] || continue
  if "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done

if [ -z "$PY" ]; then
  echo "✗ 没找到 Python 3.9 或更高版本。"
  echo "  安装方式：https://www.python.org/downloads/  或  brew install python3"
  echo
  read -n 1 -s -r -p "按任意键关闭…"
  exit 1
fi

echo "Python：$PY"
"$PY" -c 'import sys; print("版本：%d.%d.%d" % sys.version_info[:3])'
echo

# ---- 2. 自检 ----
echo "[1/3] 自检（标签体系 / 关键词索引 / 样例数据）"
"$PY" -m jd_insight.cli selfcheck || { echo; echo "✗ 自检失败，请把上面的报错发给我"; read -n 1 -s -r -p "按任意键关闭…"; exit 1; }
echo

# ---- 3. 重算两份示例报告 ----
echo "[2/3] 重算示例报告"
"$PY" -m jd_insight.cli match \
  --jd data/jd_J01.txt --resume data/resume_demo.txt \
  -o out/report_J01.html --json out/result_J01.json \
  --jobs data/jd_samples.csv \
  --jd-title "用户增长分析师" --resume-name "景雪晴"

"$PY" -m jd_insight.cli match \
  --jd data/jd_J07.txt --resume data/resume_demo.txt \
  -o out/report_J07.html --json out/result_J07.json \
  --jobs data/jd_samples.csv \
  --jd-title "产品经理（B端）" --resume-name "景雪晴"
echo

# ---- 4. 打开报告 ----
echo "[3/3] 打开报告"
open "out/report_J01.html"

cat <<'TIP'

------------------------------------------------
接下来你可以：
  · 换成自己的简历：改 data/resume_demo.txt
  · 换成目标岗位：  data/jd_J01.txt（或 --jd 指向任意 txt）
  · 看 24 条岗位的横向排名：
      python3 -m jd_insight.cli rank --jobs data/jd_samples.csv \
        --resume data/resume_demo.txt --top 10
  · 跑全部测试：
      python3 -m unittest discover -s tests -t .
------------------------------------------------
提示：这些数字是"自查参考"，不是录用标准。
分数低不等于你不行，只说明这份 JD 里有些词你没写进去。
TIP

echo
read -n 1 -s -r -p "按任意键关闭此窗口…"
