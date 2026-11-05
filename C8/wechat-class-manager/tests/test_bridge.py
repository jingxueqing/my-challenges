"""L1 桥接层测试：标准化、去重、时间窗、群过滤、真实文件扫描。"""

from __future__ import annotations

import os
import tempfile
import unittest

from helpers import FS_ROOT, cfg, messages

from wcm.bridge.base import dedupe, filter_window, normalize_message
from wcm.bridge.fs_scan import scan


class TestNormalize(unittest.TestCase):
    def test_text_message(self):
        raw = {
            "msgId": "m1",
            "time": "2026-10-21 09:00:00",
            "sender": "wxid_a",
            "senderName": "张三",
            "type": 1,
            "content": "请问怎么部署？",
            "talkerName": "测试群",
        }
        m = normalize_message(raw, default_group="测试群")
        self.assertEqual(m["type"], "text")
        self.assertEqual(m["timestamp"], "2026-10-21T09:00:00+08:00")
        self.assertEqual(m["sender"]["nickname"], "张三")
        self.assertEqual(m["sender"]["wechat_id"], "wxid_a")

    def test_file_message_type_49(self):
        raw = {
            "msgId": "m2",
            "time": 1761000000,
            "sender": "wxid_a",
            "type": 49,
            "content": "张三_C4B_交付物.md",
            "contents": {"type": 6, "title": "张三_C4B_交付物.md", "size": "12KB"},
        }
        m = normalize_message(raw, default_group="测试群")
        self.assertEqual(m["type"], "file")
        self.assertIn("C4B", m["content"])

    def test_link_message(self):
        raw = {
            "msgId": "m3",
            "time": "2026-10-21 09:00:00",
            "sender": "wxid_a",
            "type": 49,
            "content": "",
            "contents": {"type": 5, "title": "GitHub 入门", "url": "https://docs.github.com/x"},
        }
        m = normalize_message(raw)
        self.assertEqual(m["type"], "link")
        self.assertIn("https://", m["content"])

    def test_reply_detection_from_xml(self):
        raw = {
            "msgId": "m4",
            "time": "2026-10-21 09:00:00",
            "sender": "wxid_b",
            "type": 1,
            "content": "<refermsg><msgid>999</msgid></refermsg>公开的，README 要写清楚",
        }
        m = normalize_message(raw)
        self.assertEqual(m["reply_to"], "999")
        self.assertNotIn("<refermsg>", m["content"])

    def test_empty_message_dropped(self):
        self.assertIsNone(normalize_message({"msgId": "x", "type": 1, "content": "   "}))

    def test_unix_millis(self):
        from datetime import datetime, timedelta, timezone

        ts = 1761000000  # 2025-10-21 前后
        expect = datetime.fromtimestamp(ts, timezone(timedelta(hours=8))).strftime("%Y-%m-%d")
        m = normalize_message({"msgId": "m5", "type": 1, "content": "hi", "time": ts * 1000})
        self.assertTrue(m["timestamp"].startswith(expect), "毫秒时间戳要能自动识别")

    def test_system_message_is_system_type(self):
        m = normalize_message({"msgId": "m6", "type": 10000, "content": "你撤回了一条消息"})
        self.assertEqual(m["type"], "system")


class TestStream(unittest.TestCase):
    def test_dedupe_keeps_first_and_sorts(self):
        rows = [
            {"msg_id": "b", "timestamp": "2026-10-21T10:00:00+08:00", "sender": {}, "type": "text", "content": "1"},
            {"msg_id": "a", "timestamp": "2026-10-21T09:00:00+08:00", "sender": {}, "type": "text", "content": "2"},
            {"msg_id": "b", "timestamp": "2026-10-21T10:00:00+08:00", "sender": {}, "type": "text", "content": "1"},
        ]
        out = dedupe(rows)
        self.assertEqual([m["msg_id"] for m in out], ["a", "b"])

    def test_window_uses_data_anchor_not_wall_clock(self):
        rows = messages()
        last = rows[-1]["timestamp"]
        win = filter_window(rows, days=7)
        self.assertTrue(win)
        self.assertEqual(win[-1]["timestamp"], last)
        self.assertGreaterEqual(len(rows), len(win))

    def test_fixture_has_enough_messages(self):
        rows = messages()
        self.assertGreaterEqual(len(rows), 100, "Bronze 验收要求至少 100 条")
        types = {m["type"] for m in rows}
        self.assertTrue({"text", "file"} <= types)
        senders = {m["sender"]["wechat_id"] for m in rows}
        self.assertGreaterEqual(len(senders), 20)

    def test_group_filter(self):
        from wcm.bridge.sources import ReplaySource, collect

        rows = collect(ReplaySource("data/fixtures/messages_raw.jsonl"), group="不存在的群", aliases=[])
        self.assertEqual(rows, [])
        rows2 = collect(ReplaySource("data/fixtures/messages_raw.jsonl"), group="Elite20", aliases=cfg().aliases)
        self.assertGreater(len(rows2), 100)


@unittest.skipUnless(os.path.isdir(FS_ROOT), "本机没有真实提交目录，跳过磁盘扫描测试")
class TestFsScan(unittest.TestCase):
    def test_scan_real_submission_packs(self):
        subs = scan(FS_ROOT, cfg(), student_hint="wxid_jxq2024")
        self.assertGreaterEqual(len(subs), 10)
        cids = {s["challenge"] for s in subs}
        self.assertIn("C6A", cids)
        self.assertTrue(all(s["artifact_count"] > 0 for s in subs))
        self.assertTrue(all(s["student"] == "wxid_jxq2024" for s in subs))

    def test_scan_missing_dir_raises(self):
        with self.assertRaises(FileNotFoundError):
            scan("/tmp/definitely-not-here-12345", cfg())


if __name__ == "__main__":
    unittest.main()
