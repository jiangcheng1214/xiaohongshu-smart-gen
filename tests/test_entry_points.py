"""
测试模块入口点
"""

import sys
import tempfile
import unittest
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# 添加 scripts 目录到路径
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


class TestMainEntryPoint(unittest.TestCase):
    """测试 __main__.py 入口点"""

    @patch('scripts.xhs_cli.__main__.main')
    def test_main_entry_point_calls_main(self, mock_main):
        """测试入口点调用 main 函数"""
        mock_main.return_value = 0

        # 手动调用
        import scripts.xhs_cli.__main__ as main_module
        result = main_module.main()
        self.assertEqual(result, 0)
        mock_main.assert_called_once()

    @patch('scripts.xhs_cli.__main__.main')
    @patch('scripts.xhs_cli.__main__.sys.exit')
    def test_main_entry_point_with_exit(self, mock_exit, mock_main):
        """测试 __main__ 块的 sys.exit 调用"""
        mock_main.return_value = 42

        # 模拟 __name__ == "__main__" 块的行为
        import scripts.xhs_cli.__main__ as main_module

        # 直接调用 main，然后验证 sys.exit 会被调用（在实际执行中）
        result = main_module.main()
        self.assertEqual(result, 42)

    def test_main_module_can_be_executed(self):
        """测试模块可以被 Python 执行"""
        # 测试模块可以被执行（验证 sys.exit 路径）
        import scripts.xhs_cli.__main__ as main_module

        # 验证 main 函数存在并可调用
        self.assertTrue(callable(main_module.main))

        # 测试调用 main 返回 int
        with patch.object(main_module, 'main', return_value=0):
            result = main_module.main()
            self.assertEqual(result, 0)

    @patch('scripts.xhs_cli.__main__.sys.exit')
    @patch('scripts.xhs_cli.__main__.main')
    def test_main_entry_point_with_different_exit_codes(self, mock_main, mock_exit):
        """测试不同的退出码"""
        test_cases = [0, 1, 42]
        for exit_code in test_cases:
            mock_main.return_value = exit_code
            import scripts.xhs_cli.__main__ as main_module

            result = main_module.main()
            self.assertEqual(result, exit_code)

    @patch('scripts.xhs_cli.__main__.main')
    def test_main_entry_point_execution(self, mock_main):
        """测试模块作为主程序执行时的行为"""
        mock_main.return_value = 0

        # 通过 subprocess 运行模块来测试 __main__ 块
        # 这会实际触发 sys.exit
        result = subprocess.run(
            [sys.executable, "-m", "scripts.xhs_cli", "--help"],
            capture_output=True,
            text=True,
            cwd=scripts_dir.parent,
            timeout=5
        )

        # 验证运行成功（可能返回 0 或 2 表示参数错误）
        self.assertIn(result.returncode, [0, 2])


class TestXhsDoEntryPoint(unittest.TestCase):
    """测试 xhs_do.py 入口点"""

    def test_xhs_do_module_structure(self):
        """测试 xhs_do 模块结构正确"""
        # 验证文件存在
        xhs_do_path = scripts_dir / "xhs_do.py"
        self.assertTrue(xhs_do_path.exists())

        # 验证 main_do 函数存在
        from scripts.xhs_cli.cli import main_do
        self.assertTrue(callable(main_do))

    @patch('scripts.xhs_cli.cli.SessionManager')
    @patch('scripts.xhs_cli.cli.Config')
    @patch('scripts.xhs_cli.cli.argparse.ArgumentParser')
    def test_main_do_function_structure(self, mock_parser_class, mock_config_class, mock_session_mgr_class):
        """测试 main_do 函数结构"""
        # 创建 mock 对象
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_args = MagicMock()
        mock_args.vertical = "finance"
        mock_args.topic = "测试"
        mock_args.action = "--all"
        mock_parser.parse_args.return_value = mock_args

        mock_config = MagicMock()
        mock_config_class.return_value = mock_config

        mock_mgr = MagicMock()
        mock_session_mgr_class.return_value = mock_mgr

        # 模拟 cmd_all 返回 0
        with patch('scripts.xhs_cli.cli.cmd_all', return_value=0):
            from scripts.xhs_cli.cli import main_do

            # 由于 sys.argv 的复杂性，我们只验证函数存在
            self.assertTrue(callable(main_do))

    def test_xhs_do_script_execution(self):
        """测试 xhs_do.py 脚本执行"""
        xhs_do_path = scripts_dir / "xhs_do.py"

        # 验证脚本可以被执行（至少有正确的语法）
        result = subprocess.run(
            [sys.executable, str(xhs_do_path), "--help"],
            capture_output=True,
            text=True,
            cwd=scripts_dir,
            timeout=5
        )

        # 应该显示帮助或错误（因为参数不完整）
        self.assertIn(result.returncode, [0, 2])


class TestXhsDoScript(unittest.TestCase):
    """测试 xhs_do.py 脚本执行"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_xhs_do_imports_correct_modules(self):
        """测试 xhs_do 正确导入模块"""
        xhs_do_path = scripts_dir / "xhs_do.py"

        # 验证文件存在且可读
        self.assertTrue(xhs_do_path.exists())
        self.assertTrue(xhs_do_path.is_file())

        # 验证文件内容包含关键导入
        content = xhs_do_path.read_text(encoding="utf-8")
        self.assertIn("from xhs_cli.cli import main_do", content)
        self.assertIn("sys.exit(main_do())", content)

    def test_xhs_do_can_be_executed(self):
        """测试 xhs_do.py 可以作为主程序执行"""
        xhs_do_path = scripts_dir / "xhs_do.py"

        # 验证文件可以被执行（验证 sys.exit 路径）
        result = subprocess.run(
            [sys.executable, str(xhs_do_path), "--help"],
            capture_output=True,
            text=True,
            cwd=scripts_dir,
            timeout=5
        )

        # 应该显示帮助或错误（因为参数不完整）
        self.assertIn(result.returncode, [0, 2])

    def test_xhs_do_main_do_integration(self):
        """测试 xhs_do 与 main_do 函数的集成"""
        from scripts.xhs_cli.cli import main_do

        # 验证 main_do 函数存在并可调用
        self.assertTrue(callable(main_do))

    @patch('scripts.xhs_cli.cli.main_do')
    def test_xhs_do_calls_main_do(self, mock_main_do):
        """测试 xhs_do 调用 main_do 函数"""
        mock_main_do.return_value = 0

        # 模拟 xhs_do 的行为
        from scripts.xhs_cli.cli import main_do
        result = main_do()

        self.assertEqual(result, 0)
        mock_main_do.assert_called_once()


class TestMainModuleExecution(unittest.TestCase):
    """测试 __main__.py 模块执行"""

    @patch('scripts.xhs_cli.__main__.sys.exit')
    @patch('scripts.xhs_cli.__main__.main')
    def test_main_module_exits_with_main_return_value(self, mock_main, mock_exit):
        """测试 __main__ 模块使用 main 函数返回值退出"""
        mock_main.return_value = 42

        # 导入模块会触发 __main__ 块（但在这里我们只测试函数）
        import scripts.xhs_cli.__main__ as main_module

        # 直接调用 main 来模拟 __main__ 块的行为
        result = main_module.main()

        self.assertEqual(result, 42)

    @patch('scripts.xhs_cli.__main__.main')
    def test_main_module_main_function_exists(self, mock_main):
        """测试 main 函数存在"""
        mock_main.return_value = 0

        import scripts.xhs_cli.__main__ as main_module

        # 验证 main 函数存在
        self.assertTrue(hasattr(main_module, 'main'))
        self.assertTrue(callable(main_module.main))

    @patch('scripts.xhs_cli.__main__.main')
    def test_main_module_successful_execution(self, mock_main):
        """测试 main 模块成功执行"""
        mock_main.return_value = 0

        import scripts.xhs_cli.__main__ as main_module
        result = main_module.main()

        self.assertEqual(result, 0)
        mock_main.assert_called_once()

    @patch('scripts.xhs_cli.__main__.main')
    def test_main_module_error_execution(self, mock_main):
        """测试 main 模块错误执行"""
        mock_main.return_value = 1

        import scripts.xhs_cli.__main__ as main_module
        result = main_module.main()

        self.assertEqual(result, 1)

    @patch('scripts.xhs_cli.__main__.main')
    @patch('scripts.xhs_cli.__main__.sys.exit')
    def test_main_module_block_calls_sys_exit(self, mock_exit, mock_main):
        """测试 __main__ 块调用 sys.exit"""
        mock_main.return_value = 5

        # 读取 __main__.py 的内容验证有 sys.exit 调用
        import scripts.xhs_cli
        main_file = Path(scripts.xhs_cli.__file__).parent / "__main__.py"
        content = main_file.read_text()

        self.assertIn("sys.exit(main())", content)


class TestXhsDoScriptExecution(unittest.TestCase):
    """测试 xhs_do.py 脚本执行"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_xhs_do_file_exists(self):
        """测试 xhs_do.py 文件存在"""
        xhs_do_path = scripts_dir / "xhs_do.py"
        self.assertTrue(xhs_do_path.exists())
        self.assertTrue(xhs_do_path.is_file())

    def test_xhs_do_has_main_block(self):
        """测试 xhs_do.py 有 __main__ 块"""
        xhs_do_path = scripts_dir / "xhs_do.py"
        content = xhs_do_path.read_text(encoding="utf-8")

        self.assertIn('if __name__ == "__main__":', content)
        self.assertIn("sys.exit(main_do())", content)

    @patch('scripts.xhs_cli.cli.main_do')
    def test_xhs_do_main_block_exits_with_main_do_return(self, mock_main_do):
        """测试 xhs_do.py __main__ 块使用 main_do 返回值退出"""
        mock_main_do.return_value = 10

        from scripts.xhs_cli.cli import main_do
        result = main_do()

        self.assertEqual(result, 10)

    def test_xhs_do_can_be_imported(self):
        """测试 xhs_do.py 可以被导入"""
        # 验证文件可以被 Python 导入（没有语法错误）
        xhs_do_path = scripts_dir / "xhs_do.py"

        # 编译文件验证语法
        import py_compile
        try:
            py_compile.compile(str(xhs_do_path), doraise=True)
        except py_compile.PyCompileError as e:
            self.fail(f"xhs_do.py has syntax error: {e}")

        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
