# 待译批次 28

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## how-anthropic-uses-claude-code#013

## Page 9

## how-anthropic-uses-claude-code#014

Claude Code for inference
Main Claude Code use cases
The Inference team manages
the memory system that stores
Codebase comprehension and onboarding
information while Claude reads
The team relies heavily on Claude Code to quickly understand the
your prompt and generates its
architecture when joining a complex codebase. Instead of manually
response. Team members,
searching GitHub repos, they ask Claude to find which files call specific
especially those who are new to
functionalities, getting results in seconds rather than asking colleagues or
machine learning, can use Claude
Code extensively to bridge that
searching manually.
knowledge gap and accelerate
their work.
Unit test generation with edge case coverage
After writing core functionality, they ask Claude to write comprehensive
unit tests. Claude automatically includes missed edge cases, completing
what would normally take significant mental energy in minutes, acting
like a coding assistant they can review.
Machine learning concept explanation
Without a machine learning background, team members depend on
Claude to explain model-specific functions and settings. What would
require an hour of Google searching and reading documentation now
takes 10-20 minutes, reducing research time by 80%.
Cross-language code translation
When testing functionality in different programming languages, they
explain what they want to test and Claude writes the logic in the required
language (like Rust), eliminating the need to learn new languages just for
testing purposes.
Command recall and Kubernetes management
Instead of remembering complex Kubernetes commands, they ask Claude
for the correct syntax, like "how to get all pods or deployment status," and
receive the exact commands needed for their infrastructure work.
CLAUDE CODE FOR INFERENCE

## how-anthropic-uses-claude-code#015

## Page 10

## how-anthropic-uses-claude-code#016

Claude Code for inference
Team impact
Accelerated ML concept learning
Research time reduced by 80% - what took an hour of Google searching
now takes 10-20 minutes.
Faster codebase navigation
Can find relevant files and understand system architecture in seconds
instead of asking colleagues.
Comprehensive test coverage
Claude automatically generates unit tests with edge cases, relieving
mental burden while maintaining code quality.
Language barrier elimination
Can implement functionality in unfamiliar languages like Rust without
needing to learn it.
Top tips from the
Test knowledge base functionality first
Inference team
Try asking various questions to see if Claude can answer faster than
Google search. If it's faster and more accurate, it's a valuable time-saving
tool for your workflow.
Start with code generation
Give Claude specific instructions and ask it to write logic, then verify
correctness. This helps build trust in the tool's capabilities before using it
for more complex tasks.
Use it for test writing
Having Claude write unit tests relieves significant pressure from daily
development work. Leverage this feature to maintain code quality without
spending time thinking through all test cases manually.
10
CLAUDE CODE FOR INFERENCE

## how-anthropic-uses-claude-code#017

## Page 11

## how-anthropic-uses-claude-code#018

Claude Code for data science
and visualization
Main Claude Code use cases
Data Science and ML
Engineering teams need
Building JavaScript/TypeScript dashboard apps
sophisticated visualization
Despite knowing "very little JavaScript and TypeScript," the team uses
tools to understand model
Claude Code to build entire React applications for visualizing RL model
performance, but building these
performance and training data. They give Claude control to write full
tools often requires expertise
in unfamiliar languages and
applications from scratch, like a 5,000-line TypeScript app, without
frameworks. Claude Code
needing to understand the code themselves. This is critical because
enables these teams to build
visualization apps are relatively low context and don't require
production-quality analytics
understanding the entire monorepo, allowing rapid prototyping of tools
dashboards without becoming
to understand model performance during training and evaluations.
full-stack developers.
Handling repetitive refactoring tasks
When faced with merge conflicts or semi-complicated file refactoring
that's too complex for editor macros but not large enough for major
development effort, they use Claude Code like a "slot machine" - commit
their state, let Claude work autonomously for 30 minutes, and either
accept the solution or restart fresh if it doesn't work.
Creating persistent analytics tools instead of throwaway notebooks
Instead of building one-off Jupyter notebooks that get discarded, the
team now has Claude build permanent React dashboards that can be
reused across future model evaluations. This is important because
understanding Claude's performance is "one of the most important things
for the team" - they need to understand how models perform during
training and evaluations, which "is actually non-trivial and simple tools
can't get too much signal from looking at a single number go up."
Zero-dependency task delegation
For tasks in completely unfamiliar codebases or languages, they delegate
entire implementation to Claude Code, leveraging its ability to gather
context from the monorepo and execute tasks without their involvement
in the actual coding process. This allows productivity in areas outside
their expertise instead of spending time learning new technologies.
11|
CLAUDE CODE FOR DATA SCIENCE AND VISUALIZATION

## how-anthropic-uses-claude-code#019

## Page 12

## how-anthropic-uses-claude-code#020

Claude Code for data science
and visualization
Team impact
Achieved 2-4x time savings
Routine refactoring tasks that were tedious but manageable manually
are now completed much faster.
Built complex applications in unfamiliar languages
Created 5,000-line TypeScript applications despite having minimal
JavaScript/TypeScript experience.
Shifted from throwaway to persistent tools
Instead of disposable Jupyter notebooks, now building reusable React
dashboards for model analysis.
Direct model improvement insights
Firsthand Claude Code experience informs development of better
memory systems and UX improvements for future model iterations.
Enabled visualization-driven decision making
Better understanding of Claude's performance during training and
evaluations through advanced data visualization tools.
Top tips from the
Treat it like a slot machine
Data Science and
Save your state before letting Claude work, let it run for 30 minutes,
then either accept the result or start fresh rather than trying to wrestle
ML Engineering teams
with corrections. Starting over often has a higher success rate than trying
to fix Claude's mistakes.
Interrupt for simplicity when needed
While supervising, don't hesitate to stop Claude and ask "why are
you doing this? Try something simpler." The model tends toward
more complex solutions by default but responds well to requests for
simpler approaches.
12.
CLAUDE CODE FOR DATA SCIENCE AND VISUALIZATION

## how-anthropic-uses-claude-code#021

## Page 13

## how-anthropic-uses-claude-code#022

Claude Code for API
Main Claude Code use cases
The API Knowledge team works
on features like PDF support,
First-step workflow planning
citations, and web search that
The team uses Claude Code as their "first stop" for any task, asking it
bring additional knowledge into
to identify which files to examine for bug fixes, feature development,
Claude's context window.
or analysis. This replaces the traditional time-consuming process of
Working across large, complex
manually navigating the codebase and gathering context before
codebases means constantly
encountering unfamiliar code
starting work.
sections, spending significant
time understanding which files to
Independent debugging across codebases
examine for any given task, and
The team now has the confidence to tackle bugs in unfamiliar parts of the
building context before making
codebase instead of asking others for help. They can ask Claude "Do you
changes. Claude Code improves
think you can fix this bug? This is the behavior I'm seeing" and often get
this experience by serving as a
immediate progress, which wasn't feasible before given the time
guide that can help them
investment required.
understand system architecture,
identify relevant files, and
Model iteration testing through dogfooding
explain complex interactions.
Claude Code automatically uses the latest research model snapshots,
making it their primary way of experiencing model changes. This gives
them direct feedback on model behavior changes during development
cycles, which they hadn't experienced during previous launches.
Eliminating context-switching overhead
Instead of copying code snippets and dragging files into Claude.ai
while explaining problems extensively, they can ask questions directly in
Claude Code without additional context gathering, significantly reducing
mental overhead.
CLAUDE CODE FOR API

## how-anthropic-uses-claude-code#023

## Page 14

## how-anthropic-uses-claude-code#024

Claude Code for API
Team impact
Increased confidence in tackling unfamiliar areas
Team members can independently debug bugs and investigate incidents
in unfamiliar codebases.
Significant time savings in context gathering
Eliminated the overhead of copying code snippets and dragging files into
Claude.ai, reducing mental context-switching burden.
Faster rotation onboarding
Engineers rotating to new teams can quickly navigate unfamiliar
codebases and contribute meaningfully without extensive colleague
consultation.
Enhanced developer happiness
Team reports feeling happier and more productive with reduced friction
in daily workflows.
Top tips from the
Treat it as an iterative partner, not a one-shot solution
API Knowledge team
Rather than expecting Claude to solve problems immediately, approach
it as a collaborator you iterate with. This works better than trying to get
perfect solutions on the first try.
Use it for building confidence in unfamiliar areas
Don't hesitate to tackle bugs or investigate incidents outside your
expertise - Claude Code makes it feasible to work independently in areas
that would normally require extensive context building.
Start with minimal information
Begin with just the bare minimum of what you need and let Claude guide
you through the process, rather than front-loading extensive explanations.
14|
CLAUDE CODE FOR API

## how-anthropic-uses-claude-code#025

## Page 15

## how-anthropic-uses-claude-code#026

Claude Code for growth
marketing
Main Claude Code use cases
The Growth Marketing
team focuses on building out
Automated Google Ads creative generation
performance marketing channels
The team built an agentic workflow that processes CSV files containing
across paid search, paid social,
hundreds of existing ads with performance metrics, identifies
mobile app stores, email
underperforming ads for iteration, and generates new variations that
marketing, and SEO. As a non-
meet strict character limits (30 characters for headlines, 90 for
technical team of one, they use
Claude Code to automate
descriptions). Using two specialized sub-agents (one for headlines, one
repetitive marketing tasks and
for descriptions), the system can generate hundreds of new ads in
create agentic workflows that
minutes instead of requiring manual creation across multiple campaigns.
would traditionally require
This has enabled them to test and iterate at scale, something that would
significant engineering
have taken a significant amount of time to achieve previously.
resources.
Figma plugin for mass creative production
Instead of manually duplicating and editing static images for paid
social ads, they developed a Figma plugin that identifies frames and
programmatically generates up to 100 ad variations by swapping
headlines and descriptions, reducing what would take hours of copy-
pasting to half a second per batch. This enables 10x creative output,
allowing the team to test vastly more creative variations across key
social channels.
Meta Ads MCP server for campaign analytics
They created an MCP server integrated with Meta Ads API to query
campaign performance, spending data, and ad effectiveness directly
within the Claude Desktop app, eliminating the need to switch between
platforms for performance analysis, saving critical time where every
efficiency gain translates to better ROI.
Advanced prompt engineering with memory systems
They implemented a rudimentary memory system that logs hypotheses
and experiments across ad iterations, allowing the system to pull previous
test results into context when generating new variations, creating a self-
improving testing framework. This enables systematic experimentation
that would be impossible to track manually.
15
CLAUDE CODE FOR GROWTH MARKETING

## how-anthropic-uses-claude-code#027

## Page 16

## how-anthropic-uses-claude-code#028

Claude Code for growth
marketing
Team impact
Dramatic time savings on repetitive tasks
Ad copy creation reduced from 2 hours to 15 minutes, freeing up time for
strategic work.
10x increase in creative output
The team can now test vastly more ad variations across channels with
automated generation and Figma integration.
Operating like a larger team
The team can handle tasks that traditionally required dedicated
engineering resources.
Strategic focus shift
The team can spend more time on overall strategy and building agentic
automation rather than manual execution.
Top tips from the
Identify API-enabled repetitive tasks
Look for workflows involving repetitive actions with tools that have
Growth Marketing
APIs (like ad platforms, design tools, analytics platforms). These are
team
prime candidates for automation and where Claude Code provides the
most value.
Break complex workflows into specialized sub-agents
Instead of trying to handle everything in one prompt or workflow, create
separate agents for specific tasks like their headline agent vs. description
agent). This makes debugging easier and improves output quality when
dealing with complex requirements.
Thoroughly brainstorm and prompt plan before coding
Spend significant time upfront using Claude.ai to think through your
entire workflow, then have Claude.ai create a comprehensive prompt and
code structure for Claude Code to reference. Also, work step-by-step
rather than asking for one-shot solutions to avoid Claude getting
overwhelmed by complex tasks.
161
CLAUDE CODE FOR GROWTH MARKETING
