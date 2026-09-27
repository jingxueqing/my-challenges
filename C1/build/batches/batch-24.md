# 待译批次 24

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## sre-introduction#026

An accurate organic demand forecast, which extends beyond the lead time required for acquiring capacity

An accurate incorporation of inorganic demand sources into the demand forecast

Regular load testing of the system to correlate raw capacity(servers, disks, and so on) to service capacity

Because capacity is critical to availability, it naturally follows that the SRE team must be in charge of capacity planning, which means they also must be in charge of provisioning.

## Provisioning

Provisioning combines both change management and capacity planning. In our experience, provisioning must be conducted quickly and only when necessary, as capacity is expensive. This exercise must also be done correctly or capacity doesnât work when needed. Adding new capacity often involves spinning up a new instance or location, making significant modification to existing systems (configuration files, load balancers, networking), and validating that the new capacity performs and delivers correct results. Thus, it is a riskier operation than load shifting, which is often done multiple times per hour, and must be treated with a corresponding degree of extra caution.

## Efficiency and Performance

## sre-introduction#027

Efficient use of resources is important any time a service cares about money. Because SRE ultimately controls provisioning, it must also be involved in any work on utilization, as utilization is a function of how a given service works and how it is provisioned. It follows that paying close attention to the provisioning strategy for a service, and therefore its utilization, provides a very, very big lever on the serviceâs total costs.

Resource use is a function of demand (load), capacity, and software efficiency. SREs predict demand, provision capacity, and can modify the software. These three factors are a large part (though not the entirety) of a serviceâs efficiency.

Software systems become slower as load is added to them. A slowdown in a service equates to a loss of capacity. At some point, a slowing system stops serving, which corresponds to infinite slowness. SREs provision to meet a capacity target at a specific response speed , and thus are keenly interested in a serviceâs performance. SREs and product developers will (and should) monitor and modify a service to improve its performance, thus adding capacity and improving efficiency. 8

# The End of the Beginning

## sre-introduction#028

Site Reliability Engineering represents a significant break from existing industry best practices for managing large, complicated services. Motivated originally by familiarityâ"as a software engineer, this is how I would want to invest my time to accomplish a set of repetitive tasks"âit has become much more: a set of principles, a set of practices, a set of incentives, and a field of endeavor within the larger software engineering discipline. The rest of the book explores the SRE Way in detail.

6 Vice President, Google Engineering, founder of Google SRE
 7 See Disaster Role Playing .
 8 For further discussion of how this collaboration can work in practice, see Communications: Production Meetings .

Previous

Part I - Introduction

Next

Chapter 2 - The Production Environment at Google, from the Viewpoint of an SRE

Copyright Â© 2017 Google, Inc. Published by O'Reilly Media, Inc. Licensed under CC BY-NC-ND 4.0

## warp-vs-claude-code#001

Warp is an Agentic Development Environment , a modern terminal combined with powerful agents that help you build, test, deploy, and debug code. Warp's AI is powered by Oz , the orchestration platform for cloud agents. 
 
 Warp combines a modern terminal with Oz, the orchestration platform for cloud agents

## Warp 
 Warp is where you work — a fast, modern terminal built for coding with agents.
 Key capabilities:

Agent Modality : Switch between a clean terminal for commands and a dedicated conversation view for multi-turn agent workflows.

Modern terminal UX : Cursor movement, block-based navigation, multi-line editing, syntax highlighting, and rich completions. Built with Rust for high performance.

Code editor : File tree, code editor with LSP support, and interactive code review experience.

Coding agent integrations : Features like voice input, and @-selection for working with terminal based images. Compatible with Oz or agents like Claude Code and Codex.

Deep dive into Warp's core features

## warp-vs-claude-code#002

## Oz: The orchestration platform for cloud agents 
 Oz is the orchestration platform for cloud agents that powers all of Warp's intelligent features. Oz is designed to coordinate agents at scale—understanding your codebase, executing tasks autonomously, and adapting to your workflows. Oz is multi-model by design, giving you flexibility to choose the best LLM for each task.
 Oz operates in two modes:

### Local agents 
 Run directly in the Warp app for real-time, interactive coding assistance.

Write and refactor code across your codebase

Debug issues and fix errors

Run commands and interpret results

Plan and execute multi-step tasks

Local agents keep you in control. You can review changes, steer the agent mid-task, and approve actions before they execute.
 → Get started with local agents

### Cloud agents 
 Oz Cloud Agents run in the background on Warp's infrastructure (or your own) for automation at scale.

Triggers : React to events from Slack, Linear, GitHub, or custom webhooks

Schedules : Run recurring tasks like dependency updates or dead code removal

Parallelism : Run many agents concurrently across repos or tasks

## warp-vs-claude-code#003

Observability : Every run is tracked, auditable, and shareable with your team

Cloud agents are ideal for work that doesn't need your immediate attention, like PR reviews, issue triage, routine maintenance, and integration-driven workflows.
 → Learn about cloud agents

## How they work together 
 Warp and Oz provide a unified experience across local and cloud development:

Same agent, anywhere : Whether you're working interactively in Warp or running agents in the cloud, you're using the same underlying agent capabilities.

Seamless handoff : Start a task in the cloud and take over locally in Warp when you want hands-on control, without losing progress or context.

Shared context : Warp Drive , Rules , and MCP servers work across both local and cloud agents, so your team's knowledge and tools are always available.

Team collaboration : Share agent sessions, review agents' actions, and steer running tasks, regardless of who started them.

## Multi-model support 
 Oz is multi-model by design. You can choose your preferred LLM from a curated set of top models.

## warp-vs-claude-code#004

## Privacy and security 
 Warp is SOC 2 compliant and has Zero Data Retention policies with all contracted LLM providers. No customer AI data is retained, stored, or used for training.
 Warp's AI features can be globally disabled in Settings > AI .
 → Read more about data privacy

## Next steps

Quickstart Guide : Get Warp installed and start coding

Local Agents Overview : Explore all AI features available in Warp

Cloud Agents Overview : Set up background automation

Oz Platform : Learn about the CLI, API, SDK, and infrastructure

Next Quickstart 
 Last updated 3 days ago 
 Was this helpful?

## writing-effective-tools-for-agents#001

Engineering at Anthropic

# Writing effective tools for agents — with agents

Published Sep 11, 2025
 Agents are only as effective as the tools we give them. We share how to write high-quality tools and evaluations, and how you can boost performance by using Claude to optimize its tools for itself.

## writing-effective-tools-for-agents#002

The Model Context Protocol (MCP) can empower LLM agents with potentially hundreds of tools to solve real-world tasks. But how do we make those tools maximally effective?
 In this post, we describe our most effective techniques for improving performance in a variety of agentic AI systems 1 .
 We begin by covering how you can:
 Build and test prototypes of your tools
 Create and run comprehensive evaluations of your tools with agents
 Collaborate with agents like Claude Code to automatically increase the performance of your tools
 We conclude with key principles for writing high-quality tools we’ve identified along the way:
 Choosing the right tools to implement (and not to implement)
 Namespacing tools to define clear boundaries in functionality
 Returning meaningful context from tools back to agents
 Optimizing tool responses for token efficiency
 Prompt-engineering tool descriptions and specs
 Building an evaluation allows you to systematically measure the performance of your tools. You can use Claude Code to automatically optimize your tools against this evaluation.

## writing-effective-tools-for-agents#003

## What is a tool?
 In computing, deterministic systems produce the same output every time given identical inputs, while non-deterministic systems—like agents—can generate varied responses even with the same starting conditions.
 When we traditionally write software, we’re establishing a contract between deterministic systems. For instance, a function call like getWeather(“NYC”) will always fetch the weather in New York City in the exact same manner every time it is called.
 Tools are a new kind of software which reflects a contract between deterministic systems and non-deterministic agents. When a user asks "Should I bring an umbrella today?,” an agent might call the weather tool, answer from general knowledge, or even ask a clarifying question about location first. Occasionally, an agent might hallucinate or even fail to grasp how to use a tool.
 This means fundamentally rethinking our approach when writing software for agents: instead of writing tools and MCP servers the way we’d write functions and APIs for other developers or systems, we need to design them for agents.
 Our goal is to increase the surface area over which agents can be effective in solving a wide range of tasks by using tools to pursue a variety of successful strategies. Fortunately, in our experience, the tools that are most “ergonomic” for agents also end up being surprisingly intuitive to grasp as humans.

## writing-effective-tools-for-agents#004

## How to write tools
 In this section, we describe how you can collaborate with agents both to write and to improve the tools you give them. Start by standing up a quick prototype of your tools and testing them locally. Next, run a comprehensive evaluation to measure subsequent changes. Working alongside agents, you can repeat the process of evaluating and improving your tools until your agents achieve strong performance on real-world tasks.

## writing-effective-tools-for-agents#005

### Building a prototype
 It can be difficult to anticipate which tools agents will find ergonomic and which tools they won’t without getting hands-on yourself. Start by standing up a quick prototype of your tools. If you’re using Claude Code to write your tools (potentially in one-shot), it helps to give Claude documentation for any software libraries, APIs, or SDKs (including potentially the MCP SDK ) your tools will rely on. LLM-friendly documentation can commonly be found in flat llms.txt files on official documentation sites (here’s our API’s ).
 Wrapping your tools in a local MCP server or Desktop extension (DXT) will allow you to connect and test your tools in Claude Code or the Claude Desktop app.
 To connect your local MCP server to Claude Code, run claude mcp add <name> <command> [args...] .
 To connect your local MCP server or DXT to the Claude Desktop app, navigate to Settings > Developer or Settings > Extensions , respectively.
 Tools can also be passed directly into Anthropic API calls for programmatic testing.
 Test the tools yourself to identify any rough edges. Collect feedback from your users to build an intuition around the use-cases and prompts you expect your tools to enable.

## writing-effective-tools-for-agents#006

### Running an evaluation
 Next, you need to measure how well Claude uses your tools by running an evaluation. Start by generating lots of evaluation tasks, grounded in real world uses. We recommend collaborating with an agent to help analyze your results and determine how to improve your tools. See this process end-to-end in our tool evaluation cookbook .
 Held-out test set performance of our internal Slack tools 
 Generating evaluation tasks 
 With your early prototype, Claude Code can quickly explore your tools and create dozens of prompt and response pairs. Prompts should be inspired by real-world uses and be based on realistic data sources and services (for example, internal knowledge bases and microservices). We recommend you avoid overly simplistic or superficial “sandbox” environments that don’t stress-test your tools with sufficient complexity. Strong evaluation tasks might require multiple tool calls—potentially dozens.
 Here are some examples of strong tasks:
 Schedule a meeting with Jane next week to discuss our latest Acme Corp project. Attach the notes from our last project planning meeting and reserve a conference room.
 Customer ID 9182 reported that they were charged three times for a single purchase attempt. Find all relevant log entries and determine if any other customers were affected by the same issue.
 Customer Sarah Chen just submitted a cancellation request. Prepare a retention offer. Determine: (1) why they're leaving, (2) what retention offer would be most compelling, and (3) any risk factors we should be aware of before making an offer.
 And here are some weaker tasks:
 Schedule a meeting with jane@acme.corp next week.
 Search the payment logs for purchase_complete and customer_id=9182 .
 Find the cancellation request by Customer ID 45892.
 Each evaluation prompt should be paired with a verifiable response or outcome. Your verifier can be as simple as an exact string comparison between ground truth and sampled responses, or as advanced as enlisting Claude to judge the response. Avoid overly strict verifiers that reject correct responses due to spurious differences like formatting, punctuation, or valid alternative phrasings.
 For each prompt-response pair, you can optionally also specify the tools you expect an agent to call in solving the task, to measure whether or not agents are successful in grasping each tool’s purpose during evaluation. However, because there might be multiple valid paths to solving tasks correctly, try to avoid overspecifying or overfitting to strategies.
 
 Running the evaluation 
 We recommend running your evaluation programmatically with direct LLM API calls. Use simple agentic loops ( while -loops wrapping alternating LLM API and tool calls): one loop for each evaluation task. Each evaluation agent should be given a single task prompt and your tools.
 In your evaluation agents’ system prompts, we recommend instructing agents to output not just structured response blocks (for verification), but also reasoning and feedback blocks. Instructing agents to output these before tool call and response blocks may increase LLMs’ effective intelligence by triggering chain-of-thought (CoT) behaviors.
 If you’re running your evaluation with Claude, you can turn on interleaved thinking for similar functionality “off-the-shelf”. This will help you probe why agents do or don’t call certain tools and highlight specific areas of improvement in tool descriptions and specs.
 As well as top-level accuracy, we recommend collecting other metrics like the total runtime of individual tool calls and tasks, the total number of tool calls, the total token consumption, and tool errors. Tracking tool calls can help reveal common workflows that agents pursue and offer some opportunities for tools to consolidate.
 Held-out test set performance of our internal Asana tools 
 
 Analyzing results 
Agents are your helpful partners in spotting issues and providing feedback on everything from contradictory tool descriptions to inefficient tool implementations and confusing tool schemas. However, keep in mind that what agents omit in their feedback and responses can often be more important than what they include. LLMs don’t always say what they mean .
 Observe where your agents get stumped or confused. Read through your evaluation agents’ reasoning and feedback (or CoT) to identify rough edges. Review the raw transcripts (including tool calls and tool responses) to catch any behavior not explicitly described in the agent’s CoT. Read between the lines; remember that your evaluation agents don’t necessarily know the correct answers and strategies.
 Analyze your tool calling metrics. Lots of redundant tool calls might suggest some rightsizing of pagination or token limit parameters is warranted; lots of tool errors for invalid parameters might suggest tools could use clearer descriptions or better examples. When we launched Claude’s web search tool , we identified that Claude was needlessly appending 2025 to the tool’s query parameter, biasing search results and degrading performance (we steered Claude in the right direction by improving the tool description).

## writing-effective-tools-for-agents#007

### Collaborating with agents
 You can even let agents analyze your results and improve your tools for you. Simply concatenate the transcripts from your evaluation agents and paste them into Claude Code. Claude is an expert at analyzing transcripts and refactoring lots of tools all at once—for example, to ensure tool implementations and descriptions remain self-consistent when new changes are made.
 In fact, most of the advice in this post came from repeatedly optimizing our internal tool implementations with Claude Code. Our evaluations were created on top of our internal workspace, mirroring the complexity of our internal workflows, including real projects, documents, and messages.
 We relied on held-out test sets to ensure we did not overfit to our “training” evaluations. These test sets revealed that we could extract additional performance improvements even beyond what we achieved with "expert" tool implementations—whether those tools were manually written by our researchers or generated by Claude itself.
 In the next section, we’ll share some of what we learned from this process.

## writing-effective-tools-for-agents#008

## Principles for writing effective tools
 In this section, we distill our learnings into a few guiding principles for writing effective tools.

## writing-effective-tools-for-agents#009

### Choosing the right tools for agents
 More tools don’t always lead to better outcomes. A common error we’ve observed is tools that merely wrap existing software functionality or API endpoints—whether or not the tools are appropriate for agents. This is because agents have distinct “affordances” to traditional software—that is, they have different ways of perceiving the potential actions they can take with those tools
 LLM agents have limited "context" (that is, there are limits to how much information they can process at once), whereas computer memory is cheap and abundant. Consider the task of searching for a contact in an address book. Traditional software programs can efficiently store and process a list of contacts one at a time, checking each one before moving on.
 However, if an LLM agent uses a tool that returns ALL contacts and then has to read through each one token-by-token, it's wasting its limited context space on irrelevant information (imagine searching for a contact in your address book by reading each page from top-to-bottom—that is, via brute-force search). The better and more natural approach (for agents and humans alike) is to skip to the relevant page first (perhaps finding it alphabetically).
 We recommend building a few thoughtful tools targeting specific high-impact workflows, which match your evaluation tasks and scaling up from there. In the address book case, you might choose to implement a search_contacts or message_contact tool instead of a list_contacts tool.
 Tools can consolidate functionality, handling potentially multiple discrete operations (or API calls) under the hood. For example, tools can enrich tool responses with related metadata or handle frequently chained, multi-step tasks in a single tool call.
 Here are some examples:
 Instead of implementing a list_users , list_events , and create_event tools, consider implementing a schedule_event tool which finds availability and schedules an event.
 Instead of implementing a read_logs tool, consider implementing a search_logs tool which only returns relevant log lines and some surrounding context.
 Instead of implementing get_customer_by_id , list_transactions , and list_notes tools, implement a get_customer_context tool which compiles all of a customer’s recent & relevant information all at once.
 Make sure each tool you build has a clear, distinct purpose. Tools should enable agents to subdivide and solve tasks in much the same way that a human would, given access to the same underlying resources, and simultaneously reduce the context that would have otherwise been consumed by intermediate outputs.
 Too many tools or overlapping tools can also distract agents from pursuing efficient strategies. Careful, selective planning of the tools you build (or don’t build) can really pay off.
