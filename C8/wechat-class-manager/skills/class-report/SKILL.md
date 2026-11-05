---
name: class-report
description: 生成班级周报（Markdown，可直接发群/转公众号）、预警清单、催办草稿和静态看板。当用户说「出周报」「班级什么状态」「做个看板」时使用。
inputs:
  - linked.jsonl / submissions.json / qa.json / profiles.json / alerts.json
outputs:
  - report.md            # 周报，八个小节
  - report.json          # 机器可读快照（AAR 对比用）
  - dashboard/index.html # 单文件看板，双击可开
  - nudges.md            # 催办草稿（不发送）
entry: python -m wcm.cli report && python -m wcm.cli dashboard
---

# class-report · Layer 4 报告与看板

## 周报八节

一句话结论 → 关键数字 → 各挑战提交率 → 活跃 Top5 → 最佳 Q&A →
需要处理的事 → 下周建议 → 口径与局限

最后一节是刻意保留的：**每个数字都要能说出出处**，说不出的不写。

## 看板

- 单文件 HTML，**零依赖、零 CDN、断网可开**，发到群里别人下载就能看。
- 六个 KPI、20 条提交率、20×20 提交矩阵、活跃榜、沉默名单、
  意图分布、预警列表、最佳问答。
- 悬停任意格子可看到「谁 · 哪个挑战 · 什么状态」。

## 预警七条

截止风险 / 提交率过低 / 沉默学生 / 活跃度下降 / 提交缺件 / 提问无人回答 / 命名违规

每条都带 `evidence`（哪几条数据算出来的）和 `action`（建议怎么做），
没有证据的预警不产生——否则老师会关掉通知。

## 验收

- 报告里的数字与 `report.json`、`submissions.json` 一致。
- 预警在构造场景下能触发 ≥3 种（见 `tests/test_pipeline.py::TestAlerts`）。
- 看板覆盖 ≥5 个维度的班级数据。
