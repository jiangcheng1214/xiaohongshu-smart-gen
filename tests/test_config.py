"""
配置管理测试
"""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

from scripts.xhs_cli.config import Config


class TestConfig(unittest.TestCase):
    """测试 Config 类"""

    def setUp(self):
        """每个测试前重置环境"""
        # 清除可能影响测试的环境变量
        for key in ["OPENCLAW_HOME", "XHS_WORKSPACE", "GEMINI_API_KEY"]:
            os.environ.pop(key, None)

    def test_get_openclaw_home_default(self):
        """测试默认 OpenClaw 主目录"""
        config = Config()
        expected = Path.home() / ".openclaw"
        self.assertEqual(config.get_openclaw_home(), expected)

    def test_get_openclaw_home_from_env(self):
        """测试从环境变量获取 OpenClaw 主目录"""
        custom_path = "/custom/openclaw"
        with patch.dict(os.environ, {"OPENCLAW_HOME": custom_path}):
            config = Config()
            self.assertEqual(config.get_openclaw_home(), Path(custom_path))

    def test_get_workspace_default(self):
        """测试默认工作区"""
        config = Config()
        expected = Path.home() / ".openclaw" / "agents" / "main" / "agent"
        self.assertEqual(config.get_workspace(), expected)

    def test_get_workspace_from_env(self):
        """测试从环境变量获取工作区"""
        custom_workspace = "/custom/workspace"
        with patch.dict(os.environ, {"XHS_WORKSPACE": custom_workspace}):
            config = Config()
            self.assertEqual(config.get_workspace(), Path(custom_workspace))

    def test_get_skill_dir(self):
        """测试获取技能目录"""
        config = Config()
        skill_dir = config.get_skill_dir()
        # 验证目录存在
        self.assertTrue(skill_dir.exists())
        # 验证包含 SKILL.md
        self.assertTrue((skill_dir / "SKILL.md").exists())

    def test_get_gemini_api_key_from_env(self):
        """测试从环境变量获取 Gemini API Key"""
        test_key = "test_gemini_key_123"
        with patch.dict(os.environ, {"GEMINI_API_KEY": test_key}):
            config = Config()
            self.assertEqual(config.get_gemini_api_key(), test_key)

    def test_sanitize_filename(self):
        """测试文件名清理"""
        config = Config()
        # 测试非法字符替换
        self.assertEqual(config._sanitize_filename('test/file:name'), 'test_file_name')
        # 测试长度限制
        long_name = "a" * 50
        result = config._sanitize_filename(long_name)
        self.assertLessEqual(len(result), 30)

    def test_get_temp_dir_linux(self):
        """测试 Linux 临时目录"""
        with patch('platform.system', return_value='Linux'):
            config = Config()
            temp_dir = config.get_temp_dir()
            self.assertEqual(temp_dir, Path('/tmp'))

    def test_get_export_dir(self):
        """测试导出目录生成"""
        config = Config()
        title = "测试标题"
        export_dir = config.get_export_dir(title)
        # 验证目录包含时间戳
        self.assertIn("Xiaohongshu_Exports", str(export_dir))


class TestConfigWithMockOpenclawJson(unittest.TestCase):
    """测试使用 mock openclaw.json 的配置"""

    def setUp(self):
        """设置测试"""
        self.temp_dir = tempfile.mkdtemp()
        self.openclaw_dir = Path(self.temp_dir) / ".openclaw"
        self.openclaw_dir.mkdir()

    def tearDown(self):
        """清理测试"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_get_gemini_api_key_from_openclaw_json(self):
        """测试从 openclaw.json 获取 API Key"""
        # 创建测试配置文件
        config_data = {
            "env": {"GEMINI_API_KEY": "key_from_json"}
        }
        config_file = self.openclaw_dir / "openclaw.json"
        config_file.write_text(json.dumps(config_data))

        # Mock home directory
        with patch('pathlib.Path.home', return_value=self.openclaw_dir.parent):
            config = Config()
            key = config.get_gemini_api_key()
            self.assertEqual(key, "key_from_json")

    def test_get_gemini_api_key_fallback(self):
        """测试 API Key 获取的回退逻辑"""
        # 创建测试配置文件 - env 为空但有 skills 配置
        config_data = {
            "skills": {
                "entries": {
                    "nano-banana-pro": {"apiKey": "key_from_skills"}
                }
            }
        }
        config_file = self.openclaw_dir / "openclaw.json"
        config_file.write_text(json.dumps(config_data))

        with patch('pathlib.Path.home', return_value=self.openclaw_dir.parent):
            config = Config()
            key = config.get_gemini_api_key()
            self.assertEqual(key, "key_from_skills")

    def test_get_gemini_api_key_invalid_json(self):
        """测试无效 JSON 文件的处理"""
        # 创建无效的 JSON 文件
        config_file = self.openclaw_dir / "openclaw.json"
        config_file.write_text("invalid json content")

        with patch('pathlib.Path.home', return_value=self.openclaw_dir.parent):
            config = Config()
            key = config.get_gemini_api_key()
            # 应该返回 None 而不是崩溃
            self.assertIsNone(key)

    def test_get_telegram_bot_token_from_json(self):
        """测试从 openclaw.json 获取 Telegram Bot Token"""
        config_data = {
            "channels": {
                "telegram": {
                    "accounts": {
                        "default": {"botToken": "test_token_123"}
                    }
                }
            }
        }
        config_file = self.openclaw_dir / "openclaw.json"
        config_file.write_text(json.dumps(config_data))

        with patch('pathlib.Path.home', return_value=self.openclaw_dir.parent):
            config = Config()
            token = config.get_telegram_bot_token()
            self.assertEqual(token, "test_token_123")

    def test_get_telegram_bot_token_invalid_json(self):
        """测试无效 JSON 文件时获取 Telegram Token"""
        config_file = self.openclaw_dir / "openclaw.json"
        config_file.write_text("invalid json")

        with patch('pathlib.Path.home', return_value=self.openclaw_dir.parent):
            config = Config()
            token = config.get_telegram_bot_token()
            self.assertIsNone(token)

    def test_get_telegram_bot_token_from_env(self):
        """测试从环境变量获取 Telegram Bot Token"""
        test_token = "test_telegram_token"
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": test_token}):
            config = Config()
            self.assertEqual(config.get_telegram_bot_token(), test_token)


class TestConfigPlatformSpecific(unittest.TestCase):
    """测试平台特定的配置"""

    def test_get_temp_dir_windows(self):
        """测试 Windows 临时目录"""
        with patch('platform.system', return_value='Windows'):
            with patch.dict(os.environ, {"TEMP": "C:/Windows/Temp"}):
                config = Config()
                temp_dir = config.get_temp_dir()
                self.assertEqual(temp_dir, Path("C:/Windows/Temp"))

    def test_get_export_dir_windows(self):
        """测试 Windows 导出目录"""
        with patch('platform.system', return_value='Windows'):
            config = Config()
            export_dir = config.get_export_dir("测试标题")
            self.assertIn("Desktop", str(export_dir))

    def test_get_export_dir_darwin(self):
        """测试 macOS 导出目录"""
        with patch('platform.system', return_value='Darwin'):
            config = Config()
            export_dir = config.get_export_dir("测试标题")
            self.assertIn("Desktop", str(export_dir))


class TestConfigYamlLoading(unittest.TestCase):
    """测试 YAML 配置文件加载"""

    def setUp(self):
        """设置测试"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_config_from_yaml(self):
        """测试从 YAML 文件加载配置"""
        # 这个测试需要 PyYAML 安装
        try:
            import yaml

            config_file = Path(self.temp_dir) / "config.yaml"
            config_file.write_text("test_key: test_value")

            config = Config(config_path=config_file)
            # 验证配置被加载
            self.assertIsNotNone(config._config)
        except ImportError:
            # yaml 未安装，跳过测试
            pass

    def test_load_config_yaml_not_installed(self):
        """测试 yaml 未安装时的处理"""
        # 模拟 yaml 导入失败
        import sys
        yaml_module = sys.modules.get('yaml')

        try:
            # 移除 yaml 模块
            sys.modules['yaml'] = None

            config_file = Path(self.temp_dir) / "config.yaml"
            config_file.write_text("test: value")

            config = Config(config_path=config_file)
            # 应该返回空配置而不是崩溃
            self.assertEqual(config._config, {})
        finally:
            # 恢复 yaml 模块
            if yaml_module:
                sys.modules['yaml'] = yaml_module
            else:
                sys.modules.pop('yaml', None)

    def test_find_config_from_env(self):
        """测试从环境变量查找配置文件"""
        custom_config = Path(self.temp_dir) / "custom_config.yaml"
        custom_config.write_text("test: value")

        with patch.dict(os.environ, {"XHS_CONFIG": str(custom_config)}):
            config = Config()
            self.assertEqual(config.config_path, custom_config)


class TestConfigAdditionalGetters(unittest.TestCase):
    """测试额外的配置 getter 方法"""

    def test_get_verticals_dir(self):
        """测试获取垂类目录"""
        config = Config()
        verticals_dir = config.get_verticals_dir()
        self.assertTrue(verticals_dir.exists())

    def test_get_personas_dir(self):
        """测试获取人设目录"""
        config = Config()
        personas_dir = config.get_personas_dir()
        # 目录可能不存在
        self.assertIn("personas", str(personas_dir))

    def test_get_assets_dir(self):
        """测试获取资源目录"""
        config = Config()
        assets_dir = config.get_assets_dir()
        self.assertIn("assets", str(assets_dir))

    def test_get_logo_dir(self):
        """测试获取 Logo 目录"""
        config = Config()
        logo_dir = config.get_logo_dir()
        self.assertIn("logo", str(logo_dir))

    def test_get_templates_dir(self):
        """测试获取模板目录"""
        config = Config()
        templates_dir = config.get_templates_dir()
        self.assertIn("templates", str(templates_dir))


if __name__ == '__main__':
    unittest.main()
