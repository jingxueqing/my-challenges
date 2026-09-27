# 待译批次 25

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## writing-effective-tools-for-agents#010

### Namespacing your tools
 Your AI agents will potentially gain access to dozens of MCP servers and hundreds of different tools–including those by other developers. When tools overlap in function or have a vague purpose, agents can get confused about which ones to use.
 Namespacing (grouping related tools under common prefixes) can help delineate boundaries between lots of tools; MCP clients sometimes do this by default. For example, namespacing tools by service (e.g., asana_search , jira_search ) and by resource (e.g., asana_projects_search , asana_users_search ), can help agents select the right tools at the right time.
 We have found selecting between prefix- and suffix-based namespacing to have non-trivial effects on our tool-use evaluations. Effects vary by LLM and we encourage you to choose a naming scheme according to your own evaluations.
 Agents might call the wrong tools, call the right tools with the wrong parameters, call too few tools, or process tool responses incorrectly. By selectively implementing tools whose names reflect natural subdivisions of tasks, you simultaneously reduce the number of tools and tool descriptions loaded into the agent’s context and offload agentic computation from the agent’s context back into the tool calls themselves. This reduces an agent’s overall risk of making mistakes.

## writing-effective-tools-for-agents#011

### Returning meaningful context from your tools
 In the same vein, tool implementations should take care to return only high signal information back to agents. They should prioritize contextual relevance over flexibility, and eschew low-level technical identifiers (for example: uuid , 256px_image_url , mime_type ). Fields like name , image_url , and file_type are much more likely to directly inform agents’ downstream actions and responses.
 Agents also tend to grapple with natural language names, terms, or identifiers significantly more successfully than they do with cryptic identifiers. We’ve found that merely resolving arbitrary alphanumeric UUIDs to more semantically meaningful and interpretable language (or even a 0-indexed ID scheme) significantly improves Claude’s precision in retrieval tasks by reducing hallucinations.
 In some instances, agents may require the flexibility to interact with both natural language and technical identifiers outputs, if only to trigger downstream tool calls (for example, search_user(name=’jane’) → send_message(id=12345) ). You can enable both by exposing a simple response_format enum parameter in your tool, allowing your agent to control whether tools return “concise” or “detailed” responses (images below).
 You can add more formats for even greater flexibility, similar to GraphQL where you can choose exactly which pieces of information you want to receive. Here is an example ResponseFormat enum to control tool response verbosity:
 enum ResponseFormat {
 DETAILED = "detailed",
 CONCISE = "concise"
} Copy

## writing-effective-tools-for-agents#012

Here’s an example of a detailed tool response (206 tokens):
 
 Here’s an example of a concise tool response (72 tokens):
 Slack threads and thread replies are identified by unique thread_ts which are required to fetch thread replies. thread_ts and other IDs ( channel_id , user_id ) can be retrieved from a “detailed” tool response to enable further tool calls that require these. “concise” tool responses return only thread content and exclude IDs. In this example, we use ~⅓ of the tokens with “concise” tool responses. 
 Even your tool response structure—for example XML, JSON, or Markdown—can have an impact on evaluation performance: there is no one-size-fits-all solution. This is because LLMs are trained on next-token prediction and tend to perform better with formats that match their training data. The optimal response structure will vary widely by task and agent. We encourage you to select the best response structure based on your own evaluation.

## writing-effective-tools-for-agents#013

### Optimizing tool responses for token efficiency
 Optimizing the quality of context is important. But so is optimizing the quantity of context returned back to agents in tool responses.
 We suggest implementing some combination of pagination, range selection, filtering, and/or truncation with sensible default parameter values for any tool responses that could use up lots of context. For Claude Code, we restrict tool responses to 25,000 tokens by default. We expect the effective context length of agents to grow over time, but the need for context-efficient tools to remain.
 If you choose to truncate responses, be sure to steer agents with helpful instructions. You can directly encourage agents to pursue more token-efficient strategies, like making many small and targeted searches instead of a single, broad search for a knowledge retrieval task. Similarly, if a tool call raises an error (for example, during input validation), you can prompt-engineer your error responses to clearly communicate specific and actionable improvements, rather than opaque error codes or tracebacks.
 Here’s an example of a truncated tool response:
 
 Here’s an example of an unhelpful error response:
 
 Here’s an example of a helpful error response:
 Tool truncation and error responses can steer agents towards more token-efficient tool-use behaviors (using filters or pagination) or give examples of correctly formatted tool inputs.

## writing-effective-tools-for-agents#014

### Prompt-engineering your tool descriptions
 We now come to one of the most effective methods for improving tools: prompt-engineering your tool descriptions and specs. Because these are loaded into your agents’ context, they can collectively steer agents toward effective tool-calling behaviors.
 When writing tool descriptions and specs, think of how you would describe your tool to a new hire on your team. Consider the context that you might implicitly bring—specialized query formats, definitions of niche terminology, relationships between underlying resources—and make it explicit. Avoid ambiguity by clearly describing (and enforcing with strict data models) expected inputs and outputs. In particular, input parameters should be unambiguously named: instead of a parameter named user , try a parameter named user_id .
 With your evaluation you can measure the impact of your prompt engineering with greater confidence. Even small refinements to tool descriptions can yield dramatic improvements. Claude Sonnet 3.5 achieved state-of-the-art performance on the SWE-bench Verified evaluation after we made precise refinements to tool descriptions, dramatically reducing error rates and improving task completion.
 You can find other best practices for tool definitions in our Developer Guide . If you’re building tools for Claude, we also recommend reading about how tools are dynamically loaded into Claude’s system prompt . Lastly, if you’re writing tools for an MCP server, tool annotations help disclose which tools require open-world access or make destructive changes.

## writing-effective-tools-for-agents#015

## Looking ahead
 To build effective tools for agents, we need to re-orient our software development practices from predictable, deterministic patterns to non-deterministic ones.
 Through the iterative, evaluation-driven process we’ve described in this post, we've identified consistent patterns in what makes tools successful: Effective tools are intentionally and clearly defined, use agent context judiciously, can be combined together in diverse workflows, and enable agents to intuitively solve real-world tasks.
 In the future, we expect the specific mechanisms through which agents interact with the world to evolve—from updates to the MCP protocol to upgrades to the underlying LLMs themselves. With a systematic, evaluation-driven approach to improving tools for agents, we can ensure that as agents become more capable, the tools they use will evolve alongside them.

## writing-effective-tools-for-agents#016

## Acknowledgements
 Written by Ken Aizawa with valuable contributions from colleagues across Research (Barry Zhang, Zachary Witten, Daniel Jiang, Sami Al-Sheikh, Matt Bell, Maggie Vo), MCP (Theodora Chu, John Welsh, David Soria Parra, Adam Jones), Product Engineering (Santiago Seira), Marketing (Molly Vorwerck), Design (Drew Roper), and Applied AI (Christian Ryan, Alexander Bricken).
 1 Beyond training the underlying LLMs themselves.

### Looking to learn more?

Explore courses

## Get the developer newsletter
 Product updates, how-tos, community spotlights, and more. Delivered monthly to your inbox.

## index#001

CS146S: The Modern Software Developer - Stanford University

## all_urls#001

http://www.w3.org/1998/Math/MathML
http://www.w3.org/1999/xhtml
http://www.w3.org/1999/xlink
http://www.w3.org/2000/svg
http://www.w3.org/2000/svg'%3E%3Cpath d='M0.861 25.5C0.735 25.5 0.651 25.416 0.651 25.29V10.548C0.651 10.422 0.735 10.338 0.861 10.338H6.279C9.072 10.338 10.668 11.451 10.668 13.824C10.668 15.819 9.219 16.932 8.001 17.226C7.707 17.268 7.707 17.625 8.022 17.688C9.912 18.108 11.088 19.116 11.088 21.321C11.088 23.715 9.429 25.5 6.426 25.5H0.861ZM5.397 23.085C6.825 23.085 7.518 22.224 7.518 21.006C7.518 19.683 6.825 18.948 5.397 18.948H4.2V23.085H5.397ZM5.313 16.617C6.51 16.617 7.245 15.945 7.245 14.601C7.245 13.383 6.51 12.753 5.25 12.753H4.2V16.617H5.313ZM17.9758 23.883C17.9758 23.568 17.6608 23.505 17.5348 23.799C17.0308 24.954 16.1698 25.731 14.5528 25.731C12.8728 25.731 12.0958 24.471 12.0958 22.707V14.937C12.0958 14.811 12.1798 14.727 12.3058 14.727H15.2248C15.3508 14.727 15.4348 14.811 15.4348 14.937V21.657C15.4348 22.581 15.7708 23.022 16.4638 23.022C17.1778 23.022 17.6188 22.581 17.6188 21.657V14.937C17.6188 14.811 17.7028 14.727 17.8288 14.727H20.7478C20.8738 14.727 20.9578 14.811 20.9578 14.937V25.29C20.9578 25.416 20.8738 25.5 20.7478 25.5H18.1858C18.0598 25.5 17.9758 25.416 17.9758 25.29V23.883ZM25.6141 25.29C25.6141 25.416 25.5301 25.5 25.4041 25.5H22.4851C22.3591 25.5 22.2751 25.416 22.2751 25.29V14.937C22.2751 14.811 22.3591 14.727 22.4851 14.727H25.4041C25.5301 14.727 25.6141 14.811 25.6141 14.937V25.29ZM23.9131 13.74C22.8001 13.74 22.0441 12.942 22.0441 11.934C22.0441 10.926 22.8001 10.107 23.9131 10.107C25.0051 10.107 25.7611 10.926 25.7611 11.934C25.7611 12.942 25.0051 13.74 23.9131 13.74ZM26.7883 10.548C26.7883 10.422 26.8723 10.338 26.9983 10.338H29.9173C30.0433 10.338 30.1273 10.422 30.1273 10.548V22.056C30.1273 22.749 30.2533 23.085 30.8203 23.085C31.0093 23.085 31.1983 23.043 31.3663 23.001C31.5133 22.959 31.6183 22.959 31.6183 23.127V25.059C31.6183 25.164 31.5763 25.269 31.4923 25.311C30.9673 25.521 30.2953 25.71 29.5813 25.71C27.7123 25.71 26.7883 24.639 26.7883 22.476V10.548ZM32.4237 14.727C32.8227 14.727 32.9277 14.538 32.9697 14.055L33.1167 12.039C33.1167 11.913 33.2217 11.829 33.3477 11.829H35.8887C36.0147 11.829 36.0987 11.913 36.0987 12.039V14.517C36.0987 14.643 36.1827 14.727 36.3087 14.727H38.2827C38.4087 14.727 38.4927 14.811 38.4927 14.937V16.659C38.4927 16.785 38.4087 16.869 38.2827 16.869H36.0777V22.056C36.0777 22.875 36.5397 23.085 37.0647 23.085C37.4847 23.085 37.9467 22.938 38.3247 22.707C38.4717 22.623 38.5767 22.665 38.5767 22.833V24.828C38.5767 24.933 38.5347 25.017 38.4507 25.08C37.8417 25.458 36.9807 25.71 36.0357 25.71C34.2927 25.71 32.7387 24.912 32.7387 22.476V16.869H31.8567C31.7307 16.869 31.6467 16.785 31.6467 16.659V14.937C31.6467 14.811 31.7307 14.727 31.8567 14.727H32.4237ZM51.3808 14.727C51.5068 14.727 51.5908 14.79 51.6118 14.916L52.3888 19.851L52.5778 21.174C52.6198 21.468 52.9558 21.468 52.9768 21.174C53.0398 20.712 53.0818 20.271 53.1658 19.83L53.8798 14.916C53.9008 14.79 53.9848 14.727 54.1108 14.727H56.6728C56.8198 14.727 56.8828 14.811 56.8618 14.958L54.6778 25.311C54.6568 25.437 54.5728 25.5 54.4468 25.5H51.3178C51.1918 25.5 51.1078 25.437 51.0868 25.311L50.1208 20.082L49.8898 18.633C49.8688 18.444 49.6588 18.444 49.6378 18.633L49.4068 20.103L48.5458 25.311C48.5248 25.437 48.4408 25.5 48.3148 25.5H45.2068C45.0808 25.5 44.9968 25.437 44.9758 25.311L42.8128 14.958C42.7918 14.811 42.8548 14.727 43.0018 14.727H45.9628C46.0888 14.727 46.1728 14.79 46.1938 14.916L46.9288 19.83C47.0128 20.271 47.0758 20.754 47.1388 21.195C47.2018 21.51 47.4748 21.531 47.5378 21.195L47.7478 19.872L48.6088 14.916C48.6298 14.79 48.7138 14.727 48.8398 14.727H51.3808ZM61.1582 25.29C61.1582 25.416 61.0742 25.5 60.9482 25.5H58.0292C57.9032 25.5 57.8192 25.416 57.8192 25.29V14.937C57.8192 14.811 57.9032 14.727 58.0292 14.727H60.9482C61.0742 14.727 61.1582 14.811 61.1582 14.937V25.29ZM59.4572 13.74C58.3442 13.74 57.5882 12.942 57.5882 11.934C57.5882 10.926 58.3442 10.107 59.4572 10.107C60.5492 10.107 61.3052 10.926 61.3052 11.934C61.3052 12.942 60.5492 13.74 59.4572 13.74ZM62.8154 14.727C63.2144 14.727 63.3194 14.538 63.3614 14.055L63.5084 12.039C63.5084 11.913 63.6134 11.829 63.7394 11.829H66.2804C66.4064 11.829 66.4904 11.913 66.4904 12.039V14.517C66.4904 14.643 66.5744 14.727 66.7004 14.727H68.6744C68.8004 14.727 68.8844 14.811 68.8844 14.937V16.659C68.8844 16.785 68.8004 16.869 68.6744 16.869H66.4694V22.056C66.4694 22.875 66.9314 23.085 67.4564 23.085C67.8764 23.085 68.3384 22.938 68.7164 22.707C68.8634 22.623 68.9684 22.665 68.9684 22.833V24.828C68.9684 24.933 68.9264 25.017 68.8424 25.08C68.2334 25.458 67.3724 25.71 66.4274 25.71C64.6844 25.71 63.1304 24.912 63.1304 22.476V16.869H62.2484C62.1224 16.869 62.0384 16.785 62.0384 16.659V14.937C62.0384 14.811 62.1224 14.727 62.2484 14.727H62.8154ZM73.4298 16.323C73.4298 16.638 73.7868 16.68 73.9128 16.407C74.3748 15.315 75.1308 14.496 76.6008 14.496C78.2178 14.496 78.9528 15.609 78.9528 17.373V25.29C78.9528 25.416 78.8688 25.5 78.7428 25.5H75.8238C75.6978 25.5 75.6138 25.416 75.6138 25.29V18.633C75.6138 17.709 75.2778 17.268 74.5848 17.268C73.8708 17.268 73.4298 17.709 73.4298 18.633V25.29C73.4298 25.416 73.3458 25.5 73.2198 25.5H70.3008C70.1748 25.5 70.0908 25.416 70.0908 25.29V10.548C70.0908 10.422 70.1748 10.338 70.3008 10.338H73.2198C73.3458 10.338 73.4298 10.422 73.4298 10.548V16.323Z' fill='%231E1E1E'/%3E%3Cpath d='M100.132 16.3203C105.58 17.3761 107.272 22.4211 107.318 27.4961C107.318 27.6101 107.226 27.7041 107.112 27.7041H100.252C100.138 27.7041 100.046 27.6121 100.046 27.5001C100.026 23.5629 99.3877 20.0896 95.4865 19.9396C95.3705 19.9356 95.2725 20.0276 95.2725 20.1456V27.5001C95.2725 27.6141 95.1806 27.7061 95.0666 27.7061H88.206C88.092 27.7061 88 27.6141 88 27.5001V8.75585C88 8.64187 88.092 8.54989 88.206 8.54989H95.0686C95.1826 8.54989 95.2745 8.64187 95.2745 8.75585V15.7764C95.2745 15.8804 95.3585 15.9644 95.4625 15.9644C95.5445 15.9644 95.6185 15.9104 95.6425 15.8324C97.4081 10.0416 100.709 8.58588 106.07 8.55189C106.184 8.55189 106.276 8.64387 106.276 8.75785V15.7604C106.276 15.8744 106.184 15.9664 106.07 15.9664H100.166C100.066 15.9664 99.9856 16.0464 99.9856 16.1464C99.9856 16.2304 100.048 16.3043 100.132 16.3203ZM118.918 20.7095V16.1704C118.918 16.0564 119.01 15.9644 119.124 15.9644H124.173C124.273 15.9644 124.353 15.8844 124.353 15.7844C124.353 15.6985 124.291 15.6245 124.207 15.6085C120.256 14.8246 118.432 12.5511 118.37 8.75585C118.368 8.64387 118.458 8.54989 118.572 8.54989H125.986C126.1 8.54989 126.192 8.64187 126.192 8.75585V11.9532C126.192 12.0672 126.284 12.1592 126.398 12.1592H130.649C130.763 12.1592 130.855 12.2511 130.855 12.3651V15.7624C130.855 15.8764 130.763 15.9684 130.649 15.9684H126.398C126.284 15.9684 126.192 16.0604 126.192 16.1744V19.8356C126.192 21.1294 126.986 21.5553 128.04 21.5553C129.692 21.5553 131.323 20.8114 131.977 20.4735C132.113 20.4035 132.277 20.5015 132.277 20.6555V26.3543C132.277 26.5063 132.193 26.6463 132.059 26.7183C131.413 27.0582 129.418 28 127.136 28C122.435 27.996 118.918 26.0824 118.918 20.7095ZM109.266 27.4981V16.1704C109.266 16.0564 109.358 15.9644 109.472 15.9644H116.334C116.448 15.9644 116.54 16.0564 116.54 16.1704V27.4981C116.54 27.6121 116.448 27.7041 116.334 27.7041H109.472C109.358 27.7021 109.266 27.6101 109.266 27.4981ZM108.876 11.4913C108.876 13.4189 110.238 14.9826 112.853 14.9826C115.469 14.9826 116.83 13.4189 116.83 11.4913C116.83 9.56369 115.471 8 112.853 8C110.238 8 108.876 9.56369 108.876 11.4913Z' fill='%231E1E1E'/%3E%3C/svg%3E
http://www.w3.org/2000/svg'%3E%3Cpath d='M0.861 25.5C0.735 25.5 0.651 25.416 0.651 25.29V10.548C0.651 10.422 0.735 10.338 0.861 10.338H6.279C9.072 10.338 10.668 11.451 10.668 13.824C10.668 15.819 9.219 16.932 8.001 17.226C7.707 17.268 7.707 17.625 8.022 17.688C9.912 18.108 11.088 19.116 11.088 21.321C11.088 23.715 9.429 25.5 6.426 25.5H0.861ZM5.397 23.085C6.825 23.085 7.518 22.224 7.518 21.006C7.518 19.683 6.825 18.948 5.397 18.948H4.2V23.085H5.397ZM5.313 16.617C6.51 16.617 7.245 15.945 7.245 14.601C7.245 13.383 6.51 12.753 5.25 12.753H4.2V16.617H5.313ZM17.9758 23.883C17.9758 23.568 17.6608 23.505 17.5348 23.799C17.0308 24.954 16.1698 25.731 14.5528 25.731C12.8728 25.731 12.0958 24.471 12.0958 22.707V14.937C12.0958 14.811 12.1798 14.727 12.3058 14.727H15.2248C15.3508 14.727 15.4348 14.811 15.4348 14.937V21.657C15.4348 22.581 15.7708 23.022 16.4638 23.022C17.1778 23.022 17.6188 22.581 17.6188 21.657V14.937C17.6188 14.811 17.7028 14.727 17.8288 14.727H20.7478C20.8738 14.727 20.9578 14.811 20.9578 14.937V25.29C20.9578 25.416 20.8738 25.5 20.7478 25.5H18.1858C18.0598 25.5 17.9758 25.416 17.9758 25.29V23.883ZM25.6141 25.29C25.6141 25.416 25.5301 25.5 25.4041 25.5H22.4851C22.3591 25.5 22.2751 25.416 22.2751 25.29V14.937C22.2751 14.811 22.3591 14.727 22.4851 14.727H25.4041C25.5301 14.727 25.6141 14.811 25.6141 14.937V25.29ZM23.9131 13.74C22.8001 13.74 22.0441 12.942 22.0441 11.934C22.0441 10.926 22.8001 10.107 23.9131 10.107C25.0051 10.107 25.7611 10.926 25.7611 11.934C25.7611 12.942 25.0051 13.74 23.9131 13.74ZM26.7883 10.548C26.7883 10.422 26.8723 10.338 26.9983 10.338H29.9173C30.0433 10.338 30.1273 10.422 30.1273 10.548V22.056C30.1273 22.749 30.2533 23.085 30.8203 23.085C31.0093 23.085 31.1983 23.043 31.3663 23.001C31.5133 22.959 31.6183 22.959 31.6183 23.127V25.059C31.6183 25.164 31.5763 25.269 31.4923 25.311C30.9673 25.521 30.2953 25.71 29.5813 25.71C27.7123 25.71 26.7883 24.639 26.7883 22.476V10.548ZM32.4237 14.727C32.8227 14.727 32.9277 14.538 32.9697 14.055L33.1167 12.039C33.1167 11.913 33.2217 11.829 33.3477 11.829H35.8887C36.0147 11.829 36.0987 11.913 36.0987 12.039V14.517C36.0987 14.643 36.1827 14.727 36.3087 14.727H38.2827C38.4087 14.727 38.4927 14.811 38.4927 14.937V16.659C38.4927 16.785 38.4087 16.869 38.2827 16.869H36.0777V22.056C36.0777 22.875 36.5397 23.085 37.0647 23.085C37.4847 23.085 37.9467 22.938 38.3247 22.707C38.4717 22.623 38.5767 22.665 38.5767 22.833V24.828C38.5767 24.933 38.5347 25.017 38.4507 25.08C37.8417 25.458 36.9807 25.71 36.0357 25.71C34.2927 25.71 32.7387 24.912 32.7387 22.476V16.869H31.8567C31.7307 16.869 31.6467 16.785 31.6467 16.659V14.937C31.6467 14.811 31.7307 14.727 31.8567 14.727H32.4237ZM73.4298 16.323C73.4298 16.638 73.7868 16.68 73.9128 16.407C74.3748 15.315 75.1308 14.496 76.6008 14.496C78.2178 14.496 78.9528 15.609 78.9528 17.373V25.29C78.9528 25.416 78.8688 25.5 78.7428 25.5H75.8238C75.6978 25.5 75.6138 25.416 75.6138 25.29V18.633C75.6138 17.709 75.2778 17.268 74.5848 17.268C73.8708 17.268 73.4298 17.709 73.4298 18.633V25.29C73.4298 25.416 73.3458 25.5 73.2198 25.5H70.3008C70.1748 25.5 70.0908 25.416 70.0908 25.29V10.548C70.0908 10.422 70.1748 10.338 70.3008 10.338H73.2198C73.3458 10.338 73.4298 10.422 73.4298 10.548V16.323Z' fill='white'/%3E%3Cpath d='M100.132 16.3203C105.58 17.3761 107.272 22.4211 107.318 27.4961C107.318 27.6101 107.226 27.7041 107.112 27.7041H100.252C100.138 27.7041 100.046 27.6121 100.046 27.5001C100.026 23.5629 99.3877 20.0896 95.4865 19.9396C95.3705 19.9356 95.2725 20.0276 95.2725 20.1456V27.5001C95.2725 27.6141 95.1806 27.7061 95.0666 27.7061H88.206C88.092 27.7061 88 27.6141 88 27.5001V8.75585C88 8.64187 88.092 8.54989 88.206 8.54989H95.0686C95.1826 8.54989 95.2745 8.64187 95.2745 8.75585V15.7764C95.2745 15.8804 95.3585 15.9644 95.4625 15.9644C95.5445 15.9644 95.6185 15.9104 95.6425 15.8324C97.4081 10.0416 100.709 8.58588 106.07 8.55189C106.184 8.55189 106.276 8.64387 106.276 8.75785V15.7604C106.276 15.8744 106.184 15.9664 106.07 15.9664H100.166C100.066 15.9664 99.9856 16.0464 99.9856 16.1464C99.9856 16.2304 100.048 16.3043 100.132 16.3203ZM118.918 20.7095V16.1704C118.918 16.0564 119.01 15.9644 119.124 15.9644H124.173C124.273 15.9644 124.353 15.8844 124.353 15.7844C124.353 15.6985 124.291 15.6245 124.207 15.6085C120.256 14.8246 118.432 12.5511 118.37 8.75585C118.368 8.64387 118.458 8.54989 118.572 8.54989H125.986C126.1 8.54989 126.192 8.64187 126.192 8.75585V11.9532C126.192 12.0672 126.284 12.1592 126.398 12.1592H130.649C130.763 12.1592 130.855 12.2511 130.855 12.3651V15.7624C130.855 15.8764 130.763 15.9684 130.649 15.9684H126.398C126.284 15.9684 126.192 16.0604 126.192 16.1744V19.8356C126.192 21.1294 126.986 21.5553 128.04 21.5553C129.692 21.5553 131.323 20.8114 131.977 20.4735C132.113 20.4035 132.277 20.5015 132.277 20.6555V26.3543C132.277 26.5063 132.193 26.6463 132.059 26.7183C131.413 27.0582 129.418 28 127.136 28C122.435 27.996 118.918 26.0824 118.918 20.7095ZM109.266 27.4981V16.1704C109.266 16.0564 109.358 15.9644 109.472 15.9644H116.334C116.448 15.9644 116.54 16.0564 116.54 16.1704V27.4981C116.54 27.6121 116.448 27.7041 116.334 27.7041H109.472C109.358 27.7021 109.266 27.6101 109.266 27.4981ZM108.876 11.4913C108.876 13.4189 110.238 14.9826 112.853 14.9826C115.469 14.9826 116.83 13.4189 116.83 11.4913C116.83 9.56369 115.471 8 112.853 8C110.238 8 108.876 9.56369 108.876 11.4913Z' fill='white'/%3E%3C/svg%3E
http://www.w3.org/XML/1998/namespace
https://a16z.com/
https://a16z.com/author/martin-casado/
https://app.kit.com/forms/8349659/subscriptions
https://arxiv.org/pdf/2405.13565
https://blakesmith.me/2015/02/09/code-review-essentials-for-software-teams.html
https://blog.codinghorror.com/code-reviews-just-do-it/
https://blog.modelcontextprotocol.io/posts/2025-09-08-mcp-registry-preview/
https://blog.ravi-mehta.com/p/specs-are-the-new-source-code
https://blog.stockapp.com/good-context-good-code/
https://cdn.openai.com/pdf/6a2631dc-783e-479b-b1a4-af0cfbd38630/how-openai-uses-codex.pdf
https://cloud.google.com/discover/what-is-prompt-engineering
https://cognition.ai/
https://developers.cloudflare.com/agents/guides/remote-mcp-server/#add-authentication
https://devin.ai/agents101#introduction
https://docs.google.com/presentation/d/11CP26VhsjnZOmi9YFgLlonzdib9BLyAlgc4cEvC5Fps/edit?usp=sharing
https://docs.google.com/presentation/d/11pQNCde_mmRnImBat0Zymnp8TCS_cT_1up7zbcj6Sjg/edit?usp=sharing
https://docs.google.com/presentation/d/19mgkwAnJDc7JuJy0zhhoY0ZC15DiNpxL8kchPDnRkRQ/edit?usp=sharing
https://docs.google.com/presentation/d/1C05bCLasMDigBbkwdWbiz4WrXibzi6ua4hQQbTod_8c/edit?usp=sharing
https://docs.google.com/presentation/d/1Djd4eBLBbRkma8rFnJAWMT0ptct_UGB8hipmoqFVkxQ/edit?usp=sharing
https://docs.google.com/presentation/d/1GrVLsfMFIXMiGjIW9D7EJIyLYh_-3ReHHNd_vRfZUoo/edit?usp=sharing
https://docs.google.com/presentation/d/1Jf2aN5zIChd5tT86rZWWqY-iDWbxgR-uynKJxBR7E9E/edit?usp=sharing
https://docs.google.com/presentation/d/1MIhw8p6TLGdbQ9TcxhXSs5BaPf5d_h77QY70RHNfeGs/edit?usp=drive_link
https://docs.google.com/presentation/d/1Mfe-auWAsg9URCujneKnHr0AbO8O-_U4QXBVOlO4qp0/edit?usp=sharing
https://docs.google.com/presentation/d/1NkPzpuSQt6Esbnr2-EnxM9007TL6ebSPFwITyVY-QxU/edit?usp=sharing
https://docs.google.com/presentation/d/1bv7Zozn6z45CAh-IyX99dMPMyXCHC7zj95UfwErBYQ8/edit?usp=sharing
https://docs.google.com/presentation/d/1i0pRttHf72lgz8C-n7DSegcLBgncYZe_ppU7dB9zhUA/edit?usp=sharing
https://docs.google.com/presentation/d/1zSC2ra77XOUrJeyS85houg1DU7z9hq5Y4ebagTch-5o/edit?usp=drive_link
https://docs.google.com/presentation/d/1zT2Ofy88cajLTLkd7TcuSM4BCELvF9qQdHmlz33i4t0/edit?usp=sharing
https://docs.google.com/spreadsheets/d/1-485SLHw_zn7A-UXiz88Dgjy_qUGx87Am6HUwQrKsN8/edit?gid=0#gid=0
https://drive.google.com/file/d/11WnEbMGc9kny_WBpMN10I8oP8XsiQOnM/view?usp=sharing
https://drive.google.com/file/d/1J6lgZWcxPzpCpjujJSnW1aAkCYF6Yxv3/view?usp=drive_link
https://drive.google.com/file/d/1MZ0Qx68Vzw4x5x_XcV8XiPLp7fFDe1LJ/view?usp=drive_link
https://drive.google.com/file/d/1YtpKFVG13DHyQ2i3HOtwyVJOV90nWeL2/view?usp=drive_link
https://drive.google.com/file/d/1hwF-RIkOJ_OFy17BKhzFyCtxSS7Pcf7p/view?usp=drive_link
https://embracethered.com/blog/posts/2025/github-copilot-remote-code-execution-via-prompt-injection/
https://f.convertkit.com/ckjs/ck.5.js
https://github.blog/developer-skills/github/how-to-review-code-effectively-a-github-staff-engineers-philosophy/
https://github.com/SeanHeelan/o3_finds_cve-2025-37899/blob/master/system_prompt_uafs.prompt
https://github.com/SuperClaude-Org/SuperClaude_Framework
https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md
https://github.com/mihail911/modern-software-dev-assignments/blob/master/week3/assignment.md
https://github.com/mihail911/modern-software-dev-assignments/blob/master/week4/assignment.md
https://github.com/mihail911/modern-software-dev-assignments/blob/master/week6/assignment.md
https://github.com/mihail911/modern-software-dev-assignments/tree/master/week1
https://github.com/mihail911/modern-software-dev-assignments/tree/master/week2
https://github.com/mihail911/modern-software-dev-assignments/tree/master/week5
https://github.com/mihail911/modern-software-dev-assignments/tree/master/week7
https://github.com/mihail911/modern-software-dev-assignments/tree/master/week8
https://github.com/modelcontextprotocol/servers
https://github.com/modelcontextprotocol/typescript-sdk/tree/main?tab=readme-ov-file#server
https://github.com/vijaythecoder/awesome-claude-agents
https://graphite.dev/
https://graphite.dev/guides/ai-code-review-implementation-best-practices
https://kit.com/features/forms?utm_campaign=poweredby&utm_content=form&utm_medium=referral&utm_source=dynamic
https://last9.io/blog/traces-spans-observability-basics/
https://medium.com/@outsightai/peeking-under-the-hood-of-claude-code-70f5a94a9a62
https://notion.warp.dev/How-Warp-uses-Warp-to-build-Warp-21643263616d81a6b9e3e63fd8a7380c
https://owasp.org/www-project-top-ten/
https://reactjs.org/docs/error-decoder.html?invariant=
https://research.trychroma.com/context-rot
https://resolve.ai/
https://resolve.ai/blog/Top-5-Benefits
https://resolve.ai/blog/kubernetes-troubleshooting-in-resolve-ai
https://resolve.ai/blog/product-deep-dive
https://resolve.ai/blog/role-of-multi-agent-systems-AI-native-engineering
https://semgrep.dev/
https://semgrep.dev/blog/2025/finding-vulnerabilities-in-modern-web-apps-using-claude-code-and-openai-codex/
https://sre.google/sre-book/introduction/
https://stytch.com/blog/model-context-protocol-introduction/
https://unit42.paloaltonetworks.com/agentic-ai-threats/#:~:text=Identity%20spoofing%20and%20impersonation:%20Attackers,accurate%20information%20exchange%20are%20critical.
https://vercel.com/
https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf
https://www.anthropic.com/claude-code
https://www.anthropic.com/engineering/claude-code-best-practices
https://www.anthropic.com/engineering/writing-tools-for-agents
https://www.dbreunig.com/2025/06/22/how-contexts-fail-and-how-to-fix-them.html
https://www.figma.com/slides/kwbcmtqTFQMfUhiMH8BiEx/Warp---Stanford--Copy-?node-id=9-116&t=oBWBCk8mjg2l2NR5-1
https://www.linkedin.com/in/bcherny/
https://www.linkedin.com/in/brentju/
https://www.linkedin.com/in/febielin/
https://www.linkedin.com/in/gaspargarcia/
https://www.linkedin.com/in/isaacevans/
https://www.linkedin.com/in/mayank-ag/
https://www.linkedin.com/in/mganjoo/
https://www.linkedin.com/in/silasalberti/
https://www.linkedin.com/in/tomasreimers/
https://www.linkedin.com/in/zachlloyd/
https://www.mihaileric.com/
https://www.promptingguide.ai/techniques
https://www.reillywood.com/blog/apis-dont-make-good-mcp-tools/
https://www.splunk.com/en_us/blog/learn/sast-vs-dast.html
https://www.warp.dev/
https://www.warp.dev/university/getting-started/warp-vs-claude-code
https://www.warp.dev/university?slug=university
https://www.youtube.com/watch?v=7xTGNNLPyMI
https://www.youtube.com/watch?v=T9aRN5JkmL8
https://www.youtube.com/watch?v=TswQeKftnaw
https://x.com/rohanpaul_ai/status/1959414096589422619

## robots#001

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/png" sizes="16x16" href="favicon-16x16.png" />
    <link rel="icon" type="image/png" sizes="32x32" href="favicon-32x32.png" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CS146S: The Modern Software Developer - Stanford University</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script type="module" crossorigin src="assets/index-CgRb4FxC.js"></script>
    <link rel="stylesheet" crossorigin href="assets/index-LDF6HMRx.css">
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>

## README#001

# CS146S: The Modern Software Developer — Offline Cache

**Stanford University | Fall 2025**  
Cached on: April 2, 2026  
Original site: https://themodernsoftware.dev/

---

## How to Use This Offline Cache

1. **Open `index.html`** in any web browser — this is the main course page with full navigation (Overview, Syllabus, FAQ).
2. All reading materials that could be downloaded are saved locally and linked from the index page.
3. Use the **Syllabus** tab to navigate by week and access all readings, assignments, and lecture slides.

---

## Directory Structure

## README#002

```
CS146S_offline/
├── index.html              ← Main course page (start here)
├── README.md               ← This file
│
├── pdfs/                   ← Downloaded PDF documents
│   ├── how-openai-uses-codex.pdf
│   ├── how-anthropic-uses-claude-code.pdf
│   └── ai-assisted-code-review-assessment.pdf
│
├── pages/                  ← Downloaded article web pages (31 pages)
│   ├── prompt-engineering-overview.html
│   ├── prompt-engineering-guide.html
│   ├── mcp-introduction.html
│   ├── mcp-server-authentication.html
│   ├── mcp-food-for-thought.html
│   ├── mcp-registry-preview.html
│   ├── specs-are-the-new-source-code.html
│   ├── how-long-contexts-fail.html
│   ├── devin-coding-agents-101.html
│   ├── writing-effective-tools-for-agents.html
│   ├── claude-code-best-practices.html
│   ├── good-context-good-code.html
│   ├── peeking-under-the-hood-of-claude-code.html  ← placeholder (Medium blocked)
│   ├── warp-vs-claude-code.html
│   ├── how-warp-uses-warp.html
│   ├── sast-vs-dast.html
│   ├── copilot-prompt-injection-rce.html
│   ├── finding-vulnerabilities-claude-codex.html
│   ├── agentic-ai-threats.html
│   ├── owasp-top-ten.html
│   ├── context-rot.html
│   ├── code-reviews-just-do-it.html
│   ├── how-to-review-code-effectively.html
│   ├── ai-code-review-best-practices.html
│   ├── code-review-essentials.html
│   ├── lessons-from-ai-code-reviews.html
│   ├── sre-introduction.html
│   ├── observability-basics.html
│   ├── multi-agent-systems-ai-native.html
│   ├── benefits-agentic-ai-oncall.html
│   └── kubernetes-troubleshooting-ai.html
│
└── site/                   ← Original site assets (HTML, CSS, JS)
    └── themodernsoftware.dev/
        ├── index.html
        ├── assets/
        │   ├── index-CgRb4FxC.js
        │   └── index-LDF6HMRx.css
        └── ...
```

## README#003

---

## What Requires Internet Access

The following resources require an internet connection as they could not be downloaded automatically:

| Resource | Reason |
|---|---|
| YouTube videos (3 links) | Video files not downloaded by design |
| Google Slides presentations (14 links) | Require Google account |
| Google Drive files (5 links) | Require Google account |
| GitHub repositories/pages | Live code repositories |
| "Peeking Under the Hood of Claude Code" | Medium.com blocks automated access |

---

## Course Summary

**CS146S** is a Stanford course on modern AI-assisted software development. It covers:

- **Week 1:** Introduction to LLMs and prompt engineering
- **Week 2:** Coding agents, tool use, and MCP (Model Context Protocol)
- **Week 3:** AI IDEs, context management, and PRDs for agents
- **Week 4:** Claude Code and agentic coding workflows
- **Week 5:** Warp terminal and AI-native development
- **Week 6:** AI security, prompt injection, and vulnerability detection
- **Week 7:** AI-powered code review
- **Week 8:** Full-stack AI development and deployment
- **Week 9:** SRE, observability, and agentic on-call engineering
- **Week 10:** Future of AI in software engineering

## README#004

**Instructor:** Mihail Eric  
**TAs:** Febie Lin, Brent Ju  
**Units:** 3  
**Classroom:** 420-041

## Vibe_Coding_Playbook#001

## Page 1

ELite 20: Vibe Coding-
成为 AI 原生构建者的终
终极生存指南
从入学测试到巅峰交付：你的8周架构蓝图
L （ISyste Status: Ready for Bot］ | Tversiom: 2.0］

## Page 2

范式重构：跳出语法陷阱，构建认知系统
学语法
学会学习
学会选择
（Syntax）
（Learn）：
（Decide）：
掌皚如何获取结
建立顶販判断力，
构化知识，与Al
精准記置注 力
协作共生。
与宽源。
背诵坛炉各案
核心认知系统
（Rote Me.1v
rization）
（Core Cognitive
System）
标准化产出
（Standard Output）
学会识別
（Sensemaking）：
在复杂系锩中鈭別
真伪，汗估AI输
工业教育时代：知识获取成本极高。教育
出局量。
的本质被错误设定为
〕“学语法”与
“背诵
标准答案”。
>终极目标：8周内，从代码打字员进化为能交付
现实商业价值的 AI 原生构建者。

## Page 3

Vibe Coding 核心定义：结果优先、代理驱动、产出物为中心
维度 （Dimension）
传统编程
Vibe Coding
学习路径（Path）
先苦练语言语法
先明确预期结果
执行方式（Execution）
逐行手动编写代码
宏观编排 AI 代理（Agents）
能力重心 （Focus）
精通语法记忆
极致的问题分解能力
工作模式（Mode）
个人独立闭门造车
人机 （Human + AI）高效共建
交付现实世界生产级产出物
最终成果 （Output）
完成标准化的课后作业
（Artifacts）

## Page 4

真正的捷径：理解源于执行
Job / Value
重复
（Repeat）
理解
（Understand）
修复
（Fix）
失败
（Fail）
构建
（Build）
传统路径：学习一练习一应用一就业
Vibe Coding 彻底推翻了“先懂后做”的幻觉。
只有在“运行-报错-修复”的高压循环中，真正的底层理解才会涌现。

## Page 5

你的底层操作系统：NEOLAF 三阶段框架
ORTAFLON
Stage 1：
Stage 3：
Stage 2: ILT 生产工作室
苏格拉底式精通
AAR 作品集飞轮
（绝对核心 - 80% 时间）
（最小化理论）
（技能复利）
E日 IREY
仅传授必要的系统运作心理
Vibe Coding的真正战场。以产出
强制记录尝试了什么、失败
模型（如 API、前后基础）
物为中心，Agent优先。在这里，
在咖里、AI 做了什么、我
目标：懂得到足以构雞，而
你必须产生真实的现实世界价值。
改了什么。将碎片经验锁定
非懂得劉足以讲课。
为永久肌肉记忆。
AGENT CORE

## Page 6

## Vibe_Coding_Playbook#002

每日执行引擎：Vibe Coding 黄金闭环
1. 定义结果（Define Outcome）：
明确当日目标
©0. AAR 反恩（Reflection：
2.转化为 Agent任务：
总结策脆与AI 盲区交*
设定目标、约束、可用工具
5. 交付产出物（Ship Artifact）：
3. Agent 执行：
提交 Demo或Repo
AI 生成代码、搭建脚手架
4.
调试循环（Debug Loop-
The Real Learning Engine）
运行 报错 喂给 AI-修复一重复

## Page 7

DATBFLEN
你的非对称武器：专属伴随代理 （Companion Agent）
不要把AI当作自动写代码的机器。它是你的系统级导师：
任务翻译官
（Task Translator）
技能教练 （Skil1 Coach）：
将你模糊的想法维转化为机器
在卡壳时精准提示下一步最佳动
可执行的结构化指令。
作及推荐工具。
Elite 20
Companion
Agent
调试伙伴（Debug Partner）：
AAR 执行者 （AAR Enforcer）：
深度解析报错日志，不仅提供修
强制触发复盘机制，榨取每一次
复代码，更解釋崩溃根因。
失败中的认知红利。

## Page 8

8 周架构蓝图（上半场）：极速筑基与结构化构建
W4：多 Agent 协作
W3: CLI + AI IDE + Repo
抽象
W2: Agent Skills + MCP
Focus：处理长文本与复杂
结构一致性。
Artifact: 10 页可投稿级
W1：快速建站与部署
Focus：命令行记忆与
学术论文（LaTex）。
Context 工程。
Artifact：将复杂 GitHub
Focus：工具链熟练度与
Repo 逆向重构为结构化课
API 交互。
程。
Artifact：全自动内容生
Focus:AI 极逨生成，
成并发布至微信平台。
GitHub 上线。
Artifact： 可访问的公开
网id（github.io）。

## Page 9
