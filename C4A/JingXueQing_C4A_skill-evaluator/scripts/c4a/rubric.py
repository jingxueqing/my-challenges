"""评审标准定义 —— C4 四条件 → 可计算信号。

这里是"元能力"的核心资产：把模糊的评审标准变成确定性的检查项。
每条 CHECK 都是 (id, 维度, 检查项, 正向信号, 负向信号, 阈值, 建议模板)。

改这个文件就能调整评审口径，无需改引擎代码——标准与实现分离。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# 评分档位权重
LEVEL_SCORE = {"✅": 1.0, "⚠️": 0.5, "❌": 0.0}
# 维度权重（可在 CLI 用 --weights 覆盖）
DEFAULT_WEIGHTS = {
    "reusable": 0.25,
    "executable": 0.30,
    "verifiable": 0.20,
    "clear_io": 0.25,
}

CRITERIA_META = {
    "reusable": {"label": "可复用", "en": "Reusable",
                 "desc": "别人拿过去能直接用，不依赖作者特定环境"},
    "executable": {"label": "可执行", "en": "Executable",
                   "desc": "不是理论，是能跑的东西"},
    "verifiable": {"label": "可验证", "en": "Verifiable",
                   "desc": "有明确输入输出，能判断成功与否"},
    "clear_io": {"label": "IO 明确", "en": "Clear I/O",
                 "desc": "输入什么、输出什么，一目了然"},
}

# --------------------------------------------------------------------------
# 完整性检查：5 个必须文件
# 每一项包含文件名信号 与 内容信号 两类证据；文件名信号权重更高
# （作者主动按规范命名，是强信号；内容命中可能是巧合）
# --------------------------------------------------------------------------

COMPLETENESS_SPEC = {
    "skill_doc": {
        "label": "Skill 说明文档",
        "filename_signals": [
            (r"skill[-_ ]?说明", 1.0), (r"skill[-_ ]?doc", 1.0),
            (r"skill[-_ ]?description", 1.0), (r"技能说明", 1.0),
            (r"SKILL\.md$", 0.9),
        ],
        "content_signals": [
            (r"解决什么问题|使用场景|适用场景|use\s*case", 0.7),
            (r"输入|input", 0.5), (r"输出|output", 0.5),
        ],
        "extensions": [".md", ".pdf", ".docx", ".txt"],
    },
    "executable": {
        "label": "可执行内容",
        "filename_signals": [
            (r"\.skill$", 1.0), (r"\.(py|sh|js|ts)$", 0.9),
            (r"技能|skill(?![-_ ]?(说明|doc))", 0.6),
        ],
        "content_signals": [
            (r"^---\s*\nname:", 1.0),          # YAML frontmatter
            (r"```(python|bash|sh|javascript|js)", 0.9),
            (r"^\s*(def |class |import |function )", 0.8),
            (r"\b(pip install|npm install|python3?\s+\S+\.py)\b", 0.6),
        ],
        "extensions": [".skill", ".py", ".md", ".zip", ".sh", ".html", ".ipynb"],
    },
    "demo": {
        "label": "Demo（视频/截图）",
        "filename_signals": [
            (r"demo", 1.0), (r"演示", 1.0), (r"截图", 0.9),
            (r"录屏|screen\s?rec", 0.9), (r"screenshot", 0.9),
        ],
        "content_signals": [
            (r"!\[.*\]\(.*\.(png|jpg|jpeg|gif)", 0.7),  # md 内嵌截图
            (r"<video|\.mp4|\.mov", 0.5),
        ],
        "extensions": [".mp4", ".mov", ".webm", ".png", ".jpg", ".jpeg", ".gif", ".html"],
    },
    "teaching_doc": {
        "label": "教学说明",
        "filename_signals": [
            (r"教学说明", 1.0), (r"教学", 0.9), (r"tutorial", 1.0),
            (r"teaching", 1.0), (r"上手指南|quick\s?start|how[-_ ]?to", 0.9),
        ],
        "content_signals": [
            (r"常见坑|注意事项|避坑", 0.8), (r"上手|快速开始|getting\s+started", 0.7),
            (r"^\s*\d+[\.、]\s+\S+", 0.5),          # 编号步骤
        ],
        "extensions": [".md", ".pdf", ".docx", ".txt"],
    },
    "ai_log": {
        "label": "AI 日志",
        "filename_signals": [
            (r"AI\s*[-_]?日志", 1.0), (r"AI\s*[-_]?log", 1.0),
            (r"ai[-_]?log", 1.0), (r"使用记录", 0.7),
        ],
        "content_signals": [
            (r"迭代\s*\d*\s*(轮|次)|第\s*\d+\s*轮", 0.9),
            (r"使用的\s*AI|AI\s*工具|ChatGPT|Claude|DeepSeek|Cursor", 0.8),
            (r"prompt|提示词", 0.6),
        ],
        "extensions": [".md", ".pdf", ".docx", ".txt"],
    },
}

COMPLETENESS_ORDER = ["skill_doc", "executable", "demo", "teaching_doc", "ai_log"]


# --------------------------------------------------------------------------
# 质量检查：四条件 × 检查项
# strong= 达到几条判✅ ；weak = 达到几条判 ⚠️
# --------------------------------------------------------------------------

@dataclass
class Check:
    id: str
    criterion: str
    label: str
    positive: list[tuple[str, float]]      # (regex, weight)
    negative: list[tuple[str, float]] = field(default_factory=list)
    strong: int = 2
    weak: int = 1
    advice: str = ""
    # 该检查项"不适用"时是否仍算失败（例如没有代码时，语法检查应N/A）
    optional: bool = False
    # True = 纯负向检查项：成功形态是"什么都没找到"（如"无硬编码路径"）
    absence_is_pass: bool = False
    # True = 命中负向信号时反证（例如"待补充"出现在模板/示例里应被忽略）
    negatives_are_reports: bool = False


# 只有负向信号、且"零命中"即为通过的检查项
NEGATIVE_ONLY = {"REUSE.nopath", "REUSE.nosecret", "EXEC.notemplate"}

QUALITY_CHECKS: list[Check] = [
    # ---------------- 可复用 ----------------
    Check(
        id="REUSE.install", criterion="reusable", label="有安装/放置说明",
        positive=[(r"安装|install|部署到|放到\s*[~~/]|解压", 1.0),
                  (r"pip\s+install|npm\s+install|apt\s+install", 1.2),
                  (r"##\s*安装|###\s*安装|Installation", 1.2)],
        strong=1, weak=1,
        advice="补一节「安装」，写清 `pip install -r requirements.txt` / 拷贝到哪个目录 / 如何验证装上了",
    ),
    Check(
        id="REUSE.env", criterion="reusable", label="声明环境依赖",
        positive=[(r"环境要求|依赖|requirements|dependencies|prerequisite", 1.0),
                  (r"python\s*3\.\d+|node\s*v?\d+|版本要求", 1.1),
                  (r"pip\s+install|import\s+\w+", 0.6)],
        strong=2, weak=1,
        advice="列出 Python/Node 版本与第三方依赖，最好附 requirements.txt",
    ),
    Check(
        id="REUSE.nopath", criterion="reusable", label="无硬编码本地绝对路径",
        positive=[],   # 这一项靠 negative 信号判定
        negative=[(r"/Users/[A-Za-z0-9_.\-]+", 1.4),
                  (r"/home/[A-Za-z0-9_.\-]+", 1.2),
                  (r"[A-Z]:\\\\?Users\\\\?", 1.2),
                  (r"我的电脑|my\s*(machine|pc|laptop)|本机路径", 0.9)],
        strong=1, weak=1,
        advice="把 /Users/xxx 这类绝对路径改成相对路径或 `~/`，否则换台机器就跑不了",
    ),
    Check(
        id="REUSE.nosecret", criterion="reusable", label="无硬编码密钥",
        positive=[],
        negative=[(r"api[_-]?key\s*=\s*[\"'][A-Za-z0-9_\-]{12,}", 1.6),
                  (r"secret\s*=\s*[\"'][A-Za-z0-9_\-]{12,}", 1.4),
                  (r"sk-[A-Za-z0-9]{20,}", 1.6),
                  (r"Bearer\s+[A-Za-z0-9_\-\.]{20,}", 1.2)],
        strong=1, weak=1,
        advice="密钥改成从环境变量读取，并说明 `.env` 配置方式",
    ),
    Check(
        id="REUSE.general", criterion="reusable", label="有泛化/适用边界说明",
        positive=[(r"适用(范围|场景)|边界|不适用|limitation|适用于", 1.0),
                  (r"只要.{0,20}就(可以|能)|任何.{0,15}都可以", 0.9),
                  (r"兼容性|平台|macOS|Windows|Linux", 0.7)],
        strong=1, weak=1,
        advice="补「适用范围与不适用场景」，让使用者知道边界在哪",
    ),

    # ---------------- 可执行 ----------------
    Check(
        id="EXEC.code", criterion="executable", label="含可运行的代码/prompt/workflow",
        positive=[(r"```(python|bash|sh|javascript|js|json)\b", 1.0),
                  (r"^\s*(def |class )\s+\w+", 1.2),
                  (r"^\s*import \w+|^\s*from \w+ import", 0.9),
                  (r"python3?\s+\S+\.py|bash\s+\S+\.sh", 1.1),
                  (r"^\s*#{1,4}\s*(workflow|工作流|流程|步骤)\d*", 0.8)],
        strong=2, weak=1,
        advice="把方法落成可复制运行的代码块或明确的 workflow 步骤，别只描述",
    ),
    Check(
        id="EXEC.frontmatter", criterion="executable", label="SKILL.md 有 YAML frontmatter",
        positive=[(r"^---\s*\nname:\s*\S+", 1.5),
                  (r"^description:\s*\S+", 0.8)],
        strong=1, weak=1,
        advice="SKILL.md 开头加 `---\\nname: xxx\\ndescription: xxx\\n---`，否则无法被自动触发",
    ),
    Check(
        id="EXEC.runnable", criterion="executable", label="有明确运行命令",
        positive=[(r"python3?\s+[\w./\-]+\.py", 1.2),
                  (r"bash\s+[\w./\-]+\.sh|sh\s+[\w./\-]+\.sh", 1.2),
                  (r"```(bash|sh|shell)", 0.9),
                  (r"运行方式|执行命令|how\s+to\s+run|运行：", 0.8)],
        strong=2, weak=1,
        advice="给出「保存为 xxx.py 后执行 `python3 xxx.py <输入>`」这样的完整命令行",
    ),
    Check(
        id="EXEC.notemplate", criterion="executable", label="不是空壳/占位模板",
        positive=[],
        negative=[(r"TODO|待补充|待完善|填写此处|your\s+api\s+key\s+here|xxx填写", 1.3),
                  (r"<\s*你的\s*[^>]{0,20}\s*>|\{\{\s*\w+\s*\}\}", 0.7)],
        strong=1, weak=1,
        negatives_are_reports=True,
        advice="交付物里不能留 TODO/占位符——那说明还没做完",
    ),

    # ---------------- 可验证 ----------------
    Check(
        id="VERI.example", criterion="verifiable", label="有示例/测试用例",
        positive=[(r"示例|样例|例子|example", 0.9),
                  (r"测试用例|test\s*case|单元测试|pytest|unittest", 1.2),
                  (r"```\s*\n?(输入|input)[:：]", 1.1),
                  (r"案例|case\s*\d|demo", 0.7)],
        strong=2, weak=1,
        advice="补一段真实跑通的示例：给什么输入、跑出什么结果",
    ),
    Check(
        id="VERI.expected", criterion="verifiable", label="定义了预期结果/成功判据",
        positive=[(r"预期(结果|输出|效果)|期望(结果|输出)|expected", 1.3),
                  (r"应当(出现|输出|生成)|应该(出现|输出|生成)", 1.1),
                  (r"验收(标准|条件)|成功(判据|标准)|pass\s*criteria", 1.2),
                  (r"输出应|结果应", 0.9)],
        strong=2, weak=1,
        advice="明确写出「预期输出是什么」，否则使用者在不知道自己有没有做对",
    ),
    Check(
        id="VERI.demo", criterion="verifiable", label="有可看的运行证据（截图/录屏）",
        positive=[(r"!\[[^\]]*\]\([^)]*\.(png|jpg|jpeg|gif|webp)", 1.3),
                  (r"截图|screen\s?shot|录屏|运行实录|终端实录", 1.1),
                  (r"\.mp4|\.mov|\.webm", 0.9)],
        strong=1, weak=1,
        advice="贴一张真实运行截图（脱敏），比任何文字描述都有说服力",
    ),
    Check(
        id="VERI.reproduce", criterion="verifiable", label="步骤可复现（含具体数值/参数）",
        positive=[(r"\d+\s*(行|条|个|次|秒|分钟|token|字)", 0.7),
                  (r"步骤\s*\d|第\s*\d+\s*步|Step\s*\d", 0.8),
                  (r"--\w+|\bargparse\b|命令行参数", 0.6)],
        strong=3, weak=2,
        advice="把关键参数写成具体数值（处理了 42 行 / 耗时 3.2s），让人能照着复现",
    ),

    # ---------------- IO 明确 ----------------
    Check(
        id="IO.pair", criterion="clear_io", label="存在「输入…，输出…」成对描述",
        positive=[(r"输入[：: ].{0,60}输出[：: ]", 1.5),
                  (r"\*\*输入\*\*|\*\*输出\*\*", 1.3),
                  (r"input[\s:：*]{1,4}.{0,60}output[\s:：*]{1,4}", 1.2),
                  (r"接受[：: ].{0,50}(返回|输出)", 1.1),
                  (r"给定[^\n。]{0,40}(得到|生成|返回)", 1.1)],
        strong=1, weak=1,
        advice="在说明文档顶部加一行「**输入**：xxx  →  **输出**：xxx」，这是四条件里最容易检查也最容易丢分的一条",
    ),
    Check(
        id="IO.typed", criterion="clear_io", label="输入输出有类型/格式说明",
        positive=[(r"\.(md|txt|json|csv|xlsx|pdf|docx|mp4|png|jpg|py)\b", 0.8),
                  (r"字符串|路径|文件夹|URL|数组|JSON|列表|字典", 0.9),
                  (r"格式[：: ]|类型[：: ]|schema", 0.9)],
        strong=2, weak=1,
        advice="给输入输出标上具体类型（本地文件夹路径 / .md 文本 / JSON 对象）",
    ),
    Check(
        id="IO.oneline", criterion="clear_io", label="有一句话功能摘要",
        positive=[(r"一句话|一句话说明|one[- ]?liner|简介|概述|功能", 0.9),
                  (r"这个(技能|工具|脚本)(是|用来|能)", 0.9),
                  (r"##\s*(概述|简介|功能|用途)", 0.8)],
        strong=1, weak=1,
        advice="文档开头写一句「本技能用于 ……」，读者 10 秒内要能判断要不要用",
    ),
]

CHECKS_BY_CRITERION: dict[str, list[Check]] = {}
for _c in QUALITY_CHECKS:
    _c.absence_is_pass = _c.id in NEGATIVE_ONLY
    CHECKS_BY_CRITERION.setdefault(_c.criterion, []).append(_c)


def rules_version() -> str:
    return "c4a-rubric-v1.1"
