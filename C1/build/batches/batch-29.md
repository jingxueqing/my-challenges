# 待译批次 29

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## how-anthropic-uses-claude-code#029

## Page 17

## how-anthropic-uses-claude-code#030

Claude Code for product design
Main Claude Code use cases
The Product Design team
supports Claude Code, Claude.ai
Front-end polish and state management changes
and the Anthropic API,
Instead of creating extensive design documentation and going through
specializing in building Al
multiple rounds of feedback with engineers for visual tweaks (typefaces,
products. Even non-developers
colors, spacing), they now directly implement these changes using Claude
can use Claude Code to bridge
Code. Engineers noted they're making "large state management changes
the traditional gap between
that you typically wouldn't see a designer making," enabling them to
design and engineering, enabling
direct implementation of their
achieve the exact quality they envision.
design vision without extensive
back-and-forth with engineers.
GitHub Actions automated ticketing
Using Claude Code's GitHub integration, they can simply file issues/
tickets describing needed changes, and Claude automatically proposes
code solutions without having to open Claude Code, creating a seamless
bug-fixing and feature refinement workflow for their persistent backlog
of polish tasks.
Rapid interactive prototyping
By pasting mockup images into Claude Code, they generate fully
functional prototypes that engineers can immediately understand and
iterate on, replacing the traditional cycle of static Figma designs that
required extensive explanation and translation to working code.
Edge case discovery and system architecture understanding
They use Claude Code to map out error states, logic flows, and different
system statuses, allowing them to identify edge cases during design rather
than discovering them later in development, fundamentally improving
the quality of their initial designs.
Complex copy changes and legal compliance
For tasks like removing "research preview" messaging across the entire
codebase, they used Claude Code to find all instances, review surrounding
copy, coordinate changes with legal in real-time, and implement updates -
a process that took two 30-minute calls instead of a week of back-and-
forth coordination.
17|
CLAUDE CODE FOR PRODUCT DESIGN

## how-anthropic-uses-claude-code#031

## Page 18

## how-anthropic-uses-claude-code#032

Claude Code for product design
Team impact
Transformed core workflow
Claude Code becomes a primary design tool, with Figma and Claude Code
open 80% of the time.
2-3x faster execution
Visual and state management changes that previously required extensive
back-and-forth with engineers now implemented directly.
Weeks to hours cycle time
Complex projects like GA launch messaging that would take a week of
coordination now completed in two 30-minute calls.
Two distinct user experiences
Developers get "augmented workflow" (faster execution), while non-
technical users get "holy crap, I'm a developer workflow" (entirely new
capabilities previously impossible).
Improved design-engineering collaboration
Better communication and faster problem-solving because designers
understand system constraints and possibilities upfront.
Top tips from the
Get proper setup help from engineers
Product Design team
Have engineering teammates help with initial repository setup and
permissions - the technical onboarding is challenging for non-developers,
but once configured, it becomes transformative for daily workflow.
Use custom memory files to guide Claude's behavior
Create specific instructions telling Claude you're a designer with little
coding experience who needs detailed explanations and smaller,
incremental changes, dramatically improving the quality of Claude's
responses and making it less intimidating.
Leverage image pasting for prototyping
Use Command +V to paste screenshots directly into Claude Code - it excels
at reading designs and generating functional code, making it invaluable
for turning static mockups into interactive prototypes that engineers can
immediately understand and build upon.
18
CLAUDE CODE FOR PRODUCT DESIGN

## how-anthropic-uses-claude-code#033

## Page 19

## how-anthropic-uses-claude-code#034

Claude Code for RL engineering
Main Claude Code use cases
The RL Engineering team
focuses on efficient sampling in
Feature development with supervised autonomy
RL and weight transfers across
The team lets Claude Code write most of the code for small to medium
the cluster. They use Claude
features while providing oversight, such as implementing authentication
Code primarily for writing small
mechanisms for weight transfer components. They work interactively,
to medium features, debugging,
allowing Claude to take the lead but steering it when it goes off track.
and understanding complex
codebases, with an iterative
approach that includes frequent
Test generation and code review
checkpointing and rollbacks.
After implementing changes themselves, they ask Claude Code to add
tests or review their code. This automated testing workflow saves
significant time on routine but important quality assurance tasks.
Debugging and error investigation
They use Claude Code to debug errors with mixed results - sometimes it
identifies issues immediately and adds relevant tests, while other times
it struggles to understand the problem, but overall provides value when
it works.
Codebase comprehension and call stack analysis
One of the biggest changes in their workflow is using Claude Code to get
quick summaries of relevant components and call stacks, replacing
manual code reading or extensive debugging output generation.
Kubernetes operations guidance
They frequently ask Claude Code about Kubernetes operations that would
otherwise require extensive Googling, getting immediate answers for
configuration and deployment questions.
19
CLAUDE CODE FOR RL ENGINEERING

## how-anthropic-uses-claude-code#035

## Page 20

## how-anthropic-uses-claude-code#036

Claude Code for RL engineering
Development
Experimental approach enabled
workflow impact
They now use a "try and rollback" methodology, frequently committing
checkpoints so they can test Claude's autonomous implementation
attempts and revert if needed, enabling more experimental.
Documentation acceleration
Claude Code automatically adds helpful comments that save significant
time on documentation, though they note it sometimes adds comments
in odd places or uses questionable code organization.
Speed-up with limitations
While Claude Code can implement small-to-medium PRs with "relatively
little time" from them, they acknowledge it only works on first attempt
about one-third of the time, requiring either additional guidance or
manual intervention.
Top tips from the
Customize your Claude.md file for specific patterns
Add instructions to your Claude.md file to prevent Claude from making
RL Engineering team
repeated tool-calling mistakes, such as telling it to "run pytest not run and
don't cd unnecessarily - just use the right path." This significantly
improved consistency.
Use a checkpoint-heavy workflow
Regularly commit your work as Claude makes changes so you can easily
roll back when experiments don't work out. This enables a more
experimental approach to development without risk.
Try one-shot first, then collaborate
Give Claude a quick prompt and let it attempt the full implementation
first. If it works (about one-third of the time), you've saved significant
time. If not, then switch to a more collaborative, guided approach.
201
CLAUDE CODE FOR RL ENGINEERING

## how-anthropic-uses-claude-code#037

## Page 21

## how-anthropic-uses-claude-code#038

Claude Code for legal
Main Claude Code use cases
The Legal team discovered
Claude Code's potential through
Custom accessibility solution for family members
experimentation, and a desire to
Team members have built communication assistants for family members
learn about Anthropic's product
with speaking difficulties due to medical diagnoses. In just one hour, they
offerings. Additionally, one team
created a predictive text app using native speech-to-text that suggests
member had a personal use case
responses and speaks them using voice banks, solving gaps in existing
related to creating accessibility
tools for family and work
accessibility tools recommended by speech therapists.
prototypes that demonstrate
the technology's power for
Legal department workflow automation
non-developers.
They created prototype "phone tree" systems to help team members
connect with the right lawyer at Anthropic, demonstrating how legal
departments can build custom tools for common tasks without traditional
development resources.
Team coordination tools
Managers have built G Suite applications that automate weekly team
updates and track legal review status across products, allowing lawyers to
quickly flag items needing review through simple button clicks rather
than spreadsheet management.
Rapid prototyping for solution validation
They use Claude Code to quickly build functional prototypes they can
show to domain experts (like showing accessibility tools to UCSF
specialists) to validate ideas and identify existing solutions before
investing more time.
211
CLAUDE CODE FOR LEGAL

## how-anthropic-uses-claude-code#039

## Page 22

## how-anthropic-uses-claude-code#040

Claude Code for legal
Work style and impact
Planning in Claude.ai, building in Claude Code
They use a two-step process where they brainstorm and plan with
Claude.ai first, then move to Claude Code for implementation, asking it
to slow down and work step-by-step rather than outputting everything
at once.
Visual-first approach
They frequently use screenshots to show Claude Code what they want
interfaces to look like, then iterate based on visual feedback rather than
describing features in text.
Prototype-driven innovation
They emphasize overcoming the fear of sharing "silly" or "toy"
prototypes, as these demonstrations inspire others to see possibilities
they hadn't considered.
Security and
MCP integration concerns
As product lawyers, they immediately identify security implications of
compliance awareness
deep MCP integrations, noting how conservative security postures will
create barriers as Al tools access more sensitive systems.
Compliance tooling priorities
They advocate for building compliance tools quickly as AI
capabilities expand, recognizing the balance between innovation
and risk management.
Top tips from the
Plan extensively in Claude.ai first
Legal Department
Use Claude's conversational interface to flesh out your entire idea before
moving to Claude Code. Then ask Claude to summarize everything into a
step-by-step prompt for implementation.
Work incrementally and visually
Ask Claude Code to slow down and implement one step at a time so you
can copy-paste without getting overwhelmed. Use screenshots liberally to
show what you want interfaces to look like.
Share prototypes despite imperfection
Overcome the urge to hide "toy" projects or unfinished work - sharing
prototypes helps others see possibilities and sparks innovation across
departments that don't typically interact.
22
CLAUDE CODE FOR LEGAL

## how-openai-uses-codex#001

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

## how-openai-uses-codex#002

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

## how-openai-uses-codex#003

## Page 5

## how-openai-uses-codex#004

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
