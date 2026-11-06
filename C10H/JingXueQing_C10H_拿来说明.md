# JingXueQing_C10H_拿来说明

> 参照挑战要求：说清楚「拿了什么」「怎么配置的」「在哪做了个性化修改」，以及我对这套系统架构的理解程度。

---

## 1. 拿了什么（清单）

整包拿的是 **NousResearch/hermes-agent**（MIT，main 分支 commit `44ec783a`，2026-09-24 版本，本地实测约 1.06 百万行 Python，不含测试）。

| 拿来的东西 | 位置 | 规模（实测） |
|---|---|---|
| Agent 核心（推理循环、上下文压缩、模型适配） | `agent/` | 422 个文件，13.6 万行 |
| 工具实现 | `tools/` | 380 个文件（含 `memory_tool.py`、`skill_manager_tool.py`、`cronjob_tools.py`） |
| 消息网关与平台适配 | `gateway/`、`gateway/platforms/` | 356 个文件（Telegram/Discord/Slack/WhatsApp/Signal/Webhook/API server…） |
| CLI 与子命令 | `hermes_cli/` | 825 个文件 |
| 定时调度 | `cron/` | 55 个文件 |
| 内置技能库 | `skills/` | 307 个文件（安装后 44 个技能） |
| 环境管理 | `pm/`、`setup-hermes.sh`、`uv.lock` | 哈希校验的依赖与工具链安装器 |

**没拿、自己写的**：`SOUL.md`（人格）、`challenge-deliverable-check` 技能（含 `check_deliverables.py`）、配置选择、本说明与全部交付文档。

---

## 2. 它是怎么搭起来的（架构理解，按我能验证的层次说）

### 2.1 一条消息的旅程

```
入口（CLI / 网关平台）
   → hermes_cli / gateway.run 收下消息，落 state.db（SQLite WAL + FTS5）
   → prompt_builder 组装 system prompt：
        SOUL.md（身份槽位#1）
        + MEMORY.md / USER.md（冻结快照，带字符配额头）
        + 工具 schema（按 toolset 启停）
        + 技能索引（只放 name+description，正文按需 skill_view 加载）
   → agent 循环：模型 → 工具调用 → 结果回灌 → 再问，直到收敛
   → 回复写回 state.db，按目标平台投递
```

这条链路我是**逐段验证过**的，不是读 README 猜的：

- SOUL.md 生效：换人格前后自我介绍完全不同（见配置说明 §4）。
- 记忆冻结快照：新会话里 `0 tool calls` 就答出 `~/Desktop/我的挑战`，说明是 prompt 注入而非检索。
- 技能按需加载：cron 输出文件里能看到 `[IMPORTANT: The user has invoked the "challenge-deliverable-check" skill…]` + 技能全文被拼进 prompt。
- FTS5：`select count(*) from messages_fts where messages_fts match '"config.yaml"'` → 15 条。

### 2.2 三个值得学的设计

1. **记忆有配额，且拒绝静默丢弃。** MEMORY.md 2200 字符 / USER.md 1375 字符，超限时工具**报错**让 agent 自己整理，而不是悄悄截断。这比「无限记忆」更诚实——它逼 agent 做取舍。
2. **技能是文档而非代码。** SKILL.md 只有元数据 + 操作手册，正文按需读，索引只放 60 字符以内的 description。307 个技能文件在 prompt 里只占几百 token，这是「可扩展」的关键。
3. **`pm` 把环境当产物管。** `uv.lock` 哈希校验、工具（node/ffmpeg/chromium）钉版本、venv 可重建。我这台机器上它扛住了一次 SSL 抖动并自动重试成功——环境是「可复现的构建结果」，不是「我机灵地装好了」。

### 2.3 我看不惯的地方（拿来主义不等于全盘接受）

- **installer 假定网络无痛。** `--filter=blob:none` 拉全历史，在慢网下等于不可用，且没有「只装工作树」的开关。官方 dev 入口 `setup-hermes.sh` 明明能做到，installer 却不复用这条路径。
- **`doctor` 与配置注释不一致。** 注释说 `ollama` 是 `custom` 的别名，`doctor` 却按白名单报错。用户会在「照注释写」和「照校验写」之间来回。
- **≥64,000 上下文的硬门槛对小机器不友好。** 门槛本身合理（工具调用确实吃上下文），但它把「8 GB 笔记本 + 小模型」这条路直接判死，且报错文案只在运行期才出现，安装阶段无预警。
- **默认工具集对小模型过量。** 21 个 schema 一起上，4.6B 模型直接迷路。建议按模型能力自动降级工具集。

---

## 3. 我在哪里做了个性化（逐项可查）

| 改动 | 文件 / 命令 | 性质 |
|---|---|---|
| 人格「阿衡」 | `~/.hermes/SOUL.md`（副本 `JingXueQing_C10H_SOUL.md`） | 原创 |
| 自定义技能 | `~/.hermes/skills/challenge-deliverable-check/`（SKILL.md + scripts/check_deliverables.py，159 行 Python，仅标准库） | 原创 |
| provider 选型 | `custom` + 本地 Ollama，而非默认 OpenRouter | 配置决策 |
| 上下文策略 | 删除手写覆盖，交由自动探测（131072） | 配置决策 |
| 工具集策略 | 任务级 `-t file` / `-t memory` 收窄 | 使用方法论 |
| 定时任务 | `c71b73122cf4`，每日 21:00，绑定自定义技能 | 原创编排 |
| 平台接入 | Webhook 路由 `deliverable-check` + HMAC 密钥 + 端口 8644 | 原创集成 |
| 模型补充 | 自行拉取 `qwen3:4b-instruct` 并手工修复 blob/manifest | 环境攻坚 |

**没有改动 `hermes-agent` 的源码一行。** 所有个性化都落在 `~/.hermes/`（用户态）。这是有意的：源码可随时 `git pull`，定制不会与之打架。

---

## 4. 自定义技能为什么长这样

技能是 `challenge-deliverable-check`，解决的是我真实存在的重复劳动：C 系列挑战每次都要交一堆按 `<姓名拼音>_<挑战ID>_<描述>` 命名的文件，还要有 AI 日志，靠眼睛检查总会漏。

设计上遵循了 `skills/AGENTS.md` 里的硬性规范：

- `description` ≤60 字符、一句话、以句号收尾（`"Audit a challenge deliverable folder against its own naming rules."`，57 字符）；
- 章节顺序按官方要求：`# …Skill` → `When to Use` → `Prerequisites` → `How to Run` → `Quick Reference` → `Procedure` → `Pitfalls` → `Verification`；
- 复杂逻辑不塞进 prompt，而是落成 `scripts/check_deliverables.py`，由技能正文引用；
- 规则来源不写死，从挑战包的 `challenge.yaml` 读 `deliverables_pattern` / `id` / `deadline`——换一个挑战不用改技能。

技能的实际产出见 `JingXueQing_C10H_自定义技能/`，本次交付自检就是用它跑的（`README_提交说明.md` 附了输出）。
