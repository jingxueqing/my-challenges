# JingXueQing_C2G_leaderboard — BPB 对比表

> 提交人：JingXueQing（景雪晴）
> 数据来源：`openai/parameter-golf` 官方仓库 `records/track_10min_16mb/*/submission.json`（随挑战资料包 `materials/parameter-golf-main.zip` 分发，快照日期 2026-04-10）
> 解析方式：脚本遍历全部记录目录读取 `submission.json`，按 `val_bpb` 升序排序。**数字未经我任何修改。**

---

## 0. 我的位置（先说结论，避免误读）

| | BPB | 状态 |
|---|---|---|
| **我的方案（FineWeb 榜单成绩）** | **—— 尚无 ——** | **未跑。** Level 1 算力券未发放；本机（M1/8GB/无 CUDA）无法执行 8×H100 跑；FineWeb 数据在本机网络下不可下载 |
| 我的方案（设计目标，Stage C3） | ~1.081 ~ 1.083 | `[未测]` 仅为设计预期，**不是成绩** |
| 我的方案（Level 2 承诺，Stage A4） | ~1.1925 | `[未测]`，主方向为滑窗评估，有他人的公开实测作依据 |
| 我的方案（本机 tiny 管线验证） | **3.785 ± 0.059** | `[实测]` smoke 3-seed mean，见 §4。**语料与规模都不同，不可与榜单数字比较** |

**我不把任何未跑的数字写进 `submission.json` 的 `val_bpb` 字段。** 那一格是 `null`。

---

## 1. 官方榜单全量（33 条，按 BPB 升序）

| # | 方案 | 作者 | **BPB** | 日期 |
|---:|---|---|---:|---|
| 1 | SP8192 + 3-Layer Recurrence + Parallel Residuals + Legal TTT | bigbag | **1.0810** | 2026-04-09 |
| 2 | SP8192 + Parallel Residuals + Score-First TTT | aryanbhosale | 1.0822 | 2026-04-08 |
| 3 | SP8192 + QK-Gain 5 + Legal Score-First TTT | dexhunter | 1.0828 | 2026-04-06 |
| 4 | SP8192 + Parallel Residuals + Hessian-Aware SDClip | Robby Sneiderman | 1.0835 | 2026-04-06 |
| 5 | SP8192 + GPTQ Embeddings + Depth Recurrence + SDClip | Kevin Clark | 1.0856 | 2026-04-05 |
| 6 | SP4096 + Depth Recurrence + Parallel Residuals + MuonEq-R | aryanbhosale | 1.0897 | 2026-04-04 |
| 7 | MuonEq-R + Depth Recurrence + WD=0.090 + All-Int6 GPTQ | dexhunter | 1.0912 | 2026-04-03 |
| 8 | 4096-Vocab + Larger Model + High WD + Simplifications | Kevin Clark | 1.0979 | 2026-04-01 |
| 9 | Parallel Residuals + Mini Depth Recurrence | Marko Sisovic | 1.1063 | 2026-03-31 |
| 10 | 11L AR Self-Gen GPTQ + XSA | abaybektursun | 1.1147 | 2026-03-25 |
| 11 | LeakyReLU² + Legal Score-First TTT + Parallel Muon | abaybektursun | 1.1194 | 2026-03-23 |
| 12 | 11L EMA + GPTQ-lite + warmdown3500 | signalrush | 1.1228 | 2026-03-22 |
| 13 | 11L Partial RoPE + LN Scale + EMA + XSA4 | jfprincz | 1.1248 | 2026-03-21 |
| 14 | 11L XSA4 + EMA + Int6 MLP3x | jfprincz | 1.1271 | 2026-03-20 |
| 15 | 11L Efficient Partial XSA | unnir | 1.1307 | 2026-03-20 |
| 16 | 10L Int5-MLP + BigramHash(10240) | thwu1 | 1.1428 | 2026-03-20 |
| 17 | Int6 MLP3x + SmearGate + BigramHash | Raahil Shah | 1.1458 | 2026-03-20 |
| 18 | 11L MLP3x + Int6 QAT | aruniyer | 1.1502 | 2026-03-20 |
| 19 | SmearGate + OrthoInit + Muon WD | aquariouseworkman | 1.1556 | 2026-03-19 |
| 20 | **Ternary Quantization（74M 参数 1/0/−1）** | Ciprian-Florin Ifrim | 1.1570 | 2026-03-24 |
| 21 | 10L Int6 QAT + Zstd MLP2.6x | yahya010 | 1.1586 | 2026-03-19 |
| 22 | Mixed Quant + Sliding Window Eval | aquariouseworkman | 1.1630 | 2026-03-19 |
| 23 | Muon WD + 10 layer | notapplica | 1.1748 | 2026-03-19 |
| 24 | **Sliding Window Eval** | **Matthew Li** | **1.1925** | 2026-03-19 |
| 25 | LoRA TTT | samacqua | 1.1928 | 2026-03-17 |
| 26 | 4k seq length | Spokane Way | 1.2014 | 2026-03-19 |
| 27 | 2048 seq length | Spokane Way | 1.2060 | 2026-03-18 |
| 28 | int6 mixed precision（10L） | Nan Liu | 1.2147 | 2026-03-19 |
| 29 | fp16 Embed | Renier Velazco | 1.2197 | 2026-03-18 |
| 30 | Lower LR | — | 1.2230 | 2026-03-18 |
| 31 | **Naive Baseline（9L/512d/1024vocab/tied/4KV）** | Baseline | **1.2244** | 2026-03-18 |
| — | （另有 2 条 `submission.json` 未含 val_bpb 字段） | — | — | — |

---

## 2. 逐条增量分析（我做的功课）

这是我在写方案前做的第一件事：**把 33 条记录按时间排序，算每一条相对"当时的前一名"的增量**。这样才能判断"哪个方向真的值钱"。

| 跃迁 | Δ BPB | 性质 |
|---|---|---|
| 1.2244 → 1.1925（滑动窗口评估） | **−0.0319** | **纯评估改动，零训练代价** |
| 1.1925 → 1.1748（Muon WD + 10L） | −0.0177 | 优化器 |
| 1.1748 → 1.1630（Mixed Quant） | −0.0118 | 量化 |
| 1.1630 → 1.1556（SmearGate + BigramHash） | −0.0074 | 架构 |
| 1.1556 → 1.1502（Int6 QAT） | −0.0054 | 量化 |
| 1.1502 → 1.1458（MLP3x） | −0.0044 | 架构 |
| 1.1458 → 1.1307（Efficient Partial XSA） | −0.0151 | 架构 |
| 1.1307 → 1.1271（XSA4 + EMA） | −0.0036 | 架构 + 训练 |
| 1.1271 → 1.1248（Partial RoPE） | −0.0023 | 架构 |
| 1.1248 → 1.1228（GPTQ-lite + warmdown） | −0.0020 | 量化 |
| 1.1228 → 1.1194（LeakyReLU² + TTT） | −0.0034 | 激活 + 评估 |
| 1.1194 → 1.1147（AR Self-Gen GPTQ + XSA） | −0.0047 | 量化 |
| 1.1147 → 1.1063（**并行残差 + mini 深度递归**） | **−0.0084** | **架构** |
| 1.1063 → 1.0979（SP4096 + MLP4x + WD） | −0.0084 | 词表 + 架构 |
| 1.0979 → 1.0912（MuonEq-R + 深度递归 + All-Int6） | −0.0067 | 优化器 + 架构 + 量化 |
| 1.0912 → 1.0897（SP4096 栈整合） | −0.0015 | 整合 |
| 1.0897 → 1.0856（**SP8192 词表** + GPTQ 嵌入 + SDClip） | **−0.0041**（词表单项约 −0.0123） | **词表** |
| 1.0856 → 1.0835（并行残差 + Hessian SDClip） | −0.0021 | 架构 |
| 1.0835 → 1.0828（QK-Gain 5 + TTT） | −0.0007（TTT 单项约 −0.0021） | 评估 |
| 1.0828 → 1.0822（并行残差） | −0.0006 | 架构 |
| 1.0822 → 1.0810（3 层递归 + QK-Gain 5.25） | −0.0012 | 架构 |

**三条从这个表读出来的结论：**

1. **收益递减得非常快。** 前 6 条记录（1.2244 → 1.1502）拿走了 −0.074，后面 27 条合起来才 −0.069。**越往后每 0.001 越贵。**
2. **唯一一个"零训练代价"的改动（滑窗评估 −0.0319）是全部记录里收益最大的单条。** 这就是我选它做 Level 1 主方向的全部理由。
3. **榜单已经进入"组合微调"阶段**：最近 8 条记录的增量都在 −0.001 ~ −0.004 之间，且大多是"已有组件的参数微调"（QK-Gain 4.0→5.0→5.25）。这说明**继续在现有栈上堆参数微调的边际收益很低**——要么换思路（评估侧、测试时计算），要么接受 Level 3。

---

## 3. 我的方案在栈上的预期位置

| 配置 | 组成 | 预期 BPB | 依据 | 状态 |
|---|---|---|---|---|
| **Stage A4** | baseline + 滑窗评估 stride=64 | **~1.1925** | Matthew Li 公开实测 −0.0319 | `[未测]` |
| Stage B3 | + SP8192 + MuonEq-R + GPTQ SDClip + EMA | ~1.086 | 对齐 PR #1394 的 1.08563 | `[未测]` |
| Stage C3 | + 深度递归 + 并行残差 + QK-Gain + TTT | ~1.081 ~ 1.083 | 对齐当前 SOTA 1.0810 | `[未测]` |
| **Stage D3（我的原创）** | C3 + **SRD + TTDS** | **未知** | **无依据，纯假设** | `[未测]` |

**关于 D3 我必须说清楚**：前三个阶段的预期值我敢写，是因为它们是**别人的实测数字，我只是复现**。D3 我一个数字都不敢写——它是我的假设，可能正、可能负、可能是 0。

---

## 4. 达成各 Level 需要什么

| Level | 门槛 | 我需要做到 | 是否已达成 |
|---|---|---|---|
| Level 1 Bronze | 复现 1.2244 ±0.005 | 跑通 baseline | ❌ 待算力券 |
| Level 2 Silver | < 1.18 | Stage A4（滑窗评估）单独即可 | ❌ 待算力券 |
| Level 3 Gold | < 1.12 | Stage B3 + C1 左右 | ❌ 约需 $150–300 |
| Level 4 Platinum | < 1.085 | Stage C3 + D3 成立 | ❌ 需独立验证 |

---

## 4. 本机 tiny 管线验证结果 `[实测]`（唯一属于我的真实数据）

**这组数字与上面那张榜单没有任何可比性——语料、词表、规模、硬件全都不同。放在这里只是因为它是我能交出的唯一实测数据。**

| seed | pre-quant BPB | post-quant BPB | TTDS BPB | ΔTTDS | artifact |
|---:|---:|---:|---:|---:|---:|
| 42 | 3.713073 | 3.719371 | 3.774443 | +0.055072 | 397,253 B |
| 0 | 3.821949 | 3.837830 | 3.904999 | +0.067168 | 397,967 B |
| 1234 | 3.788499 | 3.799250 | 3.896424 | +0.097174 | 396,919 B |
| **mean ± std** | **3.7745 ± 0.0548** | **3.7855 ± 0.0592** | **3.8586 ± 0.0684** | **+0.0731 ± 0.0214** | **397,380 B** |

配置：4L×128d / 492,690 参数 / byte-level vocab 256 / 语料 = CPython 3.13 标准库源码 1.52 MB 真实文本 / 40 步 20.2 s / Apple M1 CPU / 滑窗 stride=32。

**为什么 BPB 高达 3.79 而榜单是 1.08？**
1. 词表是 byte-level（256），每个 token 只有 1 字节，模型必须逐字节预测——**同等模型能力下 byte-level 的 BPB 天然远高于 BPE**；
2. 只训了 40 步，模型严重欠训练；
3. 语料是 Python 源码，与 FineWeb 的分布不同。

**它的价值不在数字，在于它证明了链路正确**：`scored tokens == scored bytes`（BPB 分母没算错）、量化后 BPB 变差（方向对）、artifact 397 KB < 16 MB（打包链路通）。详见 `JingXueQing_C2G_ablation.md` §6。

---

## 5. 数据可信度声明

- 上表所有 BPB 数字**逐条来自官方 `submission.json`**，我未做任何四舍五入以外的修改（两位小数处已按原值截断显示，完整值见源文件）。
- 第 2 节的 Δ 列是我用相邻记录**相减算出来的**，属于我的二次加工，不是官方发布值；如果两条记录之间不是严格的继承关系（比如并行提交），该 Δ 只应作为量级参考。**官方 README 里明确写了记录是按 PR 创建时间排序、可能并行提交**，所以这一列请当"方向性参考"用。
- 我自己的数字一格都没有。
