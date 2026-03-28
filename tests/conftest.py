"""
Pytest 配置和共享 fixtures
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def temp_dir():
    """临时目录 fixture"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    # 清理
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def clean_env():
    """清理环境变量 fixture"""
    # 保存原始环境变量
    original_env = os.environ.copy()

    # 清除可能影响测试的环境变量
    for key in ["OPENCLAW_HOME", "XHS_WORKSPACE", "GEMINI_API_KEY",
                "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]:
        os.environ.pop(key, None)

    yield

    # 恢复原始环境变量
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def mock_workspace(temp_dir):
    """Mock 工作区 fixture"""
    workspace = temp_dir / "workspace"
    workspace.mkdir()
    return workspace


@pytest.fixture
def mock_skill_dir(temp_dir):
    """Mock 技能目录 fixture"""
    skill_dir = temp_dir / "skill"
    skill_dir.mkdir()

    # 创建必要的子目录
    (skill_dir / "verticals").mkdir()
    (skill_dir / "personas").mkdir()
    (skill_dir / "assets" / "logo").mkdir(parents=True)
    (skill_dir / "scripts" / "lib").mkdir(parents=True)

    return skill_dir
