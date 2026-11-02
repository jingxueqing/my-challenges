# C6A 提交说明 ｜ 提交数据仪表盘

**提交人**：JingXueQing（景雪晴）｜ 学号 **2024102110351** ｜ 挑战：C6A 提交数据仪表盘（ch-20260717031528-w43gy7）
**一句话**：把散落在磁盘上的 19 个真实提交包，变成「一条可复跑的数据管线 → 可点开的仪表盘 → 对得上账的 Excel → 能直接发群的日报」。

---

## 一、30 秒看结果

```bash
cd JingXueQing_C6A_pipeline && python3 run.py all      # 一条命令重建全部产物
open ../JingXueQing_C6A_仪表盘/index.html           # 双击也能开（零依赖）
```

| 指标 | 数值 |
|---|---|
| 提交者 / 挑战 / 记录 | 3 位 / 20 个 / 16 条（264 个文件，19 个真实提交包） |
| 必填项全齐 | 14 条（88%）｜缺件 2 条 |
| 平均完整度 | 90% ｜覆盖率 27%（16/60 格，本机可核验范围） |
| 规格来源 | 20 份官方 CHALLENGE.md **自动抽取**，0 处硬编码必填项 |
| 第三方依赖 | **仅 openpyxl**（Excel）；网站零依赖、无 CDN |

---

## 二、交付物对照表（对着挑战要求逐条）

| 挑战要求 | 实际交付 | 说明 |
|---|---|---|
| `姓名_C6A_方案设计.md` | `JingXueQing_C6A_方案设计.md` | 架构五层、数据模型、五条硬口径、技术选型与淘汰理由、已知局限 |
| `姓名_C6A_data/`（JSON/CSV） | `JingXueQing_C6A_数据/` | `submissions.json`（记录级）、`specs.json`（规格）、`matrix/records/files/challenge_stats.csv`、`报告/每日摘要与群通知` |
| `姓名_C6A_dashboard/` | `JingXueQing_C6A_仪表盘/` | `index.html`（数据内嵌）+ `assets/app.js` + `assets/styles.css` + `data.json` |
| `姓名_C6A_report.xlsx` | `JingXueQing_C6A_report.xlsx` | 6 Sheet：总览/按学生/按挑战/时间线/缺失项/数据来源；条件格式 + 柱状图 |
| `姓名_C6A_screenshots/` | `JingXueQing_C6A_screenshots/` | 7 张：总览、按学生、按挑战、时间线、缺失项、方法与口径、记录详情（2 倍像素） |
| `姓名_C6A_教学说明.md` | ✅ | 装（1 个依赖）、跑、日常更新、加挑战/加学生不改代码、FAQ、移交清单 |
| `姓名_C6A_AAR.md` | ✅ | 做了什么/学了什么/怎么验证/7 条失败清单/5 条改进方案 |
| `姓名_C6A_AI日志.md`（必须） | ✅ | 10 轮真实迭代，每轮含失败与修复，标注证据来源（终端/文件/时间戳） |
| `姓名_C6A_拿来说明.md` | ✅ | 逐个工具与库说明拿什么、怎么改；明确「没拿什么」 |
| （加分）生成脚本 | `JingXueQing_C6A_pipeline/` | 6 个脚本 + 配置 + 模板；`run.py check` 可自检 |

---

## 三、目录结构

```
C6A-交付_JingXueQing_提交数据仪表盘/
├── README_提交说明.md
├── JingXueQing_C6A_方案设计.md
├── JingXueQing_C6A_教学说明.md
├── JingXueQing_C6A_AAR.md
├── JingXueQing_C6A_AI日志.md
├── JingXueQing_C6A_拿来说明.md
├── JingXueQing_C6A_report.xlsx
├── JingXueQing_C6A_数据/
│   ├── submissions.json          ← 唯一事实源
│   ├── specs.json                ← 20 个挑战的必填项规格（带 source_line）
│   ├── matrix.csv / records.csv / files.csv / challenge_stats.csv
│   └── 报告/每日摘要_2026-11-01.md、群里通知_2026-11-01.txt
├── JingXueQing_C6A_仪表盘/
│   ├── index.html                ← 双击打开
│   ├── data.json                 ← 同一份数据，供二次开发
│   └── assets/app.js、styles.css
├── JingXueQing_C6A_screenshots/  ← 7 张运行截图
└── JingXueQing_C6A_pipeline/
    ├── config.json               ← 数据根路径、学生别名、人工补丁
    ├── specs.py                  ← 规格抽取与槽位归一
    ├── pipeline.py               ← 扫描 / 归属 / 匹配 / 统计
    ├── make_excel.py             ← Excel
    ├── make_site.py              ← 网站
    ├── digest.py                 ← 日报 + 群消息
    ├── run.py                    ← 一键调度 + 自检
    └── templates/                ← 站点模板（HTML/JS/CSS）
```

---

## 四、六个视图长什么样

| 视图 | 你一分钟内能看到什么 |
|---|---|
| **总览** | 6 个 KPI + 6 条自动生成的洞察 + 人 × 挑战热力矩阵 + 各挑战完整度 + 缺件提醒 + 阅读指南 |
| **按学生** | 每人的已提交/全齐/平均完整度，逐条记录带时间与缺件摘要 |
| **按挑战** | 每个必填项标签上的「命中人数/总人数」——一眼看出这个挑战最容易缺什么 |
| **时间线** | 按月份倒序，一眼看出提交聚集在哪个时间段 |
| **缺失项** | 最常缺的交付项 TOP 8 + 缺件清单，可直接拿去催 |
| **方法与口径** | 数据根、扫描规则、20 条规格明细（含 origin）、已知局限、更新命令 |

---

## 五、复现命令（评审可复核）

```bash
# 0) 依赖
python3 -m pip install openpyxl

# 1) 全量重建
cd JingXueQing_C6A_pipeline
python3 run.py all

# 2) 自检（必须打印「自检通过」）
python3 run.py check

# 3) 看结果
open ../JingXueQing_C6A_仪表盘/index.html
open ../JingXueQing_C6A_report.xlsx
```

单步命令：`specs`（重抽规格）→ `scan`（重扫数据）→ `excel` → `site` → `digest`。
本次实测输出：

```
[scan] 提交包 19 个
[data] 记录 16 条 / 学生 3 位 / 挑战 20 个 / 文件 264 个
[data] 状态：完整 14 / 缺件 2 / 平均完整度 90%
[excel] JingXueQing_C6A_report.xlsx 生成完成（6 个 Sheet）
[site]  index.html 生成完成（147 KB，内嵌 16 条记录）
[digest] 报告/每日摘要_2026-11-02.md 与 报告/群里通知_2026-11-02.txt 已生成
自检通过：状态、完整度、文件-规格映射三者一致。
```

> `JingXueQing_C6A_数据/报告/` 按运行日期留档，所以你会看到 11-01 和 11-02 两份：前者是首次采样（17 包），后者是补进 C6/C7 之后（19 包）。数字不同不是错，是同一套管线在不同时点的快照。

---

## 六、发群一句话

> 做了个提交数据仪表盘：把 19 个提交包读成结构化数据，双击 `index.html` 就能看「谁交了、什么时候交的、每个挑战缺什么」，缺件能一路点回到具体文件；Excel 和日报由同一份 JSON 生成，口径不会打架。全班数据我这台机器只有 3 个人的，把包放进数据根目录跑一条命令就能扩。

---

## 七、我自己先验收的 6 条

- [x] `index.html` 断网、双击可开（数据内嵌，无 fetch、无 CDN）
- [x] 矩阵点任意格子都能打开详情；详情里的文件名与磁盘文件一一对应
- [x] Excel 的完整度与网页完全一致（同源 JSON）
- [x] 「❌ 无记录」写成「采集不到」，没有一句「未提交」
- [x] `run.py check` 通过（状态/完整度/映射三方自洽）
- [x] 20 个挑战的必填项全部可回溯到 CHALLENGE.md 的具体行号

---

## 八、诚实的局限（写在最前面，别让评审踩坑）

1. **只有 3 位提交者的本机数据**：覆盖率 27% 是真实覆盖率，不是全班完成率；没有编造任何同学姓名或记录。
2. **提交时间取文件 mtime**：复制/解压会刷新，界面与 Excel 都标注「近似」。
3. **`WeChatGroup` / `Elite20TA` 是提交包里的账号名**，不是真实姓名，原样保留。
4. **除 C4 外没有质量分**：`review` 字段已预留（C4 已接 C4A 真实评审结果），其余挑战只回答「有没有」。
