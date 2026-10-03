# AttnScope：用「抗干扰效率阶梯」衡量机器注意力

**赛道 / Track:** Track 3 — Attention（注意力）
**作者 / Author:** JingXueQing
**日期 / Date:** 2026-10-03 ｜ 版本：v1

---

## 1. 赛道选择与动机

五个赛道中，Attention 是唯一**没有专属 benchmark** 的：其余四者分别有 ARC/SCAN、校准指标、规划任务、ToM 系列；注意力只能借用长上下文检索——NIAH、RULER、LongBench 测的是「记忆窗口有多大」，不是「能否在噪声中锁定信号」。DeepMind 已将其列为独立基础能力，社区却无对应评测。

这个缺口正转为可靠性风险：RULER（COLM 2024）显示 17 个模型全部通过 NIAH，仅约一半能在 32K 撑住；CDV（NeurIPS 2025）显示，加入语义连贯但无关的上下文，模型准确率平均掉 45%。而行业把「上下文窗口更大」当进步叙事，Lost in the Middle（TACL 2023）却证明「装得下」不等于「用得上」——缺一把尺子，这个错觉就会持续。

**KSTAR 连接。** 注意力是 KSTAR 中 **S（情境评估）的入口闸门**，决定 S 里有什么。我定义 **ΔS = S_model − S_true**，成因只有三种：该看的没看进去（选择失败）、中途丢了（维持失败）、情境变了没更新（更新失败）。ΔS 须与 ΔR 区分：ΔR 是行动后偏差，可被下游纠正掩盖；ΔS 是行动前采样偏差，不可掩盖，且沿 K→S→T→A→R 放大。Learning 测「能否更新 K」，Metacognition 测「能否预测 ΔR」，Attention 测「S 是否被正确采样」——S 错了，K 再准也无济于事。这是循环的底座。

## 2. Benchmark 设计思路

**范式转换。** 认知科学六十年从不只用「命中率」衡量注意力，而用**效率如何随干扰负荷下降**（Treisman & Gelade, 1980 的 set-size 斜率）。现有 AI benchmark 只报「找没找到」，AttnScope 报「**在多大的干扰负荷下还能找到**」。

**L1 选择性阶梯（过滤）。** 在程序化生成的虚构「仓库巡检日志」（每条 6 字段：ID／类别／数值／状态／时间戳／库位，实体名与数值全随机以杜绝预训练记忆，借鉴 ARC 与 CogBench）中定位满足复合条件的唯一记录，两个正交自变量：
- **干扰相似度**：从「目标在单一字段上独一无二」（feature／pop-out）连续调到「目标只在字段组合上唯一」（conjunction），按 Duncan & Humphreys (1989) 取 0.2→0.9 连续梯度。
- **干扰密度**：条目数 N ∈ {4,8,16,32,64}，但 **token 总量恒定**（条目增多则每条变短）。

这个 **2×2 解耦**是核心：主条件固定长度、只变密度以隔离注意力；对照条件固定密度、只变长度以复现 RULER 的长度效应。两者之差即「纯注意力损耗」。

**L2 持续性阶梯（维持）。** 数百个串行 trial，目标事件稀疏出现（Mackworth, 1948 的 vigilance 范式；原型取 400/25%，见代码 README）；按十分位分箱生成命中率／误报率的位置剖面，对标 Lost in the Middle 的 U 型曲线。AI 无生理疲劳，但上下文累积可能造成功能性 vigilance 衰减。

**L3 变化觉察阶梯（更新）。** 呈现合成文档 D 与修订版 D′（含 0 或 1 处变更，显著性 × 长度各三档），任务为「是否变化＋变化在哪」；并追加**基于变更后情境的执行题**——未察觉变更者会基于过期 S 给出系统性错误的 A，可视化 ΔS→ΔT→ΔA 的放大。

**指标体系（全部非「准确率」）：**

| 指标 | 定义 | 测量什么 |
|---|---|---|
| AES 效率斜率 | 正确率对 log₂N 的回归斜率 | 抗干扰效率 |
| B70 断点 | 正确率跌破 70% 时的负荷值 | 可承受的干扰上限 |
| Lure Capture | 选中「最相似诱饵」的比例 | 是被误导，还是没找到 |
| d′ / β（SDT） | 辨别力 / 判断标准 | 分离敏感性与响应偏向 |
| ΔS Cascade | L3 二次任务错误率 | 注意缺陷沿 KSTAR 的放大 |

**隔离性。** 答案只需「定位＋复制」，无多步推理；分数以 N=4 零干扰基线做 **within-subject 标准化**，报告「损耗」而非绝对值；规则全程不变，不涉及策略切换（属 Track 4）；材料全随机防污染，d′/β 分解使「全答无变化」这类策略得 0。

**灵感来源：** 认知科学侧见 Treisman & Gelade (1980)、Duncan & Humphreys (1989)、Posner (1980)、Mackworth (1948)、Rensink et al. (1997)、Green & Swets (1966)；工程侧见 NIAH／RULER、CDV、CogBench。

## 3. 人类基线考量

**预期分布**（成人 40–60 名，在线、约 25 分钟、within-subject）：

| 阶梯 | 指标 | 成人中位（预期范围） |
|---|---|---|
| L1-feature | AES 斜率 | ≈ −0.01（−0.03～0.00），pop-out，几乎不受负荷影响 |
| L1-conjunction | AES 斜率 | ≈ −0.09（−0.14～−0.05），显著衰减 |
| L1-conjunction | B70 | N ≈ 16–24 |
| L2 | vigilance 衰减（末十分位 d′ − 首十分位 d′） | −0.8 ～ −1.2 |
| L3 | d′（高显著 / 低显著） | 2.4 / 0.9；约 20–40% 被试至少出现一次 change blindness |

**AI 侧预测：** feature 条件接近满分；conjunction 条件出现**模型间分化**（区分度来源）；L2 出现 U 型剖面；L3 的 β 向「没变化」偏移。

**区分度保障。** 采用**自适应阶梯＋断点计分**：从 N=4 起加压，直到跌破 70% 或 N=64 封顶——起点极简无地板效应，不设上限无天花板效应。得分为「能承受多大干扰负荷」，可跨人类与模型比较，且因保留零干扰基线而不受基础能力差异污染。

**局限：** 不测空间注意、毫秒级时序（attentional blink）与内隐注意；在线环境反应时不可靠，故放弃人类侧经典的 RT 斜率指标。

## 4. 预期创新点与可行性

**创新点。** ① **范式转换**：把认知科学的「负荷阶梯＋效率斜率」引入 AI 注意力评测，从「能否找到」转向「在多大的干扰下还能找到」。② **2×2 解耦**：分离「干扰密度」与「上下文长度」，把注意力从记忆容量中剥离——现有 benchmark 只操纵长度，二者始终混淆。③ **指标升级**：以 d′/β＋诱饵捕获率＋断点替代准确率，分离敏感性与判断标准，区分「没找到」与「被误导」。④ **ΔS 对齐 KSTAR**：三阶梯对应 S 采样偏差的选择／维持／更新三成因，并测量其向下游放大，输出「注意力剖面」而非单一分数，可接入 DeepMind 十维雷达图。相较 CDV 用参数化相似度阶梯取代对抗式树搜索，相较 RULER/NIAH 把操纵变量从长度换成信噪比。

**可行性（7 天）。** 纯文本、无训练、只需 API 推理：生成器 1.5 天；评测驱动 1 天；评分库 0.5 天；3–5 个前沿模型测试 1 天；人类基线（40–60 人）1.5 天；文档与提交 1 天；缓冲 0.5 天。

**资源与风险。** 约 200–400 万 input tokens，无 GPU；本人可独立完成，理想 2 人分工；被试 40–60 名，自愿匿名。主要风险为人类样本不足（下限 25 人，低于则只报分布）与 API 成本（每条件 60–80 trial）。

---

## 参考文献 / References

1. Burnell, R., Yamamori, Y., Firat, O. et al. (2026). Measuring Progress Toward AGI: A Cognitive Framework. Google DeepMind.
2. Treisman, A. & Gelade, G. (1980). A feature-integration theory of attention. *Cognitive Psychology*, 12(1), 97–136.
3. Duncan, J. & Humphreys, G. (1989). Visual search and stimulus similarity. *Psychological Review*, 96(3), 433–458.
4. Posner, M. I. (1980). Orienting of attention. *Quarterly Journal of Experimental Psychology*, 32(1), 3–25.
5. Mackworth, N. H. (1948). The breakdown of vigilance during prolonged visual search. *QJEP*, 1(1), 6–21.
6. Rensink, R. A., O'Regan, J. K. & Clark, J. J. (1997). To see or not to see: The need for attention to perceive changes in scenes. *Psychological Science*, 8(5), 368–373.
7. Simons, D. J. & Levin, D. T. (1997). Change blindness. *Trends in Cognitive Sciences*, 1(7), 261–267.
8. Green, D. M. & Swets, J. A. (1966). *Signal Detection Theory and Psychophysics*. Wiley.
9. Hsieh, C.-P. et al. (2024). RULER: What's the Real Context Size of Your Long-Context Language Models? *COLM 2024* (arXiv:2404.06654).
10. Liu, N. F. et al. (2023). Lost in the Middle: How Language Models Use Long Contexts. *TACL* (arXiv:2307.03172).
11. Huang, Y. et al. (2025). Breaking Focus: Contextual Distraction Curse in Large Language Models. *NeurIPS 2025* (arXiv:2502.01609).
12. Coda-Forno, J., Binz, M., Wang, J. X. & Schulz, E. (2024). CogBench: A Large Language Model Walks into a Psychology Lab. *ICML 2024* (arXiv:2402.18225).
13. Bai, Y. et al. (2023). LongBench: A Bilingual, Multitask Benchmark for Long Context Understanding. *EMNLP 2023* (arXiv:2308.14508).
14. Chollet, F. (2019). On the Measure of Intelligence. arXiv:1911.01547.
15. Kamradt, G. (2023). Needle In A Haystack — Pressure Testing LLMs.
