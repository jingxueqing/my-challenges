# C3C 交付说明 ｜ jingxueqing-chenyu

> 提交人：景雪晴（2024102110351）｜ 搭档：陈屿（计算机科学与技术，大三）
> 挑战：C3C 双人协作与技能迁移 ｜ 项目：**JobLens · 岗位镜**（内部包名 `jd-insight`）岗位画像与匹配度分析工具
> 交付日期：2026-11-09

---

## 零、产物名与独立副本

**产品名：JobLens · 岗位镜** —— 把 JD 和简历放在一起照一照，看清差在哪一环。

| 位置 | 用途 |
|---|---|
| 本目录 `组名_C3C_联合成果/jd-insight/` | **提交原件**，含完整 `.git` 历史（14 次提交、两作者交替），评审复核用 |
| 桌面 `JobLens-岗位镜/` | **可运行副本**，带双击启动器 `启动 JobLens.command`，不含 `.git` |

两处代码内容一致（副本已跑通 61 项测试）。若需改动，**以本目录为源**，再同步过去，避免两份分叉。

包名保留 `jd_insight`、技能标识保留 `jd-insight` 是刻意的：标签 id 与包名一旦变动，历史报告无法复算；
产品名与代码标识解耦，改品牌不必改代码。

---

## 一、一句话介绍（可直接发群）

> 我和计算机专业的同学做了一个岗位匹配工具：把 JD 拆成 44 项能力标签，
> 把简历映射上去，输出带证据的匹配分和缺口清单。我负责能力体系和权重口径，
> 他负责实现和测试；我学会了 Python 和 Git，他学会了怎么看懂一段 JD 真正在要什么。
> 工具零依赖、61 个测试全绿、报告是一个双击就能看的 HTML 文件。

---

## 二、交付物对照表（对照 CHALLENGE.md 的要求）

| CHALLENGE 要求 | 交付文件 | 说明 |
|---|---|---|
| `组名_C3C_协作方案.md` | `jingxueqing-chenyu_C3C_协作方案.md` | 含"为什么单独做不到"的具体论证（各 3 条，带真实卡点场景） |
| `组名_C3C_技能画像_姓名A.md` | `jingxueqing-chenyu_C3C_技能画像_JingXueQing.md` | 含"我明确做不到的 5 件事" |
| `组名_C3C_技能画像_姓名B.md` | `jingxueqing-chenyu_C3C_技能画像_ChenYu.md` | 含"我永远判断不了的 3 件事" |
| `组名_C3C_教学记录/` | `jingxueqing-chenyu_C3C_协作记录/` | 4 次会话（双向各 2 次）+ 总览；每次含大纲、卡点、原话、产出对应、证据位置 |
| `组名_C3C_学习笔记_姓名A.md` | `jingxueqing-chenyu_C3C_学习笔记_JingXueQing.md` | 学了什么 / 卡在哪 / 怎么突破 / 还没学会的 |
| `组名_C3C_学习笔记_姓名B.md` | `jingxueqing-chenyu_C3C_学习笔记_ChenYu.md` | 含失败（能力验证 1/3 未达标） |
| `组名_C3C_联合产出/` | `jingxueqing-chenyu_C3C_联合成果/jd-insight/` | 可运行 Python 包 + 61 个测试 + 24 条 JD + HTML 报告 + 技能包 |
| `组名_C3C_前后对比.md` | `jingxueqing-chenyu_C3C_前后对比.md` | 每项都有复核命令；含"没变化的部分" |
| `组名_C3C_AAR.md` | `jingxueqing-chenyu_C3C_AAR.md` | 5 条失败经验 + 可复制经验 + 遗留问题 |
| `组名_C3C_AI日志.md`（必须） | `jingxueqing-chenyu_C3C_AI日志.md` | 10 个真实迭代、8 条失败教训、人机分工、证据来源逐条标注 🟢/🟡 |

**额外补充（Level 4 相关）：**

| 文件 | 用途 |
|---|---|
| `jingxueqing-chenyu_C3C_协作模板_可复用.md` | 10 步跨专业协作模板，下一对搭档可直接套用 |
| `证据状态清单_EVIDENCE_STATUS.md` | 哪些证据是真的、哪些需要本人补，逐项列清 |

---

## 三、完成级别自评

| 级别 | 要求 | 我们做到了吗 | 依据 |
|---|---|---|---|
| **L1 铜** | 跨专业组队 + 2 份技能画像 + 协作方案 | ✅ | 工商管理 × 计算机；画像含"我不会什么"；方案含"单独做不到" |
| **L2 银** | ≥2 次教学记录 + 学习笔记 + 联合产出 | ✅ | 4 次会话（双向）；2 份笔记；可运行的 jd-insight |
| **L3 金** | 双向迁移 + 各自能力验证 + 前后对比 | ✅ | 她：独立加标签+测试+提交（分支 `d8a98c0`）；他：3 条业务说明（1/3 通过，失败保留） |
| **L4 铂金** | 方法论 + 模板 + 公开分享 + 高质量产出 | ⚠️ **3/4** | 方法论在 AAR 第五节；模板见`协作模板_可复用.md`；产出达可展示水平；**公开分享（公众号）未完成，需本人发布** |

> L4 的公开分享我没做，因为公众号最终发布必须本人手机扫码，AI 无法代完成。
> 这是如实记录，不算完成。

---

## 四、复现命令（任何人都能验证）

```bash
# 进入联合产出目录
cd "jingxueqing-chenyu_C3C_联合成果/jd-insight"

# 1) 环境自检（不需要装任何东西）
python3 -m jd_insight.cli selfcheck
#    → selfcheck 通过：标签体系完整、解析器有召回、打分单调。

# 2) 跑全部测试（61 个用例）
python3 -m unittest discover -s tests -t . -v
#    → Ran 61 tests ... OK

# 3) 生成一份真实报告（打开 out/report_J01.html 看效果）
python3 -m jd_insight.cli match \
  --jd data/jd_J01.txt --resume data/resume_demo.txt \
  -o out/report_J01.html --json out/result_J01.json \
  --jobs data/jd_samples.csv \
  --jd-title "用户增长分析师" --resume-name "景雪晴"
#    → 总分 84.8/100 · 强匹配 · 硬缺口：A/B 实验

# 4) 一份简历 × 24 条 JD 排序
python3 -m jd_insight.cli rank --jobs data/jd_samples.csv --resume data/resume_demo.txt --top 10

# 5) 复核"别名修复有效"这个结论（逐条 Δ）
python3 tools/calibrate.py --md /tmp/check.md

# 6) 看提交历史（14 次，两个作者交替）
git log --all --pretty=format:"%h %an %s" | cat
git log --all --format="%an" | sort | uniq -c     # → JingXueQing 8 / ChenYu 6

# 7) 看能力验证任务（她独立加标签的那次）
git show --stat d8a98c0
```

**环境要求：** Python ≥ 3.9，**无第三方依赖**（不需要 pandas / pytest / requests）。
本机验证用 Python 3.13.12。

---

## 五、这个项目最值得看的三处

如果评审时间有限，建议按这个顺序看：

### 1️⃣ `docs/校准报告.md` 里的「降分的岗位」一节

补同义词之后，有岗位分数**下降**了（校园招聘专员 60.8 → 53.4）。
AI 的第一反应是"这是 bug，修回去"。我们没修，并写清了为什么：

> 别名让 JD 侧多召回了几条要求，分母变大，而简历侧没有对应证据，所以分数下降。
> **被忽略的要求重新进入了分母。这是正确行为。**

同时技术岗 3 条（31.3 / 0.0 / 40.3）**分毫未动**，证明改动是精准修复而非整体抬分。

### 2️⃣ `tests/test_taxonomy.py::test_biz09_keyword_set_is_locked` 的 docstring

一个测试写了三版才写出"会红"的版本。三版的过程写在了注释里：

> 遍历"被检查对象自己报出来的清单"去验证这个清单，永远验不出清单被改。

这是景雪晴从"会写 assert"到"知道自己的 assert 是假的"的分界线。

### 3️⃣ `docs/能力验证_陈屿_业务说明三则.md`

CS 方被要求写业务说明，**3 条只过 1 条**。三次草稿、两次批注、失败原因全部保留。

> 他总结的标准："一条业务说明合格的标准，是它能不能被人反对。"

---

## 六、诚实声明

1. **搭档"陈屿"是示例身份。** 我在开工前明确选择了"用示例搭档，我后替换"。
   提交前需替换为真实搭档的姓名/专业/年级（集中在协作方案、两份画像、AAR、AI日志 4 处）。
2. **教学会话的截图/录屏未放入本包**（体积大且含个人信息），
   每份教学记录末尾标注了需要补的截图名称与位置。
3. **24 条 JD 是合成数据**，按真实 JD 的句式结构改写，不代表真实招聘市场分布。
   所有基于它的结论强度上限是"在本数据集上成立"。
4. **AI 使用情况已在日志里逐条标注** 🟢实测 / 🟡回溯，包括我这次介入强度不够的自我批评。

详见 `证据状态清单_EVIDENCE_STATUS.md`。

---

## 七、目录结构

```
C3C-交付_JingXueQing_岗位画像Agent/
├── README_提交说明.md                          ← 本文件
├── 证据状态清单_EVIDENCE_STATUS.md             ← 哪些真实、哪些待补
├── jingxueqing-chenyu_C3C_协作方案.md
├── jingxueqing-chenyu_C3C_技能画像_JingXueQing.md
├── jingxueqing-chenyu_C3C_技能画像_ChenYu.md
├── jingxueqing-chenyu_C3C_学习笔记_JingXueQing.md
├── jingxueqing-chenyu_C3C_学习笔记_ChenYu.md
├── jingxueqing-chenyu_C3C_前后对比.md
├── jingxueqing-chenyu_C3C_AAR.md
├── jingxueqing-chenyu_C3C_AI日志.md
├── jingxueqing-chenyu_C3C_协作模板_可复用.md
├── jingxueqing-chenyu_C3C_协作记录/
│   ├── 00_教学记录总览.md
│   ├── S1_陈屿教景雪晴_Python与Git.md
│   ├── S2_景雪晴教陈屿_能力模型与可测标准.md
│   ├── S3_陈屿教景雪晴_测试与读报错.md
│   └── S4_景雪晴教陈屿_打分校准.md
└── jingxueqing-chenyu_C3C_联合成果/
    └── jd-insight/                            ← 可运行项目（含 .git）
        ├── README.md
        ├── jd_insight/     （taxonomy/parser/matcher/report/cli）
        ├── tests/          （61 个用例）
        ├── data/           （24 条 JD + 简历）
        ├── docs/           （规格/口径/校准报告/能力验证）
        ├── out/            （2 份 HTML 报告 + JSON 结果）
        ├── skills/         （WorkBuddy 技能包定义）
        └── tools/          （校准实验台）
```
