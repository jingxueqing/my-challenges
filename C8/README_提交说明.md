# C8 提交说明 ｜ 微信群 → 班级管理 Agent

**提交人**：JingXueQing（景雪晴）｜ 学号 **2024102110351**｜ 挑战：C8 真实项目落地（Real-World Project Execution）
**一句话**：把 20 个挑战、21 个人的班级群，变成一套「一条命令跑完、十句话问得清、每条结论都能追到证据」的班级管理能力，并交成一个 Agent 能直接调用的技能包。

---

## 一、30 秒看结果

```bash
cd wechat-class-manager
python3 -m wcm.cli run --days 14 --fs ~/Desktop/挑战的产物 --owner JingXueQing
open out/dashboard/index.html          # 单文件看板，双击也能开
```

| 指标 | 数值 |
|---|---|
| 群消息 | 268 条 / 14 天 / 21 个发言人（脱敏回放集，带 268 条标注） |
| 分类准确率 | **91.8%**，macro-F1 0.878，错 22 条（课程线 70%） |
| 挑战关联覆盖 | 239/268（89.2%）：显式 ID 116 / 上文继承 81 / 关键词 42 / 未关联 29 |
| 提交矩阵 | 44 项提交 / 307 个文件 / 400 格；完整 36、缺件 7 |
| 其中**真实磁盘提交** | 14 个提交包、235 个文件（我 C1–C7 实际交过的） |
| Q&A 沉淀 | 48 对，答出率 78.7%，平均质量 0.549 |
| 知识图谱 | 402 节点 / 702 边 / FTS5 全文索引（SQLite 实现 property graph） |
| 预警 | 17 条（高 1 / 中 15 / 低 1），7 条规则，每条强制带 `evidence` + `action` |
| 技能 | 1 个总 `SKILL.md` + 6 个子技能 |
| 代码 | 5,739 行 Python / 32 个文件 / **零第三方依赖** |
| 测试 | 62 个，全绿，1.1 s |
| 全链路耗时 | ≈ 0.9 s（含图重建与看板渲染） |

---

## 二、交付物对照表（对着挑战要求逐条）

| 挑战要求 | 实际交付 | 说明 |
|---|---|---|
| `姓名_C8_proposal.md` | `JingXueQing_C8_proposal.md` | 五部分齐全：问题/对象/方案/里程碑/风险；附 KSTAR 认知环与 R̂ 验收表、六类引用来源、角色自述（Operator + Builder + Architect）、证据索引 |
| `姓名_C8_demo.*` | `JingXueQing_C8_demo.md` | 5 分钟可看完的演示脚本：一条命令 → 四个现场问题 → 增量 → 四份产物 → Agent 调用；每段都是真命令真输出 |
| `姓名_C8_AI日志.md`（必须） | `JingXueQing_C8_AI日志.md` | 14 轮真实迭代（含 6 次失败）、4 类 prompt 进化模式、"AI 帮上/没帮上"分栏、证据来源标注 |
| `姓名_C8_拿来说明.md` | `JingXueQing_C8_拿来说明.md` | 6 条筛选标准 → 6 个采纳 + 2 个否决（Neo4j / 纯 LLM 分类）；复用比例约 15% / 30% / 55% 三档；"我没拿什么"单列 |
| `姓名_C8_AAR_W周次.md` | `JingXueQing_C8_AAR_W1.md` | R̂（11 项）对 R 表逐项 ΔR；4 条失败按"根因 vs 看起来像但不是"写；下周 R̂；拿来更新（FTS5 采纳、Neo4j/LLM 全量否决） |
| （加分）可执行代码 | `wechat-class-manager/` | 完整仓库：库 + 6 个独立 CLI + 配置 + schema + 测试 + 产物 |
| （加分）验收记录 | `JingXueQing_C8_验收记录.md` | 11 段真实终端输出，含 10 类自然语言查询、增量两次对比、预警演练、图规模对账 |
| （加分）看板截图 | `screenshots/dashboard.png` | 2560×5862，2 倍像素 |

---

## 三、目录结构

```
C8-交付_JingXueQing_微信群班级管理Agent/
├── README_提交说明.md                 ← 本文件
├── JingXueQing_C8_proposal.md         ← 项目申请书（五部分）
├── JingXueQing_C8_demo.md             ← 5 分钟演示脚本
├── JingXueQing_C8_AI日志.md           ← 14 轮迭代（必须项）
├── JingXueQing_C8_拿来说明.md          ← 拿来主义：拿什么、怎么改、没拿什么
├── JingXueQing_C8_AAR_W1.md           ← 第一周 AAR（R̂ vs R）
├── JingXueQing_C8_验收记录.md          ← 11 段真实终端输出
├── screenshots/dashboard.png
└── wechat-class-manager/
    ├── README.md                      ← 怎么跑（含 3 条最容易踩的坑）
    ├── SETUP.md                       ← 部署/交接：从零到跑通
    ├── SKILL.md                       ← 总技能（Agent 入口）
    ├── skills/                        ← 6 个子技能，各带"什么时候不要用"
    │   ├── wechat-bridge/  msg-classifier/  submission-tracker/
    │   └── qa-sink/  student-profile/  class-report/
    ├── wcm/                           ← 库（17 个模块，5739 行）
    │   ├── bridge/                    通道适配：回放 / chatlog HTTP / sqlcipher
    │   ├── classifier.py              打分式意图分类（带 signals 可解释）
    │   ├── linker.py                  四级关联：显式 ID > 文件名 > 关键词 > 上文继承
    │   ├── submissions.py             提交矩阵（以磁盘文件为准）
    │   ├── qa.py / profile.py         问答沉淀 / 学生画像
    │   ├── alerts.py / nudge.py       预警（7 规则）/ 催办草稿（只生成不发送）
    │   ├── report.py / dashboard.py   周报 / 61KB 单文件看板
    │   ├── store.py / ingest.py       SQLite property graph + FTS5
    │   ├── query.py                   11 类自然语言查询
    │   ├── watcher.py                 增量（checkpoint 存图里）
    │   ├── yamlite.py                 零依赖 YAML 子集解析（不装 PyYAML）
    │   └── cli.py                     16 个子命令
    ├── config/                        ← 20 个挑战规格 + 名单 + 阈值（改这里，不改代码）
    ├── schemas/                       ← UMF 消息 / 提交 / 学生 / 领域图
    ├── data/                          ← 268 条脱敏消息 + 268 条标注 + 生成脚本
    ├── tests/                         ← 62 个测试
    ├── docs/                          ← 架构.md（含取舍与"如果重来"）/ 数据说明.md
    ├── out/                           ← 跑好的产物：看板、周报、预警、催办、graph.db
    └── sample_output.jsonl            ← 20 条 UMF 样本，给人看格式
```

---

## 四、四级 Level 自查

| Level | 课程要求 | 实测 | 证据 |
|---|---|---|---|
| L1 Bronze | 提取 ≥100 条、符合 schema、CLI 可重复 | 268 条 UMF、`--days 14` 复跑同结果 | 验收记录 §1 §2；`schemas/message.schema.json` |
| L2 Silver | 分类 >70%、检出 ≥5 提交、≥10 组 Q&A | 91.8%、44 项、48 对 | 验收记录 §3 §4 |
| L3 Gold | SKILL.md、图存储、≥5 类查询 | 7 个技能、402 节点 702 边、11 类查询（演示 10 条） | 验收记录 §5 §8 |
| L4 Platinum | 增量、≥3 预警、周报、看板、部署文档 | 空库首跑 `new: 268` → 同库二跑 `new: 0`；7 条规则；周报 + 61KB 看板；`SETUP.md` + `docs/` | 验收记录 §6 §7 §9 |

---

## 五、三条我特意写在明处的「不」

1. **群消息不是真微信数据。** 本机 64 个微信 `.db`，抽样 20 个中 19 个是 SQLCipher 加密（文件头 `bc00 2ab8…`），
   密钥只在进程内存里。我没有去抽密钥——那要动整个微信的所有聊天。所以群消息用脱敏回放集，
   提交物用真实磁盘扫描。边界写在 `docs/数据说明.md`，`doctor` 命令每次都会打印这条限制。
2. **不会自动发消息。** `nudge` 只生成草稿到 `out/nudges.md`，第一行写着"复制粘贴到微信，自己看一遍再发"。
   一个会自动群发催交的工具，老师不敢用第二次。
3. **分类器不追到 95%。** 从 80.2% 改到 91.8% 后我主动停手：再改就是在拟合这 268 条别人看不到的标注。
   22 条错判的原文和类型都在 `out/metrics.json` 里，谁都能拿去挑。

---

## 六、复现（换台机器也能跑）

```bash
cd wechat-class-manager
python3 --version                 # 需要 3.10+
python3 -m wcm.cli doctor         # 环境自检（会告诉你微信库加没加密）
python3 -m wcm.cli selftest       # 62 个测试
python3 -m wcm.cli run --days 14 --fs ~/Desktop/挑战的产物 --owner JingXueQing
python3 -m wcm.cli query "C4B 还有谁没交"
```

没有 `~/Desktop/挑战的产物` 也能跑，只是提交矩阵变成只看群消息（44 → 30 项，脚本会打印提醒）。
零安装、零联网、零 CDN——`out/dashboard/index.html` 双击就开。

---

## 七、发群一句话介绍

> 把班级群接上 Agent：一条命令跑完 268 条消息 → 44 项提交矩阵 → 17 条预警 → 周报和看板，
> 十句自然语言问出"谁没交、谁沉默了、今天该催谁"，每条结论都能点到证据。零第三方依赖。
