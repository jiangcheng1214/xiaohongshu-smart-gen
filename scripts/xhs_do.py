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

# 添加 scripts 目录到 Python 路径
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(scripts_dir))

from xhs_cli.cli import main_do

if __name__ == "__main__":
    sys.exit(main_do())
