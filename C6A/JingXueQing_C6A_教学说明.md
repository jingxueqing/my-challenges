# C6A 教学说明：怎么装、怎么跑、怎么更新数据

> 面向：下一期接手的同学 / 助教 / 想把系统改成自己班版本的人
> 假设：macOS 或 Linux，有 Python 3.9+。**不需要联网，不需要 Node，不需要数据库。**

---

## 1. 这个系统由什么组成（30 秒版）

```
JingXueQing_C6A_pipeline/   脚本（唯一需要动的地方）
JingXueQing_C6A_数据/       数据产物（脚本生成，不用手改）
JingXueQing_C6A_仪表盘/  网站（双击 index.html 就能看）
JingXueQing_C6A_report.xlsx Excel 报表（脚本生成）
```

一条命令：`python3 run.py all` —— 从官方 CHALLENGE.md 抽规格 → 扫本机提交包 → 出 JSON/CSV → 出 Excel → 出网站 → 出日报。

---

## 2. 第一次跑（3 步）

### 2.1 装依赖（只装一个）

```bash
python3 -m pip install openpyxl
```

> 本项目实测环境：`Python 3.13.12` + `openpyxl 3.1.5`。
> 其余全部是标准库（`json / csv / re / pathlib / fnmatch / difflib / collections`），网站没有任何第三方库（无 CDN、无框架）。

### 2.2 确认两个路径对得上你的机器

打开 `JingXueQing_C6A_pipeline/config.json`，改这两处：

```jsonc
{
  "roots": [
    { "path": "/Users/jingxueqing/Desktop/挑战的产物", "label": "本机交付目录", "kind": "delivery_root" },
    // 数据根下的子目录都会被当作「提交包」逐个扫描；
    // 若某个包不在交付目录里（例如已挪到桌面），再登记一个根，并用 include_only 只认它，
    // 否则桌面上其它文件夹会被误当成提交包。
    { "path": "/Users/jingxueqing/Desktop", "label": "桌面根", "kind": "delivery_root",
      "include_only": ["C6A-交付_JingXueQing_提交数据仪表盘"] },
    { "path": "…/真实评审输入", "label": "C4A 评审输入", "kind": "review_input_root" }
  ],
  "challenge_doc_root": "/Users/jingxueqing/Desktop/我的挑战"
}
```

- `roots` = **提交包所在目录**（可以是多个，每个根目录下的**一级子目录**会被当成一个提交包）
- `challenge_doc_root` = **官方挑战文档所在目录**（每个子目录里要有 `CHALLENGE.md`）

### 2.3 跑

```bash
cd JingXueQing_C6A_pipeline
python3 run.py all
```

看到最后一行 `✅ 完成` 就成了。然后：

```bash
open ../JingXueQing_C6A_仪表盘/index.html      # 看网站
open ../JingXueQing_C6A_report.xlsx               # 看 Excel
```

---

## 3. 日常工作流（有新提交时）

```bash
# ① 把新提交包放进数据根目录（命名规范：姓名_挑战编号_内容.扩展名）
#    例：张三_C4B_AI日志.md、张三_C4B_教学说明.md
#    整个文件夹丢进去也行：张三_C4B_公众号文章/
# ② 一条命令重建
python3 run.py all
# ③ 刷新浏览器（不用重启任何服务，因为是静态页）
```

**只改了一处时的最短命令**：

| 你改了什么 | 跑什么 |
|---|---|
| 放了新提交包 | `python3 run.py scan` |
| 改了官方 CHALLENGE.md（必填项变了） | `python3 run.py specs` 再 `scan` |
| 只想重生成 Excel | `python3 run.py excel` |
| 只想重生成网站 | `python3 run.py site` |
| 要发群里的日摘要 | `python3 run.py digest` |
| 想确认数据没算错 | `python3 run.py check` |

---

## 4. 加一个新挑战（不改代码）

1. 在 `challenge_doc_root` 下新建 `挑战_C11 新挑战名_xxxxxx_完整资料/CHALLENGE.md`，**带一个标题含「交付物」或「需要提交」的章节**，里面写：

   ```markdown
   | 文件 | 说明 |
   |---|---|
   | `姓名_C11_方案设计.md` | 架构与选型 |
   | `姓名_C11_AI日志.md` | AI 使用全过程 |
   ```

2. `python3 run.py specs` → 控制台会打印 `C11  N 项 / 必填 N`，说明规格已抽到。
3. `python3 run.py all` → 矩阵自动多一列 `C11`。

> 如果新挑战的交付项用词很怪（比如「AI 心路历程」），有两种办法：
> - 在 `specs.py` 的 `SLOTS` 里给 `ai_log` 的正则加一个词（一行）；
> - 或者在 `spec_patches.json` 里加补丁（`specs.py` 已支持，补丁必须写 `reason`）。

---

## 5. 加一个新学生

不需要做任何事——**提交包就是学生**。把包放进 `roots` 下，跑一次 `scan`，网站「按学生」页就多一张卡。

如果包名里没有姓名（历史遗留），在 `config.json` 补一条：

```jsonc
"folder_owner_patches": {
  "C1-交付_stanford-vibe-coding-zh": {
    "student": "JingXueQing", "challenge": "C1",
    "reason": "文件夹名未含姓名，按本机交付目录归属本人"
  }
}
```

这条补丁会在网站详情抽屉的「提交包」一栏和 `submissions.json` 的 `attribution` 字段里留痕。

---

## 6. 网站怎么用（给学生/老师的一页说明）

| 想干什么 | 怎么做 |
|---|---|
| 看全班完成情况 | 总览页 → 提交矩阵（✅ 齐全 / ⚠️ 缺件 / ❌ 无记录） |
| 看某个人交了哪些 | 「按学生」页 → 点任意一条记录 |
| 看某个挑战谁缺什么 | 「按挑战」页 → 每个必填项标签上的 `命中/总人数` 就是缺口分布 |
| 找缺件的人去催 | 「缺失项」页 → 最常缺的交付项 + 缺件清单 |
| 按时间回看 | 「时间线」页（按月份分组） |
| 搜索 | 右上角搜索框，快捷键 `/` |
| 分享某条记录 | 地址栏 `#record=姓名|挑战编号`，直接打开对应详情 |

> 页面上所有「❌」都写的是**「本机无记录」**，不是「该同学没交」。这是刻意的：采集不到 ≠ 判定未交。

---

## 7. 常见问题

| 现象 | 原因 | 解法 |
|---|---|---|
| 网站打开是空白 | 用了 `fetch` 方式（改过模板）或 JS 报错 | 本项目数据是**内嵌**的，别改成 fetch；F12 看 Console |
| Excel 打开中文乱码 | 用了 CSV 直接改扩展名 | 用 `make_excel.py` 生成的 xlsx；CSV 是 UTF-8-BOM，Excel 正常识别 |
| 某同学显示「无记录」但他交了 | 包不在 `roots` 一级子目录里，或命名完全不合规 | 把包移到根目录下，或加 `folder_owner_patches` |
| 完整度偏低，但看起来文件都在 | 命中的是「可选」项，或文件在 3 层以下目录 | 打开详情抽屉看逐项清单和「另有 N 个深层文件未计入」 |
| 同一人被算了两份 | 你有两份内容相同的包（如 C2G 有普通版和全量版） | 这是真实情况，`duplicate_package=true` 会标记出来 |
| `run.py` 报 openpyxl 缺失 | 换了 Python 环境 | `python3 -m pip install openpyxl` |

---

## 8. 截图与录屏在哪

`JingXueQing_C6A_screenshots/`：总览、按学生、按挑战、时间线、缺失项、方法与口径、记录详情。

生成方式（可复现，macOS）：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --hide-scrollbars --force-device-scale-factor=2 \
  --window-size=1500,1250 --virtual-time-budget=3500 \
  --screenshot=overview.png "file:///…/JingXueQing_C6A_仪表盘/index.html"
```

---

## 9. 移交清单（下一期照这个做）

- [ ] `pip install openpyxl`
- [ ] 改 `config.json` 的两个路径
- [ ] 把新提交包放进来，命名按 `姓名_挑战_内容.ext`
- [ ] `python3 run.py all`
- [ ] `python3 run.py check` 必须打印「自检通过」
- [ ] 打开 `index.html` 抽查 2 条记录，核对详情里的文件确实是该同学交的
- [ ] `python3 run.py digest` 把 `报告/群里通知_*.txt` 发群
