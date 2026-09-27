# 待译批次 13

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## how-long-contexts-fail#005

But even if consolidation and competition don’t slow MCPs , Context Confusion will. It turns out there can be such a thing as too many tools.

The Berkeley Function-Calling Leaderboard is a tool-use benchmark that evaluates the ability of models to effectively use tools to respond to prompts. Now on its 3rd version, the leaderboard shows that every model performs worse when provided with more than one tool 4 . Further, the Berkeley team, “designed scenarios where none of the provided functions are relevant…we expect the model’s output to be no function call.” Yet, all models will occasionally call tools that aren’t relevant.

Browsing the function-calling leaderboard, you can see the problem get worse as the models get smaller:

A striking example of context confusion can be seen in a recent paper which evaluated small model performance on the GeoEngine benchmark , a trial that features 46 different tools . When the team gave a quantized (compressed) Llama 3.1 8b a query with all 46 tools it failed, even though the context was well within the 16k context window. But when they only gave the model 19 tools, it succeeded.

## how-long-contexts-fail#006

The problem is: if you put something in the context the model has to pay attention to it. It may be irrelevant information or needless tool definitions, but the model will take it into account. Large models, especially reasoning models, are getting better at ignoring or discarding superfluous context, but we continually see worthless information trip up agents. Longer contexts let us stuff in more info, but this ability comes with downsides.

### Context Clash

Context Clash is when you accrue new information and tools in your context that conflicts with other information in the context.

This is a more problematic version of Context Confusion : the bad context here isn’t irrelevant, it directly conflicts with other information in the prompt.

## how-long-contexts-fail#007

A Microsoft and Salesforce team documented this brilliantly in a recent paper . The team took prompts from multiple benchmarks and ‘sharded’ their information across multiple prompts. Think of it this way: sometimes, you might sit down and type paragraphs into ChatGPT or Claude before you hit enter, considering every necessary detail. Other times, you might start with a simple prompt, then add further details when the chatbot’s answer isn’t satisfactory. The Microsoft/Salesforce team modified benchmark prompts to look like these multistep exchanges:

All the information from the prompt on the left side is contained within the several messages on the right side, which would be played out in multiple chat rounds.

The sharded prompts yielded dramatically worse results, with an average drop of 39%. And the team tested a range of models – OpenAI’s vaunted o3’s score dropped from 98.1 to 64.1.

What’s going on? Why are models performing worse if information is gathered in stages rather than all at once?

## how-long-contexts-fail#008

The answer is Context Confusion : the assembled context, containing the entirety of the chat exchange, contains early attempts by the model to answer the challenge before it has all the information . These incorrect answers remain present in the context and influence the model when it generates its final answer. The team writes:

We find that LLMs often make assumptions in early turns and prematurely attempt to generate final solutions, on which they overly rely. In simpler terms, we discover that when LLMs take a wrong turn in a conversation, they get lost and do not recover.

This does not bode well for agent builders. Agents assemble context from documents, tool calls, and from other models tasked with subproblems. All of this context, pulled from diverse sources, has the potential to disagree with itself. Further, when you connect to MCP tools you didn’t create there’s a greater chance their descriptions and instructions clash with the rest of your prompt.

## how-long-contexts-fail#009

The arrival of million-token context windows felt transformative. The ability to throw everything an agent might need into the prompt inspired visions of superintelligent assistants that could access any document, connect to every tool, and maintain perfect memory.

But as we’ve seen, bigger contexts create new failure modes. Context poisoning embeds errors that compound over time. Context distraction causes agents to lean heavily on their context and repeat past actions rather than push forward. Context confusion leads to irrelevant tool or document usage. Context clash creates internal contradictions that derail reasoning.

These failures hit agents hardest because agents operate in exactly the scenarios where contexts balloon: gathering information from multiple sources, making sequential tool calls, engaging in multi-turn reasoning, and accumulating extensive histories.

Fortunately, there are solutions! In an upcoming post we’ll cover techniques for mitigating or avoding these issues, from methods for dynamically loading tools to spinning up context quarantines.

Read the follow up article, “ How to Fix Your Context “

## how-long-contexts-fail#010

Gemini 2.5 and GPT-4.1 have 1 million token context windows, large enough to throw Infinite Jest in there, with plenty of room to spare. ↩

The “ Long form text ” section in the Gemini docs sum up this optmism nicely. ↩

In fact, in the Databricks study cited above, a frequent way models would fail when given long contexts is they’d return summarizations of the provided context, while ignoring any instructions contained within the prompt. ↩

If you’re on the leaderboard, pay attention to the, “Live (AST)” columns. These metrics use real-world tool definitions contributed to the product by enterprise , “avoiding the drawbacks of dataset contamination and biased benchmarks.” ↩

## BETA: Translations

I'm testing out using LLMs to rewrite articles for different contexts and audiences. The following content has not
 been exhaustively reviewed and is presented as a proof-of-concept. Reach out if you spot
 something egregious or want to know more.

-->

## how-to-review-code-effectively#001

Sarah Vessels · @cheshire137

July 23, 2024

| 
 
 16 minutes

Share:

As a staff engineer at GitHub, code review is one of my main focus areas in my day to day work. Over the past eight years, I’ve reviewed more than 7,000 pull requests. Why so many? Because code review is crucial to building good software and another set of eyes can often spot issues you would have otherwise missed.

I see code review as one of the most important aspects of my job. In fact, whenever I see that a teammate has a pull request ready for code review, I prefer to drop whatever branch I’m working on to review their proposed changes instead. After all, their pull request has already passed the continuous integration (CI) gauntlet and met the bar for their own judgment of “done,” so it’s probably closer to being shippable than my own in-progress work. I’d rather get their code over the finish line than churn an unknown amount of time more to finish my code.

The sooner I provide feedback — “This can be nil and cause an error,” “This looks like an n+1 query,” “It would be great to have a method signature on this” — the faster that feedback can be addressed and the bug squashed or feature shipped.

## how-to-review-code-effectively#002

I’d like to share how I approach code review in hopes that we can all ship better code.

## What is code review?

Strictly speaking, code reviews—via pull request reviews on GitHub—allow collaborators to comment on the changes proposed in pull requests, indicate their approval of the changes, or request further changes before the pull request is merged.

I see a pull request as the beginning of conversation. I read it as the author saying “I think this improves on what we have today.” Code review is a great opportunity to shape the product’s implementation. As a code reviewer, my job is to go back and forth in discussion with the author to improve their code by asking questions, questioning assumptions, and generally serving as a second set of eyes.

Why review code? It's good for your career
 I’ve learned a great deal from other reviewers’ perspectives on my own code, and after repeated positive feedback thanking me for timely code reviews, I know that my code review comments have likewise helped level up my teammates. Put simply, code review has impact, and getting a promotion requires showing your impact.

## how-to-review-code-effectively#003

Code reviews are impactful because they help exchange knowledge and increase shipping velocity. They are nice, linkable artifacts that peers and managers can use to show how helpful and knowledgeable you are. They can highlight good communication skills, particularly if there’s a complex or controversial change needed. So, making your case well in a code review can not only guide the product’s future and help stave off incidents, it can be good for your career.

## Fine-tune your code review process

### How to find pull requests for review

I live in my GitHub notifications inbox . It’s one of just a few tabs I pin in my browser, so it’s always available. Any time I’m waiting on CI, I’m in between tasks, starting my day, or generally have a spare moment, I like to check my inbox. I find most of the pull requests I review there. Teams at GitHub tend to have a particular Slack channel they treat as home base, and that’s a good place to share ready-for-review pull requests—it’s one of the other main ways I discover pull requests.

## how-to-review-code-effectively#004

I also have good luck using the GitHub Slack integration to subscribe a Slack channel to new pull requests relevant to my team. To filter which pull requests show up in Slack, I use a label specific to the team, then a ‘subscribe’ command in Slack like /github subscribe your/repo pulls +label:"your-team-label" .

Tip
 
You can repeat the team-review-requested: qualifier in your query to get pull requests for review across many different code owners.

I like to search for outstanding pull requests that may need review with queries like is:open archived:false is:pr org:github -is:draft team-review-requested:github/relevant-codeowner-team . With that query, I find open , unarchived pull requests within the GitHub organization that are not drafts and have relevant codeowner teams as a requested reviewer . I usually will omit the review:required search qualifier because I’m interested in reviewing a pull request even if a teammate has already reviewed it. After all, reviewing code not only helps the author, it helps me stay up to date with changes affecting code I’m responsible for.

### Use reviewer teams to manage notifications

## how-to-review-code-effectively#005

You don’t want code changes to ping such a large team that everyone on the team assumes reviewing the change isn’t their responsibility . That can result in pull requests that either languish unreviewed or get merged before they should, because key reviewers missed them in a deluge of notifications. Both of these scenarios affect the quality of the product.

I recommend honing the number of code owner teams you’re on, if you’re able, to keep your notifications manageable. That way, pull requests that land in your inbox aren’t just noise, they’re actually something you feel you should review. While big, catch-all code owner teams can be okay as a fallback option, they aren’t great as a first-line default for automatic review requests. Keep your repository’s CODEOWNERS file well organized, with well-defined code boundaries to go along with it, to limit notifications and help reviewers avoid notification fatigue.

## how-to-review-code-effectively#006

Another way of limiting team-based notifications is to create a first responders team and then use automation to add and remove team members based on a schedule. This can let your team focus on their day-to-day code base, while scheduled first responders get notified of pull requests in your team’s service areas. Using the PagerDuty API , for example, you can determine who is a first responder on a given day. You can then use the Octokit library to add and remove team members.

### Standardize code reviews across teams with automation

Repository-level configuration and automation, such as using a CODEOWNERS file and branch protection rules , can be helpful to enforce review process standards across teams. Other standards, such as what’s worth commenting on in a pull request, have to be maintained by us humans. Document how code reviews work within your team to make sure anyone providing a code review or submitting a pull request knows how to get their pull requests reviewed, the expected turnaround time for review, and what automation is in use to facilitate review.

## how-to-review-code-effectively#007

Some teams use a project board to keep track of which pull requests come in for review; I’ve seen this work well for a team that manages a shared API, an area often modified by those outside the team. Other teams depend on GitHub notifications alone, which I’ve seen work well when code ownership is tightly scoped and the team is disciplined about reviewing pull requests as they come in.

If you follow a process unique to your specific team, automation can help communicate expectations with those outside your team. For example, if many other teams depend on your team’s reviews, you can use a bot to automatically leave a comment on any pull request where your team’s review is requested, to tell the author when they can expect to hear from you.

## What makes a code review good or bad?

Good code reviews add clarity and push code toward a better state than where it started.

## how-to-review-code-effectively#008

As a reviewer, clarity in communication is key. You’ll want to make clear which of your comments are personal preference and which are blockers for approval. Provide an example of the approach you’re suggesting to elevate your code review and make your meaning even clearer. If you can provide an example from the same repository as the pull request, even better—that further supports your suggestion by encouraging consistent implementations.

By contrast, poor code reviews lack clarity. For example, a blanket approval or rejection without any comments can leave the pull request author wondering if the review was thorough. Even just reiterating your understanding of the pull request author’s intention with your approval can surface whether you and the author have the same understanding.

## how-to-review-code-effectively#009

A code review that is unclear about when its suggestions should be implemented can also be a poor experience for the author. It’s fine to note that existing, unchanged code should be refactored, or an additional case should be handled, but it’s important to specify whether those are precursors to approval. If the pull request is okay to land without your suggestions, make sure to say so. It may be safer to keep a small diff and ship those changes separately, as separate pull requests.

Here’s a code review comment that displays specificity and clearly communicates suggested implementations:

“I see your new method matches the existing style in this file, taking [X] parameters. Having that many parameters hurts readability and implies the function is doing too much. What do you think about refactoring this method and the existing ones in a later pull request to reduce how many parameters they take?”

What this comment does well:

Provides specific details.

References specific code or issues.

Suggests a resolution to the problem.

Cites evidence or provides an explanation

On the other end of the spectrum, here are some examples of review comments that could be better:

## how-to-review-code-effectively#010

“I don’t like this.” – What doesn’t the reviewer like? Do they have an alternative in mind that they could explicitly state?

Possible improvements:

“This line is doing a lot, could we simplify it to improve readability?”

“I think this will have performance problems because of an n+1 query.”

“Could we use the [preferred framework]’s solution for this instead of writing a custom implementation?”

“This won’t work.” – Why won’t the changes work?

Possible improvements:

“This won’t work because [X], see this relevant issue: [issue link].”

“This was tried before in [pull request link] and it didn’t work because of [X].”

“If you run into problems with [X], you could try [alternative approach] instead.”

“I think this fixes a bug.” – I love the callout, but is there any additional context, such as an issue link, that could make this more clear?

Possible improvements:

“I think this fixes [issue link].”

“Is this fixing the bug from [issue link]?”

“This looks like the bug we ran into with [link to failing build]. Thanks for the fix!”

## How to give a good code review

### Ask questions
