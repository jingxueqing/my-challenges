---
layer: L4_tool
updated: 2026-11-05
note: 机器可读的表格在下方；`kstar.py` 不解析本文件，只作为人类与 Agent 的共同清单。
---

# tools.md — 我的工具层（Action = Plan × Access Token × Energy）

规则：**只留 3–5 个核心工具 + 一条清晰的串联方式**。
工具多不等于行动半径大；能串联的才叫半径。

## 核心工具（真的在用）

| id | 类别 | 工具 | 用途 | 状态 | 调用方式 |
|---|---|---|---|---|---|
| llm-main | LLM | WorkBuddy（Agent 模式）/ DeepSeek | 推理、生成、找反例、写代码 | active | 对话 + 读写文件 + 执行命令 |
| llm-local | LLM（本地） | Ollama + Gemma（C4D 验证过 E2B 档位） | 离线、无网、隐私场景的推理 | active | `ollama run` |
| code-python | 代码 | Python 3.13（本机托管版）/ zsh | 一切脚本、验证、自动化 | active | `python3` |
| repo-git | 版本控制 | git（本地仓库 + GitHub） | Skill 与交付物的版本留痕 | active | `git init/add/commit/push` |
| kb-markdown | 知识管理 | 本仓库 `memory/` + `skills/`（纯 Markdown） | L1/L2/L3 的载体 | active | 文件系统，零依赖 |
| search-web | 浏览器/API | WebSearch / WebFetch | 竞品、文档、事实核查 | active | 由 Agent 调用 |
| deploy-web | 部署 | WorkBuddy 托管发布（静态/Node/Python） | 把东西变成"别人能打开的链接" | active | 发布链路 |
| im-wechat | 通讯 | 微信群 / 公众号（扫码手动发布） | 交付与传播的最后一公里 | active（人工确认） | 手机扫码，AI 不代发 |
| office-doc | 文档 | Markdown → docx/pptx 渲染链路 | 需要正式格式时 | active | 本地脚本 |

## 不用 / 淘汰的工具（记录原因，避免重复踩坑）

| 工具 | 为什么不用 |
|---|---|
| 向量数据库（Chroma/FAISS） | 语料不到 200 篇，BM25 + 中文二元组足够；加向量库只增加部署成本（见 EP-2026-11-05-001 的反例） |
| Notion / Obsidian | 数据要能跟着 git 走、能被脚本读；纯文件最稳 |
| Neo4j | C8 明确否决：图查询不是当时的瓶颈，是"看起来高级"的成本 |
| 微信数据库解密（chatlog/attach 进程） | 侵入式，主动不做（C8 失败 1） |

## 串联方式（一条链，不是一堆孤岛）

```
WebSearch/WebFetch  →  memory/L1_raw（add）
        ↓                    ↓
   LLM（WorkBuddy）      ep new（KSTAR 结构化）
        ↓                    ↓
   kstar.py loop       skills/（ distill 长出候选 → 验证 → 上线）
        ↓                    ↓
   交付物 / 上线链接  ←  dash / report（看自己是否在变强）
```

**这张表的用法**：每次开工前问一句"这一轮我需要哪几个 access token"。
如果答案是"三个以上"，先砍需求，不是先装工具。
