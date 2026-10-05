---
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
