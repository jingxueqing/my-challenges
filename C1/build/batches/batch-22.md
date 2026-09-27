# 待译批次 22

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## specs-are-the-new-source-code#006

## Wait, didn’t prototypes kill the spec? 
 Until recently, the product lifecycle had to start with the spec (or PRD or concept doc or napkin) that gets the initial wireframing, designing, prototyping, and MVP development under way.
 The traditional approach felt like a necessary evil. Engineers built basic MVPs to get something—anything—into customers' hands. "If you're not embarrassed by the first version of your product, you've launched too late" became gospel.
 Our entire approach to building products has recently undergone a significant shift, and in this new world, the spec is often the output, not the input . 
 Today, you don't need to ship a single line of code to get a prototype into customer hands. Tools like v0, Lovable, and Replit let you build functioning prototypes in hours, not weeks. No engineering required.
 This isn't just faster—it's fundamentally different. Armed with a "vibe coded" prototype, you can gather real customer feedback before writing a single line of your feature spec. You can test assumptions, iterate on flows, refine interactions.
 The old workflow looked like this : vague idea → wireframes → designs → engineer-built MVP → customer feedback → painful spec revision → wireframes → designs → rebuild → pray.

## specs-are-the-new-source-code#007

The new workflow : vague idea → rapid prototype → customer feedback → crystal-clear spec → AI-assisted implementation.

Prototypes haven't killed the spec. They're making specs better.

## Spec-driven development in action 
 Let's look at a hands-on example of how this all plays out. Danny Martinez is the founder of decimals, a platform (in stealth) that enables experts in the creator economy to place talent from their network into jobs. 
 
 Are you an AI-first PM looking for a new opportunity? Drop in your details and we’ll let you know when we come across interesting opportunities.

Are you a company looking to hire an AI-first PM? Apply to our talent network and we’ll share a curated shortlist of candidates.

Danny is going to walk us through their spec-driven development process—a process that has had two impacts:
 massively improved communication with engineering for the bigger features, and

enabled Danny, despite having no prior coding experience, to go all the way from detailed spec to live feature for the smaller stuff.

## specs-are-the-new-source-code#008

Over to Danny…
 Here’s a recent example I worked on. For context, we’re building a product that enables expert influencers to place candidates from their networks into jobs. After shipping a new landing page, we needed to give our experts a quick way of accessing the link to their own page.
 We need a button in the header that directs to the company-apply page. I'm focused on the emails at the moment. This is vibe code-able if you can pick it up please. 
 This was from my co-founder, referring to a simple button that needed to be shipped. Easy enough, and precisely the kind of thing that a non technical person can now ship themselves.
 Here’s the setup and steps for how this got shipped within a couple of minutes:
 Project management tool : Linear

IDE : VS Code

Extension : GitHub Copilot Pro

Model : Claude Sonnet 4

MCP Server : Linear MCP server to allow Linear tickets to be accessed via Copilot

Let’s take a look at the steps in the process (follow along in the Loom video above):
 Generate a Linear ticket out of the Slack message from my co-founder (00:14)

Clarify what I want the new copy to be in the ticket above (00:25)

## specs-are-the-new-source-code#009

Open up Copilot and prompt Claude to open up the Linear ticket (01:18)

Prompt Claude to review the ticket and analyse it relative to the codebase (01:52)

Prompt Claude to create a branch and implement these changes (02:30)

Test the changes to ensure they’re working as expected. (02:52)

Open a pull request (PR) on GitHub to ship these changes into the codebase (03:55)

Wait for an engineer to review/approve the PR

Zooming out, the true power of this setup comes into focus. Yes, this is a trivial example, but the point remains: a non-technical person can now go between Linear tickets, a codebase, and an engineer, all with a couple of prompts to Claude via GitHub Copilot.
 And again, the critical part of all of this isn’t the code itself: it’s the spec.
 Now, it’s important to caveat the above with what’s needed for it to work well:
 Being specific : Using vague specs will only result in a messy codebase. Using Claude to take an initial draft of a ticket, review the codebase, and help make it more specific is an essential part of the process. In our case, we also have guidelines for writing a good spec.

## specs-are-the-new-source-code#010

Being selective : Using the above for simpler tasks is ideal. The more complex the ticket, the greater the need for someone who knows what they’re doing to get involved (“self-serve” ends up being anything but, in these cases).

Gatekeeping : This approach only works well because there’s an actual engineer who knows what they’re doing, reviewing changes and ensuring the balance between simplicity and functionality is maintained.

## specs-are-the-new-source-code#011

But let’s be clear: the rules have changed. Specs are the source of truth for everyone building the product, including the LLM.
 With the proper setup, it is entirely realistic to expect to be contributing to a codebase as a non-technical person. With enough time and patience, you can start to understand the codebase and implement changes yourself, rather than simply relying on Claude to bail you out every time.
 One day, you might even expect an AI agent to ship your ticket whilst you sip your coffee.
 If you’re a PM and worried about what AI is going to do to your job, the key is to realize that the job itself is changing. But that’s also the case for everyone else. The great thing is that the core skills required for an excellent PM are even more valuable in this new world.
 As we predicted in a previous post , the companies that are working in this way will need more, not fewer PMs. And it turns out that prediction is working out rather well:

## specs-are-the-new-source-code#012

## Long live the spec! 
 William Gibson, the science fiction writer who coined the phrase “cyberspace,” once said:
 The future is already here—it’s just not very evenly distributed.
 I’m reminded of this when I think about what is and is not possible with AI. Today, AI's gains are profoundly uneven. Some things—generating code, text, images—have made quantum leaps. They operate at AI speed . Other things—talking to customers, discovering their needs, convincing them to buy—still move at human speed . 
 This uneven distribution is reshaping product teams. The spotlight is shifting from implementation work to understanding work. The core skills that have always set apart the best PMs—understanding user needs, defining problems clearly, designing elegant solutions—have become exponentially more valuable.
 The best PMs turn those insights into specs—specifications that align teams, guide implementation, and serve as the lasting artifact in an increasingly automated development world.
 Thanks for reading Ravi on Product! Subscribe for free to receive new posts and support my work.

58
 
 16
 8
 
 Share

A guest post by
 Danny Martinez 
 ✍️ Writing about hiring 
 Subscribe to Danny

## sre-introduction#001

## 
 Chapter 1 - Introduction

Table of Contents

Foreword

Preface

Part I - Introduction

1. Introduction

2. The Production Environment at Google, from the Viewpoint of an SRE

Part II - Principles

3. Embracing Risk

4. Service Level Objectives

5. Eliminating Toil

6. Monitoring Distributed Systems

7. The Evolution of Automation at Google

8. Release Engineering

9. Simplicity

Part III - Practices

10. Practical Alerting

11. Being On-Call

12. Effective Troubleshooting

13. Emergency Response

14. Managing Incidents

15. Postmortem Culture: Learning from Failure

16. Tracking Outages

17. Testing for Reliability

18. Software Engineering in SRE

19. Load Balancing at the Frontend

20. Load Balancing in the Datacenter

21. Handling Overload

22. Addressing Cascading Failures

23. Managing Critical State: Distributed Consensus for Reliability

24. Distributed Periodic Scheduling with Cron

25. Data Processing Pipelines

26. Data Integrity: What You Read Is What You Wrote

27. Reliable Product Launches at Scale

Part IV - Management

28. Accelerating SREs to On-Call and Beyond

29. Dealing with Interrupts

30. Embedding an SRE to Recover from Operational Overload

31. Communication and Collaboration in SRE

32. The Evolving SRE Engagement Model

## sre-introduction#002

Part V - Conclusions

33. Lessons Learned from Other Industries

34. Conclusion

Appendix A. Availability Table

Appendix B. A Collection of Best Practices for Production Services

Appendix C. Example Incident State Document

Appendix D. Example Postmortem

Appendix E. Launch Coordination Checklist

Appendix F. Example Production Meeting Minutes

Bibliography

## Introduction

Written by Benjamin Treynor Sloss 6 
Edited by Betsy Beyer

Hope is not a strategy.

Traditional SRE saying

It is a truth universally acknowledged that systems do not run themselves. How, then, should a systemâparticularly a complex computing system that operates at a large scaleâbe run?

# The Sysadmin Approach to Service Management

Historically, companies have employed systems administrators to run complex computing systems.

## sre-introduction#003

This systems administrator, or sysadmin, approach involves assembling existing software components and deploying them to work together to produce a service. Sysadmins are then tasked with running the service and responding to events and updates as they occur. As the system grows in complexity and traffic volume, generating a corresponding increase in events and updates, the sysadmin team grows to absorb the additional work. Because the sysadmin role requires a markedly different skill set than that required of a productâs developers, developers and sysadmins are divided into discrete teams: "development" and "operations" or "ops."

The sysadmin model of service management has several advantages. For companies deciding how to run and staff a service, this approach is relatively easy to implement: as a familiar industry paradigm, there are many examples from which to learn and emulate. A relevant talent pool is already widely available. An array of existing tools, software components (off the shelf or otherwise), and integration companies are available to help run those assembled systems, so a novice sysadmin team doesnât have to reinvent the wheel and design a system from scratch.

## sre-introduction#004

The sysadmin approach and the accompanying development/ops split has a number of disadvantages and pitfalls. These fall broadly into two categories: direct costs and indirect costs.

Direct costs are neither subtle nor ambiguous. Running a service with a team that relies on manual intervention for both change management and event handling becomes expensive as the service and/or traffic to the service grows, because the size of the team necessarily scales with the load generated by the system.

The indirect costs of the development/ops split can be subtle, but are often more expensive to the organization than the direct costs. These costs arise from the fact that the two teams are quite different in background, skill set, and incentives. They use different vocabulary to describe situations; they carry different assumptions about both risk and possibilities for technical solutions; they have different assumptions about the target level of product stability. The split between the groups can easily become one of not just incentives, but also communication, goals, and eventually, trust and respect. This outcome is a pathology.

## sre-introduction#005

Traditional operations teams and their counterparts in product development thus often end up in conflict, most visibly over how quickly software can be released to production. At their core, the development teams want to launch new features and see them adopted by users. At their core, the ops teams want to make sure the service doesnât break while they are holding the pager. Because most outages are caused by some kind of changeâa new configuration, a new feature launch, or a new type of user trafficâthe two teamsâ goals are fundamentally in tension.

## sre-introduction#006

Both groups understand that it is unacceptable to state their interests in the baldest possible terms ("We want to launch anything, any time, without hindrance" versus "We wonât want to ever change anything in the system once it works"). And because their vocabulary and risk assumptions differ, both groups often resort to a familiar form of trench warfare to advance their interests. The ops team attempts to safeguard the running system against the risk of change by introducing launch and change gates. For example, launch reviews may contain an explicit check for every problem that has ever caused an outage in the pastâthat could be an arbitrarily long list, with not all elements providing equal value. The dev team quickly learns how to respond. They have fewer "launches" and more "flag flips," "incremental updates," or "cherrypicks." They adopt tactics such as sharding the product so that fewer features are subject to the launch review.

# Googleâs Approach to Service Management: Site Reliability Engineering

## sre-introduction#007

Conflict isnât an inevitable part of offering a software service. Google has chosen to run our systems with a different approach: our Site Reliability Engineering teams focus on hiring software engineers to run our products and to create systems to accomplish the work that would otherwise be performed, often manually, by sysadmins .

What exactly is Site Reliability Engineering, as it has come to be defined at Google? My explanation is simple: SRE is what happens when you ask a software engineer to design an operations team. When I joined Google in 2003 and was tasked with running a "Production Team" of seven engineers, my entire life up to that point had been software engineering. So I designed and managed the group the way I would want it to work if I worked as an SRE myself. That group has since matured to become Googleâs present-day SRE team, which remains true to its origins as envisioned by a lifelong software engineer.

A primary building block of Googleâs approach to service management is the composition of each SRE team. As a whole, SREs can be broken down into two main categories.

## sre-introduction#008

50â60% are Google Software Engineers, or more precisely, people who have been hired via the standard procedure for Google Software
 Engineers. The other 40â50% are candidates who were very close to the Google Software Engineering qualifications (i.e., 85â99% of the skill set required), and who in addition had a set of technical skills that is useful to SRE but is rare for most software engineers. By far, UNIX system internals and networking (Layer 1 to Layer 3) expertise are the two most common types of alternate technical skills we seek.

Common to all SREs is the belief in and aptitude for developing software systems to solve complex problems. Within SRE, we track the career progress of both groups closely, and have to date found no practical difference in performance between engineers from the two tracks. In fact, the somewhat diverse background of the SRE team frequently results in clever, high-quality systems that are clearly the product of the synthesis of several skill sets.

## sre-introduction#009

The result of our approach to hiring for SRE is that we end up with a team of people who (a) will quickly become bored by performing tasks by hand, and (b) have the skill set necessary to write software to replace their previously manual work, even when the solution is complicated. SREs also end up sharing academic and intellectual background with the rest of the development organization. Therefore, SRE is fundamentally doing work that has historically been done by an operations team, but using engineers with software expertise, and banking on the fact that these engineers are inherently both predisposed to, and have the ability to, design and implement automation with software to replace human labor.

By design, it is crucial that SRE teams are focused on engineering. Without constant engineering, operations load increases and teams will need more people just to keep pace with the workload. Eventually, a traditional ops-focused group scales linearly with service size: if the products supported by the service succeed, the operational load will grow with traffic. That means hiring more people to do the same tasks over and over again.
