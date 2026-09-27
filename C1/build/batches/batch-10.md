# 待译批次 10

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## devin-coding-agents-101#003

While a human paired with an AI assistant can achieve more than any AI alone, an autonomous agent's ability to handle tasks end to end allows for a new level of multi-tasking, turning every engineer into an engineering manager.

Adapting to working effectively alongside these new AI colleagues can take some time. Interestingly, we've observed that senior-to-staff level engineers tend to adopt and become proficient with these tools the fastest. Ultimately, these tools will become commonplace across all levels of engineering. Based on our experience and customer feedback, we want to share key insights and lessons learned to help everyone successfully integrate these tools into their workflows.

(Getting Started)

## Prompting Basics

These fundamental guidelines will help you effectively interact with coding agents in 2025. If you take nothing else away, you should at least remember these.

### Say how you want things done, not just what

## devin-coding-agents-101#004

Think of the agent as a junior coding partner whose decision-making can be unreliable. Simple tasks can be described directly, but for more complex tasks, clearly outline your preferred approach from the outset. Providing the agent with the overall architecture and logic upfront not only boosts its chances of success but also reduces your time reviewing code, as you will already be familiar with the intended method.

#### Example:

Instead of "add unit tests," specify the functionality to test, identify important edge cases, and clarify what needs mocking, if anything.

### Tell the agent where to start

Think about where you'd start if you were handling the task yourself. Even if you don't know specific file or function names, mention the repository, relevant documentation, and key components involved. Clearly indicating these elements minimizes wasted effort and confusion.

#### Example:

"Please add support for Google models to our code. You should look at the latest docs [here](link) and create a new implementation file in the model groups directory"

### Practice defensive prompting

## devin-coding-agents-101#005

Imagine giving the same prompt to a new intern. Where would confusion or errors likely arise? Anticipate these points and proactively clarify your instructions to avoid ambiguity.

#### Example:

"Please fix the C++ bindings for our search module to pass the new unit tests. Be careful, you will probably need to recompile the bindings each time you change the code before you test."

### Give access to CI, tests, types, and linters

Much of the magic of agents comes from their ability to fix their own mistakes and iterate against error messages. Providing strong feedback loops through tools like type checkers, linters, and unit tests greatly enhances their performance. Consider typed Python over plain Python, or TypeScript over JavaScript. Teach your agent how to run common checks and tests, ensuring it has all necessary packages and access rights. If the agent can interact with a browser, provide clear instructions on running your front-end development environment.

#### Example:

Our team transitioned from mostly untyped Python SDKs to exclusively typed SDKs (this is also a good task ideally for coding agents).

### Leverage your expertise

## devin-coding-agents-101#006

Everything above becomes easier when you're familiar with your codebase. Even simple tasks benefit from your ability to verify logic and results. Human oversight remains essential—ultimately, you hold responsibility for the final correctness of the code. Ownership and verification will continue to be critical responsibilities for human engineers, even as these tools become increasingly sophisticated.

(Getting Started)

## Using Agents in your Workflow

Once you've got the basics of talking to an agent down, it's time to bring these AI helpers into your daily workflow. Here are some practical ways to make agents part of your routine:

### Take on new tasks immediately

Imagine a teammate messaging you, "Hey, could we build X quickly?" or "We need to tweak Y." Instead of letting it interrupt your flow, just send a quick prompt to an autonomous agent to investigate or make the change. This frees you to stay focused on your main tasks. Got an interesting side project idea? Need to quickly prototype something, scrape data, or reproduce research? Delegate to your agent and circle back later.

#### Example:

Many teams simply tag @Devin on Slack when discussing bug fixes or minor feature updates.

## devin-coding-agents-101#007

### Code on the go

Picture yourself commuting or traveling when an urgent bug pops up, or you realize you might have left a mistake in your code. No worries! Autonomous agents often support mobile access, letting you address these issues instantly. Whether through Slack's mobile app or a dedicated mobile app, many agents let you resolve problems on the go, even if your wifi is sketchy.

#### Example:

Having this optionality has made our own team much more productive on car rides and flights.

### Hand off your chores

Stuck bisecting for old commits or updating documentation for a new feature? Hand these repetitive tasks off to your agent. You'll save precious time and stay focused on more creative and impactful work.

#### Example:

In our team, it is common for an engineer to ship a change and then have an agent update all the relevant docs & user-facing copy.

### Skip the analysis paralysis

Stuck deciding if a refactor will actually simplify your code? Can't choose between two architectural approaches? Have your agent implement both options. With concrete examples to compare, decision-making becomes straightforward, and you won't hurt any feelings by discarding a solution.

#### Example:

## devin-coding-agents-101#008

When choosing between Lexical and Slate for text boxes, we had agents implement each. Slate won out for delivering the better end result.

### Set up preview deployments

Set your CI/CD pipeline to automatically create preview deployments with each new PR, giving you an instant live URL. This is particularly handy when reviewing frontend tasks completed by AI agents.

#### Example:

Vercel is a deployment platform that makes preview deployments super easy.

(Intermediate)

## Delegating Larger Tickets

-->

As the size and complexity of your pull requests grow beyond just a few files, handling them in a single pass becomes challenging. Yet, mastering how to delegate medium-to-large tasks (typically 1-6 hours of work) is where autonomous agents give the highest ROI. Rather than saving just a few minutes, you can reclaim hours of productivity. Smaller tasks might work effortlessly, but stretching the capabilities of agents to handle larger tasks brings the biggest returns.

### Automate your first drafts

## devin-coding-agents-101#009

For substantial tasks, using an autonomous agent to create an initial draft of your PR can kickstart progress and dramatically cut down your workload. Success here depends on clearly communicating your desired approach upfront. Think of yourself as the architect guiding junior developers. Clear, detailed instructions help avoid spending unnecessary time correcting fundamental misunderstandings in the agent's code.

Domain 
 Drafting 
 Refining

Journalism 
 Journalist collects initial information, writes first draft of article 
 The editor reviews drafts, fact checks, polishes, and finalizes for publication.

Restaurant 
 Line cooks prep ingredients and make preliminary dishes. 
 The sous chef adds seasonings and adjusts the dish to taste better, before it is sent to diners.

Coding 
 Autonomous agents get started on tasks based on initial plans and creating first draft solutions 
 Human developer reviews the draft PRs, gives feedback, and adds manual refinements before merging

## devin-coding-agents-101#010

🛑 Remember, large tasks aren't completely hands-free (yet). Expect multiple feedback cycles for more challenging assignments, and anticipate some manual refinements for polish. A realistic goal is around 80% time savings, not complete automation, with your expertise remaining vital for verification and final quality assurance.

### Co-develop a PRD

For tasks that are complex or vaguely defined, collaborating with your autonomous agent to create a detailed plan can be highly effective. It's perfectly okay if you initially don't know every nuance or requirement. Start by prompting your agent to explore discovery questions, like "How does our authentication system function?" or "Which services might be impacted?" You can also ask the agent to identify specific relevant code targets for you to confirm early on.

Certain agents, such as Devin and Claude Code, offer dedicated planning modes that focus on reading and exploring existing code rather than immediately modifying it. If you'd prefer deeper preparation before delegating a task, specialized codebase search tools like deepwiki.com and Devin Search can quickly provide insights into your codebase, helping streamline the process.

## devin-coding-agents-101#011

### Set checkpoints

For multi-part tasks, especially those involving multiple codebases, establish clear checkpoints along the way:

Plan → Implement chunk → Test → Fix → Checkpoint review → Next chunk

Explicitly request pauses after each significant phase, particularly for complex features built across multiple layers (e.g., database, backend, frontend). Use these checkpoints to ensure implementation aligns with your expectations, clarify doubts (ex. "Explain the auth process and confirm its security"), and correct course early to avoid cascading issues.

#### Example:

"I want you to implement this feature that will span our database, backend, and multiple frontend interfaces. Please first plan out the database schema changes needed, and let me know when that is done so I can apply the migration." -> "Now please implement the backend changes and add tests to make sure XYZ works. Let me know when that is done" -> "Now implement the changes in both our web and mobile interfaces to call the new backend endpoint"

### Teach it to verify its own work

## devin-coding-agents-101#012

When giving feedback, go beyond simply pointing out issues ("This function isn't working"). Clearly articulate your testing process to enable the agent to independently verify future tasks. For testing patterns you'll frequently repeat, integrate these into your agent's permanent knowledge base (See Add to your agent's knowledge base ).

#### Example:

In Devin, we actively prompt users to save essential testing procedures to the agent's ongoing memory, streamlining future interactions.

### Increase test coverage in AI hot spots

Currently, agents aren't fully capable of interactively testing all scenarios thoroughly. Enhancing test coverage in areas heavily modified by AI ensures greater confidence in the agent's output. Solid tests mean that code that appears correct can be confidently merged without worry.

#### Example:

Our team strengthened unit tests in a critical section of our codebase before entrusting our AI to translate the implementation from Python to C.

(Advanced)

## Automating Workflows

Agents can respond to incoming events much faster than humans, and they're a lot more willing to do boring, repetitive work, than their human counterparts.

## devin-coding-agents-101#013

### Create Shortcuts for Your Most Repetitive Work

Engineering teams frequently encounter repetitive, routine tasks. These are perfect candidates for automation with agents. Common examples include:

feature flag removal

dependency upgrades

fixing and adding tests on new feature PRs

To set this up efficiently, an experienced engineer typically creates a robust, reusable prompt template [2] In Devin, these are called playbooks that can run repeatedly for these scenarios.

#### Example:

One of our customers automatically triggers three agents dedicated to writing unit tests whenever new features are developed.

### Intelligent Code Review & Enforcement

While specialized tools for fast code review exist [3] Such as Greptile and CodeRabbit , autonomous agents can be an interesting option to deliver more accurate insights, particularly if they've already indexed the functionality of your repositories.

#### Example:

At Cognition, we like to maintain a list of the most common mistakes engineers make and we commit this list to the codebase. Then, instead of writing classical lint rules to catch these (which is often not possible), we have an agent run on every new PRs to check for these mistakes.

## devin-coding-agents-101#014

### Hook into incidents and alerts

You can also set up autonomous agents to trigger automatically in response to specific events. For example, Devin provides an accessible API, and other agents can be integrated into custom workflows via CLI commands. These setups work especially well alongside MCPs to ingest third-party error logs.

⚠️When it comes to triaging issues in production services, AI's debugging skills are not that great. Instead of asking the AI to fix bugs end-to-end as they come up, it is often more practical to ask the AI to just flag the most suspicious errors, changes, etc.

(Advanced)

## Customization & Improving Performance

### Environment Setup

Nothing slows down an agent faster than an incomplete or mismatched environment. To keep things running smoothly, align your agent's setup exactly with your team's. This includes language versions, package dependencies, and automated checks. For example, pre-commit should be installed in the agent's environment and environment configurations (secrets, language versions, virtual environments, browser logins) should be sourced automatically using tools like .envrc or custom configuration of .bashrc

#### Example:

## devin-coding-agents-101#015

We set up our agent's browser with pre-authenticated logins, removing the hassle of manual authentication and making testing much easier.

### Build Custom CLI Tools and MCPs

MCPs are widely available and are quick to set up and experiment with connecting your agent to external tools [4] In Devin, MCPs are still in beta as we're figuring out the best way to support them. Please contact us for access! . But many people overlook setting up simple CLI scripts for your agents. As a simple example, you could give your agent a script to pull information about a linear ticket given a ticket ID. You might also want to give your agent a tool to perform common parts of a workflow reliably, such as a script for restarting the local development environment.

#### Example:

We have a customer who has had a lot of success with creating a CLI tool that surfaces only the first failing test in a test suite. The CLI prompts the agent to focus on only that test with detailed error information, and this CLI leads the agent to have higher success and faster completion rates on long tasks.

### Add to your agent's knowledge base

## devin-coding-agents-101#016

If your agent makes some common mistakes, it's a great time to codify your feedback in the agent's knowledge base. In Devin, there is a dedicated knowledge management system. Many products offer .rules files, .md files for the agent to permanently ingest. Don't just give it guidelines on the framework you're using, but also tell it about the overall architecture of your project. Tell it what type of testing is common for different kinds of tasks, how to run important commands and which tools you recommend using.

#### Example:

We give our agent knowledge about the specific procedure it should follow when adding a new service route. The information includes every place it needs to add boilerplate in the frontend and backend. As a result, these tasks are now easily delegated to our AI.

Practical Considerations

## Limitations of Autonomous Agents

### Limited debugging skills

## devin-coding-agents-101#017

Bugs reports can be deceptively simple. But many bugs often require not only access to databases and logs, but also a level of debugging that is greater than most AI agents today. If using AI to aid in debugging, we recommend asking for a list of probable root causes rather than trying to debug and fix everything itself. Then, a human can decide based on their own experience which one is the real root cause. But once the cause is known, agents can still be quite helpful at implementing the fix.

### Poor fine-grained visual reasoning

Generally models today don't have great visual reasoning capabilities at the level of details needed to match screenshots of designs or Figma mockups. They are most reliable on visuals that can be described at the level of code (ex. giving it code from Figma). If you want it to match your visual style, you should use a good design system with reusable components.

### Knowledge Cutoffs

## devin-coding-agents-101#018

Whenever you want to work with a new library, you should explicitly point it to the latest docs. Otherwise, most agents will assume the old patterns from these libraries due to knowledge cutoffs in the pretrained base models. A good agent can overcome this if you point it to docs, but you must be mindful of this (remember, the agent doesn't even know that there are new versions of these libraries).

Practical Considerations

## Managing Time and Minimizing Losses

Not all times you use an agent will result in success. In 2025, there is some real variance in the outcomes of these agents. Part of the job involves learning how to use agents in such a way to maximize the chance of running into successful outcomes while minimizing wasted time and tokens.

### Be willing to cut your losses earlier
