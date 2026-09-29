# AI4Math 论文 AI 协作日志

> 项目：Challenge C2 — AI for Math 论文  
> 实际执行日期：2026-09-29  
> 记录原则：本项目在一个自然日内集中完成。为避免伪造“连续五日”经历，以下以 D1–D5 表示五个研究阶段，而非虚构的五个日期。每一阶段均保留 AI 输入、产出、核验动作、修订决定与待人工签核项。

## 1. 角色与边界

- **AI 负责**：需求抽取、资料初筛、文献元数据检索、框架备选、结构草拟、LaTeX 排版、编译检查与错误修复建议。
- **研究者负责**：决定研究问题与结论边界；核对一手来源；判断自然语言命题与形式化/结构化表示是否等价；投稿前逐条终审并承担署名责任。
- **明确未做**：未运行或训练任何数学推理模型；未把跨论文数字拼接成新实验；未声称获得了未实际执行的性能提升。

## 2. 分阶段协作记录

### D1 — 需求拆解与红线确认（2026-09-29）

**输入材料**

- `challenge.json`、`challenge.yaml`、`CHALLENGE.md`、`README.md`、`rubric.json`
- `中文论文大纲（AI4Math）.pdf`
- `Lectures on AI for Mathematics.pdf`

**给 AI 的任务摘要**

> 提取必交文件、评分维度、红线、建议论文结构；区分“必须满足”与“可选增强”，不要开始编造实验结果。

**AI 初稿结论**

1. 必须交付 `paper.tex`、`references.bib`、AI 日志、七维 AAR。
2. 论文必须含摘要、引言、相关工作、方法/框架、分析、结论和参考文献。
3. 两条红线是引用造假与不可编译；AI 日志需要体现迭代与核验。
4. 材料建议把“语义规约层”作为生成与验证之间的关键瓶颈。

**核验动作**

- 逐项对照 `CHALLENGE.md` 第 20–46 行与 `rubric.json` 的 5 个评分维度。
- 对两份 PDF 进行文本抽取，确认大纲确实提出 Generation → Semantic Reduction → Verification 三层结构；讲义第 4 章讨论形式化内核、搜索、强化学习和复现成本。

**决定**

- 采用“语义规约瓶颈”作为理论起点，但不照搬三层大纲；扩展为覆盖数据与复现的五门框架。
- 论文定位为“框架 + 结构化证据综合”，不伪装成新模型实验论文。

---

### D2 — 文献检索与元数据核验（2026-09-29）

**提示迭代**

- 版本 1：查找 AI4Math 可靠性相关论文。
- 版本 2：按“搜索/验证、形式化/自动形式化、基准/复现”三组检索，逐篇返回 DOI 或 arXiv ID；不确定字段必须标注未知。
- 版本 3：优先出版商、ACL Anthology、OpenReview、NeurIPS 官方页、Crossref 与 arXiv；禁止用二手博客补全书目信息。

**纳入的一手研究（19 篇进入正文引用）**

- 搜索与验证：Cobbe et al. 2021；Uesato et al. 2022；Lightman et al. 2024；Wang et al. 2024。
- 基准与能力：Hendrycks et al. 2021；Lewkowycz et al. 2022；He et al. 2024；Glazer et al. 2024。
- 形式化基础与系统：Lean 4、mathlib、miniF2F、Autoformalization、Draft/Sketch/Prove、ProofNet、LeanDojo、Peano。
- 神经符号案例：AlphaGeometry、FunSearch、AlphaProof。

**核验规则**

1. 有 DOI：用 Crossref/出版商元数据核对题名、卷期、页码与年份。
2. 无 DOI 的会议论文：用 OpenReview 或会议官方论文集核对题名、作者与年份。
3. 仅预印本：只填写 arXiv ID，不虚构会议、页码或 DOI。
4. 论文支持范围在正文中显式限界，例如 GSM8K 结果不外推到自然语言证明，形式内核不外推到语义等价。

**发现的 AI 误导案例（已纠正）**

- AI 文献核验草稿把 AlphaProof 条目写成“Nature 2025, 651(8106):607–613”，原因是 DOI 中含 `-025-` 且论文曾于 2025 年在线公开。
- 进一步查询 Crossref 记录发现：该文印刷卷期为 **Nature 651(8106), 607–613，published-print: 2026-03-19**；因此 `references.bib` 使用 `year = {2026}`，并在 `note` 中保留“online 2025 / print 2026”的差异。
- 对策：年份、卷期、页码不得从 DOI 字符串或搜索摘要推断；必须以 Crossref/出版商的 `published-print` 与 `journal-issue` 字段为准。

---

### D3 — 框架构建与反例压力测试（2026-09-29）

**给 AI 的任务摘要**

> 在“搜索 + 验证、形式化证明、可复现评估”之外，提出一个能定位错误发生层级的原创框架。框架必须说明：形式证明为什么仍可能回答错问题，以及什么时候系统应拒答。

**候选方案**

1. 三层方案：生成—语义规约—验证。优点是简洁；缺点是遗漏数据污染和实验复现。
2. 四层方案：生成—规约—验证—复现。缺点是任务定义与训练/测试数据来源无独立位置。
3. 五门方案 TRACE：Task/Data Traceability、Reasoning Search、semantic Alignment、Certification、Evaluation Replay。

**压力测试问题**

- 如果 Lean 接受了证明，但自动形式化漏掉 `x \neq 0`，框架能否识别？——由 A 门拦截。
- 如果 best-of-256 找到高分错误轨迹，框架能否识别？——R 门不能单独授予“已证明”标签，需 C 门。
- 如果公开基准被预训练污染，框架能否识别？——T 门要求污染风险声明。
- 如果同一证明在新版 mathlib 失败，框架能否识别？——E 门要求锁定版本并重放。

**决定**

- 采用 TRACE 五门，并把每门视为“发布门控”，而不是可以互相补偿的加权分数。
- 用可靠性向量代替单一总分，防止高平均分掩盖语义对齐为零。
- 加入基于 Boole 不等式的保守残余风险上界，但明确：没有经验估计的 `epsilon_i` 不能被包装成概率证书。

---

### D4 — 写作、证据对齐与 LaTeX 实现（2026-09-29）

**给 AI 的任务摘要**

> 形成完整学术论文；每个强结论必须有一手来源或被明确标注为本文提出；不编造模型实验；加入图、表、公式、局限和 AI 使用声明。

**结构迭代**

- 初版：引言 → 相关工作 → 三层框架 → 结论。
- 修订：增加概念界定、文献选择方法、TRACE 五门、错误上界、跨研究机制编码、复现实验协议、讨论、效度威胁、可靠性卡和附录清单。

**关键结论—证据映射**

| 编号 | 论文中的结论 | 证据/推导 | 核验结果 |
|---|---|---|---|
| C01 | 最终答案正确不保证过程正确 | Uesato 2022；Lightman 2024 | 一手论文支持，保留任务范围限制 |
| C02 | best-of-N 依赖验证器而非自动成为真值搜索 | Cobbe 2021；本文逻辑分析 | 论文机制支持；“非真值判定”标为本文分析 |
| C03 | 形式内核保证相对于形式陈述的有效性 | Lean 4；mathlib | 一手系统论文支持；避免“绝对正确”措辞 |
| C04 | 自然语言到形式陈述的语义对齐是独立风险 | Autoformalization；ProofNet；AlphaGeometry | 多源交叉支持；“核心瓶颈”标为本文主张 |
| C05 | 公开复现与抗污染存在张力 | MATH；OlympiadBench；FrontierMath | 由数据公开策略差异推导，未声称定量因果 |
| C06 | 神经符号系统把生成与确定性检查分工 | FunSearch；AlphaGeometry；AlphaProof | 原论文机制支持，限定在各自任务域 |
| C07 | 五门错误可用并集界给出保守上界 | 本文命题，Boole 不等式 | 数学推导自洽；注明界可能很松 |

**人工核验接口**

- 论文已经给出可点击 DOI/官方 URL 与清晰的结论边界。
- 投稿前作者需逐条打开 19 篇引用并确认题名/作者；对 C04、C05 这类综合判断作最终语义签核。
- 由于当前交付由 AI 助手完成，不能虚构“作者本人已核验”的签名；签核栏保留在本日志末尾。

---

### D5 — 编译、引用与交付审计（2026-09-29）

**计划检查项**

- XeLaTeX → BibTeX → XeLaTeX ×2，全链路无致命错误。
- 检查未定义引用、未定义参考文献、Overfull/Underfull box 和缺失字体。
- 检查 `paper.tex`、`references.bib`、本日志、七维 AAR 与编译说明均非空。
- 记录最终 PDF 页数、文件哈希和编译器版本。

**结果**

- 使用 Tectonic 0.17.0（XeTeX 兼容引擎）执行完整的 TeX + BibTeX + 重跑流程，退出码为 0。
- 初次编译发现证据矩阵中的 Unicode 圆点符号缺少字形，以及表格轻微 overfull；将标记改为 `Y/P/--`、调整表格字号与列格式后重新编译。
- 最终日志中无未定义引用、未定义交叉引用、缺字、overfull/underfull 或 LaTeX 警告。
- 最终 PDF 为 12 页、478,423 字节，SHA-256：`61685c46215a3a139f66326e2a5a188d68bc174e281f775f61e02b62fd71f981`。
- BibTeX 库含 20 条条目，正文使用 19 个不同引用键，静态检查未发现缺失引用键。

## 3. AI 输出采用/拒绝清单

| AI 建议 | 处理 | 原因 |
|---|---|---|
| 使用三层生成—规约—验证框架 | 修改后采用 | 增加数据溯源与评估重放，形成 TRACE 五门 |
| 汇总公开论文中的准确率做横向排名 | 拒绝 | 模型、预算、数据与评分协议不一致，横比会误导 |
| 把形式验证描述为“绝对可靠” | 拒绝 | 只能相对于陈述、内核、公理与环境成立 |
| 给所有门加权得到单一可靠性分 | 拒绝 | 权重缺少可辩护依据，可能掩盖单门失效 |
| 用并集界描述残余风险 | 采用并加限制 | 数学上透明，但必须说明 `epsilon_i` 需实证估计 |
| 把 AlphaProof 的卷期年份记为 2025 | 拒绝并纠正 | Crossref 显示印刷卷期年份为 2026 |
| 编造一个新实验提升百分比 | 拒绝 | 本项目未运行模型，论文明确定位为框架与证据综合 |

## 4. 参考文献逐条核验摘要

| BibTeX key | 类型 | 主标识 | 核验渠道 | 状态 |
|---|---|---|---|---|
| cobbe2021verifiers | 预印本 | arXiv:2110.14168 | arXiv | 已核对 |
| uesato2022feedback | 预印本 | arXiv:2211.14275 | arXiv | 已核对 |
| lightman2024verify | ICLR 2024 | OpenReview v8L0pN6EOi | OpenReview | 已核对 |
| wang2024mathshepherd | ACL 2024 | 10.18653/v1/2024.acl-long.510 | ACL/Crossref | 已核对 |
| hendrycks2021math | NeurIPS D&B 2021 | 官方论文集页 | NeurIPS | 已核对 |
| zheng2022minif2f | ICLR 2022 | OpenReview 9ZPegFuFTFv | OpenReview | 已核对 |
| demoura2021lean4 | CADE 28 | 10.1007/978-3-030-79876-5_37 | Crossref/Springer | 已核对 |
| mathlib2020 | CPP 2020 | 10.1145/3372885.3373824 | Crossref/ACM | 已核对 |
| yang2023leandojo | NeurIPS 2023 | OpenReview g7OX2sOJtn | OpenReview | 已核对 |
| wu2022autoformalization | NeurIPS 2022 | OpenReview IUikebJ1Bf0 | OpenReview | 已核对 |
| jiang2023draft | ICLR 2023 | OpenReview SMa9EAovKMC | OpenReview | 已核对 |
| azerbayev2023proofnet | 预印本 | arXiv:2302.12433 | arXiv | 已核对 |
| trinh2024alphageometry | Nature 625 | 10.1038/s41586-023-06747-5 | Crossref/Nature | 已核对；存在作者勘误 |
| romeraparedes2024funsearch | Nature 625 | 10.1038/s41586-023-06924-6 | Crossref/Nature | 已核对 |
| lewkowycz2022minerva | NeurIPS 2022 | arXiv:2206.14858 | arXiv/NeurIPS | 已核对 |
| he2024olympiadbench | ACL 2024 | 10.18653/v1/2024.acl-long.211 | ACL/Crossref | 已核对 |
| glazer2024frontiermath | 预印本 | arXiv:2411.04872 | arXiv | 已核对；持续更新基准 |
| hubert2026alphaproof | Nature 651 | 10.1038/s41586-025-09833-y | Crossref/Nature | 已核对；online/print 跨年 |
| poesia2023peano | Royal Society A | 10.1098/rsta.2022.0044 | Crossref/出版社 | 已核对 |

## 5. 投稿前人工签核（必须由作者本人完成）

请作者在提交前完成以下动作；未签核时，不应把“AI 生成结论均经人工核验”表述为已完成。

- [ ] 我已随机抽查不少于 8 篇一手文献的题名、作者、年份和主标识。
- [ ] 我已逐条检查论文中 C01–C07 的表述与来源是否匹配。
- [ ] 我确认 TRACE、可靠性向量和门控风险界是本文提出/整合的贡献，而非错误归因给引用论文。
- [ ] 我确认论文没有声称执行未发生的模型实验。
- [ ] 我已检查匿名/实名、单位、基金、利益冲突和投稿格式。

作者签名：____________________　日期：____________________
