# JingXueQing_C10H_配置说明

> 本文只写「我做了什么选择、为什么、怎么验证」，不复述安装步骤（见安装记录）。

---

## 1. 总体配置一览

| 层 | 选择 | 值 / 位置 |
|---|---|---|
| 推理 Provider | **custom**（OpenAI 兼容自建端点） | `base_url: http://127.0.0.1:11434/v1` |
| 主模型 | `gemma4:e2b-it-q4_K_M` | 本地 Ollama，131072 上下文 |
| 备选模型 | `qwen3:4b-instruct` | 已下载、已注册，仅对比用（见 §3） |
| 人格 | 自定义 SOUL.md「阿衡」 | `~/.hermes/SOUL.md` |
| 记忆 | 内置 MEMORY.md + USER.md | `~/.hermes/memories/` |
| 会话检索 | 内置 SQLite + FTS5 | `~/.hermes/state.db` |
| 工具集 | 默认 17/27 启用 | 任务时按需用 `-t` 收窄 |
| 定时任务 | 1 个（每日 21:00） | `hermes cron list` / id `c71b73122cf4` |
| 平台接入 | Webhook（HTTP 事件入口） | `http://localhost:8644/webhooks/deliverable-check` |
| 自定义技能 | `challenge-deliverable-check` | `~/.hermes/skills/challenge-deliverable-check/` |

配置文件：`~/.hermes/config.yaml`；密钥文件：`~/.hermes/.env`（本次无云密钥，故为空模板）。

---

## 2. 为什么是「本地 Ollama + custom provider」

挑战推荐 OpenRouter，**但本机没有任何云模型凭据**（无 `OPENROUTER_API_KEY`，也没有 OpenAI/Anthropic 等 Key），而且我不想把「能不能跑通」这件事押在申请 Key 的等待上。于是选了一条零成本、可离线复现的路：Ollama 本地服务，Hermes 侧当 OpenAI 兼容端点接。

三个具体选择：

1. **`provider` 写 `custom` 而不是 `ollama`。** 配置注释里说 `ollama` 是 `custom` 的别名，但 `hermes doctor` 用严格白名单校验，会报 `model.provider 'ollama' is not a recognised provider`。写 `custom` 后该报错消失（`doctor.log` vs `doctor2.log` 对照可查）。
2. **不写 `context_length` / `ollama_num_ctx`。** 我先手写了 16384，被 Hermes 挡下（硬性要求 ≥64,000）；改成 65536 又让 8 GB 机器开始换页。最终删掉两个覆盖项，让 Hermes 从 provider 自动探测——网关日志显示 `Model context warmed: gemma4:e2b-it-q4_K_M -> 131072 tokens (detected)`。
3. **模型服务必须用 `/Applications/Ollama.app/Contents/Resources/ollama serve`。** `~/.local/bin/ollama` 是源码自编译版，缺 `llama-server`，任何推理都会 500。App 内的二进制自带 `llama-server` 与 dylib，直接可用。

验证：

```bash
$ hermes chat -t memory -q "我是谁？我的挑战资料在哪？用一句话回答。" --oneshot
你是景雪晴，你的挑战资料目录在 ~/Desktop/我的挑战。
```

---

## 3. 两个模型的对比（同任务、同机器）

**任务：** 读取 `~/.hermes/config.yaml`，回答 provider 与 model 两个值。

| | gemma4:e2b-it-q4_K_M | qwen3:4b-instruct |
|---|---|---|
| 上下文 | 131072（探测值） | 262144（声明值） |
| 8 GB 机器上的 64k KV | 可承受 | 不可承受（大量换页） |
| 观测速度 | prompt 处理流畅；单轮 20–70 s | prompt 处理 17–25 tok/s（`ollama-64k.log` 实测行：`t = 523.50 s / 17.60 tokens per second`） |
| 读文件任务 | 成功：`provider: ollama`/`model: gemma4:…`（`chat-02.log`） | 未完成即中止 |
| 中文表达 | 通顺，偶有把两行粘成一行 | 更规整，但速度不可接受 |
| 结论 | **主力** | **备选，仅记录差异** |

**这条对比最值钱的结论不是「谁更聪明」，而是「8 GB 内存决定了模型上限」**：Hermes 强制 ≥64k 上下文，而 64k KV 在 8 GB 机器上基本把小模型锁死在「能跑但很慢」的区间。要在本机获得流畅体验，要么换更省 KV 的架构（gemma4 的 e2b 正是），要么加内存。

---

## 4. SOUL.md 定制（做了什么，为什么这么做）

完整文件：交付根目录的 `JingXueQing_C10H_SOUL.md`（线上生效文件为 `~/.hermes/SOUL.md`）。

设计取舍：

| 写进去的 | 为什么 |
|---|---|
| 名字「阿衡」+ 身份是「学习搭档」而非客服 | 名字要能用一句话解释来源：权衡 → 先看证据再判断，和我的工作方式一致 |
| 「禁止编造命令输出、文件内容、行号」 | 这是我最在意的一条。AI 编造证据比答错更贵 |
| 「结论必须落到 path:line / 命令输出 / 时间戳」 | 把「有证据」写成可执行的格式要求，而不是态度要求 |
| 「失败要留痕，失败的尝试和成功步骤同等重要」 | 本次安装两次失败，正是最有价值的部分；如果 SOUL 只奖励成功，日志就会失真 |
| 命名规范 `<姓名拼音>_<挑战ID>_<内容描述>` | 我的 C 系列挑战都是这个规范，写进人格就不用每次重复提醒 |
| 「删除/覆盖/对外发送前必须确认」 | 给自己划红线，避免它自作主张动我的文件 |

**效果验证（同一句提问，换 SOUL 前后）：**

- 换之前：`您好，我是一个大型语言模型，旨在理解和生成文本来帮助您完成各种任务。我目前运行在我的底层模型架构上。`
- 换之后：`任务接收。我是阿衡，负责将你的"想做的事"转化为"有证据地做完的事"。请提供你的第一个任务或目标。我将根据"证据优先"原则，规划可验收的里程碑。`

人格文件确实改变了输出，不是装饰。

---

## 5. 定时任务配置

```bash
hermes cron create "0 21 * * *" \
  "检查今天的 C10H 交付目录是否齐备：运行 challenge-deliverable-check 技能的脚本，把结果整理成三条要点。" \
  --name "C10H交付物自检" --deliver local --skill challenge-deliverable-check
```

结果：`Created job: c71b73122cf4`，next run `2026-11-06T21:00:00+08:00`。

立即触发验证：

```bash
hermes cron run c71b73122cf4 && hermes cron tick
# → Ran now: succeeded.
# → runs: 87d0fd7c91b54aee9290f9b2bf9f3b3c  completed
```

产出落盘：`~/.hermes/cron/output/c71b73122cf4/2026-11-06_15-41-28.md`，文件里能看到技能全文被注入 prompt（`[IMPORTANT: The user has invoked the "challenge-deliverable-check" skill…]`），证明 **cron + 技能绑定**链路是通的。

> 诚实补一句：这次输出内容不理想——模型答「请提供要执行的命令」，没真去跑脚本。调度、技能注入、结果归档三段都正常，输在模型执行力。这条已写进 AAR 的改进项（改成 `--script` 纯脚本模式，不让模型自由发挥）。

---

## 6. 平台接入配置（Webhook）

挑战 Level 2 要求「至少一个消息平台」。我如实说明：**聊天类平台（Telegram/Discord/Slack）需要一个真实的 bot token，本次没有可用账号**，无法凭空造出。我改用了 Hermes 自带的 **webhook 平台**——它是网关的一个真实入站通道（HTTP + HMAC 签名），能证明「外部系统 → 网关 → agent → 回传」整条链路。

```bash
hermes config set platforms.webhook.enabled true
hermes config set platforms.webhook.extra.port 8644
hermes config set platforms.webhook.extra.secret "$(openssl rand -hex 24)"
hermes webhook subscribe deliverable-check \
  --prompt "外部系统提交了交付目录 {directory}，请检查是否齐备并给三条要点。" \
  --skills challenge-deliverable-check --deliver log
hermes gateway run --quiet
hermes webhook test deliverable-check --payload '{"directory":"/Users/jingxueqing/Desktop/C10H-交付_JingXueQing_Hermes-Agent"}'
```

实测回执与网关日志：

```
Response (202): {"status": "accepted", "route": "deliverable-check", "event": "test", "delivery_id": "7d762cf71489452ba89288a318dacb26"}

[webhook] Reloaded 1 dynamic route(s): deliverable-check
[webhook] Listening on * (all interfaces, IPv4+IPv6):8644 — routes: deliverable-check
✓ webhook connected
Gateway running with 1 platform(s)
[webhook] POST event=test route=deliverable-check prompt_len=3349 delivery=7d762cf7…
response ready: platform=webhook …
[Webhook] Sending response (106 chars) to webhook:v2:…
```

即：网关确实以「1 个平台」在跑，事件被接受、agent 被唤起、回复被投递。这条比截图更能说明问题——它是端到端闭环。

---

## 7. 工具集策略（小模型的关键调参）

默认 17 个工具集、21 个 tool schema 一起上，4.6B 模型会「迷路」：它先 `tool_search`、再挑错工具、最后问「你要我执行什么命令？」。

**有效做法：按任务用 `-t` 收窄工具集。**

```bash
hermes chat -t file  -q "读取 ~/.hermes/config.yaml，回答 provider 和 model" --oneshot   # 成功
hermes chat -t memory -q "用 memory 工具记住：…" --oneshot                                # 成功
hermes chat          -q "读取 ~/.hermes/config.yaml …" --oneshot                          # 失败（答 I am ready）
```

同一句话，加不加 `-t file` 是「成功」与「答非所问」的区别。这条经验已写进 SOUL.md 的使用约定里，也是本交付最可复用的一条调参心得。
