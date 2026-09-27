# 待译批次 08

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## context-rot#018

## Results # 
 Even a single distractor reduces performance relative to the baseline (needle only), and adding four distractors compounds this degradation further.
 
 Impact of Distractors: Performance by Number of Distractors - arXiv haystack/PG essay needles We are also able to see that distractors do not have uniform impact. For example, in our arXiv haystack and PG essay needle combination, we can see that distractor 3 (red) causes greater performance decline relative to the other distractors.
 
 Impact of Distractors: Performance by Individual Distractors - arXiv haystack/PG essay needles To further investigate this non-uniform impact, we analyze the failed attempts of various models in the 4-distractor condition. For the arXiv haystack and PG essay needle combination, we see that distractors 2 and 3 appear most frequently in hallucinated responses across models.
 
 Impact of Distractors: Failure Analysis - arXiv haystack/PG essay needles These failures also reveal model-specific differences in handling ambiguity. Claude models consistently exhibit the lowest hallucination rates. Specifically, Claude Sonnet 4 and Opus 4 are particularly conservative and tend to abstain when uncertain, explicitly stating that no answer can be found. In contrast, GPT models show the highest rates of hallucination, often generating confident but incorrect responses when distractors are present.

## context-rot#019

# Needle-Haystack Similarity # 
 In long-context tasks, irrelevant context is often treated as a neutral placeholder to scale up input length. It’s typically assumed that the content of this irrelevant context doesn't matter, as long as it doesn’t directly interfere with the task.
 However, a natural question arises: does the needle-haystack similarity influence task difficulty at all? Intuitively, if the needle blends in with the content of the haystack, the model may have greater difficulty in extracting the needle.
 Our findings reveal that needle-haystack similarity has a non-uniform effect on model performance.

## context-rot#020

## Experiment # 
 Using the needles from our needle-question similarity experiment, we set up our experiment to test the impact of needle-haystack similarity.
 We measure needle-haystack similarity by embedding the haystack and retrieving the top five most similar chunks for each needle, then averaging their cosine similarity scores. This process is repeated across five different embedding models for robustness.
 In the PG essay haystack, PG essay needles have an average needle-haystack similarity score of 0.529 with a variation of 0.101, while arXiv needles average 0.368 needle-haystack similarity with a variation of 0.111. Conversely, in the arXiv haystack, arXiv needles average 0.654 needle-haystack similarity with a variation of 0.0858, whereas PG-essay needles score lower at 0.394 needle-haystack similarity with a variation of 0.105.
 On each haystack, we test semantically similar needles against unrelated needles. For instance, we place both PG essay and arXiv needles within a Paul Graham essay haystack to compare the two conditions:
 
 Needle-Haystack Similarity: Experimental Setup

## context-rot#021

## Results # 
 We test both PG essay and arXiv needles in two haystack types: Paul Graham essays and arXiv papers. In the Paul Graham essay haystack, arXiv needles perform significantly better relative to the PG essay needles; in other words, models perform better when the needle does not semantically blend in with its haystack. In the arXiv haystack, however, we observe only minimal performance differences between our arXiv and PG essay needles.
 
 Needle-Haystack Similarity Results Testing across only two topics is insufficient to draw a generalizable conclusion that higher needle-haystack similarity degrades model performance on this task. This does highlight, however, the non-uniform nature of long-context processing. Even when task structure and needle-question similarity are held constant, changing the semantic similarity between the needle and the haystack can influence results. This points to an underexplored area in long-context benchmarks and a meaningful direction for future research.

## context-rot#022

# Haystack Structure # 
 Aside from needle-haystack similarity, we also consider the structural pattern of the haystack.
 If the haystack is composed of coherent essays, a randomly inserted needle may disrupt the logical flow of ideas, making it more noticeable. In contrast, in a shuffled haystack of randomly ordered sentences, the needle may blend in more easily since the overall context lacks structure. This follows the assumption that models are sensitive to the logical flow of context—processing it in a structured, order-sensitive manner.
 Surprisingly, we find that structural coherence consistently hurts model performance.
 Although it seems counterintuitive, models perform worse when the haystack preserves a logical flow of ideas. Shuffling the haystack and removing local coherence consistently improves performance.

## Experiment # 
 To assess the impact of haystack structure, we create two variants:
 Original: preserves the natural flow of ideas within each excerpt
 Shuffled: sentences are randomly reordered throughout the haystack to maintain the same overall topic but without logical continuity
 
 Haystack Structure: Sample Experimental Setup

## context-rot#023

## Results # 
 Across all 18 models and needle-haystack configurations, we observe a consistent pattern that models perform better on shuffled haystacks than on logically structured ones.
 
 Haystack Structure: Averaged Performance Across 18 Models for Original vs Shuffled Haystacks These results may have some implications for the model’s internal processing: structural patterns of inputs could influence how the attention mechanism is applied, particularly as input length increases.
 While out of scope for this report, this points to a potential direction for interpretability research in how attention is influenced by input structure. Understanding these structural influences that arise with increased input length could help explain these long context failure patterns.

## context-rot#024

# LongMemEval # 
 To evaluate these models in a more realistic setting, we use LongMemEval, a long-context benchmark for conversational question-answering.
 Using long inputs for chat assistants is a common approach for maintaining relevant history for subsequent chats. To incorporate “memory” into a chat assistant, a naive approach would be to include the full chat history into the prompt for following chats. This requires the model to perform two tasks, typically performed in one call: find relevant parts of the conversation history (retrieval), then synthesize them in a way that is useful to an incoming query (reasoning).
 In an ideal case, the model would be given only the relevant parts so it can focus solely on reasoning. Adding irrelevant context adds the additional step of identifying what is relevant, forcing the model to perform two tasks simultaneously.
 We systematically test the effect of adding this additional step with increased input length through two conditions:
 Focused input, containing only the relevant parts and so the model just has to do simple reasoning.

## context-rot#025

Full input, which utilizes the full 113k token LongMemEval input that includes irrelevant context. In this case, the model has to perform retrieval across the long context in addition to reasoning.

We verify that the models are highly capable of succeeding on the focused inputs, then observe consistent performance degradation with the full inputs. This performance drop suggests that adding irrelevant context, and thereby adding an additional step of retrieval, significantly impacts a model’s ability to maintain reliable performance.

## context-rot#026

## Experiment # 
 Given a chat history between a user and assistant, the model’s task is to answer a question relating to part of that chat history.
 
 LongMemEval - Examples by Question Type [[2](#longmemeval-source)] We use LongMemEval_s and filter for tasks that fall under the knowledge update, temporal reasoning, and multi-session categories. We then manually clean this dataset as some questions are too ambiguous and/or can not be answered, filtering out 38 prompts to end up with 306 total prompts. These prompts average out to ~113k tokens.
 These long prompts mostly consist of content irrelevant to the question, and sometimes distractors which may seem relevant to the question. We compare performance of the models on these long prompts to a focused version, which only contains the relevant parts to answer the question.
 Focused prompts average to ~300 tokens, which are derived from the originally labeled dataset and manual adjustments.
 Model outputs were judged using an aligned LLM judge (GPT-4.1 with >99% alignment to human judgment).

## context-rot#027

## Results # 
 Across all models, we see significantly higher performance on focused prompts compared to full prompts.
 
 LongMemEval Results - Claude Family The Claude models exhibit the most pronounced gap between focused and full prompt performance. This discrepancy is largely driven by abstentions that arise with ambiguity, leading to model uncertainty, similar to this model family’s behavior with distractors in NIAH. This behavior is most evident in Claude Opus 4 and Sonnet 4, which appear to be particularly conservative under ambiguity, leading to lower performance on full prompts relative to that of the older Claude models.
 
 Question: How many days passed between the day I attended the gardening workshop and the day I planted the tomato saplings?
 
 Correct Answer: 6 days. 7 days (including the last day) is also acceptable.
 
 Model Output: I cannot determine the number of days between the gardening workshop and planting the tomato saplings becuase the specific dates for these events are not provided in the chat history.
 
 LongMemEval - Claude Sonnet 4 (non-thinking) on full prompt containing the dates The trend of stronger performance on focused prompts holds across the GPT, Gemini, and Qwen model families as well. For models that support thinking modes, we see notable gains on both focused and full prompts when enabled. However, we still see a performance gap between the two input lengths even with full reasoning capabilities on the latest models.
 
 LongMemEval Results - GPT Family 
 LongMemEval Results - Gemini Family 
 LongMemEval Results - Qwen Family We also observe patterns among specific question types. In non-thinking mode, models generally perform best on knowledge-update, followed by multi-session, then temporal reasoning—for both focused and full prompts. However, when thinking is enabled, this ranking shifts to: knowledge update, temporal-reasoning, then multi-session.
 
 LongMemEval Results by Question Type - Claude Opus 4

## context-rot#028

# Repeated Words # 
 Our previous experiments explore how input length alone affects model performance. But what happens when output length scales with input? Since these models are autoregressive, a model’s output also belongs to its input; each token is generated conditionally on the input and generated tokens up to that point.
 Consider a basic program that repeats a string n times—it produces the same output every time. For a task this trivial, we’d expect these models to be just as reliable, and we’d like to treat them as computing systems.
 However, our findings show that even for these straightforward tasks, model performance becomes non-uniform as context length, encompassing both input and output lengths, grows.

## context-rot#029

## Experiment # 
 We design a controlled task in which the model must replicate a sequence of repeated words, with a single unique word inserted at a specific position. The prompt explicitly instructs the model to reproduce the input text exactly.
 One example prompt is:
 
 Simply replicate the following text, output the exact same text: apple apple apple apple apples apple apple apple apple apple apple apple apple apple apple apple apple apple apple apple apple apple apple apple apple
 
 Repeated Words - Sample Prompt Containing 'apple' as the repeated word, and 'apples' as the unique word For a given word combination, we create 1090 variations of context lengths and unique word indices:
 Number of words: 25, 50, 75, 100, 250, 500, 750, 1000, 2500, 5000, 7500, 10000
 Index: Every possible position for num_words <= 100
 Else: increments of num_words // 100
 
 We perform this task for the following word combinations:
 Common word: “apple” | unique word: “apples”
 Common word: “apples” | unique word: “apple”
 Common word: “golden” | unique word: “Golden”
 Common word: “orange” | unique word: “run”
 Common word: “orange” | unique word: “San Francisco”
 Common word: “San Francisco” | unique word: “sf”
 Common word: “Golden Gate Bridge” | unique word: “Golden Gate Park”
 Note: “San Francisco” = 1 word, “Golden Gate Bridge/Park” = 1 word 
 Model configurations:
 max_output_tokens = input_tokens *2 (up to model’s maximum output token limit, which is typically lower for older models)
 temperature = 0
 thinking = max(0, minimum_thinking_budget)
 We account for reasoning models by either setting their thinking budgets to 0 or the minimum value, such as 128 tokens for Gemini 2.5 Pro. We exclude OpenAI’s o3 as it does not support token-based thinking budgets and cannot be configured with a fixed output length, which is essential for maintaining consistency across evaluations.
 Scores are calculated by normalized Levenshtein distance.
 We encounter cases of models not attempting the task, which we determine by:
 Empty outputs with a stop reason (i.e. finish_reason='content_filter’ for GPT-3.5 turbo)

## context-rot#030

Non-empty outputs, but with invalid outputs:

Pure observations with no attempt:

## context-rot#031

I notice there's a discrepancy in the text. The word "apples" appears once in the original text (instead of "apple"), located in what appears to be around line 89 or 90 of the text block. Since you asked me to replicate the exact same text, I should point out this difference. Would you like me to:
 Replicate it exactly as shown (with the one instance of "apples")
 Correct it to "apple" to match the pattern
 Simply proceed with replicating it exactly as is Please let me know how you'd like me to proceed.
 
 Repeated Words - Claude Opus 4 output Refusals to answer:
 
 I’m sorry, but I can’t help with that
 
 Repeated Words - GPT-4.1 output Random outputs:
 
 -\n-\n--\n-\n-\n-\n-\n-\n-\n-\n-\n-\n-\n-\n-...
 
 Repeated Words - Gemini 2.5 Pro output We exclude such cases, and separately note the percentage of refusals and common patterns in our results. We only include cases in which the task was attempted, including cases with starting phrases such as:
 
 I notice there's a discrepancy in the text. At one point, "apple" changes to "apples" (with an 's'). I'll replicate the text exactly as provided:
 
 apple apple apple apple apple apple apple apple apple...
 
 Repeated Words - Claude Opus 4 output With these instances, we use the same scoring process to slightly penalize the model for not following exact instructions.
 We exclude GPT-3.5 turbo entirely since the model refused to generate an output for 60.29% of tasks due to finish_reason='content_filter’.
 We analyze outputs along several dimensions:
 Normalized Levenshtein distance

## context-rot#032

Presence and position of unique word
 Correct: Unique word is present and appears at the correct index
 Incorrect position: Unique word appears, but at the wrong index
 
 Word count difference (number of words in input - number of words generated)

## context-rot#033

## Results # 
 As context length increases, performance consistently degrades across all models. In this experiment, input length is directly proportional to output length, unlike our previous tests in which output length remained relatively fixed at a short length. This setting allows us to assess the models’ ability to reliably reproduce long sequences.
 We also observe patterns where models do not attempt the task, which appears across all model families.
 
 Repeated Words - Claude Family We observe that Sonnet 3.5 (red) outperforms the newer Claude models up to its maximum output token count of 8192. Opus 4 (blue), while exhibiting the slowest degradation rate, is also the only model in this family to refuse the task (2.89% of attempts).
 A common pattern with Opus 4 is that the model makes an observation before deciding whether to proceed, followed by an attempt or no attempt. This behavior typically arises starting from 2500 words.
 There are also cases where Opus 4 simply refuses to attempt the task due to:
 Risk of generating copyrighted material
 
 I can't replicate that exact text as requested. While it appears to be just a repetition of "San Francisco," I should avoid reproducing text verbatim when asked to do so, as this could potentially be used to test if I would reproduce copyrighted material in other contexts.
 
 Instead, I can tell you that the text contains "sf" followed by the phrase "San Francisco" repeated 24 times.
 
 Repeated Words - Claude Opus 4 output Inconsistencies in the repeated sequence
 
 I notice there's an error in the text you provided. In one instance, "San Francisco" appears as "San Francisco sf San Francisco" (with an extra "sf" in the middle). Since you asked me to replicate the exact text, I cannot provide a perfect replication as the source contains this inconsistency.
 
 The text consists of "San Francisco" repeated many times, but with that one error embedded within it.
 
 Repeated Words - Claude Opus 4 output We also measure the position accuracy: whether the unique word appears in the correct position. Accuracy is highest when the unique word is placed near the beginning of the sequence, especially as input length increases.
 
 Repeated Words: Position Accuracy - Claude Family Additionally, as context length increases, models often generate the repeated word until reaching the output token limit. We quantify this by computing the difference between input and output word counts:
 Positive = model under-generated
 Negative = model over-generated
 
 Repeated Words: Word Count Difference - Claude Family In the GPT model family, we observe a refusal rate of 2.55% for GPT-4.1. These refusals would typically start around 2500 words, with responses such as “I’m sorry, but I can’t help with that”.
 
 Repeated Words - GPT Family We also observe a local performance peak around 500 words for GPT-4 turbo. Between 50 and 250 words, the model tends to overgenerate (repeating the common word to the output limit), but at 500 words it becomes more accurate in word count. Beyond this point, however, it begins to undergenerate, as seen in the positive difference between input and output word counts.
 
 Repeated Words: Word Count Difference - GPT-4 Turbo Position accuracy follows a similar trend as GPT models are also more likely to place the unique word correctly when it appears early in the input.
 We also note more model-specific behavior in this family.
 GPT-4.1 mini attempts all tasks, but sometimes generates random words for the “Golden Gate Bridge”/”Golden Gate Park” combination. A random output is defined as a word, or a sequence of words, that is not present in the input.
 The model outputs duplicate words, such as “Golden Golden” and “Gate Gate”, which are not present in the input (which only includes “Golden Gate Bridge” and ”Golden Gate Park”).
 These duplicate words do not appear at the position of the unique word, but instead at a later position in the text.
 GPT-4.1 nano exhibits similar behavior on the “San Francisco” / “sf” pair, occasionally outputting lowercase "san"s.
 
 Snippet from Model Output:
 San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco san Francisco san Francisco san Francisco san Francisco
 
 Corresponding Portion from Gold Reference:
 San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco San Francisco
 
 Repeated Words - GPT-4.1 nano With these random words, we notice hints of structure with regards to position. We observe correlations between the position of the unique word and where random words start to appear, which may be a direction for future investigation.
 GPT-4 Turbo has the most variable outputs in this family, meaning that the model has a greater tendency to generate random outputs and a more diverse set of them.
 
 Repeated Words - Gemini Family Generally, we see a performance degradation across models as context length increases. With Gemini 2.5 Pro (blue), we observe a lower starting point because at 50 words, the model generates less words than it should.
 Across all word combinations and models in this family—except Gemini 2.5 Flash on “apples” / “apple”—we observe random words generated which are not present in the input. This typically starts around 500-750 words, with Gemini 2.5 Pro showing the greatest variability, followed by 2.0 Flash, then 2.5 Flash.
 
 "golden" | "Golden" (2,500 words):
 - - "I'-a-le-le-le-le-le-le-'a-le-le-le-le-le-le-le--le-le-le-le-le-le-le...
 
 "orange" | "run" (10,000 words):
 orange orange orange--g.-g/2021/01/20/orange-county-california-sheriff-deputies-wore...
 
 Repeated Words - Gemini 2.5 Pro Sample Outputs 
 Repeated Words - Qwen Family We only observe non-attempts with Qwen3-8B, with make up 4.21% of tasks. With this model, we observe random outputs starting from around 5000 words:
 
 Okay, I'm going to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and get some fresh air. Maybe go to the beach, or just chill out somewhere. I don't know, but I need to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and get some fresh air. Maybe go to the beach, or just chill out somewhere. I don't know, but I need to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and get some fresh air. Maybe go to the beach, or just chill out somewhere. I don't know, but I need to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and get some fresh air. Maybe go to the beach, or just chill out somewhere. I don't know, but I need to take a break. Let me know, I'm not in the mood. I need to chill out. I'm going to go somewhere and...
 
 Repeated Words - Qwen3-8B Output on 'golden' | 'Golden' (5,000 words)
