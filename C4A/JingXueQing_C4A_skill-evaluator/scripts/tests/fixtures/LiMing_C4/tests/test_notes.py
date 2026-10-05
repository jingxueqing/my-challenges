"""meeting-notes 的测试用例。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from notes import build  # noqa: E402


def test_has_three_sections():
    out = build("张三：今天定下上线时间\n李四：需要在下周前完成文档\n")
    assert "## 议题" in out and "## 结论" in out and "## 待办" in out


def test_empty_transcript():
    assert "（无）" in build("")


def test_todo_detected():
    assert "- [ ]" in build("李四：需要补充测试\n")
