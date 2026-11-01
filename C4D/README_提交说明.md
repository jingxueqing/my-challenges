# C4D 交付包 · 本地大模型 Agent 技能

> **JingXueQing（景雪晴）** ｜ 学号/提交 ID：**2024102110351**
> 挑战：C4D 本地大模型 Agent 技能（ch-20260717031455-uzqs9k）

---

## 一句话

用**跑在自己 MacBook Air 上的 Gemma 4**（Ollama，**零 API 费用、数据不出本机**）
通过**原生 function calling** 自主调用 5 个真实工具，把一句自然语言变成
**中英双语、可交互的腾讯地图**。综合完成 **Level 3（Gold）** + Level 4「性能调优」。

---

## 交付物对照表（对照挑战要求逐项）

| # | 挑战要求的交付物 | 本包对应文件 | 状态 |
|---|---|---|---|
| 1 | 姓名_C4D_方案设计.md | `JingXueQing_C4D_方案设计.md` | ✅ 架构/设备/选型论证 |
| 2 | 姓名_C4D_agent-skill/ | `JingXueQing_C4D_agent-skill/` | ✅ 2644 行 Python（生产 2175 + 测试 469），77 测试全绿 |
| 3 | 姓名_C4D_map.html | `JingXueQing_C4D_map.html` | ✅ 腾讯地图，5 个标记点 |
| 4 | 姓名_C4D_output_screenshots/ | `JingXueQing_C4D_output_screenshots/` | ✅ 7 张 PNG |
| 5 | 姓名_C4D_验证报告.md | `JingXueQing_C4D_验证报告.md` | ✅ 含 3 个 bug 的完整剖析 |
| 6 | 姓名_C4D_教学说明.md | `JingXueQing_C4D_教学说明.md` | ✅ 零基础可复现 |
| 7 | 姓名_C4D_AI日志.md（必须） | `JingXueQing_C4D_AI日志.md` | ✅ 9 轮迭代 + 证据标注 |
| 8 | 姓名_C4D_拿来说明.md | `JingXueQing_C4D_拿来说明.md` | ✅ 含 6 个真实踩坑 |

挑战要求截图必须显示的 4 项信息：

| 要求 | 在哪张截图 |
|---|---|
| 模型名称及版本 `gemma4:e2b-it-q4_K_M` | 01、03、04、05 |
| 运行工具 Ollama v0.40.2 | 01、03 |
| 设备信息（Apple M1 / 8GB / macOS 14.5） | 01、03 |
| 实测推理速度 tok/s | 03（15.37 均值）、04、05、06 |

---

## 完成的 Level

| Level | 要求 | 完成情况 |
|---|---|---|
| **L1 Bronze** | 本地跑通 Gemma 4 | ✅ E2B Q4_K_M，Metal 加速 ~20 tok/s |
| **L2 Silver** | 函数调用 + 交互式地图 | ✅ 4 次工具调用，5 个标记点 |
| **L3 Gold** | 完整 Agent 技能包 | ✅ **多轮对话 / 多工具 / 代码生成 / 视觉理解 / 多语言 五项全覆盖** |
| **L4 Platinum** | 至少两项 | ⚠️ 完成 **1 项**（性能调优 ctxbench）。量化对比与多设备适配**未做**，原因见验证报告第 7 节（**没有编数据**） |

---

## 30 秒复现

```bash
# 前提：已装 Ollama 且 ollama serve 在跑
cd JingXueQing_C4D_agent-skill

python3 run_agent.py doctor    # 看设备/模型/服务
python3 run_agent.py selftest  # 工具层自测（不需要模型）
python3 run_agent.py map "给我生成一个 SIAS University 周边的地图"
open ../JingXueQing_C4D_map.html
```

完整安装步骤见 `JingXueQing_C4D_教学说明.md`。

---

## 发群一句话

> C4D 提交：在自己 8GB 的 MacBook Air 上用 Ollama 跑起 Gemma 4 E2B（Q4_K_M，Metal ~20 tok/s），
> 做了一个全程离线、零 API 费用的地图 Agent——模型自己调 5 个工具决策，
> 中英双语腾讯地图 5 个点坐标全部经工具校验；抓到并修掉 4 个真实 bug
> （含 88.5km 坐标幻觉、地图 XSS、多模态静默失效）。2644 行代码 + 77 个单测全绿。

---

## 目录结构

```
C4D-交付_JingXueQing_本地大模型Agent技能/
├── README_提交说明.md                    ← 你正在看的文件
├── JingXueQing_C4D_方案设计.md
├── JingXueQing_C4D_验证报告.md
├── JingXueQing_C4D_教学说明.md
├── JingXueQing_C4D_AI日志.md
├── JingXueQing_C4D_拿来说明.md
├── JingXueQing_C4D_map.html              ← 交互式地图（双击即开）
├── JingXueQing_C4D_output_screenshots/   ← 7 张证据截图
│   ├── 01_doctor.png         环境与模型
│   ├── 02_selftest.png       工具层自测
│   ├── 03_agent_trace.png    Agent 工具调用轨迹 + tok/s
│   ├── 04_codegen.png        代码生成 Agent
│   ├── 05_vision.png         视觉理解 Agent
│   ├── 06_ctxbench.png       上下文调优基准（Level 4）
│   └── 07_tests.png          单元测试明细
├── logs/                                  ← 原始日志
└── JingXueQing_C4D_agent-skill/          ← 技能包本体
    ├── SKILL.md                    可被 Agent 平台直接加载
    ├── README.md                   快速上手
    ├── run_agent.py                CLI（8 个子命令）
    ├── make_evidence.py            证据截图生成器
    ├── sias_agent/
    │   ├── config.py               档位定义 + 设备实采
    │   ├── llm.py                  推理封装 + 指标 + JSON 自愈
    │   ├── agent.py                ReAct 循环 + 状态记忆 + 坐标自检
    │   ├── tools.py                5 个真实工具 + POI 知识库
    │   ├── advanced.py             代码生成 Agent + 视觉 Agent
    │   └── map_render.py           腾讯地图 GL JS 渲染
    ├── tests/test_agent_skill.py   77 个单元测试
    ├── data/                       状态、轨迹、测试图片
    └── reports/                    全部运行指标 JSON（证据来源）
```

---

## 三点我想特别说明的

**1. 我没有编任何数据。**
跑不出来的地方（Q8 量化对比、跨设备适配）在验证报告里明写「未完成」并给出原因。
`bench` 命令已经实现，磁盘允许时一条命令就能跑出真实对比。

**2. 最重要的产出可能是那 4 个 bug。**
AI 写的第一版代码功能级、安全级、可见性级 bug 都有：
- 多模态图片根本没送进模型，但程序退出码是 0（**静默失败**）
- 地图 HTML 的 XSS（地点名经 innerHTML 执行）
- 坐标幻觉 88.5 km（JSON 合法、肉眼看不出）
- 截图字体无中文字形，中文全变空白（**只有打开图才会发现**）
每个都有对应的回归测试，AI 日志里写了完整排查过程。

**3. 所有数字都可复现。**
截图里每个 tok/s、模型版本、内存大小，都能追到 `reports/*.json` 的具体字段，
而那些字段是 `sysctl` 和 Ollama API **实时采集**的。截图底部标了来源文件。

---

## 合规声明

- 地图使用**腾讯地图 GL JS**（`_TMapSecurityConfig` 密钥代理模式，**前端零密钥**，
  坐标 GCJ-02），**未使用** OpenStreetMap / Google Maps / Mapbox / Leaflet。
- 未标记任何军事禁区、敏感坐标；POI 数据为公开地理常识。
- 未收集或发布任何他人位置数据。
- 模型 Gemma 4 为 **Apache 2.0** 协议；Ollama 为 MIT。
