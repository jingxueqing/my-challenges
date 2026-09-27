# 待译批次 14

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## how-to-review-code-effectively#011

I think of the pull request author as the person with the most context on the changes their pull request is making. I can point out problems I see based on my history—my experience working in a Ruby on Rails monolith, in TypeScript, or with a database that gets a lot of traffic—but I trust the author’s answers to my questions. I treat their understanding of the particulars as better than mine.

Tip
 
If you’re new to a code base or team, ask questions in code reviews to learn about the tech stack and what internal tools and libraries are available. Every pull request you review is a chance to find out why the author preferred one approach to another.

## how-to-review-code-effectively#012

I also love to ask questions that involve the assumptions made in the code. What is the shape of the data they’re working with? Does data exist that doesn’t match that shape? Does the code respond to that well? Is the code resource intensive? Will it perform well? As a reviewer, my favorite response is for the author to provide an automated test that verifies the behavior in those scenarios. My second favorite response is empirical data, such as a query from our data warehouse or a Datadog graph that shows why those scenarios aren’t a problem.

As a pull request author, I appreciate receiving questions. When someone asks a question, it makes space for me to explain why I’m confident about my change, citing issues, queries, or graphs as necessary. It also lets me share my knowledge and experience with others. The author not only sees my responses, but also other reviewers and future readers who may be tracking down context on a past decision.

### Offer affirmations

## how-to-review-code-effectively#013

Beyond asking questions, it’s good practice to comment on the parts of the pull request that you agree with. These comments can highlight that you read and understood what was being changed, or that you verified some assumption in the code. Here are a few examples:

“Looks like this matches the pattern used in other classes in this module.”

“Thanks for adding a test for this!”

“This is much more readable than before.”

It’s also just nice being on the receiving end of such comments, in my experience. Receiving a code review can sometimes feel draining. When I’m fielding questions and suggestions from several parties, it can be a good boost to get a few comments that don’t ask anything of me and instead support and acknowledge the work I’ve already put in.

### Be aware of biases and assumptions

It’s easy to let your biases about the reviewer, or the area of code they’re changing, affect your review. You get used to someone working in an area or having some level of seniority and assume they know what they’re doing—but everyone makes mistakes. Your eyes on their changes, your questions checking their assumptions or validating your own, can catch a problem before it’s deployed.

## how-to-review-code-effectively#014

I’m big on writing tests because they take some of the bias out. When you write a test to check that code works properly, you don’t have to take the author’s word for it , you just look at whether the test passed—provided you get the test right, of course. 😅

I’m also big on junior developers asking senior developers questions in code review, even if they think their question is silly or has an obvious answer. If it’s not obvious to you, that’s valid. It won’t be obvious to someone else either! Ask the question, make the space for the author to write down their answer, and preserve that bit of education for those who come later.

### To approve or not

## how-to-review-code-effectively#015

I see my review as a blocking gate that can stop another person from improving our product, so I withhold approval conscientiously. I will often have personal preferences and suggest optional changes I’d like to see the author make, but I won’t withhold an approval based on those alone. If I have suggestions for someone’s pull request, but their pull request as it is won’t break production, negatively impact users, or otherwise cause problems, I will approve with those comments. The author can choose to address my feedback before they merge their pull request, or they can follow up in another branch.

Tip
 
Use feature flags and make your pull requests small. The less scary your change is, the faster it can be reversed in production, the easier it will be for me to approve it!

## how-to-review-code-effectively#016

Keep in mind the importance of your suggestion when you’re reviewing code. Is it worth delaying the ship to get your suggestion addressed? Is it worth the whole cycle of the author seeing your feedback, making the suggested changes, waiting for CI, a re-review, deployment and finally merging? If a suggestion’s absence isn’t going to make someone’s day worse, let the author decide if or when to make the suggested change.

The ‘Request changes’ option stops a pull request from being merged until the reviewer comes back and approves it. I very rarely use it, as it usually feels too heavy-handed. I trust my team to know when to approve a pull request, so a teammate’s approval is fine in place of mine. Likewise, I trust the pull request author to respect my feedback and consider it, not just blindly merging because someone else approved but I didn’t. About the only time I’ll choose the ‘Request changes’ option is when I think there is an immediate security issue and I’m worried they won’t see my concern before merging.

## how-to-review-code-effectively#017

Why code reviews matter when using AI coding tools
 
AI coding tools often include various safeguards against incorrect or insecure code, but don’t be lulled into a false sense of security. As the human reviewer at the helm, you are the last line of defense and should review all code with an equal level of diligence.

## How to get the most out of code reviews

### Review your own code

GitHub Senior Software Engineer Paul Smith taught me to review my own pull request before asking others to do so, and I would advise you to do the same. Take a first pass and leave comments inline on non-obvious changes or ones you would ask about if you saw them in someone else’s pull request. A self-review can also help determine if a pull request is too big and would benefit from being split up .

Shout-out: if you care about keeping your pull requests small, you can make use of lerebear/sizeup-action to automatically apply a label to pull requests indicating their complexity and size.

### Be welcoming of post-merge reviews

## how-to-review-code-effectively#018

If I happen to merge a pull request before someone gets a chance to review it, I still welcome their review. If my pull request broke something or had unintended consequences, commenting as much on the pull request leaves that breadcrumb trail to help future readers track down what happened!

If I receive a review on a merged pull request, I’ll address the feedback like I would have before the pull request landed. Maybe that’ll be a comment to explain my perspective, maybe it’ll be additional pull requests to iterate on the code I originally shipped. Maybe it’ll be opening new issues to capture additional work to be done.

### Use draft pull requests

When you create a new pull request, you have the option to set the pull request as a draft. I lean heavily on the draft stage to indicate whether or not I want reviews. For example, if a required CI build is failing or I’m just not finished yet, I’ll keep it as a draft. I tend to expect the same from others’ pull requests: if it’s a draft, I assume the author isn’t ready for reviews. If it’s marked as ready for review, I assume that getting enough approvals is all that’s preventing them from deploying the pull request.

## how-to-review-code-effectively#019

The draft status implies that a pull request is not finished, so I move pull requests back to draft when resolving merge conflicts or addressing reviewer feedback. If I have to modify the code, I’ll mark my pull request as a draft first so as not to overwhelm people who have already reviewed it. When I move it back to ‘ready’, it sends a GitHub notification to those reviewers so they can look at it again.

### Be gracious

The expression, “You can catch more flies with honey than vinegar,” comes to mind. I want reviews on my pull requests, so I like to reply to comments on my pull requests—especially if I disagree with the reviewer. Even if I don’t write a reply to a review comment, I’ll often react with a 👍 to indicate I agree or a ❤ to say thank you.

I want reviewers to trust that their suggestions won’t be forgotten, so I keep them in the loop via comments. If I agree with their suggestion—to go further refactoring existing code, for example—I may say as much while also pushing back about making that change in the current pull request. When I address their feedback in a later pull request, I come back to provide a link and let the reviewer know their feedback didn’t go unheard.

## how-to-review-code-effectively#020

I’ll also tag them in later pull requests where I implement the suggested changes and include a note saying “This addresses @so-and-so’s feedback from <previous pull request URL>.” This both provides context for other readers and acts as a shout-out to the original reviewer, giving them credit for the idea.

When you follow through on a promise to address feedback in a later branch, that helps build trust with your reviewer, which can help them feel comfortable approving your future pull requests because they know that you won’t leave something incomplete.

## Wrap-up

Code review’s importance for product quality can’t be overstated, especially in the age of AI code generation. Many times in my career, a bug has been caught or an incident avoided simply by having that second set of eyes. Code review is well worth the time investment, whether spent in daily reviews, in ironing out processes, or in building automation to support it. It’s faster and less painful for developers to review pull requests thoroughly now than to deal with a problem later that’s already shipped to production.

## how-to-review-code-effectively#021

Thank you for caring enough about code quality to read my philosophy on code review. Have you checked your review queue lately? Maybe now is a good time to put these ideas into action.

If you want to learn more about how to use pull request reviews on GitHub, check out the post on GitHub Community by Staff DevOps Architect Mickey Gousset and Staff DevOps Architect Joshua Johanning discussing 5 Tips for Reviewing a Pull Request .

## Tags:

code review

## 
 Written by

Staff Software Engineer, GitHub

code review

## More on code review

### How to use GitHub Copilot to level up your code reviews and pull requests 
 Discover practical ways GitHub Copilot streamlines code reviews, pull requests, and daily engineering tasks with real prompts, examples, and workflow tips from our engineering team.

Melissa Pastore

### Code review in the age of AI: Why developers will always own the merge button 
 When it comes to merging code, developers will always make the final decision. But we’re rethinking how tools like GitHub Copilot can help.

Elle Shwer

## 
 Related posts

Developer skills

### 
 
 GitHub for Beginners: Getting started with GitHub security

## how-to-review-code-effectively#022

Learn how to secure your projects and keep them safe with GitHub Advanced Security.

AI & ML

### 
 
 Building AI-powered GitHub issue triage with the Copilot SDK

Learn how to integrate the Copilot SDK into a React Native app to generate AI-powered issue summaries, with production patterns for graceful degradation and caching.

Developer skills

### 
 
 GitHub for Beginners: Getting started with GitHub Actions

Set up your first GitHub Actions workflow in this how-to guide.

## 
 Explore more from GitHub

### 
 Docs

Everything you need to master GitHub, all in one place.

Go to Docs

### 
 GitHub

Build what’s next on GitHub, the place for anyone from anywhere to build anything.

Start building

### 
 Customer stories

Meet the companies and engineering teams that build with GitHub.

Learn more

### 
 GitHub Universe 2024

Get tickets to the 10th anniversary of our global developer event on AI, DevEx, and security.

Get tickets

## We do newsletters, too
 Discover tips, technical guides, and best practices in our biweekly newsletter just for devs.

Your email address

## how-warp-uses-warp#001

Notion JavaScript must be enabled in order to use Notion.
Please enable JavaScript to continue.

## mcp-food-for-thought#001

The Model Context Protocol (MCP) is a pretty big deal these days. It’s become the de facto standard for giving LLMs access to tools that someone else wrote, which, of course, turns them into agents . But writing tools for a new MCP server is hard, and so people often propose auto-converting existing APIs into MCP tools ; typically using OpenAPI metadata ( 1 , 2 ).

In my experience, this can work but it doesn’t work well . Here are a few reasons why:

## Agents don’t do well with large numbers of tools

Infamously, VS Code has a hard limit of 128 tools - but many models struggle with accurate tool calling well before that number . Also, each tool and its description takes up valuable context window space.

Most web APIs weren’t designed with these constraints in mind! It’s fine to have umpteen APIs for a single product area when those APIs are called from code, but if each of those APIs is mapped to an MCP tool the results might not be great.

MCP tools designed from the ground up are typically much more flexible than individual web APIs , with each tool being able to do the work of several individual APIs.

## APIs can blow through context windows quickly

## mcp-food-for-thought#002

Imagine an API that returns 100 records at a time, and each record is very wide (say, 50 fields). Sending those results to an agent as-is will use up a lot of tokens; even if a query can be satisfied with only a few fields, every field ends up in the context window.

APIs are typically paginated by the number of records, but records can vary a lot in size. One record might contain a large text field that takes up 100,000 tokens , while another might contain 10. Putting these API results directly into an agent’s context window is a gamble; sometimes it works, sometimes it will blow up.

The format of the data can also be an issue. Most web APIs these days return JSON, but JSON is a very token-inefficient format. Take this:

[ 
 { 
 "firstName" : "Alice" , 
 "lastName" : "Johnson" , 
 "age" : 28 
 }, 
 { 
 "firstName" : "Bob" , 
 "lastName" : "Smith" , 
 "age" : 35 
 } 
 ] 
 
 Compare to the same data in CSV format:

firstName , lastName , age 
 Alice , Johnson , 28 
 Bob , Smith , 35 
 
 The CSV data is much more succinct - it uses up half as many tokens per record. Typically CSV, TSV, or YAML (for nested data) are better choices than JSON .

## mcp-food-for-thought#003

None of these issues are insurmountable. You could imagine automatically adding tool arguments that let agents project fields, automatically truncating or summarizing large results, and automatically converting JSON results to CSV (or YAML for nested data). But most servers I’ve seen do none of those things.

## APIs don’t make the most of agents’ unique capabilities

APIs return structured data for programmatic consumption. That’s often what agents want from tool calls… but agents can also handle other, more free-form instructions.

For example an ask_question tool could perform a RAG query over some documentation, then return information in plain text that is used to inform the next tool call - skipping structured data entirely.

Or, a call to a search_cities tool could return a structured list of cities and a suggestion of what to call next:
