# SETUP · 安装与部署

> 目标：让一个没碰过这个项目的人，在 10 分钟内从零跑到看见看板。

---

## 一、环境要求

| 项 | 要求 | 说明 |
|---|---|---|
| Python | 3.10+ | 只用标准库（json / sqlite3 / urllib / hashlib） |
| 操作系统 | macOS / Linux / Windows | 路径分隔符已用 `os.path` 处理 |
| 第三方包 | **无** | 不需要 pip install |
| SQLite | 3.9+（带 FTS5 更好） | 没有 FTS5 会自动退化为 LIKE 查询 |

自检：

```bash
python3 -m wcm.cli doctor
```

预期输出里至少这几项是 ✅：Python、SQLite、FTS5、回放数据集、标注集、挑战配置、学生名单。
`s0lcipher3` 和「本机微信库」允许是 ⚠️，不影响主链路。

---

## 二、跑起来（离线回放模式，3 步）

```bash
# 1. 生成回放数据集（可跳过，仓库里已带）
python3 data/make_fixtures.py

# 2. 全链路
python3 -m wcm.cli run --days 14

# 3. 看结果
open out/dashboard/index.html     # macOS
# xdg-open out/dashboard/index.html  # Linux
```

如果本机有真实提交包（比如 `~/Desktop/挑战的产物`），加上磁盘扫描：

```bash
python3 -m wcm.cli run --days 14 --fs ~/Desktop/挑战的产物 --owner JingXueQing
```

`--owner` 只影响「目录里没写名字的文件归给谁」，不影响有名字的文件。

---

## 三、接真实微信（三条路，按可行性排序）

### 路径 A：chatlog（推荐，若你愿意跑一个本地服务）

```bash
# 终端 1：起 chatlog server（见 sjzar/chatlog 文档），默认 127.0.0.1:5030
chatlog server

# 终端 2：
python3 wechat_bridge.py --source chatlog --url http://127.0.0.1:5030 \
    --group "Elite20" --days 7 -o out/messages.jsonl
```

`ChatlogSource` 按天切片拉取，自动去重。不同版本字段差异用「存在即取」兼容。

### 路径 B：导出一次，反复回放（最稳）

用任一工具导出群聊为 JSON，转成 `data/fixtures/messages_raw.jsonl` 的字段格式
（`time / talker / talkerName / sender / senderName / type / content / contents / msgId`），
然后：

```bash
python3 wechat_bridge.py --source replay --fixture <你的导出.jsonl> --days 30
```

好处：导出物脱敏后可给同学复现，评审不用碰你的真实聊天记录。

### 路径 C：直连 SQLCipher 库（高阶，需要密钥）

```bash
pip install sqlcipher3-binary
python3 wechat_bridge.py --source sqlcipher --db <message_0.db> --key <key>
```

**注意**：WeChat 4.x（macOS）的库是加密的，密钥在进程内存里，取出属于侵入式操作。
本项目不提供取 key 的脚本，也不建议这么做——路径 A/B 已经够用。

---

## 四、挂定时任务（Watcher）

```bash
# 每小时增量抓一次（只在有新消息时才会入库，不会重复）
0 * * * * cd /path/to/wechat-class-manager && /usr/bin/python3 -m wcm.cli watch --days 1 >> out/watch.log 2>&1
```

`watch` 的 checkpoint 存在 `out/graph.db` 的 `meta` 表，重复运行返回 `new: 0`。

每周出一次报告：

```bash
0 20 * * 5 cd /path/to/wechat-class-manager && /usr/bin/python3 -m wcm.cli run --days 7 --quiet
```

---

## 五、改配置（不用改代码）

| 想改什么 | 改哪里 |
|---|---|
| 加一个挑战 / 改必备件 | `config/challenges.yaml` 的 `challenges` |
| 改文件名识别规则 | `config/challenges.yaml` 的 `naming.regex` |
| 加人 / 改名单 | `config/group_config.yaml` 的 `roster` |
| 改预警阈值（沉默天数、提交率下限） | `config/group_config.yaml` 的 `rules` |
| 改参与分口径 | `wcm/profile.py::_engagement`（**只此一处**，报告和看板会自动跟着变） |

改完重跑 `python3 -m wcm.cli run` 即生效。

---

## 六、常见问题

**Q：看板打开是空白/样式全丢？**
A：看板是单文件、无 JS、无 CDN。空白通常是文件被压缩工具截断，重新生成：`python3 -m wcm.cli dashboard`。

**Q：提交矩阵全空？**
A：两条原因——文件名里没有挑战 ID（看 `submission_detector.py` 输出的 issues），
或者 `config/challenges.yaml` 里没有这个挑战 ID（比如课程新增了 C11）。

**Q：分类器把「讨论」判得太多？**
A：`wcm/classifier.py::_scores` 里 `discussion` 的加分项是按本课程群风格调的，
换群后建议先跑 `python3 classifier.py` 看混淆矩阵，再决定调哪一条。

**Q：能自动把周报发到群里吗？**
A：默认不能，也不建议。`nudges.md` 和 `report.md` 是给你复制粘贴的。
真要自动发，需要登录态或第三方协议，风险和合规责任落在你身上。

**Q：数据会被上传吗？**
A：不会。全链路只读写本地文件，唯一的网络调用是可选的 chatlog 本地服务和可选的 LLM 复核（你自己配 key）。

---

## 七、移交清单（交给下一个人时）

- [ ] `python3 -m wcm.cli doctor` 全部核心项通过
- [ ] `python3 -m wcm.cli selftest` 62 个测试通过
- [ ] `config/` 已改成新学期的挑战与学生
- [ ] `out/` 可以整体删除重建（`run` 一条命令即可）
- [ ] 读过 `docs/架构.md` 第 4 节（关键取舍）和 `docs/数据说明.md`（哪些是真数据）
