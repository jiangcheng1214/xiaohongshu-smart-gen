#!/usr/bin/env python3
"""
测试运行脚本
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_tests(coverage=False, verbose=False, pattern=None, marker=None):
    """运行测试套件"""
    project_root = Path(__file__).parent

    # 构建 pytest 命令
    cmd = ["python", "-m", "pytest"]

    # 添加详细输出
    if verbose:
        cmd.append("-vv")
    else:
        cmd.append("-v")

    # 添加覆盖率
    if coverage:
        cmd.extend([
            "--cov=scripts",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-fail-under=80"
        ])

    # 添加测试模式
    if pattern:
        cmd.extend(["-k", pattern])

    # 添加标记
    if marker:
        cmd.extend(["-m", marker])

    # 添加测试目录
    cmd.append(str(project_root / "tests"))

    # 运行测试
    print(f"运行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=project_root)

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="运行 xiaohongshu-smart-gen 测试套件")
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="生成测试覆盖率报告"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    parser.add_argument(
        "--pattern", "-k",
        help="运行匹配模式的测试"
    )
    parser.add_argument(
        "--marker", "-m",
        help="按标记运行测试"
    )

    args = parser.parse_args()

    exit_code = run_tests(
        coverage=args.coverage,
        verbose=args.verbose,
        pattern=args.pattern,
        marker=args.marker
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
