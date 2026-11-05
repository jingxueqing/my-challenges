"""生成 replay 数据集（chatlog 兼容格式 + 人工标注的 ground truth）。

为什么要生成而不是直接抄真实群：
    真实微信群数据在本机是 SQLCipher 加密的（见 docs/数据说明.md），
    团队评审、CI、别人复现也不能碰真实聊天记录。
    所以准备一份「结构真实、内容脱敏」的回放集：
      - 挑战定义、提交命名规范、AI 日志要求都来自真实课程材料
      - 消息内容由本脚本按真实场景手写（提问/回答/提交流程/催交/闲聊），
        每条都带人工标注的 intent，用来量分类器准确率
      - 学生人名除景雪晴（真实提交来自本机磁盘）外均为合成

用法：
    python data/make_fixtures.py            # 重新生成 data/fixtures/*.jsonl
"""

from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
OUT_DIR = os.path.join(ROOT, "data", "fixtures")
START = datetime(2026, 10, 21, 8, 30)
DAYS = 14
GROUP_ID = "elite20_2026@chatroom"
GROUP_NAME = "AI+X 实验班 Elite20 · 挑战冲刺群"
TEACHER = "班主任 · 李老师"

# (day, "HH:MM", 发送者, 类型, 内容, intent, challenge, reply_back)
# reply_back: None / "prev" / 往回第 N 条
T = "T"


def turns() -> list[tuple]:
    return [
        # ---------- Day 1 ----------
        (1, "08:35", T, "text", "【周会通知】本周三 20:00 线上周会，主题：C8 真实项目立项。请每位同学提前想好你要接的项目方向（A 高校落地 / B 企业本体 Agent / C 课程生产体系）。", "announcement", "C8", None),
        (1, "08:36", T, "text", "另外提醒：C8 的 proposal 里必须有早期验证物，只写文字不算。", "announcement", "C8", None),
        (1, "08:52", "林一舟", "text", "请问 C8 的 demo 一定要能跑起来吗？还是截个架构图就行？", "question", "C8", None),
        (1, "09:01", T, "text", "要能跑。哪怕只跑通一个 Level，也比一张漂亮的架构图有说服力。", "answer", "C8", "prev"),
        (1, "09:03", "赵明轩", "text", "C5 的仓库是公开还是私有？我这边的项目有点商业信息。", "question", "C5", None),
        (1, "09:12", "何承翰", "text", "公开的，README 里要写清楚复现命令和依赖版本，私有仓库老师打不开。", "answer", "C5", "prev"),
        (1, "09:13", "赵明轩", "text", "好的，那我把商业部分抽成一个 mock 层再公开。", "discussion", "C5", "prev"),
        (1, "09:40", "吴昊天", "link", "https://docs.github.com/zh/get-started/quickstart/hello-world  GitHub 官方入门，比看视频快。", "resource", "C5", None),
        (1, "10:05", "陈心怡", "text", "收到，谢谢！", "social", None, None),
        (1, "14:20", "孙乐", "text", "有人跑过 ollama 吗？我这台 8G 内存的 Air 一加载 gemma 就风扇狂转。", "question", "C4D", None),
        (1, "14:31", "周嘉懿", "text", "别用默认上下文长度，改成 2048 再试，显存和内存占用会小一半。", "answer", "C4D", "prev"),
        (1, "14:33", "孙乐", "text", "改了，确实不卡了，但回答质量下降了不少，感觉上下文不够用。", "discussion", "C4D", "prev"),
        (1, "14:40", "周嘉懿", "text", "那就先摘要再喂给模型，长文档不要整篇塞进去。", "discussion", "C4D", "prev"),
        (1, "15:02", "罗欣然", "text", "我这边课程冲突比较多，可能这周就潜水了。", "social", None, None),
        (1, "19:30", "徐方雨", "text", "C2 的论文选题还没定，有没有人一起讨论下 AI4Math 的可靠性？", "discussion", "C2", None),
        (1, "19:44", "景雪晴", "text", "我 C2 做的是可复核性框架，核心是把「模型自己说对」和「真的对」分开验证。", "discussion", "C2", None),

        # ---------- Day 2 ----------
        (2, "09:15", T, "file", "C8_项目池说明_v2.pdf", "announcement", "C8", None),
        (2, "09:16", "T", "text", "项目池说明已上传，A/B/C 三条线的人数上限写在第 3 页。", "announcement", "C8", None),
        (2, "09:28", "何承翰", "text", "老师，B 线要求会写 SQL 吗？我只会 Python 调库。", "question", "C8", None),
        (2, "09:45", T, "text", "需要一点 SQL，但 agent 会帮你写，你要能看懂并改。", "answer", "C8", "prev"),
        (2, "10:12", "郭雅琪", "file", "郭雅琪_C1_交付物.md", "submission", "C1", None),
        (2, "10:13", "郭雅琪", "file", "郭雅琪_C1_AI日志.md", "submission", "C1", None),
        (2, "10:30", "马嘉乐", "text", "C1 翻译那篇 Stanford 的课，术语表要单独交吗？", "question", "C1", None),
        (2, "10:41", "郭雅琪", "text", "要，术语表附在正文后面，老师说要能对得上原文页码。", "answer", "C1", "prev"),
        (2, "11:02", "马嘉乐", "file", "马嘉乐_C1_交付物.md", "submission", "C1", None),
        (2, "14:00", "彭心语", "text", "公众号封面尺寸到底用 900×383 还是 2.35:1？我 C4B 的模板一直提示尺寸不对。", "question", "C4B", None),
        (2, "14:20", "陈心怡", "text", "我用的是 900×383，微信后台会自动裁切，标题别放最上面。", "answer", "C4B", "prev"),
        (2, "15:30", "唐思涵", "text", "C4B 那个技能能不能直接接公众号后台？我不想每次都手动粘。", "question", "C4B", None),
        (2, "15:52", "景雪晴", "text", "接口申请周期很长，我最后是生成带样式的 HTML，粘贴到编辑器里样式基本不丢。", "answer", "C4B", "prev"),
        (2, "16:10", "唐思涵", "text", "这个思路可以，我试试用内联样式。", "discussion", "C4B", "prev"),
        (2, "20:05", "冯亦然", "text", "有没有人觉得 C3 的「高质量参与」很难量化？我感觉就是让大家多说话。", "discussion", "C3", None),
        (2, "20:18", "林一舟", "text", "我的理解是要有可追溯的贡献，比如你提的问题后来被写进了 FAQ。", "discussion", "C3", None),
        (2, "20:31", "冯亦然", "text", "那我这周的提问算不算？", "question", "C3", None),
        (2, "20:40", "林一舟", "text", "算，但最好带上你自己的尝试，别只问不试。", "answer", "C3", "prev"),

        # ---------- Day 3 ----------
        (3, "09:05", T, "text", "@所有人 提醒：C5 仓库必须在本周五 24:00 前公开，逾期按未提交处理。", "announcement", "C5", None),
        (3, "09:20", "邱志伟", "text", "老师，我的仓库建好了但 push 一直失败，提示权限不足。", "question", "C5", None),
        (3, "09:35", "何承翰", "text", "大概率是 SSH key 没加，或者你用的是 HTTPS 但贴了 token 到密码框。", "answer", "C5", "prev"),
        (3, "09:40", "邱志伟", "text", "确实是 token 过期了，重新生成后推上去了，谢谢！", "social", "C5", "prev"),
        (3, "10:15", "徐方雨", "file", "徐方雨_C2_交付物.pdf", "submission", "C2", None),
        (3, "10:16", "徐方雨", "file", "徐方雨_C2_AI日志.md", "submission", "C2", None),
        (3, "10:50", "邓子龙", "text", "C2 论文的参考文献格式，学校要求 GB/T 7714，但 latex 模板是 APA，怎么改？", "question", "C2", None),
        (3, "11:20", "景雪晴", "text", "换 biblatex 的 gb7714-2015 样式就行，\\usepackage[style=gb7714-2015]{biblatex}。", "answer", "C2", "prev"),
        (3, "11:26", "邓子龙", "text", "编译报错了，说找不到样式文件。", "question", "C2", "prev"),
        (3, "11:40", "景雪晴", "text", "要把 gb7714-2015.bbx 和 .cbx 放进工程目录，或者用 texlive 全量安装。", "answer", "C2", "prev"),
        (3, "13:00", "谢梦琪", "text", "问一下 C6 部署上去之后链接会不会过期？", "question", "C6", None),
        (3, "14:30", "高宇飞", "text", "我 C6 部署的链接放了两周还能打开，应该不会过期，但免费额度有请求限制。", "answer", "C6", "prev"),
        (3, "16:45", "彭心语", "text", "还是没人回答我封面尺寸的问题……我先按 2.35:1 试了。", "discussion", "C4B", None),
        (3, "20:10", "杨海森", "text", "统计口径问一下：C6A 的提交率分母是全班人数还是已报名人数？", "question", "C6A", None),
        (3, "20:35", "景雪晴", "text", "我按全班人数算的，报名人数会让完成率虚高，验收时说不清。", "answer", "C6A", "prev"),
        (3, "20:50", "杨海森", "text", "有道理，那我改成分母写清楚两种口径都出。", "discussion", "C6A", "prev"),

        # ---------- Day 4 ----------
        (4, "08:50", "赵明轩", "file", "赵明轩_C5_交付物.md", "submission", "C5", None),
        (4, "08:51", "赵明轩", "file", "赵明轩_C5_AI日志.md", "submission", "C5", None),
        (4, "09:10", "T", "text", "【提交规范】文件名统一 姓名_挑战ID_内容.md，上周有 4 份文件没写名字，我无法归档。", "announcement", None, None),
        (4, "09:30", "罗欣然", "text", "老师，我文件名写的是「最终版」，现在改还来得及吗？", "question", None, None),
        (4, "09:42", T, "text", "重新发一次，改成规范命名，旧的我不收。", "answer", None, "prev"),
        (4, "10:05", "郭雅琪", "file", "C4A评审器.zip", "submission", "C4A", None),
        (4, "10:20", "T", "text", "郭雅琪这份命名不规范，挑战 ID 有了但没有姓名和内容说明，先记待修。", "announcement", "C4A", None),
        (4, "11:00", "吴昊天", "file", "吴昊天_C4A_交付物.md", "submission", "C4A", None),
        (4, "11:01", "吴昊天", "file", "吴昊天_C4A_AI日志.md", "submission", "C4A", None),
        (4, "11:02", "吴昊天", "file", "吴昊天_C4A_拿来说明.md", "submission", "C4A", None),
        (4, "14:15", "孙乐", "text", "C4D 的 agent 一直复读我的话，是不是温度调太低了？", "question", "C4D", None),
        (4, "14:32", "周嘉懿", "text", "复读一般是 prompt 里没有明确任务，模型只能顺着你说，加一句「你的任务是…」。", "answer", "C4D", "prev"),
        (4, "14:40", "孙乐", "text", "加了之后好多了，谢谢。", "social", "C4D", "prev"),
        (4, "19:00", "唐思涵", "link", "https://developers.weixin.qq.com/doc/offiaccount/Publish/Publish.html 公众号发布接口文档，我看了下要认证服务号。", "resource", "C4B", None),
        (4, "19:20", "彭心语", "text", "个人订阅号是不是就没戏了？", "question", "C4B", None),
        (4, "19:35", "景雪晴", "text", "个人号可以复制粘贴，样式做对就行，接口不用强求。", "answer", "C4B", "prev"),

        # ---------- Day 5 ----------
        (5, "09:00", "何承翰", "file", "何承翰_C5_交付物.md", "submission", "C5", None),
        (5, "09:01", "何承翰", "file", "何承翰_C5_AI日志.md", "submission", "C5", None),
        (5, "09:30", "邱志伟", "text", "C5 的 commit 历史要不要整理？我这有 30 多个 wip commit。", "question", "C5", None),
        (5, "09:50", "林一舟", "text", "不用整理，真实历史反而好，但 README 要能让人看懂你在做什么。", "answer", "C5", "prev"),
        (5, "10:20", "陈心怡", "file", "陈心怡_C6_交付物.md", "submission", "C6", None),
        (5, "10:21", "陈心怡", "file", "陈心怡_C6_AI日志.md", "submission", "C6", None),
        (5, "10:22", "陈心怡", "file", "陈心怡_C6_demo.mp4", "submission", "C6", None),
        (5, "11:00", "T", "text", "@所有人 周五周会改到 19:30，因为教室晚上有考试。", "announcement", None, None),
        (5, "11:05", "马嘉乐", "text", "收到", "social", None, None),
        (5, "11:06", "冯亦然", "text", "收到", "social", None, None),
        (5, "11:07", "邓子龙", "text", "收到", "social", None, None),
        (5, "14:00", "徐方雨", "text", "C7 内容传播的阅读量要截图吗？我发在小红书只有 200 多浏览。", "question", "C7", None),
        (5, "14:25", "T", "text", "要截图，200 也算，重点是你能说清为什么这个选题没人看。", "answer", "C7", "prev"),
        (5, "15:10", "彭心语", "file", "彭心语_C7_交付物.md", "submission", "C7", None),
        (5, "15:11", "彭心语", "file", "彭心语_C7_AI日志.md", "submission", "C7", None),
        (5, "20:00", "高宇飞", "text", "问个偏工程的问题：C6A 的仪表盘数据从哪来？手动导还是自动扫？", "question", "C6A", None),
        (5, "20:20", "景雪晴", "text", "自动扫文件夹最省事，但命名不规范就扫不出来，所以我先做了一层命名检查。", "answer", "C6A", "prev"),
        (5, "20:40", "高宇飞", "text", "那如果消息和文件对不上怎么办？", "question", "C6A", "prev"),
        (5, "20:55", "景雪晴", "text", "以文件为准，消息只用来补时间线，这是我踩过坑之后的结论。", "answer", "C6A", "prev"),

        # ---------- Day 6 ----------
        (6, "09:20", "吴昊天", "file", "吴昊天_C6A_交付物.md", "submission", "C6A", None),
        (6, "09:21", "吴昊天", "file", "吴昊天_C6A_AI日志.md", "submission", "C6A", None),
        (6, "10:00", "孙乐", "file", "孙乐_C4D_交付物.md", "submission", "C4D", None),
        (6, "10:01", "孙乐", "file", "孙乐_C4D_AI日志.md", "submission", "C4D", None),
        (6, "10:30", "T", "text", "【进度】目前 C5 交了 4 人，C6 交了 3 人，落后于计划。请组长今天内对接一下没交的同学。", "announcement", "C5", None),
        (6, "10:45", "何承翰", "text", "我这边对接赵明轩和马嘉乐，晚上反馈。", "discussion", "C5", None),
        (6, "11:00", "冯亦然", "text", "C3C 双人协作必须两个人一起交吗？我一个人能不能算两份？", "question", "C3C", None),
        (6, "11:20", "T", "text", "不行，C3C 考的是协作过程，一个人做两份没有协作痕迹。", "answer", "C3C", "prev"),
        (6, "11:25", "冯亦然", "text", "那我找个人结对。", "social", "C3C", "prev"),
        (6, "14:00", "周嘉懿", "file", "周嘉懿_C4D_交付物.md", "submission", "C4D", None),
        (6, "14:01", "周嘉懿", "text", "我的 AI 日志还没写完，先交交付物，日志明天补。", "discussion", "C4D", None),
        (6, "14:10", "T", "text", "日志也是必交项，缺了按未完成算。", "announcement", "C4D", "prev"),
        (6, "15:30", "杨海森", "text", "C6A 的图表用什么做的？我想做得好看一点但不会前端。", "question", "C6A", None),
        (6, "15:50", "陈心怡", "text", "用现成的图表库直接嵌，别自己画 SVG，费时间还丑。", "answer", "C6A", "prev"),
        (6, "19:30", T, "text", "【周会开始】今天三件事：C8 立项、C5 收尾、下周的提交节奏。", "announcement", None, None),
        (6, "19:52", "林一舟", "text", "我选 B 线，理由是我做过知识图谱的课程作业，但企业数据规模没碰过。", "discussion", "C8", None),
        (6, "20:05", "景雪晴", "text", "我选 B 线的落地部分，但我更想做「谁能用」而不是「技术多新」。", "discussion", "C8", None),
        (6, "20:20", T, "text", "记住 C8 只看结果，不看你想得多漂亮。", "announcement", "C8", None),
        (6, "20:35", "赵明轩", "text", "老师，如果我的项目这周只有文档没有代码，算不算产出？", "question", "C8", None),
        (6, "20:50", T, "text", "算，前提是这份文档别人能拿去用，不是写给自己看的。", "answer", "C8", "prev"),

        # ---------- Day 7 ----------
        (7, "09:10", "郭雅琪", "file", "郭雅琪_C4A评审器_最终版.zip", "submission", "C4A", None),
        (7, "09:25", "T", "text", "郭雅琪这次带了姓名和挑战 ID，但「最终版」这种词不要出现在文件名里，用内容描述。", "announcement", "C4A", None),
        (7, "10:00", "谢梦琪", "text", "C6 部署的域名能不能自定义？我老板觉得默认域名不好看。", "question", "C6", None),
        (7, "10:30", "高宇飞", "text", "免费版一般不能绑自定义域名，可以先忍着。", "answer", "C6", "prev"),
        (7, "11:00", "马嘉乐", "file", "马嘉乐_C2_交付物.pdf", "submission", "C2", None),
        (7, "11:01", "马嘉乐", "file", "马嘉乐_C2_AI日志.md", "submission", "C2", None),
        (7, "14:20", "邓子龙", "file", "邓子龙_C2_交付物.pdf", "submission", "C2", None),
        (7, "14:21", "邓子龙", "file", "邓子龙_C2_AI日志.md", "submission", "C2", None),
        (7, "16:00", "徐方雨", "text", "分享一个坑：论文里的图如果是 matplotlib 出的，DPI 一定设 300，不然印刷糊。", "resource", "C2", None),
        (7, "16:20", "孙乐", "text", "学到了，我一直用默认 100。", "social", "C2", None),
        (7, "19:40", "唐思涵", "file", "唐思涵_C4B_交付物.md", "submission", "C4B", None),
        (7, "19:41", "唐思涵", "file", "唐思涵_C4B_AI日志.md", "submission", "C4B", None),
        (7, "20:00", "彭心语", "text", "C4B 的样式粘到公众号之后段落间距全变了，有人遇到吗？", "question", "C4B", None),
        (7, "20:25", "唐思涵", "text", "微信会吃掉 margin，用 padding 或者空段落顶。", "answer", "C4B", "prev"),
        (7, "20:40", "彭心语", "text", "改用 padding 之后正常了，谢谢！", "social", "C4B", "prev"),

        # ---------- Day 8 ----------
        (8, "09:00", T, "file", "C8_proposal模板.md", "announcement", "C8", None),
        (8, "09:01", "T", "text", "模板已上传，五个部分一个都不能少，早期验证物单独放。", "announcement", "C8", None),
        (8, "09:30", "冯亦然", "text", "早期验证物可以是文档吗？我不太会写代码。", "question", "C8", None),
        (8, "09:45", "T", "text", "可以，技术方案或系统架构图都算，但必须是你自己画的。", "answer", "C8", "prev"),
        (8, "10:20", "邱志伟", "text", "我这两周在准备考证，项目可能要放缓一点。", "social", None, None),
        (8, "11:00", "林一舟", "file", "林一舟_C8_proposal.md", "submission", "C8", None),
        (8, "11:01", "林一舟", "file", "林一舟_C8_AI日志.md", "submission", "C8", None),
        (8, "11:02", "林一舟", "file", "林一舟_C8_拿来说明.md", "submission", "C8", None),
        (8, "11:03", "林一舟", "file", "林一舟_C8_demo.zip", "submission", "C8", None),
        (8, "11:30", "T", "text", "林一舟这份齐全了，四件套都在，可以作为模板参考。", "announcement", "C8", None),
        (8, "14:00", "何承翰", "text", "问一下 C8 的 AAR 是每周都要交吗？还是一共一份？", "question", "C8", None),
        (8, "14:20", "T", "text", "每周一份，命名 AAR_W1、AAR_W2，连续两周不交直接移出项目。", "answer", "C8", "prev"),
        (8, "14:25", "何承翰", "text", "明白了，那我按周建文件夹。", "social", "C8", "prev"),
        (8, "19:00", "景雪晴", "text", "C8 我打算把班级管理这块做成 agent 能调的技能，先跑通数据桥接再往上叠。", "discussion", "C8", None),
        (8, "19:15", "林一舟", "text", "数据桥接是指从微信里把消息捞出来吗？这个不是有封号风险？", "question", "C8", None),
        (8, "19:30", "景雪晴", "text", "只读本地数据库、不登录不群发，风险比爬网页低，但我会把写回做成默认关闭。", "answer", "C8", "prev"),

        # ---------- Day 9 ----------
        (9, "09:05", "郭雅琪", "file", "郭雅琪_C4A_交付物.md", "submission", "C4A", None),
        (9, "09:06", "郭雅琪", "file", "郭雅琪_C4A_AI日志.md", "submission", "C4A", None),
        (9, "10:00", "孙乐", "text", "C9 自驱项目大家打算做什么？我完全没有想法。", "question", "C9", None),
        (9, "10:25", "周嘉懿", "text", "从你已经在做的工具里挑一个继续打磨，比新开一个坑靠谱。", "answer", "C9", "prev"),
        (9, "11:00", "陈心怡", "file", "陈心怡_C7_交付物.md", "submission", "C7", None),
        (9, "11:01", "陈心怡", "file", "陈心怡_C7_AI日志.md", "submission", "C7", None),
        (9, "14:00", "杨海森", "text", "C10 第二大脑那个，记忆到底存在哪？本地文件还是向量库？", "question", "C10", None),
        (9, "14:30", "吴昊天", "text", "小规模本地 markdown 就够，上千条再上向量库，别一上来就搞复杂。", "answer", "C10", "prev"),
        (9, "16:20", "T", "text", "【预警】以下同学本周零发言：罗欣然、谢梦琪、杨海森。请主动联系我说明情况。", "announcement", None, None),
        (9, "19:30", "马嘉乐", "file", "马嘉乐_C4A_交付物.md", "submission", "C4A", None),
        (9, "19:31", "马嘉乐", "file", "马嘉乐_C4A_AI日志.md", "submission", "C4A", None),
        (9, "20:00", "徐方雨", "text", "C7 我发了三篇，只有一篇破千，另外两篇几乎没人看，问题应该出在标题。", "discussion", "C7", None),
        (9, "20:15", "彭心语", "text", "标题里带具体数字和场景的打开率高很多，我自己测是这样。", "discussion", "C7", None),

        # ---------- Day 10 ----------
        (10, "09:20", "T", "text", "【提交提醒】C5 已收 8 份，还差 12 位同学，今晚 24:00 截止。", "announcement", "C5", None),
        (10, "09:40", "邓子龙", "file", "邓子龙_C5_交付物.md", "submission", "C5", None),
        (10, "09:41", "邓子龙", "file", "邓子龙_C5_AI日志.md", "submission", "C5", None),
        (10, "10:00", "冯亦然", "file", "冯亦然_C3_交付物.md", "submission", "C3", None),
        (10, "10:01", "冯亦然", "file", "冯亦然_C3_AI日志.md", "submission", "C3", None),
        (10, "10:30", "彭心语", "text", "C3 的参与记录怎么证明？光靠自己说不太好吧。", "question", "C3", None),
        (10, "10:50", "冯亦然", "text", "导一份群聊记录，把你发言的时间点标出来，老师能核对。", "answer", "C3", "prev"),
        (10, "11:20", "高宇飞", "file", "高宇飞_C6A_交付物.md", "submission", "C6A", None),
        (10, "11:21", "高宇飞", "file", "高宇飞_C6A_AI日志.md", "submission", "C6A", None),
        (10, "14:00", "唐思涵", "text", "C10H 的 Hermes 装不上，卡在依赖冲突，有人成功过吗？", "question", "C10H", None),
        (10, "15:30", "孙乐", "text", "我用虚拟环境装的，系统 Python 千万别动。", "answer", "C10H", "prev"),
        (10, "19:00", "何承翰", "file", "何承翰_C8_proposal.md", "submission", "C8", None),
        (10, "19:01", "何承翰", "file", "何承翰_C8_AI日志.md", "submission", "C8", None),
        (10, "19:02", "何承翰", "text", "拿来说明和 demo 明天补，先占个位置。", "discussion", "C8", None),
        (10, "19:10", "T", "text", "占位不算提交，四件套齐了才算。", "announcement", "C8", "prev"),

        # ---------- Day 11 ----------
        (11, "09:00", "吴昊天", "file", "吴昊天_C8_proposal.md", "submission", "C8", None),
        (11, "09:01", "吴昊天", "file", "吴昊天_C8_AI日志.md", "submission", "C8", None),
        (11, "09:02", "吴昊天", "file", "吴昊天_C8_拿来说明.md", "submission", "C8", None),
        (11, "09:03", "吴昊天", "file", "吴昊天_C8_demo.py", "submission", "C8", None),
        (11, "10:00", "赵明轩", "file", "赵明轩_C8_proposal.md", "submission", "C8", None),
        (11, "10:01", "赵明轩", "file", "赵明轩_C8_AI日志.md", "submission", "C8", None),
        (11, "10:30", "杨海森", "text", "我下周开始补交，这周家里有事，先说明一下。", "social", None, None),
        (11, "11:00", "T", "text", "可以，但要在群里留痕，别消失。", "answer", None, "prev"),
        (11, "14:20", "陈心怡", "text", "C8 的 demo 我用视频可以吗？代码实在跑不起来。", "question", "C8", None),
        (11, "14:45", "T", "text", "视频可以是补充，不能替代，至少要有能运行的东西。", "answer", "C8", "prev"),
        (11, "19:30", "景雪晴", "file", "景雪晴_C8_proposal.md", "submission", "C8", None),
        (11, "19:31", "景雪晴", "file", "景雪晴_C8_AI日志.md", "submission", "C8", None),
        (11, "19:32", "景雪晴", "file", "景雪晴_C8_拿来说明.md", "submission", "C8", None),
        (11, "19:33", "景雪晴", "file", "景雪晴_C8_demo.mp4", "submission", "C8", None),
        (11, "20:00", "T", "text", "景雪晴这份四件套齐了，但 demo 是视频，下周要补一个能跑的版本。", "announcement", "C8", None),
        (11, "20:15", "景雪晴", "text", "收到，已经在做了，下周给可运行版本。", "social", "C8", "prev"),

        # ---------- Day 12 ----------
        (12, "09:10", "徐方雨", "file", "徐方雨_C7_交付物.md", "submission", "C7", None),
        (12, "09:11", "徐方雨", "file", "徐方雨_C7_AI日志.md", "submission", "C7", None),
        (12, "10:00", "T", "text", "【周会】今晚 19:30，议题：C8 中期检查、C9 选题、C10 记忆方案。", "announcement", None, None),
        (12, "10:30", "孙乐", "text", "C10 的记忆如果只存本地，换电脑就没了，这个怎么解决？", "question", "C10", None),
        (12, "10:55", "周嘉懿", "text", "放 git 私有仓库，或者定时导出加密包，两种都行。", "answer", "C10", "prev"),
        (12, "11:20", "林一舟", "file", "林一舟_C5_交付物.md", "submission", "C5", None),
        (12, "11:21", "林一舟", "file", "林一舟_C5_AI日志.md", "submission", "C5", None),
        (12, "14:00", "马嘉乐", "text", "C8 中期检查要准备什么？PPT 还是文档？", "question", "C8", None),
        (12, "14:20", "T", "text", "文档优先，能当场演示的加演示，PPT 不是必须。", "answer", "C8", "prev"),
        (12, "19:30", T, "text", "【中期检查开始】按学号顺序，每人 3 分钟，讲清楚做了什么、卡在哪。", "announcement", "C8", None),
        (12, "19:40", "何承翰", "text", "我卡在数据清洗，字段对不上，已经在写映射表了。", "discussion", "C8", None),
        (12, "19:50", "景雪晴", "text", "我的桥接层跑通了，但真实微信库是加密的，这条得写进局限里。", "discussion", "C8", None),
        (12, "20:05", "T", "text", "能诚实写局限，比假装跑通要好，这是加分项。", "announcement", "C8", None),
        (12, "20:20", "林一舟", "text", "我的图数据库导入两万条就卡，可能要换方案。", "discussion", "C8", None),

        # ---------- Day 13 ----------
        (13, "09:00", "T", "text", "@所有人 下周开始每周五交 AAR，格式在群文件里，别自己编格式。", "announcement", "C8", None),
        (13, "09:30", "郭雅琪", "text", "AAR 里要写失败经验吗？我怕写得难看。", "question", "C8", None),
        (13, "09:50", "T", "text", "必须写，没有失败分析的 AAR 我打回去重写。", "answer", "C8", "prev"),
        (13, "10:20", "彭心语", "file", "彭心语_C8_proposal.md", "submission", "C8", None),
        (13, "10:21", "彭心语", "file", "彭心语_C8_AI日志.md", "submission", "C8", None),
        (13, "10:22", "彭心语", "file", "彭心语_C8_拿来说明.md", "submission", "C8", None),
        (13, "11:00", "邓子龙", "text", "C8 demo 我用 notebook 可以吗？不太会打包。", "question", "C8", None),
        (13, "11:20", "吴昊天", "text", "可以，但要有 README 说明怎么跑，装什么依赖。", "answer", "C8", "prev"),
        (13, "14:00", "冯亦然", "file", "冯亦然_C8_proposal.md", "submission", "C8", None),
        (13, "14:01", "冯亦然", "file", "冯亦然_C8_AI日志.md", "submission", "C8", None),
        (13, "14:02", "冯亦然", "text", "我的 demo 是个文档，不知道算不算。", "discussion", "C8", None),
        (13, "14:20", "T", "text", "算，架构图画清楚就行。", "answer", "C8", "prev"),
        (13, "19:40", "唐思涵", "text", "问一下大家，C10 的上下文超了怎么办？我只能塞 8k。", "question", "C10", None),
        (13, "20:00", "景雪晴", "text", "分层摘要，把旧对话压成一段事实清单，只保留结论不保留过程。", "answer", "C10", "prev"),

        # ---------- Day 14 ----------
        (14, "09:00", "T", "text", "【本周总结】C8 收到 9 份 proposal，四件套齐全的只有 5 份。C5 全部收齐。", "announcement", "C8", None),
        (14, "09:20", "孙乐", "file", "孙乐_C6A_交付物.md", "submission", "C6A", None),
        (14, "09:21", "孙乐", "file", "孙乐_C6A_AI日志.md", "submission", "C6A", None),
        (14, "10:00", "邱志伟", "text", "我下周开始补，这周确实没怎么动。", "social", None, None),
        (14, "10:30", "何承翰", "file", "何承翰_C8_拿来说明.md", "submission", "C8", None),
        (14, "10:31", "何承翰", "file", "何承翰_C8_demo.zip", "submission", "C8", None),
        (14, "11:00", "何承翰", "text", "补完了，四件套齐了。", "discussion", "C8", None),
        (14, "14:00", "T", "text", "下周主题：把 demo 变成别人能接手的东西，这比功能多更重要。", "announcement", None, None),
        (14, "14:30", "杨海森", "text", "接手这件事我深有体会，我上周看别人代码看了一下午才明白。", "discussion", None, None),
        (14, "19:30", "周嘉懿", "file", "周嘉懿_C4D_AI日志.md", "submission", "C4D", None),
        (14, "19:31", "周嘉懿", "text", "日志补上了。", "social", "C4D", None),
        (14, "20:00", "陈心怡", "text", "问个收尾问题：周报里要不要写下周计划？", "question", "C6A", None),
        (14, "20:20", "景雪晴", "text", "要，而且下周计划要能被检验，写「继续优化」等于没写。", "answer", "C6A", "prev"),
        (14, "20:40", "陈心怡", "text", "懂了，我改成具体动作。", "social", "C6A", "prev"),
    ]


# 闲聊/接龙填充：让活跃度分布更像真实群，而不是只有任务消息
FILLER = [
    ("收到", "social", None),
    ("好的，谢谢老师", "social", None),
    ("我这边也遇到了同样的问题", "discussion", None),
    ("这个思路好，我抄作业了", "social", None),
    ("明天我试试", "social", None),
    ("刚跑通，确实是这样", "discussion", None),
    ("有同学一起结对吗？", "question", "C3C"),
    ("我先睡了，明早看消息", "social", None),
    ("这个坑我踩过，文档里没写", "discussion", None),
    ("已提交，麻烦老师查收", "social", None),
    ("emmm 我再想想", "social", None),
    ("这个方案成本有点高吧", "discussion", None),
    ("有没有更简单的做法？", "question", None),
    ("截图我发群里了", "resource", None),
    ("今天的会我迟到五分钟", "social", None),
]


def _build() -> tuple[list[dict], list[dict]]:
    rng = random.Random(20261104)
    base = START
    raw: list[dict] = []
    labels: list[dict] = []
    prev_id: dict[str, str] = {}
    seq = 0
    last_by_sender: dict[str, str] = {}

    def emit(day: int, hhmm: str, sender: str, kind: str, content: str, intent: str, challenge: str | None, reply_back):
        nonlocal seq
        seq += 1
        hh, mm = hhmm.split(":")
        ts = base + timedelta(days=day - 1, hours=int(hh) - 8, minutes=int(mm) - 30)
        ts += timedelta(seconds=rng.randint(0, 50))
        msg_id = f"m{seq:05d}"
        sender_id = "wxid_teacher_neolaf" if sender == T else _wxid_of(sender)
        record = {
            "seq": seq,
            "msgId": msg_id,
            "time": ts.strftime("%Y-%m-%d %H:%M:%S"),
            "talker": GROUP_ID,
            "talkerName": GROUP_NAME,
            "sender": sender_id,
            "senderName": TEACHER if sender == T else sender,
            "type": 1,
            "content": content,
        }
        if kind == "file":
            record["type"] = 49
            record["content"] = content
            record["contents"] = {"type": 6, "title": content, "size": f"{rng.randint(80, 900)}KB"}
        elif kind == "link":
            record["type"] = 49
            record["contents"] = {"type": 5, "title": content.split(" ")[0], "url": content.split(" ")[0]}
            record["content"] = content
        elif kind == "image":
            record["type"] = 3
            record["content"] = "[图片]"
        if reply_back is not None:
            target = None
            if reply_back == "prev":
                target = prev_id.get("global")
            elif isinstance(reply_back, int):
                target_seq = max(1, seq - 1 - reply_back)
                target = f"m{target_seq:05d}"
            if target:
                record["reply_to"] = target
        raw.append(record)
        labels.append(
            {
                "msg_id": msg_id,
                "intent": intent,
                "challenge": challenge,
                "sender": sender_id,
                "nickname": TEACHER if sender == T else sender,
            }
        )
        prev_id["global"] = msg_id
        last_by_sender[sender] = msg_id

    for day, hhmm, sender, kind, content, intent, challenge, reply_back in turns():
        emit(day, hhmm, sender, kind, content, intent, challenge, reply_back)

    # 填充：多人接龙 + 零散闲聊，穿插在已有时间线上
    # 罗欣然 / 谢梦琪 是刻意设置的"沉默学生"样例，不安排闲聊
    openers = ["林一舟", "赵明轩", "陈心怡", "吴昊天", "孙乐", "周嘉懿", "徐方雨", "何承翰",
               "郭雅琪", "马嘉乐", "高宇飞", "唐思涵", "邓子龙", "冯亦然", "彭心语",
               "邱志伟", "杨海森", "景雪晴"]
    for i in range(46):
        day = 1 + (i * 13) // 46
        hh = 9 + (i * 7) % 11
        mm = (i * 17) % 60
        sender = openers[i % len(openers)]
        text, intent, challenge = FILLER[i % len(FILLER)]
        emit(day, f"{hh:02d}:{mm:02d}", sender, "text", text, intent, challenge, None)

    raw.sort(key=lambda r: (r["time"], r["msgId"]))
    order = {r["msgId"]: i for i, r in enumerate(raw)}
    labels.sort(key=lambda l: order[l["msg_id"]])
    return raw, labels


_NAMES: dict[str, str] = {}


def _wxid_of(nickname: str) -> str:
    if not _NAMES:
        from wcm.config import load_config

        for st in load_config().roster.students.values():
            _NAMES[st.nickname] = st.wxid
    return _NAMES.get(nickname, "wxid_" + str(abs(hash(nickname)) % 10**8))


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    raw, labels = _build()
    raw_path = os.path.join(OUT_DIR, "messages_raw.jsonl")
    label_path = os.path.join(OUT_DIR, "labels.jsonl")
    with open(raw_path, "w", encoding="utf-8") as fh:
        for r in raw:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(label_path, "w", encoding="utf-8") as fh:
        for l in labels:
            fh.write(json.dumps(l, ensure_ascii=False) + "\n")
    dist: dict[str, int] = {}
    for l in labels:
        dist[l["intent"]] = dist.get(l["intent"], 0) + 1
    meta = {
        "messages": len(raw),
        "labels": len(labels),
        "days": DAYS,
        "start": raw[0]["time"] if raw else None,
        "end": raw[-1]["time"] if raw else None,
        "intent_distribution": dict(sorted(dist.items(), key=lambda kv: -kv[1])),
        "group": GROUP_NAME,
        "note": "合成脱敏数据集：人名除景雪晴外均为合成，消息内容为课程真实场景手写，用于复现与验收。",
    }
    with open(os.path.join(OUT_DIR, "dataset_meta.json"), "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
