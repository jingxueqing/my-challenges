#!/usr/bin/env python3
"""wechat_bridge.py —— L1 数据桥接 CLI

把微信群里发生的事，变成 agent 能消费的 JSON Lines。

    python wechat_bridge.py --group "Elite20" --days 7 --output out/messages.jsonl
    python wechat_bridge.py --source chatlog --url http://127.0.0.1:5030 --group Elite20 --days 7
    python wechat_bridge.py --source replay --fixture data/fixtures/messages_raw.jsonl --days 14
    python wechat_bridge.py --scan-submissions ~/Desktop/挑战的产物 --owner JingXueQing

输出：UMF schema 的 JSONL（见 schemas/message.schema.json），可直接管道给 classifier。
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from wcm.bridge import SourceError, fetch_messages, write_jsonl  # noqa: E402
from wcm.bridge.fs_scan import scan  # noqa: E402
from wcm.config import load_config, project_path  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="微信群消息 → JSONL 桥接器")
    p.add_argument("--group", default=None, help="群名称（默认取 config/group_config.yaml）")
    p.add_argument("--days", type=int, default=7, help="最近 N 天（默认 7）")
    p.add_argument("--since", default=None, help="起始时间，如 2026-10-21 或 2026-10-21T09:00:00")
    p.add_argument("--until", default=None, help="结束时间")
    p.add_argument("--output", "-o", default=None, help="输出 JSONL 路径")
    p.add_argument("--source", default="replay", choices=["replay", "chatlog", "sqlcipher"], help="数据来源")
    p.add_argument("--fixture", default=None, help="replay 模式的 JSONL 文件")
    p.add_argument("--url", default="http://127.0.0.1:5030", help="chatlog 服务地址")
    p.add_argument("--db", default=None, help="sqlcipher 模式的 message_N.db 路径")
    p.add_argument("--key", default="", help="sqlcipher 模式的密钥")
    p.add_argument("--scan-submissions", default=None, help="额外：扫描磁盘上的提交包目录")
    p.add_argument("--owner", default=None, help="扫描提交包时，无姓名文件归属给谁（如 JingXueQing）")
    p.add_argument("--meta-out", default=None, help="把统计信息写到这个 json")
    p.add_argument("--quiet", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config()

    if args.scan_submissions:
        owner = None
        if args.owner:
            st = cfg.roster.resolve(args.owner)
            owner = st.wxid if st else args.owner
        subs = scan(args.scan_submissions, cfg, student_hint=owner)
        out = args.output or project_path("out", "submissions_fs.json")
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(
                {
                    "source": "fs_scan",
                    "root": os.path.abspath(os.path.expanduser(args.scan_submissions)),
                    "owner": args.owner,
                    "count": len(subs),
                    "artifacts": sum(s["artifact_count"] for s in subs),
                    "submissions": subs,
                },
                fh,
                ensure_ascii=False,
                indent=2,
            )
        if not args.quiet:
            print(f"扫描完成：{len(subs)} 条提交 / {sum(s['artifact_count'] for s in subs)} 个文件 → {out}")
            for s in subs:
                print(f"  {s['student_nickname']:<6} {s['challenge']:<5} {s['artifact_count']:>3} files  {','.join(s['artifact_kind_list']) if s.get('artifact_kind_list') else ','.join(s['artifact_kinds'])}")
        return 0

    fixture = args.fixture
    if args.source == "replay" and not fixture:
        fixture = project_path("data", "fixtures", "messages_raw.jsonl")
        if not os.path.exists(fixture):
            print("找不到默认回放文件，先跑：python data/make_fixtures.py", file=sys.stderr)
            return 2

    try:
        messages, meta = fetch_messages(
            cfg,
            source_name=args.source,
            group=args.group,
            days=args.days,
            since=args.since,
            until=args.until,
            fixture=fixture,
            url=args.url,
            db_path=args.db,
            db_key=args.key,
        )
    except SourceError as exc:
        print(f"[bridge] 取数失败：{exc}", file=sys.stderr)
        return 3

    out = args.output or project_path("out", "messages.jsonl")
    write_jsonl(out, messages)
    meta_out = args.meta_out or (os.path.splitext(out)[0] + ".meta.json")
    with open(meta_out, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, ensure_ascii=False, indent=2)

    if not args.quiet:
        print(f"[bridge] source={meta['source']} group={meta['group']}")
        print(f"[bridge] {meta['count']} 条消息 | {meta['earliest']} → {meta['latest']} | 发送者 {meta['senders']} 人")
        print(f"[bridge] 类型分布：{meta['types']}")
        print(f"[bridge] 输出：{out}")
    if meta["count"] < 100:
        print(f"[bridge] 注意：只有 {meta['count']} 条，Bronze 验收要求 ≥100 条", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
