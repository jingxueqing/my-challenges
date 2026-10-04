# 输入格式速查：我的 AI 协作记录在哪？

按「证据强度」排序，越靠前越推荐。

## 🥇 Claude Code 会话记录（证据最硬）

```
~/.claude/projects/<项目路径>/<session-id>.jsonl
```

找最近几次会话：

```bash
ls -t ~/.claude/projects/*/*.jsonl | head -5
```

优点：自带时间戳、工具调用、报错标记，抽出来的轮次和工具分布 100% 真实。
缺点：只有命令行版才有；网页版 / App 版没有本地文件。

## 🥈 ChatGPT / Claude 网页版导出

- ChatGPT：`设置 → 数据控制 → 导出数据` → 解压得到 `conversations.json`
- Claude 网页版：会话右上角 `⋯ → 导出` → 得到 `.md` 或 `.json`

把导出的文件直接喂给 `extract_trace.py`（后缀 `.json` 走 JSON 解析器，`.md` 走文本解析器）。
**注意**：导出 HTML 不支持，请改导出 Markdown / JSON。

## 🥉 手动粘贴的聊天记录（兜底）

新建一个 `chat.md`，按下面格式粘贴即可：

```markdown
我：第一句话
AI：AI 的回复
我：不对，改成……
AI：好的……
```

说话人标记支持：`我:` `User:` `Human:` `你:` / `AI:` `Assistant:` `Claude:` `ChatGPT:` `模型:` `助手:`
（中文全角冒号 `：` 也可以）。

## ❌ 不推荐

| 情况 | 为什么 |
|---|---|
| 凭记忆口述 | 轮次和报错会被记错，体检时拿不到硬证据 |
| 只截图 | 脚本读不了图片，需要先 OCR 或手动转成文本 |
| 导出的 HTML | 结构复杂，解析不可靠 |

## 找不到记录怎么办？

用访谈模式，照样能出合格文档：

```bash
python3 scripts/forge.py --interview -n 你的名字 -c C4 -o .
```

只是日志里要如实注明「证据来源：本人回溯访谈」，且体检时无法提供硬证据（轮次/工具数留空）。
