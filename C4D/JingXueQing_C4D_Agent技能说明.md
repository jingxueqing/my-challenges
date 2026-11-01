# Agent 技能说明（索引）：sias-local-map-agent

> 提交人：JingXueQing（景雪晴）｜提交身份：2024102110351
> 本文是这个技能包的**入口索引**：它是什么、能干什么、怎么跑、产物在哪、边界在哪。
> 技能本体见 `JingXueQing_C4D_agent-skill/`（`SKILL.md` + `README.md` + 源码）。

---

## 1. 一句话定义

**完全离线运行在用户自己电脑上的地图 Agent 技能**：本地大模型（Ollama + `gemma4:e2b-it-q4_K_M`）通过原生 function calling 调用 5 个真实工具，产出中英双语交互式腾讯地图 HTML；支持多轮改图、代码生成执行、视觉理解、多档位基准对比。**不调用任何云端 API，推理费用为零，数据不出本机。**

## 2. 能力清单（六项，均已实测）

| 能力 | 指令 | 实测佐证 |
|---|---|---|
| 环境自检 | `doctor` | Ollama 0.40.2 / M1 8GB / 模型 4.6B Q4_K_M |
| 工具层单测 | `selftest` | **7/7 通过**（含 haversine 精度 111.20 vs 111.19 km） |
| Agent 自主出图 | `map "…"` | 5 个双语标记点，单文件 HTML |
| 多轮对话改图（记忆） | `chat` | 状态落盘 `data/map_state.json`，轨迹 `data/trajectory.jsonl` |
| 代码生成执行 | `code "…" --compare` | 质数题 `{25, [2,3,5,7,11]}`，31 行，1 次通过 |
| 原生多模态视觉 | `vision <图片>` | 判校园照 true / conf 0.85（分类字段有已知缺陷） |
| 多档位基准 | `bench --profiles …` | ctx 1024/2048/4096/8192 四档对比表 |

## 3. 五个真实工具（非空壳，全部离线）

| 工具 | 作用 | 离线 |
|---|---|---|
| `geocode_local` | 地名 → 坐标，三级模糊匹配（包含 → bigram 相似度 → 兜底） | ✅ |
| `reverse_geocode` | 坐标 → 最近地标 + 距离 | ✅ |
| `search_poi` | 本地知识库 POI 检索 | ✅ |
| `route_plan` | 多点顺序路线规划（haversine + 速度模型） | ✅ |
| `score_poi` | 可解释打分（评分 65% + 可达性 35%） | ✅ |

## 4. 架构（四层）

```
自然语言指令
  ↓ agent.py     ReAct 循环（上限 4 轮），模型自己选工具、自己填参数
  ↓ tools.py     5 个真实可执行工具，观测结果回灌模型
  ↓ llm.py       Ollama 原生 format schema 约束解码；失败退回文本模式 + JSON 自愈
  ↓ map_render.py 腾讯地图 GL JS（代理模式、前端零密钥、GCJ-02）
单文件 JingXueQing_C4D_map.html
```

## 5. 目录结构

```
JingXueQing_C4D_agent-skill/
├─ SKILL.md                 技能定义（何时使用/前置条件/五步用法/架构）
├─ README.md                快速上手
├─ run_agent.py             统一 CLI 入口（doctor/selftest/map/chat/code/vision/bench）
├─ sias_agent/              核心包
│  ├─ agent.py              ReAct Agent
│  ├─ tools.py              工具层
│  ├─ llm.py                结构化输出与自愈
│  ├─ map_render.py         地图渲染
│  ├─ advanced.py           Level 3/4 能力
│  └─ config.py             模型与档位配置
├─ data/                    测试图片、改图状态、对话轨迹
├─ reports/                 7 份实测报告（doctor/selftest/run_report/run_report_v1/codegen/vision/ctxbench）
├─ tests/test_agent_skill.py 单测回归
└─ make_evidence.py         证据（截图）生成脚本
```

## 6. 怎么跑（三步，零第三方依赖）

```bash
ollama serve &                                  # 1. 起本地推理服务
ollama pull gemma4:e2b-it-q4_K_M                # 2. 拉模型（8GB 机器推荐档）
cd JingXueQing_C4D_agent-skill
python3 run_agent.py doctor                     # 3. 自检 → 开跑
python3 run_agent.py map "给我生成一个 SIAS University 周边的地图"
```

仅需 Python ≥3.10 标准库，**无需 pip install**。

## 7. 产物在哪

| 产物 | 路径 |
|---|---|
| 交互式地图（双击可开） | `C4D/JingXueQing_C4D_map.html` |
| 7 张运行截图 | `C4D/JingXueQing_C4D_output_screenshots/` |
| 7 份实测报告 | `C4D/JingXueQing_C4D_agent-skill/reports/` |
| 运行日志（Ollama 启动 / 模型拉取） | `C4D/logs/` |
| 演示脚本与证据索引 | `C4D/JingXueQing_C4D_demo演示记录.md` |
| 复盘 | `C4D/JingXueQing_C4D_AAR复盘.md` |

## 8. 已知边界（不夸大）

- **窗口下限**：`num_ctx=2048` 时结构化输出失败（返回空字符串），可用下限是 4096。
- **速度**：8GB M1 上单次完整地图任务 wall time 约 240 s，属于"能跑通但不算快"。
- **视觉分类**：`guess_category` 在建筑图上误判为 `nature`，需加 allow-list 修正（已在 AAR 列为改进项）。
- **泛化**：只验证了 gemma4 单模型家族，`--profiles` 跨模型对比接口未跑满。

---

**适用场景**：需要在离线/无 API 预算环境下生成地图、需要证明 2B 级小模型也能驱动 function calling 与结构化输出、需要可改可复用的 Agent 技能模板时使用。
