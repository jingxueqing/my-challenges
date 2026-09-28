---
source_file: prompt-engineering-guide.html
status: RECOVERED（2026-09-27 联网补抓成功）
url: https://www.promptingguide.ai/techniques
---

# 提示词工程技巧（Prompting Techniques | Prompt Engineering Guide）

> 原阅读：Prompt Engineering Guide — Prompting Techniques（https://www.promptingguide.ai/techniques，更新于 2025-12-28）。
> 该页为 SPA 动态加载，离线包未能存下正文；交付期间已联网补抓技巧总览并翻译如下（含 18 个技巧子页链接，子页未逐篇翻译，见 README 缺口台账）。

提示词工程（Prompt Engineering）的目标是通过设计与改进提示词，让大语言模型（LLM）在不同任务上获得更好的结果。在基础示例（零样本、少样本）之上，本节覆盖更进阶的提示词工程技巧，以完成更复杂的任务并提升 LLM 的可靠性与性能。

## 官方技巧总览（18 条，全译）

| # | 技巧 | 英文 | 子页 |
|---|---|---|---|
| 1 | 零样本提示 | Zero-shot Prompting | /techniques/zeroshot |
| 2 | 少样本提示 | Few-shot Prompting | /techniques/fewshot |
| 3 | 思维链提示 | Chain-of-Thought Prompting | /techniques/cot |
| 4 | 元提示 | Meta Prompting | /techniques/meta-prompting |
| 5 | 自洽性 | Self-Consistency | /techniques/consistency |
| 6 | 生成知识提示 | Generate Knowledge Prompting | /techniques/knowledge |
| 7 | 提示链 | Prompt Chaining | /techniques/prompt_chaining |
| 8 | 思维树 | Tree of Thoughts | /techniques/tot |
| 9 | 检索增强生成 | Retrieval Augmented Generation | /techniques/rag |
| 10 | 自动推理与工具使用 | Automatic Reasoning and Tool-use (ART) | /techniques/art |
| 11 | 自动提示词工程师 | Automatic Prompt Engineer (APE) | /techniques/ape |
| 12 | 主动提示 | Active-Prompt | /techniques/activeprompt |
| 13 | 方向性刺激提示 | Directional Stimulus Prompting | /techniques/dsp |
| 14 | 程序辅助语言模型 | Program-Aided Language Models (PAL) | /techniques/pal |
| 15 | ReAct（推理+行动） | ReAct | /techniques/react |
| 16 | 反思 | Reflexion | /techniques/reflexion |
| 17 | 多模态思维链 | Multimodal CoT | /techniques/multimodalcot |
| 18 | 图提示 | Graph Prompting | /techniques/graph |

> 子页逐篇详译：联网访问对应子页保存正文为 `corpus/en/` 下语料后，重跑 `bash run_all.sh translate --only <slug>` 即可补齐。
