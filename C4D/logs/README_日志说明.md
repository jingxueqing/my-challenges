# 原始日志说明

本目录存放**未经加工**的原始日志，作为截图与报告的佐证。

| 文件 | 内容 |
|---|---|
| `ollama_serve_关键日志.txt` | 服务启动日志关键行。**重点是 `inference compute ... library=Metal name=MTL0 description="Apple M1"`** —— 这一行证明走的是 GPU 加速而非 CPU 回退（踩坑③：换目录启动会退化成 `library=cpu`） |
| `模型拉取记录.txt` | 模型下载进度原始输出。含 E2B 拉取完成记录，以及 Q8 对照组**中途放弃**的记录 |

主证据在 `../JingXueQing_C4D_agent-skill/reports/*.json`，
截图底部均标注了对应的来源文件名。

未收录 `ollama_serve.log` 全量文件的原因：其中含服务器环境变量快照
（含本机路径），与本挑战无关且不适合公开。
