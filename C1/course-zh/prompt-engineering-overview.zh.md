---
source_file: prompt-engineering-overview.html
title: AI 提示词工程指南 | Google Cloud
---

# 提示词工程：概述与指南
最后更新：2026 年 1 月 14 日

大语言模型（LLM）的兴起为人机交互带来了激动人心的可能性。然而，要充分发挥这些强大 AI 模型的潜力，需要一项关键技能：提示词工程。这个新兴领域专注于精心构建有效的提示词，以解锁
大语言模型的能力
，使其能够理解意图、遵循指令并生成期望的输出。随着我们在各种应用中越来越频繁地与 AI 交互，提示词工程在确保准确、相关且安全的交互方面发挥着至关重要的作用。

1:53
成为世界级提示词工程师的技巧

## 什么是提示词工程？
提示词工程是设计和优化提示词的艺术与科学，用以引导 AI 模型（尤其是大语言模型）生成期望的响应。通过精心构建提示词，你为模型提供了上下文、指令和示例，帮助它理解你的意图并以有意义的方式响应。可以把它想象成给 AI 提供一张路线图，引导它朝向你心目中的特定输出。

想深入了解提示词设计的世界并探索其应用，请查看 Google Cloud 上的
提示词设计入门
。

准备好亲手体验大语言模型和提示词工程了吗？试用
Vertex AI
免费版，感受这项技术的力量。


## 什么是 AI 提示词？
在
AI 语境
下，提示词是你提供给模型以引出特定响应的输入。它可以有多种形式，从简单的问题或关键词，到复杂的指令、代码片段，甚至是创意写作样本。你的提示词的有效性直接影响 AI 输出的质量和相关性。


## 提示词工程需要什么？
有几个关键要素构成了有效的提示词工程。掌握这些要素，你就能与 AI 模型有效沟通并释放其全部潜力。


### 提示词格式
提示词的结构和风格在引导 AI 响应方面扮演着重要角色。不同的模型可能对特定格式的响应更好，例如：

提示词的格式会显著影响 AI 如何解读你的请求。不同的模型可能对特定格式响应更好，例如
自然语言问题
、直接命令，或带有特定字段的结构化输入。理解模型的能力和偏好的格式，对于构建有效提示词至关重要。


### 上下文与示例
在提示词中提供上下文和相关示例，能帮助 AI 理解期望的任务并生成更准确、更相关的输出。例如，如果你想要一个创意故事，加入几句描述期望语气或主题的文字，可以显著改善结果。


### 微调与适配
使用定制提示词在特定任务或领域上微调 AI 模型，可以提升其性能。此外，根据用户反馈或模型输出调整提示词，可以随时间推移进一步改善模型的响应。


### 多轮对话
为多轮对话设计提示词，使用户能够与 AI 模型进行持续的、具备上下文感知能力的交互，从而提升整体用户体验。


## 提示词的类型
AI 中使用的提示词有多种类型，各自服务于特定目的：


### 直接提示词（零样本）
零样本提示是指在不提供任何额外上下文或示例的情况下，直接给模型一个指令或问题。

一个例子是创意生成，即让模型生成创意想法或进行头脑风暴式求解。另一个例子是摘要或翻译，即让模型对某段内容进行总结或翻译。


### 单样本、少样本与多样本提示词
这种方法是在呈现实际提示词之前，先向模型提供一个或多个期望的输入-输出对示例。这可以帮助模型更好地理解任务并生成更准确的响应。


### 思维链提示词
思维链（CoT）提示鼓励模型把复杂推理分解为一系列中间步骤，从而得出更全面、结构更清晰的最终输出。


### 零样本思维链提示词
将思维链提示与零样本提示相结合，要求模型执行推理步骤，这通常能产生更好的输出。


## 提示词工程的用例与示例
以下是一些具体的例子和用例，展示提示词工程如何帮助生成定制化且相关的输出。


### 语言与文本生成
|  |
| 场景 | 指令 | 示例提示词 |
| 创意写作 | 构建指定体裁、语气、风格和情节要点的提示词，引导 AI 生成引人入胜的叙事。 | "Write a short story about a young woman who discovers a magical portal in her attic." |
| 摘要 | 向 AI 提供文本并指示其生成捕捉关键信息的简明摘要。 | "Summarize the main points of the following news article on climate change." |
| 翻译 | 指定源语言和目标语言，使 AI 能够在保留含义和上下文的前提下准确翻译文本。 | "Translate the following text from English to Spanish: 'The quick brown fox jumps over the lazy dog.'" |
| 对话 | 设计模拟对话的提示词，使 AI 能够生成模仿人类交互并保持上下文的响应。 | "You are a friendly chatbot helping users troubleshoot their computer problems. Respond to the user's query: 'My computer won't turn on.'" |

场景

指令

示例提示词

创意写作

构建指定体裁、语气、风格和情节要点的提示词，引导 AI 生成引人入胜的叙事。

"Write a short story about a young woman who discovers a magical portal in her attic."

摘要

向 AI 提供文本并指示其生成捕捉关键信息的简明摘要。

"Summarize the main points of the following news article on climate change."

翻译

指定源语言和目标语言，使 AI 能够在保留含义和上下文的前提下准确翻译文本。

"Translate the following text from English to Spanish: 'The quick brown fox jumps over the lazy dog.'"

对话

设计模拟对话的提示词，使 AI 能够生成模仿人类交互并保持上下文的响应。

"You are a friendly chatbot helping users troubleshoot their computer problems. Respond to the user's query: 'My computer won't turn on.'"


### 问答
|  |
| 场景 | 指令 | 示例提示词 |
| 开放式问题 | 构建鼓励 AI 基于其知识库提供全面且有信息量的回答的提示词。 | "Explain the concept of quantum computing and its potential impact on the future of technology." |
| 具体问题 | 设计针对特定信息的提示词，使 AI 能够从提供的上下文或其内部知识库中检索精确的答案。 | "What is the capital of France?" 或 "According to the provided text, what are the main causes of deforestation?" |
| 选择题 | 呈现带选项的提示词，促使 AI 基于对上下文的理解进行分析并选出最合适的答案。 | "Who wrote the Harry Potter series? A) J.R.R. Tolkien, B) J.K. Rowling, C) Stephen King" |
| 假设性问题 | 构建探索假设情境的提示词，让 AI 进行推理、推测并给出可能的结果或解决方案。 | "What would happen if humans could travel at the speed of light?" |
| 观点类问题 | 设计引出 AI 对特定话题的观点或看法的提示词，鼓励其为自己的立场提供推理和论证。 | "Do you believe that artificial intelligence will eventually surpass human intelligence? Why or why not?" |

场景

指令

示例提示词

开放式问题

构建鼓励 AI 基于其知识库提供全面且有信息量的回答的提示词。

"Explain the concept of quantum computing and its potential impact on the future of technology."

具体问题

设计针对特定信息的提示词，使 AI 能够从提供的上下文或其内部知识库中检索精确的答案。

"What is the capital of France?" 或 "According to the provided text, what are the main causes of deforestation?"

选择题

呈现带选项的提示词，促使 AI 基于对上下文的理解进行分析并选出最合适的答案。

"Who wrote the Harry Potter series? A) J.R.R. Tolkien, B) J.K. Rowling, C) Stephen King"

假设性问题

构建探索假设情境的提示词，让 AI 进行推理、推测并给出可能的结果或解决方案。

"What would happen if humans could travel at the speed of light?"

观点类问题

设计引出 AI 对特定话题的观点或看法的提示词，鼓励其为自己的立场提供推理和论证。

"Do you believe that artificial intelligence will eventually surpass human intelligence? Why or why not?"


### 代码生成
|  |
| 场景 | 指令 | 示例提示词 |
| 代码补全 | 向 AI 提供部分代码片段，提示它根据上下文和编程语言建议或补全剩余代码。 | "Write a Python function to calculate the factorial of a given number." |
| 代码翻译 | 指定源编程语言和目标编程语言，使 AI 能够在保留功能和语法的前提下翻译代码。 | "Translate the following Python code to JavaScript: def greet(name): print('Hello,', name)" |
| 代码优化 | 提示 AI 分析现有代码，并就效率、可读性或性能提出改进建议。 | "Optimize the following Python code to reduce its execution time." |
| 代码调试 | 向 AI 提供包含错误的代码，提示它识别问题并给出针对所识别问题的潜在解决方案。 | "Debug the following Java code and explain why it is throwing a NullPointerException." |

场景

指令

示例提示词

代码补全

向 AI 提供部分代码片段，提示它根据上下文和编程语言建议或补全剩余代码。

"Write a Python function to calculate the factorial of a given number."

代码翻译

指定源编程语言和目标编程语言，使 AI 能够在保留功能和语法的前提下翻译代码。

"Translate the following Python code to JavaScript: def greet(name): print('Hello,', name)"

代码优化

提示 AI 分析现有代码，并就效率、可读性或性能提出改进建议。

"Optimize the following Python code to reduce its execution time."

代码调试

向 AI 提供包含错误的代码，提示它识别问题并给出针对所识别问题的潜在解决方案。

"Debug the following Java code and explain why it is throwing a NullPointerException."


### 图像生成
|  |
| 场景 | 指令 | 示例提示词 |
| 照片级真实图像 | 构建详细描述期望图像的提示词，包括物体、场景、光照和风格，以生成逼真的高质量图像。 | "A photorealistic image of a sunset over the ocean with palm trees silhouetted against the sky." |
| 艺术图像 | 设计指定艺术风格、技法和题材的提示词，引导 AI 创作出模仿特定艺术流派或唤起特定情感的图像。 | "An impressionist painting of a bustling city street with people walking under umbrellas in the rain." |
| 抽象图像 | 构建鼓励 AI 生成开放解读图像的提示词，利用形状、颜色和纹理来唤起情感或概念。 | "An abstract image representing the concept of hope, using bright colors and flowing shapes." |
| 图像编辑 | 向 AI 提供已有图像并指定期望的修改，使其按照给定指令编辑和增强图像。 | "Change the background of this photo to a starry night sky and add a full moon." 或 "Remove the person from this image and replace them with a cat." |

场景

指令

示例提示词

照片级真实图像

构建详细描述期望图像的提示词，包括物体、场景、光照和风格，以生成逼真的高质量图像。

"A photorealistic image of a sunset over the ocean with palm trees silhouetted against the sky."

艺术图像

设计指定艺术风格、技法和题材的提示词，引导 AI 创作出模仿特定艺术流派或唤起特定情感的图像。

"An impressionist painting of a bustling city street with people walking under umbrellas in the rain."

抽象图像

构建鼓励 AI 生成开放解读图像的提示词，利用形状、颜色和纹理来唤起情感或概念。

"An abstract image representing the concept of hope, using bright colors and flowing shapes."

图像编辑

向 AI 提供已有图像并指定期望的修改，使其按照给定指令编辑和增强图像。

"Change the background of this photo to a starry night sky and add a full moon." 或 "Remove the person from this image and replace them with a cat."


## 编写更好提示词的策略
开发有效的提示词需要策略性思维。考虑以下策略来提升你的提示词工程技能：


### 1. 设定清晰的目标与目的：
|  |
| 技巧 | 提示词示例 |
| 使用动词明确期望的动作 | "Write a bulleted list that summarizes the key findings of the attached research paper" |
| 定义期望的输出长度和格式 | "Compose a 500-word essay discussing the impact of climate change on coastal communities." |
| 指定目标受众 | "Write a product description for a new line of organic skincare products, targeting young adults concerned with sustainability." |

技巧

提示词示例

使用动词明确期望的动作

"Write a bulleted list that summarizes the key findings of the attached research paper"

定义期望的输出长度和格式

"Compose a 500-word essay discussing the impact of climate change on coastal communities."

指定目标受众

"Write a product description for a new line of organic skincare products, targeting young adults concerned with sustainability."


### 2. 提供上下文与背景信息：
|  |
| 技巧 | 提示词示例 |
| 提供相关的事实和数据 | "Given that global temperatures have risen by 1 degree Celsius since the pre-industrial era, discuss the potential consequences for sea level rise." |
| 引用具体的来源或文档 | "Based on the attached financial report, analyze the company's profitability over the past five years." |
| 定义关键术语和概念 | "Explain the concept of quantum computing in simple terms, suitable for a non-technical audience." |

技巧

提示词示例

提供相关的事实和数据

"Given that global temperatures have risen by 1 degree Celsius since the pre-industrial era, discuss the potential consequences for sea level rise."

引用具体的来源或文档

"Based on the attached financial report, analyze the company's profitability over the past five years."

定义关键术语和概念

"Explain the concept of quantum computing in simple terms, suitable for a non-technical audience."


### 3. 使用少样本提示：
|  |
| 技巧 | 提示词示例 |
| 提供几个期望的输入-输出对示例 | Input: "Cat" Output: "A small furry mammal with whiskers." Input: "Dog" Output: "A domesticated canine known for its loyalty." Prompt: "Elephant" |
| 示范期望的风格或语气 | Example 1 (humorous): "The politician's speech was so dull, it could cure insomnia." Example 2 (formal): "The dignitary delivered an address that was both informative and engaging." Prompt: "Write a sentence describing the comedian's stand-up routine." |
| 展示期望的详细程度 | Example 1 (brief): "The movie was about a young boy who befriends an alien." Example 2 (detailed): "The science fiction film follows the story of Elliot, a lonely boy who discovers and forms a unique bond with an extraterrestrial stranded on Earth." Prompt: "Summarize the plot of the novel you just finished reading." |

技巧

提示词示例

提供几个期望的输入-输出对示例

Input: "Cat" Output: "A small furry mammal with whiskers." Input: "Dog" Output: "A domesticated canine known for its loyalty." Prompt: "Elephant"

示范期望的风格或语气

Example 1 (humorous): "The politician's speech was so dull, it could cure insomnia." Example 2 (formal): "The dignitary delivered an address that was both informative and engaging." Prompt: "Write a sentence describing the comedian's stand-up routine."

展示期望的详细程度

Example 1 (brief): "The movie was about a young boy who befriends an alien." Example 2 (detailed): "The science fiction film follows the story of Elliot, a lonely boy who discovers and forms a unique bond with an extraterrestrial stranded on Earth." Prompt: "Summarize the plot of the novel you just finished reading."


### 4. 保持具体：
|  |
| 技巧 | 提示词示例 |
| 使用精确的语言，避免歧义 | 与其写 "Write something about climate change"，不如写 "Write a persuasive essay arguing for the implementation of stricter carbon emission regulations." |
| 尽可能量化你的请求 | 与其写 "Write a long poem"，不如写 "Write a sonnet with 14 lines that explores themes of love and loss." |
| 把复杂任务拆解为更小的步骤 | 与其写 "Create a marketing plan"，不如写 "1. Identify the target audience. 2. Develop key marketing messages. 3. Choose appropriate marketing channels." |

技巧

提示词示例

使用精确的语言，避免歧义

与其写 "Write something about climate change"，不如写 "Write a persuasive essay arguing for the implementation of stricter carbon emission regulations."

尽可能量化你的请求

与其写 "Write a long poem"，不如写 "Write a sonnet with 14 lines that explores themes of love and loss."

把复杂任务拆解为更小的步骤

与其写 "Create a marketing plan"，不如写 "1. Identify the target audience. 2. Develop key marketing messages. 3. Choose appropriate marketing channels."


### 5. 迭代与实验：
|  |
| 技巧 | 行动 |
| 尝试不同的措辞和关键词 | 使用同义词或替代句式重新表述你的提示词。 |
| 调整详细程度和具体性 | 通过增删信息来微调输出。 |
| 测试不同的提示词长度 | 同时实验更短和更长的提示词，找到最佳平衡。 |

技巧

行动

尝试不同的措辞和关键词

使用同义词或替代句式重新表述你的提示词。

调整详细程度和具体性

通过增删信息来微调输出。

测试不同的提示词长度

同时实验更短和更长的提示词，找到最佳平衡。


### 6. 利用思维链提示：
|  |
| 技巧 | 提示词示例 |
| 鼓励逐步推理 | "Solve this problem step-by-step: John has 5 apples, he eats 2. How many apples does he have left? Step 1: John starts with 5 apples. Step 2: He eats 2 apples, so we need to subtract 2 from 5. Step 3: 5 - 2 = 3. Answer: John has 3 apples left." |
| 要求模型解释其推理过程 | "Explain your thought process in determining the sentiment of this movie review: 'The acting was superb, but the plot was predictable.'" |
| 引导模型遵循逻辑思维序列 | "To classify this email as spam or not spam, consider the following: 1. Is the sender known? 2. Does the subject line contain suspicious keywords? 3. Is the email offering something too good to be true?" |

技巧

提示词示例

鼓励逐步推理

"Solve this problem step-by-step: John has 5 apples, he eats 2. How many apples does he have left? Step 1: John starts with 5 apples. Step 2: He eats 2 apples, so we need to subtract 2 from 5. Step 3: 5 - 2 = 3. Answer: John has 3 apples left."

要求模型解释其推理过程

"Explain your thought process in determining the sentiment of this movie review: 'The acting was superb, but the plot was predictable.'"

引导模型遵循逻辑思维序列

"To classify this email as spam or not spam, consider the following: 1. Is the sender known? 2. Does the subject line contain suspicious keywords? 3. Is the email offering something too good to be true?"

如需更多提示词工程最佳实践的指导，请探索 Google Cloud 上的
提示词工程五大最佳实践
。


## 提示词工程的收益
有效的提示词工程带来诸多收益，提升 AI 模型的能力和可用性：


### 提升模型性能
精心构建的提示词能让 AI 模型的输出更准确、更相关、更有信息量，因为它们提供了清晰的指令和上下文。


### 减少偏见与有害响应
通过仔细控制输入并引导 AI 的关注点，提示词工程有助于缓解偏见，并最大限度降低生成不当或冒犯性内容的风险。


### 增强控制力与可预测性
提示词工程让你能够影响 AI 的行为，确保响应一致、可预测，并与你期望的结果保持一致。


### 改善用户体验
清晰简洁的提示词使用户更容易与 AI 模型进行有效交互，带来更直观、更令人满意的体验。


### 与 Google Cloud 开启你的 AI 之旅
新客户可获得 300 美元免费额度用于 Google Cloud。
与 Google Cloud 销售专家交流，更详细地讨论你的独特挑战。

## 相关的 Google Cloud 产品与服务
查看所有 AI 产品与解决方案

- Vertex AI 平台：一个面向数据科学家和工程师的统一平台，用于创建、训练、测试、监控、调优和部署机器学习（ML）与 AI 模型。
- Vertex AI 上的生成式 AI：快速原型化和测试生成式 AI 模型。测试示例提示词、设计你自己的提示词，并自定义基础模型和大语言模型。
- AI API：借助 Google Cloud 的 AI 与机器学习 API，轻松将 AI 集成到你的应用中。
- 解决方案：Vertex AI 上的模型花园（Model Garden）：在一个集中位置发现、自定义和部署来自 Google 及其合作伙伴的各类模型，为你的 ML 项目加速起步。


#### 更多入门学习资源
初次接触 Google Cloud 或生成式 AI？新客户可获得
300 美元免费额度
来运行、测试和部署工作负载。

- 培训：免费的生成式 AI 基础课程
- 文档：提示词设计入门
- 文档：通用提示词设计策略
- 文档：生成式 AI 提示词示例


#### 迈出下一步
使用 300 美元免费额度和 20 多款始终免费的产品，开始在 Google Cloud 上构建。

- 需要入门帮助？联系销售
- 与值得信赖的伙伴合作：寻找合作伙伴
- 继续浏览：查看所有产品
