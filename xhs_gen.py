#!/usr/bin/env python3
"""
小红书内容生成 - 纯 Python 版本命令行入口

替代原有的 xhs_generate.sh，提供完整的 7 步流水线功能。

用法:
    python xhs_gen.py <垂类> <话题> [action]

示例:
    python xhs_gen.py stock "NVDA stock analysis"
    python xhs_gen.py finance "美联储利率决议" --content
    python xhs_gen.py tech "AI芯片市场" --info
"""

import argparse
import json
import sys
from pathlib import Path

# 添加 lib 到路径
SCRIPT_DIR = Path(__file__).parent.absolute()
LIB_DIR = SCRIPT_DIR / "lib"
sys.path.insert(0, str(LIB_DIR))

from pipeline import Pipeline
from session import XhsSession


def print_session_info(session: XhsSession) -> None:
    """打印 session 信息"""
    print(f"# Session ID: {session.session_id}")
    print(f"# Status: {session.status}")
    print(f"# Vertical: {session.vertical}")
    print(f"# Topic: {session.topic}")
    print(f"# Directory: {session.session_dir}")
    print("\n# Steps:")
    for step_id, step_data in session.to_dict().get('steps', {}).items():
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


def main():
    parser = argparse.ArgumentParser(
        description="小红书内容生成 - 纯 Python 版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s stock "NVDA stock"           # 生成 NVDA 股票分析
  %(prog)s finance "美联储利率决议"      # 生成金融分析
  %(prog)s tech "AI芯片市场" --content   # 只生成内容
  %(prog)s stock "AAPL" --info          # 显示 session 信息
        """
    )

    parser.add_argument('vertical', help='垂类 (stock, finance, tech, beauty)')
    parser.add_argument('topic', help='话题/主题')
    parser.add_argument('--action', choices=['all', 'content', 'cover', 'info', 'init'],
                        default='all', help='执行动作 (默认: all)')
    parser.add_argument('--session-dir', help='指定 session 目录')
    parser.add_argument('--max-retries', type=int, default=3,
                        help='内容生成最大重试次数 (默认: 3)')

    args = parser.parse_args()

    # 初始化流水线
    pipeline = Pipeline(skill_dir=SCRIPT_DIR)

    # 获取或创建 session
    if args.session_dir:
        session = pipeline.load_session(Path(args.session_dir))
    elif args.action == 'init':
        session = pipeline.create_session(args.vertical, args.topic)
        print(f"# ✓ Session created: {session.session_dir}")
        return 0
    else:
        session = pipeline.get_or_create_session(args.vertical, args.topic)
        # 更新 vertical（如果是复用的 session）
        if session.vertical != args.vertical:
            session._data['vertical'] = args.vertical
            session._save()

    print(f"# Session: {session.session_dir}")

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
