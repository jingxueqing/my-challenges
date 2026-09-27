# 待译批次 12

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## finding-vulnerabilities-claude-codex#014

OpenAI Codex sometimes failed to report valid SARIF . 9 reports over the 66 we expected were not valid SARIF. We considered all findings reported in those files, but they weren't valid SARIF or JSON. Claude Code didn't have this problem in any of the cases we tried.

## finding-vulnerabilities-claude-codex#015

## Same Code, Same AI, Different Bugs Every Time: AI Coding Agents' Non-Determinism Problem 
 To explore how non-determinism manifested in practice, we selected three of these applications and ran the same prompt multiple times with the same prompt, targeting the same security issue: IDOR. A pattern emerged: the AI's findings were different every single time we ran the test .
 In the context of vulnerability detection this is a major issue. First, as a security engineer, ideally we want stronger guarantees that our code was scanned for important vulnerability classes than "I hope the model searched thoroughly this time."
 Second, intermittently detecting vulnerabilities can cause inconsistencies and noise in your security tools or vulnerability management systems. For example, if you're using a SAST platform, ASPM, or something you've built internally, oftentimes those systems assume that when a previously detected vulnerability is no longer present, then it has been fixed. But that may not be the case with LLM-driven detection, as a single scan might miss it, and thus a "new" finding will be created when a subsequent scan re-finds the same issue, leading to duplicate JIRA tickets and developer frustration.
 Here are some specific examples we observed:
 PY-APP-007 : In the first run, the AI identified a "missing search authorization" vulnerability that was absent from the other two runs. The second run flagged issues that were unique to that run. The third run, in turn, found its own distinct set of vulnerabilities.

## finding-vulnerabilities-claude-codex#016

PY-APP-006 : Similar story: the first run unearthed a vulnerability in the user API, while the subsequent runs focused on different parts of the codebase, such as the event abstracts and notes modules.

PY-APP-002 : The variability here was perhaps the most pronounced. The number of identified vulnerabilities jumped from 3 in the first run to 6 in the second, and then 11. Each run presented different findings that only partially overlapped.

## finding-vulnerabilities-claude-codex#017

So, what's behind this? We believe the key factors are what's known as context rot and compaction . When an AI agent is tasked with analyzing an entire codebase, it's dealing with a massive amount of information: context rot leads to the inability to retrieve accurately from its own context. To manage this, LLMs use a form of lossy compression (sometimes called compaction), which means that some of the finer reasoning details like function names, paths, etc. can get lost in the summarization process.
 Think of it like trying to summarize a long, complex novel. You'll capture the main plot points, but you're bound to miss some of the subtleties and nuances. In the same way, the AI might lose track of a specific architectural pattern or a subtle data flow, leading it to miss a vulnerability in one run that it might catch in another. We saw a clear example of this in PY-APP-006, where one of the AI's proposed fixes was incomplete because it failed to reuse an existing base class for user authorization — a crucial piece of context that was seemingly lost in that particular run.
 This non-determinism has significant implications for how we approach AI native SAST. On one hand, the ability of the AI to "think" differently each time means it can explore a wider range of potential attack vectors, much like a team of human penetration testers with diverse perspectives. On the other hand, it introduces a level of uncertainty that can lead to confusion or mis-behaviors.
 Incomplete Coverage : A single run might provide a false sense of security, as it could miss critical vulnerabilities that might be caught in a subsequent run.

## finding-vulnerabilities-claude-codex#018

Lack of Repeatability : The inability to reproduce results makes it difficult to verify the AI's findings and to trust its output in a consistent, repeatable manner.

Increased Cost and Time : The need to run multiple audits to get a more complete picture can significantly increase the time and computational resources required. Note : with traditional software, once you've written it, you can run it again basically "for free" (excluding hardware costs, electricity, etc.) This is not the case for LLM-heavy tooling, where in this case reading in a code base and reasoning about it could result in tens to hundreds of dollars in token costs per scan . This cost may decrease over time for today's models, but newer models may be more expensive.

## finding-vulnerabilities-claude-codex#019

## How Effective is Claude Code's New /security-review Command?
 Anthropic released a new command for Claude Code, called /security-review . It's designed to be run on a pull request to examine the changed files and ask questions to identify specific security issues. You can find the prompt here .
 When running this command on the entire codebase, we found that the security issues identified were fairly limited. Many times, it couldn't find security issues that we were getting when we prompted Claude Code to search for one specific kind of security issue at a time.
 We ran this command on PY-APP-003, PY-APP-002, and PY-APP-008, and it only found one XSS across all of them, which is very different from the results we got in the overall experiment.

## finding-vulnerabilities-claude-codex#020

## Answering Our Questions
 Let's revisit our initial research questions based on what we've learned.
 What are the FP/FN rates? For raw AI on real-world code, the false positive rate is very high, ranging from at best 53% for Path Traversal for Codex or 78% for IDOR for Claude Code to at worst 95% with SQL injection for Claude Code and 100% for SQL injection or IDOR for Codex. The performance varies dramatically by application too, from 100% (10/10) real IDOR in PY-APP-002 (Claude Code) to 0% (0/7) for PY-APP-007. Across all apps and all reported issues, Claude Code found 46 vulnerabilities (14% TPR, 86% FPR) and Codex reported 21 vulnerabilities (18% TPR, 82% FPR).

Since we've been using real applications, we can't accurately measure false negatives in this experiment. We'll cover techniques for measuring false negative rates in an upcoming blog post!

## finding-vulnerabilities-claude-codex#021

Why does it fail? The primary weakness we observed is a lack of deep, semantic understanding of code execution for injection issues. Models struggle with inter-procedural taint flow and implicit flows, the things traditional SAST engines are usually built for. Some of the limitations are also coming from context compaction and context rot. We will continue to explore these limitations in more detail and explore solutions to mitigate them.

How important are scaffolding and agentic workflows? They are not just important; they are becoming essential . The future of AI in security review is not a single, monolithic model but a system of AI agents (including coding agents like in our cases) that can use tools, reason about evidence, and collaborate to find and validate vulnerabilities.

## finding-vulnerabilities-claude-codex#022

While we don't (yet) have data here on the difference between using an agent with access to Claude Code versus more typical context engineering (that is, building the scaffolding to provide all of the relevant code) with reasoning model, we observed a huge difference in the system's ability to work through a complex process and make educated decisions on the way to reporting security issues. That being said, a counterexample of this is how Sean Heelan was able to do enough context engineering to get a reasoning model to report a vulnerability (8% of the time). We really suggest you read his blog post .

How about the cost in all of this? Unfortunately, we haven't been able to track uniformly the cost between Claude Code and Codex. The overall cost of Claude Code was $114 , for all these vulnerabilities and all these apps (except running for non-determinism and for /security-review command).

## finding-vulnerabilities-claude-codex#023

## Dataset: Future Release
 We are not releasing a dataset today nor the names of the open source applications analyzed because we're in the process of responsible disclosure, reaching out to the application developers to get all the security issues fixed and validated. Once that's done, we'll be comfortable releasing the data.

## Conclusion
 LLMs are not a silver bullet that will replace human security engineers tomorrow, in fact they are pretty weak on finding high-severity injection-style vulnerabilities end to end. However, they are an incredibly powerful tool. Our research indicates that by understanding their strengths (contextual reasoning) and weaknesses (deep semantics of the code), and by building sophisticated agentic systems around them using advanced static analysis engines, we can create a new generation of security tooling that is far more powerful than anything that has come before.
 [1] Scripted simple prompt for Claude Code and Codex
 BATCH_PROMPT_TEMPLATE = """
I am a core developer of this app. It's been reported to me that 
there are several {vuln_type} vulnerabilities in the code base. I need 
your expertise to find all of them!

## finding-vulnerabilities-claude-codex#024

# Instructions
- Find all {vuln_type} vulnerabilities in my code, don't worry about 
 third-party code.
- Explain why they are real security vulnerabilities I should care about; give 
 code snippets from the code to support your analysis (trace from entry points); 
 maybe some clue on how to trigger the issue for testing.
- Report all {vuln_type} vulnerabilities using the SARIF JSON format that you will 
 write within the <SARIF_OUTPUT>...</SARIF_OUTPUT> tag; make sure it's valid JSON.
- Fix these security issues in the code.

Don't ask for confirmation, just do it.
"""

## good-context-good-code#001

Powered by Ghost 
 
 | 
 Enter access code 
 | 
 Site owner login

## how-long-contexts-fail#001

Jun 22, 2025

AGENTS

LLM

AI

PROMPTING

CONTEXT MANAGEMENT

# How Long Contexts Fail

### Managing Your Context is the Key to Successful Agents

As frontier model context windows continue to grow 1 , with many supporting up to 1 million tokens, I see many excited discussions about how long context windows will unlock the agents of our dreams. After all, with a large enough window, you can simply throw everything into a prompt you might need – tools, documents, instructions, and more – and let the model take care of the rest.

Long contexts kneecapped RAG enthusiasm (no need to find the best doc when you can fit it all in the prompt!), enabled MCP hype (connect to every tool and models can do any job!), and fueled enthusiasm for agents 2 .

But in reality, longer contexts do not generate better responses. Overloading your context can cause your agents and applications to fail in suprising ways. Contexts can become poisoned, distracting, confusing, or conflicting. This is especially problematic for agents, which rely on context to gather information, synthesize findings, and coordinate actions.

## how-long-contexts-fail#002

Let’s run through the ways contexts can get out of hand, then review methods to mitigate or entirely avoid context fails.

## Context Fails

Context Poisoning: When a hallucination makes it into the context

Context Distraction: When the context overwhelms the training

Context Confusion: When superfluous context influences the response

Context Clash: When parts of the context disagree

### Context Poisoning

Context Poisoning is when a hallucination or other error makes it into the context, where it is repeatedly referenced.

The Deep Mind team called out context poisoning in the Gemini 2.5 technical report , which we broke down last week . When playing Pokémon, the Gemini agent would occasionally hallucinate while playing, poisoning its context:

An especially egregious form of this issue can take place with “context poisoning” – where many parts of the context (goals, summary) are “poisoned” with misinformation about the game state, which can often take a very long time to undo. As a result, the model can become fixated on achieving impossible or irrelevant goals.

## how-long-contexts-fail#003

If the “goals” section of its context was poisoned, the agent would develop nonsensical strategies and repeat behaviors in pursuit of a goal that cannot be met.

### Context Distraction

Context Distraction is when a context grows so long that the model over-focuses on the context, neglecting what it learned during training.

As context grows during an agentic workflow—as the model gathers more information and builds up history—this accumulated context can become distracting rather than helpful. The Pokémon-playing Gemini agent demonstrated this problem clearly:

While Gemini 2.5 Pro supports 1M+ token context, making effective use of it for agents presents
a new research frontier. In this agentic setup, it was observed that as the context grew significantly beyond 100k tokens, the agent showed a tendency toward favoring repeating actions from its vast history rather than synthesizing novel plans. This phenomenon, albeit anecdotal, highlights an important distinction between long-context for retrieval and long-context for multi-step, generative reasoning.

## how-long-contexts-fail#004

Instead of using its training to develop new strategies, the agent became fixated on repeating past actions from its extensive context history.

For smaller models, the distraction ceiling is much lower. A Databricks study found that model correctness began to fall around 32k for Llama 3.1 405b and earlier for smaller models.

If models start to misbehave long before their context windows are filled, what’s the point of super large context windows? In a nutshell: summarization 3 and fact retrieval. If you’re not doing either of those, be wary of your chosen model’s distraction ceiling.

### Context Confusion

Context Confusion is when superfluous content in the context is used by the model to generate a low-quality response.

For a minute there, it really seemed like everyone was going to ship an MCP . The dream of a powerful model, connected to all your services and stuff , doing all your mundane tasks felt within reach. Just throw all the tool descriptions into the prompt and hit go. Claude’s system prompt showed us the way, as it’s mostly tool definitions or instructions for using tools.
