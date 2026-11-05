---
name: qa-sink
description: 从聊天流中抽取「问题→回答」对，打分并打标签，沉淀成课程 FAQ。当用户问「关于 X 的常见问题」「这个问题以前答过吗」「把群里的问答整理出来」时使用。
inputs:
  - linked.jsonl
outputs:
  - qa.json   # pairs / top_pairs / unanswered / top_tags
entry: qa_extractor.py
---

# qa-sink · Layer 3 问答沉淀

## 配对规则（优先级从高到低）

1. 显式引用：B 的 `reply_to` 指向 A 的提问。
2. 时间窗：提问后 2 小时内、不同发送者、分类为 `answer` 的第一条。
3. 追问者说「谢谢/解决了」→ 标记 `resolved`，给质量分加成。

## 质量分（0–1）

`0.2` 基础 + 有人答 `0.25` + 答案长度 + 含命令/代码 + 分步骤 + 提问带上下文 +
被感谢 + 多人参与。低于 0.35 的不入库（阈值在 `config/group_config.yaml`）。

## 为什么有用

群里的问答三天后就翻不到了。抽出来之后：
- 老师能一次回答重复问题（`class-report` 周报会带「最佳问答」）；
- `student-profile` 能据此判断「谁在帮谁」；
- 同一套问答可以直接转成公众号 FAQ（接 C4B）。

## 验收

- 从回放集抽出 ≥10 个有意义的问答对（当前 48 对，答出率 79%）。
- 未被回答的问题单独列出，供预警使用。
