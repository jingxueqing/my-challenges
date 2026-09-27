# 待译批次 09

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## context-rot#034

# Limitations & Future Work # 
 Our experiments demonstrate that LLMs exhibit inconsistent performance across context lengths, even for simple tasks. However, this evaluation is not exhaustive of real-world use cases. In practice, long context applications are often far more complex, requiring synthesis or multi-step reasoning. Based on our findings, we would expect performance degradation to be even more severe under those conditions.
 Our results have implications for future work on long context evaluations as well. A common limitation, also noted in prior work on long context benchmarks, is the tendency to conflate input length with task difficulty, as longer inputs often introduce more complex reasoning. We focus our experiments to isolate input length as a factor and maintain task difficulty as a constant. An important direction for future work is to disentangle how much of a model’s performance degradation stems from the intrinsic difficulty of the task itself versus its ability to effectively handle long contexts.
 We also do not explain the mechanisms behind this performance degradation. Our observations suggest that structural properties of the context, such as the placement or repetition of relevant information, can influence model behavior, however we do not have a definitive answer for why that occurs. Investigating these effects would require a deeper investigation into mechanistic interpretability, which is beyond the scope of this report.
 More broadly, our findings point to the importance of context engineering: the careful construction and management of a model’s context window. Where and how information is presented in a model’s context strongly influences task performance, making this a meaningful direction of future work for optimizing model performance.

## context-rot#035

# Conclusion # 
 Through our experiments, we demonstrate that LLMs do not maintain consistent performance across input lengths. Even on tasks as simple as non-lexical retrieval or text replication, we see increasing non-uniformity in performance as input length grows.
 Our results highlight the need for more rigorous long-context evaluation beyond current benchmarks, as well as the importance of context engineering. Whether relevant information is present in a model’s context is not all that matters; what matters more is how that information is presented. We demonstrate that even the most capable models are sensitive to this, making effective context engineering essential for reliable performance.

# Footnotes # 
 [1] (July 16, 2025) Latent List insights added and clarifications made by Kiran Vodrahalli (Google Deepmind)
 [2] Original source for examples: https://arxiv.org/pdf/2410.10813

## context-rot#036

# References # 
 [1] Kamradt, G. (2023). Needle In A Haystack - Pressure Testing LLMs [GitHub Repository]. Link 
 [2] Wu, D., Wang, H., Yu, W., Zhang, Y., Chang, K.-W., and Yu, D. (2025). LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory. arXiv preprint arXiv:2410.10813. Link 
 [3] Gemini Team, Georgiev, P., Lei, V. I., Burnell, R., Bai, L., Gulati, A., Tanzer, G., Vincent, D., Pan, Z., Wang, S., et al. (2024). Gemini 1.5: Unlocking multimodal understanding across millions of tokens of context. arXiv preprint arXiv:2403.05530. Link 
 [4] OpenAI, Kumar, A., Yu, J., Hallman, J., Pokrass, M., Goucher, A., Ganesh, A., Cheng, B., McKinzie, B., Zhang, B., Koch, C., et al. (2025). Introducing GPT-4.1 in the API. Link 
 [5] Meta AI, (2025). The Llama 4 herd: The beginning of a new era of natively multimodal AI innovation. Link 
 [6] Modarressi, A., Deilamsalehy, H., Dernoncourt, F., Bui, T., Rossi, R. A., Yoon, S., and Schütze, H. (2025). NoLiMa: Long-Context Evaluation Beyond Literal Matching. arXiv preprint arXiv:2502.05167. Link 
 [7] Fu, H. Y., Shrivastava, A., Moore, J., West, P., Tan, C., and Holtzman, A. (2025). AbsenceBench: Language Models Can't Tell What's Missing. arXiv preprint arXiv:2506.11440. Link 
 [8] Vodrahalli, K., Ontanon, S., Tripuraneni, N., Xu, K., Jain, S., Shivanna, R., Hui, J., Dikkala, N., Kazemi, M., Fatemi, B., et al. (2024). Michelangelo: Long Context Evaluations Beyond Haystacks via Latent Structure Queries. arXiv preprint arXiv:2409.12640. Link 
 [9] openai. (2025). mrcr [Dataset]. Hugging Face. Link 
 [10] openai. (2025). graphwalks [Dataset]. Hugging Face. Link 
 [11] Shi, F., Chen, X., Misra, K., Scales, N., Dohan, D., Chi, E., Schärli, N., and Zhou, D. (2023). Large Language Models Can Be Easily Distracted by Irrelevant Context. arXiv preprint arXiv:2302.00093. Link 
 [12] jamescalam. (2024). ai-arxiv2 [Dataset]. Hugging Face. Link 
 [13] Peng, B., Quesnelle, J., Fan, H., and Shippole, E. (2023). YaRN: Efficient Context Window Extension of Large Language Models. arXiv preprint arXiv:2309.00071. Link 
 [14] McInnes, L., Healy, J., and Melville, J. (2020). UMAP: Uniform Manifold Approximation and Projection for Dimension Reduction. arXiv preprint arXiv:1802.03426. Link 
 [15] Campello, R. J. G. B., Moulavi, D., and Sander, J. (2013). Density-Based Clustering Based on Hierarchical Density Estimates. In Pei, J., Tseng, V. S., Cao, L., Motoda, H., and Xu, G. (Eds.), Advances in Knowledge Discovery and Data Mining (PAKDD 2013), Lecture Notes in Computer Science, vol 7819. Springer, Berlin, Heidelberg. Link

## context-rot#037

# Appendix # 
 Cleaned LongMemEval datasets and needles/distractors used can be downloaded here .

## LLM judge alignment: # 
 We employ LLM judges to evaluate outputs for our NIAH and LongMemEval experiments. These judges are calibrated to human judgment through the following process:
 A subset of model outputs are manually labeled as incorrect/correct (~500 outputs for NIAH, ~600 outputs for LongMemEval)

GPT-4.1 is used to label the same subset of model outputs as incorrect/correct.

An alignment score is calculated by measuring the proportion of human-model aligned judgements.

The prompt is iterated on based on manual inspection of misalignments.

Steps 2-4 are repeated until an alignment score > 0.99 is achieved.

## Models Tested # 
 Not all 18 models are included in each experiement due to context window or thinking_budget constraints.

### Anthropic # 
 Claude Opus 4
 Claude Sonnet 4
 Claude Sonnet 3.7
 Claude Sonnet 3.5
 Claude Haiku 3.5

### OpenAI # 
 o3
 GPT-4.1
 GPT-4.1 mini
 GPT-4.1 nano
 GPT-4o
 GPT-4 Turbo
 GPT-3.5 Turbo

### Google # 
 Gemini 2.5 Pro
 Gemini 2.5 Flash
 Gemini 2.0 Flash

### Alibaba # 
 Qwen3-235B-A22B
 Qwen3-32B
 Qwen3-8B

## context-rot#038

## Embedding Models Used # 
 text-embedding-3-small
 text-embedding-3-large
 jina-embeddings-v3 (input_type='text-matching')
 voyage-3-large (input_type=None)
 all-MiniLM-L6-v2

## Needle-Question Similarity # 
 Note: thinking/non-thinking modes of the same model are treated separately
 
 Needle-Question Similarity - arXiv haystack/PG essay needles 
 Needle-Question Similarity - PG essay haystack/PG essay needles 
 Needle-Question Similarity - PG essay haystack/arXiv needles As mentioned in our Needle-Haystack Similarity results, we note this one occurance in which models perform exceptionally well compared to the other needle-haystack combinations. On its own, it may seem that the high performance models have uniform performance. However, such uniformity for these models does not hold across the rest of the experiments.

## context-rot#039

## Impact of Distractors # 
 
 Impact of Distractors: Performance by Number of Distractors - arXiv haystack/arXiv needles 
 Impact of Distractors: Performance by Individual Distractors - arXiv haystack/arXiv needles 
 Impact of Distractors: Performance by Number of Distractors - PG essay haystack/PG essay needles 
 Impact of Distractors: Performance by Individual Distractors - PG essay haystack/PG essay needles 
 Impact of Distractors: Performance by Number of Distractors - PG essay haystack/arXiv needles 
 Impact of Distractors: Performance by Individual Distractors - PG essay haystack/arXiv needles 
 Impact of Distractors: Failure Analysis - arXiv haystack/arXiv needles 
 Impact of Distractors: Failure Analysis - PG essay haystack/PG essay needles 
 Impact of Distractors: Failure Analysis - PG essay haystack/arXiv needles

## Repeated Words # 
 
 Repeated Words: Position Accuracy - GPT Family 
 Repeated Words: Position Accuracy - Gemini Family 
 Repeated Words: Position Accuracy - Qwen Family 
 Repeated Words: Word Count Difference - GPT Family 
 Repeated Words: Word Count Difference - Gemini Family 
 Repeated Words: Word Count Difference - Qwen Family

© 2026

## context-rot#040

### Product
 Database Sync Enterprise Package Search MCP Docs Status Contact

### Follow
 GitHub X YouTube

### Company
 About Changelog Careers

### Legal
 Privacy Terms Security

## copilot-prompt-injection-rce#001

This post is about an important, but also scary, prompt injection discovery that leads to full system compromise of the developer’s machine in GitHub Copilot and VS Code .

It is achieved by placing Copilot into YOLO mode by modifying the project’s settings.json file.

As described a few days ago with Amp , a vulnerability pattern in agents that might be overlooked is that if an agent can write to files and modify its own configuration or update security-relevant settings it can lead to remote code execution. This is not uncommon and is an area to always look for when performing a security review.

## Background Research

When looking at VS Code and GitHub Copilot Agent Mode I noticed a strange behavior… it can create and write to files in the workspace without user approval.

The edits are immediately persistent, they are not in-memory as a diff to review. The modifications are written to disk right away.

It’s one of these things that as a red teamer you know is probably not good… so I was looking if this could be used to escalate privileges and execute code.

### YOLO Mode

## copilot-prompt-injection-rce#002

So, next I researched features in VS Code that depend on settings that are within the project/workspace folder, and quickly found an interesting one.

It turns out that in the .vscode/settings.json file one can add the following line:

"chat.tools.autoApprove": true

This will put GitHub Copilot in YOLO mode.

And it disables all user confirmations, and we can run shell commands, browse the web, and more!

What is interesting is that this is an experimental feature, but it is still present by default. I did not download a special version or set my VS Code overall into an experimental mode.

Furthermore, it works on Windows, macOS and also Linux.

## Exploit Chain Explained

The proof-of-concept exploit chain to hijack Copilot and escalate privileges is as follows:

The attack starts with a prompt injection planted in a source code file, web page, GitHub issue, tool call response, or other content… The payload can also use invisible text as instructions.

The prompt injection first adds the line “chat.tools.autoApprove”: true, to the ~/.vscode/settings.json file. Folder and file will be created if they don’t exist yet.

GitHub Copilot immediately enters YOLO mode!

## copilot-prompt-injection-rce#003

Attack runs a Terminal command. And using conditional prompt injection we can actually target what to run based on the operating system.

We achieved Remote Code Execution powered by Prompt Injection.

Here is a screenshot that shows the demo file with the prompt injection, the developer interacting with the file on the right side in the chat box, and the calculator popping up!

Of course any other means of prompt injection delivery, like web or data coming back from an MCP server is an attack angle. I just used it inside the source code file because it’s easiest to test with.

## Video Walkthrough

### Short Demos

Here is a demonstration video that shows the code execution on Windows.

And this one on macOS:

### Walkthrough

Here is a longer form video explaining the discovery and exploit in detail:

AI that can set its own permissions and configuration settings is wild!

## Joining the Workstation to a Botnet - ZombAIs

Of course, this means we can join the developer’s machine to a botnet as a ZombAI .

Also, for fun we can modified the settings.json file to switch VS Code into a Red color scheme and similar things.

## copilot-prompt-injection-rce#004

It doesn’t end here though! This also means we can build an actual AI virus that attaches to files and propagates as developers download and interact with infected files.

Last but not least, to demonstrate that we have full control of the developer’s host, we show that Copilot can be hijacked to download malware, and join a remote command and control server.

This means the door is open for malware, ransomware, info stealers, etc.

Scary stuff.

## Building an AI Virus

When seeing this, one will notice that this basically allows the creation of a virus. An attacker can embed instructions and once they gain code execution, additional malware can compromise other Git projects (and RAG sources) to embed the malicious instructions, and commit the changes or even force push them upstream.

This can lead to further spread as other developers unknowingly propagate the infected code.

Finally, we also need to talk about invisible instructions!

## Using Invisible Instructions

## copilot-prompt-injection-rce#005

One might say that it would be quickly discovered if instructions are embedded as comments. So in order to make it a bit more interesting, I went ahead and created an invisible payload that achieves the attack chain, but is not visible to users. This was not as reliable, but it still worked:

Note: Although the demo here with invisible instructions worked multiple times for me, using invisible instructions often leads to the exploit being very unreliable, and is also commonly also refused by the model and there is also typically a visual indicator that VS Code shows about Unicode characters. However, attacks (and models) get better over time. It’s also worth highlighting that not all models are vulnerable to such invisible prompt injection attacks.

## Recommendations and Fix

## copilot-prompt-injection-rce#006

There are actually more attack angles then just the YOLO mode example I shared. When Microsoft asked me if there is any more info I have, I had looked a bit more and noticed there are other problematic places, for instance .vscode/tasks.json that the AI can write to, or adding fake malicious MCP servers, etc which can lead to code execution. And the AI can reconfigure the user interface and configuration settings of the project.

Recently I noticed that developers often use multiple agents, so there is also the threat of overwriting other agent configuration files (allow-list bash commands, add MCP servers…), as they are commonly in the project folder as well.

Ideally, the AI would not be able to modify files without a human first approving it. Many other editors do show the diff, which then can be approved by the developer.

## Responsible Disclosure

After reporting the vulnerability on June 29, 2025 Microsoft confirmed the repro and asked a few follow up questions. A few weeks later MSRC pointed out that it is an issue they were already tracking, and that it will be patched by August. With the August Patch Tuesday release this is now fixed.

## copilot-prompt-injection-rce#007

Shout out to Markus Vervier from Persistent Security who has also identified and reported this vulnerability to Microsoft. You can find their write-up here . And also a shout out to Ari Marzuk who seems to also have discovered it in parallel.

Thanks to the members of the MSRC and product team for the help in getting it mitigated.

## Conclusion

This is another example of how an AI agent might not stay in its box! By modifying its own environment GitHub Copilot can escalate privileges and execute code to compromise the developer’s machine. It’s a not uncommon design flaw in agentic systems as I have discovered.

Keep looking out for such design flaws, these should be easily caught during threat modeling.

Cheers.

## References

Month of AI Bugs 2025

Amp Code: Arbitrary Command Execution via Prompt Injection Fixed

Copilot Settings

CVE-2025-53773: GitHub Copilot and Visual Studio Remote Code Execution Vulnerability

Persistent Security Write-Up

Persistent Security

Newer →

Contact me

← Older

## devin-coding-agents-101#001

Cognition Team June 2025 15 minute read

# Coding Agents 101: The Art of Actually Getting Things Done

The year is 2025. Coding agents aren't magic, but they're about the closest thing we have. We've noticed some engineers, in particular at the senior-to-staff level, finding success faster than others. Here we share some top lessons sourced from the experience of our customers and ourselves.

About this guide:

## Product-agnostic

We discuss tips that will help you be successful with any coding agent.

## Tactical

We offer our favorite bits of actionable advice.

## Technical

While coding agents can be valuable to many, this guide is written with engineers in mind.

## devin-coding-agents-101#002

Developer tooling has been rapidly evolving. Ten years ago, it was autocomplete and intellisense, capable of suggesting method names and carrying out programmatic refactors. Four years ago, it was copilots and tab complete, capable of writing the next couple lines of code for you. Two years ago, it was generative chatbots, capable of assisting your development and generating entire files for you. Today, it is autonomous agents, capable of taking initial descriptions to final pull requests with little human intervention. We've focused on realizing this vision over the past two years by building Devin. Now, interest in autonomous agents is reaching new heights, especially with recent releases of similar products [1] Other than Devin, some recent releases include Codex by OpenAI and Jules by Google. Some local agents like Cursor and Claude Code can be run in parallel workspaces to replicate a similar effect. . These agents can appear in many forms, including web apps, mobile apps, and integrations within popular tools like Slack, GitHub, Linear, and Jira.
