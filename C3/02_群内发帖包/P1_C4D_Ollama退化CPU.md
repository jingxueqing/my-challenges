# P1 ｜ M1 上 Ollama 退化成纯 CPU

> 类型：提问 ｜ 自检 **100 / 100** ｜ 状态：〔待发〕
> 预期收益：让 M1 用户 5 秒自查；我这边拿到「该在哪个目录 serve」的确认

## 复制这段发出去

```text
【环境】MacBook Air M1 / 8GB 内存 / macOS 14.5 / Ollama 0.3.x
【在做什么】C4D 本地大模型 Agent 技能，目标是用 Gemma 4 E2B 在本地跑一个只读文件的 Agent。
【进度】刚装完 Ollama，这是第 2 轮试；之前用 CPU 跑 1B 的小模型是正常的。

【卡点】ollama serve 起得来，ollama run 也能出字，但慢到不能用：同一句 prompt 要 40 多秒。

【我试过什么】
1. 按 README 跑 ollama run gemma4:e2b，报 tag 不存在；去 ollama.com/library/gemma4/tags 查到
   真实 tag 是 gemma4:2b-it-qat，改了之后能跑；
2. 以为是内存不够，用 top 看只用了 4.1GB，没吃满 → 排除 OOM；
3. 关掉其他 App 再跑，速度没变化 → 排除内存争抢。

【我以为 / 实际】我以为能出字就是吃上 GPU 了。实际看 ~/.ollama/logs/server.log，
第一行就是 library=cpu，根本没走 Metal。

【关键日志】
llama_model_load: library=cpu
eval time = 41233.55 ms / 18 tokens

【我的判断（不一定对）】可能是 llama-server 二进制没被找到，
我 ollama serve 时的工作目录不在 app 的 Resources/ 下。

想问：M1 上遇到 library=cpu 的同学，你们是在哪个目录起的 serve？
```

## 为什么这样写

| 段落 | 作用 |
|---|---|
| 环境 | 让同类人 1 秒认亲 |
| 「能出字但慢」 | 把「不行」变成「能跑但慢」，这是两个完全不同的 bug |
| 第 2 条排除项 | 直接砍掉群里最常见的建议（内存不够 / 关掉别的程序） |
| 日志那一行 | 别人复制一行 grep 就能自查 |
| 「我的判断（不一定对）」 | 给对方一个可以否定的靶子，比问「为什么」更容易被回答 |
| 最后一句 | 把开放问题收成一个必须给出目录的问题 |

## 如果没人回

**不要重发同一句。** 改成补一条新证据，比如：

```text
补一条：我把 serve 换成从 /Applications/Ollama.app/Contents/Resources/ 起，
日志第一行变成 library=metal 了，速度从 40 秒降到 3 秒。
所以确认是「工作目录」的问题。留个记录，后面有人踩到可以搜到。
```

这条「自问自答」的价值不比被回答低：**它把一个没人回的问题，变成了一条别人能搜到的答案。**
