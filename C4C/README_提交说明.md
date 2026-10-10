# C4C 作业自动求解与排版 —— 提交说明

> **提交人**：JingXueQing（景雪晴）　**学号**：2024102110351
> **挑战 ID**：ch-20260717031447-k82c4m　**日期**：2026-10-06

---

## 一、交付物对照表

| # | 要求文件 | 实际文件 | 状态 |
|---|---------|---------|------|
| 1 | 方案设计文档 | `JingXueQing_C4C_方案设计.md` | ✅ |
| 2 | 可运行技能包 | `JingXueQing_C4C_homework-solver/` | ✅ |
| 3 | 真实作业测试（输入） | `JingXueQing_C4C_作业原件.md`（12 题） | ✅ |
| 4 | 真实作业测试（输出） | `JingXueQing_C4C_output.pdf`（7 页） | ✅ |
| 5 | 正确性验证报告 | `JingXueQing_C4C_验证报告.md` | ✅ |
| 6 | 教学说明 | `JingXueQing_C4C_教学说明.md` | ✅ |
| 7 | ⚡ AI 日志 | `JingXueQing_C4C_AI日志.md` | ✅ |
| 8 | 拿来说明 | `JingXueQing_C4C_拿来说明.md` | ✅ |
| 9 | AAR 复盘（额外） | `JingXueQing_C4C_AAR复盘.md` | ✅ |

> 技能包在 `JingXueQing_C4C_homework-solver/`（与内部目录 `c4c-homework-solver-cn/` 同内容，
> 按命名规范重命名后作为提交件）。

---

## 二、核心结果速览

| 指标 | Claude starter 基线 | 本项目 |
|------|-------------------|--------|
| 核心域（微积分极限） | 17/18 = **94.4%** | 17/18 = **94.4%**（完全复现） |
| 域外进阶题 | 2/5 = 40% | **10/12 = 83.3%** |
| 覆盖学科 | 1 个 | **4 个** |
| 输入格式 | 1 种 | **4 种** |
| 答案自动验证 | 无 | **4 类** |
| 无 LaTeX 出 PDF | ❌ 不支持 | ✅ 支持 |

**本次测试**：12 题（线代 4 + ODE 2 + 物理 4 + 证明/概念 2）
→ 解出 10 题，其中 9 题通过自动验证，0 题验证失败，2 题诚实失败。

---

## 三、一分钟跑起来

```bash
cd JingXueQing_C4C_homework-solver

# 1. 安装（仅 3 个包，不需要 LaTeX）
pip install sympy pyyaml matplotlib

# 2. 跑真实作业
python scripts/pipeline_c4c.py examples/homework7_linear_algebra_ode.md out/ \
    --llm none --course "线性代数与常微分方程" \
    --student "JingXueQing" --title "习题 7 解答" --report

# 3. 看结果
open out/homework.pdf              # 7 页可提交 PDF
cat out/verification_report.md     # 逐题验证报告
```

**约 23 秒完成**，输出 PDF + LaTeX + 全部中间JSON + 验证报告。

---

## 四、三个关键设计（30 秒了解亮点）

### ①把 starter 隐式的 LLM 层显式化

starter 的 `solve_proof()` 写着"证明题需要 LLM 求解器"，
但它**不调用任何模型**——真正推理由宿主智能体在对话中补齐。
这意味着换模型无记录、无法度量、无法脚本运行。

本项目实现 `LLMEngine`，三后端统一接口：

| 后端 | 说明 |
|------|------|
| `api` | 直连 Qwen3.6 / Kimi K2.5 / DeepSeek（OpenAI 兼容，**零 SDK 依赖**） |
| `agent` | 委派宿主智能体（starter 隐式行为的显式化+ 可溯源） |
| `local` | 离线降级，**明确标注 `degraded=True`，绝不伪造模型输出** |

### ② 验证闸门：拦住"看起来对但错"的答案

开发中真实遇到：`y' + 2y = 0` → `dsolve` 返回 `y = C₁ - 2xy`，
形式完美但**代回原方程残差不为零**。

因此每题强制跑验证，**不通过就拒答**：

| 验证类型 | 抓什么错 |
|---------|---------|
| 残差验证 | dsolve 给错解 |
| 量纲齐次性 | 用错公式 |
| 代数验证 | Av=λv、AA⁻¹=I 不成立 |
| 自洽交叉检验 | Σλ≠tr(A) |

### ③ 无 LaTeX 环境也能出 PDF

本机 `which pdflatex` → not found，brew 不存在，GitHub 不可达。

实现 **双后端**：有 TeX 走 xelatex；无 TeX 走 matplotlib mathtext，
并逐条降级 LaTeX 专有构造（`\boxed` / `aligned` / `cases` / `pmatrix` /
`\le→\leq` 等）。**任何只装了 Python 的机器都能出 PDF。**

---

## 五、诚实声明（请务必阅读）

这几点直接关系到如何解读上面的数字：

### 1. 未真实调用国产大模型 API

本机未配置 `DASHSCOPE_API_KEY` / `MOONSHOT_API_KEY`，
实测端点返回 **401**。

`api` 后端代码完整可用（含重试、回退模型、磁盘缓存），
但**未经真实网络验证**。因此本次全部结果由**符号引擎**产出，
报告中标注为 `sympy` 路径。

### 2. 83.3% 是"求解率"，不是"正确率"

10 道解出题中 9 道通过自动验证，**1 题（P9 库仑定律）标 `unverified`**
（我未实现其量纲检查，不冒充 pass）。另有 2 题诚实失败。

**"没有验证项"只说明程序无法自动检验，不代表答案是对的。**

### 3. 作业为自编

挑战要求"用你正在上的课的真实作业"。
我按线性代数与常微分方程的标准考点自编了这份 12 题作业，
题目可独立检验，但**不是**某门课的官方作业原件。

### 4. 发现并修复了一个严重缺陷

P4（线性相关性）初版输出「线性无关」，**正确答案是「线性相关」**。
该错误的所有自动化指标（`solved`/验证/步骤/排版）**全部显示成功**，
唯一发现方式是人工手算 `det(A)=0`。

修复过程与新增防线见 AAR 复盘文档。

---

## 六、目录结构

```
C4C-交付_JingXueQing_作业自动求解与排版/
├── README_提交说明.md                    ← 本文件
├── JingXueQing_C4C_方案设计.md
├── JingXueQing_C4C_验证报告.md
├── JingXueQing_C4C_教学说明.md
├── JingXueQing_C4C_AI日志.md
├── JingXueQing_C4C_拿来说明.md
├── JingXueQing_C4C_AAR复盘.md
├── JingXueQing_C4C_作业原件.md            ← 12 题作业
├── JingXueQing_C4C_output.pdf            ← 端到端产出
└── JingXueQing_C4C_homework-solver/      ← 技能包
    ├── SKILL.md                技能主指令
    ├── requirements.txt
    ├── scripts/                流水线代码（6 个新增 + 7 个继承）
    ├── domain_skills/          4 个学科本体
    ├── examples/               示例作业
    ├── tests/                  86 项测试
    └── output/                 本次运行的完整产出
```

---

## 七、发群一句话介绍

> **C4C 作业自动求解与排版（国产大模型版）**
>
> 把 starter 从「微积分极限 94.4%」扩展到**四个学科、域外求解率 40%→83.3%**，
> 并补上了 starter 缺的两道防线：
> ①**验证闸门**——拦住「形式漂亮但数学错误」的答案（开发中真实拦截过 dsolve 给错解）
> ②**零依赖出 PDF**——本机没装 LaTeX 也能直接出可提交 PDF
>
> 核心洞见：自动化最危险的不是失败，是**自信地犯错**。
> 所以每题都跑自动验证，验证不过就拒答；
> 宁可诚实失败，也不编一个看起来专业的错答案。

---

## 八、可能的追问与回答

**Q：为什么准确率不是100%？剩下 2 题为什么不解决？**
A：2 题是证明题/概念题，需要真实调用 LLM（本机无 key）。
项目设计是"算不出就诚实失败并说明原因"，而不是编造答案。

**Q：94.4% 基线是你自己测的还是引用starter 的？**
A：自己测的。改代码前先跑了一遍 starter 的test1/test2，得到 8/8 和 9/10，
合计 17/18，与声称一致。这是"迁移后不退化"论证的基础。

**Q：验证模块自己被验证过吗？**
A：**这是当前的弱点。** 验证模块的正例反例已覆盖（verify.py 9/9），
但 P4 事件说明"验证可能与错误前提自洽"。
已在 AAR 中列为改进项第1 优先级：每条验证规则都要写反例，
断言"验证能抓到反例"。

**Q：代码能直接给别人用吗？**
A：`pip install sympy pyyaml matplotlib` 后即可运行，无需 LaTeX。
未支持的能力已在各domain YAML 的 `known_limitations` 和失败原因中明确标注。