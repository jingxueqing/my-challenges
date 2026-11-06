# JingXueQing_C10H_demo — 演示索引

本次没有屏幕截图（环境限制，`screencapture`/浏览器截图被策略拦下），全部用**原样保存的终端输出**作为演示证据。文件都在 `JingXueQing_C10H_demo/终端记录/`，可直接 `cat` 复核。

## 一、安装与诊断

| 文件 | 内容 | 看什么 |
|---|---|---|
| `JingXueQing_C10H_demo_setup.log` | `setup-hermes.sh` 完整输出（约 24 分钟） | uv 0.13.5 落地、Python 3.14.9、工具链 ffmpeg/node/python/ripgrep/chromium/cua-driver 逐个 ✓、`Setup complete!` |
| `JingXueQing_C10H_demo_install-尝试1-官方脚本.log` | 官方 `install.sh` 中止前的输出 | blobless 克隆开始、`v0.23.0` 发布号 |
| `JingXueQing_C10H_demo_install-尝试2-本地镜像.log` | 本地镜像喂 installer 的失败现场 | `promisor-remote: unable to fork off fetch subprocess`、`shallow roots are not allowed to be updated`、成片 `cannot fork()` |
| `JingXueQing_C10H_demo_doctor.log` | 修复前的 `hermes doctor` | 含 `model.provider 'ollama' is not a recognised provider` |
| `JingXueQing_C10H_demo_doctor2.log` | 改为 `custom` 后的诊断 | 该错误消失，仅剩「可选 API Key 未配置」 |
| `JingXueQing_C10H_demo_status.log` | `hermes status` | Model/Provider/Gateway/Jobs 四项状态 |

## 二、对话与工具（核心演示）

| 文件 | 任务 | 结果 |
|---|---|---|
| `JingXueQing_C10H_demo_chat-01.log` | 默认工具集下让它读 `config.yaml` | **失败**：调了 2 次工具后答 `I am ready`（保留了失败证据） |
| `JingXueQing_C10H_demo_chat-02.log` | 加 `-t file` 收窄工具集，同任务重试 | **成功**：`provider: ollama` / `model: gemma4:e2b-it-q4_K_M` |
| `JingXueQing_C10H_demo_chat-03-memory.log` | 让它用 `memory` 工具写长期记忆 | **成功**：`~/.hermes/memories/MEMORY.md` 实际落盘 |
| `JingXueQing_C10H_demo_chat-04-recall.log` | 全新会话问「我的挑战资料在哪」 | **成功**：`0 tool calls` 直接答 `~/Desktop/我的挑战`（证明是 prompt 快照注入） |
| `JingXueQing_C10H_demo_chat-05-search.log` | 让它 `session_search` 检索历史 | **失败**：转成人格自我介绍，未检索（机制另行用 SQL 验证） |

## 三、系统能力

| 文件 | 内容 | 关键值 |
|---|---|---|
| `JingXueQing_C10H_demo_tools-summary.log` | `hermes tools --summary` | CLI 平台 `17/27` 启用，逐项列出 17 个 ✓ |
| `JingXueQing_C10H_demo_tools-list.log` | `hermes tools list` | 26 个内置工具集 + 1 个插件工具集，标注启用状态 |
| `JingXueQing_C10H_demo_skills-list.log` | `hermes skills list` | 44 个技能，首行即自定义技能 `challenge-deliverable-check`（local/本地信任） |
| `JingXueQing_C10H_demo_cron-list.log` | `hermes cron list` | 任务 `c71b73122cf4`，`0 21 * * *`，绑定技能，`Last run … ok` |
| `JingXueQing_C10H_demo_cron运行输出.md` | 一次 cron 运行的完整归档 | 能看到技能全文被注入 prompt；`Response` 段是模型实际回答（不合格，已如实记录） |
| `JingXueQing_C10H_demo_webhook-list.log` | `hermes webhook list` | 路由 URL `http://localhost:8644/webhooks/deliverable-check` |
| `JingXueQing_C10H_demo_gateway-webhook.log` | 网关日志（webhook 相关行） | `webhook connected`、`Gateway running with 1 platform(s)`、`POST event=test route=deliverable-check`、`Sending response (106 chars)` |

## 四、怎么快速复看

```bash
cd JingXueQing_C10H_demo/终端记录
grep -A6 "☤ Hermes" JingXueQing_C10H_demo_chat-02.log   # 看回答
grep -E "✓|Gateway running" JingXueQing_C10H_demo_gateway-webhook.log
tail -20 JingXueQing_C10H_demo_setup.log                # 看安装收尾
```

## 五、这份 demo 的诚实边界

- **失败也留着**：`chat-01`、`chat-05`、cron 的输出都不理想，我原样保留。删掉它们会让 demo 好看，但会让我无法解释 AAR 里的结论。
- **没有录屏**：动态交互（TUI 输入、流式输出）无法在此环境录制；`--oneshot` 模式下的完整输出已能反映同样的链路。
- **聊天平台缺席**：Telegram/Discord 需要真实 bot token，本机没有，因此用 webhook 平台做了端到端替代验证，边界写在配置说明 §6。
