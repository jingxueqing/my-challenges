#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run.py —— 一条命令跑完整条数据管线。

用法：
  python3 run.py all              # 规格 → 扫描 → 数据 → Excel → 网站 → 摘要（默认就是 all）
  python3 run.py specs            # 只重抽挑战规格（改了 CHALLENGE.md 后跑）
  python3 run.py scan             # 只重扫数据 → submissions.json / CSV
  python3 run.py excel            # 只重生成 Excel
  python3 run.py site             # 只重生成网站
  python3 run.py digest           # 只生成每日摘要（发群用）
  python3 run.py check            # 自检：字段完整性、状态分布、与磁盘是否一致
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
PY = sys.executable
DATA = BASE / "JingXueQing_C6A_数据"


def run(script: str) -> int:
    print(f"\n=== {script} ===")
    return subprocess.call([PY, str(HERE / script)], cwd=HERE)


def stage_specs() -> int:
    return run("specs.py")


def stage_scan() -> int:
    return run("pipeline.py")


def stage_excel() -> int:
    return run("make_excel.py")


def stage_site() -> int:
    return run("make_site.py")


def stage_digest() -> int:
    return run("digest.py")


def stage_check() -> int:
    """自检：不写文件，只回答「数据能不能信」。"""
    payload = json.loads((DATA / "submissions.json").read_text(encoding="utf-8"))
    problems: list[str] = []
    for r in payload["records"]:
        tag = f"{r['student']}/{r['challenge_id']}"
        if not r["files"]:
            problems.append(f"{tag}：记录没有文件")
        if r["status"] == "complete" and r["missing"]:
            problems.append(f"{tag}：状态 complete 但 missing 非空")
        if r["status"] == "partial" and not r["missing"]:
            problems.append(f"{tag}：状态 partial 但缺失项为空")
        req = [i for i in r["items"] if i["required"]]
        present = [i for i in req if i["present"]]
        if req and abs(len(present) / len(req) - r["completeness"]) > 1e-3:
            problems.append(f"{tag}：完整度与必填项命中数不一致")
        for f in r["files"]:
            if f["matched_item"] and not any(i["label"] == f["matched_item"] for i in r["items"]):
                problems.append(f"{tag}：文件 {f['rel_path']} 命中的交付项不在规格里")
    pkg_paths = [Path(p["path"]) for p in payload["packages"]]
    gone = [str(p) for p in pkg_paths if not p.exists()]
    if gone:
        problems.append(f"提交包路径已不存在：{gone}")

    print("\n=== check ===")
    print(f"记录 {len(payload['records'])} 条 ｜ 学生 {payload['stats']['n_students']} ｜ 挑战 {payload['stats']['n_challenges']}")
    print(f"状态分布：完整 {payload['stats']['n_complete']} / 缺件 {payload['stats']['n_partial']}")
    for source in payload["provenance"]["roots"]:
        exists = "✅" if Path(source["path"]).exists() else "❌"
        print(f"数据根 {exists} {source['path']}")
    if problems:
        print(f"发现 {len(problems)} 个问题：")
        for p in problems[:20]:
            print("  -", p)
        return 1
    print("自检通过：状态、完整度、文件-规格映射三者一致。")
    return 0


STAGES = {
    "specs": [stage_specs],
    "scan": [stage_scan],
    "data": [stage_scan],
    "excel": [stage_excel],
    "site": [stage_site],
    "digest": [stage_digest],
    "all": [stage_specs, stage_scan, stage_excel, stage_site, stage_digest],
    "check": [stage_check],
}


def main() -> int:
    cmd = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    if cmd not in STAGES:
        print(__doc__)
        return 2
    for stage in STAGES[cmd]:
        code = stage()
        if code != 0:
            print(f"❌ 阶段失败，退出码 {code}")
            return code
    print("\n✅ 完成" + ("（数据已更新，刷新浏览器即可看到）" if cmd in ("all", "site", "scan", "data") else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
