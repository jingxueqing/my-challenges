---
name: student-profile
description: 从群互动与提交记录生成学生画像——活跃度、助人次数、提交覆盖、技能标签、风险信号。当用户问「某某怎么样」「谁最需要关注」「谁擅长什么」时使用。
inputs:
  - linked.jsonl
  - submissions.json
  - qa.json
outputs:
  - profiles.json
entry: python -m wcm.cli profile
---

# student-profile · Layer 3 学生画像

画像回答三个具体问题，不做玄学：

1. **他还在吗** — `msg_count` / `week_msgs` / `silence_days` / `delta_ratio`
2. **他有产出吗** — `submissions` / `accepted` / `challenges` / `missing_items`
3. **他在帮谁** — `answers_given` / `qa_answered` / `helped_and_thanked`（被感谢次数）

## 参与分口径（0–100）

```
发言 35 + 助人 25 + 完整提交 30 + 持续性 10
```

系数写在 `wcm/profile.py::_engagement`，改口径只改这个函数，
`dashboard` 和 `report` 会自动跟着变——口径只有一处定义。

## 风险标记

`沉默 N 天` / `活跃度下降 X%` / `N 项提交缺件` / `只问不答`

## 边界（重要）

- 不预测成绩，不评价能力高低，只描述**可观测行为**。
- 沉默 ≠ 不努力。所以预警的 action 写的是「先问是不是遇到困难」，不是「催交」。
