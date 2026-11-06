---
name: challenge-deliverable-check
description: "Audit a challenge deliverable folder against its own naming rules."
version: 1.0.0
author: JingXueQing
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Education, Deliverables, Quality, Checker]
    category: productivity
---

# Challenge Deliverable Check Skill

Validates a challenge submission folder before it is handed in: required files
listed by the challenge itself, the `<Name>_<CHALLENGE_ID>_<描述>` naming
convention, empty artifacts, and whether the mandatory AI log actually has
content. It reports; it never edits or deletes anything.

## When to Use

- A challenge pack is on disk (`challenge.yaml` / `challenge.json`) and a
  deliverable folder is about to be submitted.
- A reviewer asks "这份提交齐了吗" and a rule-based answer is wanted instead of
  eyeballing the folder.
- Not for content quality — this checks structure and naming, not whether the
  writing is any good.

## Prerequisites

- Python 3.9+ available as `python3` (stdlib only, nothing to install).
- The challenge pack directory (optional but recommended — it supplies the
  `deliverables_pattern` and `deadline`).

## How to Run

```bash
python3 ~/.hermes/skills/challenge-deliverable-check/scripts/check_deliverables.py \
  "<交付目录>" --pack "<挑战资料包目录>" --name JingXueQing
```

Exit code `0` = all checks pass, `1` = at least one check failed. The markdown
report goes to stdout, so it can be pasted straight into a submission note.

## Quick Reference

| Flag | Meaning |
|---|---|
| positional `deliver_dir` | 交付物目录（必填） |
| `--pack` | 挑战资料包目录，读取 `challenge.yaml` 的规则 |
| `--name` | 姓名拼音，用于命名校验（必填） |
| `--challenge-id` | 挑战 ID，如 `C10H`；省略时取自挑战包 |
| `--required` | 覆盖必备文件 glob，如 `'*AI日志*' '*安装记录*'` |

## Procedure

1. 确认交付目录存在，跑一次默认检查，先看 `✗` 有几行。
2. 若提示「无法确定挑战 ID」，补 `--challenge-id` 或检查 `challenge.yaml` 是否存在。
3. 按报告逐项修：先补缺失的必备文件，再改命名，最后处理空文件。
4. 修改后重跑，直到输出 `结论：全部通过。`，把报告贴进 README 的验收章节。

## Pitfalls

- 命名规则只检查「前缀姓名 + 第二段挑战 ID + 描述段」，中文描述段不做语义判断。
- 命名检查**只看顶层文件**：`README*`、`LICENSE` 以及交付目录内嵌套的证据文件/技能包文件
  保留自己的规范命名，不参与 `<Name>_<ID>_<描述>` 校验——否则几乎每个交付目录都会被误报。
- 必备文件 glob 同时对**文件与目录名**匹配，所以 `*demo*` 这种以目录形式交付的证据包能被识别。
- 目录里如果有 `.DS_Store` 之类隐藏文件，脚本已跳过；但 `--required` 用的是单层 glob，
  不匹配子目录路径，嵌套结构要自己确认。
- AI 日志阈值 500 字节是下限而非合格线，内容质量仍需人工看。

## Verification

```bash
python3 ~/.hermes/skills/challenge-deliverable-check/scripts/check_deliverables.py \
  "<交付目录>" --pack "<挑战包>" --name JingXueQing; echo "exit=$?"
```

期望输出末尾出现 `**结论：全部通过。**` 且 `exit=0`；故意传一个空目录时应输出
`✗ 缺失` 并 `exit=1`。
