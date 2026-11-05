"""提交检测与矩阵测试。"""

from __future__ import annotations

import unittest

from helpers import FS_ROOT, cfg, linked, msg

from wcm.submissions import build


def classes(cfg_):
    return cfg_


class TestSubmissionBuild(unittest.TestCase):
    def setUp(self):
        self.cfg = cfg()

    def _build(self, rows, fs=None):
        return build(rows, self.cfg, fs or [])

    def test_full_package_is_accepted(self):
        rows = [
            msg("m1", "2026-10-21T09:00:00+08:00", "wxid_linyz", "林一舟_C8_proposal.md", mtype="file"),
            msg("m2", "2026-10-21T09:01:00+08:00", "wxid_linyz", "林一舟_C8_demo.zip", mtype="file"),
            msg("m3", "2026-10-21T09:02:00+08:00", "wxid_linyz", "林一舟_C8_AI日志.md", mtype="file"),
            msg("m4", "2026-10-21T09:03:00+08:00", "wxid_linyz", "林一舟_C8_拿来说明.md", mtype="file"),
        ]
        for r in rows:
            r["intent"] = "submission"
            r["challenge_ref"] = "C8"
        res = self._build(rows)
        self.assertEqual(res["submission_count"], 1)
        row = res["rows"][0]
        self.assertEqual(row["status"], "accepted")
        self.assertEqual(row["missing"], [])
        self.assertEqual(row["completeness"], 1.0)

    def test_missing_artifact_marks_needs_revision(self):
        rows = [
            msg("m1", "2026-10-21T09:00:00+08:00", "wxid_linyz", "林一舟_C8_proposal.md", mtype="file"),
            msg("m2", "2026-10-21T09:01:00+08:00", "wxid_linyz", "林一舟_C8_AI日志.md", mtype="file"),
        ]
        for r in rows:
            r["intent"] = "submission"
        res = self._build(rows)
        row = res["rows"][0]
        self.assertEqual(row["status"], "needs_revision")
        self.assertIn("demo", row["missing"])
        self.assertIn("notes", row["missing"])
        self.assertLess(row["completeness"], 1.0)
        self.assertTrue(res["missing_required"])

    def test_naming_violation_recorded(self):
        rows = [msg("m1", "2026-10-21T09:00:00+08:00", "wxid_guoyq", "C4A评审器.zip", mtype="file")]
        rows[0]["intent"] = "submission"
        rows[0]["challenge_ref"] = "C4A"
        res = self._build(rows)
        row = res["rows"][0]
        self.assertTrue(row["issues"])
        self.assertIn("命名不规范", row["issues"][0])

    def test_teacher_file_not_counted_as_submission(self):
        rows = [msg("m1", "2026-10-21T09:00:00+08:00", self.cfg.teacher_wxid, "C8_proposal模板.md", mtype="file")]
        rows[0]["intent"] = "submission"
        rows[0]["challenge_ref"] = "C8"
        res = self._build(rows)
        self.assertEqual(res["submission_count"], 0)

    def test_matrix_dimensions(self):
        res = self._build(linked())
        self.assertEqual(res["cells"], len(self.cfg.roster) * len(self.cfg.challenge_order))
        self.assertEqual(len(res["matrix"]), len(self.cfg.roster))
        self.assertEqual(len(res["by_challenge"]), len(self.cfg.challenge_order))

    def test_from_real_message_stream(self):
        res = self._build(linked())
        self.assertGreaterEqual(res["submission_count"], 10, "回放集里至少要能检出 5 个提交事件")
        students = {r["student"] for r in res["rows"]}
        self.assertGreaterEqual(len(students), 5)

    @unittest.skipUnless(FS_ROOT, "")
    def test_disk_merge_is_additive(self):
        from wcm.bridge.fs_scan import scan

        fs = scan(FS_ROOT, self.cfg, student_hint="wxid_jxq2024")
        if not fs:
            self.skipTest("本机没有真实提交目录")
        base = self._build(linked())
        merged = self._build(linked(), fs)
        self.assertGreaterEqual(merged["artifact_count"], base["artifact_count"])
        self.assertGreaterEqual(merged["submission_count"], base["submission_count"])
        jxq = merged["by_student"]["wxid_jxq2024"]
        self.assertGreaterEqual(jxq["challenge_count"], 10)
        sources = {s for r in merged["rows"] for s in r["sources"]}
        self.assertIn("disk", sources)


if __name__ == "__main__":
    unittest.main()
