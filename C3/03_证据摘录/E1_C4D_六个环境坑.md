# 证据摘录 E1 ｜ C4D 的 6 个环境坑（含 Ollama 退化成 CPU）

> 用途：参与一（P1）的技术底稿 —— 我提问时写的「排除项」和「日志」都来自这里
> 原始文件：`挑战的产物/C4D-交付_JingXueQing_本地大模型Agent技能/JingXueQing_C4D_AI日志.md`

## 摘录原文（按行号，一字未改）

<!-- JingXueQing_C4D_AI日志.md L50-L57 -->
````text
| 坑 | 现象 | 根因 | 解法 |
|---|---|---|---|
| ① | `curl ... install.sh` 超时 | 206MB 包网络太慢 | 改**断点续传循环** `curl -C -`，按字节数判断完成 |
| ② | 照挑战文档 `ollama run gemma4:e2b` 无效 | 文档 tag 与实际不符 | 查 `ollama.com/library/gemma4/tags` 拿到真实 tag：必须带 `-it-` 和量化后缀 |
| ③ | `ollama serve` 跑起来了但很慢 | 日志显示 `library=cpu`，**退化成纯 CPU** | `llama-server` 要和主二进制同目录 → 必须 `cd` 到 app 的 `Resources/` 再 serve |
| ④ | `ollama pull` 卡在 `pulling manifest` | `registry.ollama.ai` TCP 握手超时（DNS 正常） | 稍后重试即可；且 `ollama pull` **本身支持断点续传**，重跑同命令即可 |
| ⑤ | 沙箱里 `mkdir(exist_ok=True)` 抛 `EEXIST` | 环境的路径代理拦截 | 改成先 `if not d.is_dir(): d.mkdir()` |
| ⑥ | 模型拉到 3.5GB 的 27% 卡住不动 | 网络抖动 | 写循环反复重跑 pull，进度会接着走（925MB→1.6GB→完成） |
````

## 这份 evidence 能支撑什么

| 我在群里说的 | 原始出处 |
|---|---|
| 「`ollama run gemma4:e2b` 报 tag 不存在」 | 上表第 ② 行（原文件 **L53**） |
| 「日志第一行就是 `library=cpu`」 | 上表第 ③ 行（原文件 **L54**） |
| 「`ollama pull` 卡在 pulling manifest，重跑会续传」 | 上表第 ④ 行（原文件 **L55**） |

## 我为什么把整张表都摘下来

因为**提问只需要一行，但判断「这一行值不值得发」需要看到整张表**：
6 个坑里有 4 个是我自己撞出来的，说明这不是我一个人的环境问题，
而是「M1 + 8GB + Ollama」的群体问题——**这才值得占群里一条消息**。
