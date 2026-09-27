# C1 课程资料获取与翻译

> 挑战：C1 课程资料获取与翻译　|　挑战编号：`ch-20260717031336-pxzwy0`　|　作者：jingxueqing
> 平台要求交付物：`README.md`、`*AI日志*`、`*AAR*`、`*拿来说明*`

## 1. 交付物对应关系

| 平台要求 | 本仓库文件 | 说明 |
| --- | --- | --- |
| `README.md` | `README.md` | 本文件：任务口径、语料规模、方法、复跑方式 |
| `*AI日志*` | `AI日志.md` | 与 AI 协作的过程记录：指令 → AI 输出 → 问题 → 我的纠正 |
| `*AAR*` | `AAR.md` | 事后复盘：预期 vs 实际、差异原因、经验与改进 |
| `*拿来说明*` | `拿来说明.md` | 4 条关键决策记录（含被否掉的方案与理由） |

## 2. 我理解的任务

把课程提供的英文资料**完整抓取下来并译成中文**，同时证明两件事：**译全了**（覆盖度可算）和**译一致**（术语统一）。所以我没有采用「整篇丢给模型翻一遍」的做法，而是先搭一条**可复跑、可校验的管线**，再让 AI 在管线的约束下批量翻译。

## 3. 语料规模（实测数字）

| 项目 | 数值 |
| --- | --- |
| 下载材料 | `CS146S_offline.zip` 15,151,528 字节；`Vibe_Coding_Playbook.pdf` 7,964,392 字节 |
| 解包结果 | 44 个文件，约 22.1 MB（`.html` 33、`.pdf` 3、`.txt` 2、`.png` 2、`.js` 1、`.css` 1、`.json` 1、`.md` 1） |
| 抽取后语料 | **473 段 / 560,465 字符 / 35 个文档**（其中来源于 PDF 的 75 段；33 个文档含 ≥200 字符正文段） |
| 英文规模 | 约 84,000 英文词 |
| 分段粒度 | 每段约 1,200 字符（`SEG_CHARS = 1200`） |
| 翻译批次 | 30 批（`--size 16`） |

## 4. 方法：一条管线，七个可复跑步骤

所有步骤都在 `pipeline/pipeline.py` 里，命令式、无交互、可重复执行：

| 命令 | 作用 |
| --- | --- |
| `sync` | 归集材料、建立 SHA-256 清单，保证「哪一版资料」可追溯 |
| `extract` | 抽取正文并分段，带**质量闸门**（过滤二进制噪声） |
| `batch` | 按 1,200 字符把段分成批次文件 `build/batches/batch-NN.md` |
| `glossary` | 从术语表 JSON 渲染出人类可读的 `glossary/术语表.md` |
| `collect` | 把 `translation/out/*.md` 的译文按文档归位到 `build/zh/<doc>.md` |
| `assemble` | 产出 `translation/<doc>.zh.md`（纯中文）与 `<doc>.bi.md`（中英对照） |
| `verify` | 校验**源文件哈希**、逐文档覆盖率、未译段清单、术语未命中清单 |

三条为保证「可验收」而定下的硬约定：

1. **段落定位标记**：每段译文前必须有 `<!-- seg:<文档名>#<三位段号> -->`。源有多少段、译出多少段可以**枚举比对**，漏译能定位到段号，而不是凭感觉说「翻完了」。
2. **译文落盘**：译文写到 `translation/out/batch-NN.md`，不在对话里贴。中途断了可以从任意批次续跑。
3. **哈希校验**：`verify` 会比对源文件哈希。原文更新了而译文没重译，会直接报出来，避免「改了源、交了旧译」。
4. **分母只算一次**：覆盖率分母固定为 `segments.jsonl` 的全部 473 段，与分批口径一致；≤200 字符的 40 个短片段**同样计入、不设免检区**（早期版本把它们排除在统计外，会掩盖漏译，已修正）。
5. **输入目录自清**：`batch` 每次先删除 `build/batches/batch-*.md` 再重新分批。曾出现早期实验残留 118 个批次文件（实际应只有 30 个），不清掉会把过期分段混进翻译输入。

## 5. 三个技术问题与处理方式

1. **二进制噪声污染语料**：常规 PDF 文本抽取把 `/Filter /DCTDecode` 的 JPEG 字节当正文读出来，一次抽出 **487 万字符**乱码。处理：在抽取函数内加**双指标质量闸门**（段长 ≥200、可打印率 >0.95、字母+空格率 >0.7），并跳过不含 `Tj`/`TJ` 的内容流。结果：398 段 / 451,541 字符，噪声清零，未误杀正文。
2. **PDF 抽不出文字**：先写 Swift 版 OCR，`swiftc` 报 `error: redefinition of module 'SwiftBridging'`（本机 SDK 与编译器版本不匹配）。处理：**不修工具链、不装依赖**，改用 ObjC + clang 调同一套系统 Vision，`pipeline/ocr.m` 一次编译通过，4 份讲义全量识别。
3. **OCR 漏认中文**：第一版只声明 `en-US`，中文课件被当英文硬认，只得到 2,772 字符乱码。处理：识别语言改为 `zh-Hans` 优先，**重编译后对同一份 PDF 复跑验证**，字符数 2,772 → **4,174**，中文标题正常。

> 关于 `skipped`：OCR 输出里的 `skipped` 表示**该页识别结果为空**（单页无文字），不是整份文档失败。本次唯一跳过的是 `how-anthropic-uses-claude-code` 第 23 页。

## 6. 术语一致性

`glossary/术语表.json`（51 条）分三类约束，避免「同一个词十种译法」：

- `keep_en`（14 个词保持英文原词）：`MCP`、`Claude Code`、`Codex`、`Copilot`、`Devin`、`Warp`、`SRE`、`SAST`、`DAST`、`OWASP`、`RCE`、`LLM`、`API`、`GitHub`；
- `terms`：术语 → 指定中文译法；
- `banned`：禁用译法（如不得用「代理人」而用「智能体」、不得用「提示工程」指 prompt 而用「提示词工程」）。

`verify` 会列出**术语未命中**清单，把「术语一致」从人工印象变成可检项。翻译执行口径单独固化为 `translation/翻译作业说明.md`，执行方按文件执行，不依赖对话记忆。

## 7. 当前状态与证据

- **管线全链已跑通**（小样试跑，7 个真实段 / 5 个文档）：`collect` → `{"docs":5,"segments":7,"conflicts":[]}`；`assemble` → `{"docs":35,"assembled":5}`；`verify` → `{"source_hash_ok":true,"coverage":"7/473 = 1.5%","tiny_segments_le200":40}`。首轮试跑还抓到 1 处术语违规（写了禁用词「提示工程」），已改为「提示词工程」。
- **全量翻译（473 段 / 30 批）**：进行中。完成后本节会补上 `verify` 的覆盖率、未译段数、术语未命中数，以及抽查的段号与质量结论。
- **未完成即如实标注**：本文件与 `AI日志.md` 中凡未回填的数字，都保留「待补」标记，不做未验证的声明。

## 8. 如何复跑

```bash
cd C1
python3 pipeline/pipeline.py sync
python3 pipeline/pipeline.py extract
python3 pipeline/pipeline.py batch --size 16
# 逐批次把译文写入 translation/out/batch-NN.md（格式见 translation/翻译作业说明.md）
python3 pipeline/pipeline.py collect
python3 pipeline/pipeline.py assemble
python3 pipeline/pipeline.py verify
```

环境要求：macOS + 内置 `python3`；OCR 用系统 Vision/PDFKit（离线，无需第三方依赖）。

## 9. 目录结构

```
C1/
├── README.md                  本文件
├── AI日志.md                   与 AI 协作的过程记录
├── AAR.md                      事后复盘
├── 拿来说明.md                 关键决策记录
├── 挑战_C1 ..._材料/            平台下载的原始材料
├── sources/                   材料归集（含 offline/CS146S_offline/）
├── pipeline/
│   ├── pipeline.py             管线（sync/extract/batch/glossary/collect/assemble/verify）
│   └── ocr.m                   ObjC OCR 源码（系统 Vision）
├── glossary/
│   ├── 术语表.json             术语表（keep_en / terms / banned）
│   └── 术语表.md               渲染版
├── build/
│   ├── segments.jsonl          分段语料（473 段）
│   ├── batches/                批次文件（30 批）
│   └── zh/                     按文档归位的中文段
├── translation/
│   ├── out/                    逐批次译文（batch-NN.md）
│   ├── 翻译作业说明.md          翻译执行口径
│   └── *.zh.md / *.bi.md       纯中文 / 中英对照产物
└── work/ocr/                   OCR 可执行与文本产物
```

## 10. 边界与说明

- `all_urls`（URL 清单）与 `robots.txt` 属索引/规则文件，不作为翻译对象，但保留在语料中并在覆盖率统计里单列。
- 有 3 段属**站点提示类超短文本**（如「需要启用 JavaScript」「Powered by Ghost」、付费墙提示），按原样翻译并归入语料，不做删除——删除会让覆盖率对不上。
- OCR 依赖 macOS 系统框架；换到其他平台需要替代实现，管线其余部分与平台无关。
