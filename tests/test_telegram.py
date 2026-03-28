"""
Telegram 发送模块测试
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open

from scripts.xhs_cli.config import Config
from scripts.xhs_cli.core.telegram import TelegramSender


class TestTelegramSender(unittest.TestCase):
    """测试 TelegramSender 类"""

    def setUp(self):
        """每个测试前设置环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.workspace = Path(self.temp_dir) / "workspace"
        self.workspace.mkdir()

        # 清除环境变量
        os.environ.pop("TELEGRAM_CHAT_ID", None)
        os.environ.pop("TELEGRAM_BOT_TOKEN", None)

    def tearDown(self):
        """每个测试后清理"""
        shutil.rmtree(self.temp_dir)

    def _create_config(self):
        """创建测试配置"""
        with patch('scripts.xhs_cli.config.Config.get_workspace', return_value=self.workspace):
            return Config()

    def _create_sender(self, bot_token="test_token_123"):
        """创建测试用的 TelegramSender"""
        config = self._create_config()
        with patch.object(config, 'get_telegram_bot_token', return_value=bot_token):
            return TelegramSender(config)

    def _create_session_files(self, session_dir):
        """创建 session 测试文件"""
        session_dir.mkdir(parents=True, exist_ok=True)

        # 创建 content.md
        content_file = session_dir / "content.md"
        content_file.write_text("# 测试标题\n\n这是测试内容", encoding="utf-8")

        # 创建 cover.png
        cover_file = session_dir / "cover.png"
        cover_file.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)  # 简单的 PNG

        # 创建 images 目录
        images_dir = session_dir / "images"
        images_dir.mkdir()
        (images_dir / "image_0.jpg").write_bytes(b"fake image")

        return session_dir

    def test_get_chat_id_from_env(self):
        """测试从环境变量获取 Chat ID"""
        test_chat_id = "123456789"
        with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": test_chat_id}):
            sender = self._create_sender()
            self.assertEqual(sender.chat_id, test_chat_id)

    @patch('scripts.xhs_cli.core.telegram.subprocess.run')
    def test_get_chat_id_from_openclaw(self, mock_run):
        """测试从 openclaw sessions 获取 Chat ID"""
        # Mock openclaw 命令返回
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = json.dumps({
            "sessions": [
                {"key": "telegram:direct:987654321"}
            ]
        })
        mock_run.return_value = mock_result

        sender = self._create_sender()
        # 环境变量未设置，应从 openclaw 获取
        self.assertEqual(sender.chat_id, "987654321")

    @patch('scripts.xhs_cli.core.telegram.subprocess.run')
    def test_get_chat_id_openclaw_failure(self, mock_run):
        """测试 openclaw 命令失败时使用默认值"""
        mock_run.side_effect = FileNotFoundError()

        sender = self._create_sender()
        self.assertEqual(sender.chat_id, "6167775207")  # 默认值

    @patch('scripts.xhs_cli.core.telegram.subprocess.run')
    def test_get_chat_id_openclaw_timeout(self, mock_run):
        """测试 openclaw 命令超时时使用默认值"""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("openclaw", 5)

        sender = self._create_sender()
        self.assertEqual(sender.chat_id, "6167775207")

    @patch('scripts.xhs_cli.core.telegram.subprocess.run')
    def test_get_chat_id_openclaw_invalid_json(self, mock_run):
        """测试 openclaw 返回无效 JSON 时使用默认值"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "invalid json"
        mock_run.return_value = mock_result

        sender = self._create_sender()
        self.assertEqual(sender.chat_id, "6167775207")

    def test_init_without_bot_token(self):
        """测试没有 bot token 的初始化"""
        sender = self._create_sender(bot_token=None)
        self.assertIsNone(sender.bot_token)

    def test_sanitize_caption_short_text(self):
        """测试短文本不需要截断"""
        sender = self._create_sender()
        text = "短文本"
        result = sender._sanitize_caption(text)
        self.assertEqual(result, text)

    def test_sanitize_caption_long_text(self):
        """测试长文本截断"""
        sender = self._create_sender()
        # 创建超过 1024 字符的文本
        long_text = "a" * 2000
        result = sender._sanitize_caption(long_text, max_length=1024)
        self.assertEqual(len(result), 1024)
        self.assertTrue(result.endswith("..."))

    def test_sanitize_caption_exact_limit(self):
        """测试正好等于限制的文本"""
        sender = self._create_sender()
        text = "a" * 1024
        result = sender._sanitize_caption(text, max_length=1024)
        self.assertEqual(len(result), 1024)
        # 不应该添加 ...
        self.assertFalse(result.endswith("..."))

    def test_prepare_export_dir(self):
        """测试准备导出目录"""
        sender = self._create_sender()
        session_dir = Path(self.temp_dir) / "test_session"
        self._create_session_files(session_dir)

        with patch.object(sender.config, 'get_export_dir', return_value=Path(self.temp_dir) / "export"):
            export_dir = sender._prepare_export_dir(session_dir, "测试标题")

            # 验证目录已创建
            self.assertTrue(export_dir.exists())

            # 验证文件已复制
            self.assertTrue((export_dir / "content.md").exists())
            self.assertTrue((export_dir / "cover.png").exists())
            self.assertTrue((export_dir / "image_0.jpg").exists())

    def test_prepare_export_dir_partial_files(self):
        """测试部分文件缺失时的导出目录准备"""
        sender = self._create_sender()
        session_dir = Path(self.temp_dir) / "test_session_partial"
        session_dir.mkdir(parents=True, exist_ok=True)

        # 只创建 content.md
        (session_dir / "content.md").write_text("# 内容")

        with patch.object(sender.config, 'get_export_dir', return_value=Path(self.temp_dir) / "export_partial"):
            export_dir = sender._prepare_export_dir(session_dir, "测试标题")

            # content.md 应该存在
            self.assertTrue((export_dir / "content.md").exists())
            # cover.png 不应该存在
            self.assertFalse((export_dir / "cover.png").exists())

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_photo_success(self, mock_post):
        """测试发送照片成功"""
        sender = self._create_sender()

        # Mock 成功响应
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        photo_path = Path(self.temp_dir) / "test.jpg"
        photo_path.write_bytes(b"fake photo")

        result = sender.send_photo(photo_path, "测试说明")

        self.assertTrue(result)
        mock_post.assert_called_once()

        # 验证请求参数
        call_args = mock_post.call_args
        self.assertIn("chat_id", call_args[1]["data"])
        self.assertIn("caption", call_args[1]["data"])
        self.assertIn("photo", call_args[1]["files"])

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_photo_no_token(self, mock_post):
        """测试没有 token 时跳过发送"""
        sender = self._create_sender(bot_token=None)

        photo_path = Path(self.temp_dir) / "test.jpg"
        photo_path.write_bytes(b"fake photo")

        result = sender.send_photo(photo_path, "说明")

        self.assertFalse(result)
        mock_post.assert_not_called()

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_photo_no_chat_id(self, mock_post):
        """测试没有 chat_id 时跳过发送"""
        sender = self._create_sender()
        sender.chat_id = None

        photo_path = Path(self.temp_dir) / "test.jpg"
        photo_path.write_bytes(b"fake photo")

        result = sender.send_photo(photo_path, "说明")

        self.assertFalse(result)
        mock_post.assert_not_called()

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_photo_http_error(self, mock_post):
        """测试 HTTP 错误"""
        sender = self._create_sender()

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 400")
        mock_post.return_value = mock_response

        photo_path = Path(self.temp_dir) / "test.jpg"
        photo_path.write_bytes(b"fake photo")

        result = sender.send_photo(photo_path, "说明")

        self.assertFalse(result)

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_photo_timeout(self, mock_post):
        """测试发送超时"""
        sender = self._create_sender()

        mock_post.side_effect = Exception("Timeout")

        photo_path = Path(self.temp_dir) / "test.jpg"
        photo_path.write_bytes(b"fake photo")

        result = sender.send_photo(photo_path, "说明")

        self.assertFalse(result)

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_photo_sanitizes_caption(self, mock_post):
        """测试发送照片时清理 caption"""
        sender = self._create_sender()

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        photo_path = Path(self.temp_dir) / "test.jpg"
        photo_path.write_bytes(b"fake photo")

        # 发送超长 caption
        long_caption = "a" * 2000
        sender.send_photo(photo_path, long_caption)

        # 验证 caption 被截断
        call_args = mock_post.call_args
        sent_caption = call_args[1]["data"]["caption"]
        self.assertLessEqual(len(sent_caption), 1024)

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_message_success(self, mock_post):
        """测试发送消息成功"""
        sender = self._create_sender()

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = sender.send_message("测试消息")

        self.assertTrue(result)
        mock_post.assert_called_once()

        # 验证请求参数
        call_args = mock_post.call_args
        self.assertEqual(call_args[1]["json"]["text"], "测试消息")
        self.assertIn("chat_id", call_args[1]["json"])

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_message_no_config(self, mock_post):
        """测试没有配置时跳过发送"""
        sender = self._create_sender(bot_token=None)

        result = sender.send_message("消息")

        self.assertFalse(result)
        mock_post.assert_not_called()

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_message_http_error(self, mock_post):
        """测试发送消息 HTTP 错误"""
        sender = self._create_sender()

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("HTTP 400")
        mock_post.return_value = mock_response

        result = sender.send_message("消息")

        self.assertFalse(result)

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_session_with_cover(self, mock_post):
        """测试发送完整 session（有封面）"""
        sender = self._create_sender()

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        session_dir = Path(self.temp_dir) / "test_session"
        self._create_session_files(session_dir)

        with patch.object(sender.config, 'get_export_dir', return_value=Path(self.temp_dir) / "export"):
            result = sender.send_session(session_dir, "测试标题", "测试内容")

        self.assertTrue(result)
        # 应该调用 send_photo
        self.assertEqual(mock_post.call_count, 1)

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_session_without_cover(self, mock_post):
        """测试发送 session（无封面，仅文字）"""
        sender = self._create_sender()

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        session_dir = Path(self.temp_dir) / "test_session_no_cover"
        session_dir.mkdir(parents=True, exist_ok=True)
        # 只创建 content.md，不创建 cover.png
        (session_dir / "content.md").write_text("# 内容")

        with patch.object(sender.config, 'get_export_dir', return_value=Path(self.temp_dir) / "export_no_cover"):
            result = sender.send_session(session_dir, "测试标题", "测试内容")

        self.assertTrue(result)
        # 应该调用 send_message 而不是 send_photo
        # 验证 URL 包含 sendMessage 而不是 sendPhoto
        call_args = mock_post.call_args
        url = call_args[0][0]
        self.assertIn("sendMessage", url)

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_session_failure(self, mock_post):
        """测试发送 session 失败"""
        sender = self._create_sender()

        mock_post.side_effect = Exception("Network error")

        session_dir = Path(self.temp_dir) / "test_session_fail"
        self._create_session_files(session_dir)

        with patch.object(sender.config, 'get_export_dir', return_value=Path(self.temp_dir) / "export_fail"):
            result = sender.send_session(session_dir, "测试标题", "测试内容")

        self.assertFalse(result)

    def test_send_session_creates_export_dir(self):
        """测试发送 session 时创建导出目录"""
        sender = self._create_sender()

        with patch('scripts.xhs_cli.core.telegram.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            session_dir = Path(self.temp_dir) / "test_session_export"
            self._create_session_files(session_dir)

            export_base = Path(self.temp_dir) / "exports"
            with patch.object(sender.config, 'get_export_dir', return_value=export_base):
                sender.send_session(session_dir, "测试标题", "测试内容")

            # 验证导出目录已创建
            self.assertTrue(export_base.exists())

    @patch('scripts.xhs_cli.core.telegram.requests.post')
    def test_send_session_with_images(self, mock_post):
        """测试发送包含参考图的 session"""
        sender = self._create_sender()

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        session_dir = Path(self.temp_dir) / "test_session_images"
        session_dir = self._create_session_files(session_dir)

        # 添加更多图片
        images_dir = session_dir / "images"
        for i in range(3):
            (images_dir / f"ref_{i}.jpg").write_bytes(b"ref image")

        with patch.object(sender.config, 'get_export_dir', return_value=Path(self.temp_dir) / "export_images"):
            sender.send_session(session_dir, "测试标题", "测试内容")

        # 验证导出目录包含所有图片
        export_dir = Path(self.temp_dir) / "export_images"
        self.assertTrue((export_dir / "image_0.jpg").exists())
        self.assertTrue((export_dir / "ref_0.jpg").exists())
        self.assertTrue((export_dir / "ref_1.jpg").exists())
        self.assertTrue((export_dir / "ref_2.jpg").exists())


if __name__ == '__main__':
    unittest.main()
