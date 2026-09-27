# how-openai-uses-codex（中英对照）

### seg 001

## Page 1

OpenAl
How OpenAl
uses Codex
sta
1C
=
a
• a s
st ( ) dynam
= t f
shape (x) re
t
n
[dynamic
S
is None e
]
s for i, s
i n
u m
eratestat
ef softmax
: - 1) : x
reduce
axis =
& Merged
+217 -196
k e
e
pdim
S = T
u e
X
f
X р
1
e
1
X

## Page 2

Contents
Introduction
Use Cases
Code understanding
Refactoring and migrations
Performance optimization
Improving test coverage
Increasing development velocity
Staying in flow
Exploration and ideation
Best Practices
Looking Ahead
2
How OpenAl uses Codex

## Page 3

Introduction
Codex is used daily across numerous technical teams at OpenAl like Security, Product Engineering,
Frontend, API, Infrastructure, and Performance Engineering. Teams are using it to accelerate a
range of engineering tasks, from understanding complex systems and refactoring large codebases
to shipping new features and resolving incidents under tight deadlines.
Drawing from interviews with OpenAl engineers and internal usage data, we've compiled use cases
and best practices that highlight how Codex helps our teams move faster, improve work quality,
and manage complexity at scale.
3
How OpenAl uses Codex

## Page 4

> （未译）

### seg 002

Use case 1
Code understanding
Codex helps our teams get up to speed quickly in unfamiliar parts of the codebase when
onboarding, debugging, or investigating an incident.
They often use Codex to locate the core logic of a feature, map out relationships between services
or modules, and trace data flow through a system. It also helps surface architecture patterns or
missing pieces of documentation that would otherwise require significant manual effort to
generate.
During incident response, Codex helps engineers ramp into new areas quickly by surfacing
interactions between components or tracing how failure states propagate across systems.
Anecdotes from our teams
When I fix a bug, l use
When I'm on-call, I paste
Codex answers my
Ask mode to see where
the stack trace and ask
'Where would I do this?'
else in the codebase the
Codex where the auth
repo questions across
same issue might appear.
flow lives. It jumps
Terraform and Python
straight to the right files
way faster than grep.
so / can triage fast.
Performance Engineer,
Site Reliability Engineer,
DevOps Engineer,
Retrieval Systems
API Platform
Infrastructure Services
Try using Codex for code understanding
Where is the authentication logic
with these sample prompts:
implemented in this repo?
• Summarize how requests flow through this
service from entrypoint to response.
\ Which modules interact with [insert module
namel and how are failures handled?
4
How OpenAl uses Codex

> （未译）

### seg 003

## Page 5

> （未译）

### seg 004

Use case 2
Refactoring and migrations
Codex is commonly used to make changes that span multiple files or packages. For example, when
engineers are updating an APl, changing how a pattern is implemented, or migrating to a new
dependency, Codex makes it easy to apply changes consistently.
It's especially useful when the same update needs to be made across dozens of files, or when the
update requires awareness of structure and dependencies that aren't easily caught with a regex or
find-and-replace.
They're also using it for code cleanup by breaking up oversized modules, replacing old patterns
with modern ones, or preparing code for better testability.
Anecdotes from our teams
Codex swapped every legacy
To clear launch blockers, I have Codex
getUserByld() for our new service pattern
scan for every instance of the old pattern,
and opened the PR. It did in minutes what
summarize the impact in Markdown, then
would've taken hours.
open PRs with the fixes.
Backend Engineer,
Product Engineer,
ChatGPT Web
ChatGPT Enterprise
Try using Codex for refactoring and
Split this file into separate modules by
migrations with these sample prompts:
concern and generate tests for each one.
Convert all callback-based database access
to async/await.
5
How OpenAl uses Codex

> （未译）

### seg 005

## Page 6

> ## 第 6 页

### seg 006

Use case 3
Performance optimization
Codex is used to identify and address performance bottlenecks.
During tuning or reliability efforts, engineers prompt Codex to analyze slow or memory-intensive
code paths, such as inefficient loops, redundant operations, or costly queries and suggest
optimized alternatives, often resulting in meaningful gains in efficiency and reliability.
Codex is also used to support code health by identifying risky or deprecated patterns that are still
in active use. Our teams lean on it to help reduce long-term tech debt and proactively prevent
regressions.
Anecdotes from our teams
I use Codex to scan for repeated
Codex is great for spotting performance
expensive DB calls. It's great at flagging
issues quickly— I save 30 minutes of work
hot paths and drafting batched queries /
by spending 5 minutes on a prompt.
can later tune.
Infrastructure Engineer,
Platform Engineer,
API Reliability
Model Serving
Try using Codex for performance
• Optimize this loop for memory efficiency and
optimization with these sample prompts:
explain why your version is faster.
Find repeated expensive operations in this
request handler and suggest caching
opportunities.
Suggest a faster way to batch DB queries in
this function.
6
How OpenAl uses Codex

> 用例 3
> 性能优化
> Codex 用于识别并处理性能瓶颈。
> 在性能调优或提升可靠性的工作中，工程师会提示 Codex 分析缓慢或占用内存较高的代码路径，例如低效循环、冗余操作或开销高昂的查询，并给出优化替代方案，通常能带来效率与可靠性上的明显收益。
> Codex 也用于维护代码健康度：识别那些仍在使用中、但存在风险或已被弃用的模式。我们的团队借助它减少长期技术债务，并主动预防回归。
> 
> 来自我们团队的一手案例
> - 我用 Codex 扫描重复出现的高开销数据库调用；它很擅长标记热点路径，并起草我之后可以调优的批量查询。—— 基础设施工程师，API 可靠性
> - Codex 很擅长快速发现性能问题——我只花 5 分钟写提示词，就省下了 30 分钟的工作量。—— 平台工程师，模型服务
> 
> 用这些示例提示词让 Codex 帮你做性能优化：
> - 把这个循环优化到内存友好，并解释为什么你的版本更快。
> - 在这个请求处理函数中找出重复的高开销操作，并给出缓存建议。
> - 在这个函数中给出更快的数据库批量查询方案。
> 6
> OpenAI 如何使用 Codex

### seg 007

## Page 7

Use case 4
Improving test coverage
Codex helps engineers write tests faster — especially in places where coverage is thin or
completely missing.
When working on a bug fix or refactor, engineers often ask Codex to suggest tests that cover edge
cases or likely failure paths. For new code, it can generate unit or integration tests based on the
function signature and surrounding logic.
Codex is particularly helpful for identifying boundary conditions like empty inputs, max length, or
unusual but valid states that are often missed in initial tests.
Anecdotes from our teams
I point Codex at low-coverage modules
When switching mono-repo branches is
overnight and wake up to runnable
painful, I have Codex write the tests and
unit-test PRs.
kick-off Cl while / keep working on my
branch.
Frontend Engineer,
Backend Engineer,
ChatGPT Desktop
Payments & Billing
Try using Codex for improving test
• Write unit tests for this function, including
coverage with these sample prompts:
edge cases and failure paths.
Generate a property-based test for this
sorting utility.
• Extend this test file to cover missing
scenarios around null inputs and invalid
states.
7
How OpenAl uses Codex

## Page 8

> ## 第 7 页
> 
> 用例 4
> 提升测试覆盖率
> Codex 帮助工程师更快地编写测试——在覆盖率薄弱或完全缺失的地方尤其有用。
> 在修复缺陷或重构时，工程师常常让 Codex 给出覆盖边界情况或可能失败路径的测试。对于新代码，它可以根据函数签名和周边逻辑生成单元测试或集成测试。
> Codex 在识别边界条件上尤其有用，比如空输入、最大长度，或那些不常见但合法的状态——这些在初始测试里往往被漏掉。
> 
> 来自我们团队的一手案例
> - 我把 Codex 指向覆盖率低的模块，第二天早上醒来就能拿到可直接运行的单元测试 PR。—— 前端工程师，ChatGPT 桌面端
> - 在 monorepo 分支之间切换很痛苦时，我让 Codex 写测试并把工作开跑，同时我继续在自己的分支上干活。—— 后端工程师，支付与计费
> 
> 用这些示例提示词让 Codex 帮你提升测试覆盖率：
> - 为这个函数编写单元测试，覆盖边界情况和失败路径。
> - 为这个排序工具生成一个基于属性的测试。
> - 扩展这个测试文件，覆盖空输入和非法状态等缺失场景。
> 7
> OpenAI 如何使用 Codex

### seg 008

Use case 5
Increasing development velocity
Codex helps teams move faster by accelerating both the start and end of the development cycle.
When kicking off a new feature, engineers use it to scaffold boilerplate — generating folders,
modules, and API stubs to get runnable code up quickly without hand-wiring every piece.
As projects approach release, Codex helps meet tight deadlines by handling smaller but essential
tasks like triaging bugs, filling in last-mile implementation gaps, and generating rollout scripts,
telemetry hooks, or config files.
It's also used to turn product feedback into starter code. Engineers often paste in a user request or
spec and have Codex generate a rough draft they can return to and refine later.
Anecdotes from our teams
I was in meetings all day and still merged
Codex helped ship 3-4 low-priority fixes
4 PRs because Codex was working in the
perfectly that would've languished in the
background.
backlog, which was super empowering.
Product Engineer,
Full-Stack Engineer,
ChatGPT Enterprise
Internal Tools
Try using Codex for increasing development Scaffold a new API route for POST /events
velocity with these sample prompts:
with basic validation and logging.
\ Generate a telemetry hook for tracking
success/failure of the new onboarding flow,
using this template [insert example of your
telemetry code].
) Create a stub implementation based on this
spec: [insert spec or product feedback].
8
How OpenAl uses Codex

> ## 第 8 页
> 
> 用例 5
> 提升开发速度
> Codex 通过加速开发周期的起点和终点，帮助团队走得更快。
> 在启动新功能时，工程师用它来搭建样板代码——生成目录、模块和 API 桩，快速拿到可运行的代码，而不用手工把每一块接起来。
> 当项目接近发布时，Codex 通过处理那些较小但必要的任务来帮助赶上紧张的时间线，例如分诊缺陷、补齐最后一公里的实现缺口，以及生成上线脚本、遥测钩子或配置文件。
> 它也被用来把产品反馈变成起步代码。工程师常常把用户请求或规格说明粘进去，让 Codex 生成一份粗略草稿，之后再回来打磨。
> 
> 来自我们团队的一手案例
> - 我整天都在开会，却仍然合并了 4 个 PR，因为 Codex 在后台替我干活。—— 产品工程师，ChatGPT 企业版
> - Codex 帮着交付了 3-4 个本来会烂在待办列表里的低优先级修复，这让人特别有掌控感。—— 全栈工程师，内部工具
> 
> 用这些示例提示词让 Codex 帮你提升开发速度：
> - 为 POST /events 搭建一条新的 API 路由，带基础校验和日志。
> - 生成一个遥测钩子，跟踪新引导流程的成功/失败，使用这个模板 [插入你的遥测代码示例]。
> - 根据这份规格说明创建一个桩实现：[插入规格说明或产品反馈]。
> 8
> OpenAI 如何使用 Codex

### seg 009

## Page 9

Use case 6
Staying in flow
Codex helps our engineers stay productive when their schedules are fragmented and filled with
interruptions.
It's used to capture unfinished work, turn notes into working prototypes, or spin off exploratory
tasks that can be revisited later. This makes it easier to pause and resume work without losing
context, especially when they're on call or have a lot of meetings.
Anecdotes from our teams
If I spot a drive-by fix, I fire a Codex task
I routinely forward Slack threads, Datadog
instead of swapping branches and review
traces, issues and more to Codex so / can
its PR when I'm free.
stay focused on high priority work.
Backend Engineer,
API Engineer,
ChatGPT API
Infrastructure Observability
Try using Codex for staying in flow
Generate a plan to refactor this service
with these sample prompts:
and split it into smaller modules.
Stub out the retry logic and add a TODO —
I'll fill in the backoff logic later.
Summarize this file so I can pick up where
I left off tomorrow.
9
How OpenAl uses Codex

## Page 10

> ## 第 9 页
> 
> 用例 6
> 保持心流
> 当工程师的日程被切碎、充满打断时，Codex 帮助他们保持产出。
> 它被用来接住未完成的工作、把笔记变成可运行的原型，或者分出一些可以稍后再回来看的探索性任务。这让暂停和恢复工作变得更容易，而不至于丢失上下文，尤其是在值班或会议很多的时候。
> 
> 来自我们团队的一手案例
> - 如果我发现一个顺手能修的问题，我会直接给 Codex 派个任务，而不是切换分支、等有空时再去评审它的 PR。—— 后端工程师，ChatGPT API
> - 我习惯把 Slack 讨论串、Datadog 调用链、issue 等等转发给 Codex，这样我就能继续专注于高优先级的工作。—— API 工程师，基础设施可观测性
> 
> 用这些示例提示词让 Codex 帮你保持心流：
> - 生成一个重构这个服务的计划，并把它拆成更小的模块。
> - 把重试逻辑先搭出桩并加个 TODO——退避逻辑我之后再补。
> - 总结这个文件，方便我明天接着上次的地方继续。
> 9
> OpenAI 如何使用 Codex

### seg 010

Use case 7
Exploration and ideation
Codex is also useful for open-ended work like finding alternative solutions or validating design
decisions. You can prompt for different ways of solving a problem, explore unfamiliar patterns, or
pressure-test assumptions. This helps surface tradeoffs, expand design options, and sharpen
implementation choices.
It's also used to identify related bugs. Given a known issue or deprecated method, Codex can
identify similar patterns elsewhere in the code, making it easier to catch regressions or finish
cleanup work.
Anecdotes from our teams
Codex helps me solve the cold-start
After I fix a bug / ask Codex where similar
problem - I paste a spec and docs and it
bugs might lurk, then spin follow-up tasks.
scaffolds code or shows me what I forgot.
Product Engineer,
Performance Engineer,
ChatGPT Desktop
Retrieval Systems
Try using Codex for exploration and
! How would this work if the system were
ideation with these sample prompts
event-driven instead of request/response?
Find all modules that manually build SQL
strings instead of using our query builder.
Rewrite this in a more functional style, avoid
mutation and side effects.
10
How OpenAl uses Codex

> ## 第 10 页
> 
> 用例 7
> 探索与构思
> Codex 对开放式工作也很有用，比如寻找替代方案或验证设计决策。你可以让它给出解决问题的不同思路、探索不熟悉的模式，或对假设做压力测试。这有助于呈现权衡、扩展设计选项，并让实现选择更清晰。
> 它还被用来发现相关缺陷。给定一个已知问题或已弃用的方法，Codex 能找出代码中其他地方的相似模式，从而更容易抓住回归或完成清理工作。
> 
> 来自我们团队的一手案例
> - Codex 帮我解决冷启动问题——我把规格说明和文档粘进去，它就能搭出代码框架，或者告诉我漏掉了什么。—— 产品工程师，ChatGPT 桌面端
> - 我修完一个缺陷后，会让 Codex 找出相似缺陷可能潜伏的位置，然后派发后续任务。—— 性能工程师，检索系统
> 
> 用这些示例提示词让 Codex 帮你探索与构思：
> - 如果系统改成事件驱动而不是请求/响应，会怎样运作？
> - 找出所有手工拼接 SQL 字符串、而没用我们的查询构造器的模块。
> - 用更函数式的风格重写这段代码，避免可变状态和副作用。
> 10
> OpenAI 如何使用 Codex

### seg 011

## Page 11

> ## 第 11 页

### seg 012

Best practices
Codex works best when it's given structure, context, and room to iterate. Here are some of the
habits OpenAl teams are cultivating to get consistent value out of it in day-to-day work.
Start with Ask Mode
For large changes, start by prompting Codex for an
implementation plan using Ask mode, which then becomes the
input for follow-up prompts when you switch to Code Mode.
This two-step flow keeps Codex grounded and helps avoid
errors in its output. Codex works best with well-scoped tasks
that would take you or a teammate about an hour to complete
or a few hundred lines of code to implement. As models
improve, expect the size of the tasks it can take on to increase.
Iteratively improve Codex's
Setting a startup script, environment variables, and internet
development environment
access significantly reduces Codex's error rate. As you run
tasks, look for build errors that can be corrected in Codex's
environment configuration. This may take a few iterations, but
gives significant efficiency gains in the long run.
Structure your prompt as if
Codex responds better when prompts mirror how you'd
you are writing a Github Issue
describe a change in a PR or issue. That means including file
paths, component names, diffs, and doc snippets when
relevant. Prompting with patterns like "Implement this the
same way it's done in [module X]" improves results.
Use the Codex task queue
Fire off tasks to capture tangential ideas, partial work, or
as a lightweight backlog
incidental fixes. There's no pressure to generate a full PR in one
go. Codex works well as a staging area you can return to when
you're back in focus.
11
How OpenAl uses Codex

> 最佳实践
> Codex 在获得结构、上下文和迭代空间时表现最好。以下是 OpenAI 各团队正在培养的一些习惯，用来在日常工作中稳定地获得价值。
> 
> 从 Ask 模式开始
> 对于大改动，先用 Ask 模式让 Codex 给出实现计划；当你切到 Code 模式后，这份计划就成为后续提示词的输入。这个两步流程能让 Codex 更接地气，也有助于避免输出出错。Codex 最擅长边界清晰的任务：你或同事大约一小时能做完，或者几百行代码能实现的那种。随着模型进步，它能承担的任务规模也会变大。
> 
> 迭代改进 Codex 的开发环境
> 设置好启动脚本、环境变量和网络访问，能显著降低 Codex 的错误率。执行任务时，留意那些可以通过调整 Codex 环境配置来修正的构建错误。这可能需要几轮迭代，但长期看能带来明显的效率提升。
> 
> 像写 GitHub Issue 那样组织你的提示词
> 当提示词模仿你在 PR 或 issue 里描述改动的方式时，Codex 的响应会更好。也就是说，在相关时给出文件路径、组件名、diff 和文档片段。用「按 [模块 X] 里的做法来实现这个」这类模式来提示，效果会更好。
> 
> 把 Codex 任务队列当作轻量待办列表
> 随手派发任务，用来接住跑题的灵感、半成品工作或顺手的小修小补。不必强求一次就生成完整 PR。Codex 很适合作为一个暂存区，等你重新进入专注状态时再回来处理。
> 11
> OpenAI 如何使用 Codex

### seg 013

## Page 12

Best practices
Use AGENTS.md to
Maintain an AGENTS.md file to help Codex operate more
supply persistent context
effectively in your repo across prompts. These files typically
include naming conventions, business logic, known quirks, or
dependencies Codex can't infer from the code alone. Learn
more on structuring your AGENTS.md file in the docs.
Leverage "Best of N"
The Best-of-N feature lets you simultaneously generate
to improve output
multiple responses for a single task to quickly explore multiple
solutions and pick the best one. For more complicated tasks,
you can review several iterations and combine parts of different
responses to get a stronger result.
Looking ahead
Codex is still in research preview, but it's already making a real impact in how we build, helping us
move faster, write better code, and take on work that would've otherwise never been prioritized.
We're excited by the potential ahead - as our models get better and Codex becomes more deeply
integrated into our workflows, we're looking forward to unlocking even more powerful ways to
develop software with it. We'll continue to share what we learn along the way.
12
How OpenAl uses Codex

## Page 13

OpenAl

> ## 第 12 页
> 
> 最佳实践
> 
> 用 AGENTS.md 提供持久上下文
> 维护一个 AGENTS.md 文件，帮助 Codex 在跨提示词的整个仓库工作中更有效地运作。这类文件通常包含命名约定、业务逻辑、已知的坑，或 Codex 无法仅凭代码推断的依赖关系。关于如何组织 AGENTS.md，可在文档中了解更多。
> 
> 利用「Best of N」提升输出
> Best-of-N 功能让你为同一个任务同时生成多个回答，快速探索多种方案并挑出最好的一个。对于更复杂的任务，你可以审阅多个迭代版本，并把不同回答的部分组合起来，得到更强的结果。
> 
> 展望
> Codex 仍处于研究预览阶段，但它已经在改变我们的构建方式——帮我们走得更快、写得更好，并承担那些原本永远不会被排上优先级的工作。我们对未来的潜力感到兴奋：随着模型变得更好、Codex 更深入地融入我们的工作流，我们期待解锁更多强大的软件开发方式。我们也会持续分享沿途学到的东西。
> 12
> OpenAI 如何使用 Codex
> 
> ## 第 13 页
> 
> OpenAI

