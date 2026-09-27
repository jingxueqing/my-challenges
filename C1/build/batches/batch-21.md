# 待译批次 21

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## sast-vs-dast#009

Supports various types of software, including web applications, web services, and thick clients.

Supports web applications and web services but does not typically support other software types.

Stage in SDLC

Performed early in the software development life cycle.

Conducted later in the SDLC, often during or after deployment.

Vulnerabilities detected

Identifies coding flaws, such as: SQL injection, cross-site scripting (XSS), buffer overflows, etc.

Detects runtime issues, such as server configuration errors, denial-of-service vulnerabilities, and application-level flaws.

Cost of fixing vulnerabilities

Less expensive since issues are identified early in the SDLC.

More expensive as vulnerabilities are found later, often requiring emergency fixes in order to deploy on time.

Runtime and environment issues

Cannot detect runtime-specific or environment-related vulnerabilities.

Can identify vulnerabilities that appear only during runtime or due to environmental factors.

Depth vs. breadth

Provides deep insights into code-level vulnerabilities.

Offers a broad view of the application's external security risks.

Integration with tools

Integrates with IDEs and CI/CD pipelines for automated static analysis.

## sast-vs-dast#010

Integrates with CI/CD pipelines for continuous runtime testing.

False positives and negatives

Higher chance of false positives due to in-depth code analysis.

Lower false positives but higher risk of false negatives due to limited internal visibility.

Technology dependency

Relies on programming languages and frameworks; requires compatibility with the tool.

Independent of application frameworks as they interact with the application externally.

## Pros and cons of SAST and DAST

### Pros of SAST

Identifies security vulnerabilities early in the software development life cycle.

Analyzes the codebase, including basic functions and complex branches.

Operates directly on the source code without requiring the application to run.

Provides real-time feedback with comprehensive insights, such as the exact location of vulnerabilities.

Generates exportable reports that can be tracked using dashboards.

Supports automation so that it is faster and more efficient than manual code reviews.

### Cons of SAST

Often generates a large number of false positives. Therefore, it may require manual reviews.

Cannot identify runtime or environment-specific vulnerabilities, such as configuration errors.

## sast-vs-dast#011

Requires tools specific to each programming language so that maintenance is complex.

Struggles with understanding external libraries, APIs, and REST endpoints.

### Pros of DAST

Identifies vulnerabilities that only appear during application execution.

Operates externally and no access to source code is required. This is effective for testing third-party applications or compiled code.

Simulates actual attack scenarios and identifies risks missed by SAST.

Works independently of the application's programming language.

Evaluates the entire application and system. This includes memory consumption, resource usage, and third-party interfaces.

### Cons of DAST

Focus only on the outer layers of the application, which may miss vulnerabilities in deeper layers.

Applied later in the SDLC so that fixes are more expensive and time-consuming.

Miss certain vulnerabilities that SAST tools can identify through source code analysis. As an example, consider a web application that uses an insecure random number generator (e.g., Math.random() in JavaScript) to create session tokens. DAST may miss this flaw because it only tests runtime behavior. (But SAST can detect it.)

## sast-vs-dast#012

Require custom infrastructure for large projects and multiple instances of the application to run in parallel and therefore resource intensive.

## When should I use SAST vs. DAST?

SAST and DAST play complementary roles in securing SDLC. Understanding when to use each helps to have comprehensive security coverage.

### When to use SAST

During early development phases. Developers use SAST to identify vulnerabilities like SQL injection and hardcoded credentials early in the SDLC. By catching these issues before deployment, they reduce the cost and complexity of fixing them.

Eg:- A SAST tool scans Python code and flags a vulnerability where hardcoded API keys are embedded in the source code. Developers refactor the code to use environment variables to securely store and retrieve the keys.

For code reviews. SAST integrates into version control systems. Allows developers to scan their code before committing it. This makes sure that only secure code enters the repository.

## sast-vs-dast#013

Example: A SAST tool can detect a vulnerability where a file path is constructed directly from user input without validation, exposing the application to path traversal attacks. Developers fix the issue by sanitizing the input and using secure library functions to handle file paths.

In continuous integration/continuous deployment pipelines. SAST runs automated scans during the CI/CD process. It offers real-time feedback to developers.

### When to use DAST

Pre-production testing. Developers use DAST to identify runtime vulnerabilities (eg:- insecure configurations, authentication flaws, insufficient access controls) in a staging or QA environment.

Example: A DAST tool can detect a database misconfiguration that exposes sensitive data. Then developers can secure the configuration before deployment.

In post-deployment monitoring. DAST tools continue to scan deployed applications for vulnerabilities caused by changes in the environment or emerging threats. This guarantees that the application remains secure over time.

Testing third-party integrations. DAST can mimic an external attacker's perspective to identify vulnerabilities in third-party APIs or interconnected systems.

## sast-vs-dast#014

For example: A DAST tool tests a web application and discovers a vulnerability in a third-party payment API where credit card details are being transmitted over an unencrypted HTTP connection. Developers resolve the issue by enforcing HTTPS for all API communications.

## Which is more effective: SAST or DAST?

The effectiveness of SAST or DAST depends on:

The SDLC stage

The type of vulnerabilities being addressed

SAST works best in early development, primarily to identify vulnerabilities in the source code, reduce costs, and promote secure coding practices. In contrast, DAST focuses on runtime vulnerabilities in pre-production or deployed applications. It offers insights into issues like misconfigurations and insecure integrations.

### Take a hybrid approach

## sast-vs-dast#015

Instead of choosing one over the other, combining SAST and DAST creates a multi-layered security strategy that addresses vulnerabilities in both static code and runtime environments . SAST can be integrated into early development stages to detect and fix code-level issues before the application is compiled. Once the application is running in a test environment, DAST can identify runtime vulnerabilities and evaluate the application’s behavior under attack conditions.

Automating both SAST and DAST scans within a CI/CD pipeline provides continuous feedback and accelerates the development process without compromising security.

For agile or DevOps environments, adding tools like IAST or RASP can further enhance security. By correlating results from both SAST and DAST, organizations can achieve more comprehensive and effective vulnerability management .

### Use RASP as an alternative to SAST and DAST

Runtime Application Self-Protection (RASP) is an advanced security solution installed directly on the server where the application runs.

RASP embeds itself into the application's runtime environment. This integration allows RASP to analyze the app's logic and data. While analyzing, it can:

## sast-vs-dast#016

Detect abnormal behaviors as they happen.

Block malicious activities instantly.

A key difference is that RASP doesn't just alert on potential issues — it actively prevents attacks by isolating and resolving threats without relying on external tools.

RASP offers a dynamic alternative to SAST and DAST. Unlike SAST, which analyzes static code, and DAST, which simulates external attacks, RASP operates in real time. It monitors the application’s behavior during execution and responds to live threats by terminating sessions or alerting defenders.

RASP is particularly effective in protecting applications against vulnerabilities that bypass network defenses or are missed during development.

However, overconfidence in RASP can lead organizations to neglect secure coding practices. Also, RASP may impact application performance because it operates directly within the application's runtime environment. RASP cannot replace the need to fix underlying flaws, but it provides continuous protection while remediation is underway.

As one RASP user comments:

“The decision to use a RASP tool should be based on a thorough assessment of the application's specific requirements and risk profile.”

## sast-vs-dast#017

## The future is AppSec testing with SAST, DAST, and RASP

The future of application testing lies in combining SAST, DAST, and RASP to create a comprehensive security strategy. As security challenges grow, integrating these tools into CI/CD pipelines and automating their processes will become essential.

Advances in AI and machine learning will make testing more efficient as it helps to reduce false positives and improve threat detection.

### Financial and FinServ industries

In the financial sector, AI-powered tools will transform how vulnerabilities are detected and mitigated. SAST and DAST will continue to identify coding flaws and runtime issues during development and pre-production.

But you won’t stop there: RASP will take it further by using AI to monitor live transactions . For instance, RASP could detect unusual patterns (Eg:- an attacker attempts to exploit a vulnerability in real time) and block these activities while notifying the security team.

### IoT, edge, and connected devices

When it comes to IoT, the combination of these tools will play an important role in securing connected devices. Here’s how:

## sast-vs-dast#018

SAST can confirm that the firmware is free from vulnerabilities during development.

DAST can test the security of communication protocols between devices.

RASP, meanwhile, monitors deployed devices and detects and prevents unauthorized access attempts or data leaks caused by emerging threats.

Likewise, using multiple methods will help IoT ecosystems remain resilient. As explained in our many examples, SAST, DAST, and RASP together promise a future where applications are built and deployed with stronger, more proactive security measures.

## Resilient security starts with proactive testing

Combining SAST, DAST, and RASP together can provide robust security that covers the entire software development lifecycle.

By integrating these methods into CI/CD pipelines and using advances in AI, organizations can respond proactively to emerging threats. Together, these methods offer a holistic approach to secure modern applications from security vulnerabilities.

/en_us/blog/fragments/disclaimer-with-divider

/en_us/blog/fragments/top-50-security-threats

Style

two-column

Title

Related Articles

Filter

Category

Blog Limit

3

Category

learn

Sort Category Shuffle Order

true

### Related Articles
 
 Learn 6 Minute Read

## sast-vs-dast#019

### What Is Authorization? 
 Authorization is the process of deciding what actions, parts of a website, or application a given user can access after they have been authenticated.

Learn 4 Minute Read

### Introduction to Reinforcement Learning 
 Reinforcement learning is at the core of some of the most prominent AI breakthroughs in the last decade. Learn how it works here.

Learn 8 Minute Read

### Data Observability: The Complete Introduction 
 Get the complete story on data observability here: what itis, the 5 pillars, benefits & implementing — and best of all, ALL the things you can do with it.

/en_us/blog/fragments/about-splunk

/en_us/blog/fragments/subscribe-footer

## specs-are-the-new-source-code#001

# The spec is dead, long live the spec!

### Prototypes are the new specs and specs are the new.... source code?

Ravi Mehta and Danny Martinez 
 Jul 31, 2025

58
 
 16
 8
 
 Share

Over my career, specs have gotten shorter and shorter. When I started at Microsoft, the worth of a PM was measured in the weight of their specs. Years later, at Tripadvisor, we mythologized the PM who brought a spec—scribbled on a napkin—to Product Review. 
 Product teams often treat specifications like paperwork—a necessary evil before the "real work" of shipping. Engineers get celebrated for elegant code, designers for beautiful UX. PMs get kudos for delivering impact. But specs? They’re typically rushed through, tossed aside, forgotten. 
 Thanks for reading Ravi on Product! Subscribe for free to receive new posts and support my work.

## specs-are-the-new-source-code#002

This was always a mistake. In my Product Competency Toolkit , Feature Specification sits at the top—first among twelve competencies—for a reason. It underpins Product Execution, along with Product Delivery and Product Quality. 
 Flawless execution is the foundation of good product management, and a great spec is the starting line.
 Today, the way we build is shifting. Engineers are getting faster—much faster. AI can turn rough ideas into working code in minutes. The bottleneck is no longer building. It's knowing what to build, and aligning the team around those requirements. 
 Suddenly, the humble specification isn't ephemeral paperwork. It’s the foundation of product management—it's becoming the source code itself.

## specs-are-the-new-source-code#003

## Why PMs are suddenly the bottleneck 
 In his recent talk Building Faster with AI , Andrew Ng noted an unprecedented trend: 
 "For the first time in my life that I saw managers proposed to me having twice as many PMs as engineers. I still don't know if this proposal is a good idea, but I think it's a sign of where the world is going." —Andrew Ng
 This validates what we predicted in our previous post : as engineers deliver many times faster with AI, companies need more PMs to support those productive engineers, not fewer . 
 As product delivery accelerates, that puts intense pressure on every other aspect of product management—understanding customer needs, crafting the right features, validating impact. 
 And all of that pressure gets focused into one artifact—the spec.

## specs-are-the-new-source-code#004

## Specs—the new source code 
 In traditional software development, programmers write human readable “source code” which gets compiled into highly optimized, machine readable “object code”. The “object code” (also known as a binary) is a byproduct that can be recreated with the source code. The source code is literally the source of truth. 
 Sean Grove, from OpenAI, has a provocative thesis. In his recent talk, The New Code , he argues that a well-written prompt (i.e., the spec) is the new source code. 
 Seen in that light, we’re doing AI development backwards. We craft careful prompts to communicate our intentions to models. The AI generates code. Then we keep the code and throw away the prompt.
 "This feels like you shred the source and then you very carefully version control the binary," Grove observes.
 Think about that. In traditional programming, source code is sacred. The source contains comments, structure, and documentation—everything needed to understand and modify the system. The binary is just a downstream artifact.
 But with AI, we've flipped this relationship. We treat the generated code as the artifact worth keeping and the specification—the prompt—as disposable.
 Grove argues this gets it exactly backwards. Code, even elegant code, is what he calls a "lossy projection" from the specification. Just like decompiling a binary won't give you the original comments and variable names, reading code won't tell you the full intent behind it.
 The specification, however, contains everything. A sufficiently robust spec can generate "good TypeScript, good Rust, servers, clients, documentation, tutorials, blog posts, and even podcasts."
 “A sufficiently robust spec can generate good TypeScript, good Rust, servers, clients, documentation, tutorials, blog posts, and even podcasts.” —Sean Grove, OpenAI

## specs-are-the-new-source-code#005

More importantly, specifications do something code cannot: they align both humans and machines on shared goals. Grove puts it simply: "A written specification effectively aligns humans and is the artifact that you use to communicate and discuss and debate and refer to and synchronize on."
 He predicts: "In the near future, the person who communicates most effectively is the most valuable programmer. And literally, if you can communicate effectively, you can program."
 The new scarce skill isn't coding. It's writing specifications that fully capture intent and values.
 For product managers, this should sound familiar. It's what we've always done—just now the machines are listening too.
