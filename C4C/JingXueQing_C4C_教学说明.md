# JingXueQing_C4C_教学说明.md

> **技能**：作业自动求解与排版（国产大模型版）
> **适用人群**：理工科学生 / 助教 / 任何需要批量处理作业的人
> **日期**：2026-10-06

---

## 一、三分钟上手

```bash
# 1. 安装（只需 3 个包，无需 LaTeX）
pip install sympy pyyaml matplotlib

# 2. 跑一份作业
python scripts/pipeline_c4c.py my_homework.md output/ \
    --course "线性代数" --student "张三" --title "习题 7 解答"

# 3. 拿走 output/homework.pdf
```

就这三步。**不需要装 LaTeX**，PDF 由内置的 mathtext 后端渲染。

---

## 二、安装详解

### 必需依赖

| 包 | 版本 | 用途 |
|----|------|------|
| `sympy` | ≥1.12 | 符号计算（线代/ODE/物理/微积分） |
| `pyyaml` | ≥6.0 | 读取学科本体定义 |
| `matplotlib` | ≥3.7 | PDF 渲染 + 函数图 |

```bash
pip install sympy pyyaml matplotlib
```

macOS若用 Homebrew Python，建议加 `--break-system-packages` 或用虚拟环境：

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install sympy pyyaml matplotlib
```

### 可选依赖

| 场景 | 装什么 |
|------|--------|
| 读PDF 作业 | `pip install pdfplumber pypdf` |
| 读 Word 作业 | `pip install python-docx` |
| 扫描件 OCR | `pip install pytesseract pdf2image Pillow` + 本机装 tesseract |

> **关于 OCR 的实话**：Tesseract 对数学公式的识别率约 30~50%。
> 本项目**不会**对你承诺"扫描件也能搞定"——
> 检测到无文本层时会**明确失败并说明原因**，而不是丢一堆乱码进流水线假装成功。
> 建议作业用Markdown/Word/LaTeX 录入，或手动转录。

### 关于大模型 SDK

**不需要安装任何大模型 SDK。**

Qwen3.6 / Kimi K2.5 / DeepSeek 都提供 OpenAI 兼容的 `/chat/completions` 端点，
本项目用Python 标准库 `urllib` 直接调用。换厂商只需改一个 `base_url`。

---

## 三、配置国产大模型

### 三家端点

| 模型 | 环境变量 | 端点 |
|------|---------|------|
| Qwen3.6 | `DASHSCOPE_API_KEY` | `dashscope.aliyuncs.com/compatible-mode/v1` |
| Kimi K2.5 | `MOONSHOT_API_KEY` | `api.moonshot.cn/v1` |
| DeepSeek | `DEEPSEEK_API_KEY` | `api.deepseek.com/v1` |

### 配置方法

```bash
# 临时（当前终端）
export DASHSCOPE_API_KEY="sk-你的key"

# 永久（macOS/Linux，写入 ~/.zshrc）
echo 'export DASHSCOPE_API_KEY="sk-你的key"' >> ~/.zshrc && source ~/.zshrc
```

### 检查配置状态

```bash
python scripts/llm_engine.py --vendor qwen
```

输出示例：

```
✅ Qwen3.6 已就绪 (model=qwen3.6-max, key 来自 DASHSCOPE_API_KEY)
```

或未配置时：

```
⚠️  Qwen3.6 未配置 API key；设置 DASHSCOPE_API_KEY 或 QWEN_API_KEY 后自动启用；
   当前降级为 local 确定性后端（结果会如实标注 backend=local）
```

### 没配 key 会怎样？

**不会伪造模型输出。** 系统降级为 `local` 后端，它会诚实报告
"离线确定性后端不具备多步推理能力"，并在结果里标注
`backend="local", degraded=True`。

好处：计算题照常解出（SymPy），只有证明/概念题会明确失败。
你一眼就能看出哪些答案是模型解的、哪些是符号引擎解的。

---

## 四、使用说明

### 基本命令

```bash
python scripts/pipeline_c4c.py <输入文件> <输出目录> [选项]
```

### 全部选项

| 选项 | 默认 | 说明 |
|------|------|------|
| `--course NAME` | `Mathematics` | 课程名（PDF 页眉） |
| `--student NAME` | `Student` | 学生姓名 |
| `--title TITLE` | `Homework Solutions` | 文档标题 |
| `--llm {qwen,kimi,deepseek,none}` | `qwen` | 推理后端；`none`=纯符号模式 |
| `--domain NAME` | `general` | 领域提示：`linear_algebra`/`ode`/`physics` |
| `--report` | 关| 生成 Markdown 验证报告 |
| `--no-pdf` | 关 | 只出 .tex，不出 PDF |
| `--quiet` | 关 | 静默模式 |

### 典型用法

```bash
# ① 完全离线（不需要任何 key，适合批改、演示、教学）
python scripts/pipeline_c4c.py hw.md out/ --llm none --report

# ② 用 Qwen 处理证明题
python scripts/pipeline_c4c.py hw.md out/ --llm qwen

# ③ 线性代数作业（带上领域提示，路由更准）
python scripts/pipeline_c4c.py hw.pdf out/ \
    --llm qwen --domain linear_algebra \
    --course "线性代数" --student "张三" --title "习题 7 解答" --report

# ④ 只要 LaTeX（自己拿去 Overleaf 编译）
python scripts/pipeline_c4c.py hw.md out/ --no-pdf
```

### 输入格式

| 格式 | 支持度 | 说明 |
|------|--------|------|
| `.md` / `.txt` | ✅ 完整 | 直接读 |
| `.tex` | ✅ 完整 | 自动去 preamble、`\item` 转题号 |
| `.pdf` | ✅ 文本型 | pdfplumber 提取；无文本层则明确失败 |
| `.docx` | ✅ 完整 | 含表格 |
| `.png` / `.jpg` | ❌ | 未接视觉模型；请转录为 Markdown |

**题号格式**：`Problem 1` / `题 1` / `1.` / `1)` / `Q1` / `Exercise 1`
子题：`(a)` / `a)` / `a.`

---

## 五、输出说明

| 文件 | 用途 |
|------|------|
| `homework.pdf` | **可直接提交** |
| `homework.tex` | LaTeX 源码，可上传 Overleaf 获得更好的排版 |
| `3_solutions.json` | 完整解题记录（含路由与验证证据） |
| `verification_report.md` | 逐题验证报告（`--report`） |
| `0_summary.json` | 统计摘要 |

### 怎么读验证报告

| 标记 | 含义 | 该怎么办 |
|------|------|---------|
| ✅ pass | 所有自动验证项通过 | 可放心提交 |
| ❌ fail | 有验证项不通过 | **必须人工检查**（系统已拒答） |
| ➖ unverified | 无验证项 | 需人工核对；**不等于正确** |
| ⚠ 未解出 | 诚实失败 | 看`reason` 字段，可能需要人工完成 |

> `unverified` 和 `pass` 是**不同的状态**。
> "没有验证项"只说明程序无法自动检验，不代表答案是对的。

---

## 六、支持哪些课程

| 课程 | 覆盖内容 | 状态 |
|------|---------|------|
| **线性代数** | 行列式、秩、迹、逆矩阵、特征值/向量、对角化、线性相关性、Gram-Schmidt、SVD | ✅ |
| **常微分方程** | 一阶/二阶/三阶常系数线性方程（带残差验证）、一阶线性、可分离变量 | ✅ |
| **大学物理** | 牛顿第二定律、自由落体、动能、功率、库仑定律、欧姆定律、理想气体 | ✅ |
| **微积分** | 极限、切线、ε-δ 定义（继承 starter，94.4% 基线） | ✅ |
| 概率统计 | — | ❌ |
| 信号与系统 | — | ❌ |
| 电路分析 | 仅欧姆定律 | 部分 |
| 数值方法 | — | ❌ |

**判断某门课能不能用**：拿3 道该课程的作业跑一遍，
看 `0_summary.json` 里的 `solve_rate`。低于 60% 就别指望了。

---

## 七、扩展新学科

### 步骤

**① 写学科本体** `domain_skills/your_domain.yaml`

```yaml
domain: your_domain
concepts:
  - id: core_concept
    name: "核心概念"
    formal: "形式化定义"
    keywords: [关键词1, 关键词2]
solution_methods:
  - id: solver_1
    concept: core_concept
    name: "求解方法"
    tool: sympy
    validation: "如何验证"
classification_rules:
  - priority: 100
    pattern:
      text_contains: ["关键词1"]
    maps_to: core_concept
    solver: solver_1
known_limitations:
  - "明确写出不支持什么"
```

**② 实现求解器** `scripts/solve_extended.py`

```python
def solve_your_domain(problem: dict) -> dict:
    try:
        # ... 你的求解逻辑
        return _mk(problem, steps, answer_latex, answer, "sympy:your_domain")
    except Exception as e:
        return _fail(problem, f"求解失败: {e}")
```

**③ 加路由关键词** `scripts/pipeline_c4c.py`

```python
SYMPY_ROUTE = [..., "你的关键词"]
```

**④ 加验证方法** `scripts/verify.py`

```python
def verify_your_domain(...):
    """能代回检验的性质，尽量加"""
```

**⑤ 写测试——正例反例都要有**

```python
("Y1", r"你的题目", True),    # 应该解出
("Y2", r"看起来该支持但不支持的题", False),  # 必须诚实失败
```

> ⚠️ **第 5 步的反例不能省。**
> 本项目的测试里正例反例各占一半。没有负例，测试全绿也守不住"诚实失败"这条底线。

### 参考实现

`domain_skills/university_physics.yaml` 里有`required_labels` /
`on_missing_label: fail_honestly` 字段的用法，物理求解器是该模式的参考实现。

---

## 八、常见问题

**Q1：为什么不用 Claude？**
挑战要求迁移到国产大模型。我实现了 Qwen3.6 / Kimi K2.5 / DeepSeek 三个后端，
并刻意**不引入任何官方 SDK**（三家都有 Open 兼容端点，标准库 urllib 即可），
换厂商只改一行`base_url`。

**Q2：没有 LaTeX 也能出 PDF，排版会不会很难看？**
不会。mathtext 后端专门处理了 `\boxed` / `aligned` / `cases` / `pmatrix` 等
LaTeX 专有构造——这些 matplotlib 原生不支持，需要逐条降级。
矩阵括号是用线段拼的（字体大括号多行时对不齐）。
若你想要更好的排版，用 `--no-pdf` 只出 .tex，上传 Overleaf 编译。

**Q3：准确率 83% 是真的吗？**
是自动求解率（10/12），不是"正确率"。其中 9 题通过自动验证，
**1 题（P9 库仑定律）无验证项标unverified**。另有 2 题诚实失败。
详细逐题证据见验证报告。

**Q4：为什么有的题"未解出"？**
这是**设计行为**。当符号引擎和大模型都不确定时，系统选择明确失败而非编造。
`3_solutions.json` 的 `reason` 字段会说明原因。

**Q5：能处理扫描版PDF 吗？**
不能，且**我选择不假装能**。Tesseract 对数学公式识别率只有 30~50%，
强行 OCR 会产出大量错误公式——那比明确失败更糟。

**Q6：怎么提高准确率？**
按性价比排序：
1. 修路由关键词（漏判会导致好题被路由到错误引擎）
2. 加验证项（`unverified` 的题优先）
3. 扩domain yaml（把新的问法纳入）
4. 接入真实 LLM key（证明/概念题）

**Q7：能否只把它当 LaTeX 生成器用？**
可以：`--no-pdf` 只出 .tex，排版交给 Overleaf，求解能力照常。

---

## 九、性能参考

在M系列 Mac 上，12 题作业：

| 阶段 | 耗时 |
|------|------|
| 摄入 + 解析 | < 0.1 s |
| 符号求解 | ~0.3 s |
| PDF 渲染 | ~20 s |
| **合计** | **~23 s** |

> PDF 渲染占绝大部分时间（matplotlib 逐页绘制）。
> 批量处理上百份作业时，建议先用 `--no-pdf` 快速筛查，
> 只对需要提交的部分出 PDF。

---

## 十、给助教/教师的使用建议

这个技能最适合做**参考答案初稿**，而不是直接发给学生的答案：

1. `--llm none --report` 跑一遍全部作业
2. 看`verification_report.md`：✅ pass 的题可直接用，❌/➖ 的题人工补
3. 确认无误后再出 PDF

**不要**直接把未经审阅的 PDF 发给学生——
自动求解器的诚实失败率仍有 20% 左右，且自动验证无法覆盖概念正确性。