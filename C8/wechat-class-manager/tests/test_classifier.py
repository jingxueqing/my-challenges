"""L2 分类器 / 关联器测试：准确率门槛 + 关键用例 + 可解释性。"""

from __future__ import annotations

import unittest

from helpers import cfg, classified, labels, msg, messages

from wcm.classifier import classify_batch, evaluate, summarize_batch
from wcm.linker import link_messages, link_summary


class TestAccuracy(unittest.TestCase):
    def test_accuracy_above_threshold(self):
        m = evaluate(classified(), labels())
        self.assertGreaterEqual(m["accuracy"], 0.70, "课程要求 >70%")
        self.assertEqual(m["total"], len(labels()))
        self.assertIn("confusion", m)
        self.assertLessEqual(m["error_count"], m["total"])

    def test_macro_f1_reported(self):
        m = evaluate(classified(), labels())
        self.assertGreater(m["macro_f1"], 0.6)

    def test_confusion_matrix_is_square_sum(self):
        m = evaluate(classified(), labels())
        total = sum(sum(row.values()) for row in m["confusion"].values())
        self.assertEqual(total, m["total"])


class TestCases(unittest.TestCase):
    def cls(self, rows):
        return classify_batch(rows, cfg())

    def test_file_submission_detected(self):
        rows = [
            msg("m1", "2026-10-21T09:00:00+08:00", "wxid_linyz", "林一舟_C4B_交付物.md", mtype="file"),
            msg("m2", "2026-10-21T09:05:00+08:00", "wxid_linyz", "再发一次"),
        ]
        self.assertEqual(self.cls(rows)[0]["intent"], "submission")

    def test_question_then_answer(self):
        rows = [
            msg("q1", "2026-10-21T09:00:00+08:00", "wxid_linyz", "请问 C5 的仓库要公开吗？"),
            msg("a1", "2026-10-21T09:03:00+08:00", "wxid_hech", "公开的，README 里要写复现命令。", reply_to="q1"),
        ]
        out = self.cls(rows)
        self.assertEqual(out[0]["intent"], "question")
        self.assertEqual(out[1]["intent"], "answer")
        self.assertIn("引用了提问", " ".join(out[1]["signals"]))

    def test_teacher_announcement(self):
        rows = [
            msg("n1", "2026-10-21T09:00:00+08:00", cfg().teacher_wxid, "【通知】本周五 24:00 截止，逾期按未提交处理。", nick="老师"),
        ]
        self.assertEqual(self.cls(rows)[0]["intent"], "announcement")

    def test_resource_with_url(self):
        rows = [msg("r1", "2026-10-21T09:00:00+08:00", "wxid_wuht", "https://docs.github.com/zh 官方文档，比视频快")]
        self.assertEqual(self.cls(rows)[0]["intent"], "resource")

    def test_social_short_reply(self):
        rows = [msg("s1", "2026-10-21T09:00:00+08:00", "wxid_chenxy", "收到，谢谢！")]
        self.assertEqual(self.cls(rows)[0]["intent"], "social")

    def test_confidence_and_signals_present(self):
        out = self.cls([msg("m1", "2026-10-21T09:00:00+08:00", "wxid_linyz", "林一舟_C4B_交付物.md", mtype="file")])
        row = out[0]
        self.assertGreater(row["confidence"], 0.5)
        self.assertTrue(row["signals"], "每条判定都要能说出理由")
        self.assertIn("scores", row)

    def test_summary_counts(self):
        s = summarize_batch(classified())
        self.assertEqual(s["total"], len(messages()))
        self.assertEqual(sum(s["distribution"].values()), s["total"])


class TestLinker(unittest.TestCase):
    def test_coverage_above_half(self):
        ls = link_summary(link_messages(classified(), cfg()))
        self.assertGreater(ls["coverage"], 0.5)
        self.assertIn("explicit_id", ls["by_method"])

    def test_explicit_id_from_text(self):
        rows = [msg("m1", "2026-10-21T09:00:00+08:00", "wxid_linyz", "C4B 的样式粘到公众号之后乱了")]
        out = link_messages(classify_batch(rows, cfg()), cfg())
        self.assertEqual(out[0]["challenge_ref"], "C4B")
        self.assertEqual(out[0]["link_method"], "explicit_id")

    def test_inherited_context_is_low_confidence(self):
        rows = [
            msg("m1", "2026-10-21T09:00:00+08:00", "wxid_linyz", "C4B 的封面尺寸是多少？"),
            msg("m2", "2026-10-21T09:04:00+08:00", "wxid_chenxy", "我用 900×383。"),
        ]
        out = link_messages(classify_batch(rows, cfg()), cfg())
        self.assertEqual(out[1]["challenge_ref"], "C4B")
        self.assertEqual(out[1]["link_method"], "inherited")
        self.assertLess(out[1]["link_score"], 0.5)

    def test_unrelated_message_not_linked(self):
        rows = [msg("m1", "2026-10-21T09:00:00+08:00", "wxid_linyz", "我先睡了，明早看消息")]
        out = link_messages(classify_batch(rows, cfg()), cfg())
        self.assertIsNone(out[0]["challenge_ref"])


if __name__ == "__main__":
    unittest.main()
