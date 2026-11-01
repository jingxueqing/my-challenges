# Demo 演示记录：本地大模型 Agent 技能（C4D）

> 提交人：JingXueQing（景雪晴）｜提交身份：2024102110351
> 本文是**可复现的演示脚本 + 实录证据索引**：每条命令对应一张原始截图和一份 `reports/*.json` 实测报告。
> 数字全部取自落盘报告，未做修饰；失败用例保留原样。

---

## 0. 演示环境

| 项 | 值 | 来源 |
|---|---|---|
| 设备 | Apple M1 / 8 逻辑核 / 8GB | `reports/doctor.json` |
| 推理服务 | Ollama `0.40.2`（本机 `127.0.0.1:11434`，全程无云端 API） | `reports/doctor.json` |
| 模型 | `gemma4:e2b-it-q4_K_M`（4.6B / Q4_K_M / ctx 上限 131072） | `reports/doctor.json` |
| 模型能力声明 | completion / vision / audio / tools / thinking | `reports/doctor.json` |
| Python | ≥3.10，**仅标准库，零第三方依赖** | `SKILL.md` 前置条件 |

演示目录：`JingXueQing_C4D_agent-skill/`

---

## 1. 自检：环境与模型就位（截图 `01_doctor.png`）

```bash
python3 run_agent.py doctor
```

**预期**：打印 Ollama 版本、设备信息、已拉取模型清单。
**实录**：Ollama `0.40.2`；检出 `gemma4:e2b-it-q4_K_M`，size 4,587,156,505 B，量化 Q4_K_M，能力含 `tools` 与 `vision`。
→ 报告：`reports/doctor.json`

## 2. 工具层单测：不依赖模型（截图 `02_selftest.png`）

```bash
python3 run_agent.py selftest
```

**预期**：秒级返回，覆盖精度与异常路径。
**实录**：**7/7 通过**

| 检查项 | 结果 | 详情 |
|---|---|---|
| geocode_local 命中 | ✅ | conf=0.5 |
| reverse_geocode 合理 | ✅ | 反查出「西亚斯学院-图书馆」 |
| search_poi 命中 | ✅ | count=1 |
| route_plan 计算 | ✅ | 1.421 km / 17.8 min |
| score_poi 可解释 | ✅ | score=96.1 |
| haversine 精度 | ✅ | 实测 111.20 km，理论 111.19 km |
| 非法参数抛错 | ✅ | 异常路径正确抛出 |

→ 报告：`reports/selftest.json`

## 3. 核心演示：Agent 自主调工具生成地图（截图 `03_agent_trace.png`）

```bash
python3 run_agent.py map "给我生成一个 SIAS University（郑州西亚斯学院）周边的地图，包含校园与周边地标"
```

**预期**：模型自己决定调哪个工具、自己填参数，多轮后产出 5 个标记点。
**实录**：ReAct 循环内完成多次工具调用 → 产出 5 个中英双语标记点，坐标均来自工具返回（`source: local-gemma4+grounded`）；渲染为单文件 `JingXueQing_C4D_map.html`（腾讯地图 GL JS，代理模式、前端零密钥、GCJ-02）。
**两版对照**：`reports/run_report_v1.json`（首版）→ `reports/run_report.json`（加 grounded 约束后的定稿），可见标记点与来源标注的变化。

产物：`JingXueQing_C4D_map.html`（双击即可打开）

## 4. 多轮对话改图（记忆能力）

```bash
python3 run_agent.py chat
# 你> 把图书馆删掉
# 你> 给地图加一个开封
```

**预期**：多轮上下文保持，增删改后重新渲染。
**实录**：改图状态落盘在 `data/map_state.json`，轨迹记录在 `data/trajectory.jsonl`（可逐轮回放）。

## 5. 代码生成：自己写、自己跑、自己修（截图 `04_codegen.png`）

```bash
python3 run_agent.py code "统计 1 到 100 之间的质数个数，并把前 5 个质数列出来，用 JSON 输出"
```

**预期**：生成代码 → 执行 → 用 stdout 自检 → 不合格则重试。
**实录**：

```json
{"prime_count": 25, "first_five_primes": [2, 3, 5, 7, 11]}
```

- 生成 31 行代码，**1 次尝试即通过**，执行耗时 5,079 ms
- 本次推理：976 eval tokens，总 53,405 ms，吞吐 18.28 tok/s

→ 报告：`reports/codegen.json`

## 6. 原生多模态视觉理解（截图 `05_vision.png`）

```bash
python3 run_agent.py vision data/test_campus_photo.png
```

**预期**：判断是否校园照、给出场景描述与类别。
**实录**：`is_campus_photo=true`、`confidence=0.85`、scene=「大学校园建筑」、tags=「教学楼/行政楼/砖建筑/大学建筑」，推理 600 eval tokens、12.38 tok/s。
**已知缺陷（如实记录）**：`guess_category` 输出为 `nature`，与语义不符——高置信度不代表分类正确。
→ 报告：`reports/vision.json`；该缺陷已写入 AAR 的改进项。

## 7. 上下文档位对比基准（截图 `06_ctxbench.png`）

```bash
python3 run_agent.py bench --profiles e2b-q4
```

**实录（同一任务，仅改 num_ctx）**：

| num_ctx | 是否成功 | 吞吐 | 工具调用 | 标记点 | wall time |
|---|---|---|---|---|---|
| 1024 | ✅ | 14.43 tok/s | 2 | 0 | 240.08 s |
| 2048 | ❌ | — | — | — | `结构化输出在3 轮内失败：模型返回空字符串` |
| 4096 | ✅ | 19.27 tok/s | 4 | 5 | 244.75 s |
| 8192 | ✅ | 12.91 tok/s | 4 | — | — |

**结论**：2k 窗口不够用，4k 是这台 8GB M1 的可用下限。
→ 报告：`reports/ctxbench.json`

## 8. 单测回归（截图 `07_tests.png`）

```bash
python3 -m pytest tests/test_agent_skill.py -q
```

**实录**：测试全通过（对应截图 `07_tests.png`），覆盖工具层与 schema 解析路径。

---

## 9. 一键复现步骤

```bash
# 0) 先确认本机 Ollama 在跑，且已拉模型
ollama serve &
ollama pull gemma4:e2b-it-q4_K_M

# 1) 进目录（纯标准库，无需 pip install）
cd JingXueQing_C4D_agent-skill

# 2) 依次跑 1→8 节命令
python3 run_agent.py doctor
python3 run_agent.py selftest
python3 run_agent.py map "给我生成一个 SIAS University 周边的地图"
python3 run_agent.py vision data/test_campus_photo.png
python3 run_agent.py bench --profiles e2b-q4
```

## 10. 截图与文件对照表

| 截图 | 内容 | 对应报告 |
|---|---|---|
| `01_doctor.png` | 环境/模型自检输出 | `reports/doctor.json` |
| `02_selftest.png` | 7 项工具层单测 | `reports/selftest.json` |
| `03_agent_trace.png` | Agent 工具调用轨迹 | `reports/run_report.json` |
| `04_codegen.png` | 代码生成与执行结果 | `reports/codegen.json` |
| `05_vision.png` | 图像理解结果 | `reports/vision.json` |
| `06_ctxbench.png` | 4 档上下文对比 | `reports/ctxbench.json` |
| `07_tests.png` | 单测回归 | `tests/test_agent_skill.py` |

> 说明：所有演示均在本机离线完成，未调用任何云端大模型 API，推理成本为零。
