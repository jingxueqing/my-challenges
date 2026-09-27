# 待译批次 16

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## mcp-introduction#015

## Conclusion
 Model Context Protocol (MCP) is an exciting development in AI development because it allows developers to safely and efficiently connect our increasingly intelligent language models to the extensive world of software and data previously difficult to connect with. By introducing a common protocol, MCP lets us build AI systems that are more integrated, autonomous, and easier to scale . Instead of writing one-off plugins or giving the model brittle instructions for each new tool, we have a coherent framework where AI agents can discover and use tools on the fly, with proper oversight and security.
 While the protocol is still evolving (authentication was a recent addition, and more features like standardized server discovery are on the horizon, it’s clear that MCP or something like it will play a key role in the next generation of AI applications. For developers, now is a great time to familiarize yourself with MCP concepts. Whether you’re enhancing a chatbot with company-specific knowledge or building an AI agent that automates workflows, MCP can save you time and headaches by handling the “plumbing” of tool integration. And since it’s an open standard backed by a growing community (and companies like Anthropic), it’s likely to become a foundational piece of AI infrastructure moving forward.
 In summary, Model Context Protocol enables a world where AI assistants are not siloed geniuses but well-equipped engineers and assistants – able to interface with many systems, follow procedures, and fetch or create information as needed, all through a unified, secure interface. That’s a powerful vision, and one that is quickly becoming reality with MCP.
 At Stytch, we’re focused on easily solving the remote MCP server auth problem for customers, so they can easily stand up MCP servers for their applications to allow end users to provide permissioned access to MCP clients.

## mcp-introduction#016

### MCP auth with Stytch
 Use Stytch Connected Apps to build authentication with MCP servers

Read the docs

Share this article
 
 LinkedIn
 
 X
 
 Facebook

# Related Articles

Product

Feb 20, 2025

### Stytch Connected Apps: Make any app an OAuth provider for integrations and AI agents

Auth & identity

Feb 8, 2025

### The age of agent experience

Auth & identity

Feb 15, 2025

### Detecting AI agent use & abuse

Get started
with Stytch

Start building for free Explore our docs

#### Authentication & Authorization
 For consumer applications
 
 For B2B SaaS applications
 
 Admin Portal
 
 Connected Apps
 
 Single sign-on

#### Fraud & Risk Prevention
 Fingerprinting
 
 Active risk assessment
 
 Fine-grained enforcement

#### Why Stytch
 Stytch vs. Auth0
 
 Stytch vs. Firebase
 
 Stytch vs. Cognito
 
 Stytch vs. Fingerprint

#### Company
 About us
 
 Careers
 
 Contact

#### Resources
 Pricing
 
 Docs
 
 Changelog
 
 Product roadmap
 
 API status
 
 Blog

#### Community
 Slack community
 
 Technical support
 
 Customer stories

© 2020-2026 Stytch. All rights reserved.
 Terms of use
 Privacy Policy

## mcp-registry-preview#001

Today, we’re launching the Model Context Protocol (MCP) Registry—an open catalog and API for publicly available MCP servers to improve discoverability and implementation. By standardizing how servers are distributed and discovered, we’re expanding their reach while making it easier for clients to get connected.
 The MCP Registry is now available in preview. To get started:
 Add your server by following our guide on Adding Servers to the MCP Registry (for server maintainers)
 Access server data by following our guide on Accessing MCP Registry Data (for client maintainers)

## mcp-registry-preview#002

# Single source of truth for MCP servers # 
 In March 2025, we shared that we wanted to build a central registry for the MCP ecosystem. Today we are announcing that we’ve launched https://registry.modelcontextprotocol.io as the official MCP Registry. As part of the MCP project, the MCP Registry, as well as a parent OpenAPI specification , are open source—allowing everyone to build a compatible sub-registry.
 Our goal is to standardize how servers are distributed and discovered, providing a primary source of truth that sub-registries can build upon. In turn, this will expand server reach and help clients find servers more easily across the MCP ecosystem.

## mcp-registry-preview#003

## Public and private sub-registries # 
 In building a central registry, it was important to us not to take away from existing registries that the community and companies have built. The MCP Registry serves as a primary source of truth for publicly available MCP servers, and organizations can choose to create sub-registries based on custom criteria. For example:
 Public subregistries like opinionated “MCP marketplaces” associated with each MCP client are free to augment and enhance data they ingest from the upstream MCP Registry. Every MCP end-user persona will have different needs, and it is up to the MCP client marketplaces to properly serve their end-users in opinionated ways.
 Private subregistries will exist within enterprises that have strict privacy and security requirements, but the MCP Registry gives these enterprises a single upstream data source they can build upon. At a minimum, we aim to share API schemas with these private implementations so that associated SDKs and tooling can be shared across the ecosystem.
 In both cases, the MCP Registry is the starting point – it’s the centralized location where MCP server maintainers publish and maintain their self-reported information for these downstream consumers to massage and deliver to their end-users.

## mcp-registry-preview#004

## Community-driven mechanism for moderation # 
 The MCP Registry is an official MCP project maintained by the registry working group and permissively licensed. Community members can submit issues to flag servers that violate the MCP moderation guidelines —such as those containing spam, malicious code, or impersonating legitimate services. Registry maintainers can then denylist these entries and retroactively remove them from public access.

# Getting started # 
 To get started:
 Add your server by following our guide on Adding Servers to the MCP Registry (for server maintainers)
 Access server data by following our guide on Accessing MCP Registry Data (for client maintainers)
 This preview of the MCP Registry is meant to help us improve the user experience before general availability and does not provide data durability guarantees or other warranties. We advise MCP adopters to watch development closely as breaking changes may occur before the registry is made generally available.
 As we continue to develop the registry, we encourage feedback and contributions on the modelcontextprotocol/registry GitHub repository : Discussion, Issues, and Pull Requests are all welcome.

## mcp-registry-preview#005

# Thanks to the MCP community # 
 The MCP Registry has been a collaborative effort from the beginning and we are incredibly grateful for the enthusiasm and support from the broader developer community.
 In February 2025, it began as a grassroots project when MCP creators David Soria Parra and Justin Spahr-Summers asked the PulseMCP and Goose teams to help build a centralized community registry. Registry Maintainer Tadas Antanavicius from PulseMCP spearheaded the initial effort in collaboration with Alex Hancock from Block . They were soon joined by Registry Maintainer Toby Padilla , Head of MCP at GitHub , and more recently, Adam Jones from Anthropic joined as Registry Maintainer to drive the project towards the launch today. The initial announcement of the MCP Registry’s development lists 16 contributing individuals from at least 9 different companies.
 Many others made crucial contributions to bring this project to life: Radoslav Dimitrov from Stacklok , Avinash Sridhar from GitHub , Connor Peet from VS Code , Joel Verhagen from NuGet , Preeti Dewani from Last9 , Avish Porwal from Microsoft , Jonathan Hefner , and many Anthropic and GitHub employees that provided code reviews and development support. We are also grateful to everyone on the Registry’s contributors log and those who participated in discussions and issues .
 We deeply appreciate everyone investing in this foundational open source infrastructure. Together, we’re helping developers and organizations worldwide to build more reliable, context-aware AI applications. On behalf of the MCP community, thank you.

## mcp-server-authentication#001

Copy page

# Build a Remote MCP server

This guide will show you how to deploy your own remote MCP server on Cloudflare using Streamable HTTP transport , the current MCP specification standard. You have two options:

Without authentication â anyone can connect and use the server (no login required).

With authentication and authorization â users sign in before accessing tools, and you can control which tools an agent can call based on the user's permissions.

## Choosing an approach

The Agents SDK provides multiple ways to create MCP servers. Choose the approach that fits your use case:

Approach Stateful? Requires Durable Objects? Best for 
 createMcpHandler() No No Stateless tools, simplest setup 
 McpAgent Yes Yes Stateful tools, per-session state, elicitation 
 Raw WebStandardStreamableHTTPServerTransport No No Full control, no SDK dependency

createMcpHandler() is the fastest way to get a stateless MCP server running. Use it when your tools do not need per-session state.

McpAgent gives you a Durable Object per session with built-in state management, elicitation support, and both SSE and Streamable HTTP transports.

## mcp-server-authentication#002

Raw transport gives you full control if you want to use the @modelcontextprotocol/sdk directly without the Agents SDK helpers.

## Deploy your first MCP server

You can start by deploying a public MCP server â without authentication, then add user authentication and scoped authorization later. If you already know your server will require authentication, you can skip ahead to the next section .

### Via the dashboard

The button below will guide you through everything you need to do to deploy an example MCP server â to your Cloudflare account:

Once deployed, this server will be live at your workers.dev subdomain (for example, remote-mcp-server-authless.your-account.workers.dev/mcp ). You can connect to it immediately using the AI Playground â (a remote MCP client), MCP inspector â or other MCP clients .

A new git repository will be set up on your GitHub or GitLab account for your MCP server, configured to automatically deploy to Cloudflare each time you push a change or merge a pull request to the main branch of the repository. You can clone this repository, develop locally , and start customizing the MCP server with your own tools .

### Via the CLI

## mcp-server-authentication#003

You can use the Wrangler CLI to create a new MCP Server on your local machine and deploy it to Cloudflare.

Open a terminal and run the following command:

npm yarn pnpm 
 npm create cloudflare@latest -- remote-mcp-server-authless --template=cloudflare/ai/demos/remote-mcp-authless 
 
 yarn create cloudflare remote-mcp-server-authless --template=cloudflare/ai/demos/remote-mcp-authless 
 
 pnpm create cloudflare@latest remote-mcp-server-authless --template=cloudflare/ai/demos/remote-mcp-authless

During setup, select the following options: - For Do you want to add an AGENTS.md file to help AI coding tools understand
Cloudflare APIs? , choose No . - For Do you want to use git for version control? , choose No . - For Do you want to deploy your application? , choose No (we will be testing the server before deploying).

Now, you have the MCP server setup, with dependencies installed.

Move into the project folder:

Terminal window cd remote-mcp-server-authless

In the directory of your new project, run the following command to start the development server:

Terminal window npm start

â Starting local server...

[ wrangler:info ] Ready on http://localhost:8788

## mcp-server-authentication#004

Check the command output for the local port. In this example, the MCP server runs on port 8788 , and the MCP endpoint URL is http://localhost:8788/mcp .

Note
 You cannot interact with the MCP server by opening the /mcp URL directly in a web browser. The /mcp endpoint expects an MCP client to send MCP protocol messages, which a browser does not do by default. In the next step, we will demonstrate how to connect to the server using an MCP client.

To test the server locally:

In a new terminal, run the MCP inspector â . The MCP inspector is an interactive MCP client that allows you to connect to your MCP server and invoke tools from a web browser.

Terminal window npx @modelcontextprotocol/inspector@latest

ð MCP Inspector is up and running at:

http://localhost:5173/?MCP_PROXY_AUTH_TOKEN =46ab..cd3

ð Opening browser...

The MCP Inspector will launch in your web browser. You can also launch it manually by opening a browser and going to http://localhost:<PORT> . Check the command output for the local port where MCP Inspector is running. In this example, MCP Inspector is served on port 5173 .

## mcp-server-authentication#005

In the MCP inspector, enter the URL of your MCP server ( http://localhost:8788/mcp ), and select Connect . Select List Tools to show the tools that your MCP server exposes.

You can now deploy your MCP server to Cloudflare. From your project directory, run:

Terminal window npx wrangler@latest deploy

If you have already connected a git repository to the Worker with your MCP server, you can deploy your MCP server by pushing a change or merging a pull request to the main branch of the repository.

The MCP server will be deployed to your *.workers.dev subdomain at https://remote-mcp-server-authless.your-account.workers.dev/mcp .

To test the remote MCP server, take the URL of your deployed MCP server ( https://remote-mcp-server-authless.your-account.workers.dev/mcp ) and enter it in the MCP inspector running on http://localhost:5173 .

You now have a remote MCP server that MCP clients can connect to.

## Connect from an MCP client via a local proxy

## mcp-server-authentication#006

Now that your remote MCP server is running, you can use the mcp-remote local proxy â to connect Claude Desktop or other MCP clients to it â even if your MCP client does not support remote transport or authorization on the client side. This lets you test what an interaction with your remote MCP server will be like with a real MCP client.

For example, to connect from Claude Desktop:

Update your Claude Desktop configuration to point to the URL of your MCP server:

{

" mcpServers " : {

" math " : {

" command " : "npx" ,

" args " : [

"mcp-remote" ,

"https://remote-mcp-server-authless.your-account.workers.dev/mcp"

]

}

}

}

Restart Claude Desktop to load the MCP Server. Once this is done, Claude will be able to make calls to your remote MCP server.

To test, ask Claude to use one of your tools. For example:

Could you use the math tool to add 23 and 19?

Claude should invoke the tool and show the result generated by the remote MCP server.

To learn how to use remote MCP servers with other MCP clients, refer to Test a Remote MCP Server .

## Add Authentication

## mcp-server-authentication#007

The public MCP server example you deployed earlier allows any client to connect and invoke tools without logging in. To add user authentication to your MCP server, you can integrate Cloudflare Access or a third-party service as the OAuth provider. Your MCP server handles secure login flows and issues access tokens that MCP clients can use to make authenticated tool calls. Users sign in with the OAuth provider and grant their AI agent permission to interact with the tools exposed by your MCP server, using scoped permissions.

### Cloudflare Access OAuth

You can configure your MCP server to require user authentication through Cloudflare Access. Cloudflare Access acts as an identity aggregator and verifies user emails, signals from your existing identity providers (such as GitHub or Google), and other attributes such as IP address or device certificates. When users connect to the MCP server, they will be prompted to log in to the configured identity provider and are only granted access if they pass your Access policies .

For a step-by-step deployment guide, refer to Secure MCP servers with Access for SaaS .

### Third-party OAuth

## mcp-server-authentication#008

You can connect your MCP server with any OAuth provider that supports the OAuth 2.0 specification, including GitHub, Google, Slack, Stytch , Auth0 , WorkOS , and more.

The following example demonstrates how to use GitHub as an OAuth provider.

#### Step 1 â Create a new MCP server

Run the following command to create a new MCP server with GitHub OAuth:

npm yarn pnpm 
 npm create cloudflare@latest -- my-mcp-server-github-auth --template=cloudflare/ai/demos/remote-mcp-github-oauth 
 
 yarn create cloudflare my-mcp-server-github-auth --template=cloudflare/ai/demos/remote-mcp-github-oauth 
 
 pnpm create cloudflare@latest my-mcp-server-github-auth --template=cloudflare/ai/demos/remote-mcp-github-oauth

Now, you have the MCP server setup, with dependencies installed. Move into that project folder:

Terminal window cd my-mcp-server-github-auth

You'll notice that in the example MCP server, if you open src/index.ts , the primary difference is that the defaultHandler is set to the GitHubHandler :

TypeScript import GitHubHandler from "./github-handler" ;

export default new OAuthProvider ( {

apiRoute : "/mcp" ,

apiHandler : MyMCP . serve ( "/mcp" ) ,

defaultHandler : GitHubHandler ,

## mcp-server-authentication#009

authorizeEndpoint : "/authorize" ,

tokenEndpoint : "/token" ,

clientRegistrationEndpoint : "/register" ,

} ) ;

This ensures that your users are redirected to GitHub to authenticate. To get this working though, you need to create OAuth client apps in the steps below.

#### Step 2 â Create an OAuth App

You'll need to create two GitHub OAuth Apps â to use GitHub as an authentication provider for your MCP server âÂ one for local development, and one for production.

#### Step 2.1 â Create a new OAuth App for local development

Navigate to github.com/settings/developers â to create a new OAuth App with the following settings:

Application name : My MCP Server (local)

Homepage URL : http://localhost:8788

Authorization callback URL : http://localhost:8788/callback

For the OAuth app you just created, add the client ID of the OAuth app as GITHUB_CLIENT_ID and generate a client secret, adding it as GITHUB_CLIENT_SECRET to a .env file in the root of your project, which will be used to set secrets in local development .

Terminal window touch .env

echo 'GITHUB_CLIENT_ID="your-client-id"' >> .env

echo 'GITHUB_CLIENT_SECRET="your-client-secret"' >> .env

cat .env
