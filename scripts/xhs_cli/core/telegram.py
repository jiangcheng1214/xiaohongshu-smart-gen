"""
Telegram 发送模块 - 跨平台实现
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional

import requests


class TelegramSender:
    """Telegram 发送器 (跨平台)"""

    def __init__(self, config):
        self.config = config
        self.bot_token = config.get_telegram_bot_token()
        self.chat_id = self._get_chat_id()

    def _get_chat_id(self) -> Optional[str]:
        """获取 Telegram Chat ID"""
        # 1. 环境变量
        if chat_id := os.environ.get("TELEGRAM_CHAT_ID"):
            return chat_id

        # 2. 从 openclaw sessions 获取
        try:
            result = subprocess.run(
                ["openclaw", "sessions", "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # 解析 JSON 输出
                for line in result.stdout.split('\n'):
                    if line.strip().startswith('{'):
                        data = json.loads(line)
                        if sessions := data.get("sessions", []):
                            # 查找 telegram:direct 类型的 session
                            for s in sessions:
                                if "telegram:direct" in s.get("key", ""):
                                    key_parts = s["key"].split(":")
                                    if key_parts:
                                        return key_parts[-1]
        except (subprocess.SubprocessError, json.JSONDecodeError, FileNotFoundError):
            pass

        # 3. 默认值
        return "6167775207"

    def _prepare_export_dir(self, session_dir: Path, title: str) -> Path:
        """准备导出目录"""
        export_dir = self.config.get_export_dir(title)
        export_dir.mkdir(parents=True, exist_ok=True)

        # 复制内容文件
        content_file = session_dir / "content.md"
        if content_file.exists():
            shutil.copy(content_file, export_dir / "content.md")

        # 复制封面
        cover_file = session_dir / "cover.png"
        if cover_file.exists():
            shutil.copy(cover_file, export_dir / "cover.png")

        # 复制参考图
        images_dir = session_dir / "images"
        if images_dir.exists():
            for img in images_dir.iterdir():
                if img.is_file():
                    shutil.copy(img, export_dir / img.name)

        return export_dir

    def _sanitize_caption(self, text: str, max_length: int = 1024) -> str:
        """清理 caption 文本 (Telegram 限制)"""
        # Telegram caption 限制 1024 字符
        if len(text) > max_length:
            return text[:max_length - 3] + "..."
        return text

    def send_photo(self, photo_path: Path, caption: str) -> bool:
        """发送照片到 Telegram"""
        if not self.bot_token or not self.chat_id:
            print("# ⚠️ Telegram 配置不完整，跳过发送", file=__import__("sys").stderr)
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            with open(photo_path, "rb") as f:
                files = {"photo": f}
                data = {
                    "chat_id": self.chat_id,
                    "caption": self._sanitize_caption(caption)
                }
                response = requests.post(url, files=files, data=data, timeout=30)
                response.raise_for_status()
            return True
        except Exception as e:
            print(f"# ✗ Telegram 发送失败: {e}", file=__import__("sys").stderr)
            return False

    def send_message(self, text: str) -> bool:
        """发送纯文本消息到 Telegram"""
        if not self.bot_token or not self.chat_id:
            print("# ⚠️ Telegram 配置不完整，跳过发送", file=__import__("sys").stderr)
            return False

        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text
            }
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"# ✗ Telegram 发送失败: {e}", file=__import__("sys").stderr)
            return False

    def send_session(self, session_dir: Path, title: str, content: str) -> bool:
        """发送 session 内容到 Telegram

        Args:
            session_dir: session 目录路径
            title: 标题
            content: 内容文本

        Returns:
            bool: 发送是否成功
        """
        import sys

        # 准备导出目录
        export_dir = self._prepare_export_dir(session_dir, title)
        print(f"# 文件已整理至: {export_dir}", file=sys.stderr)

        # 发送
        cover_path = export_dir / "cover.png"
        if cover_path.exists():
            print(f"# 正在发送图文到 Telegram...", file=sys.stderr)
            success = self.send_photo(cover_path, content)
        else:
            print(f"# 警告: 封面不存在，仅发送文字", file=sys.stderr)
            success = self.send_message(content)

        if success:
            print(f"# ✓ Telegram 发送完成！", file=sys.stderr)
        return success
