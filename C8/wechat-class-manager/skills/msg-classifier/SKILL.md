---
name: msg-classifier
description: 给群消息打意图标签（提交/提问/回答/讨论/通知/资源/闲聊），并输出判定依据与置信度。当需要「判断这条消息在说什么」「筛选出所有提问」「统计讨论量」时使用。
inputs:
  - messages.jsonl
outputs:
  - classified.jsonl   # 原字段 + intent / confidence / signals / scores / challenge_ref
  - metrics.json       # 与标注集对比的准确率、混淆矩阵
entry: classifier.py
---

# msg-classifier · Layer 2 意图分类

## 七个标签

`submission` 提交 · `question` 提问 · `answer` 回答 · `discussion` 讨论 ·
`announcement` 通知 · `resource` 资源 · `social` 闲聊

## 为什么不是纯 LLM

一天几百条消息全量过 LLM，又慢又贵，而且 80% 靠结构就能判。
所以默认「打分规则 + 上下文」，只有 `confidence < 0.45` 或 `margin < 0.5` 的消息
才建议交 LLM 复核（`--llm-review`，需 `WCM_LLM_BASE` / `WCM_LLM_KEY`）。

## 打分怎么算

每个意图独立累计证据分数，取最大者。例：

```
"林一舟_C8_proposal.md"（文件消息）
  submission +6  （文件名符合 姓名_挑战ID_内容）
  discussion -2  （文件消息）
  question   -1.5（文件消息）
→ submission，confidence 0.93
```

## 输出

```json
{"msg_id":"m00003","content":"请问 C8 的 demo 一定要能跑起来吗？",
 "intent":"question","confidence":0.86,
 "signals":["question:问号结尾","question:疑问词 请问"],
 "scores":{"question":5.5,"discussion":-2,"social":-3}}
```

## 验收

- 在 `data/fixtures/labels.jsonl` 上准确率 > 70%（当前实测 91.8%，268 条）。
- 每条都有 `signals`，能回答「凭什么判成提问」。
- `needs_review` 字段标出需要人工/LLM 复核的消息（默认 56/268）。
