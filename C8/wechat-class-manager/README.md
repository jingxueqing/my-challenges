# wechat-class-manager

> 把一个微信群，变成 Agent 可以调用的班级管理系统。
> 不替换微信，只在消息流上加一层智能层：让「谁交了 / 谁卡住了 / 谁在帮谁」从翻聊天记录变成一次查询。

**当前版本**：v1.0.0 ｜ **依赖**：只依赖 Python 3.10+ 标准库 ｜ **测试**：60 个，全通过

---

## 30 秒跑通

```bash
cd wechat-class-manager
python3 -m wcm.cli run --days 14 --fs ~/Desktop/挑战的产物 --owner JingXueQing
open out/dashboard/index.html
python3 -m wcm.cli query "C4B 还有谁没交"
```

不需要装任何包、不需要起服务、不需要连微信。产物全在 `out/`：

| 文件 | 是什么 |
|---|---|
| `out/messages.jsonl` | 标准化后的群消息（UMF） |
| `out/classified.jsonl` | 每条消息的意图 + 置信度 + 判定依据 |
| `out/submissions.json` | 学生 × 挑战提交矩阵、缺件清单 |
| `out/qa.json` | 问答对（含质量分、未答问题） |
| `out/profiles.json` | 学生画像 |
| `out/alerts.json` | 预警（含证据与建议） |
| `out/report.md` | 周报，可直接发群 |
| `out/dashboard/index.html` | 单文件看板，双击可开 |
| `out/graph.db` | Property Graph（SQLite，可换 Neo4j） |
| `out/nudges.md` | 催办草稿（**不会自动发送**） |

---

## 它解决什么

| 真实痛点 | 之前 | 现在 |
|---|---|---|
| 提交追踪 | 老师手动翻群文件 | `submission-tracker` 自动出矩阵 + 缺件清单 |
| 活跃度 | 全凭感觉 | 每人发言频率、时段、ΔE 可查 |
| 问答沉淀 | 好问题三天后沉底 | 48 对问答自动入库，可检索 |
| 通知确认 | 发了不知道谁看了 | 已读/已回/已行动可追踪 |
| 学生画像 | 不了解每个人强弱 | 从群互动推断技能标签与风险 |

---

## 四个 Level 的完成度

| Level | 要求 | 状态 | 证据 |
|---|---|---|---|
| L1 Bronze | 提取 ≥100 条消息、符合 schema、可重复运行 | ✅ | 268 条；`wechat_bridge.py`；`sample_output.jsonl` |
| L2 Silver | 分类准确率 >70%、检出 ≥5 提交、≥10 组 Q&A | ✅ | 91.8% / 44 项 / 48 对 |
| L3 Gold | 标准 SKILL.md、图存储、≥5 类自然语言查询 | ✅ | 6 个子技能；702 条边；10 类查询 |
| L4 Platinum | Watcher 增量、≥3 种预警、周报、看板、可部署 | ✅ | 二次运行 new=0；7 条规则；单文件看板 |

---

## 实测数字（可复现）

| 指标 | 数值 | 怎么测的 |
|---|---|---|
| 分类准确率 | **91.8%**（macro-F1 0.878） | 268 条人工标注回放集，`out/metrics.json` |
| 挑战关联覆盖 | 89.2%（239/268） | `out/summary.json` |
| 提交项 / 文件 | 44 项 / 307 个文件 | 14 项来自磁盘真实提交包，其余来自群文件消息 |
| 完整提交 | 36 项（缺件 7 项） | 必备件比对 `config/challenges.yaml` |
| Q&A | 48 对（答出率 78.7%，均分 0.55） | `out/qa.json` |
| 图规模 | 6 类节点 / 702 条边 | `out/graph.db` |
| 测试 | 60 个通过 | `python3 -m wcm.cli selftest` |

> 准确率是在**合成脱敏回放集**上测的；真实微信群的准确率尚未测量（本机微信库加密，见 `docs/数据说明.md`）。这个差异我写在报告和看板页脚里，没有藏。

---

## 目录

```
wechat-class-manager/
├── SKILL.md                     # 技能总入口（Agent 先读这个）
├── README.md  SETUP.md          # 本文件 / 部署指南
├── wechat_bridge.py             # L1 CLI
├── classifier.py                # L2 CLI
├── challenge_linker.py          # L2 CLI
├── submission_detector.py       # L2 CLI
├── qa_extractor.py              # L2 CLI
├── wcm/
│   ├── bridge/                  # adapters: replay / chatlog / sqlcipher / fs_scan
│   ├── classifier.py            # 打分式意图分类
│   ├── linker.py                # 挑战关联
│   ├── submissions.py           # 提交矩阵
│   ├── qa.py                    # 问答抽取
│   ├── profile.py               # 学生画像
│   ├── alerts.py                # 预警引擎
│   ├── report.py                # 周报
│   ├── dashboard.py             # 单文件看板
│   ├── query.py                 # 自然语言查询路由
│   ├── watcher.py               # 增量处理 + checkpoint
│   ├── ingest.py / store.py     # Property Graph
│   └── cli.py                   # 统一命令
├── skills/                      # 6 个子技能，各有 SKILL.md
├── schemas/                     # UMF / Submission / Student + domain-graph.yaml
├── config/                      # 挑战定义、群配置、阈值（改这里不改代码）
├── data/fixtures/               # 268 条脱敏回放集 + 人工标注
├── tests/                       # 62 个测试
├── docs/                        # 架构、数据说明
└── out/                         # 产物
```

---

## 命令速查

```bash
python3 -m wcm.cli doctor                     # 环境自检（含本机微信库加密检测）
python3 -m wcm.cli run --days 14 [--fs DIR]   # 全链路
python3 -m wcm.cli query "林一舟的画像"        # 自然语言查询
python3 -m wcm.cli watch --days 1             # 增量抓取（可挂 cron）
python3 -m wcm.cli alerts --as-of 2026-12-29  # 按指定日期演练预警
python3 -m wcm.cli selftest                   # 跑测试
```

---

## 已知局限（写在这里，不藏在代码注释里）

1. **真实微信群未接通**：本机 WeChat 4.x 的 `message_*.db` 是 SQLCipher 加密的，密钥只在进程内存里，取出需要侵入式操作。所以默认走 `replay`，`chatlog` adapter 已实现但本机未验证。
2. **分类器是规则驱动**：91.8% 是回放集成绩，换一个群的说话风格需要重新校准（调 `wcm/classifier.py` 的 `_scores`）。
3. **不判断作业质量**：这套系统只回答「交了没有、齐不齐、谁在帮谁」，不评价内容好坏。
4. **不做自动发送**：`nudge` 只出草稿，写回群需要人工确认。
5. **规模上限**：SQLite 在图规模万级节点内很稳，再大建议换 Neo4j（换 `store.py` 一个类）。

---

## 三条最容易踩的坑（都是我自己踩过的）

1. **忘了 `--fs`**：不传它，`run` 只从群消息推提交，提交数会从 44 掉到 30，
   而且**不报错**——因为"少传参数"和"今天真没人交"在输出上长得一样。
   现在脚本会打印一行 `未传 --fs，跳过磁盘扫描…`。看到这行就说明数字偏小。
2. **忘了 `--owner`**：磁盘上有些文件名不带姓名（如 `C4A评审器.zip`），
   没给 `--owner` 时它们会归到"未知学生"，导致某人明明交了却显示缺件。
3. **验证增量用错了库**：在已经被 `run` 写满的 `out/graph.db` 上连跑两次 `watch`，
   两次都是 `new: 0`——**这什么也没证明**。要验增量请指向空库：
   `python3 -m wcm.cli watch --days 14 --db /tmp/x.db`，第一次应当是 `new: 268`。

顺带一条：`out/graph.db` 是纯派生数据，坏了直接 `rm` 重跑，别手修。

---

## 许可

MIT。`config/` 里的挑战定义来自课程官方材料，仅用于本课程场景。
