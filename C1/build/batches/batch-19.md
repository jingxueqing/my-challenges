# 待译批次 19

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## owasp-top-ten#017

Builder

Defender

• Previous Version (2021)

• Previous Version (2017)

### Downloads or Social Links

• OWASP Top 10 2017

• Other languages → tab ‘Translation Efforts’

### Social

Twitter

### Code Repository

Github repo

### Leaders

Andrew van der Stock

Brian Glas

Neil Smithline

Tanya Janca

Torsten Gigler

### Upcoming OWASP Global Events

### OWASP News & Opinions

-->

## peeking-under-the-hood-of-claude-code#001

Peeking Under the Hood of Claude Code

# Peeking Under the Hood of Claude Code

This article is hosted on Medium and requires a browser to access.

Original URL: https://medium.com/@outsightai/peeking-under-the-hood-of-claude-code-70f5a94a9a62

Medium blocks automated downloads. Please visit the link above when you have internet access.

## prompt-engineering-guide#001

Prompting Techniques

Copy page

# Prompting Techniques

Prompt Engineering helps to effectively design and improve prompts to get better results on different tasks with LLMs.

While the previous basic examples were fun, in this section we cover more advanced prompting engineering techniques that allow us to achieve more complex tasks and improve reliability and performance of LLMs.

Examples of Prompts Zero-shot Prompting

## prompt-engineering-overview#001

Prompt Engineering for AI Guide | Google Cloud

# Prompt engineering: overview and guide
 Last Updated: 01/14/2026 
 The rise of large language models (LLMs) has brought forth exciting possibilities for human-computer interaction. However, harnessing the full potential of these powerful AI models requires a crucial skill: prompt engineering. This burgeoning field focuses on crafting effective prompts that unlock the capabilities of LLMs , enabling them to understand intent, follow instructions, and generate desired outputs. As we increasingly interact with AI in various applications, prompt engineering plays a vital role in ensuring accurate, relevant, and safe interactions.

Get started for free

Try chat prompts

1:53

Tips to becoming a world-class Prompt Engineer

## prompt-engineering-overview#002

## What is prompt engineering?
 Prompt engineering is the art and science of designing and optimizing prompts to guide AI models, particularly LLMs, towards generating the desired responses. By carefully crafting prompts, you provide the model with context, instructions, and examples that help it understand your intent and respond in a meaningful way. Think of it as providing a roadmap for the AI, steering it towards the specific output you have in mind.
 To dive deeper into the world of prompt design and explore its applications, check out the Introduction to Prompt Design on Google Cloud.
 Ready to experiment with LLMs and prompt engineering firsthand? Try the Vertex AI free trial and experience the power of this technology.

## What is a prompt for AI?
 In the context of AI , a prompt is the input you provide to the model to elicit a specific response. This can take various forms, ranging from simple questions or keywords to complex instructions, code snippets, or even creative writing samples. The effectiveness of your prompt directly influences the quality and relevance of the AI's output.

## prompt-engineering-overview#003

## What do you need for prompt engineering?
 Several key elements contribute to effective prompt engineering. Mastering these allows you to communicate effectively with AI models and unlock their full potential.

### Prompt format
 The structure and style of your prompt play a significant role in guiding the AI's response. Different models may respond better to specific formats, such as:
 The format of your prompt plays a significant role in how the AI interprets your request. Different models may respond better to specific formats, such as natural language questions , direct commands, or structured inputs with specific fields. Understanding the model's capabilities and preferred format is essential for crafting effective prompts.

### Context and examples
 Providing context and relevant examples within your prompt helps the AI understand the desired task and generate more accurate and relevant outputs. For instance, if you're looking for a creative story, including a few sentences describing the desired tone or theme can significantly improve the results.

## prompt-engineering-overview#004

### Fine-tuning and adapting
 Fine-tuning the AI model on specific tasks or domains using tailored prompts can enhance its performance. Additionally, adapting prompts based on user feedback or model outputs can further improve the model's responses over time.

### Multi-turn conversations
 Designing prompts for multi-turn conversations allows users to engage in continuous and context-aware interactions with the AI model, enhancing the overall user experience.

## Types of prompts
 There are various types of prompts used in AI, each serving a specific purpose:

### Direct prompts (Zero-shot)
 Zero-shot prompting involves providing the model with a direct instruction or question without any additional context or examples. 
 An example of this is idea generation, where the model is prompted to generate creative ideas or brainstorming solutions. Another example is summarization, or translation, where the model is asked to summarize or translate some piece of content.

## prompt-engineering-overview#005

### One-, few- and multi-shot prompts
 This method involves providing the model with one or more examples of the desired input-output pairs before presenting the actual prompt. This can help the model better understand the task and generate more accurate responses.

### Chain of Thought Prompts
 CoT prompting encourages the model to break down complex reasoning into a series of intermediate steps, leading to a more comprehensive and well-structured final output.

### Zero-shot CoT Prompts
 Combines chain of thought prompting with zero-shot prompting by asking the model to perform reasoning steps, which may often produce better output.

## Use cases and examples of prompt engineering
 Here are some specific examples and use cases showing how prompt engineering helps produce customized and relevant output.

### Language and Text Generation
 
 Scenario

Instructions

Example Prompt

Creative Writing

Craft prompts that specify genre, tone, style, and plot points to guide the AI in generating engaging narratives.

"Write a short story about a young woman who discovers a magical portal in her attic."

Summarization

## prompt-engineering-overview#006

Provide the AI with text and instruct it to generate concise summaries that capture key information.

“Summarize the main points of the following news article on climate change."

Translation

Specify the source and target languages to enable the AI to accurately translate text while preserving meaning and context.

"Translate the following text from English to Spanish: 'The quick brown fox jumps over the lazy dog.'"

Dialogue

Design prompts that simulate conversations, allowing the AI to generate responses that mimic human interaction and maintain context.

"You are a friendly chatbot helping users troubleshoot their computer problems. Respond to the user's query: 'My computer won't turn on.'"

Scenario

Instructions

Example Prompt

Creative Writing

Craft prompts that specify genre, tone, style, and plot points to guide the AI in generating engaging narratives.

"Write a short story about a young woman who discovers a magical portal in her attic."

Summarization

Provide the AI with text and instruct it to generate concise summaries that capture key information.

“Summarize the main points of the following news article on climate change."

Translation

## prompt-engineering-overview#007

Specify the source and target languages to enable the AI to accurately translate text while preserving meaning and context.

"Translate the following text from English to Spanish: 'The quick brown fox jumps over the lazy dog.'"

Dialogue

Design prompts that simulate conversations, allowing the AI to generate responses that mimic human interaction and maintain context.

"You are a friendly chatbot helping users troubleshoot their computer problems. Respond to the user's query: 'My computer won't turn on.'"

### Question Answering
 
 Scenario

Instructions

Example Prompt

Open-Ended Questions

Formulate prompts that encourage the AI to provide comprehensive and informative answers based on its knowledge base.

"Explain the concept of quantum computing and its potential impact on the future of technology."

Specific Questions

Design prompts that target specific information, enabling the AI to retrieve precise answers from the provided context or its internal knowledge base.

"What is the capital of France?" or "According to the provided text, what are the main causes of deforestation?"

Multiple Choice Questions

## prompt-engineering-overview#008

Present prompts with options, prompting the AI to analyze and select the most appropriate answer based on its understanding of the context.

"Who wrote the Harry Potter series? A) J.R.R. Tolkien, B) J.K. Rowling, C) Stephen King"

Hypothetical Questions

Craft prompts that explore hypothetical situations, allowing the AI to reason, speculate, and provide potential outcomes or solutions.

"What would happen if humans could travel at the speed of light?"

Opinion-Based Questions

Design prompts that elicit the AI's perspective or opinion on a specific topic, encouraging it to provide reasoning and justification for its stance.

"Do you believe that artificial intelligence will eventually surpass human intelligence? Why or why not?"

Scenario

Instructions

Example Prompt

Open-Ended Questions

Formulate prompts that encourage the AI to provide comprehensive and informative answers based on its knowledge base.

"Explain the concept of quantum computing and its potential impact on the future of technology."

Specific Questions

Design prompts that target specific information, enabling the AI to retrieve precise answers from the provided context or its internal knowledge base.

## prompt-engineering-overview#009

"What is the capital of France?" or "According to the provided text, what are the main causes of deforestation?"

Multiple Choice Questions

Present prompts with options, prompting the AI to analyze and select the most appropriate answer based on its understanding of the context.

"Who wrote the Harry Potter series? A) J.R.R. Tolkien, B) J.K. Rowling, C) Stephen King"

Hypothetical Questions

Craft prompts that explore hypothetical situations, allowing the AI to reason, speculate, and provide potential outcomes or solutions.

"What would happen if humans could travel at the speed of light?"

Opinion-Based Questions

Design prompts that elicit the AI's perspective or opinion on a specific topic, encouraging it to provide reasoning and justification for its stance.

"Do you believe that artificial intelligence will eventually surpass human intelligence? Why or why not?"

### Code Generation
 
 Scenario

Instructions

Example Prompt

Code Completion

Provide the AI with a partial code snippet and prompt it to suggest or complete the remaining code based on the context and programming language.

"Write a Python function to calculate the factorial of a given number."

Code Translation

## prompt-engineering-overview#010

Specify the source and target programming languages to enable the AI to translate code while preserving functionality and syntax.

"Translate the following Python code to JavaScript: def greet(name): print('Hello,', name)"

Code Optimization

Prompt the AI to analyze existing code and suggest improvements for efficiency, readability, or performance.

"Optimize the following Python code to reduce its execution time."

Code Debugging

Provide the AI with code containing errors and prompt it to identify and suggest potential solutions for the identified issues.

"Debug the following Java code and explain why it is throwing a NullPointerException."

Scenario

Instructions

Example Prompt

Code Completion

Provide the AI with a partial code snippet and prompt it to suggest or complete the remaining code based on the context and programming language.

"Write a Python function to calculate the factorial of a given number."

Code Translation

Specify the source and target programming languages to enable the AI to translate code while preserving functionality and syntax.

"Translate the following Python code to JavaScript: def greet(name): print('Hello,', name)"

Code Optimization

## prompt-engineering-overview#011

Prompt the AI to analyze existing code and suggest improvements for efficiency, readability, or performance.

"Optimize the following Python code to reduce its execution time."

Code Debugging

Provide the AI with code containing errors and prompt it to identify and suggest potential solutions for the identified issues.

"Debug the following Java code and explain why it is throwing a NullPointerException."

### Image Generation
 
 Scenario

Instructions

Example Prompt

Photorealistic Images

Craft prompts that describe the desired image in detail, including objects, scenery, lighting, and style, to generate realistic and high-quality images.

"A photorealistic image of a sunset over the ocean with palm trees silhouetted against the sky."

Artistic Images

Design prompts that specify art styles, techniques, and subject matter to guide the AI in creating images that mimic specific artistic movements or evoke certain emotions.

"An impressionist painting of a bustling city street with people walking under umbrellas in the rain."

Abstract Images

Formulate prompts that encourage the AI to generate images that are open to interpretation, utilizing shapes, colors, and textures to evoke feelings or concepts.

## prompt-engineering-overview#012

"An abstract image representing the concept of hope, using bright colors and flowing shapes."

Image Editing

Provide the AI with an existing image and specify desired modifications, enabling it to edit and enhance the image according to the given instructions.

"Change the background of this photo to a starry night sky and add a full moon." or "Remove the person from this image and replace them with a cat."

Scenario

Instructions

Example Prompt

Photorealistic Images

Craft prompts that describe the desired image in detail, including objects, scenery, lighting, and style, to generate realistic and high-quality images.

"A photorealistic image of a sunset over the ocean with palm trees silhouetted against the sky."

Artistic Images

Design prompts that specify art styles, techniques, and subject matter to guide the AI in creating images that mimic specific artistic movements or evoke certain emotions.

"An impressionist painting of a bustling city street with people walking under umbrellas in the rain."

Abstract Images

Formulate prompts that encourage the AI to generate images that are open to interpretation, utilizing shapes, colors, and textures to evoke feelings or concepts.

## prompt-engineering-overview#013

"An abstract image representing the concept of hope, using bright colors and flowing shapes."

Image Editing

Provide the AI with an existing image and specify desired modifications, enabling it to edit and enhance the image according to the given instructions.

"Change the background of this photo to a starry night sky and add a full moon." or "Remove the person from this image and replace them with a cat."

## Strategies for writing better prompts
 Developing effective prompts requires a strategic approach. Consider these strategies to enhance your prompt engineering skills:

### 1. Set Clear Goals and Objectives:
 
 Tactic

Prompt Example

Use action verbs to specify the desired action

"Write a bulleted list that summarizes the key findings of the attached research paper"

Define the desired length and format of the output

"Compose a 500-word essay discussing the impact of climate change on coastal communities."

Specify the target audience

"Write a product description for a new line of organic skincare products, targeting young adults concerned with sustainability."

Tactic

Prompt Example

Use action verbs to specify the desired action
