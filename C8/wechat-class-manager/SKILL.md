---
name: wechat-class-manager
description: 把一个微信群变成 Agent 可调用的班级管理系统。输入群聊（本地数据库或导出文件）+ 课程挑战配置，输出提交矩阵、Q&A 库、学生画像、预警、周报和看板。当用户提到「班级管理」「群消息分析」「谁没交」「学生画像」「周报」「考勤/提交追踪」时使用。
version: 1.0.0
license: MIT
---

# 微信群 → 班级管理 Agent 技能

> 不替换微信，只在消息流上加一层 Agent 智能层：让「谁交了、谁卡住了、谁在帮谁」
> 从翻聊天记录变成一次查询。

## 什么时候用

| 用户说什么 | 走哪个子技能 |
|---|---|
| 「把群消息导出成 JSON」 | `skills/wechat-bridge` |
| 「这条消息是提问还是提交」 | `skills/msg-classifier` |
| 「C4B 还有谁没交」「某某交了哪些」 | `skills/submission-tracker` |
| 「关于 GitHub 的常见问题」「把问答存下来」 | `skills/qa-sink` |
| 「某某擅长什么」「谁最需要关注」 | `skills/student-profile` |
| 「出周报」「班级现在什么状态」 | `skills/class-report` |

## 30 秒跑通（零第三方依赖）

```bash
python3 -m wcm.cli run --days 14 --fs ~/Desktop/挑战的产物 --owner <你的名字>
open out/dashboard/index.html      # 看板
python3 -m wcm.cli query "C4B 还有谁没交"
```

## 目录

```
wechat-class-manager/
├── SKILL.md                  # 本文件（技能总入口）
├── wechat_bridge.py          # L1 CLI：群消息 → JSONL
├── classifier.py             # L2 CLI：意图分类
├── challenge_linker.py       # L2 CLI：挑战关联
├── submission_detector.py    # L2 CLI：提交检测
├── qa_extractor.py           # L2 CLI：问答抽取
├── wcm/                      # 实现（bridge/classifier/linker/submissions/qa/profile/alerts/report/dashboard/query/watcher）
├── skills/                   # 6 个可被 Agent 单独调用的子技能
├── schemas/                  # UMF / Submission / Student schema + 领域图
├── config/                   # 挑战定义、群配置、阈值
├── data/fixtures/            # 脱敏回放集（268 条，带人工标注）
├── tests/                    # 62 个测试
├── out/                      # 产物（可整体重建）
└── docs/                     # 架构、数据说明、部署
```

## 契约

- 所有子技能都接受 **JSON/JSONL 文件路径** 作为输入输出，可单独跑、也可串联。
- 每个判定都带 `signals` 或 `evidence` 字段，答案可追溯。
- 写回群（nudge）**默认只生成草稿，不发送**。

## 常见失败

| 现象 | 原因 | 处理 |
|---|---|---|
| `取数失败：连不上 chatlog` | chatlog server 没起 | 起服务，或改用 `--source replay` |
| 提交矩阵是空的 | 文件名没有挑战 ID | 看 `submission_detector.py` 输出的 issues，退回重发 |
| 分类置信度普遍低 | 群语言风格差异大 | 用 `--llm-review` 复核低置信度消息 |
| 看板打开是空白 | 浏览器限制本地文件 JS | 本看板无 JS，检查是否被解压破坏 |

## 验收（自检）

```bash
python3 -m wcm.cli doctor      # 环境自检
python3 -m wcm.cli selftest    # 62 个测试
```
