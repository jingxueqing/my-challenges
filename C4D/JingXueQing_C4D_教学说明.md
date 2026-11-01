# 教学说明：从零复现这个本地 Agent

> 目标读者：**没装过本地模型、也没写过 Agent** 的同学。
> 全程不需要任何云端 API Key，不需要注册、不花钱。
> 预计耗时：**首次 30–60 分钟**（主要是下载），之后每次跑 1–3 分钟。

---

## 第 0 步：先确认你的机器能跑

打开终端（Terminal），粘贴：

```bash
system_profiler SPHardwareDataType | grep -E "Chip|Memory"
df -h / | tail -1
```

对照下表选模型：

| 你的配置 | 建议模型 | 能不能跑通本文 |
|---|---|---|
| 8GB 内存（如 MacBook Air M1/M2 8G） | `gemma4:e2b-it-q4_K_M` | ✅ 能，就是本文档基准环境 |
| 16GB 内存（多数轻薄本） | `gemma4:e4b-it-q4_K_M` | ✅ 能，质量更好 |
| 16GB+ 显存 N 卡 | `gemma4:26b-a4b-it-q4_K_M` | ✅ 能，速度快 |
| 24GB+ Mac / 24GB 显存 | `gemma4:31b-it-q4_K_M` | ✅ 能，最强 |
| 磁盘可用 < 10GB | — | ❌ 先清磁盘 |

> ⚠️ **磁盘提醒**：模型下载后不会自动删。8GB 机器建议只留 1 个模型。
> 换模型前先 `ollama rm <旧模型名>` 腾空间。

---

## 第 1 步：安装 Ollama

### macOS

最简单的方式是官网下载双击安装：<https://ollama.com/download>

如果想用命令行（本文档采用的方式）：

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

> 我的实际经历：官网的 `Ollama-darwin.zip` 有 206 MB，网络慢时**一次下不完会失败**。
> 用下面的断点续传写法能扛住慢速/断线，强烈建议复制这一段：
>
> ```bash
> # 断点续传下载（可重复执行，直到显示"完整"）
> for i in 1 2 3 4 5; do
>   sz=$(stat -f%z ~/Ollama-darwin.zip 2>/dev/null || echo 0)
>   [ "$sz" -ge 206251392 ] && { echo "下载完整"; break; }
>   curl -fsSL -C - --max-time 580 -o ~/Ollama-darwin.zip \
>     "https://github.com/ollama/ollama/releases/latest/download/Ollama-darwin.zip"
> done
> unzip -q ~/Ollama-darwin.zip -d /Applications/
> ```
>
> `curl -C -` 是「从断点继续」，`--max-time 580` 防止单次卡死。多次循环直到字节数达标。

### Windows

从 <https://ollama.com/download> 下载 `.exe` 双击安装。

### 验证装好了

```bash
ollama --version
```

能看到版本号就成了。

---

## 第 2 步：启动服务并拉模型

**启动后台服务**（装完通常已自动启动，没有就手动跑）：

```bash
ollama serve
```

如果提示 `address already in use`，说明它已经在跑了，**不用管**，开另一个终端继续。

**拉模型**（另开一个终端）：

```bash
# 8GB 机器用这个
ollama pull gemma4:e2b-it-q4_K_M

# 16GB+ 机器可以用这个（质量更好）
# ollama pull gemma4:e4b-it-q4_K_M
```

拉完先**手动聊一句确认能用**：

```bash
ollama run gemma4:e2b-it-q4_K_M
# 进去后输入：介绍一下西亚斯学院
# 输入 /bye 退出
```

> 💡 第一个 token 会慢（要把 ~2GB 权重从磁盘载入内存），之后就快了。

---

## 第 3 步：跑这个技能包

```bash
cd <解压后的目录>/JingXueQing_C4D_agent-skill

# 3.1 环境自检 —— 确认 Ollama 在跑、模型在、设备信息对
python3 run_agent.py doctor
```

应该看到类似这样的输出：

```
[设备] Apple M1 / 8.0 GB RAM / macOS 14.5 (arm64)
[运行时] Ollama v0.x.x @ http://127.0.0.1:11434
[本地已装模型]
       · gemma4:e2b-it-q4_K_M        1.83 GB  Q4_K_M  2.3B
```

**注意**：本技能包只用 Python 标准库，**不需要 `pip install` 任何东西**。
Python 3.10+ 即可（macOS 自带的 `python3` 一般就够）。

### 3.2 先跑不需要模型的自测（秒级返回）

```bash
python3 run_agent.py selftest
```

输出 `7/7 通过` 说明工具层没问题。**这一步能在下载模型之前就把代码 bug 排除掉，
强烈建议先跑它。**

### 3.3 完整单元测试（66 个）

```bash
python3 -m unittest discover -s tests -v
```

### 3.4 核心：让 Agent 生成地图 ⭐

```bash
python3 run_agent.py map "给我生成一个 SIAS University 周边的地图"
```

这条命令会依次做：
1. 本地模型**自己决定**调用哪个工具（原生 function calling）
2. 工具返回真实计算结果 → 回灌模型 → 模型做下一步决策（多步）
3. 模型输出受 JSON schema 约束的地点数据
4. 渲染成 `../JingXueQing_C4D_map.html`

**首次运行会慢一点**（要载入权重），我这边实测总耗时见验证报告。

跑完后用浏览器打开：

```bash
open ../JingXueQing_C4D_map.html
```

地图能拖动、能缩放、点标记有中英文弹窗、左侧点卡片地图会飞过去。

---

## 第 4 步：多轮对话改地图 ⭐

```bash
python3 run_agent.py chat
```

```
你> 把图书馆删掉
Agent> 已删除 m1。（当前 6 个标记, 18.4 tok/s）

你> 加一个开封
Agent> 已添加开封。（当前 7 个标记, 17.9 tok/s）
```

状态存在 `data/map_state.json`，所以**关掉程序再回来还在**。

---

## 第 5 步：Level 3 / Level 4 能力

```bash
# 代码生成 Agent：模型写代码 → 受限执行 → 报错自动回灌修复
python3 run_agent.py code "统计 1 到 100 的质数个数，用 JSON 输出" --compare

# 视觉理解：把一张校园照片喂给本地多模态模型
python3 run_agent.py vision /path/to/你的照片.jpg

# 多档位对比（Level 4）
ollama pull gemma4:e2b-it-q8_0          # 先拉对照组模型
python3 run_agent.py bench --profiles e2b-q4,e2b-q8
```

---

## 第 6 步：生成证据截图

```bash
# 需要 Pillow，仅截图这一步用到
python3 -m pip install pillow
python make_evidence.py
```

会在 `JingXueQing_C4D_output_screenshots/` 下生成 6 张终端风格 PNG，
包含**模型名 + 版本 + 设备信息 + 实测 tok/s + 工具调用轨迹**，
每张图底部标注数据来源文件。

---

## 常见问题

**Q1: `无法连接本地 Ollama`**
```bash
ollama serve        # 另开一个终端保持它运行
curl http://127.0.0.1:11434/api/version   # 应该返回版本 JSON
```

**Q2: `模型输出不是合法 JSON`**
工具层会把真实报错回灌给模型自动重试（最多 2 轮）。仍然失败说明任务太复杂——
换成更具体的指令，比如 `"只生成 5 个点"`。换大模型（`--profile e4b-q4`）也能解决。

**Q3: 地图打开是空白**
腾讯地图 SDK 需要联网加载。按 F12 看控制台：
如果报 key 相关错误，说明你不在 WorkBuddy 环境里——需要去腾讯位置服务
<https://lbs.qq.com/dev/console/key/manage> 申请自己的 key，
然后按该平台文档把 key 配到 `map_render.py` 生成的 HTML 里。
（**在 WorkBuddy 内打开则无需任何 key**，走的是内置代理。）

**Q4: 推理很慢 / 机器发烫**
- 8GB 机器跑 E2B 属正常。`num_ctx` 从 8192 调小到 4096 会明显快一点
  （改 `config.py` 的 `DEFAULT_PROFILE.num_ctx`）。
- 关掉其他吃内存的 App。
- 用 `--profile e2b-mlx`（Apple Silicon 原生 MLX 后端），通常比默认 GGUF 快。

**Q5: 模型把坐标吐到非洲（0,0 附近）**
这是 2B 模型的真实缺陷，**技能包已经处理了**：`_sanitize()` 会把离郑州 500km
以上的坐标判定为幻觉并拉回校园。这属于代码层的正确性兜底，不是 bug。

**Q6: 想换地图数据源**
`sias_agent/tools.py` 里的 `KNOWLEDGE_BASE` 是内置的 10 条 POI。
换成全量在线数据要接腾讯地图地点搜索 API，但那会失去离线能力——
这是有意的取舍，见方案设计第 7 节。

---

## 命令速查表

| 我想…… | 命令 |
|---|---|
| 检查环境 | `python3 run_agent.py doctor` |
| 快速验证代码没坏 | `python3 run_agent.py selftest` |
| 生成地图 | `python3 run_agent.py map "你的指令"` |
| 换模型档位 | `python3 run_agent.py map "..." --profile e2b-q8` |
| 多轮改地图 | `python3 run_agent.py chat` |
| 跑全部单测 | `python3 -m unittest discover -s tests` |
| 代码生成 | `python3 run_agent.py code "你的需求"` |
| 视觉理解 | `python3 run_agent.py vision 图片路径` |
| 模型对比 | `python3 run_agent.py bench --profiles e2b-q4,e2b-q8` |
| 生成截图 | `python3 make_evidence.py` |
