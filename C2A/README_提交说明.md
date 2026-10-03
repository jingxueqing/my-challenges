# C2A 提交清单 / Submission Index

**作者：** JingXueQing ｜ **赛道：** Track 3 — Attention（注意力）
**截止：** 2026-12-31 23:59（北京时间）

---

## 群内提交用的一句话

> 这是我的 C2A 提案，选择了 Track 3（注意力），核心设计是用「抗干扰负荷阶梯＋效率斜率」替代「找没找到」，
> 并把注意力定义为 KSTAR 中情境采样偏差 ΔS 的入口。欢迎反馈！

---

## 必交文件（挑战书要求）

| 文件 | 状态 | 说明 |
|---|---|---|
| `JingXueQing_C2A_proposal.md` | ✅ | 1498 字；占比 20% / 40% / 16% / 21% |
| `JingXueQing_C2A_AI日志.md` | ✅ | 工作流设计、5 轮文献核验、5 轮压缩、反向举证 |
| `JingXueQing_C2A_拿来说明.md` | ✅ | 17 个来源，逐条写「拿了 / 去掉 / 改了」 |

## 额外文件（依据 rubric.json 的隐藏要求）

交叉比对发现 `rubric.json` 的交付物是 `*proposal*, *benchmark*, *AI日志*, *AAR*`，
且 `reflectionQuality`（AAR 反思）占 **20 分**——挑战书正文只列了 3 个文件。两套都交：

| 文件 | 对应 rubric 维度 |
|---|---|
| `JingXueQing_C2A_AAR.md` | reflectionQuality（20 分） |
| `JingXueQing_C2A_benchmark/` | artifactCompleteness 的「可运行」信号 + `*benchmark*` 交付物 |

---

## 原型怎么跑

```bash
cd JingXueQing_C2A_benchmark
python run_eval.py --runner mock --items-per-cell 50      # 离线冒烟，零依赖
```

详见 `JingXueQing_C2A_benchmark/README.md`。

---

## 迭代路线（鼓励多版本）

```
JingXueQing_C2A_proposal.md      ← v1（当前）
JingXueQing_C2A_proposal_v2.md   ← 根据群内反馈改进
JingXueQing_C2A_proposal_v3.md   ← 再次优化
```

**已知的 v2 候选改进方向**（见 AAR 第 5 节）：
1. 提案只承诺 L1，把 L2/L3 明确写成 v2 路线图（少承诺、多交付）
2. 先做 5–8 人预测试，再谈 40–60 人的正式人类基线
3. 把「相似度」明确写成「诱饵占比（相似度的操作化代理）」，把简化讲在前面
