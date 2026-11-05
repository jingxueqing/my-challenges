---
name: submission-tracker
description: 从群文件消息 + 磁盘提交包构建「学生 × 挑战」提交矩阵，判断每项是否必备件齐全、命名是否规范，输出缺件清单。当用户问「谁交了」「谁没交」「还缺什么」时使用。
inputs:
  - linked.jsonl       # 带 challenge_ref 的消息
  - fs_submissions     # 可选，磁盘扫描结果
  - config/challenges.yaml  # 每个挑战的必备件
outputs:
  - submissions.json   # matrix / rows / missing_required / by_challenge
entry: submission_detector.py
---

# submission-tracker · Layer 3 提交追踪

## 判定顺序（和老师手工验收一致）

1. 是文件消息吗？不是 → 不可能是提交。
2. 文件名能解析出挑战 ID 吗？→ 解析不到就用消息的 `challenge_ref`。
3. 挑战要求的必备件齐吗？→ 缺件标 `needs_revision` 并列出缺什么。
4. 命名规范吗？→ 不规范记 issue（老师最常打回的原因）。

## 关键取舍

**以文件为准，消息只补时间线。** 「我交了」不等于交了，能验收的只有文件。
所以磁盘扫描（`--fs`）的结果优先于群消息，同名文件不重复计。

## 输出片段

```json
{"id":"submission:wxid_linyz:C8","nickname":"林一舟","challenge":"C8",
 "required":["proposal","demo","ailog","notes"],
 "kinds":["ailog","notes","proposal"],"missing":["demo"],
 "completeness":0.75,"status":"needs_revision",
 "issues":[],"sources":["wechat"]}
```

## 口径

- 完成率分母 = 全班人数（不是报名人数；两种口径都会失真，这里固定并写明）。
- 一个学生同一挑战多次提交 → 合并为一项，artifacts 逐条保留。

## 验收

- 能正确检出回放集里的 ≥5 个提交事件（当前 44 项）。
- 缺件项能说出缺哪几件（用中文名，如「AI 日志」）。
- 老师发的模板不算学生提交。
