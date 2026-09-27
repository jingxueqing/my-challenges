# 待译批次 17

> 逐段翻译为简体中文：保留 Markdown 标题/列表/代码块，不改写、不增删、不总结。
> 术语严格遵循 glossary/术语表.json（keep_en 中的词保留英文）。
> 每段译文之前必须写一条定位标记，格式 `<!-- seg:文档名#段号 -->`，文档名与段号照抄下方小节标题。
> 例：小节标题为 `## context-rot#003` 时，输出 `<!-- seg:context-rot#003 -->`。

## mcp-server-authentication#010

> .envecho 'GITHUB_CLIENT_SECRET="your-client-secret"' >> .envcat .env">

Run the following command to start the development server:

Terminal window npm start

Your MCP server is now running on http://localhost:8788/mcp .

In a new terminal, run the MCP inspector â . The MCP inspector is an interactive MCP client that allows you to connect to your MCP server and invoke tools from a web browser.

Terminal window npx @modelcontextprotocol/inspector@latest

Open the MCP inspector in your web browser:

Terminal window open http://localhost:5173

In the inspector, enter the URL of your MCP server, http://localhost:8788/mcp

In the main panel on the right, click the OAuth Settings button and then click Quick OAuth Flow .

You should be redirected to a GitHub login or authorization page. After authorizing the MCP Client (the inspector) access to your GitHub account, you will be redirected back to the inspector.

Click Connect in the sidebar and you should see the "List Tools" button, which will list the tools that your MCP server exposes.

#### Step 2.2 â Create a new OAuth App for production

You'll need to repeat Step 2.1 to create a new OAuth App for production.

## mcp-server-authentication#011

Navigate to github.com/settings/developers â to create a new OAuth App with the following settings:

Application name : My MCP Server (production)

Homepage URL : Enter the workers.dev URL of your deployed MCP server (ex: worker-name.account-name.workers.dev )

Authorization callback URL : Enter the /callback path of the workers.dev URL of your deployed MCP server (ex: worker-name.account-name.workers.dev/callback )

For the OAuth app you just created, add the client ID and client secret, using Wrangler CLI:

Terminal window npx wrangler secret put GITHUB_CLIENT_ID

Terminal window npx wrangler secret put GITHUB_CLIENT_SECRET

npx wrangler secret put COOKIE_ENCRYPTION_KEY # add any random string here e.g. openssl rand -hex 32

Warning
 When you create the first secret, Wrangler will ask if you want to create a new Worker. Submit "Y" to create a new Worker and save the secret.

Set up a KV namespace

a. Create the KV namespace:

Terminal window npx wrangler kv namespace create "OAUTH_KV"

b. Update the wrangler.jsonc file with the resulting KV ID:

{

" kvNamespaces " : [

{

" binding " : "OAUTH_KV" ,

" id " : "<YOUR_KV_NAMESPACE_ID>"

}

]

}

" } ]}">

Deploy the MCP server to your Cloudflare workers.dev domain:

## mcp-server-authentication#012

Terminal window npm run deploy

Connect to your server running at worker-name.account-name.workers.dev/mcp using the AI Playground â , MCP Inspector, or other MCP clients , and authenticate with GitHub.

## Next steps

MCP Tools Add tools to your MCP server.

Authorization Customize authentication and authorization.

## observability-basics#001

Apr 23rd, 2025

# Traces & Spans: Observability Basics You Should Know 
 Learn how traces and spans help you see inside distributed systems—so you can troubleshoot faster and build more reliable software.
 
 Anjali Udasi

#### 
Contents

In modern software architecture, applications aren't just getting bigger—they're getting more distributed. With microservices, serverless functions, and containers running across multiple environments, understanding what's happening inside your systems can feel like trying to track a single raindrop in a storm.
 That's where traces and spans come in. These observability tools aren't just buzzwords—they're your secret weapon for making sense of complex distributed systems. Let's break down what traces and spans are, why they matter, and how you can use them to troubleshoot faster and build more reliable systems.

## observability-basics#002

## Understanding Traces and Spans: Core Concepts
 Traces capture the journey of a request as it moves through your distributed system. Think of a trace as the complete story of a request from start to finish—from when a user clicks a button until they see the result.
 Spans are the building blocks of traces. Each span represents a unit of work within that journey—like a database query, an API call, or a function execution. Spans nest within each other to show parent-child relationships between operations.
 Here's the relationship in simple terms:
 A trace contains multiple spans
 Each span represents one operation
 Spans have timing data and metadata
 Spans can be nested to show how operations relate to each other
 Trace 
 ├── Span (API Gateway) 
 │ ├── Span (Auth Service) 
 │ └── Span (User Service) 
 │ └── Span (Database Query) 
 └── Span (Response Formatting) 💡
 If you're curious how traces and spans fit alongside metrics, logs, and events , this post breaks down all four.

## observability-basics#003

## Benefits of Traces and Spans for DevOps Professionals
 You're running a complex system with dozens of microservices. Suddenly, users report the checkout process is slow. Without tracing, you'd need to check each service individually, wasting precious time.
 With traces and spans, you can:
 Find bottlenecks instantly : See exactly which service or function is taking too long
 Debug across service boundaries : Follow requests as they jump between services
 Understand dependencies : Visualize how your services connect and depend on each other
 Improve performance : Identify and fix slow operations with precision
 Reduce mean time to recovery (MTTR) : Get to the root cause faster when issues arise

## Technical Implementation of Traces and Spans
 Let's get into the nuts and bolts of how tracing works in distributed systems.

## observability-basics#004

### Trace Context and Propagation
 For tracing to work across service boundaries, each service needs to know it's handling part of the same request. This happens through context propagation —passing a trace ID and span ID between services.
 When a request first hits your system, it gets assigned a unique trace ID. As the request moves between services, this ID travels with it (usually as HTTP headers). Each service then creates its own spans but links them to the same trace.

### Span Attributes and Events
 Spans aren't just timestamps—they're rich with data:
 Name : What operation this span represents
 Timing : Start and end times
 Status : Success, error, etc.
 Attributes : Custom key-value pairs (like user_id or cart_size )
 Events : Notable occurrences within the span
 Links : Connections to other spans

## observability-basics#005

### Sampling Strategies
 Tracing everything can create massive amounts of data. That's why most systems use sampling—collecting only a percentage of traces. Smart sampling strategies include:
 Head-based sampling : Decide whether to sample at the beginning of a request
 Tail-based sampling : Decide after the request completes (better for catching errors)
 Priority sampling : Always trace important operations, but sample routine ones
 💡
 If you're looking to understand the differences between observability, telemetry, and monitoring, check out this helpful post: Observability vs Telemetry vs Monitoring .

## Tracing Implementation Guide: Tools and Frameworks
 Ready to add tracing to your systems? Here's what you need:

### OpenTelemetry: The Industry Standard
 OpenTelemetry has become the go-to framework for implementing traces and spans. It provides:
 Libraries for all major programming languages
 A vendor-neutral API and SDK
 Automatic instrumentation for popular frameworks
 A consistent way to collect and export data

### The Tracing Toolbox
 Several tools can help you collect, store, and visualize your traces:

Tool 
 Type 
 Best For

## observability-basics#006

Last9 
 All-in-one observability 
 Cost-effective, high-cardinality observability with predictable pricing

Jaeger 
 Open-source tracing 
 Self-hosted tracing visualization

Zipkin 
 Open-source tracing 
 Simple distributed tracing

Grafana Tempo 
 Tracing backend 
 Integration with Grafana dashboards

OpenTelemetry Collector 
 Data collection pipeline 
 Processing and routing telemetry data

If you're after an observability solution that fits your budget, Last9 is worth checking out. With pricing based on ingested events, it keeps things predictable. Plus, our platform handles high-cardinality data at scale and integrates with OpenTelemetry and Prometheus to bring your metrics, logs, and traces together in one place.

## observability-basics#007

### Implementing Tracing in Your Code
 Here's a simplified example of how to create spans in a Node.js application using OpenTelemetry:
 // Initialize the OpenTelemetry SDK (once in your app) 
 const { NodeTracerProvider } = require ( '@opentelemetry/sdk-trace-node' ); 
 const { SimpleSpanProcessor } = require ( '@opentelemetry/sdk-trace-base' ); 
 const { OTLPTraceExporter } = require ( '@opentelemetry/exporter-trace-otlp-http' ); 
 
 const provider = new NodeTracerProvider (); 
 const exporter = new OTLPTraceExporter ({ 
 url: 'http://localhost:4318/v1/traces' , 
 }); 
 provider. addSpanProcessor ( new SimpleSpanProcessor (exporter)); 
 provider. register (); 
 
 // Get a tracer 
 const { trace } = require ( '@opentelemetry/api' ); 
 const tracer = trace. getTracer ( 'my-service' ); 
 
 // Create spans in your code 
 async function processOrder ( orderId ) { 
 const span = tracer. startSpan ( 'process-order' ); 
 
 // Add attributes to the span 
 span. setAttribute ( 'order.id' , orderId); 
 span. setAttribute ( 'customer.type' , 'premium' ); 
 
 try { 
 // Do work... 
 
 // Create a child span 
 const dbSpan = tracer. startSpan ( 'database-query' , { 
 parent: span, 
 }); 
 
 try { 
 // Run database query... 
 dbSpan. end (); 
 } catch (error) { 
 dbSpan. setStatus ({ code: SpanStatusCode. ERROR }); 
 dbSpan. recordException (error); 
 dbSpan. end (); 
 throw error; 
 } 
 
 span. end (); 
 } catch (error) { 
 span. setStatus ({ code: SpanStatusCode. ERROR }); 
 span. recordException (error); 
 span. end (); 
 throw error; 
 } 
 } 💡
 Wondering how OpenTelemetry stacks up against traditional APM tools? This post breaks down the key differences: OpenTelemetry vs Traditional APM Tools .

## observability-basics#008

## Advanced Tracing Techniques
 Once you've got basic tracing in place, these advanced techniques can take your observability to the next level.

### Distributed Context Management
 In complex systems, you need to manage context beyond just trace IDs. The W3C Trace Context specification provides standards for:
 traceparent : Contains the trace ID and parent span ID
 tracestate : Allows vendors to add custom context data
 Using these headers ensures your tracing works across different services and vendors.

### Correlation Between Traces, Metrics, and Logs
 The real power of observability comes from connecting different signals:
 Exemplar traces : Link metrics to the traces that generated them
 Trace IDs in logs : Add trace IDs to log messages for cross-referencing
 Custom attributes : Use consistent attributes across all telemetry types

## observability-basics#009

### Error Handling and Exception Tracking
 When exceptions occur, spans can provide crucial context:
 Mark spans with error status
 Record exceptions with stack traces
 Add events to spans that show the error's progression
 Create baggage items that carry error context across service boundaries
 💡
 For a deeper look at staying ahead of issues and improving system reliability, check out this post on proactive monitoring: Proactive Monitoring .

## Real-World Tracing Patterns and Anti-Patterns

### Effective Tracing Patterns
 Meaningful span names : Use consistent naming conventions like service_name/operation 
 Right granularity : Create spans for significant operations, not every function call
 Proper context propagation : Ensure trace context flows through all communication channels
 Useful attributes : Add attributes that help with troubleshooting, like user IDs or feature flags
 Performance awareness : Watch out for the overhead of excessive span creation

## observability-basics#010

### Tracing Anti-Patterns to Avoid
 Over-instrumentation : Creating too many spans can cause performance issues
 Missing context : Failing to propagate context breaks traces across service boundaries
 Inconsistent naming : Using different naming standards makes traces harder to interpret
 Too much data : Putting large payloads in spans can overwhelm your tracing backend
 Ignoring third-party services : Missing spans for external calls creates blind spots
 💡
 Explore how observability plays a crucial role in the performance and reliability of LLMs: LLM Observability .

## Business Value of Traces and Spans: Beyond Technical Benefits
 Traces aren't just for troubleshooting—they can provide business insights too:
 Track critical user journeys from end-to-end
 Measure the performance of key business operations
 Set SLOs (Service Level Objectives) based on trace data
 Quantify the cost of performance issues in real user terms
 Create business context by adding relevant attributes to spans
 When you can show how technical improvements affect user experience and business metrics, you bridge the gap between DevOps and business stakeholders.

## observability-basics#011

## Conclusion
 Traces and spans give you X-ray vision into your distributed systems. They reveal the hidden connections between services, pinpoint performance bottlenecks, and dramatically speed up debugging.
 As systems grow more complex, this kind of observability isn't a luxury—it's essential. 
 💡
 If you'd like to continue the conversation about distributed tracing and observability, join our Discord Community where DevOps professionals share their experiences and best practices!

## FAQs

### What's the difference between tracing and logging?
 Logging captures discrete events, while tracing shows the relationships between operations across services. Logs tell you what happened; traces show you how it happened.

### Will adding tracing slow down my application?
 Modern tracing libraries add minimal overhead — typically less than 3% performance impact when properly configured. With sampling, you can further reduce this impact.

### Do I need to modify all my code to add tracing?
 Not necessarily. Many frameworks offer automatic instrumentation that adds tracing with minimal code changes. OpenTelemetry provides auto-instrumentation for popular frameworks in most languages.

## observability-basics#012

### How much data does distributed tracing generate?
 It varies widely based on traffic, sampling rate, and span detail. Plan for anywhere from gigabytes to terabytes per day for busy systems. That's why choosing the right observability platform matters for cost control.

### Can traces help with security and compliance?
 Yes! Traces create an audit trail of request flow through your system. With the right attributes, you can track which users or services accessed what data and when.

### How do traces and spans fit with other observability signals?
 Traces complement metrics and logs. Metrics show system health at a high level, logs provide detailed events, and traces connect the dots to show request flows across services.

##

Topics
 
 Observability Monitoring

About the authors
 
 Anjali Udasi 
 Helping to make the tech a little less intimidating. I

#### 
Contents

## 
Start observing for free. No lock-in.

Book demo

## observability-basics#013

OPENTELEMETRY • PROMETHEUS Just update your config. Start seeing data on Last9 in seconds. 
 
 DATADOG • NEW RELIC • OTHERS We've got you covered. Bring over your dashboards & alerts in one click. 
 
 BUILT ON OPEN STANDARDS 100+ integrations. OTel native, works with your existing stack.

4.8/5

G2 Reviews
 
 Gartner Cool Vendor 2025 
 High Performer 
 Best Usability 
 Highest User Adoption
