---
name: wechat-publisher-pro
description: "Convert Markdown or Word documents into WeChat Official Account (微信公众号) ready-to-paste HTML with inline-CSS styling, four selectable themes, callout boxes (知识/实践/注意/踩坑/重点), auto table of contents, article metadata, footer copyright, Chinese typography spacing, base64-embedded local images, syntax-highlighted code blocks, batch conversion, and a built-in WeChat-compliance auditor. This skill should be used when the user says 公众号文章, 微信公众号格式, 转换成公众号, 排版公众号, 推文, or provides a .md or .docx file and asks to format it for WeChat publishing. Also trigger when the user mentions publishing an article, or preparing content for mp.weixin.qq.com."
agent_created: true
---

# WeChat Publisher Pro — Markdown/Word → 公众号 HTML

## Purpose

把 Markdown / Word 文章转成**可直接粘贴进微信公众号编辑器**的 HTML，并保证
粘贴后格式不丢失。定位是"公众号的打印驱动"：你给内容，它给排版。

本技能基于 C4B starter kit 深度改造，**修掉了 starter 实测复现的 12 个缺陷**，
并新增 12 项能力（多主题、callout、目录、元数据、页脚、中文排版、图片内嵌、
批量、语法高亮、合规体检、手机预览、Word 表格/列表支持）。

## Quick Start

```bash
# 1. 装依赖（推荐虚拟环境）
python -m pip install markdown beautifulsoup4 python-docx lxml Pillow pygments

# 2. 转换
python scripts/wechat_publisher.py article.md out.html --toc --footer

# 3. 打开 out.html → 选中白框内正文 → 复制 → 粘到 mp.weixin.qq.com
```

> 每次转换产出**两个文件**：
> - `out.html` —— 带边框的预览页（浏览器看效果用，别复制外壳）
> - `out.body.html` —— 纯正文，直接全选复制

## Core Workflow

```
读取源文件 → 解析元数据 → Markdown→HTML → 语义化转换（callout/代码/图片/表格）
→ 注入 inline CSS（主题）→ 中文排版 → 属性清理 + CSS白名单 → 合规体检 → 输出
```

## The Extended Markdown Syntax

除了标准 Markdown，本技能支持以下扩展语法：

### Callout 提示框

```
:::note
📘 知识框（默认）
:::

:::tip 实践标题
💡 实践框，标题可自定义
:::

:::warn
⚠️ 注意框
:::

:::danger
🔥 踩坑框
:::

:::key
⭐ 重点框
:::
```

规则：开闭 `:::` 必须**独占一行**；框内支持完整 Markdown（代码、加粗、列表）。

### 文章元数据（YAML frontmatter）

文件开头写：

```yaml
---
title: 我的文章标题
author: JingXueQing
date: 2026-10-05
tags: AI, 技能开发
abstract: 这段会渲染成摘要卡片，也应复制到公众号摘要栏。
cover: cover.png
---
```

缺省时会自动推断：标题取第一个 `#`，摘要取第一个 `>` 引用，作者默认 `JingXueQing`。

### 标题编号

`##` 自动编号为 `1.` `2.`，`###` 为 `1.1` `2.1`。用 `--no-number` 关闭。

### 图片与图注

```markdown
![替代文本](assets/pic.png)
（紧跟图片的单独短段落会自动变成居中小字图注）
```

本地图片自动转 base64 内嵌（避免粘贴后裂图）。**SVG 不支持**，会跳过并在报告里提示。

## CLI Reference

| 参数 | 说明 | 默认 |
|------|------|------|
| `--theme {ink,forest,amber,mono}` | 主题 | `ink` |
| `--toc` | 生成目录卡片 | 关 |
| `--footer` / `--footer-text "..."` | 页脚版权 | 关 |
| `--cjk-spacing {thin,space,none}` | 中英文间距 | `thin` |
| `--preview {desktop,phone}` | 预览页宽度 | `desktop` |
| `--no-highlight` | 关闭代码高亮 | 关 |
| `--no-number` | 标题不编号 | 关 |
| `--no-meta-header` | 正文顶部不渲染元信息块 | 关 |
| `--audit` | 只做合规体检，不出文件 | — |
| `--list-themes` | 列出全部主题 | — |
| `--batch DIR --out-dir DIR` | 批量转换 | — |

## Compliance Auditor

```bash
python scripts/wechat_publisher.py article.md --audit
```

扫描成品 HTML 里的公众号违规项并给出修复建议：

| 代码 | 含义 |
|------|------|
| `TAG_SCRIPT/STYLE/IFRAME/DIV/H1/SVG` | 残留禁用标签 |
| `ATTR_CLASS/ATTR_ID` | 残留 class/id |
| `CSS_LAYOUT` | style 里有 position/float/flex/grid/@media |
| `IMG_EXT` | 图片既非 data: 也非微信 CDN |
| `IMG_SVG` | SVG（微信保存时会消失） |
| `LEN` | 正文可能超 2 万字 |

高危项存在时退出码为 1，可直接接入 CI。

## Known Constraints（诚实说明）

1. **目录不可点击跳转**。公众号会剥离 `id` 锚点，所以本技能的目录是**静态卡片**。
   需要点击跳转，只能在微信编辑器里手动给标题加书签链接。
2. **外链图片不可靠**。本技能无法上传素材库，只能原样保留并提示。
   稳妥做法：发布前把图片传到公众号素材库，替换为 `mmbiz.qpic.cn` 地址。
3. **不发布文章**。本技能只产出 HTML 和发布 SOP，**不代你登录公众号**。
   最后一步粘贴发布必须人工完成。
4. **SVG 会被丢弃**。这是微信行为，不是本技能能绕过的。
5. **语法高亮依赖 pygments**。未安装时自动降级为纯文本代码块。

## Testing

```bash
python tests/eval_suite.py              # 24 用例 / 117 断言
python tests/eval_suite.py --verbose    # 逐条明细
python tests/eval_suite.py --json r.json # 机读结果
python tests/eval_suite.py --only T07   # 跑单个用例
```

测试覆盖三类：功能正确性、微信合规性、以及针对 starter 12 个缺陷的**回归防护**。
改代码后必须重跑，全绿才算完成。

## Publishing SOP（发布流程）

1. `python scripts/wechat_publisher.py article.md out.html --theme ink --toc --footer`
2. 浏览器打开 `out.html`，**只选中白框内正文**复制
3. 打开 mp.weixin.qq.com → 新建图文
4. 标题栏填 frontmatter 的 `title`，摘要栏填 `abstract`
5. 粘贴正文 → 上传封面
6. 检查外链图片是否需要换 CDN 地址
7. 手机预览 → 发布

详细版见 `references/publishing_sop.md`。

## Customization

| 想改什么 | 改哪里 |
|----------|--------|
| 配色 | `scripts/wechat_publisher.py` 的 `THEMES` |
| 字号间距 | 同文件的 `StyleFactory` |
| 新增主题 | 复制 `THEMES["ink"]` 一份改颜色 |
| 新增 callout 类型 | `CALLOUT_KINDS` 加一项 |
| 公众号限制规则 | `ALLOWED_TAGS` / `ALLOWED_CSS_PROPS` / `DROP_TAGS` |

改完务必重跑 `tests/eval_suite.py`。

## File Map

```
wechat-publisher-pro/
├── SKILL.md
├── scripts/
│   └── wechat_publisher.py       # 转换器（唯一入口）
├── references/
│   ├── wechat_restrictions.md    # 公众号 HTML 限制速查
│   ├── wechat_styles.md          # 样式值速查
│   └── publishing_sop.md         # 从 Markdown 到发布的完整 SOP
├── examples/
│   └── demo_article.md           # 演示全部扩展语法
└── tests/
    ├── eval_suite.py             # 24 用例 / 117 断言
    └── fixtures/                 # 测试样本
```

## Author

JingXueQing（学号 2024102110351）｜ Elite20 Challenge C4B
基于 C4B starter kit 改造，遵循 skill-creator 流程：intent → draft → eval → iterate。
