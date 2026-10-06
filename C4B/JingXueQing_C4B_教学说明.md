# 教学说明：安装与使用 wechat-publisher-pro

> 作者：JingXueQing ｜ 学号：2024102110351
> 30 秒上手，含完整参数表与排错手册。

---

## 一、这是什么

把 Markdown / Word 转成**可以直接粘贴进微信公众号编辑器**的 HTML 的命令行工具。

- **输入**：`.md` / `.docx` / `.html`
- **输出**：公众号 HTML（inline CSS，无违规标签）+ 浏览器预览页
- **不做什么**：不登录公众号、不上传图片、不代你发布

---

## 二、安装（3 分钟）

### 1. 装依赖

推荐用虚拟环境，别污染系统 Python：

```bash
git clone <本技能目录> && cd wechat-publisher-pro

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install markdown beautifulsoup4 python-docx lxml pygments
```

> `pygments` 是可选的，装了才有代码语法高亮；不装会自动降级为纯文本代码块。
> `Pillow` 仅在需要生成图片时用得到，普通转换不必装。

**Windows 用户**如果遇到编码报错，先设：

```powershell
chcp 65001
$env:PYTHONUTF8 = "1"
```

### 2. 验证安装

```bash
python scripts/wechat_publisher.py --list-themes
```

能列出 4 套主题就装好了。

### 3. 跑测试（可选但强烈建议）

```bash
python tests/eval_suite.py
```

预期输出 `用例通过率 27/27`。

---

## 三、30 秒上手

```bash
# 转换
python scripts/wechat_publisher.py my_article.md out.html --toc --footer

# 打开 out.html，选中白框内正文，复制
# 打开 https://mp.weixin.qq.com → 新建图文 → 粘贴 → 预览 → 发布
```

**⚠️ 一定要复制 `out.body.html`，或者只复制预览页白框里的内容。**
复制整个 `out.html` 会把外层边框样式也带进去，公众号里会显示一个灰框。

---

## 四、写文章：用上扩展语法

### 4.1 文件开头写元数据

```markdown
---
title: 我给公众号排版做了一个技能
author: JingXueQing
date: 2026-10-05
tags: AI技能, 内容生产
abstract: 一句话说清读者能得到什么。
cover: cover.png
---

正文从这里开始……
```

| 字段 | 作用 | 必填 |
|------|------|------|
| `title` | 填公众号标题栏 | 建议 |
| `author` | 显示在标题下 | 建议 |
| `date` | 页脚会引用 | 建议 |
| `tags` | 显示在标题下 | 可选 |
| `abstract` | 渲染成摘要卡片 | 建议 |
| `cover` | 封面（自动转 base64） | 可选 |

不写也能跑：标题取第一个 `#`，摘要取第一个 `>` 引用，作者默认 `JingXueQing`。

### 4.2 Callout 提示框

```
:::note
知识框（蓝色）
:::

:::tip 自定义标题
实践框（绿色）
:::

:::warn
注意框（橙色）
:::

:::danger
踩坑框（红色）
:::

:::key
重点框（紫色）
:::
```

:::warn 规则
- `:::` 标记必须**独占一行**，前后不要有空格以外的字符
- 框内可以写完整的 Markdown（代码、加粗、列表都行）
- 建议一篇文章里 `:::key` 最多用 2 次，用多了就不"重点"了
:::

### 4.3 其他约定

- **标题编号**：`##` 自动编号为 `1.` `2.`，`###` 为 `1.1`。加 `--no-number` 关闭
- **图注**：紧跟在图片后面的、40 字以内的独立段落，会自动变成居中小字
- **图片**：本地图片用相对路径引用，会自动转 base64。**SVG 不支持**
- **分隔线**：`---` 会变成带边框的分隔线

---

## 五、参数速查

```bash
# 主题（默认 ink）
--theme {ink|forest|amber|mono}

# 目录 / 页脚
--toc
--footer
--footer-text "我的版权声明 2026"

# 排版细节
--cjk-spacing {thin|space|none}   # 中英文间距，默认 thin
--no-highlight                    # 关闭代码高亮
--no-number                       # 标题不编号
--no-meta-header                  # 正文顶部不显示标题/作者信息块

# 预览
--preview {desktop|phone}         # phone = 375px 手机模拟

# 合规体检
--audit

# 批量
--batch ./posts --out-dir ./html --pattern "*.md"

# 主题清单
--list-themes
```

### 主题怎么选

| 主题 | 适合 |
|------|------|
| `ink` 墨蓝 | 技术教程、复盘长文（默认，最百搭） |
| `forest` 松绿 | 长文阅读，绿色护眼 |
| `amber` 暖橙 | 经验分享、学习心得、故事 |
| `mono` 黑白 | 学术报告、克制的风格 |

### 参数组合推荐

| 场景 | 命令 |
|------|------|
| 技术长文 | `--theme ink --toc --footer --safe-code` |
| 学习心得 | `--theme amber --footer` |
| 学术报告 | `--theme mono --toc` |
| 交作业截图 | 加 `--preview phone` |
| 每次发布前 | 先跑 `--audit`，0 高危再走 |

### 5.1 `--safe-code` 是什么，为什么发布时推荐

代码块的换行原本靠 `white-space: pre-wrap`。但**微信对这个属性的支持不稳定**——
一旦被剥离，整段代码会塌成一行（就是 starter kit 最致命的那个 bug）。

`--safe-code` 做三件事，任何一项单独失效都不影响结果：

| 机制 | 作用 | 抗剥离性 |
|------|------|---------|
| `<br />` 显式断行 | 换行**不依赖 CSS** | ★★★ 完全不依赖 |
| `padding-left` 表达缩进 | 缩进层级 | ★★☆ 微信支持较稳 |
| `\u00a0` 不换行空格 | 缩进双保险 | ★☆☆ 折叠风险 |
| `white-space: pre-wrap` 保留 | 正常时的最优呈现 | ★☆☆ 可能被剥离 |

**代价：safe 模式放弃语法高亮。** 因为高亮的 `<span>` 会被行边界切断，
所以两个模式二选一：

| 模式 | 命令 | 代码颜色 | 抗剥离 |
|------|------|---------|--------|
| 高亮优先 | 默认 | ✅ 有 | 中 |
| **结构优先** | `--safe-code` | ❌ 无 | **高** |

> **建议**：技术文章代码多 → 用默认模式（颜色能帮读者读懂）；
> 担心微信环境不稳定 / 代码是核心内容 → 用 `--safe-code`。
> 交付目录里的 `JingXueQing_C4B_output.html` 是 **safe 版**，
> `附_对比版_高亮代码.html` 是高亮版，可打开对比。

---

## 六、发布流程（完整版见 `references/publishing_sop.md`）

```bash
# 1. 转换
python scripts/wechat_publisher.py article.md out.html --theme ink --toc --footer

# 2. 自查（必须 0 高危）
python scripts/wechat_publisher.py article.md --audit

# 3. 浏览器打开 out.html，手机预览一遍

# 4. mp.weixin.qq.com → 新建图文
#    标题栏填 title，摘要栏填 abstract，正文粘贴 out.body.html

# 5. 手机上再翻一遍 → 发布
```

---

## 七、排错手册

### 报错类

**`❌ 缺少依赖：markdown beautifulsoup4`**
→ 没装或没激活虚拟环境。`pip install markdown beautifulsoup4 python-docx lxml`

**`❌ 文件不存在`**
→ 检查路径。批量模式注意 `--batch` 要给目录不是文件。

**Windows 报 `UnicodeEncodeError`**
→ 执行 `chcp 65001` 和 `$env:PYTHONUTF8 = "1"`。

**`SyntaxError` 指向 markdown 里的 `:::`**
→ 你的文章里直接写了 `:::`，被误当成 callout 起止标记。检查 callout 语法。

### 输出效果类

**粘贴后格式全乱**
→ 复制了 `out.html` 的外壳。改用 `out.body.html`。

**图片不显示**
→ 可能是外链图（`https://`），微信会拒收。把图放在 md 同级目录用相对路径引用，
会自动转 base64。

**代码块缩进没了**
→ 微信对 `white-space:pre-wrap` 支持不稳定。缩进若丢失，说明平台重写了样式。
应急方案：把代码截图，或缩短代码行宽。

**表格手机端挤成一团**
→ 列数 ≥5 时拆表（`--audit` 会提示 `宽表格`）。

**目录点不动**
→ **这是平台限制，不是 bug。** 公众号会剥离 `id` 锚点。
需要点击跳转，在微信编辑器里给标题手动加「书签」链接。

**代码没有颜色**
→ 没装 pygments。`pip install pygments`。或用 `--no-highlight` 明确关闭。

**中英文之间没空格**
→ 用了 `--cjk-spacing none`。默认是 `thin`（U+2009 极细空格）。

### 体检器报警

| 报警 | 意思 | 怎么办 |
|------|------|-------|
| `[高] TAG_DIV` | 残留 `<div>` | 正常情况不会出现，若出现请提 issue |
| `[高] ATTR_CLASS` | 残留 `class=` | 同上 |
| `[中] IMG_EXT` | 外链图 | 发布前传素材库换 CDN 地址 |
| `[高] IMG_SVG` | SVG 图 | 转成 PNG |
| `[中] LEN` | 可能超 2 万字 | 拆成上下篇 |
| `[中] IMG_MISS` | 图片找不到 | 检查相对路径是否相对 md 文件 |

---

## 八、二次开发

| 想改 | 改哪里 |
|------|--------|
| 配色 | `scripts/wechat_publisher.py` → `THEMES` |
| 字号、行距、间距 | 同文件 → `StyleFactory` |
| 加新主题 | 复制 `THEMES["ink"]` 一份改颜色 |
| 加新 callout 类型 | `CALLOUT_KINDS` 加一项 |
| 改支持哪些标签 | `ALLOWED_TAGS` |
| 改允许哪些 CSS | `ALLOWED_CSS_PROPS` |
| 加新测试用例 | `tests/fixtures/` 放样本 → `tests/eval_suite.py` 加断言 |

**改完必须重跑测试：**

```bash
python tests/eval_suite.py --verbose
```

全绿才算完成。测试用例 T01–T10 是针对 starter 12 个缺陷的**回归防护**，
改代码时如果它们变红，说明你把修好的 bug 改回去了。

---

## 九、目录结构

```
wechat-publisher-pro/
├── SKILL.md                          # 技能主文件（AI 读这个）
├── scripts/
│   └── wechat_publisher.py           # 转换器（唯一入口，1518 行）
├── references/
│   ├── wechat_restrictions.md        # 公众号 HTML 限制速查
│   ├── wechat_styles.md              # 样式取值速查
│   └── publishing_sop.md             # 完整发布 SOP
├── examples/
│   ├── demo_article.md               # 演示全部扩展语法
│   └── assets/demo.png
└── tests/
    ├── eval_suite.py                 # 27 用例 / 135 断言
    └── fixtures/                     # 19 个测试样本
```

---

## 十、许可与署名

基于 C4B 官方 starter kit 改造。starter kit 归属挑战主办方。
本改造版本作者：JingXueQing（2024102110351）。
