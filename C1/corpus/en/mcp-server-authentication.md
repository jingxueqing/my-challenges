---
source_file: mcp-server-authentication.html
title: Build a Remote MCP server Â· Cloudflare Agents docs
---

astro:end

# Build a Remote MCP server
This guide will show you how to deploy your own remote MCP server on Cloudflare using
Streamable HTTP transport
, the current MCP specification standard. You have two options:

- Without authentication â anyone can connect and use the server (no login required).
- With authentication and authorization â users sign in before accessing tools, and you can control which tools an agent can call based on the user's permissions.


## Choosing an approach
The Agents SDK provides multiple ways to create MCP servers. Choose the approach that fits your use case:

| Approach | Stateful? | Requires Durable Objects? | Best for |
| createMcpHandler() | No | No | Stateless tools, simplest setup |
| McpAgent | Yes | Yes | Stateful tools, per-session state, elicitation |
| Raw WebStandardStreamableHTTPServerTransport | No | No | Full control, no SDK dependency |

- createMcpHandler() is the fastest way to get a stateless MCP server running. Use it when your tools do not need per-session state.
- McpAgent gives you a Durable Object per session with built-in state management, elicitation support, and both SSE and Streamable HTTP transports.
- Raw transport gives you full control if you want to use the @modelcontextprotocol/sdk directly without the Agents SDK helpers.


## Deploy your first MCP server
You can start by deploying a
public MCP server
â
without authentication, then add user authentication and scoped authorization later. If you already know your server will require authentication, you can skip ahead to the
next section
.


### Via the dashboard
The button below will guide you through everything you need to do to deploy an
example MCP server
â
to your Cloudflare account:

Once deployed, this server will be live at your
workers.dev
subdomain (for example,
remote-mcp-server-authless.your-account.workers.dev/mcp
). You can connect to it immediately using the
AI Playground
â
(a remote MCP client),
MCP inspector
â
or
other MCP clients
.

A new git repository will be set up on your GitHub or GitLab account for your MCP server, configured to automatically deploy to Cloudflare each time you push a change or merge a pull request to the main branch of the repository. You can clone this repository,
develop locally
, and start customizing the MCP server with your own
tools
.


### Via the CLI
You can use the
Wrangler CLI
to create a new MCP Server on your local machine and deploy it to Cloudflare.

1. Open a terminal and run the following command: npm create cloudflare@latest -- remote-mcp-server-authless --template=cloudflare/ai/demos/remote-mcp-authless yarn create cloudflare remote-mcp-server-authless --template=cloudflare/ai/demos/remote-mcp-authless pnpm create cloudflare@latest remote-mcp-server-authless --template=cloudflare/ai/demos/remote-mcp-authless During setup, select the following options: - For Do you want to add an AGENTS.md file to help AI coding tools understand Cloudflare APIs? , choose No . - For Do you want to use git for version control? , choose No . - For Do you want to deploy your application? , choose No (we will be testing the server before deploying). Now, you have the MCP server setup, with dependencies installed.
2. Move into the project folder: Terminal window cd remote-mcp-server-authless
3. In the directory of your new project, run the following command to start the development server: Terminal window npm start â Starting local server... [ wrangler:info ] Ready on http://localhost:8788 Check the command output for the local port. In this example, the MCP server runs on port 8788 , and the MCP endpoint URL is http://localhost:8788/mcp .
4. To test the server locally: In a new terminal, run the MCP inspector â . The MCP inspector is an interactive MCP client that allows you to connect to your MCP server and invoke tools from a web browser. Terminal window npx @modelcontextprotocol/inspector@latest ð MCP Inspector is up and running at: http://localhost:5173/?MCP_PROXY_AUTH_TOKEN =46ab..cd3 ð Opening browser... The MCP Inspector will launch in your web browser. You can also launch it manually by opening a browser and going to http://localhost:<PORT> . Check the command output for the local port where MCP Inspector is running. In this example, MCP Inspector is served on port 5173 . In the MCP inspector, enter the URL of your MCP server ( http://localhost:8788/mcp ), and select Connect . Select List Tools to show the tools that your MCP server exposes.
5. You can now deploy your MCP server to Cloudflare. From your project directory, run: Terminal window npx wrangler@latest deploy If you have already connected a git repository to the Worker with your MCP server, you can deploy your MCP server by pushing a change or merging a pull request to the main branch of the repository. The MCP server will be deployed to your *.workers.dev subdomain at https://remote-mcp-server-authless.your-account.workers.dev/mcp .
6. To test the remote MCP server, take the URL of your deployed MCP server ( https://remote-mcp-server-authless.your-account.workers.dev/mcp ) and enter it in the MCP inspector running on http://localhost:5173 .

You now have a remote MCP server that MCP clients can connect to.


## Connect from an MCP client via a local proxy
Now that your remote MCP server is running, you can use the
mcp-remote
local proxy
â
to connect Claude Desktop or other MCP clients to it â even if your MCP client does not support remote transport or authorization on the client side. This lets you test what an interaction with your remote MCP server will be like with a real MCP client.

For example, to connect from Claude Desktop:

1. Update your Claude Desktop configuration to point to the URL of your MCP server: { " mcpServers " : { " math " : { " command " : "npx" , " args " : [ "mcp-remote" , "https://remote-mcp-server-authless.your-account.workers.dev/mcp" ] } } }
2. Restart Claude Desktop to load the MCP Server. Once this is done, Claude will be able to make calls to your remote MCP server.
3. To test, ask Claude to use one of your tools. For example: Could you use the math tool to add 23 and 19? Claude should invoke the tool and show the result generated by the remote MCP server.

To learn how to use remote MCP servers with other MCP clients, refer to
Test a Remote MCP Server
.


## Add Authentication
The public MCP server example you deployed earlier allows any client to connect and invoke tools without logging in. To add user authentication to your MCP server, you can integrate Cloudflare Access or a third-party service as the OAuth provider. Your MCP server handles secure login flows and issues access tokens that MCP clients can use to make authenticated tool calls. Users sign in with the OAuth provider and grant their AI agent permission to interact with the tools exposed by your MCP server, using scoped permissions.


### Cloudflare Access OAuth
You can configure your MCP server to require user authentication through Cloudflare Access. Cloudflare Access acts as an identity aggregator and verifies user emails, signals from your existing
identity providers
(such as GitHub or Google), and other attributes such as IP address or device certificates. When users connect to the MCP server, they will be prompted to log in to the configured identity provider and are only granted access if they pass your
Access policies
.

For a step-by-step deployment guide, refer to
Secure MCP servers with Access for SaaS
.


### Third-party OAuth
You can connect your MCP server with any
OAuth provider
that supports the OAuth 2.0 specification, including GitHub, Google, Slack,
Stytch
,
Auth0
,
WorkOS
, and more.

The following example demonstrates how to use GitHub as an OAuth provider.


#### Step 1 â Create a new MCP server
Run the following command to create a new MCP server with GitHub OAuth:


```
npm create cloudflare@latest -- my-mcp-server-github-auth --template=cloudflare/ai/demos/remote-mcp-github-oauth
```

```
yarn create cloudflare my-mcp-server-github-auth --template=cloudflare/ai/demos/remote-mcp-github-oauth
```

```
pnpm create cloudflare@latest my-mcp-server-github-auth --template=cloudflare/ai/demos/remote-mcp-github-oauth
```
Now, you have the MCP server setup, with dependencies installed. Move into that project folder:

Terminal window

```
cd my-mcp-server-github-auth
```
You'll notice that in the example MCP server, if you open
src/index.ts
, the primary difference is that the
defaultHandler
is set to the
GitHubHandler
:

TypeScript

```
import GitHubHandler from "./github-handler";
export default new OAuthProvider({  apiRoute: "/mcp",  apiHandler: MyMCP.serve("/mcp"),  defaultHandler: GitHubHandler,  authorizeEndpoint: "/authorize",  tokenEndpoint: "/token",  clientRegistrationEndpoint: "/register",});
```
This ensures that your users are redirected to GitHub to authenticate. To get this working though, you need to create OAuth client apps in the steps below.


#### Step 2 â Create an OAuth App
You'll need to create two
GitHub OAuth Apps
â
to use GitHub as an authentication provider for your MCP server âÂ one for local development, and one for production.


#### Step 2.1 â Create a new OAuth App for local development
1. Navigate to github.com/settings/developers â to create a new OAuth App with the following settings: Application name : My MCP Server (local) Homepage URL : http://localhost:8788 Authorization callback URL : http://localhost:8788/callback
2. For the OAuth app you just created, add the client ID of the OAuth app as GITHUB_CLIENT_ID and generate a client secret, adding it as GITHUB_CLIENT_SECRET to a .env file in the root of your project, which will be used to set secrets in local development . Terminal window touch .env echo 'GITHUB_CLIENT_ID="your-client-id"' >> .env echo 'GITHUB_CLIENT_SECRET="your-client-secret"' >> .env cat .env
3. Run the following command to start the development server: Terminal window npm start Your MCP server is now running on http://localhost:8788/mcp .
4. In a new terminal, run the MCP inspector â . The MCP inspector is an interactive MCP client that allows you to connect to your MCP server and invoke tools from a web browser. Terminal window npx @modelcontextprotocol/inspector@latest
5. Open the MCP inspector in your web browser: Terminal window open http://localhost:5173
6. In the inspector, enter the URL of your MCP server, http://localhost:8788/mcp
7. In the main panel on the right, click the OAuth Settings button and then click Quick OAuth Flow . You should be redirected to a GitHub login or authorization page. After authorizing the MCP Client (the inspector) access to your GitHub account, you will be redirected back to the inspector.
8. Click Connect in the sidebar and you should see the "List Tools" button, which will list the tools that your MCP server exposes.


#### Step 2.2 â Create a new OAuth App for production
You'll need to repeat
Step 2.1
to create a new OAuth App for production.

1. Navigate to github.com/settings/developers â to create a new OAuth App with the following settings:

- Application name : My MCP Server (production)
- Homepage URL : Enter the workers.dev URL of your deployed MCP server (ex: worker-name.account-name.workers.dev )
- Authorization callback URL : Enter the /callback path of the workers.dev URL of your deployed MCP server (ex: worker-name.account-name.workers.dev/callback )

1. For the OAuth app you just created, add the client ID and client secret, using Wrangler CLI:

Terminal window

```
npx wrangler secret put GITHUB_CLIENT_ID
```
Terminal window

```
npx wrangler secret put GITHUB_CLIENT_SECRET
```

```
npx wrangler secret put COOKIE_ENCRYPTION_KEY # add any random string here e.g. openssl rand -hex 32
```
1. Set up a KV namespace a. Create the KV namespace: Terminal window npx wrangler kv namespace create "OAUTH_KV" b. Update the wrangler.jsonc file with the resulting KV ID: { " kvNamespaces " : [ { " binding " : "OAUTH_KV" , " id " : "<YOUR_KV_NAMESPACE_ID>" } ] }
2. Deploy the MCP server to your Cloudflare workers.dev domain: Terminal window npm run deploy
3. Connect to your server running at worker-name.account-name.workers.dev/mcp using the AI Playground â , MCP Inspector, or other MCP clients , and authenticate with GitHub.


## Next steps
MCP Tools
Add tools to your MCP server.
Authorization
Customize authentication and authorization.
