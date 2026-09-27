# 待译批次 04

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## agentic-ai-threats#042

Most agent frameworks rely on container-based sandboxes to isolate execution environments. However, default configurations are often not sufficient. To prevent sandbox escape or misuse, apply stricter runtime controls:

Restrict container networking : Allow only necessary outbound domains. Block access to internal services (e.g., metadata endpoints and private addresses).

Limit mounted volumes : Avoid mounting broad or persistent paths (e.g., ./, /home ). Use tmpfs to store temporary data in-memory

Drop unnecessary Linux capabilities : Remove privileged permissions like CAP_NET_RAW , CAP_SYS_MODULE and CAP_SYS_ADMIN

Block risky system calls : Disable syscalls like kexec_load , mount , unmount , iopl and bpf

Enforce resource quotas : Apply CPU and memory limits to prevent denial of service (DoS), runaway code or cryptojacking

## Conclusion

## agentic-ai-threats#043

Agentic applications inherit the vulnerabilities of both LLMs and external tools while expanding the attack surface through complex workflows, autonomous decision-making and dynamic tool invocation. This amplifies the potential impact of compromises, which can escalate from information leakage and unauthorized access to remote code execution and full infrastructure takeover. As our simulated attacks demonstrate, a wide variety of prompt payloads can trigger the same weakness, underscoring how flexible and evasive these threats can be.

Securing AI agents requires more than ad hoc fixes. It demands a defense-in-depth strategy that spans prompt hardening, input validation, secure tool integration and robust runtime monitoring.

General-purpose security mechanisms alone are insufficient. Organizations must adopt purpose-built solutions — such as Palo Alto Networks Prisma AIRS — to Discover, Assess and Protect threats unique to agentic applications.

Palo Alto Networks customers are better protected from the threats discussed above through the following products:

A Unit 42 AI Security Assessment can help you proactively identify the threats most likely to target your AI environment.

## agentic-ai-threats#044

If you think you may have been compromised or have an urgent matter, get in touch with the Unit 42 Incident Response team or call:

North America: Toll Free: +1 (866) 486-4842 (866.4.UNIT42)

UK: +44.20.3743.3660

Europe and Middle East: +31.20.299.3130

Asia: +65.6983.8730

Japan: +81.50.1790.0200

Australia: +61.2.4062.7950

India: 00080005045107

Palo Alto Networks has shared these findings with our fellow Cyber Threat Alliance (CTA) members. CTA members use this intelligence to rapidly deploy protections to their customers and to systematically disrupt malicious cyber actors. Learn more about the Cyber Threat Alliance .

## Additional Resources

Stock Advisory Assistant – GitHub

CrewAI – CrewAI Documentation

CrewAI – CrewAI GitHub Repository

SerperDevTool – CrewAI GitHub Repository

ScrapeWebsiteTool – CrewAI GitHub Repository

Hierarchical Process – CrewAI Documentation

AutoGen – AutoGen Documentation

AutoGen – AutoGen GitHub Repository

Swarm – AutoGen Documentation

About VM metadata – Google Cloud Documentation

OWASP Top 10 for LLMs – OWASP

OWASP Agentic AI Threats and Mitigation – OWASP

Nasdaq – Nasdaq

Updated May 2, 2025, at 2:20 p.m. PT to update product language.

## agentic-ai-threats#045

Updated 2 May, 2025 at 2:39 PM PDT -->
 Back to top

### Tags
 Agentic AI 
 AI 
 BOLA 
 GenAI 
 Prompt injection

Threat Research Center

Next: Gremlin Stealer: New Stealer on Sale in Underground Forum

### Table of Contents

### Related Articles

Double Agents: Exposing Security Blind Spots in GCP Vertex AI

Threat Brief: March 2026 Escalation of Cyber Risk Related to Iran (Updated March 26)

Who’s Really Shopping? Retail Fraud in the Age of Agentic AI

## Related Malware Resources

High Profile Threats April 1, 2026

#### Threat Brief: Widespread Impact of the Axios Supply Chain Attack

API attacks

JavaScript

Supply chain

Read now

High Profile Threats March 31, 2026

#### Weaponizing the Protectors: TeamPCP’s Multi-Stage Supply Chain Attack on Security Infrastructure

CVE-2025-55182

GitHub

Infostealer

Read now

Threat Research March 31, 2026

#### Double Agents: Exposing Security Blind Spots in GCP Vertex AI

Agentic AI

Data exfiltration

GCP

Read now

High Profile Threats March 26, 2026

#### Threat Brief: March 2026 Escalation of Cyber Risk Related to Iran (Updated March 26)

APK

DDoS attacks

GenAI

Read now

Threat Actor Groups March 26, 2026

## agentic-ai-threats#046

#### Converging Interests: Analysis of Threat Clusters Targeting a Southeast Asian Government

CL-STA-1048

CL-STA-1049

Stately Taurus

Read now

Threat Research March 24, 2026

#### Threat Brief: Recruiting Scheme Impersonating Palo Alto Networks Talent Acquisition Team

Email scam

Lure

Phishing

Read now

Threat Research March 19, 2026

#### Analyzing the Current State of AI Use in Malware

.NET

ChatGPT

GenAI

Read now

Threat Research March 17, 2026

#### Open, Closed and Broken: Prompt Fuzzing Finds LLMs Still Fragile Across Open and Closed Models

Evasion

GenAI

LLM

Read now

Threat Research March 12, 2026

#### Suspected China-Based Espionage Operation Against Military Targets in Southeast Asia

Advanced Persistent Threat

AppleChris

Backdoor

Read now

Threat Research March 10, 2026

#### Auditing the Gatekeepers: Fuzzing "AI Judges" to Bypass Security Controls

AI

Fuzzing

LLM

Read now

## ai-code-review-best-practices#001

Index
 
 Series

Merge queues What is a merge queue 
 Defining merge skew

Guides by topic

graphite 
 stacked diffs 
 code review 
 Developer productivity 
 github 
 git 
 AI 
 CI-CD 
 software development 
 monorepo 
 version control 
 quality assurance 
 merging 
 security 
 code quality 
 programming 
 tools 
 sapling 
 phabricator 
 VS Code 
 pull requests 
 analytics 
 agile development 
 typescript 
 bug tracking 
 gerrit 
 GitHub Actions 
 GitHub Copilot 
 repo configuration 
 automation 
 Monorepos 
 merge queue

# AI code review implementation and best practices
 Greg Foster
 Graphite software engineer

Try Graphite 
 
 As artificial intelligence becomes increasingly integrated into software development workflows, AI code review has emerged as a useful tool for improving code quality and developer productivity. This technical guide explores the implementation of AI code review systems and outlines best practices for effectively leveraging these tools in your development process.

## ai-code-review-best-practices#002

# Table of contents 
 Understanding AI code review 
 Benefits of AI code review 
 Implementing AI Code Review 
 Best practices for AI code review 
 Popular AI code review tools 
 Measuring success 
 Common challenges and solutions 
 Conclusion 
 Frequently asked questions 
 As artificial intelligence becomes increasingly integrated into software development workflows, AI code review has emerged as a powerful tool for improving code quality and developer productivity. This technical guide explores the implementation of AI code review systems and outlines best practices for effectively leveraging these tools in your development process.
 AI code review tools like Graphite Agent are transforming how teams approach code quality assurance, enabling faster iteration cycles while maintaining high standards. This guide will help you understand how to implement and optimize AI code review in your organization.

## ai-code-review-best-practices#003

### Understanding AI code review 
 AI code review refers to the use of machine learning and natural language processing technologies to automatically analyze code for issues including:
 Bugs and potential runtime errors
 Security vulnerabilities
 Performance inefficiencies
 Style inconsistencies
 Architecture and design flaws
 Unlike traditional static analyzers, modern AI code review tools can understand code context, suggest improvements, and even generate fixes automatically.

### Benefits of AI code review 
 Increased efficiency - Automation reduces review time and catches issues early
 Consistency - AI applies the same standards across all code reviews
 Knowledge sharing - Developers learn best practices through AI suggestions
 Reduced cognitive load - AI handles routine checks, letting humans focus on complex logic
 Continuous improvement - AI systems improve over time with more data

### Implementing AI Code Review

## ai-code-review-best-practices#004

#### Step 1: Choose the Right Tool 
 Several AI code review tools are available, with varying capabilities:
 Graphite Agent : Offers immediate, actionable feedback via contextual code analysis with PR automation
 GitHub Copilot : Provides real-time suggestions while coding to provide cleaner code for reviews
 SonarQube with AI : Combines traditional static analysis with AI capabilities
 DeepCode : Focuses on detecting security vulnerabilities
 When selecting an AI code review tool, it's important to consider:
 Language and framework support
 Integration with existing workflows
 Customization options
 Privacy and security requirements

#### Step 2: Integration into development workflow 
 For effective AI code review implementation:
 Configure repository hooks 
 Set up webhooks or integrations to trigger reviews automatically on pull requests
 
 Define review policies 
 Create configuration files specifying severity levels and focus areas
 Set up ignore patterns for generated code
 Configure team-specific rules
 
 Train developers 
 Introduce teams to AI review capabilities and limitations
 Establish guidelines for interpreting and acting on AI suggestions

## ai-code-review-best-practices#005

#### Step 3: Customization and fine tuning 
 Most AI code review tools allow customization, including:
 Rule sensitivity : Adjust thresholds for different types of issues
 Domain-specific patterns : Define custom rules for your codebase
 Integration depth : Configure how deeply the AI integrates with your workflow

### Best practices for AI code review

#### 1. Establish clear expectations 
 Define what the AI should and shouldn't review:
 DO : use AI for style consistency, basic logic errors, and security scanning
 DON'T : rely solely on AI for architectural decisions or complex business logic
 DO : establish clear acceptance criteria for automated reviews

#### 2. Human-in-the-loop approach 
 The most effective AI code review implementations maintain human oversight:
 Use AI as a first pass to catch obvious issues
 Have human reviewers validate AI suggestions
 Track which AI suggestions are accepted vs. rejected to improve the system

## ai-code-review-best-practices#006

#### 3. Focus on actionable feedback 
 Train developers to analyze AI suggestions critically. For example, encourage your team to:
 Prioritize high-impact issues first.
 Understand the reasoning behind suggestions.
 Challenge suggestions that don't make sense in context.
 Document recurring false positives.
 Example of evaluating AI feedback :
 AI Suggestion Evaluation Action 
 "Replace synchronous file operations with async versions" Valid performance concern Accept and implement 
 "Add null check for parameter" Unnecessary - checked by TypeScript Decline with explanation 
 "Use more descriptive variable name" Subjective but helpful Accept and implement 
 "Restructure entire class hierarchy" Too broad for automated suggestion Discuss in team meeting

#### 4. Continuous learning 
 Implement feedback loops to improve both AI and human performance, which could include:
 Tracking which AI suggestions developers accept vs. reject.
 Periodically reviewing false positives and false negatives.
 Updating review configurations based on findings.
 Sharing insights across teams.

## ai-code-review-best-practices#007

#### 5. Security-first mindset 
 When reviewing AI code suggestions, always prioritize security:
 Verify AI suggestions don't introduce new vulnerabilities
 Be especially cautious with AI-generated code that handles: User input
 Authentication
 Database queries
 File operations
 Network requests

### 6. Performance optimization 
 Train the AI review process to identify performance concerns, such as:
 Look for N+1 query patterns
 Check for unnecessary recomputation
 Identify inefficient data structures
 Flag unoptimized resource usage
 A human reviewer should then evaluate:
 Is the list comprehension actually more efficient in this case?
 Does it improve readability?
 Is the operation suited for a different data structure altogether?
 Graphite Agent automatically identifies performance bottlenecks in your PRs, helping you catch inefficiencies before they reach production. Its contextual analysis understands your entire codebase to provide actionable performance recommendations.

### Popular AI code review tools

## ai-code-review-best-practices#008

#### Graphite Graphite Agent 
 Graphite Agent tool stands out for its deep integration with development workflows and contextual understanding of code. Key features include:
 Contextual code understanding across entire repositories
 Automatic PR summaries and descriptions
 Intelligent code suggestions that respect project patterns
 Deep integration with GitHub
 ![screenshot of Graphite Agent comment](/images/content/guides/ai-code-review-implementation-best-practices/Graphite Agent-comment.png)
 Graphite Agent excels at understanding not just isolated code snippets but entire codebases, making its suggestions more relevant and aligned with project standards.

### Other notable tools 
 DeepCode : Strong in security vulnerability detection
 Codacy : Combines traditional analysis with AI capabilities
 SonarQube AI : Enterprise-grade code quality platform

## ai-code-review-best-practices#009

### Measuring success 
 To evaluate the effectiveness of your AI code review implementation, you can pay attention to these metrics:
 Quality metrics 
 Reduction in production bugs
 Reduction in security incidents
 Improved code coverage
 
 Process metrics 
 Time to complete reviews
 Number of review cycles needed
 Developer satisfaction scores
 
 ROI metrics 
 Development time saved
 Reduction in technical debt
 Customer satisfaction improvements

## ai-code-review-best-practices#010

### Common challenges and solutions 
 Challenge Solution 
 False positives overwhelming developers Tune sensitivity settings and implement feedback loops 
 Team resistance to AI review Start with opt-in approach and demonstrate value gradually 
 AI missing context-specific issues Supplement with human reviews and custom rules 
 Too many low-value suggestions Configure priority levels and focus on high-impact areas 
 Dependency on AI slowing skill development Use AI suggestions as teaching opportunities 
 Graphite Agent is designed to address many of these common challenges out of the box. With intelligent filtering, contextual understanding, and seamless GitHub integration, it helps teams avoid false positive fatigue while maintaining high code quality standards.

## ai-code-review-best-practices#011

### Conclusion 
 AI code review tools like Graphite Agent are transforming development practices by providing faster, more consistent analysis while reducing the burden on human reviewers. By implementing the best practices outlined in this guide and approaching AI code review as a complement to human expertise rather than a replacement, teams can significantly improve code quality, security, and developer productivity.
 Remember that AI code review is most effective when it's part of a comprehensive quality strategy that includes testing, documentation, and thoughtful human oversight. The goal is not to eliminate human judgment but to enhance it by automating routine checks and providing valuable insights.

### Frequently asked questions

#### How accurate are AI code review tools? 
 AI code review tools typically achieve 70-90% accuracy for common issues like syntax errors, style violations, and basic security vulnerabilities. However, accuracy varies significantly based on the complexity of the issue and the specific tool. For architectural decisions and complex business logic, human review remains essential.
