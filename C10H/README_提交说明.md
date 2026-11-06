# C10H 交付说明 — JingXueQing

> 挑战：C10H 安装并驾驭 Hermes Agent ｜ 平台 ID `ch-20260717031609-rnur5a` ｜ 截止 2026-12-31
> 提交人：景雪晴（JingXueQing / 2024102110351）
> 完成日期：2026-11-06 ｜ 机器：MacBook Air M1 / 8 GB / macOS 14.5

---

## 1. 一句话介绍（发群用）

> 在 M1/8G 的 MacBook Air 上把 Hermes Agent 装起来并跑通了：官方 installer 因全历史克隆在慢网下卡死，改走仓库自带 `setup-hermes.sh` 装成；接本地 Ollama（gemma4:e2b，131k 上下文）当推理后端，跑通了对话、工具调用、跨会话记忆（MEMORY.md 落盘可验）、44 个技能 + 自写 1 个、每日 21:00 定时任务，并用 webhook 平台把「外部 POST → 网关 → agent → 回传」整条链路打通。踩坑记录和失败样本全部留在交付物里。

---

## 2. 交付物对照表

| 挑战要求 | 本交付对应文件 | 状态 |
|---|---|---|
| `姓名_C10H_安装记录.md` | `JingXueQing_C10H_安装记录.md` | ✅ 含三次安装尝试、6 条踩坑表、Level 1 三问解答 |
| `姓名_C10H_配置说明.md` | `JingXueQing_C10H_配置说明.md` | ✅ provider/模型/SOUL/cron/webhook/工具集策略 |
| `姓名_C10H_demo.mp4` 或截图 | `JingXueQing_C10H_demo.md` + `JingXueQing_C10H_demo/终端记录/`（19 份原始日志 + 1 份索引） | ⚠️ 用终端记录替代截图（环境无法截屏，已说明） |
| `姓名_C10H_自定义技能/` | `JingXueQing_C10H_自定义技能/`（SKILL.md + 159 行脚本 + 技能说明） | ✅ agentskills.io 规范 |
| `姓名_C10H_AI日志.md` | `JingXueQing_C10H_AI日志.md` | ✅ 8 轮迭代、4 次真实失败、prompt 演进表、分工声明 |
| `姓名_C10H_拿来说明.md` | `JingXueQing_C10H_拿来说明.md` | ✅ 拿了什么/架构理解/个性化清单/对系统的批评 |
| （加分项）AAR | `JingXueQing_C10H_AAR.md` | ✅ 差距根因、重做方案、驾驭方法论 |
| （附加）人格文件 | `JingXueQing_C10H_SOUL.md` | ✅ 线上生效文件副本 |

---

## 3. Level 自评（对自己诚实）

| Level | 目标 | 自评 | 依据 |
|---|---|---|---|
| L1 | 装上、能对话 | ✅ 达成 | `hermes --version` 有版本；CLI 完成实质对话；三个必答题答完 |
| L2 | 平台 + 工具 + 技能 + cron | 🟡 3/4 | 工具/技能/cron 有实测；**聊天平台未接**（无 bot token），用 webhook 平台做了端到端替代验证；**自动技能创建未触发**（4.6B 模型能力不足） |
| L3 | 人格 + 自定义技能 + 模型对比 | 🟡 主要项达成 | SOUL.md 生效可验、技能符合规范且能跑、两模型有同任务数据；subagent 与 `/insights` 未实机验证 |
| L4 | 深度集成 / 开源贡献 | ❌ 未做 | 无 Docker/云凭据，当日余力不足 |

**不掩饰的部分：** 8 GB 内存 + 4.6B 本地模型这个组合，决定了它「能跑通流程、但做不稳多步任务」。我没有为了好看而把失败的会话删掉——`chat-01.log`、`chat-05-search.log` 和 cron 那次不合格的回答都在。

---

## 4. 复现命令（干净机器照着跑）

```bash
# ── 1. 取源码（慢网用浅克隆，先拿到工作树）
git clone --depth 1 https://github.com/NousResearch/hermes-agent.git ~/hermes-src
cd ~/hermes-src

# ── 2. 装环境：走仓库自带入口，避开 installer 的全历史克隆
bash setup-hermes.sh            # 约 24 分钟（含 chromium 等工具下载）
export PATH="$HOME/.local/bin:$PATH"
hermes --version                # 期望：vgit.44ec783 (2026.9.24)

# ── 3. 起本地模型（必须用 App 内二进制，否则缺 llama-server）
/Applications/Ollama.app/Contents/Resources/ollama serve &

# ── 4. 接推理后端（注意 custom，不是 ollama）
hermes config set model.provider custom
hermes config set model.base_url http://127.0.0.1:11434/v1
hermes config set model.default "gemma4:e2b-it-q4_K_M"

# ── 5. 人格与技能
cp JingXueQing_C10H_SOUL.md ~/.hermes/SOUL.md
cp -R JingXueQing_C10H_自定义技能 ~/.hermes/skills/challenge-deliverable-check

# ── 6. 定时任务
hermes cron create "0 21 * * *" "检查交付目录是否齐备" \
  --name "C10H交付物自检" --deliver local --skill challenge-deliverable-check

# ── 7. 验收
hermes doctor
hermes chat -t file -q "读取 ~/.hermes/config.yaml，回答 provider 和 model" --oneshot
hermes skills list | grep challenge
hermes cron list
```

---

## 5. 自检结果（用交付的技能跑本交付目录）

```bash
python3 JingXueQing_C10H_自定义技能/scripts/check_deliverables.py . \
  --pack "/Users/jingxueqing/Desktop/我的挑战/挑战_C10H 安装并驾驭 Hermes Agent_rnur5a_完整资料" \
  --name JingXueQing
```

```
| 检查项 | 结果 |
|---|---|
| 必备文件 `*安装记录*` | ✓ JingXueQing_C10H_安装记录.md |
| 必备文件 `*配置说明*` | ✓ JingXueQing_C10H_配置说明.md |
| 必备文件 `*demo*` | ✓ JingXueQing_C10H_demo/终端记录/…（20 个） |
| 必备文件 `*AI日志*` | ✓ JingXueQing_C10H_AI日志.md |
| 命名规范 <Name>_<ID>_<描述> | ✓ 全部合规 |
| 空文件检查 | ✓ 无空文件 |
| AI 日志非空且 >500 字节 | ✓ 10767 字节 |

**结论：全部通过。**   exit=0
```

---

## 6. 文件清单

```
C10H-交付_JingXueQing_Hermes-Agent/
├── README_提交说明.md                  ← 你在读的这份
├── JingXueQing_C10H_安装记录.md
├── JingXueQing_C10H_配置说明.md
├── JingXueQing_C10H_AI日志.md
├── JingXueQing_C10H_拿来说明.md
├── JingXueQing_C10H_AAR.md
├── JingXueQing_C10H_demo.md            ← demo 索引（截图替代方案说明）
├── JingXueQing_C10H_SOUL.md            ← 人格文件（已上线版本副本）
├── JingXueQing_C10H_demo/
│   └── 终端记录/                        ← 19 份原始终端输出 + 命名索引
└── JingXueQing_C10H_自定义技能/
    ├── SKILL.md
    ├── README_技能说明.md
    └── scripts/check_deliverables.py
```

---

## 7. 如果评审只给我 3 分钟

1. 看 `JingXueQing_C10H_安装记录.md` §2——三次安装尝试里两次失败，失败原因写到了 git 层（promisor/浅根）。
2. 看 `JingXueQing_C10H_demo/终端记录/JingXueQing_C10H_demo_chat-02.log` 与 `..._chat-04-recall.log`——工具调用与跨会话记忆都是真的。
3. 看 `JingXueQing_C10H_AAR.md` §3——为什么一个 8 GB 笔记本上的 4.6B 模型注定做不稳多步任务，以及我下次会先做什么。
