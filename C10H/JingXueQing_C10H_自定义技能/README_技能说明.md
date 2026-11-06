# challenge-deliverable-check — 自定义技能说明

这是一个 **agentskills.io 兼容**的 Hermes Agent 技能，用来在提交挑战作业前做结构化自检。

## 它解决什么问题

C 系列挑战的交付目录有几条硬规则，靠眼睛检查总会漏：

1. 必备文件必须齐（安装记录 / 配置说明 / demo / AI日志 / 拿来说明）；
2. 文件命名必须是 `<姓名拼音>_<挑战ID>_<内容描述>.<扩展名>`；
3. 不能有空文件；
4. AI 日志不能是一句话敷衍（rubric 里是 red flag）。

这个技能把上面四条变成一条命令，输出 markdown 表格，`exit 0` 代表全过。

## 目录结构

```
challenge-deliverable-check/
├── SKILL.md                      # 技能正文（元数据 + 操作手册，符合官方章节顺序）
└── scripts/
    └── check_deliverables.py     # 159 行，仅用标准库，无第三方依赖
```

## 安装到 Hermes

```bash
# 技能目录即 source of truth
cp -R challenge-deliverable-check ~/.hermes/skills/
hermes skills list | grep challenge     # 应显示 local / enabled
```

## 用法

```bash
python3 ~/.hermes/skills/challenge-deliverable-check/scripts/check_deliverables.py \
  "<交付目录>" \
  --pack "<挑战资料包目录，含 challenge.yaml>" \
  --name JingXueQing
```

| 参数 | 说明 |
|---|---|
| 位置参数 | 交付目录（必填） |
| `--pack` | 挑战资料包；从 `challenge.yaml` 读 `id` / `deliverables_pattern` / `deadline` |
| `--name` | 姓名拼音，用于命名校验（必填） |
| `--challenge-id` | 手动指定挑战 ID（省略时取自挑战包） |
| `--required` | 覆盖必备文件 glob，如 `'*AI日志*' '*安装记录*'` |

## 设计要点（为什么这么写）

- **规则不写死。** 挑战 ID、必备文件、截止时间都从挑战包读，换一个挑战不用改代码。
- **必备文件对「目录」也匹配。** 证据包常以目录形式交付（如 `xxx_demo/`），只匹配文件名会漏判。
- **命名检查只看顶层文件。** 嵌套的证据文件与技能包保留自身规范命名，否则误报一片。
- **只报不改。** 技能不删不改任何文件——交付物是用户的东西，检查器只有读权限。

## 在 Hermes 里的两种调用方式（实测均可用）

```bash
# 1) 手动跑脚本（最稳，模型不参与）
python3 ~/.hermes/skills/challenge-deliverable-check/scripts/check_deliverables.py <dir> --pack <pack> --name JingXueQing

# 2) 绑定到定时任务，每晚自检（已配置）
hermes cron create "0 21 * * *" "运行 challenge-deliverable-check 技能检查交付目录" \
  --name "C10H交付物自检" --deliver local --skill challenge-deliverable-check
```

## 本次实战输出（C10H 交付目录）

```
| 检查项 | 结果 |
|---|---|
| 必备文件 `*安装记录*` | ✓ JingXueQing_C10H_安装记录.md |
| 必备文件 `*配置说明*` | ✓ JingXueQing_C10H_配置说明.md |
| 必备文件 `*demo*` | ✓ …（20 个文件） |
| 必备文件 `*AI日志*` | ✓ JingXueQing_C10H_AI日志.md |
| 命名规范 <Name>_<ID>_<描述> | ✓ 全部合规 |
| 空文件检查 | ✓ 无空文件 |
| AI 日志非空且 >500 字节 | ✓ 10767 字节 |

**结论：全部通过。**   exit=0
```

> 第一次跑它的时候，它自己抓出 3 个问题（demo 目录没被识别、证据文件命名不合规、一份日志是空文件）。修的是交付物，也顺手修了技能自身两条过严的规则——**技能被自己用一遍，才知道规则哪里写歪了**（详见 AI 日志 R8）。
