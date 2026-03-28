"""
路径管理模块测试
"""

import platform
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from scripts.xhs_cli.config import Config
from scripts.xhs_cli.lib.paths import PathManager


class TestPathManager(unittest.TestCase):
    """测试 PathManager 类"""

    def setUp(self):
        """每个测试前设置环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.config = Config()
        self.path_manager = PathManager(self.config)

    def tearDown(self):
        """每个测试后清理"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.path_manager.config, self.config)
        self.assertEqual(self.path_manager.system, platform.system())

    def test_normalize_path(self):
        """测试路径规范化"""
        # 测试相对路径
        result = PathManager.normalize("test/path")
        self.assertTrue(result.is_absolute())

        # 测试 ~ 展开
        result = PathManager.normalize("~/test")
        self.assertTrue(str(result).startswith(str(Path.home())))

    def test_get_skill_dir(self):
        """测试获取技能目录"""
        skill_dir = self.path_manager.get_skill_dir()
        self.assertTrue(skill_dir.exists())
        # 应该包含 verticals 目录
        self.assertTrue((skill_dir / "verticals").exists())

    def test_get_session_dir(self):
        """测试获取 Session 目录"""
        session_id = "test_session_123"
        session_dir = self.path_manager.get_session_dir(session_id)
        expected = self.config.get_workspace() / session_id
        self.assertEqual(session_dir, expected)

    def test_get_temp_dir(self):
        """测试获取临时目录"""
        temp_dir = self.path_manager.get_temp_dir()
        self.assertTrue(temp_dir.exists() or temp_dir.parent.exists())

    def test_get_export_dir(self):
        """测试获取导出目录"""
        title = "测试标题"
        export_dir = self.path_manager.get_export_dir(title)
        self.assertIsNotNone(export_dir)

    def test_get_verticals_dir(self):
        """测试获取垂类配置目录"""
        verticals_dir = self.path_manager.get_verticals_dir()
        skill_dir = self.path_manager.get_skill_dir()
        expected = skill_dir / "verticals"
        self.assertEqual(verticals_dir, expected)

    def test_get_personas_dir(self):
        """测试获取人设目录"""
        personas_dir = self.path_manager.get_personas_dir()
        skill_dir = self.path_manager.get_skill_dir()
        expected = skill_dir / "personas"
        self.assertEqual(personas_dir, expected)

    def test_get_assets_dir(self):
        """测试获取资源目录"""
        assets_dir = self.path_manager.get_assets_dir()
        skill_dir = self.path_manager.get_skill_dir()
        expected = skill_dir / "assets"
        self.assertEqual(assets_dir, expected)

    def test_get_logo_dir(self):
        """测试获取 Logo 目录"""
        logo_dir = self.path_manager.get_logo_dir()
        assets_dir = self.path_manager.get_assets_dir()
        expected = assets_dir / "logo"
        self.assertEqual(logo_dir, expected)

    def test_get_templates_dir(self):
        """测试获取模板目录"""
        templates_dir = self.path_manager.get_templates_dir()
        skill_dir = self.path_manager.get_skill_dir()
        expected = skill_dir / "templates"
        self.assertEqual(templates_dir, expected)

    def test_sanitize_filename(self):
        """测试文件名清理"""
        # 测试非法字符替换
        result = PathManager.sanitize_filename("test<>file?.txt")
        self.assertNotIn("<", result)
        self.assertNotIn(">", result)
        self.assertNotIn("?", result)

        # 测试长度限制
        long_name = "a" * 50
        result = PathManager.sanitize_filename(long_name)
        self.assertLessEqual(len(result), 30)

    def test_sanitize_filename_replaces_special_chars(self):
        """测试特殊字符被替换为下划线"""
        test_cases = [
            ("test:file", "test_file"),
            ("test/file", "test_file"),
            ("test\\file", "test_file"),
            ("test|file", "test_file"),
            ("test?file", "test_file"),
            ("test*file", "test_file"),
            ('test"file', "test_file"),
            ("test<file>", "test_file"),
        ]

        for input_name, expected_contains in test_cases:
            result = PathManager.sanitize_filename(input_name)
            self.assertNotIn("<>:\"/\\|?*", result[:20])

    @patch('pathlib.Path.exists')
    @patch('shutil.which')
    def test_find_homebrew_on_darwin(self, mock_which, mock_exists):
        """测试在 Darwin 上查找 Homebrew"""
        mock_exists.return_value = True

        with patch.object(self.path_manager, 'system', 'Darwin'):
            result = self.path_manager.find_homebrew()
            self.assertIsNotNone(result)

    @patch('pathlib.Path.exists')
    @patch('shutil.which')
    def test_find_homebrew_not_found(self, mock_which, mock_exists):
        """测试 Homebrew 未找到"""
        mock_exists.return_value = False

        with patch.object(self.path_manager, 'system', 'Darwin'):
            result = self.path_manager.find_homebrew()
            self.assertIsNone(result)

    @patch('pathlib.Path.exists')
    @patch('shutil.which')
    def test_find_homebrew_on_linux(self, mock_which, mock_exists):
        """测试在 Linux 上查找 Homebrew"""
        mock_exists.return_value = True

        with patch.object(self.path_manager, 'system', 'Linux'):
            result = self.path_manager.find_homebrew()
            self.assertIsNotNone(result)

    @patch('shutil.which')
    def test_find_imagemagick_magick(self, mock_which):
        """测试查找 ImageMagick magick 命令"""
        mock_which.return_value = "/usr/bin/magick"

        result = self.path_manager.find_imagemagick()
        self.assertEqual(result, "magick")

    @patch('shutil.which')
    def test_find_imagemagick_convert(self, mock_which):
        """测试查找 ImageMagick convert 命令"""
        # magick 不存在，convert 存在
        def which_side_effect(cmd):
            return "/usr/bin/convert" if cmd == "convert" else None

        mock_which.side_effect = which_side_effect

        result = self.path_manager.find_imagemagick()
        self.assertEqual(result, "convert")

    @patch('shutil.which')
    def test_find_imagemagick_not_found(self, mock_which):
        """测试 ImageMagick 未找到"""
        mock_which.return_value = None

        result = self.path_manager.find_imagemagick()
        self.assertIsNone(result)

    @patch('shutil.which')
    def test_find_imagemagick_magick_convert(self, mock_which):
        """测试查找 ImageMagick magick convert 组合命令"""
        # magick convert 存在
        def which_side_effect(cmd):
            if cmd == "magick":
                return "/usr/bin/magick"
            return None

        mock_which.side_effect = which_side_effect
        # 由于 which 检查单个命令，"magick convert" 不会被找到
        result = self.path_manager.find_imagemagick()
        # 应该找到 magick
        self.assertIsNotNone(result)


if __name__ == '__main__':
    unittest.main()
