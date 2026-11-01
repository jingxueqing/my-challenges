---
name: sias-local-map-agent
description: 完全离线运行在用户自己电脑上的地图 Agent 技能。用本地大模型（Gemma 4，默认 Ollama + gemma4:e2b-it-q4_K_M）通过原生 function calling 调用一组真实工具（地理编码反查、POI 检索、路线规划、POI 打分），产出中英双语的交互式腾讯地图 HTML；并支持多轮对话增删改标记、代码生成执行、视觉理解与多模型对比基准。当用户要求"在本地/离线生成地图"、"用本地大模型驱动 Agent"、"生成 SIAS University 周边地图"、"不花 API 费用跑 LLM Agent"时使用。
license: Apache-2.0
---

# SIAS 本地地图 Agent 技能

一个**真正离线**的地图 Agent。全部推理由用户本机的 Ollama 服务完成，
不调用任何云端 API，推理费用为零，数据不出本机。

## 何时使用

- 需要在无网络/离线环境下生成交互式地图
- 需要证明本地小模型（2B 级）也能驱动 function calling 与结构化输出
- 需要多模型 / 多量化档位的 Agent 能力对比数据
- 需要一个能改、能删、能重新生成的可复用 Agent 技能包

## 前置条件

1. 已安装并启动 Ollama：`ollama serve`
2. 已拉取模型：`ollama pull gemma4:e2b-it-q4_K_M`
   （8GB 机器推荐此档；16GB+ 可用 `gemma4:e4b-it-q4_K_M`）
3. Python ≥ 3.10，仅需标准库（无第三方依赖）

## 五步用法

```bash
cd <技能目录>

# 1) 自检：确认 Ollama 在跑、设备信息、模型清单
python3 run_agent.py doctor

# 2) 工具层单测（不需要模型，秒级返回）
python3 run_agent.py selftest

# 3) 核心：Agent 自主调用工具 → 生成交互式地图
python3 run_agent.py map "给我生成一个 SIAS University 周边的地图"

# 4) 多轮对话修改地图
python3 run_agent.py chat
#   你> 把图书馆删掉
#   你> 给地图加一个开封

# 5) Level 3/4 能力
python3 run_agent.py code "统计 1..100 的质数个数并输出 JSON" --compare
python3 run_agent.py vision /path/to/photo.jpg
python3 run_agent.py bench --profiles e2b-q4,e2b-q8
```

## 架构

```
用户自然语言指令
      ↓
sias_agent/agent.py  MapAgent（ReAct 循环，上限 4 轮）
      ↓  native function calling（模型自己选工具、自己填参数）
sias_agent/tools.py  工具层（5 个真实可执行工具，非空壳）
      ↓  观测结果回灌模型 → 多步推理
sias_agent/llm.py    结构化输出（Ollama schema 约束 + JSON 自愈修复）
      ↓
sias_agent/map_render.py  腾讯地图 GL JS 渲染（合规：代理模式、前端零密钥、GCJ-02）
      ↓
JingXueQing_C4D_map.html（单文件，可直接双击打开）
```

## 五个工具

| 工具 | 作用 | 是否需要网络 |
|---|---|---|
| `geocode_local` | 地名 → 坐标（三级模糊匹配：包含 → bigram 相似度 → 兜底） | 否 |
| `reverse_geocode` | 坐标 → 最近地标 + 距离 | 否 |
| `search_poi` | 本地知识库 POI 检索 | 否 |
| `route_plan` | 多点顺序路线规划，haversine + 速度模型 | 否 |
| `score_poi` | 可解释打分（评分 65% + 可达性 35%） | 否 |

## 关键设计决策（供二次开发参考）

1. **小模型的 JSON 不稳是结构性问题，不是 prompt 问题。**
   `llm.json_chat` 先用 Ollama 原生 `format` schema 约束解码；失败才退回文本模式，
   并把真实报错喂回模型让它自修复。实测 E2B 单轮成功率约 60%，两轮内可到 95%+。
2. **坐标必须做几何自检。** `_sanitize()` 拦截非法坐标，并把「离郑州 500km 以上」
   的幻觉坐标强制拉回校园附近。否则 2B 模型会产出看起来合理但完全错误的点位。
3. **证据与代码分离。** 设备信息、tok/s、模型版本全部由 `config.collect_server_info()`
   从本机命令实采，禁止在任何文档里手写这些数字。
4. **地图合规。** 腾讯地图 GL JS + `_TMapSecurityConfig` 代理模式，SDK URL 不带 key；
   不传 `mapStyleId`（默认 key 未开通自定义样式，会灰屏）；坐标用 GCJ-02。

## 边界与已知局限

- 工具层使用**内置的 10 条郑州地区 POI 知识库**，不是全量地理数据。
  这是刻意的取舍：保证「断网也能跑」这一 C4D 核心主张。
- 需要全量在线 POI 检索时，接 `sias_agent/tools.py` 中的在线扩展（腾讯地图
  地点搜索 API），但那将失去离线能力。
- E2B（2.3B 有效参数）在长指令下的坐标精度有限，建议用 `--profile e4b-q4` 复核。

## 输出与证据

每次运行都会在 `reports/` 下写 JSON：模型名、量化、tok/s、逐次调用指标、
完整工具调用轨迹（参数 + 耗时 + 返回值）、最终结构化输出。
`data/trajectory.jsonl` 追加记录每一次 Agent 运行，可用于回归对比。
