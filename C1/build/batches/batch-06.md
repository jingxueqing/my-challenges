# 待译批次 06

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## code-review-essentials#002

The most critical function of a Code Review is to keep every member of
the team moving in the right direction. You can’t safetly change a
system you don’t understand, and so Code Review keeps the team
mentally aligned together. When Bob submits a pull request for the
accounting subsystem, Amy keeps her mental model of that system
updated as she reviews Bob’s code. Amy gets the chance to ask
questions about pieces she doesn’t understand, and Bob gets the
benefit of clarifying his design decisions as well as teaching someone
else about his work. When Amy has to make a change to the accounting
subsystem a month later, her mental model of the system is already up
to date and ready for action. She spends less time reading code and
trying to piece the system together in her brain, and more time
thinking about higher level abstractions and designs. Everyone wins,
because everyone stays together.

## Executing a Good Pull Request

Before you even write a line of code changing the system, ask yourself the following
questions:

## code-review-essentials#003

“Is this the right thing to be working on?” There will always be
 competing needs from customers, internal team members and other
 parties. This can be a good way to keep priorities straight in your
 head before you dive in deep. Other processes like iteration /
 sprint planning meetings also help keep this on track.

“Does the team already agree that the change is the right one?” If
not, it’d be better to start a design discussion by email or maybe
in person. Your changes are more likely to get accepted when people
are in agreement about the design before you change it.

“How can I break this change into digestable chunks that are easy to
review and understand?” Small changes are easier to think about and
understand. Good discussions flow from the team being able to
comprehend your change quickly. If your change is massive,
teammate’s eyes will glaze over, and you might only get a few style
nitpicks from them.

## code-review-essentials#004

“How am I going to test this change to kill bugs and ensure
correctness?” You might have a QA department, but it’s still your
job as the developer to ship quality working software. Easily
testable software is usually more decoupled, is broken into smaller
chunks, and easier to reason about. You need to have a testing plan
for all your changes.

I’ve found that answering these questions ahead of time has saved me a
lot of headache in the long run. The last thing you want to do is
spend days coding up a change only to have it rejected based on
fundamental design flaws or team disagreement. Or for your change to
get held up because no one can verify it for correctness. Again, the
goal is to change the system while keeping other team members up to
date with your changes. Asking yourself about how you’re going to
break your work into bite-sized chunks and test those chunks is
helpful on many fronts:

It reduces risk

It makes changes easier to reason about

It pushes you towards a better design

## code-review-essentials#005

You’d rather make many small, precise cuts with a scalpel than one
giant gash with a machete. I prefer scalpel driven developement in
most additive cases, and like to save the machete for when it’s time
to delete large blocks of dead code.

## Sending the Pull Request

Ok, so you’ve gotten buy-in from the team that your changes are good,
and you’ve achieved the design you set out to build. What’s the most
effective way to actually send your pull request? You’ve been working
hard on your changes, and you want other members of your team to pay
attention to your pull request and give you fast feedback. How can you
do that?

## code-review-essentials#006

Remember earlier when I said that the most important part of a code
review is to keep the team’s collective mental model well aligned?
Your other teammates are probably working on something completely
different than you, maybe in a completely different part of the
system. Their brains are in a completely different context, so you
must overcome this by giving them the helpful guidance they need to do
the review. This means writing a well-organized description of the
changes you made, why you made them and any other relevant information
they won’t get from just reading the code alone. Don’t make your
teammates do more mental work than they have to.

Let’s look at some good and bad examples of pull request descriptions:

Bad Example:

Title: Fix uninitialized memory bug
Description:

This is the bug Bob and I talked about earlier. I had
trouble with the compiler but managed to make this work. Let me
know what you guys think.

## code-review-essentials#007

If you’re the developer of this pull request, stop and put yourself in
your code reviewer’s shoes for a second. The title is vague, and
raises more questions than answers: Where is the memory bug? How
critical is this change? What was the bug that Bob and you talked
about earlier? What trouble did you have with the compiler? The
description doesn’t provide any helpful context about the problem, nor
does it provide any helpful description of your changes. If this pull
request is long, the reviewer is going to have to dive into the code
and do mental gymnastics in an attempt to gain context before even
getting a chance to think about how this change fits in to the
coherent design of the system.

Here’s a improved example that helps clarify the changeset:

Title: Fix process crash on startup from uninitialized memory [#54633]
Description:

This bug was causing process crashes on boot due to a memory
initialization error in our statistics Counter class. I talked this
over with Bob, and we both agree the crashes are a rare edge case
that don't warrant a hot-fix release. Here's a summary of the
changes:

## code-review-essentials#008

- Moved the underlying int variable into the class initializer
 to prevent ununitialized memory in the Counter.
 - Reworked the Counter interface to simplify caller conditional
 logic and prevent further off-by-one counting problems.
 - Added a unit test that exposes the crash

Testing: I've verified the test suite still passes, and verified
manually that the crash doesn't happen locally.

## code-review-essentials#009

A few things that have improved in this pull request description: The
title is descriptive enough to give the reviewer some short context,
and entice them to click on the email and learn more. The reviewer
knows it’s a process crash (which is usually a really bad thing) and
there’s also a bug report number where the reviewer can read more
details about the bug report if they’re interested in understand more
about the problem. The new description also outlines where the problem
was occuring, and helps give some context about how critical the fix
is. There’s a summary that lists the high level structural changes in
the pull request, which will give the reviewer a mental picture of the
changes before they even look at the code. Code reviewers should not
be surprised with what they find. This example also outlines testing
that was performed, which will give reviewers confidence that the
changes were well thought out, well tested and ready to be merged. Set
your reviewers up for success by making it stupid easy for them to
click ‘merge’.

## Reviewers: Giving Constructive Feedback

## code-review-essentials#010

The next part of the review process to consider is giving constructive
feedback to your peers. If the goal is clarity and alignment, giving
quality constructive feedback helps everyone understand the system
better and push towards better code.

Avoid saying things like:

“This design is broken.” Why is it broken? How can it be made
 better? Statements like this hurt confidence and can bruise egos.

“I don’t like this change.” Why don’t you like it? What would you
 like instead? It’s okay to not like something, but you should
 articulate your thoughts and provide helpful clues about how the
 code can be improved.

“Can you rewrite this to be more clear?” What’s wrong with what
 I have now? How should I rewrite it? What’s unclear? Comments
 like this are themselves unclear, and don’t give a simple path
 forward.

Instead, say things like:

## code-review-essentials#011

“How does this code handle negative integers?” This feedback is
 specific, and causes the developer to think through the outcomes
 themselves. As a reviewer, you might know that the code in
 question crashes with negative integers, but it’s better to have
 the developer intuit this themselves. Questions like this might
 also be indicative of a testing gap, or a need for further
 specification of scope.

“This section is confusing to me, I don’t understand why class A
 is talking to class B” If the developer hasn’t provided a helpful
 description, and the code isn’t neatly structured, this kind of
 comment helps drive for clarity of design and cleaner code.

“It looks like you broke an interface boundary here. How will
 that affect the user?” You’ve pointed out an issue you noticed,
 giving them the benefit of the doubt that they meant to do it. Now
 they can think through the unseen ramifications of breaking the
 interface boundary and either provide a rationale for their
 decision, or choose to change it.

## code-review-essentials#012

In general, framing feedback as questions is a good way to drive for
clarity, correctness, and at the same time help the developer improve
their designs in the future. This is usually how quality creative
writing groups give each other feedback. In a creative writing
setting, it’s harmful to say things like, “I don’t like this
character.” whereas the same comment can be reframed more clearly: “In
chapter one your character was warm and compassionate and now he’s
cold and icey. He doesn’t seem like a real person to me.” Now there’s
specific feedback that can be clarified to suss out the problem.

Programmers like to solve problems and point out issues, so by nature
they like to discover and point out flaws. It’s tempting to see code
reviews as a way to prove how smart you are by finding problems in
your peer’s code. Don’t do it. Code review is a way to get more eyes
on a change and suss out critical problems, but your goal should be to
review in a way that encourages your team members to improve their
skills while fixing the problems at hand.

## Style Points

## code-review-essentials#013

Brace positions, variable / function names, indentation and spacing
issues should be addressed, but they are not the central purpose of
good code review (notice that I put them at the top the code
review pyramid). If you find that your team is spending 90% of it’s
time nitpicking indentation and variable names, you’re probably
wasting everyone’s time on something that could be mostly automated.
Write up a style guide, enforce indentation and spacing issues on
check-in and spend your time focusing on higher value issues. I don’t
want to diminish the importance of a consistent style. On the
contrary, having a consistent idiomatic style is one of the easiest
ways to make your codebase easy to read and comprehend. Still, if you
spend all of your code review focused on these simplistic tasks, ask
yourself whether you’re avoiding the harder and more important work of
keeping your team mentally aligned and thinking about higher level
designs.

more posts

### about the author

Blake Smith is a Principal
 Software Engineer at Sprout
 Social .

## code-reviews-just-do-it#001

In Humanizing Peer Reviews , Karl Wiegers starts with a powerful pronouncement:
 Peer review – an activity in which people other than the author of a software deliverable examine it for defects and improvement opportunities – is one of the most powerful software quality tools available. Peer review methods include inspections, walkthroughs, peer desk checks, and other similar activities. After experiencing the benefits of peer reviews for nearly fifteen years, I would never work in a team that did not perform them. After participating in code reviews for a while here at Vertigo, I believe that peer code reviews are the single biggest thing you can do to improve your code. If you’re not doing code reviews right now with another developer, you’re missing a lot of bugs in your code and cheating yourself out of some key professional development opportunities. As far as I’m concerned, my code isn’t done until I’ve gone over it with a fellow developer.
 But don’t take my word for it. McConnell provides plenty of evidence for the efficacy of code reviews in Code Complete :

## code-reviews-just-do-it#002

… software testing alone has limited effectiveness – the average defect detection rate is only 25 percent for unit testing, 35 percent for function testing, and 45 percent for integration testing. In contrast, the average effectiveness of design and code inspections are 55 and 60 percent . Case studies of review results have been impressive:

In a software-maintenance organization, 55 percent of one-line maintenance changes were in error before code reviews were introduced. After reviews were introduced, only 2 percent of the changes were in error. When all changes were considered, 95 percent were correct the first time after reviews were introduced. Before reviews were introduced, under 20 percent were correct the first time.

In a group of 11 programs developed by the same group of people, the first 5 were developed without reviews. The remaining 6 were developed with reviews. After all the programs were released to production, the first 5 had an average of 4.5 errors per 100 lines of code. The 6 that had been inspected had an average of only 0.82 errors per 100. Reviews cut the errors by over 80 percent.

## code-reviews-just-do-it#003

The Aetna Insurance Company found 82 percent of the errors in a program by using inspections and was able to decrease its development resources by 20 percent.

IBM’s 500,000 line Orbit project used 11 levels of inspections. It was delivered early and had only about 1 percent of the errors that would normally be expected.

A study of an organization at AT&T with more than 200 people reported a 14 percent increase in productivity and a 90 percent decrease in defects after the organization introduced reviews.

Jet Propulsion Laboratories estimates that it saves about $25,000 per inspection by finding and fixing defects at an early stage.

The only hurdle to a code review is finding a developer you respect to do it, and making the time to perform the review. Once you get started, I think you’ll quickly find that every minute you spend in a code review is paid back tenfold.
 If your organization is new to code reviews, I highly recommend Karl’s book, Peer Reviews in Software : A Practical Guide. The sample chapters Karl provides on his website are a great primer, too.

software development 
 code reviews 
 peer reviews 
 code quality 
 professional development

## context-rot#001

Products
 Sync Database Agent 
 Docs Enterprise Pricing Research 
 Resources
 Changelog Updates Community GitHub Package Search 
 Log in Sign up
