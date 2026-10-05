---
name: c4-skill-evaluator
description: >
  Scan a local folder containing Elite20 C4 skill submissions (typically synced from a
  WeChat group), identify each submitter, check the 5 required deliverables, evaluate
  skill quality against the C4 four-criteria rubric (Reusable / Executable / Verifiable /
  Clear I-O), and generate a Markdown + Excel + HTML evaluation report in which every
  verdict is traceable to a specific file and line number.
  Use whenever the user says "evaluate C4 submissions", "review skill submissions",
  "check C4 completeness", "grade the submissions", "评审C4提交", "检查技能提交",
  "C4评审报告", "谁没交作业", or hands you a folder path and asks to evaluate/review
  the skill files inside. Also trigger when the user mentions the C4 challenge together
  with evaluation, grading, review, or ranking.
---

# C4 技能提交自动评审器

把「收发室」升级成「自动阅卷系统」：输入一个装着大家 C4 提交的本地文件夹，
输出一份**每条判定都能追溯到源文件行号**的评审报告。

## 核心设计：证据优先

这个技能与普通"关键词计数脚本"的根本区别：

> **没有证据的判定不允许进入评分。**

每一个 ✅ / ⚠️ / ❌ 都携带 `文件:行号` + 命中的原文片段 + 规则 ID。
这带来三个后果：

1. **误判可申诉** —— 老师说"这条判错了"，1 秒定位到原文；
2. **置信度可量化** —— 证据少就标"需人工复核"，不硬给结论；
3. **改标准不动代码** —— 评审口径全在 `c4a/rubric.py`，改文件即可。

实测准确率（8 份带金标准的提交，含 3 份对抗样本 / 72 个判定点）：

| 指标 | 数值 |
|------|------|
| 严格准确率（完全一致） | **90.3%** |
| 宽松准确率（一致+保守） | **100%** |
| 误判率（放过真问题） | **0%** |

## 快速开始

```bash
cd scripts

# 完整评审（Level 1-4）
python3 evaluate_c4.py <文件夹> --out ./评审输出

# 只盘点谁交了什么（秒级）
python3 evaluate_c4.py <文件夹> --scan-only

# 只跑到完整性检查
python3 evaluate_c4.py <文件夹> --level 2

# 自检：跑金标准测试集，看准确率
python3 evaluate_c4.py --selftest
python3 tests/make_fixtures.py     # 首次需先生成测试集
```

**零第三方依赖**，Python 3.8+ 即可运行。（PDF 内容抽取需要 `pypdf`，
没装会自动降级为"仅按文件名评估"并在报告里说明，不影响其他维度。）

## 四个层级

```
① 采集与识别  collect.py      递归扫描 → 作者归属 → 按作者分组
       ↓
② 完整性检查  completeness.py 5 个必交文件是否齐（带空壳检测）
       ↓
③ 质量评审    quality.py      四条件 × 19 个检查项，逐条带证据
       ↓
④ 报告生成    report.py       Markdown + Excel + HTML 仪表盘
```

每层都是独立函数，可单独调用、单独测试。

## 评审口径

### 完整性：5 个必交文件

| 槽位 | 文件名信号（权重 1.0） | 内容信号（权重 ≤0.7） |
|------|----------------------|---------------------|
| Skill 说明文档 | `skill说明` `skill_doc` | "解决什么问题" "使用场景" |
| 可执行内容 | `.skill` `.py` | YAML frontmatter、代码块 |
| Demo | `demo` `演示` `截图` | md 内嵌截图 |
| 教学说明 | `教学说明` `tutorial` | "常见坑" "上手" |
| AI 日志 | `AI日志` `AI_log` | "迭代N轮" "使用的AI工具" |

判定档位：证据强度 ≥0.90 → ✅；≥0.60 → ⚠️（弱证据，需人工确认）；否则 ❌。

**两道防误判闸门**（都是实测踩坑后加的）：
- **空壳检测** —— 文件名合规但正文是「待补充/TODO」，降级为 ⚠️；
- **附件降权** —— `samples/` 下的模板不能算作者交了 AI 日志。

### 质量：C4 四条件

| 条件 | 检查项 |
|------|--------|
| 可复用 | 安装说明 / 环境依赖 / **无硬编码路径** / **无明文密钥** / 适用边界 |
| 可执行 | 可运行代码 / YAML frontmatter / 运行命令 / 非空壳模板 |
| 可验证 | 示例或测试 / 预期结果 / 运行证据 / 可复现参数 |
| IO 明确 | 输入输出成对描述 / 类型格式 / 一句话摘要 |

默认权重：可执行 30%、可复用 25%、可验证 20%、IO 明确 25%（可用 `--weights` 覆盖）。

**三条判定规则**：
1. **负向优先** —— 检出问题信号时压档，不能靠"多写几段"洗白；
2. **致命一票否决** —— 硬编码个人路径 / 明文密钥直接判该维度 ❌
   （依据 C4 检验方法："陌生人按你的说明操作能成功吗？"这类问题让他必然失败）；
3. **占位符污染** —— 标题写了「## 安装」但正文是「TODO: 补充安装步骤」，
   不算有安装说明（有标题无内容）。

## 已知边界

- **元提及**：技能文档在列举"要检查哪些关键词"时会提到坏味道本身。
  已用 `META_ENUM` 规则过滤，但换一种写法仍可能误判 → 这类结论会标"需人工复核"。
- **语义判断**：规则读不懂"这段话是不是真的在讲安装"。这是选择规则层的
  代价：换来可复现、零成本、可申诉。架构上预留了 LLM 深审接口
  （`quality.extract_signals_for_llm`），需要时可在规则层之上叠加。
- **作者同名**：中文名与拼音名不会被自动合并（`张伟` vs `ZhangWei`），
  报告里分列，等人确认。

## 扩展

改评审口径 → 只改 `c4a/rubric.py`（标准与实现分离）。
加挑战 → `c4a/rubric.py` 的 `COMPLETENESS_SPEC` 加一组槽位。
换权重 → 命令行 `--weights`，不用改代码。

## 文件结构

```
scripts/
├── evaluate_c4.py         CLI 入口
├── c4a/
│   ├── collect.py         Level 1 采集与作者识别
│   ├── completeness.py    Level 2 完整性检查
│   ├── quality.py         Level 3 四条件质量评审
│   ├── report.py          Level 4 报告生成（含手写 xlsx）
│   ├── evidence.py        证据引擎（行号级追溯、档位判定）
│   ├── rubric.py          评审标准（改这里即可调口径）
│   ├── extract.py         多格式内容抽取（纯标准库）
│   └── pipeline.py        流水线编排
└── tests/
    ├── make_fixtures.py   生成 8 份带金标准的测试提交
    └── run_selftest.py    跑测试并输出准确率报告
```

> `extract.py` 从 `wechat-doc-mapper` 拿来了标题抽取的分派思路，
> 但改为纯标准库实现（OOXML 用 zipfile+正则，PDF 用可选 pypdf），
> 去掉了 `pandas` / `python-docx` / `openpyxl` 依赖，让技能在任意机器上直接跑。
