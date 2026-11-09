# JobLens · 岗位镜

> 把 JD 和简历放在一起照一照，看清你差在哪一环。

**v1.2** ｜ 岗位画像与匹配度分析 ｜ 纯标准库，零依赖，Python ≥ 3.9

把一份 JD 拆成可量化的能力向量，把一份简历映射上去，输出**可解释、可溯源**的匹配报告。
定位：投递前的自查清单 + 岗位横向排序。**不是**自动筛选器。

**最快的用法：双击本目录下的 `启动 JobLens.command`**，它会自检、重算示例报告并直接打开。

> 内部包名仍是 `jd_insight`（`python3 -m jd_insight.cli …`）。
> 这是有意的：包名与标签 id 一旦改动，历史报告就无法复算，品牌名和代码标识不该互相绑死。

C3C 联合产出 ｜ 工商管理 × 计算机

| 角色 | 姓名 | 负责 |
|---|---|---|
| 业务与体系 | JingXueQing（工商管理） | 44 项能力标签体系、权重校准口径、验收标准、样例 JD 标注 |
| 工程与实现 | ChenYu（计算机科学与技术） | 模块拆分、解析与打分算法、测试、CLI 与技能包封装 |

![report](out/report_J01.html)

---

## 30 秒跑起来

不需要安装任何第三方库（**纯标准库**，Python ≥ 3.9）。

```bash
cd "JobLens-岗位镜"

# 1) 自检：确认环境和标签体系都正常
python3 -m jd_insight.cli selfcheck

# 2) 单条 JD × 一份简历 → 生成 HTML 报告
python3 -m jd_insight.cli match \
  --jd data/jd_J01.txt \
  --resume data/resume_demo.txt \
  -o out/report_J01.html \
  --json out/result_J01.json \
  --jobs data/jd_samples.csv \
  --jd-title "用户增长分析师" --resume-name "景雪晴"

# 3) 一份简历 × 24 条 JD → 岗位排名
python3 -m jd_insight.cli rank --jobs data/jd_samples.csv --resume data/resume_demo.txt --top 10

# 4) 看标签体系
python3 -m jd_insight.cli taxonomy
```

打开 `out/report_J01.html` 即可看到报告（单文件，可直接发邮件）。

## 跑测试

```bash
python3 -m unittest discover -s tests -t . -v      # 零依赖
pytest tests/ -v                                    # 装了 pytest 也能直接跑（等价）
```

当前：**61 个用例全部通过**（含 7 个 CLI 端到端用例）。

---

## 它到底怎么算

```
JD 文本 ──parser──▶ 标签命中（带原句证据）
                      │
                      ▼
              需求向量 w_i （Σw=1）
                      │
简历文本 ──parser──▶ 供给集合
                      │
                      ▼
        total = 100 × Σ ( w_i × c_i )
        c_i = 0（未命中）｜0.85（命中 1 次）｜1.0（命中 ≥2 次）
        w_i = weight_default × 次数增益 × 段落系数(必需 1.0 / 加分 0.5)
```

三条校准决策及理由：

1. **c_i 不取二值（0/1），而是 0/0.85/1.0。**
   校园简历里"上过课"和"做过项目"在文本上都只出现一次，二值化会把二者等同。单次命中给 0.85 的满分，让"多处印证"能拉开差距，同时不误杀只写了一次的关键技能——**宁可系统性偏松，不要系统性误杀**。

2. **加分段落系数 0.5。**
   人工核对 24 条样例 JD，加分项段落平均只覆盖 15–25% 的真实要求。给到 0.5 以上，会让"加分项齐全但硬门槛缺失"的候选人排名虚高。

3. **长度优先级 + 位置占用解决双计。**
   `对接客户`(COM06) 与 `对接`(COM01)、`Python`(ENG01/DAT06) 会互相干扰。按 `(起始位置升序, 长度降序)` 贪心占用区间，同位置必然先接受最长的词。

## 目录

```
JobLens-岗位镜/
├── 启动 JobLens.command   ← 双击这个就能跑（自检 + 重算报告 + 自动打开）
├── jd_insight/
│   ├── taxonomy.py     44 项标签体系（业务方设计，工程方实现）
│   ├── parser.py       JD/简历 → 命中（长词优先 + 歧义消解 + 加分段标记）
│   ├── matcher.py      需求向量 × 供给向量 → 分数、缺口、建议、排名
│   ├── report.py       单文件 HTML 报告（无 CDN、无 JS 依赖）
│   └── cli.py           match / rank / taxonomy / selfcheck
├── tests/              61 个用例（含口径回归用例）
├── data/
│   ├── jd_samples.csv  24 条**合成** JD（技术岗 3 + 非技术岗 21）
│   ├── jd_J01.txt      单条 JD 示例
│   └── resume_demo.txt 演示简历
├── skills/
│   └── jd-insight-SKILL.md   WorkBuddy 技能包定义（可安装后自然语言调用）
└── docs/
    ├── 需求规格_v1.md        业务方写的原始规格（工程方的输入）
    ├── 权重校准口径.md        每一条权重背后的业务判断
    └── 校准报告.md            v1.0→v1.2 的分数变化实测
```

## 已知局限（写在这里是为了不被误用）

1. **不处理否定与被动语义**：`"未使用过 Python"` 会被判为命中。因此不能用于自动筛简历。
2. **不做语义相似度**：`"经营分析"` 与 `"商业洞察"` 属于同义，但只有进 alias 表才能匹配。alias 表是人工维护的，会持续漏。
3. **权重是场景化的**：同一标签在技术岗与非技术岗的重要性不同，当前只按"校园招聘普遍重要性"给了单一权重，未做岗位族分层。
4. **样例数据是合成的**：24 条 JD 由业务方按真实 JD 的句式结构改写，不代表真实市场分布；用于演示与回归，不能用于得出招聘市场结论。

## 换自己的数据

```bash
# JD 库：csv 至少包含 title, jd_text 两列（id / company 可选）
# 简历：任意纯文本（txt / md 均可）
python3 -m jd_insight.cli rank --jobs 你的jd.csv --resume 你的简历.txt --top 20
```

## 许可

课程作业产出，可自由参考。标签体系与权重口径引用请注明来源。
