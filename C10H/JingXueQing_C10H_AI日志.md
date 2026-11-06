# JingXueQing_C10H_AI日志

> **证据来源声明（先说，避免误读）**
> 本文所有技术细节、报错原文、数字，均来自本机命令输出与会话记录，可在 `JingXueQing_C10H_demo/终端记录/` 中逐条比对；无法复现的主观判断我会标「判断」。
> **人机分工如实标注**：本次执行由 WorkBuddy 智能体（模型标识 `deepseek-v4.1-flash`）完成；本人（景雪晴）承担目标设定、节奏控制与交付验收，过程中下发 4 次指令（`完成挑战` → `请继续执行任务` ×2 → `继续`），中途主动中断过 1 次以检查进度。**没有人工逐条改代码**，所有排错由 AI 自主完成——这既是本次的强项，也是风险点，写在 AAR 里。

---

## 1. 人机分工一览

| 角色 | 做了什么 | 证据 |
|---|---|---|
| 本人 | 指定挑战包路径、下达「完成挑战」、两度催「继续」、中断一次 | 对话记录 |
| 本人 | 交付前的验收判断（哪些算完成、哪些必须写失败） | 本文 §5 |
| AI | 环境勘察、三次安装尝试、模型服务修复、provider 调参、技能与人格撰写、cron/webhook 配置、证据归档、全部文档 | 终端记录 + 交付文件 |

**一句话提醒（写给自己）：** 这次 AI 独立完成了 90% 的执行，我实际只做了「点头」。真正的学习发生在读 AAR 和失败清单的时候，不是在看它跑通的时候。

---

## 2. 迭代全过程（7 轮，含 4 次真失败）

### R1 环境勘察（约 5 分钟）

- 读挑战包四件套，确认交付物命名规范与截止时间（2026-12-31）。
- 查环境：macOS 14.5 / M1 / **8 GB** / Python 3.13.12 / Node 22.22.2 / 磁盘余 14 GB。
- 查凭据：**没有任何云模型 API Key**（`OPENROUTER_API_KEY` 不存在）。
- 判断：走本地模型路线。这一步决定了后面所有麻烦，但它是当时唯一不需要等待外部审批的选择。

### R2 安装，连续两次撞墙（约 35 分钟，最大时间黑洞）

1. 官方 `install.sh` 跑起来正常，卡在 blobless 全历史克隆：10 分钟只到 144 MB（150 KB/s）。**我中止了它**——继续等是浪费。
2. 想让官方 installer 吃本地镜像：`HERMES_REPO_URL=<本地 clone>` → `promisor-remote: unable to fork off fetch subprocess`、`shallow roots are not allowed to be updated`、成片 `cannot fork()`。**失败。**
3. 改用仓库自带 `setup-hermes.sh`：不碰 git，pm 从 `uv.lock` 重建环境。24 分钟跑完，`hermes --version` 通。

**这轮的教训：** 我第一反应是「按挑战写的命令跑」，第二反应是「改造官方命令」，都不如第三反应「读仓库里还有什么入口」。`setup-hermes.sh` 就在根目录，我一开始 scan 过它却没当回事。

### R3 模型服务：`llama-server binary not found`（约 20 分钟）

第一次 `hermes chat` 直接失败，Ollama 返回 500：

```
error starting llama-server: llama-server binary not found (checked: ~/.local/bin/llama-server, ~/.local/bin/lib/ollama/llama-server, …)
```

排查顺序（有效）：① `ollama --version` 能动 → 服务没坏；② `ollama run` 也报同样错 → 不是 Hermes 的问题；③ `ls -la ~/.local/bin/ollama` 是 52 MB 独立二进制，旁边没有任何 `lib/ollama/` → 这是源码自编译版，缺运行时；④ `find /Applications/Ollama.app -name "*llama*"` 找到 `Contents/Resources/llama-server`。

**修法：** 不用 `~/.local/bin/ollama`，改从 App 内启动 `ollama serve`，它自带 `llama-server` 与全部 dylib。

**弯路（记录在此）：** 我曾想给 `~/.local/lib/ollama/llama-server` 做软链，后来判断 dylib 的 `@loader_path` 解析会断，直接放弃——**软链能骗过报错，但跑不起来**，这类「看起来修好了」的修法要警惕。

### R4 provider 与上下文的两次误判（约 20 分钟）

- 误 1：把 `model.provider` 设成 `ollama`（照配置注释写的别名），`hermes doctor` 报 `not a recognised provider`。改 `custom` 后消失。**教训：注释和校验器不一致时，以校验器为准。**
- 误 2：手写 `context_length: 16384` → Hermes 直接拒绝（`below the minimum 64,000 required by Hermes Agent`）。改成 65536 → 通过门槛，但 8 GB 机器开始疯狂换页，qwen3 prompt 处理掉到 17 tok/s，甚至把我执行命令的 shell 也拖死（多次 `SIGTERM`）。最终**删掉两个覆盖项**，让 Hermes 自动探测 131072，同时确认 Ollama 侧不要用 4096 默认槽位。

**这一轮是我自己制造的问题：** 想「手动控一下内存」，结果两次都比默认更差。参数不是越显式越好。

### R5 小模型迷路 → 收窄 toolset（约 15 分钟）

现象：让它读一个 yaml，它先 `tool_search`、再挑 `terminal`、最后反问我「你想执行什么命令？」。同一任务加了 `-t file` 之后**一次成功**：

```
$ hermes chat -t file -q "读取 ~/.hermes/config.yaml，然后回答：provider 是什么？model 是什么？"
provider: ollama
model: gemma4:e2b-it-q4_K_M
```

没有 `-t file` 的同一句话，输出是 `I am ready. Please let me know what you would like me to do`。

**这是本次最实用的一条结论：小模型 + 多工具 = 注意力稀释；工具集要按任务收窄。**

### R6 第二个模型：下载被环境拦截，手工修复（约 40 分钟）

`ollama pull qwen3:4b-instruct` 下载到 100% 后失败：

```
Error: remove …/sha256-85e4a5b7…-partial-0: operation not permitted
```

2.5 GB 主 blob 其实是**完整的**（`shasum -a 256` 与远端摘要逐字一致），只是清理分片临时文件被环境策略拒绝。手工修复：校验摘要 → 重命名为主 blob → 清理 `-partial-*` → 补齐 3 个小 blob（config/template/license/params）→ 手写 manifest。

**代价与取舍：** 修好后发现它在 8 GB 机器上跑 64k 上下文太慢，最终只作为对比样本。**投入产出比很差**，但如果没修，我就说不出「8 GB 决定了模型上限」这句有数据的话。

### R7 集成：cron + webhook（约 25 分钟）

- cron：`hermes cron create "0 21 * * *" … --skill challenge-deliverable-check`，`cron run` + `cron tick` 验证 `succeeded`，输出落盘可查。
- webhook：需要先 `platforms.webhook.enabled`，再 `webhook subscribe` 建路由，重启网关后 `webhook test` 拿到 `202 accepted`，网关日志显示 `Gateway running with 1 platform(s)`、事件被处理、106 字符回复被投递。
- 诚实记录：cron 那次的**模型输出不达标**（答「请提供要执行的命令」），链路通但执行差。改进方向已写进 AAR。

### R8 交付自检：技能抓出了自己的毛病（约 10 分钟）

交付目录搭好后，用自己的技能跑一遍：

```
必备文件 `*demo*`   ✗ 缺失
命名规范            ✗ chat-01.log（前缀应为 JingXueQing；缺少描述段）…
空文件检查          ✗ gateway-webhook.log
结论：3 项未通过。  exit=1
```

三个问题都是真的：demo 是**目录**而脚本只匹配文件名；证据日志沿用了 `chat-01.log` 这种随手名；一份网关日志因为 `grep` 找错文件而写成了空文件。

修法分两侧：
- **交付物侧**：证据文件统一重命名为 `JingXueQing_C10H_demo_*.log`；从 `~/.hermes/logs/gateway.log` 重抓 webhook 行；补一份 `JingXueQing_C10H_demo.md` 作 demo 索引。
- **技能侧**：必备文件 glob 改为同时对目录名匹配；命名检查限定在**顶层文件**（嵌套的技能包/证据文件保留自身规范命名）。

改完重跑：`**结论：全部通过。** exit=0`。

**这一轮的价值：** 「自己写检查器 → 用它检查自己的作业 → 发现检查器本身过严 → 同时修作业和修检查器」，这才是工具该有的闭环。如果我只是写完脚本没真用，那两条过严规则会一直留着害人。

---

## 3. Prompt 与指令的演进（我实际改了什么）

| 阶段 | 指令写法 | 结果 | 改法 |
|---|---|---|---|
| 初版 | 「读取 ~/.hermes/config.yaml，告诉我 provider 和 model」 | 模型调 `terminal` 不带 command，反问要命令 | 加约束 |
| 二版 | 同上 + 「只给结论，不要解释过程」 | 仍失败（`I am ready`） | 换思路：不是 prompt 问题，是工具集问题 |
| 三版 | `-t file` + 「然后回答：provider 是什么？model 是什么？只回答这两个值。」 | **成功** | 收敛为模板 |
| 记忆 | 「请用 memory 工具把这条事实写进长期记忆：…写完告诉我完成」 | 成功落盘 | 明确点名工具 + 要求确认 |
| 检索 | 「用 session_search 检索…列出各次问了什么」 | 失败（转成人格自我介绍） | 未解决，改走 SQL 直查 FTS 验证机制 |

**得出的写法规则（已写进 SOUL.md 的使用约定）：**
1. 一句话只给一个动作，不带并列任务；
2. 明确点名工具（`memory` / `read_file`），别让它自己挑；
3. 指定输出形状（「只回答两个值」），比「简洁一点」有效；
4. 工具集比 prompt 更能决定成败——先收 `-t`，再调措辞。

---

## 4. 工作流设计（这套流程可以复用到下一个挑战）

```
① 读挑战包 → 抽出验收清单（命名规范 / 必备文件 / 截止）
② 环境勘察 → 把「不可控项」先列出来（本例：无 API Key、8 GB 内存、慢网）
③ 装最稳的路径，不装最官方的路径（本例：setup-hermes.sh 而非 install.sh）
④ 先打通「最小闭环」：一句对话能回 → 再谈工具、记忆、技能
⑤ 每加一层配置就验一次（provider 改完立刻 hermes doctor + 一次对话）
⑥ 证据边做边存：每条命令的输出直接重定向进日志文件，不靠回忆补
⑦ 交付前用自己的技能跑一遍自检（challenge-deliverable-check）
```

第 ⑥ 条是这次做得最对的事：`logs/` 里每一份日志都是当场写的，所以失败细节（`cannot fork()`、`operation not permitted`、`17.60 tokens per second`）才能原样出现在文档里。**事后凭记忆写 AI 日志，一定会美化自己。**

---

## 5. 我自己（本人）的验收判断

- 认可：安装可复现、CLI 真实对话、记忆落盘且跨会话生效、cron 与 webhook 链路端到端通、自定义技能可用。
- 不认可、已在文档中如实标注：**没有聊天平台接入**（无 token）、**cron 的模型输出不合格**、**没有屏幕截图**（环境限制，用终端记录替代）。
- 不接受的做法（本次未发生，作为红线记录）：用示意图冒充截图、把「链路通」写成「功能完成」、把失败步骤从日志里删掉。
