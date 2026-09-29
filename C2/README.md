# AI4Math Reliability Paper — Submission Package

本目录是 Challenge C2「AI for Math 论文」的完整交付包。论文提出 **TRACE 五门可靠性框架**：任务/数据溯源（T）、推理搜索（R）、语义对齐（A）、确定性确证（C）与评估重放（E）。

## 文件清单

| 文件 | 用途 |
|---|---|
| `paper.tex` | 可投稿中文 LaTeX 主文件，含中英文题名、图、表、公式、局限与附录 |
| `references.bib` | BibTeX 文献库，含 20 条真实可查的一手来源 |
| `paper.pdf` | 已通过 Tectonic 0.17.0 完整编译的 12 页论文 |
| `AI协作日志.md` | 实际协作日期、提示迭代、采用/拒绝记录、结论—证据映射和人工签核清单 |
| `七维AAR.md` | 七维复盘，含三个 AI 误导/过强表述案例及制度化对策 |
| `README.md` | 本文件：编译、复现与提交说明 |

## 已验证构建

- 编译器：Tectonic 0.17.0
- 结果：退出码 0；TeX、BibTeX 与最终重跑均成功
- 最终日志：无未定义引用、未定义交叉引用、缺字、overfull/underfull 或 LaTeX 警告
- PDF：12 页，478,423 字节
- SHA-256：`61685c46215a3a139f66326e2a5a188d68bc174e281f775f61e02b62fd71f981`
- 引用：BibTeX 共 20 条，正文使用 19 个不同引用键，缺失引用键 0

## 编译方法

### 方案 A：XeLaTeX + BibTeX

在本目录执行：

```bash
xelatex -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
xelatex -interaction=nonstopmode -halt-on-error paper.tex
xelatex -interaction=nonstopmode -halt-on-error paper.tex
```

### 方案 B：Tectonic

```bash
tectonic --keep-logs --keep-intermediates paper.tex
```

主文件使用 `ctexart` 与 Fandol 字体集，不依赖系统中文字体；推荐 XeLaTeX 或 Tectonic。论文引用采用标准 BibTeX `unsrtnat` 样式。

## 提交前检查

1. 打开 `paper.pdf`，检查 TRACE 流程图、跨层证据表与长表是否分页正常。
2. 在编译日志中搜索 `undefined`、`Citation`、`Reference`、`Error`。
3. 打开 `AI协作日志.md`，由作者本人完成末尾五项人工签核并签名。
4. 按目标会议/期刊要求替换匿名作者信息、模板、页数和 AI 使用声明。
5. 若增加模型实验，必须保存数据快照、提示、随机种子、搜索预算、评分脚本和失败样本；不得直接拼接不同论文的排行榜数字。

## 论文贡献与边界

- **原创贡献**：TRACE 五门、门控式选择性发布、残余错误并集界、可靠性卡和跨研究机制编码。
- **证据基础**：正文引用 19 篇一手研究，覆盖 verifier/PRM、Lean/自动形式化、神经符号系统和数学基准。
- **研究类型**：框架论文与结构化证据综合；未开展新的模型训练或性能实验，因此不声称新的准确率提升。
- **尚需人工完成**：作者署名、目标投稿模板适配、引用与核心论点的最终人工签核。

## Rubric 对照

| 评分维度 | 本包中的对应证据 |
|---|---|
| 研究严谨性 | 研究问题、纳入标准、19 篇一手引用、适用边界、效度威胁、AI 误导纠正 |
| 技术实现 | 可独立编译的 `paper.tex`、TikZ 图、规范表格、公式、BibTeX 与编译日志 |
| 产物完整性 | 主文件、文献库、AI 日志、七维 AAR、编译说明、最终 PDF |
| AI 使用质量 | 多轮提示演化、采纳/拒绝表、结论—证据映射、人工签核接口 |
| 复盘质量 | 七维 AAR、失败点、根因、三个具体 AI 误导案例、下一轮 Go/No-Go 标准 |
