# JingXueQing_C2G_拿来说明

> 「拿来主义」三问：**拿了什么 / 改了什么 / 为什么改。**
> 提交人：JingXueQing（景雪晴）

---

## 0. 总原则

CHALLENGE.md 明确要求：**严禁从零写 Transformer**。这个挑战的正确打法就是站在巨人肩膀上——因为 16MB / 10 分钟的约束下，任何"我自己重写一遍"的部分都是浪费掉的字节和秒数。

我的做法是：**底座整段拿来（不改动），只在我有明确假设的地方动刀。** 下面按来源逐条交代。

---

## 1. 从 `openai/parameter-golf`（官方 repo）拿来

| 拿了什么 | 改了什么 | 为什么改 |
|---|---|---|
| **BPB 的定义与口径**（`bits = nats / ln2`，除以**原始 UTF-8 字节数**） | 封装成 `Tokenizer.bytes_per_token()` 一等公民方法；另写独立校验器 `JingXueQing_C2G_verify_bpb.py` | BPB 的分母是这类任务**最容易算错、且算错会让分数虚假变好**的地方。我把它从"散落在 eval 函数里的一行除法"提升为有显式定义的接口，是为了能被独立复核 |
| **16MB artifact 规则**（code bytes + 压缩后权重，十进制 16,000,000，非 16 MiB） | 训练循环末尾自动断言 `total <= ARTIFACT_CAP`，并把 raw / compressed / code / total 四个数都打进日志 | 挑战文档自己把「超 16MB 却没发现」列为常见陷阱。我让超限变成**运行时硬失败**而不是提交时被拒 |
| **提交格式**（`submission.json` 字段、`records/` 目录结构、3 seed 日志要求） | 沿用，并额外把每一次 eval 的 `scored_bytes` 打进日志 | 官方只要求 BPB；我把分母也记录下来，别人复核我的数字时不必重跑 |
| **Issue #1017 四条合规条件**（因果 / 归一化分布 / 先打分后更新 / 单遍） | 在 `eval_sliding` 的 docstring 里写成 **correctness contract**，逐条说明代码如何满足；TTT 严格写成「先整块 no_grad 打分 → 再训练已打分块」的两阶段 | 「合法性」是这个比赛最容易被误判的地方（CHALLENGE.md 自己都写了 "The validation language around test-time training has been confusing people"）。我把合规从口头承诺变成代码结构 |
| **`data/cached_challenge_fineweb.py` 的数据目录约定**（`fineweb_train_*.bin` / `fineweb_val_*.bin`，uint32 memmap） | 保留该布局作为 full mode 的输入；另加一条 **smoke mode** 分支，从任意本地真实文本构建数据 | 我在本机下载不到 FineWeb。与其让脚本在没数据的机器上完全跑不起来，不如让**同一份代码**能在小数据上端到端自证 |

---

## 2. 从 `karpathy/nanoGPT` + `KellerJordan/Muon` 拿来

| 拿了什么 | 改了什么 | 为什么改 |
|---|---|---|
| **Transformer 的基本骨架**（pre-norm RMSNorm、残差、tied embedding、GQA） | 无实质改动 | 这是公共知识，改它没有收益 |
| **Muon 的 Newton-Schulz 正交化**（系数 a=3.4445, b=−4.7750, c=2.0315，5 步迭代） | 无改动，原样使用 | 这组系数是 Keller Jordan 调优过的，我不觉得自己能调得更好。Jordan 凭这个进的 OpenAI |
| — | 在 Muon 之上加了**行归一化**（`row_rms` 均衡 + 全局均值还原），即 MuonEq-R | 来自 PR #1217（见下）。原始 Muon 对不同 fan-in/fan-out 的矩阵给出量级差异很大的更新，行归一化让更新尺度在矩阵间可比，配合统一的学习率更稳 |

---

## 3. 从历史 top 方案拿来（这是最有价值的部分）

我读了 `records/track_10min_16mb/` 下全部 33 条记录，把它们的 `submission.json` 解析排序，算出每条的增量。下面按**我实际采用**的顺序列出。

### 3.1 PR #705 族 —— 滑动窗口评估（Matthew Li，2026-03-19，1.1925）

- **拿了什么**：核心思想「用重叠窗口前进 stride、只给窗口最右侧 stride 个 token 打分」。
- **改了什么**：
  1. 原实现的窗口边界处理会在尾部留下未打分 token（README 里没写清）。我重写了 `_windows()`，用「按 `end` 枚举窗口」的方式保证**被打分的区间严格连续且不重叠**，并在文档里写成了可验证的契约：打分区间 = `[seq_len−stride, seq_len)`, `[seq_len, seq_len+stride)`, …，最后补一个覆盖 `[E, n)` 的尾部窗口。**每个 token 恰好被打一次分。**
  2. 加了一条性质：`stride == seq_len` 时**数学上退化为原始 baseline**。这让 A/B 变成纯粹的单一旋钮对比，不留"是不是别的地方也变了"的争议空间。
- **为什么改**：这是我 Level 1 的主方向，我要的不只是"抄过来能跑"，而是"我能向评审证明这个增益干净地来自上下文长度"。第 1 条保证分母（字节数）和分子（nats）覆盖同一批 token；第 2 条保证对照组严格。

### 3.2 PR #1394 —— SP8192 + GPTQ 嵌入 + SD-Clip + MuonEq-R（@clarkkev，1.08563）

- **拿了什么**：
  - `c = k · std(row)` 的 SD-Clip 准则（矩阵 int6, k=12.85；嵌入 int8, k=20.0）；
  - GPTQ 量化嵌入矩阵而非 round-to-nearest；
  - 用 `ShuffledSequenceLoader` 取代 PR #726 的互质步长 loader；
  - 词表 4096 → 8192。
- **改了什么**：几乎没改，只把"量化 + 压缩"的路徑拆成 `quantize_model()` / `pack_artifact()` 两个可单独调用的函数，方便我在没 GPU 的情况下单独验证打包字节数。
- **为什么改**（为什么选它当底座）：它的 README 给出了 `H(q) ≈ b − log₂k + const` 的推导，**让我能预判"改 k 会让 artifact 变大还是变小"**，这对 16MB 硬约束是决定性的。别的记录只给结论，它给机制。

### 3.3 PR #1331 / #1437 —— 3 层深度递归（@dexhunter）

- **拿了什么**：循环物理层 3–5，11 物理层 → 17 虚拟层；在训练进度 35% 后启用。
- **改了什么**：**把固定的展开次数 2，改成训练时随机采样 `extra ∈ {1,2}`** —— 这就是我的原创点 [1] SRD。
- **为什么改**：见下节 4.1。核心理由：参数共享让"展开几次"成为一个**零字节代价的旋钮**，而固定深度训练把这个旋钮焊死了。

### 3.4 PR #1204 / #1412 —— 并行残差（@msisovic / @Robby955）

- **拿了什么**：第 7 层起改 GPT-J 式并行残差（attention 和 MLP 读同一个 pre-residual 输入）。
- **改了什么**：无。原样采用，包括"第 7 层起"这个具体分界。
- **为什么没改**：这条我没有更好的假设，硬改只会引入噪声。消融里我会关掉它验证贡献，但不改它的实现。

### 3.5 PR #1413 / #1493 —— QK-Gain（@dexhunter / bigbag）

- **拿了什么**：可学习的 per-head query 缩放，初值从 4.0 → 5.0 → 5.25 单调变好。
- **改了什么**：无。取 5.25。
- **为什么没改**：这是一个已经扫过的单调超参，我复扫一遍的期望收益低于扫 SRD/TTDS。

### 3.6 PR #549 / #1413 —— Legal score-first TTT（@abaybektursun / @dexhunter）

- **拿了什么**：「先对整个 chunk 在 `no_grad` 下打分，再在该 chunk 上做 SGD」的**顺序**；32K chunk、3 epoch、lr=0.005、momentum=0.9、跨 chunk 余弦衰减。
- **改了什么**：
  1. 明确加了 `if ci == n_chunks - 1: break` —— **最后一个 chunk 训练前就退出**，保证不存在"训练了还没打分的 token"。
  2. 把 chunk 的 nats 和 bytes 都从 `eval_sliding` 的返回值取，而不是另算一遍整 chunk 的字节数。
- **为什么改**：第 1 条是合规硬要求（Condition 3），原实现的边界处理在我的读法下有歧义，我宁可保守；第 2 条是防止分母和分子覆盖的 token 集合不一致——这正是最容易产生"虚假增益"的地方。

### 3.7 PR #1019 —— Full-Hessian GPTQ 校准（@abaybektursun）

- **拿了什么**：用校准数据估计每层 `H = XᵀX`，再做 GPTQ 列间误差补偿。
- **改了什么**：
  1. 校准数据**只用训练流**（`ShuffledSequenceLoader` 采样），代码里显式注释 "never the val split"；
  2. 加了 `QUANT_METHOD=gptq|rtn` 开关，rtn 路径用于本机 smoke（MPS/CPU 上 `linalg.inv` 不稳定且慢）。
- **为什么改**：第 1 条是合规（绝不能碰 val）；第 2 条是为了让我能在没 GPU 的机器上验证"量化→反量化→重算 BPB"这条链路。

---

## 4. 我没拿、自己加的部分（原创声明）

### 4.1 [1] SRD —— Stochastic Recurrence Depth

- **是什么**：训练时每一步随机采样递归展开次数（默认 `extra ∈ {1,2}`），而不是固定 2。
- **不是什么**：不是 LayerDrop（LayerDrop 是随机**丢弃**层做正则化；SRD 是随机**加深**，目的是让参数在多个深度上都被优化，从而换取深度方向的外推能力）。
- **灵感来源**：把 stochastic depth 的思想迁移到共享参数的递归块上。我没有在 Parameter Golf 的 33 条记录里见过这个做法——**如果别人做过而我没检索到，欢迎指出，我会在 AI 日志里更正。**
- **代码位置**：`GPT.schedule()` + `train()` 里 `extra` 的采样处，`SRD_ENABLED` / `SRD_EXTRA_CHOICES` 两个开关。

### 4.2 [2] TTDS —— Test-Time Depth Scaling

- **是什么**：评估时把展开次数从 2 提到 3（虚拟层 17 → 20），权重、artifact、训练时长全部不变，只多花评估时间。
- **合法性论证**：见 `JingXueQing_C2G_方案设计.md` §2.3。核心是官方 README 明确训练与评估是两个独立的 600s 预算，且当前 SOTA 评估只用约 500s。
- **与 TTT 的关系**：TTT 是**横向**加测试时计算（用更多 token 适应），TTDS 是**纵向**加测试时计算（用更多深度推理）。递归结构让 TTDS 的参数代价为 0，这是 TTT 没有的优势。
- **代码位置**：`train()` 中 TTDS 分支 + `GPT.forward(extra=)` 参数。

### 4.3 工程性的小改动

| 改动 | 作用 |
|---|---|
| `_windows()` 的连续性契约 + `stride==seq_len` 退化性质 | 让滑窗 A/B 成为干净的单一旋钮实验 |
| `Tokenizer.bytes_per_token()` | 把 BPB 分母变成可复核的接口 |
| 独立校验器 `JingXueQing_C2G_verify_bpb.py` | 用常量 n-gram 模型反算 BPB，防止分母算错 |
| smoke mode（byte tokenizer + 本地真实语料） | 让代码在没 GPU / 没 FineWeb 的机器上也能端到端自证 |
| 日志里同时打 `tokens` 和 `bytes` | 别人复核我的数字时不必重跑 |

---

## 5. 一句话总结

> **底座（架构 + 优化器 + 量化 + 词表）整段拿来，一个参数没动；评估侧拿来了思想但重写了边界处理，让它成为可证明的干净实验；我只在"深度递归"这一个点上动刀，加了 SRD 和 TTDS 两把刀，并且它们是成对设计的——SRD 存在的唯一理由就是让 TTDS 不崩。**

---

## 6.  Attribution（按官方要求）

- `openai/parameter-golf` — scaffold、BPB 定义、提交规范（MIT License，见其 LICENSE）
- `karpathy/nanoGPT` — Transformer 骨架的公共祖先
- `KellerJordan/Muon` — Newton-Schulz 系数
- PR #1394 @clarkkev、#1331/#1437 @dexhunter、#1204 @msisovic、#1412 @Robby955、#549/#1019 @abaybektursun、#1413 @dexhunter、#1493 bigbag、#705 族 Matthew Li、#1217 MuonEq-R、#1445 @X-Abhishek-X（超参 WD=0.095 / MLR=0.022 / EMA=0.9965）
- 上述引用在 `JingXueQing_C2G_train_gpt.py` 文件头注释中逐条列出
