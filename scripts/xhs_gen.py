#!/usr/bin/env python3
"""
小红书内容生成 - 统一入口

用法:
    python xhs_gen.py <垂类> <话题> [action]

示例:
    python xhs_gen.py stock "AAPL"           # 完整生成
    python xhs_gen.py stock "NVDA" --content # 只生成内容
    python xhs_gen.py stock "TSLA" --cover   # 只生成封面
"""

import argparse
import os
import sys
from pathlib import Path

# 添加 scripts/lib 到路径
SCRIPT_DIR = Path(__file__).parent.absolute()
LIB_DIR = SCRIPT_DIR / "lib"
SKILL_DIR = SCRIPT_DIR.parent  # skill 根目录
sys.path.insert(0, str(LIB_DIR))

from pipeline import Pipeline
from session import XhsSession


def print_session_info(session: XhsSession) -> None:
    """打印 session 信息"""
    data = session.to_dict()
    print(f"\n# Session ID: {session.session_id}")
    print(f"# Status: {session.status}")
    print(f"# Vertical: {session.vertical}")
    print(f"# Topic: {session.topic}")
    print(f"# Directory: {session.session_dir}")

    print("\n# Steps:")
    for step_id, step_data in data.get('steps', {}).items():
        status_emoji = {
            'pending': '○',
            'in_progress': '◐',
            'completed': '●',
            'failed': '✗'
        }.get(step_data.get('status', 'unknown'), '?')
        print(f"  {status_emoji} {step_id}: {step_data.get('status', 'unknown')}")

    # 显示生成的内容摘要
    gen_data = session.get_step_data('generate')
    if gen_data:
        print(f"\n# Generated Content:")
        print(f"  Title: {gen_data.get('title', '')}")
        print(f"  Subtitle: {gen_data.get('subtitle', '')}")
        print(f"  Length: {gen_data.get('content_length', 0)} chars")

    # 显示股票数据（如果有）
    prep_data = session.get_step_data('prepare_img')
    if prep_data:
        variables = prep_data.get('data', {}).get('variables', {})
        if variables:
            print(f"\n# Cover Variables:")
            for k, v in variables.items():
                if k in ['price', 'change', 'reason', 'trend_arrow']:
                    print(f"  {k}: {v}")


def main():
    parser = argparse.ArgumentParser(
        description="小红书内容生成 - 统一入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s stock "AAPL"                # 完整生成（内容+封面+发送）
  %(prog)s stock "NVDA" --content      # 只生成内容
  %(prog)s stock "TSLA" --cover        # 只生成封面
  %(prog)s stock "AAPL" --info         # 显示 session 信息
  %(prog)s stock "MSFT" --init         # 只初始化 session

测试模式（使用 mock 数据）:
  XHS_TEST_MODE=true %(prog)s stock "AAPL"
        """
    )

    parser.add_argument('vertical', help='垂类 (stock, finance, tech, beauty)')
    parser.add_argument('topic', help='话题/主题/股票代码')
    parser.add_argument('--action', choices=['all', 'content', 'cover', 'info', 'init'],
                        default='all', help='执行动作 (默认: all)')
    parser.add_argument('--max-retries', type=int, default=2,
                        help='内容生成最大重试次数 (默认: 2)')

    args = parser.parse_args()

    # 检查测试模式
    use_test_mode = os.environ.get('XHS_TEST_MODE', 'false').lower() == 'true'
    if use_test_mode:
        print(f"# TEST MODE: Using mock data for stock variables", file=sys.stderr)

    # 初始化流水线
    skill_dir = SKILL_DIR
    workspace = Path.home() / '.openclaw' / 'agents' / 'main' / 'agent'
    workspace.mkdir(parents=True, exist_ok=True)

    pipeline = Pipeline(skill_dir=skill_dir, workspace=workspace)

    # 获取或创建 session
    if args.action == 'init':
        session = pipeline.create_session(args.vertical, args.topic)
        print(f"# ✓ Session created: {session.session_dir}")
        return 0
    else:
        session = pipeline.get_or_create_session(args.vertical, args.topic)
        # 更新 vertical（如果是复用的 session）
        if session.vertical != args.vertical:
            session._data['vertical'] = args.vertical
            session._save()

    print(f"# Session: {session.session_dir}", file=sys.stderr)

    # 执行动作
    if args.action == 'info':
        print_session_info(session)
        return 0

    if args.action == 'content':
        success = pipeline.run_content_pipeline(session, args.max_retries)
        print_session_info(session)
        return 0 if success else 1

    if args.action == 'cover':
        success = pipeline.run_cover_pipeline(session)
        print_session_info(session)
        return 0 if success else 1

    if args.action == 'all':
        success = pipeline.run_all(session, args.max_retries)
        print_session_info(session)
        return 0 if success else 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
