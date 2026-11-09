"""解析器测试：这里锁住三个"踩坑后"的设计决策，防止后来者改坏。

关键回归用例（每一个都对应一次真实的 bug）：
- BUG-01 最长匹配：'数据分析' 曾被拆成 '数据' + '分析' 造成双计
- BUG-02 歧义消解：'Python' 曾固定判给 ENG01，导致数据岗简历被判缺后端能力
- BUG-03 加分段落：'加分项' 里的具体要求曾被当成硬门槛，硬缺口虚高 2 倍
"""

import unittest

from jd_insight import parser as jp


class TestSplitSentences(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(jp.split_sentences(""), [])

    def test_basic(self):
        s = jp.split_sentences("要求 A。要求 B！要求 C？")
        self.assertEqual(len(s), 3)

    def test_newline_split(self):
        s = jp.split_sentences("第一行\n\n第二行")
        self.assertEqual(s, ["第一行", "第二行"])

    def test_no_double_count_on_semicolon(self):
        """分号是 JD 里的高频分隔符，必须切句，否则一句里堆 5 个要求会共同抬权重。"""
        self.assertEqual(len(jp.split_sentences("会SQL；会Excel")), 2)


class TestLongestMatch(unittest.TestCase):
    def test_bug01_duijie_kehu_not_double_counted(self):
        """BUG-01 回归：'对接客户'(COM06) 不该再被 '对接'(COM01) 二次计。

        初版这里曾写成断言 '数据分析' 不被拆开，但那不是标签关键词，
        断言永远空转——测试通过得莫名其妙，等于没测。改成本例后才有真信号。
        """
        hits = jp.extract("负责对接客户的需求")
        kws = [h.keyword for h in hits]
        self.assertIn("对接客户", kws)
        self.assertNotIn("对接", kws, "长词命中后短词不应重复计入")
        self.assertIn("COM06", {h.tag_id for h in hits})

    def test_adjacent_distinct_keywords_both_kept(self):
        """不相邻/不重叠的多个关键词必须都保留，别把贪心写成"只留一个"。"""
        hits = jp.extract("熟悉 SQL 与 Excel")
        self.assertGreaterEqual(len(hits), 2)


class TestDisambiguation(unittest.TestCase):
    def test_bug02_python_in_data_context_is_DAT06(self):
        """BUG-02 回归：数据语境下 Python 应判给 DATA 域。"""
        hits = jp.extract("用 Python 做数据清洗")
        ids = {h.tag_id for h in hits}
        self.assertIn("DAT06", ids)

    def test_python_in_backend_context_is_ENG01(self):
        hits = jp.extract("用 Python 写后端服务与接口")
        ids = {h.tag_id for h in hits}
        self.assertIn("ENG01", ids)

    def test_disambiguation_is_deterministic(self):
        text = "熟悉 Python"
        self.assertEqual([h.tag_id for h in jp.extract(text)], [h.tag_id for h in jp.extract(text)])


class TestBonusSection(unittest.TestCase):
    def test_bug03_bonus_flagged(self):
        """BUG-03 回归：'者优先' 必须被标记为 bonus。"""
        hits = jp.extract("有电商行业研究经验者优先")
        self.assertTrue(any(h.section == "bonus" for h in hits))

    def test_required_not_flagged(self):
        hits = jp.extract("必须熟练掌握 SQL")
        self.assertTrue(all(h.section == "required" for h in hits))

    def test_bonus_markers_cover_common_phrases(self):
        for phrase in ("加分项：会 Python", "有竞赛经历更佳", "英语流利者优先", "nice to have: Git"):
            with self.subTest(phrase=phrase):
                self.assertTrue(jp.is_bonus_sentence(phrase))


class TestAggregate(unittest.TestCase):
    def test_counts_split_by_section(self):
        hits = jp.extract("熟悉 SQL。熟悉 SQL 加分。")
        stats = jp.aggregate(hits)
        st = stats["DAT02"]
        self.assertEqual(st.count, 2)
        self.assertEqual(st.required_count, 1)
        self.assertEqual(st.bonus_count, 1)

    def test_sentences_deduped(self):
        hits = jp.extract("熟悉 SQL 和 Excel。熟悉 SQL 和 Excel。")
        st = jp.aggregate(hits)["DAT02"]
        self.assertEqual(len(st.sentences), 1)

    def test_pos_is_monotonic(self):
        hits = jp.extract("SQL。Excel。Python")
        self.assertEqual([h.pos for h in hits], sorted(h.pos for h in hits))

    def test_tag_ids_shortcut(self):
        self.assertEqual(jp.tag_ids("熟练 SQL"), {"DAT02"})


class TestEmptyInput(unittest.TestCase):
    def test_empty_text_no_error(self):
        self.assertEqual(jp.extract(""), [])

    def test_punctuation_only(self):
        self.assertEqual(jp.extract("。。。！！"), [])


if __name__ == "__main__":
    unittest.main()
