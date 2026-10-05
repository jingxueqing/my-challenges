"""c4a.skill_evaluator — C4 技能提交自动评审器

设计原则（详见 方案设计.md）：
1. 零硬依赖：仅用Python 标准库，任何装了 Python 3.8+ 的机器都能跑。
2. 证据优先：每条判定都必须能指回"哪个文件第几行命中了什么信号"，
   否则不予采信。没有证据的判定在报告里会被标成低置信度。
3. 分层：Level1 采集 / Level2 完整性 / Level3 质量 / Level4 报告，
   每层可单独调用、可单独测试。
"""

__version__ = "1.0.0"
__all__ = ["collect", "completeness", "quality", "report", "extract", "rubric"]
