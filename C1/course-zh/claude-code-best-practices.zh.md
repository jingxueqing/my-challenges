---
source_file: claude-code-best-practices.html
title: Claude Code 概览 - Claude Code 官方文档（Claude Code overview - Claude Code Docs）
---

# Claude Code 概览

Claude Code 是一个由 AI 驱动的编码助手，帮助你构建功能、修复缺陷并自动化开发任务。它理解你的整个代码库，能够跨多个文件和工具协同工作，把事情办成。

## 开始使用

选择你的环境开始上手。大多数界面都需要 Claude 订阅或 Anthropic Console 账户。终端 CLI 和 VS Code 也支持第三方提供商。

- 终端
- VS Code
- 桌面应用
- Web
- JetBrains

功能完整的 CLI，可直接在终端中使用 Claude Code。通过命令行编辑文件、运行命令并管理你的整个项目。

安装 Claude Code，可选用以下方法之一：

- 原生安装（推荐）
- Homebrew
- WinGet

macOS、Linux、WSL：

```
curl -fsSL https://claude.ai/install.sh | bash
```

Windows PowerShell：

```
irm https://claude.ai/install.ps1 | iex
```

Windows CMD：

```
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

如果你看到 The token '&&' is not a valid statement separator，说明你正在使用的是 PowerShell 而不是 CMD。请改用上面的 PowerShell 命令。提示符显示 PS C:\ 时，你就在 PowerShell 中。

Windows 需要先安装 Git for Windows。如果尚未安装，请先安装它。

原生安装会在后台自动更新，让你始终使用最新版本。

```
brew install --cask claude-code
```

Homebrew 安装不会自动更新。请定期运行 brew upgrade claude-code 以获取最新功能和安全修复。

```
winget install Anthropic.ClaudeCode
```

WinGet 安装不会自动更新。请定期运行 winget upgrade Anthropic.ClaudeCode 以获取最新功能和安全修复。

然后在任意项目中启动 Claude Code：

```
cd your-project
claude
```

首次使用时会提示你登录。就这么简单！

继续阅读快速入门 →

关于安装选项、手动更新或卸载说明，请参阅高级设置。如果遇到问题，请访问故障排查页面。

VS Code 扩展直接在编辑器中提供内联差异（diff）、@ 提及、计划评审和会话历史。

- 为 VS Code 安装
- 为 Cursor 安装

或者在扩展视图（Mac 上 Cmd+Shift+X，Windows/Linux 上 Ctrl+Shift+X）中搜索"Claude Code"。安装后，打开命令面板（Cmd+Shift+P / Ctrl+Shift+P），输入"Claude Code"，然后选择 Open in New Tab。

开始使用 VS Code →

一个独立应用，让你在 IDE 或终端之外运行 Claude Code。以可视化方式评审差异、并行运行多个会话、安排周期性任务，以及启动云端会话。

下载并安装：

- macOS（Intel 和 Apple Silicon）
- Windows（x64）
- Windows ARM64（仅支持远程会话）

安装后，启动 Claude，登录，然后点击 Code 标签页开始编码。需要付费订阅。

进一步了解桌面应用 →

在浏览器中运行 Claude Code，无需任何本地配置。启动长时间运行的任务，完成后回来查看结果；处理你本地没有的仓库；或并行运行多个任务。支持桌面浏览器和 Claude iOS 应用。

在 claude.ai/code 开始编码。

在 Web 上开始使用 →

适用于 IntelliJ IDEA、PyCharm、WebStorm 和其他 JetBrains IDE 的插件，支持交互式差异查看和选区上下文共享。

从 JetBrains Marketplace 安装 Claude Code 插件，然后重启你的 IDE。

开始使用 JetBrains →

## 你能做什么

以下是使用 Claude Code 的一些方式：

把你一直拖延的工作自动化

Claude Code 能处理那些吞噬你一天时光的繁琐任务：为未经测试的代码编写测试、修复整个项目的 lint 错误、解决合并冲突、更新依赖，以及编写发布说明。

```
claude "write tests for the auth module, run them, and fix any failures"
```

构建功能与修复缺陷

用平实的语言描述你想要什么。Claude Code 会规划实现方案、跨多个文件编写代码，并验证其可用。

对于缺陷，粘贴一条错误信息或描述症状即可。Claude Code 会在你的代码库中追踪问题，定位根因并实现修复。更多示例参见常见工作流。

创建提交与拉取请求（PR）

Claude Code 直接与 git 协作。它会暂存变更、撰写提交信息、创建分支并打开拉取请求（PR）。

```
claude "commit my changes with a descriptive message"
```

在 CI 中，你可以用 GitHub Actions 或 GitLab 持续集成/持续交付（CI/CD） 自动化代码评审和问题分拣。

用模型上下文协议（MCP）连接你的工具

模型上下文协议（MCP）是一个开放标准，用于把 AI 工具连接到外部数据源。借助 MCP，Claude Code 可以读取你在 Google Drive 中的设计文档、更新 Jira 中的工单、从 Slack 拉取数据，或使用你自己的自定义工具。

用指令、技能和钩子（hooks）进行定制

CLAUDE.md 是一个添加到项目根目录的 markdown 文件，Claude Code 会在每次会话开始时读取它。你可以在其中设定编码规范、架构决策、偏好的库以及评审清单。Claude 还会在工作过程中构建自动记忆，把构建命令、调试心得等经验跨会话保存下来，而无需你编写任何内容。

创建自定义命令，把可复用的工作流打包，供团队共享，例如 /review-pr 或 /deploy-staging。

钩子（Hooks）让你在 Claude Code 操作之前或之后运行 shell 命令，例如每次文件编辑后自动格式化，或在提交前运行 lint。

运行智能体团队并构建自定义智能体

生成多个 Claude Code 智能体，同时处理任务的不同部分。由一个主智能体（lead agent）协调工作、分配子任务并合并结果。

对于完全自定义的工作流，Agent SDK 让你构建由 Claude Code 的工具与能力驱动的自定义智能体，并可完全掌控编排、工具访问和权限。

用 CLI 进行管道、脚本化和自动化

Claude Code 是可组合的，遵循 Unix 哲学。你可以把日志通过管道输入给它、在 CI 中运行它，或与其他工具串联：

```
# Analyze recent log output
tail -200 app.log | claude -p "Slack me if you see any anomalies"

# Automate translations in CI
claude -p "translate new strings into French and raise a PR for review"

# Bulk operations across files
git diff main --name-only | claude -p "review these changed files for security issues"
```

完整的命令与参数列表请参阅 CLI 参考。

安排周期性任务

按计划运行 Claude，自动化重复性工作：早晨的拉取请求（PR）评审、通宵的 CI 失败分析、每周的依赖审计，或在拉取请求合并后同步文档。

- 云端计划任务运行在 Anthropic 托管的基础设施上，即使你的电脑关机也会继续运行。可以从 Web、桌面应用创建，或在 CLI 中运行 /schedule。
- 桌面计划任务在你的机器上运行，可直接访问你的本地文件和工具
- /loop 在 CLI 会话内重复某个提示词，适合快速轮询

随处工作

会话不绑定于单一界面。随着你的场景变化，可在不同环境之间转移工作：

- 离开工位后，使用 Remote Control 从手机或任意浏览器继续工作
- 用消息调度（Message Dispatch）从手机派发任务，然后打开它在桌面端创建的会话
- 在 Web 或 iOS 应用上启动一个长时间运行的任务，然后用 claude --teleport 拉入你的终端
- 用 /desktop 把终端会话交给桌面应用，进行可视化的差异评审
- 从团队聊天中路由任务：在 Slack 中带上缺陷报告 @Claude，即可收回一个拉取请求（PR）

## 在所有地方使用 Claude Code

每个界面都连接到同一个底层 Claude Code 引擎，因此你的 CLAUDE.md 文件、设置和 MCP 服务器在所有界面间通用。

除了上文介绍的终端、VS Code、JetBrains、桌面端和 Web 环境之外，Claude Code 还可与 CI/CD、聊天和浏览器工作流集成：

| 我想…… | 最佳选择 |
| 从手机或其他设备继续本地会话 | Remote Control |
| 将来自 Telegram、Discord、iMessage 或我自己 webhook 的事件推送到会话中 | Channels |
| 本地启动任务，在移动端继续 | Web 或 Claude iOS 应用 |
| 按周期计划运行 Claude | 云端计划任务或桌面计划任务 |
| 自动化拉取请求（PR）评审和问题分拣 | GitHub Actions 或 GitLab CI/CD |
| 为每个拉取请求（PR）获取自动代码评审 | GitHub Code Review |
| 把缺陷报告从 Slack 路由到拉取请求（PR） | Slack |
| 调试实时 Web 应用 | Chrome |
| 为自己的工作流构建自定义智能体 | Agent SDK |

## 后续步骤

安装 Claude Code 之后，以下指南可以帮助你深入使用。

- 快速入门：完成你的第一个真实任务，从探索代码库到提交修复
- 存储指令与记忆：用 CLAUDE.md 文件和自动记忆为 Claude 提供持久化指令
- 常见工作流与最佳实践：充分发挥 Claude Code 价值的模式
- 设置：为你的工作流定制 Claude Code
- 故障排查：常见问题的解决方案
- code.claude.com：演示、定价与产品详情
