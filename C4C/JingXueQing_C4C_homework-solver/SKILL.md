# Homework Auto-Solver & Formatter — 国产大模型版（C4C）

> 从作业文件到可提交 PDF，一条命令搞定。
> Ontology-grounded · 混合求解（SymPy + 国产大模型）· 带验证闸门。

作者：JingXueQing（2024102110351）｜ 基于 C4C starter kit 迁移与扩展

---

## 这个技能与starter 的差别

starter kit 在 Claude Code 上跑通微积分极限（17/18 = 94.4%），但它的"LLM 层"是**隐式**的——
`solve_proof()` 直接 `_unsolved("证明题需要 LLM 求解器")`，真正推理由运行 skill 的宿主智能体在对话里补齐。
本项目把这一层**显式化、可替换、可度量**：

| 维度 | starter kit | 本项目 |
|------|-------------|--------|
| 推理层 | 隐式（宿主智能体补齐） | 显式三后端：api / agent / local |
| 国产模型 | 未接入 | Qwen3.6、Kimi K2.5、DeepSeek（OpenAI 兼容，零 SDK 依赖） |
| 学科 | 仅微积分极限 | + 线性代数、常微分方程、大学物理 |
| 输入格式 | 仅 Markdown | + PDF、Word、LaTeX |
| PDF | 需本机装 LaTeX（脚手架） | **双后端**：有 TeX 走 xelatex；无 TeX 走 matplotlib mathtext |
| 正确性 | 无验证 | 残差 / 量纲 / 代数 / 自洽四类自动验证 |
| 失败行为 | 返回 unsolved | **诚实失败**：算不出就说算不出，绝不编造 |

---

## 快速开始

### 1. 安装

```bash
pip install sympy pyyaml matplotlib          # 必需
pip install pdfplumber python-docx# PDF/Word 摄入（可选）
```

无LaTeX 环境也能出PDF（自动走 mathtext 后端）。

### 2. 配置国产大模型（可选，但强烈建议）

```bash
export DASHSCOPE_API_KEY="sk-..."     # Qwen3.6
export MOONSHOT_API_KEY="sk-..."      # Kimi K2.5
```

检查配置状态：

```bash
python scripts/llm_engine.py --vendor qwen
```

未配置 key 时**不会伪造模型输出**，而是降级为 `local` 后端并在结果中如实标注
`backend=local, degraded=True`。

### 3. 运行

```bash
# Markdown 输入
python scripts/pipeline_c4c.py homework.md out/ \
    --course "线性代数" --student "张三" --title "习题 7 解答"

# 只用符号引擎，不调模型（完全离线）
python scripts/pipeline_c4c.py homework.md out/ --llm none

# 换用 Kimi，并输出验证报告
python scripts/pipeline_c4c.py homework.pdf out/ --llm kimi --domain linear_algebra --report
```

### 4. 输出

| 文件 | 内容 |
|------|------|
| `1_ingested.json` | 摄入结果 + 摄入方式、页数、告警 |
| `2_parsed.json` | 结构化题目（含子题、公式、类型） |
| `3_solutions.json` | 解答 + **路由记录** + **验证证据** |
| `homework.tex` | LaTeX 源码（可上传 Overleaf） |
| `homework.pdf` | **可提交 PDF** |
| `verification_report.md` | 逐题验证报告（`--report`） |
| `0_summary.json` | 统计摘要 |

---

## 混合求解：谁用什么

这是本项目的核心设计。原则：**能用符号计算证明的，绝不交给大模型猜。**

```
                    ┌──────────────────┐
                    │  题目进来         │
                    └────────┬─────────┘
                             │
                ┌────────────▼────────────┐
       证明/说理？ ─是─→ LLM（推理不可替代）│
                │否                       │
                └────────────┬────────────┘
                             │
              命中确定性题库？ ─是─→ SymPy（可验证）
                             │否
                ┌────────────▼────────────┐
                │ starter 内核可处理？     │
                └────┬──────────────┬─────┘
                  是  │              │ 否
                     ▼              ▼
              starter 求解      LLM 求解
                     │              │
                     └──────┬───────┘
                            ▼
                   ┌─────────────────┐
                   │ verify.py 闸门   │ ← 残差/量纲/代数/自洽
                   └────────┬────────┘
                       pass │ fail → 拒答（不输出错误答案）
                            ▼
                   LaTeX → PDF
```

### 路由表

| 路径 | 触发条件 | 为什么这样分 |
|------|---------|------------|
| `sympy` | 特征值/行列式/秩/逆矩阵/ODE/牛顿定律/库仑/欧姆/自由落体… | 确定性计算，结果可代回验证 |
| `llm` | 证明、说理、概念题 | 符号引擎无能为力 |
| `starter` | 极限、切线、ε-δ | starter 内核已验证 94.4%，不重写 |

**顺序很关键**：先判证明题。「证明可逆矩阵特征值非零」同时含"矩阵"和"证明"，
若先匹配关键词会误判为计算题，交给符号引擎后必然失败。

---

## 验证闸门（为什么必须有）

开发中真实踩到的坑：

> `y' + 2y = 0` → dsolve 返回 `y = C₁ - 2xy`
> 形式漂亮、步骤完整、LaTeX 排版正常，但**代回原方程残差不为零**。

自动求解器最危险的失败模式不是"答不出"，而是**"答得很像真的但其实错"**。
因此每题求解后强制跑验证，**验证不通过就拒答**。

| 验证类型 | 检查内容 | 抓什么错 |
|---------|---------|---------|
| 残差验证 | 解代回方程，残差须为 0 | dsolve 给错解、方程解析错位 |
| 量纲齐次性 | 公式两侧量纲向量相等 | 用错物理公式、数值算错 |
| 代数验证 | Av=λv、AA⁻¹=I、QᵀQ=I | 特征对配错、逆矩阵算错 |
| 自洽交叉检验 | Σλ=tr(A)、det≠0 ⟺满秩 | 中间步骤系统性偏差 |

`unverified`（无验证项）与 `pass` 是**不同的状态**——无法验证不等于正确。

---

## 支持的学科

### 线性代数（`domain_skills/linear_algebra.yaml`）

行列式、秩、迹、逆矩阵、特征值/特征向量、对角化、线性相关性、
Gram-Schmidt 正交化、SVD

### 常微分方程（`domain_skills/differential_equations.yaml`）

一阶/二阶/三阶常系数线性方程（dsolve + 残差验证）、
一阶线性、可分离变量

### 大学物理（`domain_skills/university_physics.yaml`）

力学（牛顿第二定律、自由落体、动能、功率）、
电磁学（库仑定律、欧姆定律）、热学（理想气体）

### 微积分极限（继承 starter）

切线、ε-δ 定义、极限计算与证明、连续性

---

## 物理题的标签锚定原则

**绝不按数字出现顺序猜测物理量。**

真实教训：初版按顺序取数，在「质量 2 kg、受力 10 N」上
把 2 当成 F、10 当成 m，得出 `a = 0.2 m/s²`（正确值 5 m/s²）——
一个看起来完全专业、实则彻底错误的答案。

现在的做法：只有当数字旁边能找到所属物理量的**标签**
（`质量为 2 kg` / `F = 10 N` / `q_1 = 2 C`）才采用；
找不到就诚实失败，并说明缺哪个量。

```python
# ✅ 标签锚定
extract_quantities("一质量为 $2\,\mathrm{kg}$ 的物体受合力 $10\,\mathrm{N}$")
# → {'m': 2.0, 'F': 10.0}

# ❌ 顺序猜测（初版，已废弃）
numbers[:2]  # → [2.0, 10.0]，恰好把 F 和 m 弄反
```

---

## 无 LaTeX 环境如何出 PDF

本机（以及大量学生机）没装 TeX，且 GitHub 不可达、brew 不存在，
常规"装个 TeX 发行版"的路线全被封死。starter 的 `--compile` 因此形同虚设。

本项目实现**双后端**：

| 后端 | 条件 | 说明 |
|------|------|------|
| `latex` | 有 pdflatex/xelatex | 生成 .tex 后编译 3 遍（starter 原路径） |
| `mathtext` | 无 TeX（默认） | matplotlib mathtext 直接渲染 PDF |

mathtext 后端的工程量在于 LaTeX 方言转换。实测 mathtext **不支持**：

```
\boxed   \begin{aligned}   \begin{cases}   \begin{pmatrix}
\fbox    \stackrel          \tfrac          \textcolor   \le/\ge/\to
```

因此实现了逐条降级：`aligned`→逐行、`boxed`→渲染后叠边框、
`cases`→加左侧大括号、`pmatrix`→逐元素网格+线段括号、
`\le→\leq` 等别名映射、`\frac12→\frac{1}{2}` 补花括号。

排版采用**两遍法**：先在探针 figure 上**实测**每段高度，再贪心分页。
初版用固定常数估算高度，结果出现「答案压到下一题标题上」等错版——
公式高度依赖实际字号与内容，必须实测。

---

## 测试

```bash
python tests/test_llm_engine.py# 40 项：JSON 容错、降级诚实性、缓存
python tests/test_render_pdf.py       # 23 项：方言转换、PDF 产出
python scripts/solve_extended.py      # 11 项：三学科求解（含负例）
python scripts/verify.py              #  9 项：正例反例各半
python tests/make_preview.py /tmp/pv  # 生成排版预览 PNG 供目检
```

**共 83 项，全部通过。** 其中负例（必须失败却解出的题）是刻意设计的，
用来守住"诚实失败"这条底线。

---

## 扩展新学科

1. 在 `domain_skills/` 加一个 YAML，定义 concepts / solution_methods /
   classification_rules / validation_rules
2. 在 `solve_extended.py` 实现对应的求解函数，返回统一结构
3. 在 `pipeline_c4c.py` 的 `SYMPY_ROUTE` 加入路由关键词
4. 在 `verify.py` 加入该学科的验证方法
5. **加负例测试**：至少一题"看起来该支持但确实不支持"，确保它诚实失败

参考 `calculus_limits.yaml`（starter 原件）与 `university_physics.yaml`
（含 `required_labels` / `on_missing_label: fail_honestly` 字段）。

---

## 已知边界

| 限制 | 说明 |
|------|------|
| 扫描型 PDF | Tesseract 对数学公式识别率约 30~50%，本项目**明确拒绝**而非输出乱码 |
| 图片输入 | 未接入视觉模型；建议转录为 Markdown |
| 拉普拉斯变换法 | 未实现（回退 dsolve） |
| 偏微分方程 / 转动 / 振动 / 光学 | 未覆盖 |
| 多过程复合物理题 | 需人工审阅 |
| 参数矩阵讨论 | 未实现 |

这些边界都写在各domain YAML 的 `known_limitations` 里，
且**失败时会在PDF 中标注原因**，不会静默产出错误答案。

---

## 文件结构

```
c4c-homework-solver-cn/
├── SKILL.md← 本文件
├── requirements.txt
├── scripts/
│   ├── pipeline_c4c.py         ← 一键流水线（Stage 1-5 + 混合路由）
│   ├── llm_engine.py           ← 国产大模型适配层（api/agent/local）
│   ├── solve_extended.py       ← 线代/ODE/物理求解器
│   ├── verify.py               ← 答案验证模块
│   ├── render_pdf.py           ← LaTeX + mathtext 双后端渲染
│   ├── ingest_ext.py           ← 多格式摄入（md/tex/pdf/docx）
│   ├── solve.py                ← 继承自starter（微积分内核）
│   ├── parse_problems.py       ← 继承自 starter
│   ├── render_latex.py         ← 继承自 starter
│   ├── classify.py             ← 继承自 starter（T-box 分类）
│   ├── retrieve.py             ← 继承自 starter（T-box 检索）
│   └── bootstrap.py            ← 继承自 starter（依赖自举）
├── domain_skills/
│   ├── calculus_limits.yaml    ← 继承 starter
│   ├── linear_algebra.yaml     ← 新增
│   ├── differential_equations.yaml ← 新增
│   └── university_physics.yaml ← 新增
├── examples/
│   └── homework7_linear_algebra_ode.md
├── tests/                      ← 83 项测试
└── output/                     ← 真实作业端到端产出
```