# 第二大脑 · brain/

> 一个用 Markdown + 一个 Python 文件搭起来的个人 Agent 系统。
> 目标不是"演示一个 AI 应用"，而是**每天真的用它记住、抽象、调用、变强**。
>
> 主配置（给模型看）：[`AGENT.md`](AGENT.md) ｜ 给陌生人看的说明：本文件

---

## 30 秒上手

```bash
cd brain
python3 scripts/kstar.py selftest        # 自检（应输出 5 项通过）
python3 scripts/kstar.py doctor          # 体检（结构 / ΔR / 空壳 Skill / 积压笔记）
python3 scripts/kstar.py recall "移动端 验收 量错"   # 跨四层检索，带命中理由
python3 scripts/kstar.py dash            # 生成 reports/dashboard.html（离线可开）
```

**要求**：Python 3.9+。**不需要任何第三方库**，不需要联网，不需要数据库服务。
`index/brain.db` 是 SQLite 索引，删掉会自动重建；**删掉它不丢数据**（数据都在 Markdown 里）。

---

## 它是怎么组织的（五层 → 目录）

| 层 | 目录/文件 | 说明 |
|---|---|---|
| L5 Interface | `AGENT.md` · `scripts/kstar.py` · `reports/dashboard.html` | Markdown 驱动 + CLI + 离线看板 |
| L4 Tool/Access | `config/tools.md` · `config/identity.md` | 工具清单与调用方式；身份/原则/判断偏好 |
| L3 Agent Loop | `scripts/kstar.py loop start/close` · `logs/runs/` | K→S→T→Â→R̂→A→R→ΔR→写回 |
| L2 Skill | `skills/<name>/SKILL.md` | 可复用的行动计划，带使用记录与迭代史 |
| L1 Memory | `memory/L1_raw/` · `memory/L2_episodes/` | 原始笔记（未结构化）/ KSTAR 经验（结构化） |

---

## 一条命令跑完一次循环

```bash
# 1. 开循环（自动做 K 步检索，把命中结果写进 run 文件）
python3 scripts/kstar.py loop start --task "给家里有什么加一条过期提醒聚合规则" \
    --situation "上次预警太吵，high 19 条" --rhat 0.8

# 2. 干活……（补 S / Â / R̂，执行，收集证据）

# 3. 关循环（自动算 ΔR，并落一条 L2 草稿）
python3 scripts/kstar.py loop close RUN-20261105-2112 \
    --actual "聚合后 23 条，high 从 19 降到 1，第 7 类靠 --as-of 演练触发" --r 0.55 \
    --lesson "覆盖率是给自己看的，信噪比是给用户看的"
```

关循环时会打印：`ΔR = R̂ − R` 与判定。若 `|ΔR| > 0.2`，它会提醒你去
`skill iterate`——**这就是"自进化"的触发点，不是口号**。

---

## 全部命令

| 命令 | 作用 |
|---|---|
| `init` | 初始化目录结构（幂等） |
| `add "笔记" --tag x` | 写一条 L1 原始笔记 |
| `recall "查询" --k 5` | K 步：BM25 + 中文二元组检索，返回命中理由 |
| `ep new / list / show / promote` | L2 KSTAR 经验（new 支持 `--rhat/--r` 自动算 ΔR） |
| `loop start / close` | L3 KSTAR 循环，close 自动算 ΔR 并落草稿 |
| `skill new / use / iterate / deprecate / list / stats` | L3 Skill 全生命周期 |
| `distill --min 3 --write` | 从多条同类经验提名候选 Skill（只提名，不上线） |
| `note processed <name>` | 标记 L1 已转 L2（回填场景补标） |
| `index` | 重建 SQLite 索引 |
| `doctor` | 体检：结构/ΔR 缺失/空壳 Skill/积压笔记 |
| `dash` | 生成 `reports/dashboard.html` |
| `report --since YYYY-MM-DD` | 用真实流水生成使用记录 |
| `export-skills --out DIR` | 导出 Skill 库快照（提交用） |
| `selftest` | 不依赖 pytest 的内核自检 |

---

## 为什么是 Markdown + SQLite 索引，而不是数据库/向量库

1. **可迁移**：整个 brain 是一个文件夹，`cp -r` 就搬走，随 git 走。
2. **可读**：任何编辑器都能改；模型不需要专有 SDK 就能读。
3. **可解释**：检索是 BM25 + 中文二元组，命中理由能打印出来（"命中 口径、验收（标签命中）"）。
4. **够用**：语料 < 200 篇时，向量检索带来的收益小于它带来的部署成本和黑箱成本。

这不是"做不到"，是**刻意不做**（见 `config/tools.md` 的"不用的工具"一节）。

---

## 数据是活的：三个不可手工编辑的文件

| 文件 | 生成命令 | 为什么不能手改 |
|---|---|---|
| `reports/dashboard.html` | `kstar.py dash` | 看板是可重算的结果，手改等于伪造 |
| `reports/usage_log_auto.md` | `kstar.py report` | 使用次数来自 `logs/usage.jsonl` 流水 |
| `logs/usage.jsonl` | 每条命令自动追加 | 这是"我到底用了几次"的唯一证据 |

删掉 `reports/` 与 `index/` 再跑一次命令，全部原样重建。
