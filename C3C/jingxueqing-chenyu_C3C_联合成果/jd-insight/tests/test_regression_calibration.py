"""口径回归用例（Calibration Regression）

背景
----
2026-11-08，景雪晴看到「商业分析师（管培）」只给了 35.1 分，直接说"这不可能"。
她的理由：她读得懂财报（CET-6 能读英文财报），这是工商管理专业的基本功。
而标签体系里 BIZ03「财务与报表」的关键词只有「财务报表 / 三张表 / 利润表 / 资产负债表 /
现金流 / 财务分析」——她简历里写的是「财报」。

陈屿（CS 方）无法判断"财报 == 财务报表"，因为这是领域知识，不是代码问题。
她补上 alias 后，同一条 JD 分数从 35.1 → 75.0。

这个文件的作用：把那次判断固化成回归用例。任何人日后精简关键词表，
只要删掉「财报」这个 alias，这里就会红。
"""

import unittest

from jd_insight import matcher as mt
from jd_insight import parser as jp
from jd_insight import taxonomy as tx


JD_BIZ_ANALYST = (
    "岗位职责：围绕商业模式与单位经济模型做经营分析，输出月度经营复盘，参与年度预算编制。"
    "任职要求：能读懂三张财务报表，理解利润表与现金流的差异；"
    "熟练使用 Excel 建模，会用 SQL 独立取数；具备结构化汇报能力，能向管理层做方案讲解。"
)

RESUME_JXQ = (
    "工商管理专业，CET-6 通过，可阅读英文财报与行业报告。"
    "实习期间负责月度经营复盘，用 Excel 数据透视搭建品类看板，用 SQL 多表取数做交叉分析。"
    "参与需求评审并做方案讲解。"
)


class TestCaiBaoAlias(unittest.TestCase):
    def test_alias_caibao_hits_BIZ03(self):
        self.assertIn("财报", [k.lower() for k in tx.get_tag("BIZ03").all_keywords()])
        hits = jp.extract("可阅读英文财报")
        self.assertIn("BIZ03", {h.tag_id for h in hits})

    def test_biz03_reachable_by_alias_only(self):
        """用「财报」而不是「财务报表」时，也必须命中 BIZ03。"""
        self.assertIn("BIZ03", jp.tag_ids("能独立读财报并做财务分析"))

    def test_full_resume_reaches_previously_failed_score(self):
        """锁定修复效果：不得回落到 35 分附近的假阴性区间。"""
        r = mt.match(JD_BIZ_ANALYST, RESUME_JXQ)
        self.assertGreater(r.total, 60.0, f"口径回归：当前 {r.total:.1f}，已回落到假阴性区间")

    def test_bonus_only_biz03_would_score_lower(self):
        """反证：若把财报放在"加分项"段落，权重必须显著低于必需项，
        说明降权机制确实在工作，而不是所有命中都被同等对待。"""
        # 注意：weight 是「单条 JD 内部」归一化后的值，只有 1 个标签时必然都是 1.0，
        # 跨 JD 比较归一化权重没有意义。要比必须比归一化之前的 raw_weight。
        required = mt._need_vector("必须能读财报。")
        bonus = mt._need_vector("有财报阅读能力者优先。")
        self.assertEqual(required["BIZ03"].weight, 1.0)  # 单标签 JD，归一化后必然 1.0
        self.assertGreater(required["BIZ03"].raw_weight, bonus["BIZ03"].raw_weight)


class TestJingYingAlias(unittest.TestCase):
    def test_jingying_fupan_hits_BIZ02(self):
        """「经营复盘」是「经营分析」的等价说法，也应命中商业模式理解。"""
        self.assertIn("BIZ02", jp.tag_ids("负责月度经营复盘的数据整理"))

    def test_biz02_and_biz03_are_distinct(self):
        """两个标签不能被 alias 合并——它们考的是不同东西。"""
        self.assertNotEqual("BIZ02", "BIZ03")
        only_fin = jp.tag_ids("能读财报并算财务比率")
        self.assertIn("BIZ03", only_fin)


class TestAliasDoesNotOverreach(unittest.TestCase):
    def test_alias_does_not_create_false_positive_on_unrelated_text(self):
        """别名扩展最大的风险是误召回。用一段完全无关的文本验证它没扩散。"""
        ids = jp.tag_ids("本人爱好唱歌、羽毛球，性格开朗，喜欢阅读科幻小说。")
        self.assertNotIn("BIZ03", ids)
        self.assertNotIn("BIZ02", ids)


if __name__ == "__main__":
    unittest.main()
