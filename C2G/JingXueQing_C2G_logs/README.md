# JingXueQing_C2G_logs — 训练日志目录

> 提交人：JingXueQing（景雪晴）
> 状态更新日期：2026-10-04

---

## ⚠️ 状态：**0 条 8×H100 正式日志 ｜ 3 条真实规模本地日志 + 3 条 tiny 验证日志**

**当前没有 8×H100 的训练日志。** 这不是疏忽，原因如下（可复核）：

| 原因 | 证据 |
|---|---|
| **Level 1 算力券尚未发放** | CHALLENGE.md 规定：券在 `方案草案.md` 审核通过后才发放。本目录随草案一同提交，**先有方案，后有算力** |
| **本机跑不了 8×H100 赛道** | Apple M1 / 8 GB RAM / 无 CUDA。`sysctl` 实测；`torch.cuda.is_available() == False` |
| **FineWeb 数据下载不到** | `huggingface.co` → HTTP 000；`raw.githubusercontent.com` → HTTP 000（本机网络拦截）。实测记录见 `JingXueQing_C2G_AI日志.md` 轮次 5 |

**已完成的替代方案**：3 条 **本机 tiny 管线验证日志**（2026-10-03 23:35–23:38 真实跑出）：

| 文件 | seed | pre-quant BPB | post-quant BPB | ΔTTDS | artifact |
|---|---:|---:|---:|---:|---:|
| `smoke_seed42.log` | 42 | 3.713073 | 3.719371 | +0.055072 | 397,253 B |
| `smoke_seed0.log` | 0 | 3.821949 | 3.837830 | +0.067168 | 397,967 B |
| `smoke_seed1234.log` | 1234 | 3.788499 | 3.799250 | +0.097174 | 396,919 B |

配置：4L×128d / 492,690 参数 / byte-level vocab 256 / 语料 = CPython 3.13 标准库源码 1.52 MB 真实文本 / 约 40 步 20.2 s / Apple M1 CPU。
**用途**：证明 tokenize → train → 滑窗 eval → quantize → compress → BPB → artifact 断言全链路可跑通，`scored tokens == scored bytes`（BPB 分母没算错）。**规模与语料都与正式赛道无关，不可用于任何榜单结论。** 详细解读见 `JingXueQing_C2G_ablation.md` §6。

---

## ✅ 2026-10-04 新增：3 条真实规模本地训练日志（**权重已落盘**）

比上面大一个量级，且这次**权重真的写进了 artifact**（初版的 tar.gz 里没有权重——`pack_artifact` 压出了字节但从未写盘，这是"核心交付物缺失"的根因）。

| 文件 | seed | steps | final loss | pre-quant BPB | post-quant BPB | ΔTTDS | 权重 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `real_seed42.log` | 42 | 127 | 2.27946 | 3.358476 | **3.366591** | +0.027774 | 1,385,031 B |
| `real_seed0.log` | 0 | 125 | 2.28144 | 3.345621 | **3.346589** | +0.011053 | **1,387,394 B → 已打包** |
| `real_seed1234.log` | 1234 | 125 | 2.29391 | 3.370503 | **3.372740** | +0.003416 | 1,386,394 B |
| **mean ± std** | — | — | — | 3.3582 ± 0.0125 | **3.3620 ± 0.0112** | +0.0141 ± 0.0124 | — |

配置：6L×192d×6H/3KV / mlp 3× / **2,042,343 参数** / byte-level vocab 256 / seq_len 256 / eval_stride 64 / CPython 标准库语料 / **180 s/seed** / Apple M1 CPU。

每条日志末尾另附 `[ab]` 行：**同权重、只改 `eval_stride` 的 A/B**（stride 256 / 128 / 64）。结果是滑窗比不滑窗**差 +0.042 BPB，3/3 seed 一致**，与我的主方向相反 —— 详见 `README_提交说明.md` §3.6 与 `JingXueQing_C2G_AAR.md` §8。

> 注：这 3 个文件由构建脚本捕获程序 stdout 后落盘（沙箱阻止子进程直接写入 `~/Desktop`）。内容是程序的完整原始输出，未做任何修改。

---

## 计划中的日志（拿到算力券后 3 个工作日内补齐）

| 文件名 | 配置 | seed | 用途 |
|---|---|---|---|
| `train_seed0.log` | 完整栈（SP8192 + SRD + TTDS + 滑窗 + TTT） | 0 | 主结果 |
| `train_seed42.log` | 同上 | 42 | 主结果 |
| `train_seed1234.log` | 同上 | 1234 | 主结果 |
| `smoke_seed42.log` | tiny 配置，本机 | 42 | 管线验证 |
| `ablation_G0..G7_seed*.log` | 消融 8 组 × 3 seed | 0/42/1234 | 消融证据 |

seed 选择 0 / 42 / 1234 与 PR #1413 一致，便于与公开记录横向对照。

---

## 每条日志必须包含的字段（已写进脚本，不是事后补）

脚本 `JingXueQing_C2G_train_gpt.py` 在每次跑结束时打印一行 JSON，落盘为 `result_seed{N}.json`，同时完整 stdout 落盘为 log。字段包括：

```
run_id, seed, smoke, device, steps, train_seconds, params, vocab_size,
eval_stride, train_seq_len,
pre_quant_bpb, post_quant_bpb,      <- 这两个必须基本相同，否则训练侧被误改
ttds_extra, ttds_bpb,               <- TTDS 开关与结果
ttt_bpb,                            <- Legal score-first TTT
artifact_bytes, artifact_cap, artifact_ok,
srd_enabled, final_train_loss, tokenizer
```

以及 stdout 里的过程信息：

```
[env]    设备 / torch 版本 / seed / 是否 smoke
[tok]    tokenizer 类型与词表大小
[data]   train / val token 数
[model]  层数×维度×头数 / 参数量 / SRD 与 TTDS 的开关状态
step N   loss / extra(本步递归深度) / lr_scale / 已用时间百分比
[train]  总步数 / 训练秒数 / tokens per second
[ema]    EMA 起止
[quant]  GPTQ Hessian 收集的矩阵数
[eval]   pre-quant BPB + nats/tok + **scored tokens + scored bytes**
[eval]   post-quant BPB（同上）
[eval]   TTDS BPB 与 delta
[eval]   TTT BPB 与耗时
[artifact] raw / compressed / code / total 字节数 + 是否超 16MB
[done]   完整 JSON
```

**为什么要把 `scored bytes` 也打出来**：BPB 的分母是字节数，这是最容易算错、且算错**只会让分数变好**的地方。把分母同时写进日志，别人复核我的数字时不必重跑。

---

## 复现命令

```bash
# 本机管线验证（tiny 配置，不需要 GPU / 不需要 FineWeb）
python3 JingXueQing_C2G_train_gpt.py --smoke

# 8×H100 正式跑（单个 seed）
EVAL_STRIDE=64 SRD_ENABLED=1 SRD_EXTRA_CHOICES=1,2 TTDS_ENABLED=1 TTDS_EXTRA=3 \
QK_GAIN_INIT=5.25 TTT_ENABLED=1 TTT_LR=0.005 TTT_EPOCHS=3 \
WEIGHT_DECAY=0.095 MATMUL_LR=0.022 EMA_DECAY=0.9965 \
MAX_WALLCLOCK_SECONDS=560 SEED=42 \
  torchrun --standalone --nproc_per_node=8 JingXueQing_C2G_train_gpt.py
```

`MAX_WALLCLOCK_SECONDS=560`（不是 600）是刻意留的 ~7% buffer——CHALLENGE.md 把「10 分钟踩边」列为常见陷阱。

---

## 校验

拿到日志后第一件事不是提交，是跑：

```bash
python3 JingXueQing_C2G_verify_bpb.py --text <val 文本> --bpb-from-trainer <日志里的 BPB>
```

校验器会独立重算一遍 BPB，并验证「训练出的模型必须优于一个常量 3-gram 模型」。**校验不过，不提交。**
