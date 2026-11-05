"""Q&A 抽取、预警规则、图存储、增量 watch、自然语言查询的测试。"""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime

from helpers import FS_ROOT, cfg, classified, linked, msg

from wcm import alerts as alerts_mod
from wcm import qa as qa_mod
from wcm.classifier import classify_batch
from wcm.ingest import ingest
from wcm.profile import build as build_profiles
from wcm.query import answer as query_answer
from wcm.store import CST, GraphStore
from wcm.submissions import build as build_submissions
from wcm.watcher import watch_once


# ------------------------------- Q&A -------------------------------
class TestQA(unittest.TestCase):
    def test_pair_extracted(self):
        rows = [
            msg("q1", "2026-10-21T09:00:00+08:00", "wxid_linyz", "请问 latex 参考文献怎么改成国标格式？"),
            msg("a1", "2026-10-21T09:06:00+08:00", "wxid_jxq2024", "换 biblatex 的 gb7714-2015 样式，编译一次就好。", reply_to="q1"),
            msg("t1", "2026-10-21T09:09:00+08:00", "wxid_linyz", "解决了，谢谢！"),
        ]
        rows = classify_batch(rows, cfg())
        res = qa_mod.extract(rows, cfg())
        self.assertEqual(res["answered"], 1)
        pair = res["pairs"][0]
        self.assertEqual(pair["asker"]["wechat_id"], "wxid_linyz")
        self.assertEqual(pair["answerer"]["wechat_id"], "wxid_jxq2024")
        self.assertTrue(pair["evidence"]["cited_by_reply"])
        self.assertGreaterEqual(pair["quality_score"], 0.5)

    def test_unanswered_question_recorded(self):
        rows = [msg("q1", "2026-10-21T09:00:00+08:00", "wxid_pengxy", "公众号封面尺寸到底用多少？")]
        res = qa_mod.extract(classify_batch(rows, cfg()), cfg())
        self.assertEqual(res["answered"], 0)
        self.assertEqual(res["unanswered_count"], 1)

    def test_quality_sorted_desc(self):
        res = qa_mod.extract(linked(), cfg())
        scores = [p["quality_score"] for p in res["pairs"]]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_at_least_ten_pairs_from_fixture(self):
        res = qa_mod.extract(linked(), cfg())
        self.assertGreaterEqual(res["kept"], 10, "Silver 验收要求 ≥10 个有意义的 Q&A")
        self.assertTrue(res["top_tags"])


# ------------------------------- 预警 -------------------------------
class TestAlerts(unittest.TestCase):
    def _fixture_data(self):
        rows = linked()
        subs = build_submissions(rows, cfg(), [])
        qa = qa_mod.extract(rows, cfg())
        prof = build_profiles(cfg(), rows, subs, qa)
        return rows, subs, qa, prof

    def test_multiple_rule_types_fire(self):
        rows, subs, qa, prof = self._fixture_data()
        res = alerts_mod.evaluate(cfg(), rows, subs, qa, prof)
        self.assertGreaterEqual(len(res["by_type"]), 3, "L4 验收要求至少 3 种预警能触发")
        self.assertIn("silent_student", res["by_type"])
        self.assertIn("unanswered_question", res["by_type"])

    def test_deadline_rule_fires_near_due_date(self):
        rows, subs, qa, prof = self._fixture_data()
        as_of = datetime(2026, 12, 29, 10, 0, tzinfo=CST)  # C8 截止 2026-12-31
        res = alerts_mod.evaluate(cfg(), rows, subs, qa, prof, as_of=as_of)
        kinds = {a["type"] for a in res["alerts"]}
        self.assertIn("deadline_risk", kinds)
        deadline = [a for a in res["alerts"] if a["type"] == "deadline_risk"][0]
        self.assertIn(deadline["severity"], ("high", "medium"))
        self.assertGreater(deadline["evidence"]["missing_count"], 0)

    def test_silent_student_threshold(self):
        rows, subs, qa, prof = self._fixture_data()
        silent = [p for p in prof["profiles"] if p["silence_days"] >= cfg().rules.silent_days]
        res = alerts_mod.evaluate(cfg(), rows, subs, qa, prof)
        alert_names = {a["evidence"].get("nickname") for a in res["alerts"] if a["type"] == "silent_student"}
        self.assertTrue(alert_names)
        self.assertTrue({p["nickname"] for p in silent} >= alert_names)

    def test_every_alert_has_evidence_and_action(self):
        rows, subs, qa, prof = self._fixture_data()
        res = alerts_mod.evaluate(cfg(), rows, subs, qa, prof)
        for a in res["alerts"]:
            self.assertTrue(a["evidence"], f"{a['id']} 没有证据")
            self.assertTrue(a["action"])
            self.assertIn(a["severity"], ("high", "medium", "low"))

    def test_no_alerts_no_crash(self):
        res = alerts_mod.evaluate(cfg(), [], {"by_challenge": {}, "rows": [], "matrix": {}},
                                  {"pairs": [], "unanswered": []}, {"profiles": []})
        self.assertEqual(res["total"], 0)

    def test_statement_disguised_as_question_is_not_nudged(self):
        """分类器判成 question，但人一眼看出是在陈述——不应该生成「催人回答」。

        真实触发：彭心语「…打开率高很多，我自己测是这样。」被推进了催办草稿。
        """
        self.assertFalse(alerts_mod.looks_like_question("标题里带具体数字和场景的打开率高很多，我自己测是这样。"))
        self.assertTrue(alerts_mod.looks_like_question("C8 的 proposal 要写几页？"))
        self.assertTrue(alerts_mod.looks_like_question("有人知道 demo 怎么录吗"))
        self.assertFalse(alerts_mod.looks_like_question(""))


# ------------------------------- 图存储 -------------------------------
class TestStore(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = GraphStore(os.path.join(self.tmp.name, "g.db"))

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_upsert_and_merge(self):
        self.store.upsert_node("student:a", "Student", {"name": "张三"})
        self.store.upsert_node("student:a", "Student", {"major": "计算机"})
        node = self.store.get_node("student:a")
        self.assertEqual(node["props"]["name"], "张三")
        self.assertEqual(node["props"]["major"], "计算机")

    def test_edges_and_neighbors(self):
        self.store.upsert_node("student:a", "Student", {"name": "张三"})
        self.store.upsert_node("challenge:C1", "Challenge", {"name_cn": "翻译"})
        self.store.upsert_node("submission:1", "Submission", {"status": "accepted"})
        self.store.add_edge("SUBMITTED", "student:a", "submission:1")
        self.store.add_edge("ABOUT", "submission:1", "challenge:C1")
        out = self.store.neighbors("student:a", "SUBMITTED")
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["id"], "submission:1")

    def test_search(self):
        self.store.upsert_node("qa:1", "QAPair", {"question": "GitHub 仓库要公开吗", "answer": "要公开"})
        hits = self.store.search("GitHub")
        self.assertTrue(hits)

    def test_meta_checkpoint(self):
        self.store.set_meta("checkpoint", {"last_msg_id": "m9"})
        self.assertEqual(self.store.get_meta("checkpoint")["last_msg_id"], "m9")

    def test_stats(self):
        self.store.upsert_node("a", "Student")
        self.store.upsert_node("b", "Student")
        self.assertEqual(self.store.stats()["Student"], 2)

    def test_edge_counts_match_total_after_dedupe(self):
        """同一对师生重复建边只能留一条，逐类相加必须等于总数。

        这条是补的：ingest 早期返回的是「调用次数」而不是「库里行数」，
        于是逐类相加 711、总数 702，报给人的数字自己都对不起账。
        """
        self.store.upsert_node("student:teacher", "Student", {"name": "甲"})
        self.store.upsert_node("student:asker", "Student", {"name": "乙"})
        for _ in range(3):
            self.store.add_edge("MENTORED", "student:teacher", "student:asker")
        counts = self.store.counts_by_edge()
        self.assertEqual(counts["MENTORED"], 1)
        self.assertEqual(sum(counts.values()), self.store.stats()["_edges"])


# ------------------------------- 增量 -------------------------------
class TestWatcher(unittest.TestCase):
    def test_incremental_no_repeat(self):
        from helpers import FIXTURE

        with tempfile.TemporaryDirectory() as tmp:
            store = GraphStore(os.path.join(tmp, "g.db"))
            first = watch_once(cfg(), store, source_name="replay", days=14, fixture=FIXTURE)
            self.assertGreater(first["new"], 100)
            self.assertEqual(store.stats().get("Message"), first["new"])

            second = watch_once(cfg(), store, source_name="replay", days=14, fixture=FIXTURE)
            self.assertEqual(second["new"], 0, "第二次运行不能重复处理")
            self.assertEqual(second["already_processed"], first["new"])
            self.assertEqual(store.stats().get("Message"), first["new"])
            store.close()

    def test_checkpoint_written(self):
        from helpers import FIXTURE

        with tempfile.TemporaryDirectory() as tmp:
            store = GraphStore(os.path.join(tmp, "g.db"))
            res = watch_once(cfg(), store, source_name="replay", days=7, fixture=FIXTURE)
            ck = store.get_meta("checkpoint", {})
            self.assertEqual(ck.get("last_msg_id"), res["checkpoint"]["last_msg_id"])
            store.close()


# ------------------------------- 查询 -------------------------------
class TestQuery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cfg_ = cfg()
        rows = linked()
        fs = []
        if os.path.isdir(FS_ROOT):
            from wcm.bridge.fs_scan import scan

            fs = scan(FS_ROOT, cfg_, student_hint="wxid_jxq2024")
        subs = build_submissions(rows, cfg_, fs)
        qa = qa_mod.extract(rows, cfg_)
        prof = build_profiles(cfg_, rows, subs, qa)
        cls.store = GraphStore(os.path.join(cls.tmp.name, "g.db"))
        ingest(cfg_, cls.store, rows, subs, qa, prof, None)
        cls.cfg = cfg_

    @classmethod
    def tearDownClass(cls):
        cls.store.close()
        cls.tmp.cleanup()

    def ask(self, q):
        return query_answer(self.store, self.cfg, q)

    def test_who_missing_for_challenge(self):
        res = self.ask("C4B 还有谁没交")
        self.assertEqual(res["intent"], "missing_for_challenge")
        self.assertIn("C4B", res["answer"])
        self.assertTrue(res["data"]["missing"])

    def test_student_submissions(self):
        res = self.ask("景雪晴提交了哪些挑战")
        self.assertEqual(res["intent"], "student_submissions")
        self.assertIn("景雪晴", res["answer"])

    def test_top_active(self):
        res = self.ask("最近一周谁最活跃")
        self.assertEqual(res["intent"], "top_active")
        self.assertIn("参与分", res["answer"])

    def test_faq_by_topic(self):
        res = self.ask("关于 C4B 的常见问题有哪些")
        self.assertEqual(res["intent"], "faq")
        self.assertTrue(res["data"], "C4B 相关问答应该能检索到")

    def test_faq_unknown_topic_is_graceful(self):
        res = self.ask("关于量子计算的常见问题有哪些")
        self.assertEqual(res["intent"], "faq")
        self.assertIn("没有找到", res["answer"])

    def test_overview(self):
        res = self.ask("这周班级状态如何")
        self.assertEqual(res["intent"], "overview")
        self.assertIn("消息", res["answer"])

    def test_silent(self):
        res = self.ask("谁最近不活跃")
        self.assertEqual(res["intent"], "silent_students")
        self.assertIn("沉默", res["answer"])

    def test_challenge_rate(self):
        res = self.ask("C8 的提交率是多少")
        self.assertEqual(res["intent"], "challenge_rate")
        self.assertIn("提交率", res["answer"])

    def test_unknown_student_does_not_crash(self):
        res = self.ask("王小明提交了哪些挑战")
        self.assertIn("哪位同学", res["answer"])

    def test_evidence_returned(self):
        res = self.ask("谁最活跃")
        self.assertTrue(res["evidence"])


if __name__ == "__main__":
    unittest.main()
