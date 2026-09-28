---
source_file: mcp-server-authentication.html
title: 构建远程 MCP 服务器 · Cloudflare Agents 文档
---

astro:end

# 构建远程 MCP 服务器
本指南将向你展示如何使用
Streamable HTTP 传输
（当前的模型上下文协议（MCP）规范标准）在 Cloudflare 上部署你自己的远程 MCP 服务器。你有两个选择：

- 不带身份验证——任何人都可以连接并使用该服务器（无需登录）。
- 带身份验证与授权——用户在访问工具前需要登录，并且你可以根据用户权限控制智能体能调用哪些工具。


## 选择实现方式
Agents SDK 提供了多种创建 MCP 服务器的方式。请根据你的用例选择合适的方式：

| 方式 | 有状态？ | 是否需要 Durable Objects？ | 最适合 |
| createMcpHandler() | 否 | 否 | 无状态工具，最简单的设置 |
| McpAgent | 是 | 是 | 有状态工具、会话级状态、elicitation |
| 原生 WebStandardStreamableHTTPServerTransport | 否 | 否 | 完全控制，不依赖 SDK |

- createMcpHandler() 是让无状态 MCP 服务器跑起来的最快方式。当你的工具不需要会话级状态时可以使用它。
- McpAgent 为每个会话提供一个 Durable Object，内置状态管理、elicitation 支持，并同时支持 SSE 和 Streamable HTTP 传输。
- 原生传输让你获得完全控制权，适合想直接使用 @modelcontextprotocol/sdk 而不借助 Agents SDK 辅助工具的情况。


## 部署你的第一个 MCP 服务器
你可以先部署一个
不带身份验证的公开 MCP 服务器
↗，之后再添加用户身份验证和受限授权。如果你已经确定你的服务器需要身份验证，可以直接跳到
下一节
。


### 通过控制台
下面的按钮将引导你完成把一个
示例 MCP 服务器
↗部署到你的 Cloudflare 账户所需的全部步骤：

部署完成后，该服务器将在你的
workers.dev
子域名上线（例如，
remote-mcp-server-authless.your-account.workers.dev/mcp
）。你可以立即使用
AI Playground
↗
（一个远程 MCP 客户端）、
MCP inspector
↗
或
其他 MCP 客户端
连接到它。

一个全新的 git 仓库会在你的 GitHub 或 GitLab 账户上创建，并配置为每次你推送变更或合并拉取请求（PR）到仓库主分支时自动部署到 Cloudflare。你可以克隆这个仓库、
在本地开发
，并开始用你自己的
工具
定制 MCP 服务器。


### 通过 CLI
你可以使用
Wrangler CLI
在本地机器上创建一个新的 MCP 服务器并部署到 Cloudflare。

1. 打开终端并运行以下命令：npm create cloudflare@latest -- remote-mcp-server-authless --template=cloudflare/ai/demos/remote-mcp-authless yarn create cloudflare remote-mcp-server-authless --template=cloudflare/ai/demos/remote-mcp-authless pnpm create cloudflare@latest remote-mcp-server-authless --template=cloudflare/ai/demos/remote-mcp-authless 在设置过程中，选择以下选项： - 对于 Do you want to add an AGENTS.md file to help AI coding tools understand Cloudflare APIs? ，选择 No 。 - 对于 Do you want to use git for version control? ，选择 No 。 - 对于 Do you want to deploy your application? ，选择 No （我们会在部署前先测试服务器）。现在，MCP 服务器已设置完成，依赖也已安装。
2. 进入项目文件夹：终端窗口 cd remote-mcp-server-authless
3. 在新项目的目录中，运行以下命令启动开发服务器：终端窗口 npm start ⎔ Starting local server... [ wrangler:info ] Ready on http://localhost:8788 检查命令输出中的本地端口。在本例中，MCP 服务器运行在端口 8788 上，MCP 端点 URL 为 http://localhost:8788/mcp 。
4. 要在本地测试服务器：在一个新终端中运行 MCP inspector ↗ 。MCP inspector 是一个交互式 MCP 客户端，允许你连接到你的 MCP 服务器并从网页浏览器调用工具。终端窗口 npx @modelcontextprotocol/inspector@latest 🚀 MCP Inspector is up and running at: http://localhost:5173/?MCP_PROXY_AUTH_TOKEN =46ab..cd3 🌐 Opening browser... MCP Inspector 将在你的网页浏览器中启动。你也可以手动启动它：打开浏览器并访问 http://localhost:<PORT> 。检查命令输出中 MCP Inspector 运行所在的本地端口。在本例中，MCP Inspector 运行在端口 5173 上。在 MCP inspector 中，输入你的 MCP 服务器的 URL（ http://localhost:8788/mcp ），然后选择 Connect 。选择 List Tools 来显示你的 MCP 服务器暴露的工具。
5. 现在你可以把 MCP 服务器部署到 Cloudflare 了。在项目目录中运行：终端窗口 npx wrangler@latest deploy 如果你已经把一个 git 仓库连接到承载 MCP 服务器的 Worker，你可以通过向仓库主分支推送变更或合并拉取请求来部署你的 MCP 服务器。MCP 服务器将被部署到你的 *.workers.dev 子域名，地址为 https://remote-mcp-server-authless.your-account.workers.dev/mcp 。
6. 要测试远程 MCP 服务器，把你已部署的 MCP 服务器的 URL（ https://remote-mcp-server-authless.your-account.workers.dev/mcp ）输入到运行在 http://localhost:5173 的 MCP inspector 中。

现在你拥有了一个可供 MCP 客户端连接的远程 MCP 服务器。


## 通过本地代理从 MCP 客户端连接
现在你的远程 MCP 服务器已经运行，你可以使用
mcp-remote
本地代理
↗
把 Claude Desktop 或其他 MCP 客户端连接到它——即使你的 MCP 客户端不支持远程传输或客户端侧授权。这让你可以用一个真实的 MCP 客户端来测试与你的远程 MCP 服务器交互的体验。

例如，从 Claude Desktop 连接：

1. 更新你的 Claude Desktop 配置，指向你的 MCP 服务器的 URL：{ " mcpServers " : { " math " : { " command " : "npx" , " args " : [ "mcp-remote" , "https://remote-mcp-server-authless.your-account.workers.dev/mcp" ] } } }
2. 重启 Claude Desktop 以加载 MCP 服务器。完成后，Claude 将能够调用你的远程 MCP 服务器。
3. 要测试，让 Claude 使用你的某个工具。例如：Could you use the math tool to add 23 and 19? Claude 应该会调用该工具，并显示由远程 MCP 服务器生成的结果。

要了解如何将远程 MCP 服务器与其他 MCP 客户端配合使用，请参阅
Test a Remote MCP Server
。


## 添加身份验证
你之前部署的公开 MCP 服务器示例允许任何客户端无需登录即可连接并调用工具。要为你的 MCP 服务器添加用户身份验证，你可以集成 Cloudflare Access 或第三方服务作为 OAuth 提供方。你的 MCP 服务器负责处理安全的登录流程，并签发访问令牌，MCP 客户端可以使用这些令牌发起经过身份验证的工具调用。用户通过 OAuth 提供方登录，并使用受限权限授权其智能体与你的 MCP 服务器暴露的工具进行交互。


### Cloudflare Access OAuth
你可以将 MCP 服务器配置为通过 Cloudflare Access 要求用户身份验证。Cloudflare Access 充当身份聚合器，验证用户邮箱、来自你现有
身份提供方
（如 GitHub 或 Google）的信号，以及其他属性（如 IP 地址或设备证书）。当用户连接到 MCP 服务器时，系统会提示他们登录所配置的身份提供方，只有通过你的
Access 策略
后才会被授予访问权限。

如需分步部署指南，请参阅
Secure MCP servers with Access for SaaS
。


### 第三方 OAuth
你可以将 MCP 服务器与任何支持 OAuth 2.0 规范的
OAuth 提供方
连接，包括 GitHub、Google、Slack、
Stytch
、
Auth0
、
WorkOS
等。

以下示例演示如何使用 GitHub 作为 OAuth 提供方。


#### 第 1 步 — 创建一个新的 MCP 服务器
运行以下命令，创建一个带 GitHub OAuth 的新 MCP 服务器：


```
npm create cloudflare@latest -- my-mcp-server-github-auth --template=cloudflare/ai/demos/remote-mcp-github-oauth
```

```
yarn create cloudflare my-mcp-server-github-auth --template=cloudflare/ai/demos/remote-mcp-github-oauth
```

```
pnpm create cloudflare@latest my-mcp-server-github-auth --template=cloudflare/ai/demos/remote-mcp-github-oauth
```
现在，MCP 服务器已设置完成，依赖也已安装。进入该项目文件夹：

终端窗口

```
cd my-mcp-server-github-auth
```
你会注意到，在示例 MCP 服务器中，如果打开
src/index.ts
，主要的区别是
defaultHandler
被设置为
GitHubHandler
：

TypeScript

```
import GitHubHandler from "./github-handler";
export default new OAuthProvider({  apiRoute: "/mcp",  apiHandler: MyMCP.serve("/mcp"),  defaultHandler: GitHubHandler,  authorizeEndpoint: "/authorize",  tokenEndpoint: "/token",  clientRegistrationEndpoint: "/register",});
```
这确保你的用户会被重定向到 GitHub 进行身份验证。不过，要让这一切生效，你需要在下面的步骤中创建 OAuth 客户端应用。


#### 第 2 步 — 创建一个 OAuth 应用
你需要创建两个
GitHub OAuth 应用
↗
才能使用 GitHub 作为 MCP 服务器的身份验证提供方——一个用于本地开发，一个用于生产环境。


#### 第 2.1 步 — 为本地开发创建一个新的 OAuth 应用
1. 前往 github.com/settings/developers ↗ ，使用以下设置创建一个新的 OAuth 应用：Application name : My MCP Server (local) Homepage URL : http://localhost:8788 Authorization callback URL : http://localhost:8788/callback
2. 对于刚创建的 OAuth 应用，把该应用的 client ID 添加为 GITHUB_CLIENT_ID，并生成一个 client secret，将其作为 GITHUB_CLIENT_SECRET 添加到项目根目录的 .env 文件中，该文件将用于在本地开发中设置密钥。终端窗口 touch .env echo 'GITHUB_CLIENT_ID="your-client-id"' >> .env echo 'GITHUB_CLIENT_SECRET="your-client-secret"' >> .env cat .env
3. 运行以下命令启动开发服务器：终端窗口 npm start 你的 MCP 服务器现在运行在 http://localhost:8788/mcp 。
4. 在一个新终端中运行 MCP inspector ↗ 。MCP inspector 是一个交互式 MCP 客户端，允许你连接到你的 MCP 服务器并从网页浏览器调用工具。终端窗口 npx @modelcontextprotocol/inspector@latest
5. 在网页浏览器中打开 MCP inspector：终端窗口 open http://localhost:5173
6. 在 inspector 中，输入你的 MCP 服务器的 URL：http://localhost:8788/mcp
7. 在右侧的主面板中，点击 OAuth Settings 按钮，然后点击 Quick OAuth Flow 。你应该会被重定向到 GitHub 登录或授权页面。在授权 MCP 客户端（即 inspector）访问你的 GitHub 账户后，你会被重定向回 inspector。
8. 在侧边栏点击 Connect，你应该会看到 "List Tools" 按钮，它会列出你的 MCP 服务器暴露的工具。


#### 第 2.2 步 — 为生产环境创建一个新的 OAuth 应用
你需要重复
第 2.1 步
，为生产环境创建一个新的 OAuth 应用。

1. 前往 github.com/settings/developers ↗ ，使用以下设置创建一个新的 OAuth 应用：

- Application name : My MCP Server (production)
- Homepage URL : 输入你已部署的 MCP 服务器的 workers.dev URL（例如：worker-name.account-name.workers.dev ）
- Authorization callback URL : 输入你已部署的 MCP 服务器的 workers.dev URL 的 /callback 路径（例如：worker-name.account-name.workers.dev/callback ）

1. 对于刚创建的 OAuth 应用，使用 Wrangler CLI 添加 client ID 和 client secret：

终端窗口

```
npx wrangler secret put GITHUB_CLIENT_ID
```
终端窗口

```
npx wrangler secret put GITHUB_CLIENT_SECRET
```

```
npx wrangler secret put COOKIE_ENCRYPTION_KEY # add any random string here e.g. openssl rand -hex 32
```
1. 设置一个 KV 命名空间 a. 创建 KV 命名空间：终端窗口 npx wrangler kv namespace create "OAUTH_KV" b. 使用生成的 KV ID 更新 wrangler.jsonc 文件：{ " kvNamespaces " : [ { " binding " : "OAUTH_KV" , " id " : "<YOUR_KV_NAMESPACE_ID>" } ] }
2. 将 MCP 服务器部署到你的 Cloudflare workers.dev 域名：终端窗口 npm run deploy
3. 使用 AI Playground ↗ 、MCP Inspector 或其他 MCP 客户端 连接到运行在 worker-name.account-name.workers.dev/mcp 的服务器，并通过 GitHub 完成身份验证。


## 后续步骤
MCP 工具
为你的 MCP 服务器添加工具。
授权
自定义身份验证与授权。
