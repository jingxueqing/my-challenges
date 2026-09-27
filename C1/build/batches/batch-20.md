# 待译批次 20

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## prompt-engineering-overview#014

"Write a bulleted list that summarizes the key findings of the attached research paper"

Define the desired length and format of the output

"Compose a 500-word essay discussing the impact of climate change on coastal communities."

Specify the target audience

"Write a product description for a new line of organic skincare products, targeting young adults concerned with sustainability."

### 2. Provide Context and Background Information:
 
 Tactic

Prompt Example

Include relevant facts and data

"Given that global temperatures have risen by 1 degree Celsius since the pre-industrial era, discuss the potential consequences for sea level rise."

Reference specific sources or documents

"Based on the attached financial report, analyze the company's profitability over the past five years."

Define key terms and concepts

"Explain the concept of quantum computing in simple terms, suitable for a non-technical audience."

Tactic

Prompt Example

Include relevant facts and data

"Given that global temperatures have risen by 1 degree Celsius since the pre-industrial era, discuss the potential consequences for sea level rise."

Reference specific sources or documents

## prompt-engineering-overview#015

"Based on the attached financial report, analyze the company's profitability over the past five years."

Define key terms and concepts

"Explain the concept of quantum computing in simple terms, suitable for a non-technical audience."

### 3. Use Few-Shot Prompting:
 
 Tactic

Prompt Example

Provide a few examples of desired input-output pairs

Input: "Cat" Output: "A small furry mammal with whiskers." Input: "Dog" Output: "A domesticated canine known for its loyalty." Prompt: "Elephant"

Demonstrate the desired style or tone

Example 1 (humorous): "The politician's speech was so dull, it could cure insomnia." Example 2 (formal): "The dignitary delivered an address that was both informative and engaging." Prompt: "Write a sentence describing the comedian's stand-up routine."

Show the desired level of detail

Example 1 (brief): "The movie was about a young boy who befriends an alien." Example 2 (detailed): "The science fiction film follows the story of Elliot, a lonely boy who discovers and forms a unique bond with an extraterrestrial stranded on Earth." Prompt: "Summarize the plot of the novel you just finished reading."

Tactic

Prompt Example

Provide a few examples of desired input-output pairs

## prompt-engineering-overview#016

Input: "Cat" Output: "A small furry mammal with whiskers." Input: "Dog" Output: "A domesticated canine known for its loyalty." Prompt: "Elephant"

Demonstrate the desired style or tone

Example 1 (humorous): "The politician's speech was so dull, it could cure insomnia." Example 2 (formal): "The dignitary delivered an address that was both informative and engaging." Prompt: "Write a sentence describing the comedian's stand-up routine."

Show the desired level of detail

Example 1 (brief): "The movie was about a young boy who befriends an alien." Example 2 (detailed): "The science fiction film follows the story of Elliot, a lonely boy who discovers and forms a unique bond with an extraterrestrial stranded on Earth." Prompt: "Summarize the plot of the novel you just finished reading."

### 4. Be Specific:
 
 Tactic

Prompt Example

Use precise language and avoid ambiguity

Instead of: "Write something about climate change," use: "Write a persuasive essay arguing for the implementation of stricter carbon emission regulations."

Quantify your requests whenever possible

Instead of: "Write a long poem," use: "Write a sonnet with 14 lines that explores themes of love and loss."

## prompt-engineering-overview#017

Break down complex tasks into smaller steps

Instead of: "Create a marketing plan," use: "1. Identify the target audience. 2. Develop key marketing messages. 3. Choose appropriate marketing channels."

Tactic

Prompt Example

Use precise language and avoid ambiguity

Instead of: "Write something about climate change," use: "Write a persuasive essay arguing for the implementation of stricter carbon emission regulations."

Quantify your requests whenever possible

Instead of: "Write a long poem," use: "Write a sonnet with 14 lines that explores themes of love and loss."

Break down complex tasks into smaller steps

Instead of: "Create a marketing plan," use: "1. Identify the target audience. 2. Develop key marketing messages. 3. Choose appropriate marketing channels."

### 5. Iterate and Experiment:
 
 Tactic

Action

Try different phrasings and keywords

Rephrase your prompt using synonyms or alternative sentence structures.

Adjust the level of detail and specificity

Add or remove information to fine-tune the output.

Test different prompt lengths

Experiment with both shorter and longer prompts to find the optimal balance.

Tactic

Action

Try different phrasings and keywords

## prompt-engineering-overview#018

Rephrase your prompt using synonyms or alternative sentence structures.

Adjust the level of detail and specificity

Add or remove information to fine-tune the output.

Test different prompt lengths

Experiment with both shorter and longer prompts to find the optimal balance.

### 6. Leverage Chain of Thought Prompting:
 
 Tactic

Prompt Example

Encourage step-by-step reasoning

"Solve this problem step-by-step: John has 5 apples, he eats 2. How many apples does he have left? Step 1: John starts with 5 apples. Step 2: He eats 2 apples, so we need to subtract 2 from 5. Step 3: 5 - 2 = 3. Answer: John has 3 apples left."

Ask the model to explain its reasoning process

"Explain your thought process in determining the sentiment of this movie review: 'The acting was superb, but the plot was predictable.'"

Guide the model through a logical sequence of thought

"To classify this email as spam or not spam, consider the following: 1. Is the sender known? 2. Does the subject line contain suspicious keywords? 3. Is the email offering something too good to be true?"

Tactic

Prompt Example

Encourage step-by-step reasoning

## prompt-engineering-overview#019

"Solve this problem step-by-step: John has 5 apples, he eats 2. How many apples does he have left? Step 1: John starts with 5 apples. Step 2: He eats 2 apples, so we need to subtract 2 from 5. Step 3: 5 - 2 = 3. Answer: John has 3 apples left."

Ask the model to explain its reasoning process

"Explain your thought process in determining the sentiment of this movie review: 'The acting was superb, but the plot was predictable.'"

Guide the model through a logical sequence of thought

"To classify this email as spam or not spam, consider the following: 1. Is the sender known? 2. Does the subject line contain suspicious keywords? 3. Is the email offering something too good to be true?"

For further guidance on prompt engineering best practices, explore the Five Best Practices for Prompt Engineering on Google Cloud.

## Benefits of prompt engineering
 Effective prompt engineering offers numerous benefits, enhancing the capabilities and usability of AI models:

### Improved model performance
 Well-crafted prompts lead to more accurate, relevant, and informative outputs from AI models, as they provide clear instructions and context.

## prompt-engineering-overview#020

### Reduced bias and harmful responses
 By carefully controlling the input and guiding the AI's focus, prompt engineering helps mitigate bias and minimize the risk of generating inappropriate or offensive content.

### Increased control and predictability
 Prompt engineering empowers you to influence the AI's behavior and ensure consistent and predictable responses aligned with your desired outcomes.

### Enhanced user experience
 Clear and concise prompts make it easier for users to interact effectively with AI models, leading to more intuitive and satisfying experiences.

### Start your AI journey with Google Cloud

New customers get $300 in free credits to spend on Google Cloud.

Get started

Talk to a Google Cloud sales specialist to discuss your unique challenge in more detail.

Contact us

## Related Google Cloud products and services 
 See all AI products and solutions

Vertex AI Platform
 A single platform for data scientists and engineers to create, train, test, monitor, tune, and deploy ML and AI models.

Generative AI on Vertex AI
 Rapidly prototype and test generative AI models. Test sample prompts, design your own prompts, and customize foundation models and LLMs.

## prompt-engineering-overview#021

AI APIs 
 Easily integrate AI into your applications with Google Cloud's AI and machine learning APIs.

Solution
 Model Garden on Vertex AI
 Jumpstart your ML project with a single place to discover, customize, and deploy a wide variety of models from Google and Google partners.

#### Additional learning resources to get started 
 New to Google Cloud or generative AI? New customers get $300 in free credits to run, test, and deploy workloads.

Training: No cost generative AI fundamentals course 
 Documentation: Introduction to prompt design 
 Documentation: General prompt design strategies 
 Documentation: Generative AI prompt samples

#### Take the next step
 Start building on Google Cloud with $300 in free credits and 20+ always free products.
 Get started for free

##### Need help getting started?
 Contact sales

##### Work with a trusted partner
 Find a partner

##### Continue browsing
 See all products

## sast-vs-dast#001

# SAST vs. DAST vs. RASP: Comparing Application Security Testing Methods

Learn December 18, 2024 Shanika Wickramasinghe 
 
 Global spending on information security is set to reach $212 billion by 2025 . This represents a growth of 15% from 2024. According to Gartner, the rise of generative AI and cloud adoption are key reasons for this rapid increase. The analyst firm further predicts that GenAI will play a part in 17% of all cyberattacks by 2027.

Businesses need advanced security strategies that go beyond traditional methods to counter these growing threats. This is why business owners need to be aware of security solutions like SAST, DAST, and RASP, as they offer multi-layered protection for applications.

(Related reading: application security explained & common software testing methods .)

## What is SAST?

Static Application Security Testing (SAST) is a white-box security testing method. SAST uses an application’s static source code or binaries to identify vulnerabilities. This means SAST tools operate on the application's code when the application is not running.

## sast-vs-dast#002

Developers use SAST to detect various security risks, such as: cross-site scripting (XSS) , insecure deserialization, buffer overflows, and other OWASP vulnerabilities in the code. Since SAST alone cannot identify run-time-specific vulnerabilities, developers have to often combine SAST with other testing methods to achieve comprehensive security.

SAST is a major component of the software development lifecycle because it detects vulnerabilities early. The earlier you catch them, the least costly they are to fix. As SAST tools can be executed during the development phase, developers are now able to write code and test it even a thousand times (!!) before releasing the product to the market.

SAST can be integrated into the CI/CD pipeline , and when done so, it is referred to as “Secure DevOps” or “ DevSecOps .” SAST is widely scalable through automation. The ability to Implement automated tests covering SAST techniques makes it an efficient solution for addressing code-level risks quickly.

## What is DAST?

## sast-vs-dast#003

Dynamic Application Security Testing is a black-box testing method. The term "Dynamic" in DAST suggests that this method evaluates the security of an application while the application is running . Unlike SAST, DAST does not require access to the application’s source code. Instead, it :

Simulates the actions of an external attacker.

Tests the application from the outside to identify vulnerabilities that only emerge during runtime.

DAST has the capability to identify various security flaws like denial-of-service (DoS) vulnerabilities and insecure server configurations. By mimicking real-world attack scenarios, DAST tools assess how the application responds to these simulated threats. With this approach, developers can identify weaknesses that static testing methods like SAST might miss.

Typically, developers perform DAST during the later stages of the software development lifecycle, often just before deployment. By testing applications in their live environments, DAST provides a clear overview of runtime security and supports better-performing applications that can withstand potential attacks.

## How does SAST work?

## sast-vs-dast#004

Developers use SAST tools to apply predefined rules and other detection methods — such as pattern matching and data flow analysis — to identify coding errors and other vulnerabilities. They integrate these tools into their IDEs or CI/CD pipelines to automate scans during the coding and testing phases.

### Common SAST methods

Here are some methods used in SAST.

Pattern matching scans the codebase for known patterns of insecure coding practices. For example, the use of weak cryptographic algorithms or insecure API calls.

Data flow C tracks how data flows through the application. This can identify vulnerabilities like SQL injection or buffer overflows by tracing untrusted input paths to sensitive operations.

Control flow analysis can analyze the application's control structures. For example, loops and conditionals to uncover logical flaws or potential vulnerabilities like race conditions.

Custom rule creation. Many tools allow developers to create custom rules to have coding best practices. Here are some examples of these custom rules:

Flag any use of unsanitized input in SQL queries.

Identify code that outputs user-provided data to the browser without proper escaping.

## sast-vs-dast#005

Highlight the use of vulnerable or deprecated functions, such as eval() in JavaScript or strcpy() in C.

Detect occurrences of hardcoded API keys and passwords in the source code and mark any instance where input validation is missing for user-provided data.

Dependency scanning. Some SAST tools analyze third-party libraries and frameworks used in the application to identify vulnerabilities in dependencies.

Semantic analysis. By interpreting the meaning of the code rather than just its structure, SAST tools can detect insecure configurations or misuse of APIs.

Machine learning models: Advanced SAST tools incorporate machine learning algorithms to recognize previously unknown vulnerabilities by analyzing patterns across large datasets.

### Performance considerations when using SAST tools

SAST tools often require significant CPU and memory resources. This can be a major issue when analyzing large codebases. A full scan of a million lines of code might consume several gigabytes of RAM.

The time required for SAST scans can vary dramatically based on the size of the codebase, ranging from a few minutes for small projects to several hours for enterprise applications. This can impact:

## sast-vs-dast#006

Build pipeline timelines

Developer productivity

Consider using modern SAST tools that support incremental scanning, allowing you to analyze only the changed code instead of the entire codebase.

Additionally, performance tuning through rule selection and scope definition is crucial. Poorly configured SAST tools can unnecessarily analyze non-critical code paths, wasting time and resources without providing security benefits.

## How does DAST work?

DAST tools simulate real-world attacks — for example, sending various forms of malicious data into input fields to see how the application processes it — to identify vulnerabilities and weaknesses in the application’s behavior and responses.

### Steps in DAST

The process typically involves the following steps.

Step 1: Scanning. Scan the web application to discover entry points (such as URLs, forms, and APIs). This step maps out the application’s structure and identifies potential attack surfaces .

Step 2: Attack simulation. Simulate malicious activities by sending crafted requests to the application. These requests test for vulnerabilities like cross-site scripting and cross-site request forgery by attempting to exploit the entry points.

## sast-vs-dast#007

Step 3: Vulnerability detection. Analyze the application’s responses to identify security weaknesses. It evaluates whether the application behaves as expected under attack. For example, malicious data can be injected to detect an SQL injection flaw.

Step 4: Reporting. Generate reports with detected vulnerabilities and recommendations for remediation. Developers can use the results in the reports to fix the identified issues.

Modern DAST solutions can incorporate advanced features such as AI-driven analysis and real-time data integration . They automatically create test sets. Dynamically adapt to the application’s structure and minimize false positives using machine learning algorithms.

### Performance considerations when using DAST tools

Here are certain performance bottlenecks when using DAST tools that you need to keep in mind.

DAST tools actively interact with the running application , temporarily increasing CPU and memory usage on both the application and web servers.

The high volume of concurrent requests generated during DAST scanning can consume significant network bandwidth.

## sast-vs-dast#008

DAST scanners often bypass or invalidate application caches by generating unique requests, reducing the effectiveness of caching mechanisms.

The creation and management of multiple test sessions by DAST tools can increase memory usage on application servers.

To avoid such issues or reduce their impact as much as possible, follow the practices below.

Schedule DAST scans during off-peak hours when application usage is minimal.

Conduct scans in a staging or pre-production environment that mirrors the production setup.

Use throttling features in DAST tools to control the number of simultaneous requests.

Increase application server thread pools during scanning periods.

Configure separate caching policies for DAST scanner IPs.

Implement automatic scan suspension if performance thresholds are exceeded.

## SAST vs. DAST: key differences

This table summarizes the difference between SAST and DAST.

Criteria

SAST

DAST

Type of testing

White-box testing. Tests the application from the inside out with access to the source code.

Black-box testing. Tests the application from the outside without access to the source code.

Software types supported
