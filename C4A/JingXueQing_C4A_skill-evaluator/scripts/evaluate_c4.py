#!/usr/bin/env python3
"""C4 技能提交自动评审器 —— 命令行入口。

用法：
    # 完整评审（Level 1-4），输出 Markdown/HTML/Excel/JSON
    python3 evaluate_c4.py <文件夹> --out ./评审输出

    # 只盘点谁交了什么（Level 1，秒级）
    python3 evaluate_c4.py <文件夹> --scan-only

    # 只跑到完整性检查（Level 1-2）
    python3 evaluate_c4.py <文件夹> --level 2

    # 自检：跑内置测试集，输出准确率报告
    python3 evaluate_c4.py --selftest

零第三方依赖，仅需 Python 3.8+。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from c4a import pipeline, report as reporter          # noqa: E402
from c4a.rubric import DEFAULT_WEIGHTS                # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(
        description="C4 技能提交自动评审器（Level 1-4）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("folder", nargs="?", help="包含 C4 提交文件的本地文件夹路径")
    p.add_argument("--out", default="./评审输出", help="报告输出目录（默认 ./评审输出）")
    p.add_argument("--challenge", default="C4", help="挑战 ID，默认 C4")
    p.add_argument("--level", type=int, default=4, choices=[1, 2, 3, 4],
                   help="跑到第几级（默认 4）")
    p.add_argument("--scan-only", action="store_true", help="只做 Level 1 盘点")
    p.add_argument("--weights", default="",
                   help="覆盖维度权重，如 'reusable=0.3,executable=0.3,verifiable=0.2,clear_io=0.2'")
    p.add_argument("--no-xlsx", action="store_true", help="不生成 Excel")
    p.add_argument("--no-html", action="store_true", help="不生成 HTML")
    p.add_argument("--print", dest="to_stdout", action="store_true",
                   help="把Markdown 报告打到标准输出")
    p.add_argument("--selftest", action="store_true", help="运行内置测试集并输出准确率")
    args = p.parse_args()

    if args.selftest:
        from tests.run_selftest import main as selftest_main
        return selftest_main()

    if not args.folder:
        p.print_help()
        print("\n错误：需要提供文件夹路径，或使用 --selftest。", file=sys.stderr)
        return 2

    folder = Path(args.folder).expanduser()
    if not folder.is_dir():
        print(f"错误：'{folder}' 不是有效目录。", file=sys.stderr)
        return 2

    if args.scan_only:
        import json
        print(json.dumps(pipeline.quick_scan(folder, args.challenge),
                         ensure_ascii=False, indent=2))
        return 0

    weights = dict(DEFAULT_WEIGHTS)
    if args.weights:
        for pair in args.weights.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                if k.strip() in weights:
                    weights[k.strip()] = float(v)

    levels = tuple(range(1, args.level + 1))
    rep = pipeline.evaluate(
        folder, challenge=args.challenge, weights=weights,
        out_dir=args.out, write_xlsx=not args.no_xlsx,
        write_html=not args.no_html, levels=levels,
    )

    md = reporter.render_markdown(rep)
    if args.to_stdout or args.level < 4:
        print(md)
    else:
        s = rep.stats()
        print(f"✅ 评审完成：{s.get('n', 0)} 位作者 / {rep.n_files} 个 C4 文件")
        print(f"   报告已输出到：{Path(args.out).expanduser().resolve()}")
        print(f"   - 评审报告.md")
        if not args.no_html:
            print(f"   - 评审仪表盘.html")
        if not args.no_xlsx:
            print(f"   - 评审详表.xlsx")
        print(f"   - 评审结果.json / 文件清单.json")
        if s.get("needs_human"):
            print(f"⚠️有 {s['needs_human']} 位作者证据不足，报告中标为「需人工复核」")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
