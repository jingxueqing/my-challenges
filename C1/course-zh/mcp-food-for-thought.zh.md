---
source_file: mcp-food-for-thought.html
title: API 并不适合直接转化为 MCP 工具（APIs don't make good MCP tools）
---

# API 并不适合直接转化为 MCP 工具

模型上下文协议（MCP）如今风头正劲。它已成为让大语言模型访问他人编写的工具的事实标准——这当然也把它们变成了智能体（agent）。但是，为新 MCP 服务器编写工具并不容易，因此人们经常提议把现有 API 自动转换成 MCP 工具，通常借助 OpenAPI 元数据来实现（参见 1、2）。

根据我的经验，这种做法可行，但效果并不好。原因有如下几点：

## 智能体难以应对大量工具

众所周知，VS Code 的工具数量硬性上限是 128 个——但许多模型在远未达到这个数字之前，就已在工具调用准确性上力不从心了。此外，每个工具及其描述都会占用宝贵的上下文窗口空间。

大多数 Web API 在设计时并没有考虑这些约束！当这些 API 由代码调用时，一个产品领域拥有几十个 API 没问题；但如果把每个 API 都映射为一个 MCP 工具，结果可能就不太理想了。

从零开始设计的 MCP 工具通常比单个 Web API 灵活得多，每个工具可以完成相当于若干个单独 API 的工作。

## API 会迅速撑爆上下文窗口

设想一个 API，一次返回 100 条记录，每条记录都很宽（比如 50 个字段）。把这些结果原样发给智能体将消耗大量 Token；即使一次查询只需要其中几个字段，每个字段也都会进入上下文窗口。

API 通常按记录数量分页，但记录之间的大小差异可能很大。一条记录可能包含占用 100,000 个 Token 的大文本字段，而另一条可能只包含 10 个。把这些 API 结果直接塞进智能体的上下文窗口就是一场赌博：有时没事，有时就会爆炸。

数据格式本身也可能成为问题。如今大多数 Web API 返回 JSON，但 JSON 是一种 Token 效率极低的格式。看这个：

```json
[
  {
    "firstName": "Alice",
    "lastName": "Johnson",
    "age": 28
  },
  {
    "firstName": "Bob",
    "lastName": "Smith",
    "age": 35
  }
]
```

对比同样数据的 CSV 格式：

```csv
firstName,lastName,age
Alice,Johnson,28
Bob,Smith,35
```

CSV 数据要简洁得多——每条记录消耗的 Token 只有 JSON 的一半。通常来说，对于嵌套数据，CSV、TSV 或 YAML 比 JSON 更合适。

这些问题都不是不可逾越的。你可以设想自动添加工具参数，让智能体能投影（project）字段；自动截断或摘要过大的结果；以及自动把 JSON 结果转换为 CSV（嵌套数据则转为 YAML）。但我见过的大多数服务器，这些事一件都没做。

## API 没有充分利用智能体的独特能力

API 返回结构化数据，供程序化消费。这往往正是智能体从工具调用中所需要的……但智能体同样能处理其他更自由形式的指令。

例如，一个 `ask_question` 工具可以对某些文档执行 RAG 查询，然后以纯文本形式返回信息，用于指导下一次工具调用——完全跳过结构化数据。

再比如，对 `search_cities` 工具的调用可以既返回结构化的城市列表，又附带对下一步调用的建议：

```csv
city_name,population,country,region
Tokyo,37194000,Japan,Asia
Delhi,32941000,India,Asia
Shanghai,28517000,China,Asia

Suggestion: To get more specific information (weather, attractions, demographics), try calling get_city_details with the city_name parameter.
```

这种分层与工具链式调用在 MCP 服务器中可能非常有效，而如果把 API 自动转换成工具，你就完全错失了这一点。

## 如果智能体需要调用 API，它其实可以直接调用

如今像 Claude Code 这样的智能体在编写并执行代码（包括调用 Web API 的脚本）方面能力极强。有些人甚至据此主张根本不需要 MCP！

我不同意这个结论，但我确实认为我们应该滑向冰球将要到达的地方。智能体的沙箱化正在快速改进，如果让智能体直接调用 API 既简单又安全，那我们不妨就这么做，省去中间层。

## 结论

智能体与 API 的典型消费者有着根本的不同。从现有 API 自动创建 MCP 工具是可能的，但这样做效果大概率不好。只有为智能体独特的能力与局限量身设计的工具，才能让它们发挥出最佳水平。
