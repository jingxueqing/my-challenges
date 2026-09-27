# 待译批次 11

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## devin-coding-agents-101#019

A common mistake for people who are new to using agents is that they commit to making an interaction successful, even when an agent's work is veering off track. If you ever find yourself thinking "it's ignoring my instructions" or "this thing is going in circles", you should be ok discontinuing that conversation or manually taking over. Sending more messages is more likely a sign of the inherent complexity of your task being higher than the agent's capabilities rather than some simple mistake that can be corrected.

### Diversifying your experiments

If you're new to working with agents, we recommend diversifying your bets at the start. Try a range of different prompts and ideas. Double down on the types of tasks you see the agents naturally performing well on - and cut your losses on the ones they don't. Don't feel a need to force your agents to find success every time.

### Start fresh when you aren't making progress

## devin-coding-agents-101#020

Starting over is the right answer a lot more often with agents than with humans. If you've given an agent a task and it is struggling to address feedback or correct course, starting fresh with a new agent and all of the instructions up front can often get to success much faster. The ability of an agent to correct a messed-up environment is much worse than its ability to spit out fresh code from scratch.

Practical Considerations

## Security and Permissioning

### Create accounts for your agent

A throwaway email is helpful for safe testing of sites. Create custom IAM roles for your agent if it needs to access cloud resources.

### Give it a development / staging environment

Ideally the agent uses the same testing setup as the engineers on your team. We suggest avoiding giving access to production services entirely. When using remote agents, you can run fully isolated test environments on the agent's remote machine.

### Readonly API keys

Where possible, give it readonly access. We find it is still helpful for humans to manually run any script that interacts with outside services.

Practical Considerations

## Big Changes Ahead

## devin-coding-agents-101#021

We firmly believe that software engineers aren't going anywhere. Even as coding agents become smarter and more capable, deep technical expertise and intimate knowledge of your codebase remain invaluable. True ownership of your projects, your systems, and your code is more critical now than ever. On our team today, engineers are expected to oversee multiple systems while still maintaining deep understanding and thoughtful judgment. As automation amplifies your impact, the ability to juggle parallel tasks won't just become possible; It'll become essential. We're excited to share the insights we've gathered while preparing our own organization for this shift, so you and your team can also thrive in the evolving world of software development.

## finding-vulnerabilities-claude-codex#001

TL;DR: We evaluated how effective AI Coding Agents are at finding vulnerabilities in real code.
 How : we tasked Anthropic's Claude Code (v1.0.32, Sonnet 4) and OpenAI Codex (v0.2.0, o4-mini) with finding vulnerabilities in 11 popular and large open-source Python web applications. Together they produced over 400 security findings our security research team reviewed.

AI Coding Agents Find Real Vulnerabilities : Claude Code found 46 vulnerabilities (14% true positive rate – TPR, 86% false positive rate – FPR) and Codex reported 21 vulnerabilities (18% TPR, 82% FPR). About 20 of these are high severity vulnerabilities.

AI Grasps Context, Chokes on Flows : Claude Code was best at finding Insecure Direct Object Reference (IDOR) bugs with a 22% (13 correct issues/59 reported) true positive rate (TPR), but struggled at performing taint tracking across multiple files and functions, with a 5% (2/38) TPR for SQL Injection and a 16% (12/74) TPR for XSS.

OpenAI Codex struggled to report any correct IDOR 0% (0/5) TPR, did very poorly at SQL injection 0% (0/5) and XSS 0% (0/28) but surprisingly reported more correct Path Traversal issues than Claude Code 47% (8/17) TPR.

## finding-vulnerabilities-claude-codex#002

Non-Determinism is a Real Struggle : Running the exact same prompt on the exact same codebase multiple times often yielded vastly different results. In one application, three identical runs produced 3, 6, and then 11 distinct findings.

Key take-aways :
 AI Coding Agents with relatively simple security-focused prompts can already find real vulnerabilities in real applications .

BUT: depending on the vulnerability class, the results may be quite noisy (high false positive rate), especially on traditional injection-style vulnerability classes like SQL injection, XSS, and SSRF.

Detailed evaluations and benchmarking are key for understanding how effective an approach is for finding vulnerabilities (this has always been true, but even more so now with non deterministic tools like LLMs), and to know when your improvements are headed in the right direction.

This is our first post of a series on using and augmenting AI for finding vulnerabilities !

In this post we'll cover:
 The problems with usual SAST benchmarks and how it affects AI SAST evaluation

Some open research questions about AI-based vulnerability hunting

Our AI Coding Agents experiment, dataset, and what we learned

## finding-vulnerabilities-claude-codex#003

How Anthropic's /security-review command is pretty mid

The non-determinism of AI Coding Agents, and why it happens

This post was last edited on Sept 3, 2025, 11:15am UTC 
 Sept 3, 2025, 11:15am UTC: Added details about models used and commands to call them

## Introduction
 Here at Semgrep, we live and breathe application security (AppSec). We've been productionizing AI for a long time in our products ( tech behind Assistant , promptfoo for testing our AI workflows , using security researcher triage to evaluate auto triage performance ), constantly researching the best combination of traditional, deterministic analysis and the contextual power of modern AI without chasing trends.
 This research is part of that ongoing mission. We're embarking on a deep, public exploration to answer a question that's on everyone's mind: how effective are LLMs really at finding vulnerabilities in source code?

## finding-vulnerabilities-claude-codex#004

## Open Research Questions about AI-based Vulnerability Hunting
 To guide our investigation, we broke down the broad question of "Are LLMs good at finding bugs?" into more specific, measurable sub-questions.
 What are the false positive and false negative rates for LLM-based vulnerability finding? Does it vary by programming language, framework, code base size, or vulnerability class? What are the sensibilities to how code is written?

What are the common reasons for false positives and false negatives?

How deterministic is the analysis? Do you get the same results every time?

For injection vulnerabilities specifically, we wanted to know:
 How effective is the LLM at tracking user input between a source (e.g., a user supplied value) and a sink (e.g., a method that consumes a raw SQL query)?

Can it track data across functions and files?

Can it reason about sanitization functions and other security controls?

Can it reason about functions from third-party open source dependencies?

## finding-vulnerabilities-claude-codex#005

## The Problem with Usual SAST Benchmarks: Lack of Realism
 Before diving into our findings, let's talk about how we measure AI performance. Much of the current research/claims relies on benchmarks that, while valuable, don't fully capture the complexity of real-world code.
 Apps with known vulnerabilities : These benchmarks only use open-source applications with known vulnerabilities; many can be found in vulnerable-apps thanks to Kinnaird McQuade . If you read this blog, you may recognize some of the names WebGoat , JuiceShop , OWASP Benchmark , etc. But, there's a problem with these, current LLMs have likely ingested the code for these repositories as well as many public write-ups on the Internet, giving them pre-existing knowledge and skewing the results. 
Their code is often not realistic with an abundance of comments, annotations, and variable names that hint at or directly describe where the vulnerabilities are in the code or how to exploit them. Sometimes, tools results are even checked in the repo .

from javaspringvulny's SearchService.java 
 from juiceshop, the challenge is part of the file name …

## finding-vulnerabilities-claude-codex#006

XBOW provides benchmarks for auto pentesting tools, but not adapted to static analysis: the code is often too contrived and simplistic and doesn't represent real application. ZeroPath did a good job when they sanitized them , but only a fraction were sanitized. Moreover, each of these test cases are tiny applications, designed to stimulate a dedicated attack scenario. If we focus on Python benchmarks, XBOW has 45 of them; 45 different tiny applications with an average of less than 98 lines of code and 3 Python files . This is too small to capture the complexity of searching and reasoning across an entire code base or many functions.

CVE Memorization Bias: As LLMs are trained on a massive corpus of public data from the internet, including the very codebases where CVEs were found and fixed. This creates a fundamental data contamination problem. The AI may not be detecting a vulnerability through novel analysis but simply recognizing a pattern it memorized during training.

## finding-vulnerabilities-claude-codex#007

More recently academics have designed benchmarks such as CyberGym , Eyeballvul , or SecVulEval . These show a great improvement and are closer to real-world examples but they lack the focus on modern web apps or isolate vulnerabilities from the broader application context.
 EyeballVul: A more recent benchmark from Timothée Chauvin that extracts real-world, human-vetted vulnerabilities from open-source projects and presents them as minimal, reproducible test cases. While based on real code, it still isolates the vulnerability from the broader application context, making the search problem easier.

SecVulEval and CyberGym: These suites are designed to evaluate vulnerabilities in C or C++. While valuable in their domain, their focus on C and C++ means these data are not applicable to the Python/JavaScript and other web-centric languages that dominate modern cloud-native development.

## finding-vulnerabilities-claude-codex#008

While each of these approaches are useful and should be used at times, they don't necessarily reflect the reality of modern software development. Real-world applications are not clean, isolated functions. They are complex webs of dependencies, frameworks, and business logic.
 Our approach is different. We tested on 11 large, Python based, actively maintained open-source projects, written in common web frameworks (Django, Flask, FastAPI) . Our method is complementary to the previous ones, and we believe it's unique in that it a) aims to be representative of AI-driven vulnerability finding in the real world (vs. small, isolated synthetic examples), b) is not contaminated by model training data, and c) represents the types of applications most developers and companies are actually building – web applications using modern languages and frameworks.

## Scope for this Blog Post
 To make this tractable, we focused on:
 Using 1 run of Anthropic Claude Code (v1.0.32, Sonnet 4) and OpenAI Codex (v0.2.0, o4-mini) out of the box with a simple, scripted prompt [1] reused for the different kinds of vulnerabilities. We asked them to return SARIF formatted security issues.

## finding-vulnerabilities-claude-codex#009

Analyzing 11 different large-ish, real-world open source Python projects .

Focusing on common, high-impact vulnerability classes: Auth Bypass, IDOR , Path Traversal, SQL Injection, SSRF, and XSS.

Exploratory results with Anthropic's recent /security-review command

Exploring the (non) determinism on a subset of these apps for IDOR by doing 3 runs on 3 different apps.

## finding-vulnerabilities-claude-codex#010

To ground our research, we selected popular and actively maintained projects. Here's a look at the scale of the applications we analyzed. Note that we are not releasing the names of these popular open-source web apps today, since we are still in the process of responsible disclosure , we will release the dataset once the process has concluded.
 App ID 
 Commits 
as of Aug, 2025
 Github Stars 
 Python files 
 Python lines of code 
 No blank. No comment.
 
 PY-APP-001 
 >25k
 5k
 >500
 85k
 
 PY-APP-002 
 >5k
 6k
 >500
 60k
 
 PY-APP-003 
 >15k
 10k
 >200
 45k
 
 PY-APP-004 
 >5k
 >100
 >500
 95k
 
 PY-APP-005 
 >15k
 1k
 >500
 100k
 
 PY-APP-006 
 >25k
 2k
 >1000
 110k
 
 PY-APP-007 
 >5k
 20k
 >1000
 250k
 
 PY-APP-008 
 >1k
 >100
 >200
 40k
 
 PY-APP-009 
 1k
 3k
 >50
 2k
 
 PY-APP-010 
 15k
 5k
 >200
 45k
 
 PY-APP-011 
 >5k
 >25k
 >200
 30k

7k files
 >800kLOC
 
 Application names will be released when all vulnerabilities are disclosed and handled.

## The Experiment: AI vs. Real-World Apps Code
 We ran our analysis across the 11 applications and then triaged every one of the 445 findings manually, validating most of them (especially IDOR or Auth bypass) dynamically .

## finding-vulnerabilities-claude-codex#011

#### Anthropic Claude Code (v1.0.32, Sonnet 4)
 Vulnerability Class 
 True Positives 
 False Positives 
 True Positive Rate 
 
 Auth bypass
 6 
 52
 10% (6/58)
 
 IDOR 
 13 
 46 
 22% (13/59) 
 
 Path traversal
 5 
 31
 13% (5/36)
 
 SQL Injection 
 2 
 36 
 5% (2/38) 
 
 SSRF
 8
 57
 12% (8/65)
 
 XSS 
 12 
 62 
 16% (12/74) 
 
 Using the following command:
 claude --verbose 
 --print 
 --output-format json 
 --dangerously-skip-permissions 
 <PROMPT>

#### OpenAI Codex (v0.2.0, o4-mini/high reasoning)
 Vulnerability Class 
 True Positives 
 False Positives 
 True Positive Rate 
 
 Auth bypass
 5
 32
 13% (5/37)
 
 IDOR 
 0 
 5 
 0% (0/5) 
 
 Path traversal 
 8 
 9 
 47% (8/17) 
 
 SQL Injection
 0
 5
 0% (0/5)
 
 SSRF 
 8 
 15 
 34% (8/23) 
 
 XSS
 0
 28
 0% (0/28)
 
 Using the following command:
 codex --config disable_response_storage=true
 --config model_reasoning_effort=high
 --config model_reasoning_summary=detailed
 exec
 --model o4-mini
 --full-auto
 --skip-git-repo-check
 <PROMPT>

## finding-vulnerabilities-claude-codex#012

### What we Found
 Both Claude Code and Codex are useful today: they find real security vulnerabilities, but they're very noisy. The overall noise is still very high, but they found real security vulnerabilities in these popular open source Python web applications. Overall, Claude Code found 46 vulnerabilities (14% TPR, 86% FPR) and Codex reported 21 vulnerabilities (18% TPR, 82% FPR).

Many IDOR bugs looked correct at first and Claude Code suggested credible fixes: The LLM could not only find these bugs but also suggest credible fixes, like injecting new permission checks based on existing patterns in the code. IDOR issues can be hard to triage and we had to test most of them to be certain, which brought the true positive rate much lower.

Claude Code as a good secure guardrails tool? Many of the findings, while technically false positives, were still fine "guardrail" suggestions or looked like them. For instance, the model would often suggest parameterizing a SQL query that was already safe. While not a vulnerability, this strengthens the code. We still considered these to be false positives, though not as severe as others.

## finding-vulnerabilities-claude-codex#013

However, these code hardening recommendations can't always be trusted. We found several instances, especially in client-side JavaScript code, where the AI tries to fix what it perceives as an issue around DOM manipulation, but in fact, it breaks the code (double escaping the HTML in the cases we observed), despite there being no security issue there in the first place.

XSS and SQL Injection – hard to piece components together: The model struggles to trace data from a server-side framework to a client-side component (a common pattern for XSS) or through complex application layers. It often got confused by statically defined data or failed to recognize server-side sanitization.

Repeating the prompt helped with getting more results: The probabilistic nature of LLMs means that asking the same question in a slightly different way can yield new findings, highlighting the inconsistency of the analysis. Repeating the same prompt multiple times on the same code base gave us different answers, but it eventually circled back to the same findings.
