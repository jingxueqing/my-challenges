"""打分器测试：所有业务校准规则都要有对应断言。

这些断言的"期望值"由 JingXueQing 用人工判断给出（她会读 JD、知道什么算达标），
ChenYu 负责把它翻译成不依赖具体文本的数学性质（单调性、边界、归一化）。
这是本项目里"业务方出题、工程方写断言"最典型的一个文件。
"""

import unittest

from jd_insight import matcher as mt

JD_FULL = (
    "任职要求：熟练使用 SQL 完成多表取数；掌握 Excel 数据透视；"
    "具备指标体系设计能力，能统一口径；有 A/B 测试经验。"
)


class TestBoundaries(unittest.TestCase):
    def test_empty_resume_scores_zero(self):
        r = mt.match(JD_FULL, "")
        self.assertEqual(r.total, 0.0)
        self.assertEqual(r.grade, "不建议投")

    def test_perfect_resume_scores_100(self):
        resume = "熟练 SQL 多表取数，Excel 数据透视，指标体系与口径，A/B 测试。"
        r = mt.match(JD_FULL, resume)
        self.assertGreater(r.total, 95.0)

    def test_score_within_range(self):
        for resume in ("", "SQL", "SQL Excel 指标体系 A/B 测试 Python Java 财务 招聘"):
            with self.subTest(resume=resume):
                r = mt.match(JD_FULL, resume)
                self.assertGreaterEqual(r.total, 0.0)
                self.assertLessEqual(r.total, 100.0)

    def test_empty_jd_scores_zero(self):
        """空 JD 不应报错，也不应给分（曾经除零崩溃）。"""
        r = mt.match("", "SQL Excel")
        self.assertEqual(r.total, 0.0)


class TestMonotonicity(unittest.TestCase):
    def test_more_evidence_never_lowers_score(self):
        r1 = mt.match(JD_FULL, "会 SQL")
        r2 = mt.match(JD_FULL, "会 SQL，掌握 Excel 数据透视，能统一口径")
        self.assertGreaterEqual(r2.total, r1.total)

    def test_repetition_raises_score_via_deeper_coverage(self):
        """命中 1 次 0.85，命中 ≥2 次 1.0——这是"深度"能被区分的最小机制。"""
        once = mt.match(JD_FULL, "SQL")
        twice = mt.match(JD_FULL, "SQL。再次强调 SQL 取数。")
        self.assertGreater(twice.total, once.total)


class TestWeightNormalization(unittest.TestCase):
    def test_need_vector_sums_to_one(self):
        need = mt._need_vector(JD_FULL)
        self.assertAlmostEqual(sum(t.weight for t in need.values()), 1.0, places=6)

    def test_bonus_gets_less_weight_than_required(self):
        jd = "必须会 SQL。有 Python 能力者优先。"
        need = mt._need_vector(jd)
        self.assertGreater(need["DAT02"].weight, need["ENG01"].weight)


class TestHardGap(unittest.TestCase):
    def test_high_weight_missing_is_hard_gap(self):
        r = mt.match(JD_FULL, "完全无关的经历：参加过合唱团。")
        ids = [t.tag_id for t in r.hard_gaps]
        self.assertIn("DAT02", ids)

    def test_bonus_only_tag_is_not_hard_gap(self):
        jd = "必须会 SQL。有 Python 能力者优先。"
        r = mt.match(jd, "熟练 SQL")
        self.assertNotIn("ENG01", [t.tag_id for t in r.hard_gaps])

    def test_hard_gap_implies_zero_coverage(self):
        r = mt.match(JD_FULL, "")
        for g in r.hard_gaps:
            self.assertEqual(g.coverage, 0.0)


class TestClassifyRole(unittest.TestCase):
    def test_tech_role(self):
        self.assertEqual(mt.classify_role("Java SpringBoot MySQL Redis Docker"), "技术岗")

    def test_business_role(self):
        self.assertEqual(mt.classify_role("负责用户研究与问卷设计，输出用户画像"), "非技术岗/复合岗")


class TestRankJobs(unittest.TestCase):
    def test_rank_sorted_desc(self):
        jobs = [
            {"id": "1", "company": "A", "title": "数据岗", "jd_text": "SQL Excel 指标体系"},
            {"id": "2", "company": "B", "title": "后端岗", "jd_text": "Java Spring MySQL Docker Redis"},
        ]
        rows = mt.rank_jobs("熟练 SQL 与 Excel 数据透视", jobs)
        self.assertEqual([r["id"] for r in rows], ["1", "2"])
        self.assertGreaterEqual(rows[0]["total"], rows[1]["total"])

    def test_top_limit(self):
        jobs = [{"id": str(i), "company": "C", "title": f"岗{i}", "jd_text": "SQL"} for i in range(5)]
        self.assertEqual(len(mt.rank_jobs("SQL", jobs, top=2)), 2)


class TestAdvice(unittest.TestCase):
    def test_advice_not_empty_when_gaps_exist(self):
        r = mt.match(JD_FULL, "")
        self.assertTrue(r.advise)

    def test_advice_mentions_gap_name(self):
        r = mt.match(JD_FULL, "")
        joined = "".join(r.advise)
        self.assertTrue(any(g.name in joined for g in r.hard_gaps))


if __name__ == "__main__":
    unittest.main()
