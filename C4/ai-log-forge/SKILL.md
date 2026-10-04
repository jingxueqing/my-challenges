---
name: ai-log-forge
description: >
  Turn raw AI collaboration records (Claude Code .jsonl session logs, ChatGPT/Claude chat exports
  in .json, or pasted chat transcripts in .md/.txt) into submission-ready "AI 使用日志" and
  "AAR 复盘" documents — with real evidence (turn count, tool calls, failure rounds, prompt
  evolution chains) auto-extracted instead of fabricated, plus a pre-submission health check
  scored against any rubric. Use whenever the user says "写 AI 日志", "生成 AI 日志", "AI日志",
  "AAR", "复盘报告", "AI 使用记录", "交作业前检查一下", "帮我总结这次和 AI 的协作过程",
  "write my AI usage log", "generate AAR", "AI collaboration log", "after action review",
  "log my Claude Code session", "did I iterate enough", or mentions a course/challenge that
  requires an AI 日志 / AAR deliverable. Also trigger when the user hands over a .jsonl/.json/.md
  transcript and asks "总结我们刚才做了什么" or wants to prove how they used AI.
---

# AI Log Forge — 把 AI 协作记录锻造成可提交日志

## Purpose

几乎每个 AI 相关课程 / 项目都要求交一份 **AI 日志**（你用了什么 AI、怎么指挥的、迭代了几轮、你做了什么）
和一份 **AAR 复盘**（目标 / 实际 / 差距 / 失败经验 / 改进方案）。这两份东西的评分口径其实很固定：
**有没有真实迭代、有没有失败经验、有没有可复现证据**。但人手写时要么记流水账，要么临交卷前编一段空话。

本技能的核心主张：**日志里的「事实」必须是真的，「叙事」才交给模型写。**

- `extract_trace.py` 从真实记录里抽出硬证据：第几轮说了什么、用了几次工具、哪一轮报错返工、prompt 怎么逐轮改的。
- `forge.py` 用这些证据生成骨架：《AI 日志》《AAR》，数据和表格已经填好。
- 你在（或让模型）补写需要判断的部分——脚本用 `<!-- LLM-FILL: ... -->` 明确标出每一处待写，绝不替用户编反思。
- `health_check.py` 交卷前打分：对照评分标准逐维度给分，并抓出「一句话指令直接提交」这类**会直接封顶的红旗**。

一句话：**输入**一段真实的 AI 协作记录，**输出**一份有数据支撑、能过评审的 AI 日志 + AAR + 体检报告。

## Input

三选一（越原始越好，原始 jsonl 证据最硬；找不到记录时见 `references/input_formats.md`，
内含 Claude Code / ChatGPT / Claude 网页版三种获取路径和定位命令）：

| 形式 | 例子 |
|---|---|
| Claude Code 会话文件 | `~/.claude/projects/<project>/<session-id>.jsonl` |
| 对话导出 | ChatGPT / Claude 导出的 `.json`、`.md`、`.txt` |
| 粘贴的聊天记录 | 直接把对话粘进一个 `.md`，用 `User:` / `Assistant:` 或 `我:` / `AI:` 分隔 |

另外需要三元数据：`--name`（姓名）、`--challenge`（挑战号 / 项目代号）、`--title`（一句话任务）。
**一个都没有？** 用 `--interview` 走访谈模式，回答 8 个问题照样能出完整日志。

## Output

```
<姓名>_<挑战号>_AI日志.md     一页速览 + 迭代时间线 + prompt 优化轨迹 + 失败返工 + 我的贡献
<姓名>_<挑战号>_AAR.md        目标/实际/差距 + 失败经验 + 改进方案 + 下一步
体检报告.md                   逐维度得分 + 红旗警告 + 未填占位符清单 + 改进建议
trace.json                   中间产物：结构化证据（可复现、可复核）
```

## Workflow

### Step 0 — 确认输入与元数据

先问清（缺哪个问哪个，不要一次甩八个问题）：
1. 原始记录在哪？（给路径，或让用户粘贴）
2. 姓名、挑战号、任务标题？

找不到记录文件时的定位命令：

```bash
ls -t ~/.claude/projects/*/*.jsonl 2>/dev/null | head -5      # Claude Code 最近的会话
```

### Step 1 — 抽取证据（脚本，确定性）

```bash
python3 scripts/extract_trace.py --input <记录路径> --out trace.json --markdown
```

`--markdown` 会顺手打印轮次摘要，先扫一眼确认抽对了（抽错了后面全错）。
**判据**：轮次数 ≥ 3、工具调用 > 0 才算有像样的协作记录。如果只有 1 轮，
说明要么找错文件了，要么这次确实是一次成型——后者要如实写，并在体检里接受扣分。

### Step 2 — 锻造文档（脚本）

```bash
python3 scripts/forge.py --trace trace.json \
    --name JingXueQing --challenge C4 --title "ai-log-forge 技能开发" --out-dir .
```

没有记录时：`python3 scripts/forge.py --interview --name X --challenge C4 --out-dir .`

### Step 3 — 补写叙事（你 + LLM 的判断部分，**本步骤不可替代**）

打开生成的 md，搜索 `<!-- LLM-FILL:`，逐条补写。补写规则：

- **迭代时间线**：每轮的「我的判断 / 我改了什么」要写具体动作，不要写"AI 给出了建议"。
- **失败与返工**：这是评分最看重的一节。**没有捕获到失败事件时也要手动补**——
  写"没失败"会被判定为敷衍。实在没有，就写"哪个环节差点出问题、我怎么提前规避的"。
- **我做了什么**：列 3-5 条只有人能做的（判断、取舍、验收、手动改动）。
- **AAR 的失败经验**：每个失败点写清「为什么错 + 我误判了什么 + 下次怎么提前发现」。

补写完，**所有 `<!-- LLM-FILL:` 标记必须清零**（`health_check.py` 会数，没清零就报错退出码 1）。

### Step 4 — 交卷前体检（脚本）

```bash
python3 scripts/health_check.py \
    --files JingXueQing_C4_AI日志.md JingXueQing_C4_AAR.md \
    --trace trace.json --out 体检报告.md
```

- 给了 `--trace` 就用真实数字判（轮次≥3、有失败轮次、有工具调用），比关键词靠谱。
- 退出码非 0 = 有红旗或未填占位符，可以直接当提交前的关卡用。
- 换评分标准：`--profile 你的标准.yaml`（照抄 `references/rubric_profile.yaml` 改关键词即可，不用动代码）。
- **只评日志本身**用精简档案，别拿全套 C4 标准吓自己：
  `--profile references/rubric_ai_log.yaml`（AI使用质量 30 / 复盘质量 45 / 产物完整性 25）。
- 未填的 `<!-- LLM-FILL -->` 每处扣 1 分（上限 20）——所以「补完占位符」是性价比最高的提分动作。

### Step 5 — 按报告改，再跑一次

先看「红旗警告」（不解决就封顶），再看「改进建议（按性价比排序）」。
改完重跑 Step 4，看分数有没有涨。这个循环本身就是最好的迭代证据——
**把每次体检分数记下来，放进日志的迭代时间线里**。

## 关键设计（为什么这么分）

| 层 | 谁负责 | 为什么 |
|---|---|---|
| 事实层（轮次/工具/失败/prompt 改动） | **脚本** | LLM 会编造。日志一旦编造，评审一眼看穿，直接零分。 |
| 叙事层（判断/取舍/为什么改） | **人 + LLM 补写** | 只有当事人知道。脚本只标占位，不代写。 |
| 评分层（对照 rubric 打分） | **脚本 + 数据驱动 yaml** | 换标准不改代码，适配任何课程/公司口径。 |

## Edge Cases

| 情况 | 处理 |
|---|---|
| 找不到 / 解析出 0 条对话 | 脚本退出码 3 并提示支持格式。先确认后缀（`.jsonl/.json/.md/.txt`），再确认文件非空。 |
| 单个源文件损坏 | 跳过该文件并打印警告，不中断整体解析。 |
| 超大 jsonl（>25MB） | 截断读取并在 sources 里注明；建议先按 session 切分。 |
| 记录里只有 1-2 轮 | 如实生成，体检会扣分并提示"补做或换记录"。不要为了好看伪造轮次。 |
| 纯文本没有说话人标记 | 整段会被当成同一说话人。先让用户加 `User:` / `Assistant:` 标记再跑。 |
| ChatGPT 导出的 HTML | 不支持（结构复杂）。让用户改导出 Markdown/JSON。 |
| 没有失败事件 | 正常现象。必须手动补一节"风险规避"，否则复盘质量维度拿不到分。 |
| 没装 PyYAML | 内置迷你 YAML 解析器兜底，无需 pip install。 |
| 中文文件名 / 路径 | 全程 UTF-8，`errors="replace"` 兜底，不会因编码炸掉。 |
| 评分标准和课程不一致 | 改 `references/rubric_profile.yaml` 的 `signal_keywords`，代码零改动。 |

## Examples

### 例 1：有 Claude Code 会话记录（最常见）

```bash
python3 scripts/extract_trace.py -i ~/.claude/projects/myproj/abc123.jsonl -o trace.json --markdown
python3 scripts/forge.py -t trace.json -n JingXueQing -c C4 --title "技能开发" -o .
python3 scripts/health_check.py -f JingXueQing_C4_AI日志.md JingXueQing_C4_AAR.md -t trace.json
```

### 例 2：只有粘贴的聊天记录

用户把对话粘进 `chat.md`，每行以 `我:` / `AI:` 开头 → 直接 `--input chat.md`，后续同上。

### 例 3：完全没有记录

```bash
python3 scripts/forge.py --interview -n JingXueQing -c C4 -o .
```
输出 8 问访谈提纲；用户回答后，按同一套模板生成两份文档，并在日志里注明"证据来源：本人回溯访谈"。

### 例 4：真人一句话触发

> "帮我写这次作业的 AI 日志，会话文件在 ~/.claude/projects/x/y.jsonl，我是 JingXueQing，挑战 C4"

→ 按 Step 1→5 跑完，最后把体检分数报给用户，并主动补写所有 `LLM-FILL` 占位（补完让用户核对）。

## 不要做的事

- ❌ 不要凭空编造轮次、工具调用、失败事件——证据必须来自 trace.json 或用户口述。
- ❌ 不要把 `<!-- LLM-FILL -->` 原样留在最终交付物里。
- ❌ 不要跳过 Step 4 体检直接交——红旗不解决，写得再长也封顶 5 分。
- ❌ 不要在日志里写"AI 帮我完成了全部工作"——那等于承认自己没贡献，AI 使用质量维度直接失分。
