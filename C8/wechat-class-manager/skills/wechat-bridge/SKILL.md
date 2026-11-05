---
name: wechat-bridge
description: 从本地微信数据源（chatlog HTTP API / SQLCipher 数据库 / 导出的 JSONL）提取某个群的消息流，标准化为 UMF JSONL。当需要「把群消息拿出来给 agent 用」「导出群聊」「统计消息量」时使用。
inputs:
  - group: string        # 群名，如 "Elite20"
  - days: int            # 最近 N 天
  - source: replay|chatlog|sqlcipher
  - fixture/db/key       # 按 source 选填
outputs:
  - messages.jsonl       # UMF，见 schemas/message.schema.json
  - messages.meta.json   # 条数、时间跨度、类型分布
entry: wechat_bridge.py
---

# wechat-bridge · Layer 1 数据桥接

## 做什么

把「微信群」这个私有消息流，变成任何 agent 都能消费的 JSON Lines。
只读，不登录，不发消息。

## 命令

```bash
# A. 离线回放（推荐给评审/CI：不碰真实聊天记录）
python wechat_bridge.py --source replay --fixture data/fixtures/messages_raw.jsonl --days 14 -o out/messages.jsonl

# B. chatlog HTTP（本机微信在跑 + chatlog server 在跑）
python wechat_bridge.py --source chatlog --url http://127.0.0.1:5030 --group Elite20 --days 7

# C. 直连加密库（需要密钥，属于高阶路径）
python wechat_bridge.py --source sqlcipher --db <message_0.db> --key <key> --group Elite20 --days 3

# D. 顺手扫磁盘上的真实提交包
python wechat_bridge.py --scan-submissions ~/Desktop/挑战的产物 --owner JingXueQing
```

## 输出示例

```json
{"msg_id":"m00003","timestamp":"2026-10-21T08:52:13+08:00",
 "sender":{"wechat_id":"wxid_linyz","nickname":"林一舟"},
 "type":"text","content":"请问 C8 的 demo 一定要能跑起来吗？",
 "media_ref":"","reply_to":null,"group":"AI+X 实验班 Elite20 · 挑战冲刺群"}
```

## 硬要求

- 同一个 `msg_id` 只出现一次（去重后按时间排序）。
- `timestamp` 必须带 `+08:00`。
- 消息类型至少能区分 text / file / image / link / voice / system。
- `--days` 以**数据里最新一条**为基准，回放历史数据时行为可预测。

## 失败处理

- 连不上 chatlog → 提示起服务，或降级到 `--source replay`。
- 数据库加密 → `doctor` 会告诉你本机库是否加密；不要尝试破解，走导出路径。
- 条数 < 100 → 打印警告（Bronze 验收门槛）。
