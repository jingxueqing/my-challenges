# 待译批次 27

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## ai-assisted-code-review-assessment#015

## Page 8

## ai-assisted-code-review-assessment#016

Alware '24, July 15-16, 2024, Porto de Galinhas, Brazil
Manushree Vijayvergiya et al.
URL, we inspected its best practice document and determined (1) the
highlight that how automated analysis is and should be used varies
best-practice type (section 1) and (2) whether a linter that detects a
based on the programming language.
corresponding violation exists or can be easily built. Specifically,
In contrast, using machine learning for code analysis is a compar-
three authors, each with over 10 years of experience in building
atively new and less understood field. A number of recent publica-
static analysis tools, read the documentation and independently
tions (e.g., Hong et al. [11], Li et al. [16], Li et al. [17], Thongtanunam
categorized the URLs. There were no disagreements on the best-
et al. [24], Tufano et al. [25], and Tufano et al. [26]) report on model
practice type, but there were disagreements on whether a linter
evaluations and propose tools for automated code review. While
can be easily built for about 15% of URLs. The three authors re-
these models and the review comment generation task are very sim-
solved these disagreements through majority vote and discussion.
ilar to the model presented in this paper, evaluations largely focused
Disagreements stemmed from ambiguous best practices, and those
on historical datasets. As discussed in section 3.3.1 an intrinsic eval-
with multiple guidelines. For example, while checking the pres-
uation on only historical comments is somewhat limited and can
ence of code documentation is relatively straightforward, reasoning
nocking the ro
sometimes fail to predict real-world performance. Another recent
about justified exceptions and clarity of content may not.
publication by Frömmgen et al. [9] presents an evaluation of a live
Figure 6 shows the distribution of the 50 sampled URLs, broken
system, but for the opposite task: creating code from comments
down by type and whether violations can be detected by a linter.
rather than comments from code.
For 33/50 (66%) of these best practices, violation detection is beyond
the scope of traditional static analysis.
8 CONCLUSION
6 LESSONS LEARNED
Verifying that code adheres to best practices is a common task in
modern code review processes. While some best practices can be
Based on our experience developing and deploying AutoCommenter,
automatically verified with traditional tools such as linters, many
we summarize a few key lessons learned:
require the knowledge and judgement of experienced developers,
• Complementing traditional analyses: AutoCommenter's
which requires time and effort.
LLM-backed approach generates comments for 68% of best
This paper reports on our experience developing, deploying, and
practices frequently referenced by human reviewers. Many
evaluating AutoCommenter, an LLM-backed code review assistant
of these are out of scope for traditional static analyses.
system. Specifically, it lays out the entire process from task and
• Intrinsic evaluation vs. real-world performance: Intrin-
model design, over intrinsic evaluations and system calibrations,
sic evaluations and real-world performance can diverge sig-
to a staged roll out and end-user evaluation.
nificantly: our intrinsic evaluation, using a dataset of real-
The evaluation results show that it is feasible to develop an
world human comments together with a state of the art
end-to-end system with capabilities well beyond traditional tools
model architecture and training process, indicated a promis-
while achieving a high degree of end-user acceptance. These results
ing model, but our extrinsic evaluations and system improve-
are a promising first step towards the deployment of sophisticated
ments proved essential for a successful deployment.
code-review assistants and automated code reviews.
• Monitoring user acceptance is critical: Even a few nega-
Our priority was to ensure a positive developer experience by
tive user experiences can erode trust in an automated system.
designing AutoCommenter to have very high precision. While recall
Continuously monitoring and analyzing real-world feedback
was not the primary focus, we recognize its significance and plan
was crucial in detecting such instances and identifying reme-
to explore what changes in the model and system architecture can
dies. In the case of AutoCommenter, a simple suppression
improve recall. For example, the model we used in 2022 was state of
mechanism was sufficient to strongly improve user accep-
the art at the time. However, it has a limited context window of 2048
tance to over 80% without major sacrifices in efficacy.
tokens which suffices for only around 200 lines of code. Current
state of the art models have context windows of tens of thousands of
7 RELATED WORK
tokens during training and over a million tokens during inference.
Johnson [15] introduced the C linter almost 50 years ago in 1977. In
This leap opens up opportunities for new features and significant
those 50 years, a considerable body of research on automated static
improvement in existing ones.
analysis was produced: a recent literature review by Heckman and
Williams [10] identified 17,571 papers. Many studies explore how
9 ACKNOWLEDGEMENTS
developers interact with static analysis. Johnson et al. [14] explore
This work is the result of years of collaboration between teams in
challenges developers face when trying to use static analysis. The
Google Core Systems and Google DeepMind. We are grateful for the
results of their study highlights the importance of good integration
support and advice of all our team members and leadership, includ-
into existing developer workflows and the importance of develop-
ing Alberto Elizondo, Alexander Frömmgen, Ballie Sandhu, Chandu
ing and maintaining trust in the tool. Vassallo et al. [27] explore
Thekkath, Chris Gorgolewski, David Tattersall, Ilya Cherny, Jacob
how developers interact with static analysis in different contexts,
Austin, Katja Grünwedel, Kristóf Molnár, Lera Kharatyan, Luka Ri-
including coding and code review. They too find that integration
manic, Madhura Dudhgaonkar, Marc Brockschmidt, Marcus Revaj,
into existing workflows plays a major role in developers willing-
Maxim Tabachnyk, Nina Chen, Niranjan Tulpule, Nitya Ramani,
ness to use the tools and that high quality of results is extremely
Paige Bailey, Pavel Sychev, Pierre-Antoine Manzagol, Quinn Madi-
important. Beller et al. [6] studied usage of static code analysis in a
son, Roger Fleig, Satish Chandra, Savinee Dancs, Stoyan Nikolov,
large number of open source projects. Among other findings, they
Subhodeep Moitra, and Vaibhav Tulsyan.

## ai-assisted-code-review-assessment#017

## Page 9

## ai-assisted-code-review-assessment#018

Al-Assisted Assessment of Coding Practices in Modern Code Review
Alware '24, July 15-16, 2024, Porto de Galinhas, Brazil
REFERENCES
pre-training models. In Proceedings of the Joint Meeting of the European Soft-
[1] 2024. Google Style Guides. https://google.github.io/styleguide/. Accessed:
ware Engineering Conference and the Symposium on the Foundations of Software
[2] 2024. Linux kernel coding style. https://www.kernel.org/doc/html/v4.10/process/
(17) Zhiyu Li, Shuai Lu, Daya Guo, Nan Duan, Shailesh Jannu, Grant Jenks, Deep
Engineering (ESEC/FSE). 1009-1021.
coding-style.html. Accessed: 2024-03-15.
Majumder, Jared Green, Alexey Svyatkovskiy, Shengyu Fu, and Neel Sundaresan.
[3] 2024. PEP 8 - Style Guide for Python Code. https://peps.python.org/pep-0008/.
2022. Automating code review activities by large-scale pre-training. In Proceedings
of the 30th ACM Joint European Software Engineering Conference and Symposium
(4) 2024. Rust Style Guide. https://doc.rust-lang.org/nightly/style-guide/. Accessed:
on the Foundations of Software Engineering (<conf-loc>, < city>Singapore</city>,
<country ›Singapore</country>, </conf-loc>) (ESEC/FSE 2022). Association for
[5] Alberto Bacchelli and Christian Bird. 2013. Expectations, outcomes, and chal-
Computing Machinery, New York, NY, USA, 1035-1047. https://doi.org/10.1145/
lenges of modern code review. In 2013 35th International Conference on Software
16) Monite ile Sain 70l hate Shane M/1010, arE 202y Zaidan. 2016.
Goran Petrovic, Marko Ivankovic, Gordon Fraser, and René Just. 2023. Please fix
this mutant: How do developers resolve mutants surfaced during code review?. In
Analyzing the state of static analysis: A large-scale evaluation in open source soft-
International Conference on Software Engineering: Software Engineering in Practice
and Reengineering (SANER), Vol. 1. IEEE, 470-481.
ware. In 2016 IEEE 23rd International Conference on Software Analysis, Evolution,
[19] Rachel Potvin and Josh Levenberg. 2016. Why Google Stores Billions of Lines
(7] Zimin Chen, Malgorzata Salawa, Manushree Vijayvergiya, Goran Petrovic, Marko
of Code in a Single Repository. Communications of the ACM (CACM) 59 (2016),
Ivankovié, and René Just. 2023. MuRS: Mutant Ranking and Suppression using
78-87. http://dl.acm.org/citation.cfm?id=2854146
Identifier Templates. In Proceedings of the Symposium on the Foundations of
[20] Peter Rigby, Brendan Cleary, Frederic Painchaud, Margaret-Anne Storey, and
Software Engineering (FSE). 1798-1808.
Daniel German. 2012. Contemporary Peer Review in Action: Lessons from Open
[8] M. E. Fagan. 1976. Design and code inspections to reduce errors in program
Source Development. IEBE Software 29, 6 (2012), 56-61. https://doi.org/10.1109/
development. IBM Systems Journal 15, 3 (1976), 182-211. https://doi.org/10.1147/
[21] Peter C. Rigby and Christian Bird. 2013. Convergent contemporary software peer
[9] Alexander Frömmgen, Jacob Austin, Peter Choy, Nimesh Ghelani, Lera Kharatyan,
review practices. In Proceedings of the 2013 9th Joint Meeting on Foundations of
Gabriela Surita, Elena Khrapko, Pascal Lamblin, Pierre-Antoine Manzagol, Marcus
Revaj, Maxim Tabachnyk, Daniel Tarlow, Kevin Villela, Daniel Zheng, Satish
Computing Machinery, New York, NY, USA, 202-212. https://doi.org/10.1145/
Software Engineering (Saint Petersburg, Russia) (ESEC/FSE 2013). Association for
Chandra, and Petros Maniatis. 2024. Resolving Code Review Comments with
Machine Learning. In International Conference on Software Engineering: Software
Adam Roberts, Hyung Won Chung, Gaurav Mishra, Anselm Levskaya, James
Bradbury, Daniel Andor, Sharan Narang, Brian Lester, Colin Gafiney, Afroz
[10]|
Engineering in Practice (ICSE-SEIP).
Sarah Heckman and Laurie Williams. 2011. A systematic literature review of
Mohiuddin, et al. 2023. Scaling up models and data with t5x and seqio. Journal
actionable alert identification techniques for automated static code analysis.
[23] Caitlin Sadowski, Emma Söderberg, Luke Church, Michal Sipko, and Alberto
of Machine Learning Research 24, 377 (2023), 1-8.
1016/j.infsof.2010.12.007 Special section: Software Engineering track of the 24th
Information and Software Technology 53, 4 (2011), 363-387.
https://doi.org/10.
Bacchelli. 2018. Modern Code Review: A Case Study at Google. In International
Annual Symposium on Applied Computing.
Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP).
[11] Yang Hong, Chakkrit Tantithamthavorn, Patanamon Thongtanunam, and Aldeida
Aleti. 2022. Commentfinder: a simpler, faster, more accurate code review com-
[24] Patanamon Thongtanunam, Chanathip Pornprasit, and Chakkrit Tantithamtha-
ments recommendation. In Proceedings of the Joint Meeting of the European Soft-
vorn. 2022. Autotransform: Automated code transformation to support modern
code review process. In Proceedings of the International Conference on Software
Engineering (ESEC/FSE). 507-519.
ware Engineering Conference and the Symposium on the Foundations of Software
[12] Marko Ivankovic, Goran Petrovic, René Just, and Gordon Fraser. 2019. Code
[25) Rosalia Tufano, Ozren Dabié, Antonio Mastropaolo, Matteo Ciniselli, and Gabriele
Engineering (ICSE). 237-248.
Coverage at Google. In Proceedings of the Joint Meeting of the European Soft-
Bavota. 2024. Code Review Automation: Strengths and Weaknesses of the State
ware Engineering Conference and the Symposium on the Foundations of Software
[26] Rosalia Tufano, Simone Masiero, Antonio Mastropaolo, Luca Pascarella, Denys
of the Art. IEEE Transactions on Software Engineering (TSE) (2024).
[13] Marko Ivankovic, Goran Petrovic, Yana Kulizhskaya, Mateusz Lewko, Luka Kali-
Engineering (ESEC/FSE). 955-963.
Poshyvanyk, and Gabriele Bavota. 2022. Using pre-trained models to boost code
noveié, René Just, and Gordon Fraser. 2024. Productive Coverage: Improving
review automation. In Proceedings of the International Conference on Software
the Actionability of Code Coverage. In International Conference on Software
[27] Carmine Vassallo, Sebastiano Panichella, Fabio Palomba, Sebastian Proksch, Har-
Engineering (ICSE). 2291-2302.
[14] Brittany Johnson, Yoonki Song, Emerson Murphy-Hill, and Robert Bowdidge.
Engineering: Software Engineering in Practice (ICSE-SEIP).
ald C Gall, and Andy Zaidman. 2020. How developers engage with static analysis
2013. Why don't software developers use static analysis tools to find bugs?. In
tools in different contexts. Empirical Software Engineering 25 (2020), 1419-1457.
2013 35th International Conference on Software Engineering (ICSE). IEEE, 672-681.
[28] T. Winters, T. Manshreck, and H. Wright. 2020. Software Engineering at Google:
[15] Stephen C Johnson. 1977. Lint, a C program checker. Bell Telephone Laboratories
Lessons Learned from Programming Over Time. O'Reilly Media. https://books.
Murray Hill.
google.ch/books?id=TyIrywEACAAJ
[16] Lingwei Li, Li Yang, Huaxi Jiang, Jun Yan, Tiejian Luo, Zihan Hua, Geng Liang,
and Chun Zuo. 2022. Auger: Automatically generating review comments with
Received 2024-04-05; accepted 2024-05-04

## how-anthropic-uses-claude-code#001

## Page 1

ANTHROPIC
How Anthropic teams
use Claude Code
<>
Anthropic's internal teams are transforming their workflows with Claude Code, enabling
developers and non-technical staff to tackle complex projects, automate tasks, and bridge
skill gaps that previously limited their productivity.
Through interviews with our own Claude Code power users, we've gathered insights on how
different departments leverage Claude Code, its impact on their work, and tips for other
organizations considering adoption.

## Page 2

Contents
Claude Code for data infrastructure
3
Claude Code for product development
5
Claude Code for security engineering
7
Claude Code for inference
9
Claude Code for data science and visualization
11
Claude Code for API
13
Claude Code for growth marketing
15
Claude Code for product design
17
Claude Code for RL engineering
Claude Code for legal
21
HOW ANTHROPIC TEAMS USE CLAUDE CODE

## Page 3

## how-anthropic-uses-claude-code#002

Claude Code for data
infrastructure
Main Claude Code use cases
The Data Infrastructure team
organizes all business data for
Kubernetes debugging with screenshots
teams across the company. They
When Kubernetes clusters went down and weren't scheduling new pods,
use Claude Code for automating
the team used Claude Code to diagnose the issue. They fed screenshots of
routine data engineering tasks,
dashboards into Claude Code, which guided them through Google Cloud's
troubleshooting complex
UI menu by menu until they found a warning indicating pod IP address
infrastructure issues, and
creating documented workflows
exhaustion. Claude Code then provided the exact commands to create a
for technical and non-technical
new IP pool and add it to the cluster, bypassing the need to involve
team members to access and
networking specialists.
manipulate data independently.
Plain text workflows for finance team
The team showed finance team members how to write plain text files
describing their data workflows, then load them into Claude Code to get
fully automated execution. Employees with no coding experience could
describe steps like "query this dashboard, get information, run these
queries, produce Excel output," and Claude Code would execute the entire
workflow, including asking for required inputs like dates.
Codebase navigation for new hires
When new data scientists join the team, they're directed to use Claude
Code to navigate their massive codebase. Claude Code reads their
Claude.md files (documentation), identifies relevant files for specific
tasks, explains data pipeline dependencies, and helps newcomers
understand which upstream sources feed into dashboards. This replaces
traditional data catalogs and discoverability tools.
End-of-session documentation updates
The team asks Claude Code to summarize completed work sessions and
suggest improvements at the end of each task. This creates a continuous
improvement loop where Claude Code helps refine the Claude.md
documentation and workflow instructions based on actual usage, making
subsequent iterations more effective.
Parallel task management across multiple instances
When working on long-running data tasks, they open multiple instances
of Claude Code in different repositories for different projects. Each
instance maintains full context, so when they switch back after hours or
days, Claude Code remembers exactly what they were doing and where
they left off, enabling true parallel workflow management without
context loss.
CLAUDE CODE FOR DATA INFRASTRUCTURE

## how-anthropic-uses-claude-code#003

## Page 4

## how-anthropic-uses-claude-code#004

Claude Code for data
infrastructure
Team impact
Resolved infrastructure problems without specialized expertise
Resolved Kubernetes cluster issues that would normally require pulling in
systems or networking team members, using Claude Code to diagnose
problems and provide exact fixes.
Accelerated onboarding
New data analysts and team members can quickly understand complex
systems and contribute meaningfully without extensive guidance.
Enhanced support workflow
Can process much larger data volumes and identify anomalies (like
monitoring 200 dashboards) that would be impossible for humans to
review manually.
Enabled cross-team self-service
Finance teams with no coding experience can now execute complex data
workflows independently.
Top tips from the
Write detailed Claude.md files
Data Infrastructure
The better you document your workflows, tools, and expectations in
Claude.md files, the better Claude Code performs. This made Claude Code
team
excel at routine tasks like setting up new data pipelines when you have
existing patterns.
Use MCP servers instead of CLI for sensitive data
They recommend using MCP servers rather than the BigQuery CLIto
maintain better security control over what Claude Code can access,
especially for handling sensitive data that requires logging or has
potential privacy concerns.
Share team usage sessions
The team held sessions where members demonstrated their Claude Code
workflows to each other. This helped spread best practices and showed
different ways to use the tool they might not have discovered on
their own.
CLAUDE CODE FOR DATA INFRASTRUCTURE

## how-anthropic-uses-claude-code#005

## Page 5

## how-anthropic-uses-claude-code#006

Claude Code for product
development
Main Claude Code use cases
The Claude Code team uses their
own product to build updates to
Fast prototyping with auto-accept mode
Claude Code, expanding the
Engineers use Claude Code for rapid prototyping by enabling "auto-
product's enterprise capabilities
accept mode" (shift +tab) and setting up autonomous loops where Claude
and agentic loop functionalities.
writes code, runs tests, and iterates continuously. They give Claude
abstract problems they're unfamiliar with, let it work autonomously, then
review the 80% complete solution before taking over for final refinements.
Teams emphasize starting from a clean git state and committing
checkpoints regularly so they can easily revert any incorrect changes
if Claude goes off track.
Synchronous coding for core features
For more critical features touching the application's business logic, the
team works synchronously with Claude Code, giving detailed prompts
with specific implementation instructions. They monitor the process in
real-time to ensure code quality, style guide compliance, and proper
architecture while letting Claude handle the repetitive coding work.
Building Vim mode
One of their most successful async projects was implementing Vim
key bindings for Claude Code. They asked Claude to build the entire
feature (despite it not being a priority), and roughly 70% of the final
implementation came from Claude's autonomous work, requiring
only a few iterations to complete.
Test generation and bug fixes
They use Claude Code to write comprehensive tests after implementing
features and handle simple bug fixes identified in pull request reviews.
They also leverage GitHub Actions integration to have Claude
automatically address Pull Request comments like formatting issues
or function renaming.
Codebase exploration
When working with unfamiliar codebases (like the monorepo or API
side), the team uses Claude Code to quickly understand how systems
work. Instead of waiting for Slack responses, they ask Claude directly
for explanations and code references, saving significant time in
context switching.
CLAUDE CODE FOR PRODUCT DEVELOPMENT

## how-anthropic-uses-claude-code#007

## Page 6

## how-anthropic-uses-claude-code#008

Claude Code for product
development
Team impact
Faster feature implementation
Successfully implemented complex features like Vim mode with 70% of
code written autonomously by Claude.
Improved development velocity
Can rapidly prototype features and iterate on ideas without getting
bogged down in implementation details.
Enhanced code quality through automated testing
Claude generates comprehensive tests and handles routine bug fixes,
maintaining high standards while reducing manual effort.
Better codebase exploration
Team members can quickly understand unfamiliar parts of the monorepo
without waiting for colleague responses.
Top tips from the
Create self-sufficient loops
Claude Code team
Set up Claude to verify its own work by running builds, tests, and lints
automatically. This allows Claude to work longer autonomously and catch
its own mistakes, especially effective when you ask Claude to generate
tests before writing code.
Develop task classification intuition
Learn to distinguish between tasks that work well asynchronously
(peripheral features, prototyping) versus those needing synchronous
supervision (core business logic, critical fixes). Abstract tasks on the
product's edges can be handled with "auto-accept mode," while core
functionality requires closer oversight.
Form clear, detailed prompts
When components have similar names or functions, be extremely specific
in your requests. The better and more detailed your prompt, the more you
can trust Claude to work independently without unexpected changes to
the wrong parts of the codebase.
CLAUDE CODE FOR PRODUCT DEVELOPMENT

## how-anthropic-uses-claude-code#009

## Page 7

## how-anthropic-uses-claude-code#010

Claude Code for security
engineering
Main Claude Code use cases
The Security Engineering team
focuses on securing the software
Complex infrastructure debugging
development lifecycle, supply
When working on incidents, they feed Claude Code stack traces and
chain security, and development
documentation, asking it to trace control flow through the codebase. This
environment security. They use
significantly reduces time-to-resolution for production issues, allowing
Claude Code extensively for
them to understand problems that would normally take 10-15 minutes of
writing and debugging code.
manual code scanning in about 5 minutes.
Terraform code review and analysis
For infrastructure changes requiring security approval, they copy
Terraform plans into Claude Code to ask "what's this going to do? Am I
going to regret this?" This creates tighter feedback loops and makes it
easier for the security team to quickly review and approve infrastructure
changes, reducing bottlenecks in the development process.
Documentation synthesis and runbooks
They have Claude Code ingest multiple documentation sources and
create markdown runbooks, troubleshooting guides, and overviews.
They use these condensed documents as context for debugging real
issues, creating a more efficient workflow than searching through full
knowledge bases.
Test-driven development workflow
Instead of their previous "design doc - janky code - refactor - give up
on tests" pattern, they now ask Claude Code for pseudocode, guide it
through test-driven development, and periodically check in to steer it
when stuck, resulting in more reliable and testable code.
Context switching and project onboarding
When contributing to existing projects like "dependant" (a web
application for security approval workflows), they use Claude Code
to write, review, and execute specifications written in markdown and
stored in the codebase, enabling meaningful contributions within days
instead of weeks.
CLAUDE CODE FOR SECURITY ENGINEERING

## how-anthropic-uses-claude-code#011

## Page 8

## how-anthropic-uses-claude-code#012

Claude Code for security
engineering
Team impact
Reduced incident resolution time
Infrastructure debugging that normally takes 10-15 minutes of manual
code scanning now takes about 5 minutes.
Improved security review cycle
Terraform code reviews for security approval happen much faster,
eliminating developer blocks while waiting for security team approval.
Enhanced cross-functional contribution
Team members can meaningfully contribute to projects within days
instead of weeks of context building.
Better documentation workflow
Synthesized troubleshooting guides and runbooks from multiple sources
create more efficient debugging processes.
Top tips from the
Use custom slash commands extensively
Security engineering uses 50% of all custom slash command
Security Engineering
implementations in the entire monorepo. These custom commands
team
streamline specific workflows and speed up repeated tasks.
Let Claude talk first
Instead of asking targeted questions for code snippets, they now
tell Claude Code to "commit your work as you go" and let it work
autonomously with periodic check-ins, resulting in more
comprehensive solutions.
Leverage it for documentation
Beyond coding, Claude Code excels at synthesizing documentation and
creating structured outputs. They provide writing samples and formatting
preferences to get documents they can immediately use in Slack, Google
Docs, and other tools to avoid interface switching fatigue.
CLAUDE CODE FOR SECURITY ENGINEERING
