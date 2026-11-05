# C10 提交说明 · JingXueQing

> **一句话介绍（发群用）**
> 我做了一套能自己长大的第二大脑：1,296 行零依赖命令行内核 + 13 条原始笔记 / 11 条 KSTAR 经验 / 6 个带使用记录的 Skill，
> 它第一次运行时抓到了我自己的三个错——这才是它活着的证据。

---

## 一、交付物对照表（CHALLENGE 第五节「必须提交的文件」逐条对齐）

| # | CHALLENGE 要求 | 交付文件 | 规模 | 状态 |
|---|---|---|---|---|
| 1 | 系统架构说明 `姓名_C10_architecture.md` | `JingXueQing_C10_architecture.md` | 373 行 / 21 KB，五层逐层证据 + 8 个设计决策 + 可删索引证明 | ✅ |
| 2 | Demo `姓名_C10_demo.mp4` 或录屏 | `JingXueQing_C10_demo.html`（22 KB 离线回放）<br>+ `brain/demo/demo_transcript.txt`（134 行真实终端输出）<br>+ `brain/demo/record.sh`（可复跑录制脚本） | 见下方「诚实声明 ②」 | ⚠️ 降级但可复现 |
| 3 | Skill 库 `姓名_C10_skills/` ≥5 个 | `JingXueQing_C10_skills/`（6 个，v2–v4） | 6 个 Skill，全部含使用记录 + 迭代史 + 状态机 | ✅ |
| 4 | 使用记录 `姓名_C10_usage_log.md` | `JingXueQing_C10_usage_log.md` | 176 行；A 类 65 次系统调用 + B 类 26 次回填分开统计 | ✅ |
| 5 | 系统级 AAR `姓名_C10_AAR.md` | `JingXueQing_C10_AAR.md` | 7 节：对/错/意外/重来/下一步 + 诚实边界表 | ✅ |
| 6 | ⚡ AI 日志 `姓名_C10_AI日志.md` | `JingXueQing_C10_AI日志.md` | 178 行，五标法 + 人机分工表 + `[待复核]` 清单 | ✅ |
| 7 | 拿来说明 `姓名_C10_拿来说明.md` | `JingXueQing_C10_拿来说明.md` | 57 行，7 个参考系统 + 3 个明确拒绝 | ✅ |
| + | 可运行系统本体（非强制，但缺了就是空壳） | `brain/` | 1,296 行内核 / 14 命令 / 13 L1 / 11 L2 / 6 Skill | ✅ |

**目录导航**

```
C10-交付_JingXueQing_第二大脑/
├── JingXueQing_C10_architecture.md    ← 先看这份（五层怎么搭的）
├── JingXueQing_C10_AAR.md             ← 再看这份（哪里错了）
├── JingXueQing_C10_usage_log.md       ← 证明"真的在用"
├── JingXueQing_C10_AI日志.md          ← 人机分工，逐条溯源
├── JingXueQing_C10_拿来说明.md        ← 拿了谁的、改了哪
├── JingXueQing_C10_demo.html          ← 打开即看一次完整 KSTAR 循环
├── JingXueQing_C10_skills/            ← 6 个 Skill 快照（导出副本）
└── brain/                             ← 系统本体，可直接跑
    ├── AGENT.md                       ← 给模型的启动协议
    ├── README.md                      ← 命令速查
    ├── scripts/kstar.py               ← 内核（纯标准库）
    ├── memory/L1_raw/  L2_episodes/   ← 13 条 / 11 条
    ├── skills/  config/  logs/        ← Skill / L4 身份与工具 / 流水
    ├── inbox/candidates/              ← distill 提名 + 我的裁决记录
    ├── reports/                       ← dashboard.html + usage_log_auto.md
    └── demo/                          ← record.sh + transcript
```

---

## 二、复现命令（任何一台装了 Python 3 的机器，无需联网、无需 pip）

```bash
cd brain
PY=python3

$PY scripts/kstar.py selftest          # 1. 内核自检（5 项断言，应打印 ✓ 全部通过）
$PY scripts/kstar.py doctor            # 2. 体检：应为 L1 13 / L2 11 / Skill 6 / Run 1
$PY scripts/kstar.py recall "移动端 验收 量错" --k 3   # 3. 验 K 步检索（应命中 C9 那条经验）
$PY scripts/kstar.py report --since 2026-09-01        # 4. 从 usage.jsonl 重算使用记录
$PY scripts/kstar.py dash              # 5. 重生成离线看板 reports/dashboard.html
```

**想重跑一次完整 KSTAR 循环：**

```bash
bash demo/record.sh      # 会新开一个 RUN-* 文件，并把每一步的真实输出写进 demo_transcript.txt
```

> 注意：`demo/record.sh` 里写死了 `RUN-20261105-2122`（本次录制的循环）。
> 重跑前先 `kstar.py loop start ...` 拿到新 run id 再替换，否则会提示找不到循环。

---

## 三、CHALLENGE 第十节检查清单（自评，含打折项）

| # | 检查项 | 自评 | 依据 |
|---|---|---|---|
| 1 | 五层架构都实现 | ✅ | Memory / Skill / Agent Loop / Tool / Interface，架构说明 §1 逐层给了命令 |
| 2 | Memory 四层齐全 | ✅ | L1 13 篇、L2 11 条、L3 6 个 Skill、L4 `config/identity.md`+`tools.md` |
| 3 | Skill ≥5 且有使用记录 | ✅ | 6 个；每个都有「回填次数 + 系统计数 + 使用表 + 最近效果」 |
| 4 | 至少一个 Skill 迭代过 | ✅ | `measure-before-fix` v1→v2→v3→v4，每次触发原因都指向一条真实失败 |
| 5 | Demo 展示完整 KSTAR 循环 | ⚠️ **0.5** | 展示了（K→S→T→Â→R̂→A→R→ΔR 八步全有真实输出），但**不是 mp4** |
| 6 | 使用记录真实（日期/输入/ΔR） | ✅ | A 类由 `usage.jsonl` 生成；B 类 26 条逐条标了来源交付物与段落 |
| 7 | 系统级 AAR 反思对错 | ✅ | 5 个"对"、5 个"错"、5 个"意外"，每个错都写了"怎么发现的" |
| 8 | 拿来说明 ≥3 参考系统 | ✅ | 7 个（含明确拒绝的 3 个） |
| 9 | 数据可积累 | ✅ | 删掉 `index/` 与 `reports/` 后所有命令照常工作（架构说明 §7 有验证） |
| 10 | 提交前已用 ≥2 周 | ❌ **0.1** | 系统 2026-11-05 建成，被使用 1 天。记忆内容跨 6 周（真实交付物回填） |

**加权 R = (8×1.0 + 0.5 + 0.1) / 10 = 0.86**（R̂ 0.88，ΔR 0.02）
> 这个 0.02 **不代表准**：清单是我自己定的、10 项等权，于是第 5、10 项这两件真正会被扣分的事各只值 1/10。
> 详见 AAR §3.3 —— 这是本次最重要的一条自我批评。

---

## 四、红牌自检（CHALLENGE 第七节淘汰机制）

| 红牌 | 本项目情况 | 证据 |
|---|---|---|
| ❌ 只有架构文档，没有使用记录 | 有 65 次真实 CLI 调用流水 + 26 次历史回填，分开统计 | `brain/logs/usage.jsonl`、usage_log §0 |
| ❌ Skill 库全是空壳 | 6 个 Skill 每个都有 ≥5 行使用记录表，最早一条追到 09-25 的 C1 交付 | `skills/*/SKILL.md` §使用记录 |
| ❌ 没有进化痕迹 | `measure-before-fix` v1→v4；`distill` 提名 3 个我否掉 2 个；`doctor` 抓错后我改的是系统不是数据 | AAR §3.2、`inbox/candidates/README.md` |
| ❌ 不做拿来主义 | 7 个参考系统 + 3 个明确拒绝（含拒绝向量库的理由） | 拿来说明 |
| ❌ 只在提交那周用过 | **部分成立**：软件是本周建的。但记忆内容来自 6 周真实工作，且 §短期计划里写了怎么延续 | AAR §6 诚实边界 |

---

## 五、诚实声明（5 条，先说为敬）

1. **「已用 2 周」不成立。** 系统建成到现在只有 1 天。我没有改时间戳（那和伪造使用记录是同一种行为），
   而是把 C1–C9 六周的真实工作回填成记忆，并在 AAR 与 usage_log 里把「系统被使用 1 天」和「经验跨 6 周」拆开写。
2. **Demo 不是 mp4。** 沙箱没有 ffmpeg，Pillow 也不可用。交付的是：134 行真实终端输出 + 22 KB 离线 HTML 回放 + 可复跑脚本。
   任何人 `bash demo/record.sh` 都能得到同构的 transcript。**形式打折，可复现性不打折。**
3. **6 个 Skill 的"使用次数"分两个字段。** `uses_backfilled`（C1–C9 真的用过）+ `uses_system`（本系统内被调用），永不合并。
   合并就能做出"用了 84 次"的漂亮数字，但那是拿过去冒充现在。
4. **65 次调用全部 `ok: true` 是幸存者偏差。** 构建中至少撞了 5 次硬失败（文件截断、`sed` 未匹配、`%` 格式化崩、退出码、旧 run 残留），
   它们发生在 `log_usage` 之前，所以零记录。已列为 AAR §2.2 + 短期第一项修复。
5. **系统级 R = 0.86 是我自己给自己打的。** 权重自利，真实分应更低。AAR §3.3 把这个漏洞写成了规则补丁。

---

## 六、5 分钟验收路径（给评审/同学）

```bash
# 0) 打开 demo（不用装任何东西，双击即可）
open JingXueQing_C10_demo.html

# 1) 30 秒确认系统是活的（不是截图）
cd brain && python3 scripts/kstar.py selftest && python3 scripts/kstar.py doctor

# 2) 60 秒确认记忆是真的（检索出我在 C9 犯过的错）
python3 scripts/kstar.py recall "移动端 验收 量错" --k 2

# 3) 60 秒确认 Skill 有资历（看它的 8 行使用记录 + 4 个版本）
cat skills/measure-before-fix/SKILL.md

# 4) 60 秒确认进化发生过（这次 distill 提名了 3 个，我否了 2 个）
cat inbox/candidates/README.md
```

---

## 七、这套东西接下来怎么活

| 时间 | 动作 | 系统会怎么揭发我 |
|---|---|---|
| 每周日 | `doctor` 体检 | 积压笔记 > 30 天未转 L2 会报警 |
| 每月 | `report --since` 看 ΔR 趋势 | 平均 \|ΔR\| 不降 = 预测能力没长 |
| 12-05 起 | 第一次 `skill deprecate` | 30 天 0 调用的 Skill 自动进候选淘汰名单 |
| 到 500 篇 L2 | 才考虑上语义检索 | 现在 11 条用 BM25 + 中文二元组，够用且可解释 |

> 设计里最"不体面"的一条：`doctor` 会主动报"Skill 30 天未用"。
> 我把它留着，因为一个不敢揭发主人的系统，不配叫第二大脑。

---

*提交人：JingXueQing（2024102110351）｜日期：2026-11-05｜挑战：C10 Build Your Own Agent*
