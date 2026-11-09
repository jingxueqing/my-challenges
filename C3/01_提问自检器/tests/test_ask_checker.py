#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ask_checker 的回归测试。

测试的重点不是「分数好不好看」，而是三件容易在改动里悄悄坏掉的事：
1. 灌水必须 0 分（C3 rubric 写死的红线）；
2. 「这个报错了怎么办」不能拿到「真实报错」的分（第一版真发生过，见 AI日志 R2）；
3. 已经达标的好问题，分数不能因为改规则掉下来（防止改 A 坏 B）。

跑法： python3 tests/test_ask_checker.py -v
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

import ask_checker as ac  # noqa: E402

SAMPLES = ROOT / "samples"


def dim(rep, dim_id):
    return next(d for d in rep.dimensions if d.id == dim_id)


def check(rep, dim_id, check_id):
    return next(c for c in dim(rep, dim_id).checks if c.id == check_id)


class TestSlack(unittest.TestCase):
    """灌水规则：宁可错杀，不可放水。"""

    def test_plus_one_is_zero(self):
        for text in ["+1", "＋1 同问", "同问", "收到", "好的", "蹲", "？？？", "👍👍👍", ""]:
            with self.subTest(text=text):
                rep = ac.analyze(text)
                self.assertTrue(rep.is_slack, f"{text!r} 应判灌水")
                self.assertEqual(rep.total, 0)

    def test_short_but_real_is_not_slack(self):
        """有报错原文的短句不算灌水 —— 短不等于水。"""
        rep = ac.analyze("ModuleNotFoundError: No module named 'markdown'")
        self.assertFalse(rep.is_slack)


class TestFakeErrorCredit(unittest.TestCase):
    """第一版的假分：只要出现「报错」两个字就给分。"""

    def test_vague_complaint_gets_no_error_credit(self):
        rep = ac.analyze("这个报错了怎么办")
        self.assertFalse(check(rep, "blocker", "error").hit,
                         "只说「报错了」不该算提供了报错")
        self.assertLessEqual(rep.total, 25)

    def test_bare_word_needs_codeblock(self):
        """只有贴了代码块，宽泛的「报错/失败」才算数。"""
        no_block = ac.analyze("我跑了一下，它报错了，想问下怎么解决这个问题呢")
        self.assertFalse(check(no_block, "blocker", "error").hit)

        with_block = ac.analyze("我跑了一下，它报错了：\n```\nError: something\n```\n想问下怎么解决")
        self.assertTrue(check(with_block, "blocker", "error").hit)


class TestGoodSamples(unittest.TestCase):
    """真实群发言（本轮写好的三帖）必须稳定达标。"""

    FLOOR = {"good_01_C4D_ollama_cpu.txt": 95,
             "good_02_C4B_依赖缺失.txt": 85,
             "good_03_C4A_给同学补件建议.txt": 80}

    def test_floors(self):
        for name, floor in self.FLOOR.items():
            with self.subTest(sample=name):
                rep = ac.analyze((SAMPLES / name).read_text(encoding="utf-8"))
                self.assertGreaterEqual(rep.total, floor,
                                        f"{name} 掉到 {rep.total}，低于底线 {floor}")

    def test_full_marks_sample_is_really_full(self):
        rep = ac.analyze((SAMPLES / "good_01_C4D_ollama_cpu.txt").read_text(encoding="utf-8"))
        self.assertEqual(rep.total, 100)
        for d in rep.dimensions:
            with self.subTest(dim=d.id):
                self.assertEqual(d.score, d.max, f"{d.name} 没拿满：{d.missed}")


class TestBadSamples(unittest.TestCase):

    def test_bad_samples_are_low(self):
        for name in ["bad_01_甩问题.txt", "bad_02_纯表情灌水.txt", "bad_03_有报错没上下文.txt"]:
            with self.subTest(sample=name):
                rep = ac.analyze((SAMPLES / name).read_text(encoding="utf-8"))
                self.assertLessEqual(rep.total, 25)


class TestStructure(unittest.TestCase):

    def test_dimensions_are_four_and_sum_to_100(self):
        rep = ac.analyze("占位")
        self.assertEqual(len(rep.dimensions), 4)
        self.assertEqual(sum(d.max for d in rep.dimensions), 100)

    def test_json_is_serialisable(self):
        rep = ac.analyze((SAMPLES / "good_02_C4B_依赖缺失.txt").read_text(encoding="utf-8"))
        payload = json.loads(json.dumps(rep.to_dict(), ensure_ascii=False))
        self.assertEqual(set(payload) >= {"total", "verdict", "dimensions"}, True)
        self.assertEqual(len(payload["dimensions"]), 4)

    def test_every_miss_has_actionable_hint(self):
        """缺项必须给出「补什么」的具体句子，不能是空话。"""
        rep = ac.analyze("我在做 C4D")
        missed = [c for d in rep.dimensions for c in d.missed]
        self.assertTrue(missed)
        for c in missed:
            with self.subTest(check=c.id):
                self.assertGreaterEqual(len(c.hint), 8)


class TestCli(unittest.TestCase):

    def _run(self, *args, stdin_text=None):
        return subprocess.run(
            [sys.executable, str(ROOT / "ask_checker.py"), *args],
            input=stdin_text, capture_output=True, text=True, timeout=30,
        )

    def test_exit_code_pass(self):
        r = self._run(str(SAMPLES / "good_01_C4D_ollama_cpu.txt"))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("可以直接发", r.stdout)

    def test_exit_code_fail(self):
        r = self._run(str(SAMPLES / "bad_01_甩问题.txt"))
        self.assertEqual(r.returncode, 1)

    def test_stdin_json(self):
        r = self._run("-", "--json", "--min", "0", stdin_text="+1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(json.loads(r.stdout)["total"], 0)

    def test_missing_file_exit_2(self):
        r = self._run("/tmp/definitely_not_here_9527.txt")
        self.assertEqual(r.returncode, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
