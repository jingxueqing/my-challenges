# 待译批次 30

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## how-openai-uses-codex#005

## Page 6

## how-openai-uses-codex#006

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

## how-openai-uses-codex#007

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

## how-openai-uses-codex#008

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

## how-openai-uses-codex#009

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

## how-openai-uses-codex#010

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

## how-openai-uses-codex#011

## Page 11

## how-openai-uses-codex#012

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

## how-openai-uses-codex#013

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
