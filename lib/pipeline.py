#!/usr/bin/env python3
"""
小红书内容生成 - 流水线管理

协调 7 步流水线的执行流程。
"""

import sys
from pathlib import Path
from typing import Optional

from session import XhsSession
from steps import (
    Step1Research,
    Step2Generate,
    Step3Validate,
    Step4PrepareImg,
    Step4aValidateStockData,
    Step5GenImg,
    Step6Overlay,
    Step7Deliver
)


class Pipeline:
    """
    小红书内容生成 7 步流水线

    Steps:
        1. Research    - 搜索数据
        2. Generate    - 生成内容
        3. Validate    - 验证内容
        4. PrepareImg  - 准备封面变量
        5. GenImg      - 生成封面图
        6. Overlay     - 添加 Logo
        7. Deliver     - 发送到 Telegram
    """

    def __init__(self, skill_dir: Optional[Path] = None,
                 workspace: Optional[Path] = None):
        """
        初始化流水线

        Args:
            skill_dir: 技能根目录
            workspace: 工作空间目录
        """
        self.skill_dir = skill_dir or Path(__file__).parent.parent
        self.workspace = workspace or Path.home() / ".openclaw" / "agents" / "main" / "agent"

        # 初始化步骤
        self.step1 = Step1Research(self.skill_dir)
        self.step2 = Step2Generate(self.skill_dir)
        self.step3 = Step3Validate(self.skill_dir)
        self.step4 = Step4PrepareImg(self.skill_dir)
        self.step4a = Step4aValidateStockData(self.skill_dir)
        self.step5 = Step5GenImg(self.skill_dir)
        self.step6 = Step6Overlay(self.skill_dir)
        self.step7 = Step7Deliver(self.skill_dir)

    def create_session(self, vertical: str, topic: str) -> XhsSession:
        """
        创建新 session

        Args:
            vertical: 垂类
            topic: 话题

        Returns:
            XhsSession 实例
        """
        session = XhsSession(workspace=self.workspace)
        session.create(vertical, topic)
        return session

    def get_or_create_session(self, vertical: str, topic: str) -> XhsSession:
        """
        获取现有 session 或创建新的

        Args:
            vertical: 垂类
            topic: 话题

        Returns:
            XhsSession 实例
        """
        existing = XhsSession.find_existing(topic, self.workspace)
        if existing:
            session = XhsSession(workspace=self.workspace)
            session.load(existing)
            return session

        return self.create_session(vertical, topic)

    def load_session(self, session_dir: Path) -> XhsSession:
        """
        加载现有 session

        Args:
            session_dir: Session 目录路径

        Returns:
            XhsSession 实例
        """
        session = XhsSession(workspace=self.workspace)
        session.load(session_dir)
        return session

    def run_content_pipeline(self, session: XhsSession,
                            max_retries: int = 3) -> bool:
        """
        运行内容生成流水线（步骤 1-3）

        Args:
            session: XhsSession 实例
            max_retries: 最大重试次数

        Returns:
            bool: 是否成功完成
        """
        retry_count = 0
        feedback = ""

        while retry_count < max_retries:
            print(f"# --- 内容生成循环 ({retry_count + 1}/{max_retries}) ---")

            # Step 1: 搜索
            print("# Step 1: 搜索数据")
            if not self.step1.run(session):
                retry_count += 1
                continue

            # Step 2: 生成
            print("# Step 2: 生成内容")
            success, error = self.step2.run(session, feedback=feedback)
            if not success:
                retry_count += 1
                feedback = error
                continue

            # Step 3: 验证
            print("# Step 3: 验证内容")
            passed, feedback = self.step3.run(session)
            if passed:
                print("# ✓ 验证通过")
                return True

            retry_count += 1
            print(f"# ✗ 验证未通过 ({retry_count}/{max_retries}): {feedback}")

        return False

    def run_cover_pipeline(self, session: XhsSession) -> bool:
        """
        运行封面生成流水线（步骤 4-6）

        Args:
            session: XhsSession 实例

        Returns:
            bool: 是否成功完成
        """
        print("# Step 4: 收集封面变量")
        if not self.step4.run(session):
            return False

        # Step 4a: 验证股票数据（仅 stock 垂类）
        if session.vertical == 'stock':
            print("# Step 4a: 验证股票数据")
            self.step4a.run(session)

        print("# Step 5: 生成封面图片")
        if not self.step5.run(session):
            return False

        print("# Step 6: 添加 Logo")
        if not self.step6.run(session):
            return False

        return True

    def run_delivery(self, session: XhsSession) -> bool:
        """
        运行发送步骤（步骤 7）

        Args:
            session: XhsSession 实例

        Returns:
            bool: 是否成功完成
        """
        print("# Step 7: 发送到 Telegram")
        return self.step7.run(session)

    def run_all(self, session: XhsSession, max_retries: int = 3) -> bool:
        """
        运行完整流水线（步骤 1-7）

        Args:
            session: XhsSession 实例
            max_retries: 内容生成最大重试次数

        Returns:
            bool: 是否成功完成
        """
        print("\n========================================")
        print("小红书内容生成 - 7步流水线")
        print("========================================\n")

        # 步骤 1-3: 内容生成
        print("步骤 1-3: 内容生成 + 验证")
        if not self.run_content_pipeline(session, max_retries):
            print("✗ 内容生成失败")
            return False

        print("\n步骤 4-6: 封面生成")
        if not self.run_cover_pipeline(session):
            print("⚠ 封面生成失败，继续发送文字")

        print("\n步骤 7: 发送到 Telegram")
        self.run_delivery(session)

        session.update_status('completed')

        print("\n✓ 全部完成！")
        return True
