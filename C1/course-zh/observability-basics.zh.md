---
source_file: observability-basics.html
title: 调用链与调用段：你该知道的可观测性基础 | Last9
---

在现代软件架构中，应用程序不只是变得更大——它们正变得更分布式。随着微服务、无服务器函数和容器跨多个环境运行，想要弄清系统内部正在发生什么，就像在暴风雨中追踪一滴雨水。

这正是调用链与调用段发挥作用的地方。这些可观测性工具不只是流行语——它们是理解复杂分布式系统的秘密武器。让我们来拆解什么是调用链和调用段、它们为什么重要，以及你如何利用它们更快地排障并构建更可靠的系统。


## 理解调用链与调用段：核心概念
调用链
记录了一个请求在分布式系统中流转的完整旅程。可以把调用链想象成一个请求从头到尾的完整故事——从用户点击按钮开始，直到看到结果为止。

调用段
是调用链的构建模块。每个调用段代表旅程中的一个工作单元——比如一次数据库查询、一次 API 调用或一次函数执行。调用段彼此嵌套，以展示操作之间的父子关系。

简单来说，它们的关系是：

- 一条调用链包含多个调用段
- 每个调用段代表一个操作
- 调用段包含计时数据和元数据
- 调用段可以嵌套，以展示操作之间的关联


```
Trace
├── Span (API Gateway)
│   ├── Span (Auth Service)
│   └── Span (User Service)
│       └── Span (Database Query)
└── Span (Response Formatting)
```
💡
如果你好奇调用链和调用段如何与指标、日志和事件配合，这篇文章对四者做了全面解析。

## 调用链与调用段对 DevOps 从业者的价值
你正在运行一个拥有几十个微服务的复杂系统。突然，用户反馈结账流程很慢。没有调用链追踪，你就得逐个检查每个服务，浪费宝贵时间。

有了调用链和调用段，你可以：

1. 即时找到瓶颈：精确看到哪个服务或函数耗时过长
2. 跨服务边界调试：跟随请求在服务之间跳转的轨迹
3. 理解依赖关系：可视化你的服务如何相互连接与依赖
4. 改善性能：精准识别并修复缓慢的操作
5. 缩短平均恢复时间（MTTR）：问题出现时更快找到根本原因


## 调用链与调用段的技术实现
让我们深入探讨分布式系统中调用链追踪的工作原理。


### 调用链上下文与传播
要让调用链追踪跨服务边界工作，每个服务都需要知道自己正在处理同一个请求的一部分。这通过
上下文传播
实现——在服务之间传递调用链 ID 和调用段 ID。

当请求首次进入你的系统时，它会被分配一个唯一的调用链 ID。当请求在服务之间流转时，这个 ID 随之传递（通常作为 HTTP 头）。每个服务随后创建自己的调用段，但将它们关联到同一条调用链。


### 调用段属性与事件
调用段不只是时间戳——它们包含丰富的数据：

- 名称：这个调用段代表什么操作
- 计时：开始与结束时间
- 状态：成功、错误等
- 属性：自定义键值对（如 user_id 或 cart_size）
- 事件：调用段内值得注意的事件
- 链接：与其他调用段的连接


### 采样策略
追踪一切会产生海量数据。因此大多数系统采用采样——只收集一定比例的调用链。明智的采样策略包括：

- 头部采样：在请求开始时决定是否采样
- 尾部采样：在请求完成后决定（更有利于捕获错误）
- 优先级采样：始终追踪重要操作，而对常规操作进行采样

💡
如果你想了解可观测性、遥测与监控之间的区别，请看这篇有用的文章：
Observability vs Telemetry vs Monitoring
。

## 调用链实施指南：工具与框架
准备好为你的系统添加调用链追踪了吗？你需要以下内容：


### OpenTelemetry：行业标准
OpenTelemetry
已成为实现调用链与调用段的首选框架。它提供：

- 支持所有主流编程语言的库
- 与厂商无关的 API 和 SDK
- 针对流行框架的自动埋点
- 一致的数据收集与导出方式


### 调用链工具箱
有多种工具可以帮助你收集、存储和可视化调用链：

kg-card-begin: html
| 工具 | 类型 | 最适合 |
| Last9 | 一体化可观测性 | 高性价比、高基数可观测性，定价可预测 |
| Jaeger | 开源调用链追踪 | 自托管的调用链可视化 |
| Zipkin | 开源调用链追踪 | 简单的分布式调用链追踪 |
| Grafana Tempo | 调用链后端 | 与 Grafana 仪表盘集成 |
| OpenTelemetry Collector | 数据采集管道 | 处理和路由遥测数据 |

kg-card-end: html
如果你在寻找一个符合预算的可观测性方案，
Last9
值得一试。其定价基于摄入的事件数，成本可预测。此外，我们的平台能大规模处理高基数数据，并与 OpenTelemetry 和 Prometheus 集成，把你的指标、日志和调用链汇聚到一处。


### 在代码中实现调用链追踪
下面是一个使用 OpenTelemetry 在 Node.js 应用中创建调用段的简化示例：


```
// Initialize the OpenTelemetry SDK (once in your app)
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const provider = new NodeTracerProvider();
const exporter = new OTLPTraceExporter({
  url: 'http://localhost:4318/v1/traces',
});
provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
provider.register();

// Get a tracer
const { trace } = require('@opentelemetry/api');
const tracer = trace.getTracer('my-service');

// Create spans in your code
async function processOrder(orderId) {
  const span = tracer.startSpan('process-order');
  
  // Add attributes to the span
  span.setAttribute('order.id', orderId);
  span.setAttribute('customer.type', 'premium');
  
  try {
    // Do work...
    
    // Create a child span
    const dbSpan = tracer.startSpan('database-query', {
      parent: span,
    });
    
    try {
      // Run database query...
      dbSpan.end();
    } catch (error) {
      dbSpan.setStatus({ code: SpanStatusCode.ERROR });
      dbSpan.recordException(error);
      dbSpan.end();
      throw error;
    }
    
    span.end();
  } catch (error) {
    span.setStatus({ code: SpanStatusCode.ERROR });
    span.recordException(error);
    span.end();
    throw error;
  }
}
```
💡
想知道 OpenTelemetry 与传统 APM 工具的对比？这篇文章解析了关键差异：
OpenTelemetry vs Traditional APM Tools
。

## 高级调用链追踪技术
掌握基础追踪之后，这些高级技术能把你的可观测性提升到新的水平。


### 分布式上下文管理
在复杂系统中，你需要管理的上下文不只是调用链 ID。W3C Trace Context 规范为以下方面提供了标准：

- traceparent：包含调用链 ID 和父调用段 ID
- tracestate：允许厂商添加自定义上下文数据

使用这些头能确保你的调用链追踪跨不同服务和厂商正常工作。


### 调用链、指标与日志之间的关联
可观测性的真正威力来自连接不同的信号：

- 示例调用链（Exemplar traces）：把指标与生成它们的调用链关联起来
- 日志中的调用链 ID：在日志消息中加入调用链 ID 以便交叉引用
- 自定义属性：在所有遥测类型中使用一致的属性


### 错误处理与异常追踪
当异常发生时，调用段可以提供关键上下文：

- 将调用段标记为错误状态
- 记录异常及其堆栈跟踪
- 在调用段中添加事件，展示错误的演进过程
- 创建携带错误上下文跨服务边界传递的 baggage 项

💡
要深入了解如何防患于未然并提升系统可靠性，请看这篇关于主动监控的文章：
Proactive Monitoring
。

## 现实中的调用链模式与反模式

### 有效的调用链模式
有意义的调用段命名：使用一致的命名约定，如
service_name/operation

合适的粒度：为重要操作创建调用段，而不是每个函数调用

正确的上下文传播：确保调用链上下文流经所有通信通道

有用的属性：添加有助于排障的属性，如用户 ID 或功能开关

性能意识：注意过度创建调用段带来的开销


### 应避免的调用链反模式
过度埋点：创建太多调用段会导致性能问题

缺失上下文：未能传播上下文会破坏跨服务边界的调用链

命名不一致：使用不同的命名标准会让调用链更难解读

数据过多：把大体积负载放进调用段会压垮你的追踪后端

忽视第三方服务：缺少外部调用的调用段会制造盲区

💡
了解可观测性如何在大语言模型的性能与可靠性中发挥关键作用：
LLM Observability
。

## 调用链与调用段的业务价值：超越技术收益
调用链不只是用来排障的——它还能提供业务洞察：

- 端到端追踪关键用户旅程
- 衡量关键业务操作的性能
- 基于调用链数据设定 SLO（服务级别目标）
- 用真实用户视角量化性能问题的代价
- 通过为调用段添加相关属性来构建业务上下文

当你能展示技术改进如何影响用户体验和业务指标时，你就打通了 DevOps 与业务相关方之间的鸿沟。


## 结语
调用链与调用段赋予你透视分布式系统的 X 光视觉。它们揭示服务之间隐藏的连接、精准定位性能瓶颈，并大幅加快调试速度。

随着系统日益复杂，这种可观测性不再是奢侈品——而是必需品。

💡
如果你想继续参与关于分布式调用链追踪与可观测性的讨论，欢迎加入我们的
Discord 社区
，DevOps 从业者在这里分享他们的经验与最佳实践！

## 常见问题

### 调用链追踪与日志记录有什么区别？
日志记录捕捉离散事件，而调用链追踪展示跨服务操作之间的关系。日志告诉你发生了什么；调用链告诉你它是如何发生的。


### 添加调用链追踪会拖慢我的应用吗？
现代追踪库的开销极小——配置得当时通常性能影响低于 3%。通过采样，你还可以进一步降低这一影响。


### 我需要修改所有代码才能添加调用链追踪吗？
不一定。许多框架提供自动埋点，只需极少的代码改动即可加入追踪。OpenTelemetry 为大多数语言的流行框架提供自动埋点。


### 分布式调用链追踪会产生多少数据？
这取决于流量、采样率和调用段细节，差异很大。繁忙的系统每天可能产生几 GB 到几 TB 的数据。这就是为什么选择合适的可观测性平台对成本控制很重要。


### 调用链对安全与合规有帮助吗？
有！调用链为请求在系统中的流转创建了审计轨迹。借助合适的属性，你可以追踪哪些用户或服务在何时访问了什么数据。


### 调用链与调用段如何与其他可观测性信号配合？
调用链与指标、日志互为补充。指标从高层展示系统健康状况，日志提供详细事件，而调用链把各个环节串联起来，展示跨服务的请求流转。
