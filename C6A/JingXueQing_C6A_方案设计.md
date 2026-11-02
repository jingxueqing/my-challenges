# C6A 方案设计：提交数据仪表盘

> 作者：JingXueQing ｜ 学号 2024102110351 ｜ 交付目录：`C6A-交付_JingXueQing_提交数据仪表盘/`
> 一句话：**把「散落的提交包」变成「一条可复跑的数据管线 + 一个点得开的仪表盘 + 一份对得上账的 Excel」。**

---

## 1. 问题定义：真正难的不是画图，是三个「对不上」

课程里有 20 个挑战、若干份提交包，文件散在不同目录。做仪表盘最容易走的路，是手工抄一张表再画几个图。我一开始就否掉了这条路，因为它会在三个地方对不上账：

| 问题 | 具体表现 | 本项目怎么解 |
|---|---|---|
| **归属对不上** | 有的包叫 `C1-交付_stanford-vibe-coding-zh`（没写姓名），有的文件名不按 `姓名_挑战_内容` 命名 | 文件名 → 父目录 → 提交包 → 人工补丁，四级归属，每条都记**判定方式** |
| **规格对不上** | 「该交什么」写在各挑战的 CHALLENGE.md 里，格式五花八门（表格、代码块、反引号清单） | 写正则解析 20 份官方文档，抽出 20 组规格；抽不到才用补丁，补丁必须写理由 |
| **证据对不上** | 交了 6 个文件，但其中 3 个互不相关，真正的「验证报告」没交 | 一个文件只算一个交付项（贪心最优分配），命中要给出**文件名 + 置信度** |

结论：**交付状态不是「有文件夹就算交」，而是「必填项逐条命中」**。这条口径决定了后面所有数字。

---

## 2. 权威数据源（口径的第一性问题）

| 数据 | 权威来源 | 说明 |
|---|---|---|
| 挑战清单与必填项 | `/Users/jingxueqing/Desktop/我的挑战/挑战_*/CHALLENGE.md`（20 份） | 机器抽取，可回溯到具体行号 `source_line` |
| 提交包与文件 | `/Users/jingxueqing/Desktop/挑战的产物/`（本人各挑战交付物）<br>`/Users/jingxueqing/Desktop/C6A-交付_JingXueQing_提交数据仪表盘/`（本包已移出交付目录，单独登记）<br>`…/C4A-…/真实评审输入/`（另两位提交者的真实 C4 包） | 只统计**本机磁盘上真实存在**的文件 |
| 质量分 | C4A 技能输出的 `评审结果.json` | 复用 C4 的真实评审结果，不重新打分 |
| 提交时间 | 提交包内文件的**最大修改时间** | 本地没有平台时间戳，属于近似口径，界面上明确标注「近似」 |

### 2.1 五条硬口径（写进代码、也写进界面「方法与口径」页）

1. **`❌` 不等于「未提交」**：本机没有该记录时显示「无记录」，而不是判学生没交。这是最容易误伤同学的坑。
2. **一个文件只满足一个交付项**：否则 `README_提交说明.md` 能同时冒充「说明文档」「截图」「教学说明」，完整度虚高。
3. **同名交付项只算一项**：同一挑战里「AI 日志 / AI 生成日志」这类同义条目会合并（相似度 ≥ 0.6 且槽位相同），避免重复计数。
4. **扫描深度 2 层 + 忽略工程目录**：`node_modules/.git/work/logs` 等不进统计；未计入的深层文件数量会在详情抽屉里如实显示。
5. **归属必须可追溯**：每条记录带 `attribution` 字段（`filename` / `parent_dir` / `folder_name` / `filename_vote` / `manual_patch`），人工补丁写在 `config.json` 的 `folder_owner_patches` 里并附 `reason`。

---

## 3. 架构：五层，层与层之间只靠 JSON 交接

```
┌──────────────────────────────────────────────────────────────┐
│ L1 规格层  specs.py                                          │
│    CHALLENGE.md ──正则抽取──▶ 交付项（label/pattern/slot）    │
│    归一化：AI日志 / AI协作日志 / AI 使用  →  同一槽位 ai_log  │
│    输出：data/specs.json（20 个挑战 / 带 source_line 可回溯） │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│ L2 采集层  pipeline.py                                       │
│    discover_packages → collect_candidates → attribute        │
│    排除嵌套提交包、限制深度、跳过工程目录                      │
└───────────────────────────┬──────────────────────────────────┘
                            │
┌───────────────────────────▼──────────────────────────────────┐
│ L3 匹配层  pipeline.py（score_match / match_items）           │
│    slug 精确 100 ▸ 去版本号同名 96 ▸ 前缀 92 ▸ glob 85 ▸ 槽位 60│
│    贪心分配：一个文件只落一个交付项；未命中即 missing          │
│    质量检查：命名合规率 / AI日志体量 / 空文件 / 版本噪声        │
└───────────────────────────┬──────────────────────────────────┘
                            │
        ┌───────────────────┼────────────────────┐
        ▼                   ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌────────────────────┐
│ L4 产出层      │   │               │   │                    │
│ submissions   │   │ make_excel.py │   │ make_site.py       │
│ .json + 4 CSV │   │ 6 Sheet xlsx  │   │ 单文件静态站点     │
│ （唯一事实源） │   │ 条件格式+图表 │   │ 内嵌 JSON，零依赖  │
└───────┬───────┘   └───────────────┘   └────────────────────┘
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│ L5 通知层  digest.py：日报 Markdown + 可直接发群的短消息       │
└──────────────────────────────────────────────────────────────┘
```

**为什么坚持「JSON 是唯一事实源」**：Excel 和网站都从同一份 `submissions.json` 生成，所以两边的「完整度」永远一致；不会出现「网页 84%、Excel 85%」这种自相矛盾。

---

## 4. 数据模型

### 4.1 挑战规格（`specs.json`）

```jsonc
"C6A": {
  "challenge_id": "C6A",
  "title": "提交数据仪表盘",
  "origin": "auto_extracted",          // auto_extracted | auto_extracted+patch | patch_only
  "source_file": "…/挑战_C6A 提交数据仪表盘_w43gy7_完整资料/CHALLENGE.md",
  "items": [
    {
      "label": "方案设计",              // 展示名（已清洗：去扩展名、去占位符）
      "desc": "架构、技术选型、数据模型设计",
      "pattern": "姓名_C6A_方案设计.md", // 官方原始写法，保留证据
      "match_type": "slug",             // slug | glob
      "slug": "方案设计.md",            // 用于精确匹配的「挑战编号之后的部分」
      "slot": "design",                 // 归一化槽位（跨挑战通用）
      "slot_cn": "方案设计",
      "required": true,
      "source_line": 252                // 可回溯到 CHALLENGE.md 第 252 行
    }
  ]
}
```

### 4.2 提交记录（`submissions.json → records[]`）

```jsonc
{
  "student": "JingXueQing",
  "challenge_id": "C4C",
  "challenge_title": "作业自动求解与排版",
  "submitted_at": "2026-10-07T15:57:40+08:00",   // = 包内文件最大 mtime
  "n_files": 14,
  "packages": ["C4C-交付_JingXueQing_作业自动求解与排版"],
  "duplicate_package": false,
  "status": "complete",                          // complete | partial | missing
  "completeness": 1.0,                           // 必填项命中率
  "items": [
    { "label": "方案设计文档", "slot": "design", "required": true,
      "present": true, "file": "JingXueQing_C4C_方案设计.md",
      "confidence": 100, "origin": "challenge_doc" }
  ],
  "missing": [],
  "quality": { "naming_compliance": 1.0, "ai_log_ok": true,
               "ai_log_size": 24576, "version_files": [], "empty_files": [] },
  "files": [ { "rel_path": "…", "is_dir": false, "size": 5120,
               "category": "方案设计", "matched_item": "方案设计文档" } ],
  "review": null                                  // C4 记录会挂 C4A 评审分
}
```

### 4.3 为什么要有 `slot`（这是能复用到下一期的关键）

各挑战对同一件事的叫法都不一样：C1 叫「`*AI日志*`」、C2A 叫「AI日志」、C5 内部又写「`AI_LOG.md`」。如果按字符串比，每加一门课就要改代码。

`slot` 把「叫什么」和「属于哪类」分开：**20 个挑战共享一张 20 条槽位表**（readme / ai_log / aar / attribution / design / teaching / validation / skill_pkg / screenshots / demo / data / dashboard / excel / output / article / paper / bib / extra …）。新增挑战 → 只要 CHALLENGE.md 按规范写，`specs.py` 自动抽规格、自动落槽位，**不改一行代码**。

---

## 5. 技术选型与理由

| 选择 | 理由 | 被淘汰的方案 |
|---|---|---|
| Python 标准库 + openpyxl | 环境自带、无网络依赖、脚本可读可改 | pandas（本轮数据量 264 文件，过重）；pandas 还要额外装 |
| 原生 HTML/CSS/JS 单文件站点 | `file://` 双击即开，离线、零依赖、给老师发过去就能看 | React/Vite（要 build）、Streamlit（要装环境+起服务）、Tailwind CDN（断网白屏） |
| 数据内嵌 `<script type="application/json">` | `file://` 下 `fetch('data.json')` 会被 CORS 拦，内嵌才真的「双击可开」 | 外部 JSON + fetch（本地打开必挂） |
| CSV 同时产出 | Excel 打不开时的兜底，也方便丢进任何 BI 工具 | 只给 xlsx |
| 惰性渲染（原生 DOM 字符串） | 20 人 × 20 挑战规模下，框架是负担 | Vue/React 运行时 |

---

## 6. 关键实现细节（踩过的坑都在这）

### 6.1 规格抽取：三个必须防的「串味」

| 坑 | 现象 | 处理 |
|---|---|---|
| 章节串味 | C4 的文档里还有「附件：两个示例 .skill」表，被误当成必填项 | 只在标题含「交付物 / 需要提交 / 必须提交」的章节内抓取 |
| 挑战串味 | `挑战_C2A` 的文档里嵌了一整段 C9 的交付清单 | 抽到的 pattern 里若含 `_C9_` 而当前是 C2A，直接丢弃 |
| 同义重复 | 表格里「AI 日志」+ 命名清单里「YourName_C4_AI日志.md」 | 同槽位 + 标签相似度 ≥ 0.6 合并；优先保留带 `姓名_` 的那条 |

### 6.2 归属：四级判定与人工补丁

```
① 文件名  JingXueQing_C4C_方案设计.md       → JingXueQing / C4C   （最可信）
② 父目录  …/Elite20TA_C4_skill-explainer/…  → Elite20TA   / C4
③ 提交包  C2-交付_JingXueQing_AI4Math论文     → JingXueQing / C2   （包名带姓名）
④ 补丁    C1-交付_stanford-vibe-coding-zh     → JingXueQing / C1   （包名无姓名，写明理由）
```

第 ④ 类共 2 条，写在 `config.json` 的 `folder_owner_patches`，每条带 `reason`；界面上这条记录的「提交包」一栏能看到来源。

### 6.3 嵌套提交包去重

`C4A-交付_…_另版含真实评审输入/` 里放着一份 `真实评审输入/`，里面是**别人的**提交包。如果不处理，同一个人会被算两遍、别人的文件会被算到本人头上（第一版就是这么错的，见 AI 日志第 3 轮）。处理方式：`真实评审输入` 进忽略列表，由独立根目录单独扫描。

### 6.4 状态与完整度的定义

```
必填项命中集合 P，必填项总数 N
completeness = |P| / N
status = complete  (|P| == N)
       | partial   (0 < |P| < N)
       | missing   （该 (学生,挑战) 在本机没有任何文件 → 不生成记录，矩阵里显示 ❌ 无记录）
```

`run.py check` 会反过来验算：状态、完整度、文件-规格映射三者必须自洽，否则退出码非 0。

---

## 7. 交付物与目录

```
C6A-交付_JingXueQing_提交数据仪表盘/
├── README_提交说明.md                  ← 交付物对照表 / 复现命令 / 发群文案
├── JingXueQing_C6A_方案设计.md          ← 本文
├── JingXueQing_C6A_教学说明.md          ← 装、跑、更新数据、扩课程
├── JingXueQing_C6A_AAR.md               ← 复盘（含失败清单）
├── JingXueQing_C6A_AI日志.md            ← 8 轮真实迭代记录
├── JingXueQing_C6A_拿来说明.md          ← 用了哪些库/工具/Agent
├── JingXueQing_C6A_report.xlsx          ← 6 个 Sheet，条件格式 + 柱状图
├── JingXueQing_C6A_数据/                ← 结构化数据（唯一事实源 + 4 份 CSV + 日报）
│   ├── submissions.json
│   ├── specs.json / matrix.csv / records.csv / files.csv / challenge_stats.csv
│   └── 报告/每日摘要_*.md、群里通知_*.txt
├── JingXueQing_C6A_仪表盘/           ← 网站（index.html + assets + data.json）
├── JingXueQing_C6A_screenshots/         ← 6 张运行截图
└── JingXueQing_C6A_pipeline/            ← 全部脚本（specs/pipeline/make_excel/make_site/digest/run）
```

---

## 8. 已知局限与下一步

| 局限 | 影响 | 下一步 |
|---|---|---|
| 只有 3 位提交者的本机数据 | 覆盖率 27%，不能代表全班 | 把群文件批量下载到 `数据根`，跑 `python3 run.py all` 即可，不改代码 |
| 提交时间取文件 mtime | 复制/解压会刷新时间，可能偏晚 | 接 EduSeed 平台提交时间字段（`challenge.json` 已有 deadline 结构可扩展） |
| 归属靠命名 + 补丁 | 完全乱命名的包需要人工补 | 用 LLM 读包内 `README/方案设计` 首段自动推断姓名（下一步） |
| 不判断内容质量 | 「交了」≠「交得好」 | 已预留 `review` 字段（C4 已接 C4A 评审分），全部挑战接评审器即可出总分 |
| 只扫 2 层目录 | 深层文件不计入 | 已在详情里显示「另有 N 个深层文件未计入」，可按挑战白名单放开 |

**可复用性结论**：本期 → 下期的迁移成本 = 改 `config.json` 里的两个路径 + 保证新挑战的 CHALLENGE.md 按既有格式写。规格、匹配、Excel、网站、日报全部自动。
