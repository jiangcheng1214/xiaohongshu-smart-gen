#!/usr/bin/env python3
"""
xhs-do - 跨平台小红书内容生成入口
确定性执行命令，绕过 AI 解析

用法:
    python xhs_do.py <垂类> "<话题>" [action]

示例:
    python xhs_do.py finance "错过了lite怎么办"
    python xhs_do.py beauty "雅诗兰黛DW值得买吗" --send
"""

import sys
from pathlib import Path

# 获取技能目录
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "lib"))

from pipeline import Pipeline

def main():
    if len(sys.argv) < 3:
        print("用法: xhs_do <垂类> <话题> [action]", file=sys.stderr)
        print("Actions: init, content, cover, info, all", file=sys.stderr)
        sys.exit(1)

    vertical = sys.argv[1]
    topic = sys.argv[2]
    action = sys.argv[3] if len(sys.argv) > 3 else "all"

    # 映射 action 到 Pipeline 的方法
    action_map = {
        "init": "init",
        "content": "content",
        "cover": "cover",
        "info": "info",
        "all": "all"
    }

    if action not in action_map:
        print(f"未知 action: {action}", file=sys.stderr)
        sys.exit(1)

    # 初始化流水线
    pipeline = Pipeline(skill_dir=SKILL_DIR)

    # 执行
    if action == "init":
        session = pipeline.create_session(vertical, topic)
        print(f"Session created: {session.session_dir}")
        return 0
    elif action == "info":
        session = pipeline.get_or_create_session(vertical, topic)
        # 确保使用正确的 vertical
        session._data['vertical'] = vertical
        session._save()

        print(f"# Session ID: {session.session_id}")
        print(f"# Status: {session.status}")
        print(f"# Vertical: {session.vertical}")
        print(f"# Topic: {session.topic}")
        print(f"# Directory: {session.session_dir}")
        return 0
    elif action == "content":
        session = pipeline.get_or_create_session(vertical, topic)
        session._data['vertical'] = vertical
        session._save()
        success = pipeline.run_content_pipeline(session)
        return 0 if success else 1
    elif action == "cover":
        session = pipeline.get_or_create_session(vertical, topic)
        session._data['vertical'] = vertical
        session._save()
        success = pipeline.run_cover_pipeline(session)
        return 0 if success else 1
    else:  # all
        session = pipeline.get_or_create_session(vertical, topic)
        # 确保使用正确的 vertical
        session._data['vertical'] = vertical
        session._save()
        success = pipeline.run_all(session)
        return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
