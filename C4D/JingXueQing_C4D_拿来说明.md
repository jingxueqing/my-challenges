# 拿来说明：用了什么、参考了什么

> 挑战要求「说明用了哪些库/工具、参考了什么」。这里写得尽量具体，包括**踩过的坑**。

---

## 1. 运行时与工具

| 类别 | 用了什么 | 为什么选它 | 许可证 |
|---|---|---|---|
| 本地推理运行时 | **Ollama v0.40.2**（macOS 版，官方 .app） | 挑战推荐首选；自带 OpenAI 兼容 API；一条命令起服务 | MIT |
| 本地模型 | **Gemma 4 E2B**（`gemma4:e2b-it-q4_K_M`，2.3B 有效参数 / 3.5GB 权重） | 8GB 统一内存下唯一稳定档位 | **Apache 2.0** |
| 地图渲染 | **腾讯地图 GL JS v1.exp** | 合规要求只能用腾讯/高德/百度/天地图；GL JS 支持矢量图、自定义 MarkerStyle、无 Leaflet 那样严的类名坑 | 商业服务，需合规申请 |
| 语言 | **Python 3.13.12**（macOS 原生，纯标准库） | 技能包零第三方依赖，`git clone` 完就能跑 | PSF |
| 测试 | `unittest`（标准库） | 不引入 pytest = 评审少装一个东西 | PSF |
| 截图生成 | **Pillow 12.3.0**（仅 `make_evidence.py` 需要） | 把真实日志渲染成 PNG；技能包主功能不依赖它 | HPND |

**明确没用**：OpenAI/Anthropic/Gemini API、LangChain、LlamaIndex、向量数据库、
Folium、Leaflet、Mapbox、OpenStreetMap、任何地图 API key。

---

## 2. 知识来源

| 来源 | 用途 | 怎么用的 |
|---|---|---|
| Google《Gemma 4 发布博客》 | 确认四款模型的参数/上下文/定位 | 选型依据：E2B 定位为 mobile/edge 设备 |
| Google《Gemma 4 Model Card》 | 核对架构细节（PLE、hybrid attention、E2B = 2.3B 有效/5.1B 含 embedding、128K 上下文） | 写方案设计第 1 节的选型论证 |
| Google Developers Blog《Bring agentic skills to the edge with Gemma 4》 | 理解 Agent Skills 的设计范式 | 参考了它「skill 扩展模型能力边界」的思路 |
| Ollama 官方模型库页面 | 列出 `gemma4:*` 的**真实可用 tag** | 发现实际 tag 与挑战文档写法不同（见下节踩坑 ②） |
| 郑州市公开地理常识 + haversine 公式 | `KNOWLEDGE_BASE` 的 10 条 POI 坐标 | 我本人所在地认知，量级经 haversine 自校验 |

**我没有伪造的地方**：POI 坐标是「量级正确、位置合理」的近似值，
不是从官方 POI 数据库导出的精确值。工具层据此计算的**相对距离**是可靠的，
绝对坐标有百米级误差。这在验证报告的局限性一节里明确写了。

---

## 3. 踩过的坑（这部分我认为比成功经验更有价值）

### 坑 ①：Ollama 官方包 206MB，网络慢时反复下载失败

`curl https://ollama.com/install.sh | sh` 在我这台机器上超时了。改成手动下载时
又遇到单次 900s 只能下到 160MB。

**解法**：断点续传循环 —— `curl -C -`（从断点继续）+ 按字节数判断完成：

```bash
for i in 1 2 3 4 5; do
  sz=$(stat -f%z ~/Ollama-darwin.zip 2>/dev/null || echo 0)
  [ "$sz" -ge 206251392 ] && { echo "下载完整"; break; }
  curl -fsSL -C - --max-time 580 -o ~/Ollama-darwin.zip \
    "https://github.com/ollama/ollama/releases/latest/download/Ollama-darwin.zip"
done
```

这条已经写进教学说明，因为**任何人都可能遇到**。

### 坑 ②：挑战文档里的 tag 与实际可用 tag 不一致

挑战文档写 `ollama run gemma4:e2b` / `ollama run gemma4:26b`。
我实际查 `ollama.com/library/gemma4/tags` 后发现真实 tag 是：

```
gemma4:e2b-it-q4_K_M   gemma4:e4b-it-q4_K_M   gemma4:26b-a4b-it-q4_K_M
gemma4:31b-it-q4_K_M   gemma4:e2b-mlx        gemma4:e2b-it-q8_0  ...
```

即**必须带 `-it-`（instruction-tuned）和量化后缀**，`gemma4:e2b` 这个 tag 并不存在。
如果直接照抄挑战文档会卡在这一步。教学说明里用的是真实 tag。

### 坑 ③：把 ollama 二进制拷到别处会丢 GPU runner

`cp /Applications/Ollama.app/Contents/Resources/ollama ~/.local/bin/ollama` 之后，
CLI 能用、`--version` 正常，但 `serve` 找不到推理后端：

```
failure during llama-server GPU discovery ... llama-server binary not found
inference compute id=cpu library=cpu  ← 退化成纯 CPU
```

原因是 `ollama` 会**相对自身路径**去找同目录的 `llama-server` 和一堆 `libggml-*.so`。

**解法**：把 CLI 装到 `~/.local/bin` 供日常使用，但 **`serve` 必须回到
`/Applications/Ollama.app/Contents/Resources/` 目录下执行**。改完后正确识别到：

```
inference compute id=0 library=Metal compute=0.0 name=MTL0
  description="Apple M1" total="5.3 GiB" available="5.3 GiB"
```

### 坑 ④：registry.ollama.ai 偶发连不上

`curl https://registry.ollama.ai/v2/` 反复超时（DNS 能解析，TCP 握手不通），
但 `ollama.com` 正常。这导致 `ollama pull` 卡在 `pulling manifest` 不动。

**解法**：重试即可 —— 稍后再试 manifest 就返回 200 了。
另外 **`ollama pull` 支持断点续传**，中途失败直接重跑同一条命令即可，
它会从已下载的分片继续（我这次从 925MB → 1.6GB → 完成）。

### 坑 ⑤：沙箱环境下 `mkdir(exist_ok=True)` 会抛 EEXIST

写 `_save()` 和截图脚本时踩到：

```
PermissionError: EEXIST: file already exists, mkdir '.../reports'
```

成因是运行环境的路径代理拦截了 `mkdir`。**解法**：先 `if not DIR.is_dir(): DIR.mkdir(...)`。
两处代码都改成了这个写法，教学说明里的复现步骤在普通终端不会遇到，但这是环境的坑。

### 坑 ⑥：单元测试抓出的两个真实 bug

我没有只写「跑通就行」的 demo，而是写了 66 个断言。它们抓到了两个我自己没预料的问题：

**bug A — `reverse_geocode` 参数命名不一致。**
函数签名是 `lat/lng`，但我在测试和模型输出里都用了 `latitude/longitude`，
结果 `TypeError: missing 1 required positional argument: 'lng'`。
2B 模型**经常混用这两套命名**，所以这不是测试写错了，是接口设计太脆。
**修法**：让函数同时接受两种命名，把模型的噪声吸收在工具层。

**bug B — 地图 HTML 的 XSS 漏洞。**
卡片区用了 `html.escape()`，但**注入到 JS 里的 `properties` 没有转义**：
地点名如果含 `<script>`，会经 `InfoWindow` 的 `innerHTML` 执行。
这是真漏洞（虽然输入来自本地模型，但知识库是外部可编辑的数据）。
**修法**：JS 数据区的所有字符串同样 `html.escape()`；测试加了
`test_escapes_html` 回归断言（同时验证 `<img onerror=` 变体）。

---

## 4. 我做的取舍（以及放弃了什么）

| 放弃了 | 换来的 | 我的判断 |
|---|---|---|
| **Folium/Leaflet + OSM**（挑战原示例） | 腾讯地图 GL JS | 必须的。OSM 是境外地图源，不合规；且我想要矢量底图 + 自定义 SVG MarkerStyle |
| 全量在线 POI 检索 | 内置 10 条知识库 | 「断网也能跑」是这个挑战的核心主张，用在线 API 就自相矛盾了。教学说明 Q6 写了怎么改回来 |
| 向量数据库 / RAG | 关键词 + bigram 模糊匹配 | 只有 10 条数据，上向量库是过度设计 |
| 一个大而全的 Agent 框架（LangChain 等） | 271 行的 ReAct 循环 | 自己写能看清每一步在干什么，且评审能一眼看懂没有黑箱 |
| 跨设备对比数据（Level 4 要求之一） | —— | **我只有一台 MacBook Air。编不出 Windows/Android 的数据，所以不写。** |

---

## 5. 可复现性承诺

评审可以这样验证我的每一个数字：

```bash
# 1. 确认设备与模型（实采，不是我手写的）
python3 run_agent.py doctor

# 2. 复现工具层正确性（66 个断言，含 haversine 物理常数校验）
python3 -m unittest discover -s tests

# 3. 复现完整 Agent 运行（会重新调本地模型）
python3 run_agent.py map "给我生成一个 SIAS University 周边的地图"

# 4. 核对报告里的每个数字来自哪个文件
cat reports/run_report.json
```

截图里出现的每一个 `tok/s`、模型版本、内存大小，都能在 `reports/*.json`
里找到对应字段，且该字段是由 `sysctl` / Ollama API **实时采集**的。
截图底部也标注了来源文件。

---

## 6. AI 在这个项目里做了什么（人机分工）

| 环节 | 谁做的 | 说明 |
|---|---|---|
| 需求拆解、架构设计、选型论证 | **我（人）** | 决定「工具层必须离线」「证据代码分离」「坐标几何自检」三条原则 |
| 查文档、核对 tag、踩坑排查 | **AI + 联网检索** | 坑 ②③④ 都是 AI 检索 + 我实机验证找到的 |
| 工具层 / Agent 循环 / 地图渲染 | **AI 写，我审** | 我逐个模块 review，并坚持要求它写测试；bug A/B 是测试抓出来的 |
| 单元测试 | **AI 写 66 个断言，我补反例** | 我追加了 XSS 变体、500km 幻觉坐标、未知工具等边界用例 |
| 文档 | **AI 起草，我补真实踩坑记录** | 坑 ①–⑥ 全是我实机遇到的，一手材料 |
| 运行结果 | **本机实跑** | 无任何模拟数据 |

一句话：**架构和取舍是我做的，代码是 AI 写的，但每一个 bug 都是我的测试抓出来的。**
