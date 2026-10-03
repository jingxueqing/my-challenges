# AttnScope — 用「抗干扰效率阶梯」衡量机器注意力

**赛道：** Kaggle × DeepMind "Measuring Progress Toward AGI" — Track 3 · Attention
**作者：** JingXueQing ｜ **版本：** v0.1（C2A 提案配套的可运行原型）
**状态：** L1 选择性阶梯**已实装并可运行**；L2 / L3 的生成器与评分函数已写好但尚未接入 CLI。

> ⚠️ 本仓库中的 `MockRunner` 仅为**管线冒烟测试**而存在，它的数字不代表任何真实模型，
> 也不构成任何科学结论。真实结论必须在 C9 阶段用前沿模型的实测数据得出。

---

## 1. 这份代码在测什么

认知科学六十年从不只用「命中率」衡量注意力，而是用**效率如何随干扰负荷下降**
（Treisman & Gelade, 1980 的 set-size 斜率）。现有 AI benchmark 只报「找没找到」，
AttnScope 报的是「**在多大的干扰负荷下还能找到**」。

| 阶梯 | 认知科学来源 | 测量 ΔS 的哪一类成因 | 状态 |
|---|---|---|---|
| **L1 选择性**（过滤） | Treisman & Gelade (1980)；Duncan & Humphreys (1989) | 选择失败（被显著干扰物捕获） | ✅ 可运行 |
| **L2 持续性**（维持） | Mackworth (1948) vigilance；对标 Liu et al. (2023) U 型曲线 | 维持失败（中途丢失） | 🧪 生成器已实装 |
| **L3 变化觉察**（更新） | Rensink et al. (1997)；Simons & Levin (1997) | 更新失败（情境变了但 S 没更新） | 🧪 生成器已实装 |

**核心指标（刻意不用准确率作主指标）：**

| 指标 | 定义 | 为什么 |
|---|---|---|
| `AES_slope` | 正确率对 log₂(负荷) 的回归斜率 | 斜率≈0 = pop-out；显著为负 = 资源受限 |
| `B70` | 正确率跌破 70% 时的负荷值（log 刻度插值） | 自适应难度，天然避免天花板/地板效应 |
| `lure_capture_rate` | 错误中「选中了最相似诱饵」的比例 | 区分「没找到」与「被误导」——两种失败机制 |
| `d_prime` / `criterion` | 信号检测论（Green & Swets, 1966） | 分离敏感性与响应偏向；堵住「全答一类」刷分 |
| `split_half_reliability` | 分半信度（Spearman-Brown 校正） | 报告信度，而非只报一个分数 |

---

## 2. 安装

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt     # 仅在使用 --runner openai 时才真正需要 openai 包
```

> 题目生成与**全部评分逻辑只依赖 Python 标准库**（`statistics.NormalDist` 用于 d′ 计算），
> 因此离线冒烟测试零依赖。要求 Python ≥ 3.9。

---

## 3. 使用

### 3.1 离线冒烟（推荐先跑这个）

```bash
python run_eval.py --runner mock --items-per-cell 50 --out results/mock_l1.json
```

### 3.2 真实模型

```bash
export OPENAI_API_KEY=sk-...
python run_eval.py --runner openai --model gpt-4o-mini --items-per-cell 50 \
                   --out results/gpt-4o-mini_l1.json
```

### 3.3 兼容网关 / 本地 vLLM / 其他家模型

```bash
python run_eval.py --runner openai --model Qwen/Qwen2.5-72B-Instruct \
                   --base-url http://localhost:8000/v1 --out results/qwen_l1.json
```

### 3.4 常用参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--loads` | `4,8,16,32,64` | 干扰负荷阶梯 N（**token 总量恒定**，仅密度变化） |
| `--similarities` | `0.2,0.5,0.9` | 目标-干扰相似度（诱饵占比） |
| `--conditions` | `feature,conjunction` | feature = pop-out；conjunction = 需逐个特征绑定 |
| `--items-per-cell` | `50` | 每格题目数。20 时单格标准误约 ±0.09，噪声过大 |
| `--seed` | `20261003` | 随机种子；换种子即换一套全新题目（防污染） |

---

## 4. 输出示例（MockRunner，仅示意管线）

`python run_eval.py --runner mock --items-per-cell 50`：

| 条件 × 相似度 | 总体正确率 | AES 斜率 | B70 | 诱饵捕获率 | 分半信度 |
|---|---|---|---|---|---|
| conjunction \| sim=0.2 | 0.776 | −0.060 | 14.8 | 0.554 | 0.917 |
| conjunction \| sim=0.5 | 0.704 | −0.102 | 14.8 | 0.554 | 0.992 |
| conjunction \| sim=0.9 | 0.556 | −0.052 | **4.0** | 0.604 | 0.872 |
| feature \| sim=0.2 | 0.820 | −0.064 | 28.5 | 0.533 | 0.813 |
| feature \| sim=0.5 | 0.860 | −0.056 | **64.0** | 0.629 | 0.607 |
| feature \| sim=0.9 | 0.840 | −0.074 | 52.5 | 0.575 | 0.895 |

可以读出：**conjunction 条件随相似度升高而崩塌（B70 从 14.8 掉到 4.0，即刚起步就撑不住），
feature 条件基本稳住（B70 28–64）**——这正是 Treisman & Gelade 的经典分离效应，
说明评分管线确实捕捉到了「feature vs conjunction × 相似度 × 负荷」的交互，而不只是一个总分。

---

## 5. 目录结构

```
JingXueQing_C2A_benchmark/
├── README.md
├── requirements.txt
├── run_eval.py              # CLI 入口（L1）
├── results/                 # 评测输出
└── attnscope/
    ├── __init__.py
    ├── world.py             # 合成世界：6 字段巡检日志 + L1 题目生成（含 100% 可解性保证）
    ├── ladders.py           # L1/L2/L3 题目装配
    ├── scoring.py           # SDT(d′/c/β)、AES 斜率、B70 断点、诱饵捕获率、分半信度
    └── runners.py           # MockRunner（离线冒烟）/ OpenAICompatibleRunner
```

---

## 6. 设计上的刻意取舍

- **固定 token 总量、只变条目密度**：这是与 NIAH / RULER 最关键的分歧。它们操纵**长度**，
  因而混淆了注意力与记忆容量；AttnScope 操纵**信噪比**，把两者解耦。
- **诱饵是「满足目标条件之一」的记录，而不是无关填充文本**：CDV（NeurIPS 2025）已证明
  语义连贯的干扰物杀伤力远高于 filler， filler 型的干扰对今天的模型基本无效。
- **干扰物是参数化的，不是针对单个模型做对抗搜索**：CDV 用树搜索为每个模型定制干扰，
  那样测的是「对某次攻击的脆弱性」，难度不可刻度、结果不可跨模型比较。
- **放弃反应时（RT）指标**：LLM 无人类意义上的 RT；在线人类实验的 RT 噪声也过大。
  代价是失去人类视觉搜索最经典的指标，已在提案中明确声明。
- **L2 的信号 trial 采用「分层布点」而非纯伯努利抽样**：初版用 10% 概率随机放信号，
  实测 200 trial 下只有 14 个信号，导致 10 个十分位箱中有 4 个箱内信号数为 0、d′ 不可估
  （这是原型阶段真实踩到的坑）。改为每箱随机放置等量信号（箱内位置仍随机，保留稀疏感），
  实际信号率提升到 25%，保证每箱 d′ 可估。
- **不测空间注意、毫秒级时序（attentional blink）与内隐注意**：见提案的局限声明。

---

## 7. 已知未做的事（C9 阶段补）

- [ ] L2 / L3 接入 CLI，跑通 400-trial 序列与 3×3 网格
- [ ] ΔS Cascade 的完整评分（L3 变更后执行题已生成，尚未计分）
- [ ] 2×2 解耦的**对照条件**（固定密度、只变长度），用于拆分「注意力损耗」与「记忆容量损耗」
- [ ] 人类基线 Web 界面（与 AI 版同构、同题、同计分）
- [ ] 5% 超高显著探针（诊断用，不计分）
- [ ] 跨种子重测信度

---

## 8. 引用

若使用本代码，请引用提案 `JingXueQing_C2A_proposal.md` 中的参考文献列表。
