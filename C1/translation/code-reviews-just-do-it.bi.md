# code-reviews-just-do-it（中英对照）

### seg 001

In Humanizing Peer Reviews , Karl Wiegers starts with a powerful pronouncement:
 Peer review – an activity in which people other than the author of a software deliverable examine it for defects and improvement opportunities – is one of the most powerful software quality tools available. Peer review methods include inspections, walkthroughs, peer desk checks, and other similar activities. After experiencing the benefits of peer reviews for nearly fifteen years, I would never work in a team that did not perform them. After participating in code reviews for a while here at Vertigo, I believe that peer code reviews are the single biggest thing you can do to improve your code. If you’re not doing code reviews right now with another developer, you’re missing a lot of bugs in your code and cheating yourself out of some key professional development opportunities. As far as I’m concerned, my code isn’t done until I’ve gone over it with a fellow developer.
 But don’t take my word for it. McConnell provides plenty of evidence for the efficacy of code reviews in Code Complete :

> 在《Humanizing Peer Reviews》一文中，Karl Wiegers 开篇就给出了一个有力的论断：
> 
> 同行评审（peer review）——由软件交付物作者之外的人对其进行检查，以发现缺陷与改进机会的活动——是现有最强大的软件质量工具之一。同行评审的方法包括审查（inspections）、走查（walkthroughs）、同行桌面检查（peer desk checks）以及其他类似活动。在亲身受益于同行评审近十五年之后，我绝不会在一个不做同行评审的团队里工作。在 Vertigo 参与了一段时间代码评审之后，我相信同行的代码评审是你能为改进代码所做的最大的一件事。如果你现在没有和另一位开发者一起做代码评审，那你的代码里正遗漏大量缺陷，也白白错过了一些关键的职业成长机会。就我而言，在没有和一位开发者同伴一起过一遍之前，我的代码就不算完成。
> 
> 但请别只听我的一面之词。McConnell 在《Code Complete》中为代码评审的有效性提供了大量证据：

### seg 002

… software testing alone has limited effectiveness – the average defect detection rate is only 25 percent for unit testing, 35 percent for function testing, and 45 percent for integration testing. In contrast, the average effectiveness of design and code inspections are 55 and 60 percent . Case studies of review results have been impressive:

In a software-maintenance organization, 55 percent of one-line maintenance changes were in error before code reviews were introduced. After reviews were introduced, only 2 percent of the changes were in error. When all changes were considered, 95 percent were correct the first time after reviews were introduced. Before reviews were introduced, under 20 percent were correct the first time.

In a group of 11 programs developed by the same group of people, the first 5 were developed without reviews. The remaining 6 were developed with reviews. After all the programs were released to production, the first 5 had an average of 4.5 errors per 100 lines of code. The 6 that had been inspected had an average of only 0.82 errors per 100. Reviews cut the errors by over 80 percent.

> ……软件测试本身的效果是有限的——平均缺陷检出率在单元测试中只有 25%，功能测试为 35%，集成测试为 45%。相比之下，设计审查与代码审查的平均有效性分别为 55% 和 60%。评审结果的案例研究令人印象深刻：
> 
> 在一家软件维护机构中，引入代码评审之前，55% 的单行维护改动是有错误的。引入评审之后，只有 2% 的改动存在错误。就全部改动而言，引入评审后 95% 的改动一次就正确；而在引入评审之前，一次正确的不足 20%。
> 
> 在一组由同一批人开发的 11 个程序中，前 5 个在没有评审的情况下开发，其余 6 个在评审参与下开发。所有程序发布到生产环境后，前 5 个平均每 100 行代码有 4.5 个错误，而经过审查的 6 个平均只有 0.82 个。评审把错误减少了 80% 以上。

### seg 003

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

> Aetna 保险公司通过审查发现了程序中 82% 的错误，并因此把开发资源减少了 20%。
> 
> IBM 的 50 万行 Orbit 项目采用了 11 级审查。它提前交付，且错误大约只有通常预期水平的 1%。
> 
> 一项针对 AT&T 内部一个 200 多人组织的研究报告称，该组织引入评审后，生产率提高了 14%，缺陷下降了 90%。
> 
> 喷气推进实验室（Jet Propulsion Laboratories）估计，通过尽早发现并修复缺陷，每次审查可节省约 25,000 美元。
> 
> 代码评审唯一的门槛，是找到一位你尊重的开发者来做这件事，并抽出时间执行评审。一旦开始，我想你很快就会明白：你在代码评审上花的每一分钟，都会以十倍的回报还给你。
> 
> 如果你的组织对代码评审还很陌生，我强烈推荐 Karl 的《Peer Reviews in Software: A Practical Guide》。他在自己网站上提供的样章也是非常好的入门材料。
> 
> 软件开发 / 代码评审 / 同行评审 / 代码质量 / 职业发展

