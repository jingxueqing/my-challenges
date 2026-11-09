"""标签体系自检：体系是数据，数据必须有约束。

负责人：JingXueQing（标签体系是她设计的，所以她有责任证明体系内部自洽）
审查人：ChenYu（把约束写成可执行断言）
"""

import unittest

from jd_insight import taxonomy as tx


class TestTaxonomyIntegrity(unittest.TestCase):
    def test_tag_count_is_44(self):
        """标签数一旦变化必须显式改这个数字——防止有人偷偷删标签让分数好看。"""
        self.assertEqual(len(tx.all_tags()), 44)

    def test_ids_unique(self):
        ids = [t.id for t in tx.all_tags()]
        self.assertEqual(len(ids), len(set(ids)), "存在重复标签 id")

    def test_domains_valid(self):
        for t in tx.all_tags():
            self.assertIn(t.domain, tx.DOMAINS, f"{t.id} 的域非法")

    def test_every_tag_has_at_least_three_keywords(self):
        for t in tx.all_tags():
            self.assertGreaterEqual(
                len(t.all_keywords()), 3, f"{t.id} 关键词少于 3 个，召回会不稳"
            )

    def test_weight_in_range(self):
        for t in tx.all_tags():
            self.assertGreaterEqual(t.weight_default, 0.4, f"{t.id} 权重过低")
            self.assertLessEqual(t.weight_default, 1.0, f"{t.id} 权重超过 1.0")

    def test_weights_are_not_all_equal(self):
        """若所有标签权重相同，权重字段就是装饰品，打分等于数命中个数。"""
        ws = {t.weight_default for t in tx.all_tags()}
        self.assertGreater(len(ws), 3)

    def test_keyword_index_consistent(self):
        for kw, ids in tx.KEYWORD_INDEX.items():
            self.assertGreaterEqual(len(ids), 1)
            for tid in ids:
                self.assertIn(kw, [k.lower() for k in tx.get_tag(tid).all_keywords()])

    def test_get_tag_raises_on_unknown(self):
        with self.assertRaises(KeyError):
            tx.get_tag("NOPE99")

    def test_tags_in_domain_rejects_unknown(self):
        with self.assertRaises(ValueError):
            tx.tags_in_domain("不存在的域")

    def test_stats_shape(self):
        s = tx.stats()
        self.assertEqual(s["tags"], 44)
        self.assertEqual(sum(s["domains"].values()), 44)

    def test_every_domain_has_tags(self):
        for d in tx.DOMAINS:
            self.assertGreaterEqual(len(tx.tags_in_domain(d)), 4, f"{d} 标签过少")


class TestAliasUniqueness(unittest.TestCase):
    def test_alias_does_not_collide_across_different_meaning(self):
        """别名允许跨标签共存（靠 parser 消歧），但不能同一个词在同一域内指向两个标签，
        否则该域内无法消歧，命中会随机。"""
        for kw, ids in tx.KEYWORD_INDEX.items():
            domains = [tx.get_tag(i).domain for i in ids]
            self.assertEqual(
                len(domains), len(set(domains)),
                f"关键词「{kw}」在同一域内指向多个标签：{ids}",
            )


if __name__ == "__main__":
    unittest.main()
