"""端到端测试：不看函数，只看"用户敲的那条命令还灵不灵"。

为什么必须有这一层：三个模块的单测全绿，但 CLI 里参数名写错、默认路径错、
SystemExit 码错，用户第一次用就会失败。这是最丢分的一类问题，也是最容易漏测的。
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_cli(*args, cwd=ROOT):
    """用 -m 方式调用，确保和 README 里写的用法完全一致。"""
    return subprocess.run(
        [sys.executable, "-m", "jd_insight.cli", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )


class TestSelfcheck(unittest.TestCase):
    def test_exit_zero(self):
        r = run_cli("selfcheck")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("selfcheck 通过", r.stdout)


class TestTaxonomyCmd(unittest.TestCase):
    def test_prints_all_domains(self):
        r = run_cli("taxonomy")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("标签总数 44", r.stdout)
        self.assertIn("业务与行业", r.stdout)


class TestMatchCmd(unittest.TestCase):
    def test_generates_html_and_json(self):
        with tempfile.TemporaryDirectory() as td:
            html_path = os.path.join(td, "r.html")
            json_path = os.path.join(td, "r.json")
            r = run_cli(
                "match",
                "--jd", "data/jd_J01.txt",
                "--resume", "data/resume_demo.txt",
                "-o", html_path,
                "--json", json_path,
                "--jobs", "data/jd_samples.csv",
                "--jd-title", "用户增长分析师",
                "--resume-name", "景雪晴",
            )
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertTrue(os.path.exists(html_path))
            self.assertGreater(os.path.getsize(html_path), 5000, "HTML 报告过小，可能模板没渲染")

            with open(html_path, encoding="utf-8") as f:
                html = f.read()
            self.assertIn("岗位匹配度报告", html)
            self.assertIn("六域覆盖度", html)
            self.assertIn("景雪晴", html)

            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertIn("total", data)
            self.assertIn("ranking", data)
            self.assertGreater(len(data["ranking"]), 0)

    def test_missing_file_returns_2(self):
        r = run_cli("match", "--jd", "data/__nope__.txt", "--resume", "data/resume_demo.txt", "-o", "/tmp/x.html")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("文件不存在", r.stderr)

    def test_bad_csv_returns_3(self):
        with tempfile.TemporaryDirectory() as td:
            bad = os.path.join(td, "bad.csv")
            with open(bad, "w", encoding="utf-8") as f:
                f.write("a,b\n1,2\n")
            r = run_cli("match", "--jd", "data/jd_J01.txt", "--resume", "data/resume_demo.txt",
                        "-o", os.path.join(td, "x.html"), "--jobs", bad)
            self.assertEqual(r.returncode, 3, r.stderr)
            self.assertIn("缺少必需列", r.stderr)


class TestRankCmd(unittest.TestCase):
    def test_rank_output_ordered(self):
        r = run_cli("rank", "--jobs", "data/jd_samples.csv", "--resume", "data/resume_demo.txt", "--top", "5")
        self.assertEqual(r.returncode, 0, r.stderr)
        lines = [l for l in r.stdout.splitlines() if l.strip().startswith(tuple("123456789"))]
        self.assertEqual(len(lines), 5)
        self.assertIn("共 24 条 JD", r.stdout)


class TestVersion(unittest.TestCase):
    def test_version_flag(self):
        r = run_cli("--version")
        self.assertEqual(r.returncode, 0)
        self.assertIn("jd-insight", r.stdout)


if __name__ == "__main__":
    unittest.main()
