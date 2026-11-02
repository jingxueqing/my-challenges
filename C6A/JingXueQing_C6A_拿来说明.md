# C6A 拿来说明：用了哪些库 / 工具 / Agent，哪些是我写的

> 原则：**能从公开来源拿的，写清楚拿了什么；剩下的是我自己写的。** 不把「调用标准库」说成「自研」，也不把「AI 生成」藏起来。

---

## 一、工具与 Agent

| 类别 | 用了什么 | 用途 | 说明 |
|---|---|---|---|
| **Coding Agent** | **WorkBuddy 内置 Agent**（本机，DS-V4.1-Flash 驱动） | 读资料、写全部脚本、跑命令、看截图、写文档 | 全程 1 个会话完成；**没有**使用 OpenClaw / Claude Code / Cursor（本机无这些环境的会话记录） |
| 终端 | macOS zsh + 系统命令 | 建目录、跑脚本、拷贝文件 | — |
| 浏览器 | Google Chrome（`--headless=new --screenshot`） | 生成 6 张运行截图 | 无头模式，不依赖任何截图插件 |
| Python | 3.13.12（WorkBuddy 托管环境，含 openpyxl 3.1.5） | 跑管线 | 环境路径见 `教学说明.md` |
| 编辑器 | 无（Agent 直接写文件） | — | — |

---

## 二、代码依赖（Python 侧）

| 库 | 版本 | 是否第三方 | 用途 |
|---|---|---|---|
| `json` `csv` `re` `os` `pathlib` `fnmatch` `difflib` | 标准库 | ❌ 自带 | 数据读写、正则抽取、文件匹配、同义标签判定 |
| `collections`（Counter/defaultdict） | 标准库 | ❌ 自带 | 统计、分组 |
| `datetime` `subprocess` `sys` | 标准库 | ❌ 自带 | 时间戳、阶段调度 |
| **`openpyxl`** | **3.1.5** | ✅ 唯一第三方依赖 | 生成 xlsx：多 Sheet、条件格式填充、冻结窗格、自动筛选、BarChart |

> 只有 1 个第三方依赖，`pip install openpyxl` 即可。没有 pandas / 没有 Flask / 没有 Jinja。

---

## 三、前端依赖

| 项 | 用了吗 | 说明 |
|---|---|---|
| React / Vue | ❌ | 20×20 规模用不上框架，原生 DOM 字符串渲染足够 |
| Tailwind CSS | ❌ | **手写 CSS**（`assets/styles.css`，约 400 行），因为 CDN 版断网就白屏，而本项目要求「发过去双击就能看」 |
| Chart.js | ❌ | 图表只有三类（进度条/热力矩阵/时间线），手写 CSS + 表格比引图表库更快更可控，也避免「图表误导」 |
| 图标库 | ❌ | 只用 `✅ ⚠️ ❌` 与一个内联 SVG 放大镜 |
| 字体 | 系统字体 | PingFang SC / 微软雅黑 / 系统无衬线回退，无外链字体 |

---

## 四、拿来的东西（逐条写清）

| 来源 | 拿了什么 | 用在哪 | 我怎么改的 |
|---|---|---|---|
| `挑战_C6A…/CHALLENGE.md` | ① 提交记录 Schema 与挑战要求 Schema 的字段设计（`student/challenge/submitted_at/files/status/completeness/missing/level_achieved`）② 五个 Sheet 的划分（总览/按学生/按挑战/时间线/缺失项） | `submissions.json` 结构、`make_excel.py` | 扩了 `quality`（命名合规、AI日志体量）、`review`（评审分）、`attribution`（归属方式）、`provenance`（口径与局限）四组字段；Sheet 增加「数据来源」 |
| `我的挑战/挑战_*/CHALLENGE.md`（20 份） | **必填项原文**（如 `姓名_C4C_验证报告.md`）与交付说明 | 规格抽取的唯一输入 | 用正则解析成结构化条目，保留 `source_line` 以便回溯；跨挑战串味丢弃；同义项合并 |
| 本人 C4A 交付里的 `评审输出/评审结果.json`、`文件清单.json` | 3 位提交者的 C4 真实评审分与完整性判定（rubric `c4a-rubric-v1.1`） | 网站/Excel 的 `review` 字段 | 只读不改；把 `author` 名做别名归一（`jingxueqing → JingXueQing`），并标注来源路径 |
| openpyxl 官方文档 | `PatternFill` / `Border` / `FreezePanes` / `AutoFilter` / `BarChart` / `Reference` 的用法 | `make_excel.py` | 组合成统一表头样式与状态色（绿/琥珀/红三色与网站一致） |
| C4A 挑战的评审思路（红线规则：无 AI 日志 → 复盘质量 ≤5） | 「AI 日志是硬卡口」这一判断 | 「洞察」卡片里的 AI 日志专项检查 | 变成可执行规则：命中情况 + 文件体量 ≥300B |

**没有拿的部分（明说）**：没有复制任何开源项目的代码；没有用现成的仪表盘模板；没有参考别人的 C6A 实现（本机无该数据）。

---

## 五、我自己写的（占绝大多数）

| 模块 | 行数（约） | 内容 |
|---|---|---|
| `specs.py` | 300 | 章节定位、交付项抽取、槽位归一（20 条槽位表）、标签清洗、同义合并、补丁机制 |
| `pipeline.py` | 560 | 提交包发现、候选收集（深度/忽略）、四级归属、三级匹配与贪心分配、质量检查、评审挂载、矩阵与洞察计算、JSON/CSV 输出 |
| `make_excel.py` | 330 | 6 个 Sheet、条件格式、柱状图、冻结窗格、筛选、数据来源页 |
| `make_site.py` | 50 | JSON 内嵌注入、静态化 |
| `digest.py` | 90 | 日报 + 群消息 |
| `run.py` | 120 | 阶段调度 + `check` 反向自检 |
| `templates/app.js` | 480 | 6 个视图渲染、筛选/搜索/排序、详情抽屉、深链、键盘快捷键 |
| `templates/styles.css` | 400 | 设计系统（色板/间距/组件），无框架 |
| 文档 | — | 方案设计 / 教学说明 / AAR / AI 日志 / 本文件 / README |

---

## 六、诚实边界

1. **数据只有 3 位提交者**：全班数据不在本机，也不允许编造。所以「覆盖率 27%」是真实覆盖率，不是完成率。
2. **提交时间是近似值**：取文件 mtime，复制/解压会刷新。界面与 Excel 都标了「(近似)」。
3. **不判断质量**：除 C4 接了 C4A 评审分外，其它挑战只有「有没有」。
4. **AI 参与程度**：代码与文档由 WorkBuddy Agent 生成，人负责需求边界、数据真实性与验收。过程见 `JingXueQing_C6A_AI日志.md`（10 轮迭代、7 个失败点，逐条有终端证据）。
