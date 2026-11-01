# sias-local-map-agent

> **完全离线**的地图 Agent。全部推理由你自己电脑上的 Ollama 完成，
> 不调用任何云端 API —— **推理费用 ¥0，数据不出本机**。

实测环境：MacBook Air M1 / 8GB / macOS 14.5 ／ Gemma 4 E2B (Q4_K_M) ／ Ollama v0.40.2

---

## 快速开始

```bash
# 前提：ollama serve 在跑，且已 ollama pull gemma4:e2b-it-q4_K_M

python3 run_agent.py doctor      # 环境自检（设备/模型/服务，实采）
python3 run_agent.py selftest    # 工具层自测，不需要模型，秒级
python3 -m unittest discover -s tests   # 77 个单元测试

python3 run_agent.py map "给我生成一个 SIAS University 周边的地图"
open ../JingXueQing_C4D_map.html
```

**零第三方依赖** —— 纯 Python 标准库，`git clone` 完就能跑。
（只有 `make_evidence.py` 生成截图时需要 Pillow。）

---

## 八个子命令

| 命令 | 作用 | 需要模型 |
|---|---|---|
| `doctor` | 环境/模型/设备信息 | ❌ |
| `selftest` | 工具层 7 项自测 | ❌ |
| `map "指令"` | **核心**：Agent 生成交互式地图 | ✅ |
| `chat` | 多轮对话增删改标记 | ✅ |
| `code "需求"` | 代码生成 Agent（写码→受限执行→自修复） | ✅ |
| `vision 图片` | 视觉理解 Agent（Gemma 4 原生多模态） | ✅ |
| `ctxbench` | 上下文长度调优基准（Level 4） | ✅ |
| `bench --profiles a,b` | 多模型对比（Level 4，需自行 pull） | ✅ |

---

## 架构

```
用户自然语言
     ↓
MapAgent（ReAct 循环，最多 4 轮）      agent.py
     ↓  Ollama /api/chat + tools=[...]（模型自己选工具、自己填参数）
本地 Gemma 4 E2B                      llm.py   ← 指标采集 + JSON 自愈
     ↓  tool_calls
5 个真实工具（全部离线可跑）            tools.py
     ↓  真实结果回灌模型 → 多步推理
schema 约束解码 + 几何自检              agent.py
     ↓  markers[]
腾讯地图 GL JS 渲染（合规）             map_render.py
     ↓
单文件 HTML（双击即开）
```

### 五个工具

| 工具 | 作用 | 离线 |
|---|---|---|
| `geocode_local` | 地名 → 坐标（三级模糊匹配） | ✅ |
| `reverse_geocode` | 坐标 → 最近地标 + 距离 | ✅ |
| `search_poi` | POI 检索（AND 无结果时自动放宽） | ✅ |
| `route_plan` | 多点路线规划（haversine + 速度模型） | ✅ |
| `score_poi` | 可解释打分（评分 65% + 可达性 35%） | ✅ |

---

## 三个值得学的设计决策

**① 小模型 JSON 不稳，靠解码期约束，不靠 prompt。**
先用 Ollama 原生 `format: <JSON Schema>` 在采样层面限制，
失败才退回文本模式并把真实报错回灌让模型自修复。
「请严格输出 JSON」这种提示词对 2B 模型基本无效。

**② 2B 模型会输出「格式完美但地理错误」的坐标。**
实测：让模型「加一个开封」，它给出 `34.5092,113.4050`，
而权威值是 `34.7970,114.3070`，**偏差 88.5 km**。
JSON 合法、描述通顺、星级合理，肉眼完全看不出来。

所以有**三道几何自检**：坐标非法 → 丢弃；名称命中知识库 → **强制吸附权威坐标**；
名称不在知识库且离郑州 >500km → 拉回。纠正动作写进审计日志和 `source` 字段。

**③ 证据与代码彻底分离。**
设备信息从 `sysctl` 实采，tok/s 从 Ollama 的 `eval_count`/`total_duration` 实算，
**任何文档里都不许手写这些数字**。截图脚本只做排版，
并在每张图底部标注数据来源文件。

---

## 地图合规

用腾讯地图 GL JS，不用 OSM/Google/Mapbox/Leaflet。关键点：

- `_TMapSecurityConfig` 密钥代理模式，SDK URL **不带 key**，前端零密钥
- 坐标 **GCJ-02**
- **不传 `mapStyleId`**（默认 key 未开通自定义样式，传了会灰屏）
- 类名规范：图层 `MultiMarker`（带 Multi），样式 `MarkerStyle`（不带）
- 所有注入 JS 的字符串也走 `html.escape()`（防 XSS）

测试里有 6 条专项断言盯着这些。

---

## 已知局限

- **POI 是内置的 10 条**，非全量地理数据。这是刻意的取舍：
  保证「断网也能跑」这一核心主张。绝对坐标有百米级误差，
  因此工具算的**相对距离可靠**，绝对定位有偏差。
- **E2B 速度约 20 tok/s**，一次完整任务需 3–4 分钟（含首载权重约 55s）。
  推荐 `num_ctx=4096`（实测吞吐最高 19.27 tok/s，比 8192 快约 49%）。
- **ctx 不是越大越好**：2048 会直接失败（模型返回空串）；
  1024 只能产出 2 个标记点。
- 视觉识别的精度未在真实照片上验证过（测试图是示意图）。

---

## 目录

```
sias_agent/
  config.py       档位定义 + 设备/服务端信息实采
  llm.py          推理封装 + 逐次指标 + JSON 多层修复 + 多模态
  agent.py        ReAct 循环 + 状态记忆 + 几何自检
  tools.py        5 个工具 + POI 知识库 + MapState
  advanced.py     代码生成 Agent + 视觉理解 Agent
  map_render.py   腾讯地图 GL JS 渲染
tests/            77 个单元测试
data/             状态、轨迹、测试图片
reports/          运行指标 JSON（证据来源）
```

详细设计见 `../JingXueQing_C4D_方案设计.md`，
安装/复现步骤见 `../JingXueQing_C4D_教学说明.md`。

许可证：代码 MIT；模型 Gemma 4 为 Apache 2.0。
