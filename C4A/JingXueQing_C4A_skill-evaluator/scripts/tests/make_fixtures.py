#!/usr/bin/env python3
"""生成带金标准标签的测试集（Level 1-3 回归测试 + 准确率测量）。

为什么要造测试集：
    C4A 的评分表里"评审准确性"占 30%，"误判率低"是明写的信号。
    一个从没被测量过的评审器，说自己准确率 95% 是没有意义的。
    所以这里造 8 份**故意各不相同**的提交（含3 份对抗样本），
    人工标注金标准，然后跑评审器算准确率。

三份对抗样本（专门用来打规则的漏洞）：
    TrapHardcode  内容写得很漂亮，但代码里硬编码了 /Users/xxx 绝对路径 + 明文key
                  → 期望：可复用 ❌
    TrapTemplate  全文都是"示例/模板/待填写"，是典型未完成品
                  → 期望：可执行 ❌、可验证 ❌
    TrapMention   文档里大段讨论"不要硬编码路径 / 不要留 TODO"（元提及）
                  → 期望：不应被判❌（这是最容易误判的一类）

运行：
    python3 tests/make_fixtures.py      # 生成到 tests/fixtures/
    python3 tests/run_selftest.py                # 跑测试并输出准确率
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"


def w(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ==========================================================================
# 1) Excellent —— 五件套齐全，四条件全满足（金标准：全 ✅）
# ==========================================================================
def make_excellent(d: Path) -> None:
    w(d / "LiMing_C4_skill说明.md", """---
name: meeting-notes
description: 把会议录音转写文本整理成结构化纪要
---

# meeting-notes 会议纪要生成技能

## 概述
本技能用于把会议转写文本（带时间戳的纯文本）整理成结构化会议纪要。

## 输入
- 一个 `.txt` 文件路径，内容为会议转写文本（每行一句，含发言人前缀）

## 输出
- 一个 `.md` 纪要文件，包含「议题 / 结论 / 待办（含负责人与截止日期）」三节

## 安装
```bash
pip install -r requirements.txt
```

## 环境要求
- Python 3.10+
- 依赖：见 `requirements.txt`（jieba、python-dateutil）

## 使用步骤
1. 准备转写 `.txt` 文件
2. 执行：
   ```bash
   python3 scripts/notes.py transcript.txt -o summary.md
   ```
3. 打开 `summary.md` 检查三节是否齐全

## 预期结果
运行后 `summary.md` 至少包含 `## 议题`、`## 结论`、`## 待办` 三个二级标题；
待办条目形如 `- [ ] 负责人：@张三 截止：2026-10-20`。

![运行结果截图](../screenshots/run.png)

## 适用范围
适用于 30 分钟以内的中文会议。不适用于中英混合且专业术语密集的会议。
""")
    w(d / "LiMing_C4_meeting-notes.skill", """---
name: meeting-notes
description: 把会议转写文本整理成结构化纪要
---

# meeting-notes

## Workflow
1. 读取输入文件
2. 解析发言人
3. 抽取待办

## 运行
```bash
python3 scripts/notes.py <input.txt> -o <output.md>
```
""")
    w(d / "scripts" / "notes.py", '''#!/usr/bin/env python3
"""会议纪要生成器。"""
import argparse
import re
from pathlib import Path

TODO_RE = re.compile(r"(需要|待办|action\\s*item)", re.IGNORECASE)


def split_speaker(line: str):
    if "：" in line:
        who, _, said = line.partition("：")
        return who.strip(), said.strip()
    return None, line.strip()


def build(transcript: str) -> str:
    topics, todos = [], []
    for line in transcript.splitlines():
        who, said = split_speaker(line)
        if not said:
            continue
        if TODO_RE.search(said):
            todos.append(f"- [ ] {said}")
        else:
            topics.append(f"- {who or '未知'}：{said}")
    out = ["## 议题"] + (topics or ["- （无）"]) + ["", "## 结论", "- 见议题", "", "## 待办"]
    out += todos or ["- （无）"]
    return "\\n".join(out) + "\\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="会议纪要生成器")
    ap.add_argument("input", help="转写文本 .txt 路径")
    ap.add_argument("-o", "--output", default="summary.md")
    a = ap.parse_args()
    text = Path(a.input).read_text(encoding="utf-8")
    Path(a.output).write_text(build(text), encoding="utf-8")
    print(f"已生成 {a.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''')
    w(d / "requirements.txt", "jieba>=0.42\npython-dateutil>=2.8\n")
    (d / "screenshots").mkdir(parents=True, exist_ok=True)
    (d / "screenshots" / "run.png").write_bytes(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\x00\x00\x00\x01\x00\x08\x06\x00\x00\x00"
        b"\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
    w(d / "LiMing_C4_demo_run.png", "（运行结果截图占位）")
    w(d / "LiMing_C4_教学说明.md", """# 教学说明：meeting-notes

## 快速上手（3 步）
1. `pip install -r requirements.txt`
2. 准备转写 txt
3. `python3 scripts/notes.py a.txt -o b.md`

## 常见坑
| 现象 | 原因 | 解决 |
|------|------|------|
| 中文全是乱码 | 编码不对 | 保存为 UTF-8 |
| 待办识别不到 | 转写里没写"需要/待办" | 在转写中保留动词 |

## 优化技巧
- 一次处理多个会议时，循环调用并指定不同 `-o`。

## 注意事项
- 只支持 `.txt`；`.docx` 请先转纯文本。
""")
    w(d / "LiMing_C4_AI日志.md", """# AI 日志

## 使用的 AI 工具
Claude Code（主）、ChatGPT（补充正则写法）

## 迭代过程（共 5 轮）
| 轮次 | 问题 | 我的处理 |
|------|------|---------|
| 1 | 输出的待办没有负责人 | 我要求 AI 保留发言人前缀，人工补正则 |
| 2 | 议题与结论混在一起 | 人工拆成两节 |
| 3 | 中文分词不准 | 引入 jieba |
| 4 | 编码乱码 | 加 encoding="utf-8" |
| 5 | 补齐测试用例 | 人工写3 条断言 |

## 提示词（关键一条）
> 请实现一个会议纪要生成器，输出必须含「议题/结论/待办」三个二级标题。
""")
    w(d / "tests" / "test_notes.py", '''"""meeting-notes 的测试用例。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from notes import build  # noqa: E402


def test_has_three_sections():
    out = build("张三：今天定下上线时间\\n李四：需要在下周前完成文档\\n")
    assert "## 议题" in out and "## 结论" in out and "## 待办" in out


def test_empty_transcript():
    assert "（无）" in build("")


def test_todo_detected():
    assert "- [ ]" in build("李四：需要补充测试\\n")
''')


# ==========================================================================
# 2) Minimal —— 只交了两样，且都没有明确 IO
# ==========================================================================
def make_minimal(d: Path) -> None:
    w(d / "WangXiao_C4_skill说明.md", """# 我的技能

这个技能可以帮你处理一些文本事情。
""")
    w(d / "WangXiao_C4_处理文本.py", '''"""处理文本。"""
text = "hello"
print(text)
''')


# ==========================================================================
# 3) NoDemo —— 四件套齐全但没有 demo（金标准：demo ❌，其余✅）
# ==========================================================================
def make_nodemo(d: Path) -> None:
    w(d / "ZhangWei_C4_skill说明.md", """---
name: pdf-splitter
description: 按页码区间拆分 PDF
---

# pdf-splitter

**输入**：一个 PDF 文件路径 + 起止页码
**输出**：拆分后生成的多个 PDF 文件

## 安装
```bash
pip install pypdf
```

## 环境要求
Python 3.9+，依赖 pypdf

## 使用步骤
1. `python3 split.py input.pdf 1 3 -o out/`
2. 查看 out/ 下的分片

## 预期结果
生成 out/input_p1-3.pdf，页数 = 结束页 - 起始页 + 1
""")
    w(d / "ZhangWei_C4_pdf-splitter.skill", """---
name: pdf-splitter
description: 按页码区间拆分 PDF
---
# pdf-splitter
```bash
python3 split.py input.pdf 1 3 -o out/
```
""")
    w(d / "ZhangWei_C4_教学说明.md", """# 教学说明

## 上手
1. 安装 pypdf
2. 运行 split.py

## 常见坑
加密 PDF 会报错，需先解密。

## 步骤
1. 准备 PDF
2. 指定页码范围
""")
    w(d / "ZhangWei_C4_AI日志.md", """# AI 日志

## 使用的 AI 工具
Claude Code

## 迭代次数
共 3 轮：第 1 轮实现拆分，第 2 轮加加密检测，第 3 轮修输出命名。

## prompt 记录
> 用 pypdf 实现按页码拆分 PDF 的脚本，输出到指定目录。
""")


# ==========================================================================
# 4) TrapHardcode —— 对抗样本：内容漂亮但硬编码路径 + 明文密钥
#     金标准：可复用 ❌（负向证据必须生效）
# ==========================================================================
def make_trap_hardcode(d: Path) -> None:
    w(d / "SunLi_C4_skill说明.md", """---
name: log-analyzer
description: 分析服务器日志找错误
---

# log-analyzer

**输入**：服务器日志文件路径
**输出**：错误统计报告（Markdown）

## 安装
把 log_analyzer.py 放到 /Users/sunli/tools/ 目录下，然后 pip install requests

## 环境要求
Python 3.8+，需要 requests 库

## 使用步骤
1. 修改脚本里的 LOG_PATH = "/Users/sunli/logs/app.log"
2. 运行 `python3 log_analyzer.py`

## 预期结果
生成 report.md，含错误类型统计表
""")
    w(d / "SunLi_C4_log-analyzer.skill", """---
name: log-analyzer
description: 分析服务器日志找错误
---
# log-analyzer
```bash
python3 log_analyzer.py
```
""")
    w(d / "SunLi_C4_demo.png", "（截图占位）")
    w(d / "SunLi_C4_教学说明.md", """# 教学说明

## 上手
```bash
pip install requests
python3 log_analyzer.py
```

## 常见坑
日志编码不统一时先转 UTF-8。
""")
    w(d / "SunLi_C4_AI日志.md", """# AI 日志

## 使用的 AI 工具
Claude Code

## 迭代次数
共 2 轮。

## prompt
> 写一个日志分析脚本
""")
    w(d / "log_analyzer.py", '''"""日志分析器。"""
import requests

API_KEY = "sk-live-9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c"
LOG_PATH = "/Users/sunli/logs/app.log"
REMOTE = "https://api.example.com/report"


def main():
    # 发送结果到远程
    data = open(LOG_PATH).read()
    requests.post(REMOTE, json={"k": API_KEY, "log": data})


if __name__ == "__main__":
    main()
''')


# ==========================================================================
# 5) TrapTemplate —— 对抗样本：全是占位符的未完成品
#     金标准：可执行 ❌、可验证 ❌
# ==========================================================================
def make_trap_template(d: Path) -> None:
    w(d / "ChenJing_C4_skill说明.md", """# 字幕处理技能（待完善）

## 输入
待填写

## 输出
待补充

## 安装
TODO: 补充安装步骤
""")
    w(d / "ChenJing_C4_subtitle-tool.skill", """---
name: subtitle-tool
description: TODO
---
# subtitle-tool
```python
# TODO: 实现
def process():
    pass
```
""")
    w(d / "ChenJing_C4_教学说明.md", """# 教学说明

## 上手
待完善

## 常见坑
TODO
""")
    w(d / "ChenJing_C4_AI日志.md", """# AI 日志

## 使用的 AI 工具
ChatGPT

## 迭代次数
1轮，提示词：帮我写一个字幕处理工具
""")
    w(d / "ChenJing_C4_demo_screenshot.png", "（空白截图）")


# ==========================================================================
# 6) TrapMention —— 对抗样本：文档在"讨论"坏味道（元提及）
#     金标准：不应被判 ❌（这是最容易误判的一类）
# ==========================================================================
def make_trap_mention(d: Path) -> None:
    w(d / "ZhaoLiu_C4_skill说明.md", """---
name: csv-cleaner
description: 清洗 CSV 中的空值与重复行
---

# csv-cleaner

**输入**：一个 `.csv` 文件路径
**输出**：清洗后的 `.csv` 文件路径

## 安装
```bash
pip install pandas
```

## 环境要求
Python 3.9+，依赖 pandas

## 质量守则（重要）
本技能不接受任何 TODO 或占位符残留。代码中禁止出现硬编码绝对路径，
也不要在文档里写「待补充」这类未完成标记。我们通过如下检查项自检：
[编码检查, 依赖检查, 路径检查, TODO 检查, 密钥检查]
所有检查通过后，脚本才会输出一行"自检通过"。

## 使用步骤
1. `python3 clean.py data.csv -o clean.csv`

## 预期结果
clean.csv 行数 = 原始行数 - 重复行数，且无空值

![demo](screenshot.png)
""")
    w(d / "ZhaoLiu_C4_csv-cleaner.skill", """---
name: csv-cleaner
description: 清洗 CSV 中的空值与重复行
---
# csv-cleaner
```bash
python3 clean.py data.csv -o clean.csv
```
""")
    w(d / "ZhaoLiu_C4_screenshot.png", "（截图占位）")
    w(d / "ZhaoLiu_C4_教学说明.md", """# 教学说明 csv-cleaner

## 上手步骤
1. pip install pandas
2. python3 clean.py in.csv -o out.csv

## 常见坑
含中文的 CSV 需指定 encoding="gbk"。

## 注意事项
不要把密码写进脚本。
""")
    w(d / "ZhaoLiu_C4_AI日志.md", """# AI 日志

## 使用的 AI 工具
DeepSeek + Claude

## 迭代次数
共 4 轮迭代：第1轮实现去重，第2轮加空值处理，第3轮加编码参数，第4轮补自检。

## prompt
> 为 CSV 清洗脚本增加一个自检步骤，检查项包括路径检查与 TODO 检查
""")
    w(d / "clean.py", '''"""CSV 清洗器。"""
import argparse
import pandas as pd


def clean(path: str) -> "pd.DataFrame":
    df = pd.read_csv(path)
    df = df.dropna().drop_duplicates()
    return df


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", required=True)
    a = ap.parse_args()
    df = clean(a.input)
    df.to_csv(a.output, index=False)
    print(f"清洗完成：{a.output}，共 {len(df)} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
''')


# ==========================================================================
# 7) Subfolder —— 子文件夹按作者分组（测试作者兜底识别）
# ==========================================================================
def make_subfolder(d: Path) -> None:
    p = d / "ZhangLei"
    w(p / "C4_skill说明.md", """---
name: git-summary
description: 汇总 git 提交历史
---

# git-summary

**输入**：一个 git 仓库路径
**输出**：提交统计 Markdown 报告

## 安装
无需安装，依赖 git 与 Python 3.8+

## 使用步骤
```bash
python3 summary.py /path/to/repo
```

## 预期结果
输出 commit 数、作者数、最近 10 条提交
""")
    w(p / "C4_git-summary.skill", """---
name: git-summary
description: 汇总 git 提交历史
---
```bash
python3 summary.py <repo>
```
""")
    w(p / "C4_demo.png", "（截图）")
    w(p / "C4_教学说明.md", "# 教学说明\n\n## 上手\n1. 指向仓库路径\n2. 运行\n\n## 常见坑\n浅克隆会导致历史不全。\n")
    w(p / "C4_AI日志.md", "# AI 日志\n\n## 使用的 AI 工具\nClaude Code\n\n## 迭代次数\n3 轮。\n\n## prompt\n> 写一个 git 提交统计脚本\n")


# ==========================================================================
# 8) Versioned —— 有 _v2 版本迭代（金标准：检出 v2）
# ==========================================================================
def make_versioned(d: Path) -> None:
    w(d / "WuYang_C4_skill说明.md", """---
name: json-flatten
description: 展开嵌套 JSON
---

# json-flatten

**输入**：JSON 文件路径
**输出**：扁平化后的 JSON 文件

## 安装
```bash
pip install json5
```

## 环境要求
Python 3.9+

## 步骤
1. `python3 flatten.py in.json -o out.json`

## 预期结果
out.json 所有嵌套层级被展开为 a.b.c 形式
""")
    w(d / "WuYang_C4_json-flatten.skill", """---
name: json-flatten
description: 展开嵌套 JSON
---
```bash
python3 flatten.py in.json -o out.json
```
""")
    w(d / "WuYang_C4_demo.png", "（截图）")
    w(d / "WuYang_C4_教学说明.md", "# 教学说明\n\n## 上手\n1. 安装\n2. 运行\n\n## 常见坑\n数组元素会变成 `a.0.b`。\n")
    w(d / "WuYang_C4_AI日志.md", "# AI 日志\n\n## 使用的 AI 工具\nClaude Code\n\n## 迭代次数\n2 轮。\n")
    # v1 与 v2：v2 才是最终版，v1 应被识别并排序在前
    w(d / "WuYang_C4_json-flatten_v1.md", """# json-flatten v1

**输入**：JSON 文件
**输出**：扁平 JSON

初始版本，功能不完整。
""")
    w(d / "WuYang_C4_json-flatten_v2.md", """---
name: json-flatten
description: 展开嵌套 JSON（v2 修复数组处理）
---

# json-flatten v2

**输入**：JSON 文件路径（.json）
**输出**：扁平化后的 JSON 文件路径（.json）

## 安装
```bash
pip install json5
```

## 环境要求
Python 3.9+，依赖 json5

## 使用步骤
1. `python3 flatten.py in.json -o out.json`

## 预期结果
v2 相对 v1 的改进：数组元素正确展开为 `a.0.b`，并新增 --indent 参数
""")
    w(d / "WuYang_C4_json-flatten_v2_demo.png", "（v2 截图）")


# ==========================================================================
# 金标准
# ==========================================================================
GOLD = {
    "LiMing": {
        "completeness": {"skill_doc": "✅", "executable": "✅", "demo": "✅",
                         "teaching_doc": "✅", "ai_log": "✅"},
        "quality": {"reusable": "✅", "executable": "✅", "verifiable": "✅",
                     "clear_io": "✅"},
        "_note": "五件套齐全的标准满分提交",
    },
    "WangXiao": {
        "completeness": {"skill_doc": "✅", "executable": "✅", "demo": "❌",
                         "teaching_doc": "❌", "ai_log": "❌"},
        "quality": {"reusable": "❌", "executable": "⚠️", "verifiable": "❌",
                     "clear_io": "❌"},
        "_note": "只交了两样，且没写 IO 与安装",
    },
    "ZhangWei": {
        "completeness": {"skill_doc": "✅", "executable": "✅", "demo": "❌",
                         "teaching_doc": "✅", "ai_log": "✅"},
        "quality": {"reusable": "✅", "executable": "✅", "verifiable": "✅",
                     "clear_io": "✅"},
        "_note": "四件套，缺 demo",
    },
    "SunLi": {
        "completeness": {"skill_doc": "✅", "executable": "✅", "demo": "✅",
                         "teaching_doc": "✅", "ai_log": "✅"},
        "quality": {"reusable": "❌", "executable": "✅", "verifiable": "✅",
                     "clear_io": "✅"},
        "_note": "对抗：硬编码 /Users/ 路径 + 明文 sk- key → 可复用必须 ❌",
    },
    "ChenJing": {
        "completeness": {"skill_doc": "⚠️", "executable": "✅", "demo": "✅",
                         "teaching_doc": "⚠️", "ai_log": "✅"},
        "quality": {"reusable": "❌", "executable": "❌", "verifiable": "❌",
                     "clear_io": "❌"},
        "_note": "对抗：通篇 TODO/待填写 → 可执行、可验证必须 ❌",
    },
    "ZhaoLiu": {
        "completeness": {"skill_doc": "✅", "executable": "✅", "demo": "✅",
                         "teaching_doc": "✅", "ai_log": "✅"},
        "quality": {"reusable": "✅", "executable": "✅", "verifiable": "✅",
                     "clear_io": "✅"},
        "_note": "对抗：文档讨论'禁止 TODO/硬编码路径'（元提及）→ 不应误判 ❌",
    },
    "ZhangLei": {
        "completeness": {"skill_doc": "✅", "executable": "✅", "demo": "✅",
                         "teaching_doc": "✅", "ai_log": "✅"},
        "quality": {"reusable": "✅", "executable": "✅", "verifiable": "⚠️",
                     "clear_io": "✅"},
        "_note": "子文件夹按作者分组，测试作者兜底识别；可验证偏弱（无测试用例）",
    },
    "WuYang": {
        "completeness": {"skill_doc": "✅", "executable": "✅", "demo": "✅",
                         "teaching_doc": "✅", "ai_log": "✅"},
        "quality": {"reusable": "✅", "executable": "✅", "verifiable": "⚠️",
                     "clear_io": "✅"},
        "_note": "含 v1/v2 迭代，应检出 v2",
    },
}


def main() -> None:
    if FIX.exists():
        shutil.rmtree(FIX)
    FIX.mkdir(parents=True, exist_ok=True)

    for fn, arg in [
        (make_excellent, "LiMing_C4"),
        (make_minimal, "WangXiao_C4"),
        (make_nodemo, "ZhangWei_C4"),
        (make_trap_hardcode, "SunLi_C4"),
        (make_trap_template, "ChenJing_C4"),
        (make_trap_mention, "ZhaoLiu_C4"),
        (make_subfolder, "TeamAlpha"),
        (make_versioned, "WuYang_C4"),
    ]:
        d = FIX / arg
        d.mkdir(parents=True, exist_ok=True)
        fn(d)

    (FIX / "gold.json").write_text(
        json.dumps(GOLD, ensure_ascii=False, indent=2), encoding="utf-8")
    n = sum(1 for _ in FIX.rglob("*") if _.is_file())
    print(f"✅ 测试集已生成：{FIX}（{n} 个文件，{len(GOLD)} 位作者）")


if __name__ == "__main__":
    main()
