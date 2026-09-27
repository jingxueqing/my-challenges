# 待译批次 01

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## index#001

Offline Cache — This is a locally saved version of themodernsoftware.dev captured on April 2, 2026.
 Article pages are saved in the pages/ folder. PDF documents are in the pdfs/ folder.
 Video links (YouTube) and Google Slides remain as external links.

## Course Description

In the last few years, large language models have introduced a revolutionary new paradigm in software development. The traditional software development lifecycle is being transformed by AI automation at every stage, raising the question: how should the next generation of software engineers leverage these advances to 10x their productivity and prepare for their careers?

This course demonstrates that modern AI tooling will not only enhance developer productivity but also democratize software engineering for a broader audience. We'll show that software development has evolved from 0-1 code creation to an iterative workflow of plan, generate with AI, modify, and repeat. Students will master both the theory behind traditional software engineering challenges and the cutting-edge AI-powered tools solving them today.

## index#002

Through hands-on engineering tasks and talks from industry pioneers building these revolutionary tools, you'll gain practical experience with AI-assisted development, automated testing, intelligent documentation, and security vulnerability detection. By the end of this course, you'll have a crisp understanding of how to integrate state-of-the-art LLM models into complex development workflows and avoid common pitfalls.

### Units

3 units

### Prerequisites

CS111 equivalent programming experience. CS221/229 recommended.

### Format

Weekly lectures, hands-on coding sessions, and guest speakers from industry. Final project showcasing modern development practices.

### Goals

Master modern development tools, understand AI-assisted coding, learn automated testing and deployment, explore emerging software trends.

### Classroom

420-041

### Office Hours

Mihail Eric: Friday 12:00–12:30 PM

Febie Lin: Wednesday 9:00–11:00 AM (Huang Basement)

### Assignment Deadlines

Calendar (Google Sheets)

## Team

Mihail Eric

Instructor

Febie Lin

TA

Brent Ju

TA

## Course Schedule

Week 1: Introduction to Coding LLMs and AI Development

#### Topics

Course logistics

What is an LLM actually

How to prompt effectively

#### Reading

Deep Dive into LLMs

## index#003

Prompt Engineering Overview

Prompt Engineering Guide

AI Prompt Engineering: A Deep Dive

How OpenAI Uses Codex

#### Assignment

LLM Prompting Playground

#### Lectures

Mon 9/22: Introduction and how an LLM is made — Slides

Fri 9/26: Power prompting for LLMs — Slides

Week 2: The Anatomy of Coding Agents

#### Topics

Tool use and function calling

MCP (Model Context Protocol)

#### Reading

MCP Introduction

Sample MCP Server Implementations

MCP Server Authentication

MCP Server SDK

MCP Registry

MCP Food-for-Thought

#### Assignment

First Steps in the AI IDE

#### Lectures

Mon 9/29: Building a coding agent from scratch — Slides , Completed Exercise

Fri 10/3: Building a custom MCP server — Slides , Completed Exercise

Week 3: The AI IDE

#### Topics

Context management and code understanding

PRDs for agents

IDE integrations and extensions

#### Reading

Specs Are the New Source Code

How Long Contexts Fail

Devin: Coding Agents 101

Getting AI to Work In Complex Codebases

How FAANG Vibe Codes

Writing Effective Tools for Agents

#### Assignment

Build a Custom MCP Server

#### Lectures

Mon 10/6: The AI IDE deep dive — Slides

Fri 10/10: Guest: Silas Alberti ( Cognition ) — Slides

Resources: Design Doc Template

Week 4: Claude Code and Agentic Coding

## index#004

#### Topics

Claude Code architecture and internals

Agentic coding workflows

Context engineering for agents

#### Reading

How Anthropic Uses Claude Code

Claude Best Practices

Awesome Claude Agents

Super Claude

Good Context Good Code

Peeking Under the Hood of Claude Code

#### Assignment

Coding with Claude Code

#### Lectures

Mon 10/13: Claude Code deep dive — Slides

Fri 10/17: Guest: Boris Cherney ( Claude Code ) — Slides

Week 5: Warp and the AI Terminal

#### Topics

AI-native terminal development

Agentic development workflows

#### Reading

Warp vs Claude Code

How Warp Uses Warp to Build Warp

Warp University

#### Assignment

Agentic Development with Warp

#### Lectures

Mon 10/20: Warp and the AI terminal — Slides

Fri 10/24: Guest: Zach Lloyd ( Warp ) — Slides (Figma)

Week 6: AI Security and Vulnerability Detection

#### Topics

Security testing (SAST vs DAST)

Prompt injection attacks

AI-assisted vulnerability detection

OWASP Top 10

#### Reading

SAST vs DAST

Copilot Remote Code Execution via Prompt Injection

Finding Vulnerabilities in Modern Web Apps Using Claude Code and OpenAI Codex

Agentic AI Threats: Identity Spoofing and Impersonation Risks

OWASP Top Ten: The Leading Web Application Security Risks

## index#005

Context Rot: Understanding Degradation in AI Context Windows

Vulnerability Prompt Analysis with O3

#### Assignment

Writing Secure AI Code

#### Lectures

Mon 10/27: AI security deep dive — Slides

Fri 10/31: Guest: Isaac Evans ( Semgrep )

Week 7: AI-Powered Code Review

#### Topics

Code review best practices

AI-assisted code review

Automated review tooling

#### Reading

Code Reviews: Just Do It

How to Review Code Effectively

AI-Assisted Assessment of Coding Practices in Modern Code Review

AI Code Review Implementation Best Practices

Code Review Essentials for Software Teams

Lessons from Millions of AI Code Reviews

#### Assignment

Code Review Reps

#### Lectures

Mon 11/3: AI code review deep dive — Slides

Fri 11/7: Guest: Tomas Reimers ( Graphite ) — Slides

Week 8: Full-Stack AI Development and Deployment

#### Topics

Multi-stack web application development

AI-assisted deployment pipelines

#### Assignment

Multi-stack Web App Builds

#### Lectures

Mon 11/10: Full-stack AI development — Slides

Fri 11/14: Guest: Gaspar Garcia ( Vercel ) — Slides

Week 9: SRE, Observability, and Agentic On-Call

#### Topics

Site Reliability Engineering fundamentals

Observability and monitoring

AI agents in on-call engineering

Multi-agent systems

## index#006

#### Reading

Introduction to Site Reliability Engineering

Observability Basics You Should Know

Kubernetes Troubleshooting with AI

Your New Autonomous Teammate / Benefits of Agentic AI in On-call Engineering

Role of Multi Agent Systems in Making Software Engineers AI-native

#### Lectures

Mon 11/17: SRE and AI observability — Slides

Fri 11/21: Guests: Mayank Agarwal & Milind Ganjoo ( Resolve ) — Slides

Week 10: The Future of AI in Software Engineering

#### Topics

Future trends in AI-assisted development

Industry perspectives and career implications

Final project presentations

#### Lectures

Mon 12/1: Guest: Martin Casado ( a16z )

Fri 12/5: Final project presentations

## Frequently Asked Questions

### Who is this course for?

This course is designed for students with programming experience (CS111 equivalent) who want to learn how to leverage modern AI tools to dramatically improve their software development productivity. CS221/229 is recommended but not required.

### What will I build in this course?

## index#007

Students will complete weekly hands-on assignments covering LLM prompting, MCP server development, AI IDE usage, Claude Code workflows, security analysis, code review automation, and full-stack web applications. The course culminates in a final project showcasing modern development practices.

### What tools will we use?

The course covers a range of AI development tools including Claude Code, Warp terminal, Cursor/Windsurf IDEs, Semgrep, Graphite, and Vercel. We'll also work with the Model Context Protocol (MCP) and various LLM APIs.

### How are grades determined?

Grades are based on weekly assignments, participation in class discussions, and the final project. See the assignment calendar for specific deadlines.

### Are lectures recorded?

Please check with the course staff for recording availability. Slides for each lecture are linked in the syllabus above.

### How do I contact the teaching team?

Mihail Eric: Office hours Friday 12:00–12:30 PM

Febie Lin: Office hours Wednesday 9:00–11:00 AM (Huang Basement)

Brent Ju: See course Slack/Ed for contact info.

## agentic-ai-threats#001

Threat Research Center 
 Threat Research 
 Malware

Malware

# AI Agents Are Here. So Are the Threats.

21 min read

Related Products Prisma SASE Secure Access Service Edge (SASE) Unit 42 AI Security Assessment Unit 42 Incident Response

By: Jay Chen 
 Royce Lu

Published: May 1, 2025

Categories: Malware 
 Threat Research

Tags: Agentic AI 
 AI 
 BOLA 
 GenAI 
 Prompt injection

Share

## Executive Summary

Agentic applications are programs that leverage AI agents — software designed to autonomously collect data and take actions toward specific objectives — to drive their functionality. As AI agents are becoming more widely adopted in real-world applications, understanding their security implications is critical. This article investigates ways attackers can target agentic applications, presenting nine concrete attack scenarios that result in outcomes such as information leakage, credential theft, tool exploitation and remote code execution.

## agentic-ai-threats#002

To assess how widely applicable these risks are, we implemented two functionally identical applications using different open-source agent frameworks — CrewAI and AutoGen — and executed the same attacks on both. Our findings show that most vulnerabilities and attack vectors are largely framework-agnostic, arising from insecure design patterns, misconfigurations and unsafe tool integrations, rather than flaws in the frameworks themselves.

We also propose defense strategies for each attack scenario, analyzing their effectiveness and limitations. To support reproducibility and further research, we’ve open-sourced the source code and datasets on GitHub .

### Key Findings

Prompt injection is not always necessary to compromise an AI agent. Poorly scoped or unsecured prompts can be exploited without explicit injections.

Mitigation : Enforce safeguards in agent instructions to explicitly block out-of-scope requests and extraction of instruction or tool schema.

Prompt injection remains one of the most potent and versatile attack vectors , capable of leaking data, misusing tools or subverting agent behavior.

## agentic-ai-threats#003

Mitigation : Deploy content filters to detect and block prompt injection attempts at runtime.

Misconfigured or vulnerable tools significantly increase the attack surface and impact.

Mitigation : Sanitize all tool inputs, apply strict access controls and perform routine security testing, such as with Static Application Security Testing (SAST), Dynamic Application Security Testing (DAST) or Software Composition Analysis (SCA).

Unsecured code interpreters expose agents to arbitrary code execution and unauthorized access to host resources and networks.

Mitigation : Enforce strong sandboxing with network restrictions, syscall filtering and least-privilege container configurations.

Credential leakage , such as exposed service tokens or secrets, can lead to impersonation, privilege escalation or infrastructure compromise.

Mitigation : Use a data loss prevention (DLP) solution, audit logs and secret management services to protect sensitive information.

No single mitigation is sufficient . A layered, defense-in-depth strategy is necessary to effectively reduce risk in agentic applications.

## agentic-ai-threats#004

Mitigation : Combine multiple safeguards across agents, tools, prompts and runtime environments to build resilient defenses.

It is important to emphasize that neither CrewAI nor AutoGen are inherently vulnerable. The attack scenarios in this study highlight systemic risks rooted in language models’ limitation in resisting prompt injection and misconfigurations or vulnerabilities in the integrated tool — not in any specific framework. Therefore, our findings and recommended mitigations are broadly applicable across agentic applications, regardless of the underlying frameworks.

Palo Alto Networks redefines AI security with Prisma AIRS (AI Runtime Security) — delivering real-time protection for your AI applications, models, data, and agents. By intelligently analyzing network traffic and application behavior, Prisma AIRS proactively detects and prevents sophisticated threats like prompt injection, denial-of-service attacks, and data exfiltration. With seamless, inline enforcement at both the network and API levels.

## agentic-ai-threats#005

Meanwhile, AI Access Security offers deep visibility and precise control over third-party generative AI (GenAI) use. This helps prevent shadow AI risks, data leakage and malicious content in AI outputs through policy enforcement and user activity monitoring. Together, these solutions provide a layered defense that safeguards both the operational integrity of AI systems and the secure use of external AI tools.

A Unit 42 AI Security Assessment can help you proactively identify the threats most likely to target your AI environment.

If you think you might have been compromised or have an urgent matter, contact the Unit 42 Incident Response team .

Related Unit 42 Topics 
 GenAI , Prompt Injection

## An Overview of the AI Agent

An AI agent is a software program designed to autonomously collect data from its environment, process information and take actions to achieve specific objectives without direct human intervention. These agents are typically powered by AI models — most notably large language models (LLMs) — which serve as their core reasoning engines.

## agentic-ai-threats#006

A defining feature of AI agents is their ability to connect AI models to external functions or tools, allowing them to autonomously decide which tools to use in pursuit of their objectives. A function or tool is an external capability — like an API, database or service — that the agent can call to perform specific tasks beyond the model's built-in knowledge. This integration enables them to reason through given tasks, plan solutions and execute actions effectively to achieve their goals. In more complex scenarios, multiple AI agents can collaborate as a team — each handling different aspects of a problem — to solve larger and more intricate challenges collectively. ​

AI agents have diverse applications across various sectors. In customer service, they power chatbots and virtual assistants to handle inquiries efficiently. In finance, they assist with fraud detection and portfolio management. Healthcare can also utilize AI agents for patient monitoring and diagnostic support.

## agentic-ai-threats#007

Figure 1 is a typical AI Agent architecture that shows how an agent uses an LLM to plan, reason and act through an execution loop. It connects to external tools via function calling to perform tasks such as accessing code, data or human input.

Figure 1. AI agent architecture. 
 The agent could also incorporate memory — both short- and long-term — to retain context and enhance decision-making. Applications interact with the agent by sending requests and receiving results through input and output interfaces, typically exposed as APIs.

## Security Risks of AI Agents

As AI agents are typically built on LLMs, they inherit many of the security risks outlined in the OWASP Top 10 for LLMs , such as prompt injection, sensitive data leakage and supply chain vulnerabilities. However, AI agents go beyond traditional LLM applications by integrating external tools that are often built in various programming languages and frameworks.

## agentic-ai-threats#008

Including these external tools exposes the LLMs to classic software threats like SQL injection, remote code execution and broken access control. This expanded attack surface, combined with the agent’s ability to interact with external systems or even the physical world, makes securing AI agents particularly critical.

The recently published article OWASP Agentic AI Threats and Mitigation highlights these emerging threats. Below is a summary of key threats relevant to the attack scenarios demonstrated in the next section:

Prompt injection: Attackers sneak in hidden or misleading instructions to a GenAI system, attempting to cause the application to deviate from its intended behavior. This can cause the agent to behave in unexpected ways, like ignoring given rules and policies, revealing sensitive information or using tools to take unintended actions.

Tool misuse: Attackers manipulate the agent — often through deceptive prompts — to abuse its integrated tools. This can involve triggering unintended actions or exploiting vulnerabilities within the tools, potentially resulting in harmful or unauthorized execution.

## agentic-ai-threats#009

Intent breaking and goal manipulation : Attackers target an AI agent’s ability to plan and pursue objectives by subtly altering its perceived goals or reasoning process. Attackers exploit these vulnerabilities to redirect the agent’s actions away from its original intent. A common tactic includes agent hijacking, where adversarial inputs distort the agent’s understanding and decision-making.

Identity spoofing and impersonation : Attackers exploit weak or compromised authentication to pose as legitimate AI agents or users. A major risk is the theft of agent credentials, which can allow attackers to access tools, data or systems under a false identity.

Unexpected RCE and code attacks : Attackers exploit the AI agent’s ability to execute code. By injecting malicious code, they can gain unauthorized access to elements of the execution environment, like the internal network and host file system. This poses serious risks, especially when agents have access to sensitive data or privileged tools.
