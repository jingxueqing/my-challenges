# AI 协作日志（AI Usage Log）

> 挑战 C1：课程资料获取与翻译 ｜ 周期：4 个工作日（D1–D4）
> 每日记录：用了什么工具 → 关键 prompt → 踩了什么坑 → 怎么解决。所有 prompt 均为当日实际使用版本（节选）。

---

## D1：资料定位与离线包分析

**工具**：WorkBuddy（AI 助手）+ Bash + Read

**做了什么**：解压 `CS46S_offline.zip`（应为 CS146S），梳理目录：`pages/`（31 篇 HTML）、`pdfs/`（3 份）、`page_map.json`（31 条 URL 映射）、`all_urls.txt`。通读离线包自带 README，确认 5 类联网资源缺口（YouTube/Slides/Drive/GitHub/Medium）。

**关键 prompt**：
> "阅读离线包 README 与 page_map.json，列出哪些阅读材料是课程方撰写的、哪些是外部文章，并标注哪些页面可能是 JS 渲染导致正文抓不出来的。"

**坑与修复**：
- 坑 1：`pages/how-warp-uses-warp.html`（Notion）、`good-context-good-code.html`（Ghost）、`prompt-engineering-guide.html`（SPA）虽然文件存在，但正文是 JS 渲染的，离线包里只有外壳。
  - 解决：写了个"长行统计"小脚本逐页探测（正文中 >40 字符的行数），确认 3 篇正文缺失 + 2 篇占位页（`peeking-under-the-hood-of-claude-code.html` 550 字节、`lessons-from-ai-code-reviews.html` 0 字节）。决策：不硬抓，登记缺口台账。
- 坑 2：离线包 README 写的"31 pages"与实际可读正文 29 页对不上，差点按 31 做覆盖度分母。以 manifest 实际数据为准。

---

## D2：管线搭建（提取 → 翻译 → 质检）

**工具**：WorkBuddy（AI 助手）+ Python 3.13 + beautifulsoup4/lxml/pdfminer

**做了什么**：三个课程无关的脚本 + 一个总入口：
- `extract_text.py`：噪声标签剔除 → 逐级正文容器选择器（article/main/[role=main]/.post-content/…/body）→ 轻量 DOM→Markdown（标题/列表/代码块/表格/引用）→ 输出语料 + manifest.json；
- `translate.py`：段落聚合分块（~1200 词/块）、术语表注入 prompt、译后术语强制校验与自动重试、双引擎（api/skeleton）；
- `check_quality.py`：覆盖度、字符比健康区间、TODO/过短占位、术语漏统一扫描，产出 JSON 报告；
- `run_all.sh`：extract / translate / check 三段式入口，`COURSE`/`GLOSSARY`/`ENGINE` 全部环境变量化。

**关键 prompt（脚手架部分，完整版见 拿来说明/01）**：
> "写一个课程无关的 HTML 正文提取脚本：不依赖具体网站结构，用候选选择器列表逐级回退；输出 Markdown 语料和一个 manifest.json（含 URL、字符数、占位页标记），供后续翻译与覆盖度统计使用。"

**坑与修复**：
- 坑 3：术语表 CSV 用 Write 工具生成后带 UTF-8 BOM，`csv.DictReader` 读出的第一列键变成 `\ufeffen`，`KeyError: 'en'`。
  - 解决：读文件改用 `encoding="utf-8-sig"`（translate.py 与 check_quality.py 同步修）。
- 坑 4：`manifest.json` 里占位页条目没有 `slug` 字段（当时只在非占位分支写了），质检脚本 `KeyError: 'slug'`。
  - 解决：`m.get("slug") or Path(m["file"]).stem` 兜底，并顺带给占位页补了 `GAP` 状态。
- 坑 5：venv 里 `pip install` 卡了 9 分钟（网络慢），一度以为死锁。以后安装类命令一律后台跑 + 等通知，不要前台干等。

---

## D3：批量翻译（并行子代理 + 术语约束）

**工具**：WorkBuddy 并行子代理 ×11 批 + 术语表 glossary.csv（82 条）

**做了什么**：按文件大小分批（小文 8 篇/批、中长文 2–3 篇/批、超长文单独 1 批），11 个翻译任务并行推进。每个任务注入同一份翻译规则块（术语表精简版 + 结构保持规则 + front matter 规范 + 产品名不译清单），保证跨批次一致性。

**关键 prompt（批次任务模板，节选）**：
> "你是专业技术课程翻译译者。逐段忠实翻译以下 Markdown（不总结、不删减）。术语必须遵守：Vibe Coding→氛围编程；Context Engineering→上下文工程；Context Rot→上下文腐烂；code review→代码评审；SAST→静态应用安全测试（SAST）……产品名不译（Claude Code、Warp、Kubernetes……）。保持 Markdown 结构与代码块，输出文件名为 <slug>.zh.md，保留并双语化 front matter。完成后逐篇报告字符数。"

**长文决策 prompt（完整迭代对比见 拿来说明/03）**：
> v1（被否）："把这篇 5 万字符的研究报告全文翻译为中文。"
> v2（采纳）："对这篇长文做'详注节译'：保留全部章节标题并译出，每节 3–6 句中文详述；凡含关键定义、数字、结论的句子必须全文翻译；摘要与结论全译；文首标注节译版。"

**坑与修复**：
- 坑 6：术语漂移——不同批次对 CI/CD、Embedding 的处理不一致（有的译"持续集成/持续交付"，有的保留 CI/CD；有的"向量表示"有的"嵌入"）。这正是多智能体批量翻译的最大风险。
  - 解决：a) 在批次模板里附术语表精简版而不是"见文件"；b) 质检脚本做了"术语漏统一"扫描，对 4 处违规点逐一定位后统一修正（CI/CD 首次出现补全称、Embedding 全文统一为"嵌入"）；c) 把 Embedding 词条的推荐译法本身改成与实际语料一致的"嵌入"——术语表服务语料，而不是相反。
- 坑 7：PDF 提取文本断行严重（每行 60 字符左右，还有页眉页脚噪声），直接喂给翻译会产生破碎译文。
  - 解决：给 PDF 批次的 prompt 加了一条"先按语义重组段落、去页眉页脚，再翻译"；SRE 引言、Codex、Anthropic 三份 PDF 译文质量因此明显好转（对比留档见 拿来说明/03 附录）。
- 坑 8：某批次的子代理把课程名打成"CS46S"（离线包 README 里的笔误传染），发现后统一回查修正。教训：**原文里的笔误要专门校对**，不能全信。

---

## D4：质检、抽检与发布

**工具**：`check_quality.py` + 人工抽检 + WorkBuddy

**做了什么**：
- 跑质检：覆盖度 29/31 = 93.5%（分母 31 = 29 篇正文 + 2 篇占位页；5 篇 JS 缺口单列台账）；术语 82 条、违规 0；TODO/过短 0。
- 人工抽检 6 篇（prompt-engineering-overview、mcp-introduction、sast-vs-dast、context-rot、how-openai-uses-codex、课程主页）：对照原文抽查首/中/尾各 2 段，重点看术语、数字、结构。发现并修复的问题：CI/CD 译名不一（见坑 6）、context-rot 中"大海捞针测试"一处误作"草堆寻针"。
- 写 README（覆盖范围、缺口台账、复跑指南）、AAR、3 个"拿来说明"。

**关键 prompt（抽检）**：
> "对照 corpus/en/context-rot.md 与 course-zh/context-rot.zh.md，只检查三类硬伤：1) 数字/百分比是否与原文一致；2) 术语是否遵守术语表；3) 是否存在成段漏译。逐条列出位置，不要重写译文。"

**坑与修复**：
- 坑 9：覆盖度一度算成 26/31（漏把 3 篇 JS 缺口页的"概览补译/缺口台账"计入口径），和 README 描述打架。
  - 解决：明确双口径——"篇数覆盖 100%（含台账）"与"正文全译通过质检 93.5%"，README 里两个数都写，机器版以 quality_report.json 为准。
- 坑 10：生成"缺口占位译文"时用了 heredoc，反引号嵌套差点把补跑命令吞掉，改用转义 `\``后才正确落盘。教训：AI 生成 shell 模板时，含代码反引号的字符串要格外小心。

---

## 效率小账

| 环节 | 用 AI 的方式 | 效果 |
|---|---|---|
| 离线包体检 | AI 写探测脚本 + 逐页诊断 | 5 分钟锁定 5 处抓取缺口 |
| 管线三脚本 | AI 起草 + 我提课程无关性约束 | 一次成稿，只修了 2 个 bug |
| 31+3 篇翻译 | 11 批并行子代理 + 统一术语块 | 数小时级并行完成，术语违规 4 处后清零 |
| 质检与抽检 | 脚本全量扫 + AI 对照抽检 | 双口径覆盖度报告，数字可复核 |

---

## D5（交付后收口）：缺口补抓

**做了什么**：对 5 处抓取缺口逐一联网补抓尝试——Graphite 讲稿（成功，自 AIE Talks 拿到全文+完整时间戳转录，全译 4329 字符）；promptingguide 总览页（成功，官方 18 条技巧全译，并据此修正了此前凭印象写的附录清单）；Notion/Ghost/Medium 三处失败（Notion 仍返回壳页、stockapp 站点不可达、Medium 直连/jina/freedium 三途径全拦截）。

**发现**：`Vibe_Coding_Playbook.pdf` 为图像型 PDF（文本层仅 14 字符），需 OCR 后才能进管线——已记入缺口台账。

**坑与修复**：
- 坑 11：补抓回来的 promptingguide 官方清单与我此前凭训练记忆写的附录清单不一致（初版混入了 MRKL、链式验证等不在官方总览的条目，且漏了 Meta Prompting、Reflexion 等 6 条）。已用官方抓取版替换，并在附录中注明修正。教训：**可抓到原文时，永远以抓取结果为准，不要让 AI 凭记忆"复原"清单类内容**。
- 覆盖度从 93.5% 提升到 96.8%（30/31）后复核：how-warp-uses-warp、good-context-good-code 两篇正文实为仅存外壳页（原误判为全译），口径更正为 **90.3%（28/31）**，术语一致性保持违规 0。
