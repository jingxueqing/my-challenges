# C2G 参数高尔夫 —— 提交说明

> 提交人：**JingXueQing（景雪晴）**｜学号 **2024102110351**
> 挑战：C2G 参数高尔夫 —— 极限约束下的语言模型训练（OpenAI Parameter Golf）
> 提交日期：2026-10-03（**2026-10-04 补齐：AAR + 真权重 artifact + 3 seed 实测**）
> 交付目录：`~/Desktop/挑战_C2G 参数高尔夫 _JingXueQing/`

---

## 1. 一句话介绍（发群用）

> 做 C2G 参数高尔夫，我先把榜单 33 条记录全解析了一遍算出每个方向的真实增量，发现**史上收益最大的单组件改动是"滑动窗口评估"（−0.0319 BPB，零训练代价）**——所以我 Level 1 的主方向选的是改"尺子"而不是改模型；在此之上我提了两个原创点：**SRD（训练时随机采样递归展开深度）** 和 **TTDS（评估时加深展开，零字节代价）**，它们是成对设计的。目前**尚未跑 8×H100（算力券未发放、本机是 M1/8GB、FineWeb 下载不到），所以我不填任何 BPB 数字，方案草案 + 设计 + 消融协议 + 完整训练脚本已就绪，拿到券即可开跑。**

---

## 2. 交付物对照表

| # | 要求文件 | 实际文件 | 状态 | 说明 |
|---|---|---|---|---|
| 1 | `姓名_C2G_方案草案.md` | `JingXueQing_C2G_方案草案.md` | ✅ | ~2,600 字（要求 ≥500），回答 4 个门槛问题 |
| 2 | `姓名_C2G_方案设计.md` | `JingXueQing_C2G_方案设计.md` | ✅ | 目标 Level / 技术选型 / 实验矩阵 / 风险登记 |
| 3 | `姓名_C2G_train_gpt.py` | `JingXueQing_C2G_train_gpt.py` | ✅ | ~700 行，已通过 `py_compile`；含 SRD + TTDS |
| 4 | `姓名_C2G_submission.tar.gz` | `JingXueQing_C2G_submission.tar.gz` | ✅ | **1,408,593 B，含代码 + 真实压缩权重（1,387,394 B，seed 0）+ tokenizer + MANIFEST（sha256）** |
| 5 | `姓名_C2G_submission.json` | `JingXueQing_C2G_submission.json` | ✅ | 赛道 `val_bpb` 仍为 `null`（未跑 8×H100）；新增 `val_bpb_measured_local` = **3.3620 ± 0.0112（3 seed 实测）** |
| 6 | `姓名_C2G_logs/` | `JingXueQing_C2G_logs/` | ⚠️ | **3 条 2026-10-04 真实规模日志（125–127 步 / 2.04M 参数）＋ 3 条 tiny smoke 日志**；仍 **0 条 8×H100 正式日志** |
| 7 | `姓名_C2G_ablation.md` | `JingXueQing_C2G_ablation.md` | ✅ | 8 组消融设计 + **先验登记**（跑前写下、跑后不改） |
| 8 | `姓名_C2G_leaderboard.md` | `JingXueQing_C2G_leaderboard.md` | ✅ | 33 条官方记录全量 + 逐条增量分析 |
| 9 | `姓名_C2G_AI日志.md` | `JingXueQing_C2G_AI日志.md` | ✅ | 11 个真实轮次 + 6 条失败经验 + 人机分工 |
| 9b | **`*AAR*`（challenge.json 四项必交之一）** | `JingXueQing_C2G_AAR.md` | ✅ | 七维复盘。**注：`CHALLENGE.md` 的表格漏列了 AAR，但 `challenge.json` / `challenge.yaml` / `挑战总览.csv` 的 `required_deliverables` 都含 `*AAR*`** |
| 10 | `姓名_C2G_拿来说明.md` | `JingXueQing_C2G_拿来说明.md` | ✅ | 逐条：拿了什么 / 改了什么 / 为什么改 |
| 11 | （额外）BPB 校验器 | `JingXueQing_C2G_verify_bpb.py` | ✅ | 独立重算 BPB，防"分母算错导致虚假增益" |
| 12 | （额外）本说明 | `README_提交说明.md` | ✅ | |
| — | Level 4 的 `tech_report.pdf` | — | ❌ | **未提交**：Level 4 尚未达成，我不会先写一份没有实验支撑的"技术报告" |

---

## 3. 核心内容摘要

### 3.1 主方向：滑动窗口评估（评估侧，不是模型侧）

我把官方 `records/` 下 33 条记录的 `submission.json` 全部解析、按时间排序、算相邻增量。**单组件收益 Top 4：**

| 方向 | Δ BPB | 代价 |
|---|---|---|
| **滑动窗口评估** | **−0.0319** | **零训练代价** |
| SP8192 词表 | −0.0123 | 重训 + 重做 tokenizer |
| 并行残差 + 深度递归 | −0.0084 | 重训 + 架构改动 |
| MuonEq-R + All-Int6 | −0.0067 | 重训 + 量化管线 |

**决定性证据**：那条记录（Matthew Li, 2026-03-19）的 **pre-quant BPB 是 1.2196，比 baseline 的 1.2172 还略差**，而 post-quant 是 1.1925 vs 1.2244。**模型一点没变好，分数好了 0.032** —— 说明 baseline 那个 1.2244 里有相当一部分根本不是模型的问题，是**测量方式**的问题。

机制：baseline 把 val 切成不重叠的 1024-token 块，每块第一个 token 上下文为 0，**平均每个 token 只有 ~512 上下文**，而训练时是满窗 1024。滑窗以 stride=64 前进、只给最右侧 64 个 token 打分（上下文 ≥960），**每个 token 仍然只打一次分**（满足单遍要求）。

### 3.2 两个原创点（成对设计）

| | SRD | TTDS |
|---|---|---|
| 是什么 | 训练时**随机采样**递归展开次数 `extra ∈ {1,2}`，而不是固定 2 | 评估时把展开从 2 提到 3（17 → 20 虚拟层） |
| 代价 | 0 参数、0 字节、~5–8% 步时间 | 0 参数、0 字节、**0 训练秒**，只花评估预算 |
| 单独预期 | **略变差**（+0.001~0.003） | **明显变差**（train/test 失配） |
| 存在理由 | **它是给 TTDS 交的保险费**，不是自己的收益来源 | 真正想要的效果 |

洞察：现有深度递归把"展开几次"这个**零字节代价的旋钮**焊死了。SRD 的作用是让模型在多个深度上都优化过，从而让 TTDS 的外推落在一条更平缓的曲线上。

**我预先登记了预期（见 ablation.md §3），跑完照单对照，预期错了就写错了，不回头改。**

### 3.3 诚实口径（全文统一）

所有数字带来源标签，绝不混用：

| 标签 | 含义 |
|---|---|
| `[引用]` | 官方记录里他人已公开的成绩，附路径 |
| `[实测]` | 本人跑出来的，附日志文件 |
| `[未测]` | 设计预期，**不构成任何成绩声明** |

### 3.4 已实测：本机 tiny 管线验证（3 seed，2026-10-03 23:35–23:38）

| seed | pre-quant BPB | post-quant BPB | ΔTTDS | artifact |
|---:|---:|---:|---:|---:|
| 42 | 3.713073 | 3.719371 | +0.055072 | 397,253 B |
| 0 | 3.821949 | 3.837830 | +0.067168 | 397,967 B |
| 1234 | 3.788499 | 3.799250 | +0.097174 | 396,919 B |
| **mean ± std** | **3.7745 ± 0.0548** | **3.7855 ± 0.0592** | **+0.0731 ± 0.0214** | **397,380 B** |

配置：492,690 参数 / byte-level vocab 256 / CPython 标准库源码 1.52 MB 真实语料 / 约 40 步 20.2 s / M1 CPU。
**用途**：证明链路正确（BPB 分母 `scored tokens == scored bytes`、量化方向正确、artifact 打包通），**不是榜单成绩**。
顺带初步支持了我预先登记的假设 H3：**评估时展开深度超过训练深度会让 BPB 变差（3/3 seed 同向）**。

### 3.5 已实测：2026-10-04 真实规模本地训练（3 seed）

比 §3.4 大一个量级，且**权重真的落盘了**（这就是 §2 第 4 项从"无权重"变成"有权重"的来源）。

**配置**：6L × 192d × 6H/3KV · mlp 3× · **2,042,343 参数** · byte-level vocab 256 · seq_len 256 · CPython 标准库语料 1.5 MB · 180 s/seed · 125–127 步 · Apple M1 CPU。

| seed | steps | final loss | pre-quant BPB | **post-quant BPB** | ΔTTDS | 权重 |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | 127 | 2.27946 | 3.358476 | **3.366591** | +0.027774 | 1,385,031 B |
| 0 | 125 | 2.28144 | 3.345621 | **3.346589** | +0.011053 | 1,387,394 B |
| 1234 | 125 | 2.29391 | 3.370503 | **3.372740** | +0.003416 | 1,386,394 B |
| **mean ± std** | — | — | 3.3582 ± 0.0125 | **3.3620 ± 0.0112** | **+0.0141 ± 0.0124** | — |

日志：`JingXueQing_C2G_logs/real_seed{42,0,1234}.log`。`scored bytes == scored tokens` 在全部 9 次评估中都成立（BPB 分母没算错）。
ΔTTDS 3/3 seed 同向为正，**再次支持预先登记的 H3**（评估时展开超过训练深度会变差）。

### 3.6 ⚠️ 一个我不喜欢的实测结果：滑窗评估在本机规模下是**变差的**

同权重、只改 `eval_stride` 的直接 A/B（stride == seq_len 即"不滑窗"，也就是 baseline 的做法）：

| eval_stride | seed 42 | seed 0 | seed 1234 | mean |
|---:|---:|---:|---:|---:|
| 256（**不滑窗** = baseline 口径） | 3.321875 | 3.306959 | 3.331905 | **3.320246** |
| 128 | 3.359315 | 3.339898 | 3.365371 | 3.354861 |
| 64（滑窗） | 3.366591 | 3.346589 | 3.372740 | **3.361973** |

**3/3 seed 一致：滑窗比不滑窗差 +0.042 BPB，且单调。** 这与我在 §3.1 选的主方向**相反**。

我不打算把它藏起来，也不打算因为它难看就改口。我的判断是：**它既不足以推翻榜单证据，也足以让我不能再说"本地已验证"。**

- **不足以推翻**：榜单那条 −0.0319 是别人在 seq_len 8192、完整训练规模下的实测；我这里 seq_len 只有 256、模型只训了 125 步（loss 2.28）。**两者不在同一个尺度上，不能直接对冲。**
- **足以警告**：滑窗收益很可能**是尺度相关的**——需要模型"会利用长上下文"才兑现。一个训了 125 步的模型大概率不会。
- **我没能排除的另一种可能**：`_windows` 的尾窗处理、或训练/评估的上下文深度分布失配，属于实现层面的假象。**在拿到 8×H100 之前我无法区分这两种解释，所以我把它记为"未决"，不记为"结论"。**

**这对计划的实际影响**：`方案设计.md` 里的 **G0 校准闸门**（先量 stride=1024，量不到 −0.03 ± 0.005 就 debug、不往下走）从"稳妥"升级为**必须**。如果滑窗在大尺度上也不兑现，整个 Level 1 路线要换——**现在知道这一点，比烧掉 $13 之后才知道便宜得多。**

---

## 4. 复现命令

```bash
cd ~/Desktop/C2G-交付_JingXueQing_参数高尔夫

# ① 本机管线验证（tiny 配置，真实语料，不需要 GPU / 不需要 FineWeb）
python3 JingXueQing_C2G_train_gpt.py --smoke

# ② Level 1 主方向 A/B（同一份 checkpoint，只换 stride —— 不用重训）
EVAL_STRIDE=1024 MAX_WALLCLOCK_SECONDS=560 SEED=42 \
  torchrun --standalone --nproc_per_node=8 JingXueQing_C2G_train_gpt.py
EVAL_STRIDE=64 MAX_WALLCLOCK_SECONDS=560 SEED=42 \
  torchrun --standalone --nproc_per_node=8 JingXueQing_C2G_train_gpt.py

# ③ 完整栈 + SRD + TTDS
EVAL_STRIDE=64 SRD_ENABLED=1 SRD_EXTRA_CHOICES=1,2 TTDS_ENABLED=1 TTDS_EXTRA=3 \
QK_GAIN_INIT=5.25 TTT_ENABLED=1 TTT_LR=0.005 TTT_EPOCHS=3 \
WEIGHT_DECAY=0.095 MATMUL_LR=0.022 EMA_DECAY=0.9965 \
MAX_WALLCLOCK_SECONDS=560 SEED=42 \
  torchrun --standalone --nproc_per_node=8 JingXueQing_C2G_train_gpt.py

# ④ BPB 校验（拿到日志后第一件事）
python3 JingXueQing_C2G_verify_bpb.py --text <val 文本> --bpb-from-trainer <BPB>
```

依赖：`torch>=2.3`、`numpy`、`sentencepiece`（仅 SP8192 路径需要）、`brotli`（可选，缺省回退 zlib）。
数据：`python3 data/cached_challenge_fineweb.py --variant sp8192`（**本机网络下载不到**）。

---

## 5. 我主动没做的事（以及为什么）

| 没做 | 为什么 |
|---|---|
| **填赛道 BPB 数字** | 没跑 8×H100 就是没跑。一个编出来的 1.08 能骗过评审一天，骗不过任何人重跑一次。**本机实测的 3.3620 我照填，但明确标注了它是 2.04M 参数 / byte vocab / CPython 语料下的数字，不是赛道成绩** |
| **编造 3 份训练日志** | 同上。宁可交"0 条日志 + 说明"，也不交 3 份假日志 |
| **写 Level 4 的 tech report PDF** | 没有实验支撑的"技术报告"只是作文。Level 4 达成后再写 |
| **改底座的一个参数** | PR #1394 那一整套（SP8192 / MuonEq-R / GPTQ SDClip）我原样拿来——我没有更好的假设，硬改只会引入噪声 |

---

## 6. 拿到算力券后的 72 小时计划

| 时间 | 动作 |
|---|---|
| 第 1 小时 | **E0 环境校验**（1×H100，$2.5）。10 分钟约束下，一次白跑 = 1/7 预算 |
| 第 2–3 小时 | E1 baseline 复现 + E2 stride 扫描（复用同一 ckpt，最省钱的设计） |
| 第 4–6 小时 | 3 seed 确认 + 合规自检 + BPB 校验器对照 |
| 之后 | Stage B/C 组合；Stage D（SRD/TTDS 消融） |

预算：A 组约 $13，全流程约 $80（低于 CHALLENGE.md 估的 $150–500，主要靠"复用 checkpoint 扫评估超参"）。

---

## 7. 目录结构

```
挑战_C2G 参数高尔夫 _JingXueQing/
├── README_提交说明.md                  ← 本文件
├── JingXueQing_C2G_方案草案.md          ★ Level 1 算力申请门槛文件
├── JingXueQing_C2G_方案设计.md
├── JingXueQing_C2G_train_gpt.py        ★ 训练脚本
├── JingXueQing_C2G_verify_bpb.py       ★ 独立 BPB 校验器
├── JingXueQing_C2G_submission.json     ★ 含 val_bpb_measured_local + stride_ablation_local
├── JingXueQing_C2G_submission.tar.gz   ★ 含真实权重（1,387,394 B）+ tokenizer + MANIFEST
├── JingXueQing_C2G_tokenizer.json
├── JingXueQing_C2G_ablation.md
├── JingXueQing_C2G_leaderboard.md
├── JingXueQing_C2G_AI日志.md            ★ 评审必看
├── JingXueQing_C2G_AAR.md               ★ 复盘（challenge.json 四项必交之一）
├── JingXueQing_C2G_拿来说明.md
└── JingXueQing_C2G_logs/
    ├── README.md
    ├── real_seed42.log  real_seed0.log  real_seed1234.log   ← 2026-10-04，2.04M 参数
    └── smoke_seed42.log smoke_seed0.log smoke_seed1234.log  ← 2026-10-03，492K 参数
```
