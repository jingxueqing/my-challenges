---
source_file: lessons-from-ai-code-reviews.html
title: AI-powered entomology: Lessons from millions of AI code reviews
url: https://ai.engineer/talks/TswQeKftnaw-ai-powered-entomology-lessons-from-millions-ai
recovered: 2026-09-27（离线包原文件为 0 字节，自 AIE Talks 页面补抓全文）
---

# AI-powered entomology: Lessons from millions of AI code reviews

**Speaker**: Tomas Reimers (Graphite) · 10:21

> Diamond's development shows why finding bugs is only the beginning: an AI reviewer must choose useful comments, then measure whether developers act on them.

From a talk by Tomas Reimers.

Before you start: Familiarity with pull requests and code review is sufficient; no machine learning background is required.

## 01 · [0:16] Can AI find the bugs AI helps create?

As AI writes more code, can it also find the bugs that come with it? That question led Graphite co-founder Tomas Reimers and his team to build Diamond, an AI reviewer that connects to GitHub. The project began about a year before the talk, as the team saw both AI-generated code and bugs increasing. Reimers calls the work AI-powered entomology: the study of bugs.

The initial experiment was straightforward: give Claude a pull request and ask it to find bugs. The results included a concrete failure in Graphite's own codebase: certain paths returned a database ORM class without instantiating it, which Reimers says would crash the server. Another example, shared on Twitter, involved border-radius arithmetic that he described as dividing by a negative number and crashing the frontend.

## 02 · [1:42] A correct comment can still be unwelcome

Finding real bugs did not make the reviewer consistently useful. Alongside the successful catches came suggestions to change code to do what it already did, assertions that valid CSS behavior was invalid, and requests to restore old behavior simply because the code used to work that way. These comments eroded the confidence earned by the useful ones.

The first explanation was a capability boundary: there are issues an LLM can catch and issues it cannot. Asking a model what review comments someone would leave on a PR encourages it to imitate the whole activity of code review. That includes comments within its capabilities and comments beyond them. Categorizing those capabilities helped, but it left another class of frustrating output: requests to document a class, extract logic into a function, or add tests. These could be technically defensible without being useful interruptions.

The distinction became clearer when developers and designers reviewed historical comments from both humans and the bot. Developers largely agreed about which comments they would accept from an LLM. Designers found some of those judgments puzzling: superficially similar comments received different reactions. The developers were evaluating more than correctness. Advice they might welcome from a colleague could feel pedantic or annoying from an automated reviewer. **Model capability and developer receptiveness are separate axes.** A useful reviewer needs to satisfy both.

## 03 · [3:55] Build the taxonomy from real reviews

Graphite repeatedly asked various LLMs to categorize 10,000 comments from its own and open-source codebases, then summarized the categorizations. This produced a vocabulary for discussing what reviewers actually say, rather than treating every comment as a bug report.

| Comment category | What it identifies |
| --- | --- |
| Bugs | Logical inconsistencies causing unintended behavior |
| Accidentally committed code | Code included unintentionally |
| Performance concerns | Potential performance problems |
| Security concerns | Potential security problems |
| Documentation mismatches | Code and its description disagree |
| Stylistic changes | Comments or patterns inconsistent with local conventions |

These categories require different judgments. A documentation mismatch, for example, establishes a disagreement but leaves open whether the implementation or the prose is wrong. A style suggestion may depend on knowing which pattern the repository follows.

Some highly desirable comments require information unavailable to the model. A senior developer might explain that the team previously used an approach but abandoned it for a particular reason. If that history exists only in developers' heads, the reviewer cannot recover it from the code. This **tribal knowledge** belongs on the wanted-but-difficult side of the taxonomy.

A quadrant chart places best practice and code cleanliness at upper left, bugs, performance and security at upper right, preference at lower left, and tribal knowledge at lower right. Review comment categories mapped by LLM capability and human receptiveness.

## 04 · [5:18] Best-practice advice needs a reason to appear

The opposite problem is advice that models can readily produce but developers do not necessarily want: comment this function, add tests, extract a type, or move this logic into a function. A human reviewer applies a local judgment. Is this logic unusually tricky for this codebase? Is someone likely to misunderstand it? Would extraction actually help? Without that judgment, the bot can keep producing defensible cleanliness suggestions almost anywhere. Technical correctness alone does not decide whether a comment belongs in the review.

More context can change the boundary. Repository code, past history, style guides, and explicit rules can help the reviewer determine which advice fits the project. Reimers suggests that the region of comments a model can produce and developers will welcome expands as that context grows. The practical target is the intersection supported by the context available now.

## 05 · [6:33] Keep checking the boundary as the reviewer changes

An offline taxonomy provides an initial direction, but it cannot establish that a changing reviewer stays useful. Graphite updated its prompts to request only comments within the model's capabilities that developers wanted to receive. Reimers reports that reception improved anecdotally. The next problem was maintaining that behavior as the system evolved.

Moving to Claude 4, or choosing Opus instead of Sonnet, raises the question again: does the reviewer still operate in the useful part of the chart? Adding context raises a related opportunity: perhaps it can now produce valuable categories of comments that were previously out of reach. Graphite began by inspecting the distribution of comment types the reviewer actually produced.

## 06 · [7:47] Use reactions to detect overreach

Graphite added emoji upvotes and downvotes to review comments as a feedback channel for capability failures. A spike in downvotes could signal hallucinations or an attempt to push the reviewer beyond what it could reliably assess. The operational response was to narrow its behavior again. That made reactions useful for detecting trouble, while leaving the second axis—whether developers wanted the comments—harder to measure.

Reimers reports a downvote rate below 4% at the time of the talk.

## 07 · [8:30] Measure whether the requested change happens

A review comment usually asks someone to change code. Graphite therefore began measuring the percentage of comments followed by the change they described, examining open-source repositories and repositories available through its code review product. This turns usefulness into an observable outcome: did the requested change occur?

Reimers reports that about 50% of human review comments led to changes within the same PR. That supplied a practical target for the bot: reach the level of action associated with human feedback. The observation window matters. A developer may agree with a comment but defer the fix to a follow-up PR; advice may concern future work rather than the current change; and a preference may reasonably remain unimplemented. Healthy review cultures leave room for disagreement, so an unacted-on comment is not automatically a failed review.

Reimers reports that Diamond reached a 52% within-PR action rate as of March. He attributes reaching the human baseline to prompting the reviewer appropriately. These are reported action rates, not bug-detection accuracy. The result supports a narrower, useful conclusion: a reviewer constrained to appropriate comments can get developers to make the changes it requests at roughly the observed human rate.

Diamond is the production product Reimers presents for applying these findings. Its underlying approach connects scope to feedback: select comment categories the model can handle and developers welcome, then measure whether those comments produce changes. That is what turns the ability to spot an occasional bug into a code review product people can use.

## 08 · Key takeaways from the timestamped transcript

1. AI-generated code volume and bug volume rose together; Graphite built Diamond to test whether AI could also find the bugs.
2. Early experiments with Claude on pull requests found real failures: an uninstantiated database ORM class that would crash the server, and border-radius arithmetic dividing by a negative number.
3. The same experiments produced unusable comments: asking for changes to code that already did the thing, wrongly challenging valid CSS, and requesting reverts to old behavior.
4. LLM capability and developer receptiveness are two separate axes; a comment can be technically correct and still unwelcome from a bot.
5. Graphite categorized 10,000 comments from its own and open-source codebases into: bugs, accidentally committed code, performance concerns, security concerns, documentation mismatches, and stylistic changes.
6. Tribal knowledge (why the team stopped doing it the old way) is wanted by developers but out of reach for the model; code-cleanliness advice is easy for the model but unwelcome.
7. More context (repo history, style guides, explicit rules) expands the region of useful AI review.
8. Emoji reactions on comments detect overreach: downvote spikes signal hallucination; the downvote rate was below 4%.
9. About 50% of human comments lead to within-PR changes; Diamond reached 52% as of March by prompting the reviewer to stay in the useful quadrant.
10. Action rate is the measurement that turned "AI can occasionally find bugs" into a usable code review product.
