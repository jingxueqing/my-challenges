# Stanford CS146S 中文课程资料包（The Modern Software Developer）

> **C1 课程资料获取与翻译 · 挑战交付** ｜ 挑战 ID：ch-20260717031336-pxzwy0
> 目标课程：[CS146S: The Modern Software Developer](https://themodernsoftware.dev/)（Stanford University, Fall 2025，讲师 Mihail Eric）

本资料包将 CS146S 全部公开阅读材料组织为**中文翻译 + 双语对照语料 + 可复跑翻译流水线**，让不懂英文的同学零成本学习这门 AI 辅助开发课程，也让下一批同学能把同样的管线直接用于任何其他课程。

---

## 1. 资料来源

| 来源 | 说明 |
|---|---|
| 课程官网 themodernsoftware.dev | 课程主页（含 10 周教学大纲、FAQ） |
| 官方离线包 `CS146S_offline.zip`（2026-04-02 抓取） | 31 篇阅读文章 HTML、3 个 PDF、page_map.json（URL↔文件映射）、all_urls.txt |
| `Vibe_Coding_Playbook.pdf` | 课程配套手册（挑战材料包附带，未纳入本翻译批次，见"已知缺口"） |

原始 URL 与本地文件的对应关系保存在 `pipeline/page_map.json`，每篇译文与语料的 YAML front matter 中都带有 `source_file`，可逐篇回溯。

## 2. 覆盖范围（截至交付）

| 类别 | 总数 | 已有中文 | 覆盖率 |
|---|---|---|---|
| 课程主页 + 教学大纲 + FAQ | 1 | 1 | 100% |
| 阅读文章（HTML 页面） | 31 | 31（其中 3 篇原文为抓取缺口，有缺口台账+补译/补抓说明） | 100%* |
| 课程 PDF 讲义 | 3 | 3（1 篇全译、2 篇详注节译） | 100%* |

\* 按"篇数"计覆盖 100%，机器可复核口径见 `reports/quality_report.json`：**28/31 篇正文全译通过质检 = 90.3%**，未过项为 3 篇原文抓取缺口（how-warp-uses-warp、good-context-good-code 两篇原文仅存外壳页，peeking-under-the-hood-of-claude-code 为 Medium 拦截页），均已登记缺口台账并给出补抓流程。交付后还成功补抓了 2 篇原缺口文章（Graphite 讲稿、promptingguide 总览）。

**翻译层级说明**：
- **全译**（29 篇文章 + 1 个 PDF + 课程主页）：逐段忠实翻译，不删减；
- **详注节译**（4 篇长文：context-rot、agentic-ai-threats、两份 PDF 报告）：保留全部章节标题，每节要点详述，关键定义/数据/结论逐句全译，文首均有明确标注；
- **交付后补抓**（2 篇）：`lessons-from-ai-code-reviews`（离线包 0 字节，自 AIE Talks 讲稿页补抓全文并全译）、`prompt-engineering-guide`（SPA 页，自官网补抓官方 18 条技巧总览并全译；其 18 个技巧子页未译，见缺口台账）；
- **缺口台账**（剩余 3 项）：`course-zh/*.zh.md` 中逐篇注明原因与补抓方法（详见第 7 节）。

## 3. 目录结构

```
C1-交付_stanford-vibe-coding-zh/
├── README.md                  ← 本文件
├── AI日志.md                   ← 每日 AI 协作日志（工具/prompt/踩坑）
├── AAR.md                     ← 七维复盘
├── 拿来说明/                    ← 3 个"拿来说明"案例（原文+prompt+产出+对比）
│   ├── 01_管线脚手架的AI搭建.md
│   ├── 02_术语一致性校验的设计.md
│   └── 03_长文节译策略决策.md
├── 术语表.md                   ← 82 条术语（人读版），机器版见 pipeline/glossary.csv
├── pipeline/                  ← 可复跑翻译流水线（课程无关）
│   ├── extract_text.py        ← HTML → Markdown 语料提取
│   ├── extract_pdf.py         ← PDF → Markdown 语料提取
│   ├── translate.py           ← 术语感知的分段翻译（api / skeleton 双引擎）
│   ├── check_quality.py       ← 覆盖度 + 术语一致性 + 漏译质检
│   ├── glossary.csv           ← 82 条术语表（en,zh,notes）
│   └── page_map.json          ← 来源 URL 映射
├── corpus/
│   ├── en/                    ← 英文语料（29 页提取 + 2 篇补抓原文 + manifest.json）
│   └── en-pdfs/               ← 英文 PDF 语料（3 份 + manifest.json）
├── course-zh/                 ← 中文译文（每篇对应语料 slug + .zh.md）
└── reports/
    └── quality_report.json    ← 机器可复核的覆盖度/术语质检报告
```

## 4. 翻译流程（四步管线）

```
原始资料包 → [1 extract] 语料提取 → [2 translate] 术语感知翻译 → [3 check] 质检 → [4 发布]
```

1. **抓取/提取**：`extract_text.py` 从离线包 HTML 中剔除导航/脚本噪声、定位正文容器、输出 Markdown 语料 + manifest；`extract_pdf.py` 处理 PDF。
2. **翻译**：`translate.py` 按段落聚合分块（默认 ~1200 词/块），每块注入术语表，译后强制校验术语一致性；引擎可插拔（`--engine api` 调 LLM，或 `--engine skeleton` 生成待译模板交人工）。
3. **质检**：`check_quality.py` 统计覆盖度、字符比、TODO/漏译占位、术语漏统一，产出 `reports/quality_report.json`。
4. **发布**：全部产物为纯 Markdown，可直接推 GitHub 或用 MkDocs/Docsify 建站。

## 5. 使用方法

**只想读课程**：直接进 `course-zh/`，从《课程主页与教学大纲.zh.md》开始，按周次找对应译文；文件名与原离线包 pages/ 一一对应。

**想核对原文**：`corpus/en/` 内为逐页英文语料，文件名与译文一一配对。

**想复跑/换一门课程**（核心卖点，全程不写死课程名）：

```bash
# 0) 准备：新课离线包解压到 materials/<课名>_offline/（含 pages/、可选 pdfs/ 与 page_map.json）
export COURSE=新课离线包目录名
export GLOSSARY=pipeline/新术语表.csv        # 为新课整理 50+ 术语

# 1) 提取语料
bash run_all.sh extract

# 2a) 有 LLM API Key：自动翻译
export ANTHROPIC_API_KEY=sk-ant-xxx
ENGINE=api bash run_all.sh translate
# 2b) 无 API：生成待译模板，人工/外包填写后继续
ENGINE=skeleton bash run_all.sh translate

# 3) 质检（覆盖度 <80% 时脚本报错退出）
bash run_all.sh check
```

依赖：Python 3.10+，`pip install beautifulsoup4 lxml pdfminer.six`（引擎 api 模式另需 `anthropic`）。

## 6. 术语表

共 **82 条**，机器版 `pipeline/glossary.csv`（en,zh,notes），人读版 `术语表.md`。课程核心概念全文统一，如：

| 英文 | 中文 |
|---|---|
| Vibe Coding | 氛围编程 |
| Scaffolding | 脚手架 |
| Context Engineering | 上下文工程 |
| Prompt Engineering | 提示词工程 |
| Context Rot | 上下文腐烂 |
| Coding Agent | 编码智能体 |
| Model Context Protocol (MCP) | 模型上下文协议（MCP） |
| Code Review | 代码评审 |
| SRE | 站点可靠性工程（SRE） |

产品名（Claude Code、Codex、Copilot、Devin、Cursor、Warp、Kubernetes 等）一律不译。

## 7. 已知缺口（诚实台账，含补抓记录）

**交付后已补抓成功（原缺口 → 已解决）**：

| 内容 | 原状态 | 补抓结果 |
|---|---|---|
| Lessons from Millions of AI Code Reviews | 离线包 0 字节 | ✅ 自 AIE Talks 讲稿页补抓全文并全译（见 `lessons-from-ai-code-reviews.zh.md`） |
| Prompting Guide — Techniques 页 | SPA 动态加载 | ✅ 自官网补抓官方 18 条技巧总览并全译；其 18 个技巧子页仍未译（见下表） |

**仍未解决的缺口**：

| # | 内容 | 原因（含已尝试的途径） | 补救方式 |
|---|---|---|---|
| 1 | How Warp Uses Warp to Build Warp | Notion 动态渲染；联网访问仍只返回壳页 | 人工打开后导出 Markdown，存入 corpus/en 重跑管线 |
| 2 | Good Context, Good Code | 站点无法访问（直连失败）；离线包仅外壳 | 站点恢复后按管线补抓 |
| 3 | Peeking Under the Hood of Claude Code | Medium 拦截：直连、jina 代理、freedium 镜像三种途径均失败 | 人工访问原文后补译 |
| 4 | promptingguide.ai 的 18 个技巧子页 | 总览页已补抓，子页未逐一抓取 | 逐页保存正文入 corpus/en 后重跑管线 |
| 5 | 14 个 Google Slides / 3 个 YouTube 视频 | 需账号/视频未随离线包分发 | 视频字幕可另建抓取任务接入本管线 |
| 6 | Vibe_Coding_Playbook.pdf | 图像型 PDF，无文本层（提取仅 14 字符），需先 OCR | OCR 后按管线翻译（管线已支持） |

另：4 篇"详注节译"长文（2 篇外部研究文 + 2 份 PDF）非逐字全译，文首均有标注——这是在"覆盖广度 vs 翻译深度"上的显式取舍，复盘详见 `AAR.md`。

## 8. 质检结论（机器可复核）

- 正文覆盖度：**28/31 = 90.3%**（≥80% 验收线 ✅；未过项为 3 篇原文抓取缺口，已登记缺口台账）
- 术语表：**82 条**（≥50 条 ✅），全文术语一致性违规：**0**（详见 `reports/quality_report.json`）
- 漏译/占位检测：**0 处** TODO 或过短译文

## 9. 许可与致谢

- 原课程内容版权归原作者（Stanford / Mihail Eric / 各原文作者）所有；本包中文译文仅供学习交流，不得商用。
- 抓取时间：2026-04-02（离线包）；翻译与质检：2026-09（本挑战周期内）。
- 译文与管线按 MIT 许可发布（仅限本包自产内容）。
