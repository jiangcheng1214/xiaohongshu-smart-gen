#!/usr/bin/env python3
"""
小红书 Session 管理类

管理 XHS 内容生成 session 的创建、读取、更新等操作。
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class XhsSession:
    """
    小红书内容生成 Session 管理类

    负责管理单个内容生成任务的状态、配置和中间结果。
    """

    def __init__(self, session_dir: Optional[Path] = None,
                 workspace: Optional[Path] = None):
        """
        初始化 Session

        Args:
            session_dir: Session 目录路径，如果为 None 则创建新 session
            workspace: 工作空间根目录，默认为 ~/.openclaw/agents/main/agent
        """
        self.workspace = workspace or Path.home() / ".openclaw" / "agents" / "main" / "agent"
        self.workspace.mkdir(parents=True, exist_ok=True)

        self._session_dir: Optional[Path] = None
        self._data: Dict[str, Any] = {}

        if session_dir:
            self.load(session_dir)

    @property
    def session_dir(self) -> Path:
        """获取 session 目录路径"""
        if self._session_dir is None:
            raise RuntimeError("Session not initialized. Call create() or load() first.")
        return self._session_dir

    @property
    def session_id(self) -> str:
        """获取 session ID"""
        return self._data.get('id', '')

    @property
    def topic(self) -> str:
        """获取话题"""
        return self._data.get('topic', '')

    @property
    def vertical(self) -> str:
        """获取垂类"""
        return self._data.get('vertical', '')

    @property
    def status(self) -> str:
        """获取状态"""
        return self._data.get('status', 'unknown')

    @staticmethod
    def sanitize_topic(topic: str) -> str:
        """
        将话题转换为安全的文件名

        Args:
            topic: 原始话题

        Returns:
            安全化的话题字符串
        """
        # 替换空格和特殊字符
        safe = topic.replace(" ", "_").replace("/", "_").replace("\\", "_")
        safe = re.sub(r'[^\w\u4e00-\u9fff_]', '', safe)
        return safe[:20]

    @classmethod
    def find_existing(cls, topic: str, workspace: Optional[Path] = None) -> Optional[Path]:
        """
        查找现有 session 目录

        Args:
            topic: 话题
            workspace: 工作空间目录

        Returns:
            找到的 session 目录路径，未找到返回 None
        """
        workspace = workspace or Path.home() / ".openclaw" / "agents" / "main" / "agent"
        safe_topic = cls.sanitize_topic(topic)

        existing = list(workspace.glob(f"xhs_session_*_{safe_topic}"))
        if existing:
            return max(existing, key=lambda p: p.stat().st_mtime)
        return None

    def create(self, vertical: str, topic: str) -> 'XhsSession':
        """
        创建新的 session

        Args:
            vertical: 垂类 (stock, finance, tech, beauty 等)
            topic: 话题

        Returns:
            self (支持链式调用)
        """
        safe_topic = self.sanitize_topic(topic)
        timestamp = int(datetime.now(timezone.utc).timestamp())
        session_id = f"xhs_session_{timestamp}_{safe_topic}"

        self._session_dir = self.workspace / session_id
        self._session_dir.mkdir(parents=True, exist_ok=True)

        self._data = {
            "id": session_id,
            "vertical": vertical,
            "topic": topic,
            "safe_topic": safe_topic,
            "created_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "updated_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            "status": "initialized",
            "steps": {
                "research": {"status": "pending", "attempts": 0},
                "generate": {"status": "pending", "attempts": 0},
                "validate": {"status": "pending", "attempts": 0},
                "prepare_img": {"status": "pending", "attempts": 0},
                "gen_img": {"status": "pending", "attempts": 0},
                "overlay": {"status": "pending", "attempts": 0},
                "deliver": {"status": "pending", "attempts": 0}
            },
            "config": {
                "vertical": vertical
            },
            "title": "",
            "subtitle": "",
            "debug": {}
        }

        self._save()
        return self

    def load(self, session_dir: Path) -> 'XhsSession':
        """
        加载现有 session

        Args:
            session_dir: Session 目录路径

        Returns:
            self (支持链式调用)
        """
        self._session_dir = Path(session_dir)
        session_file = self._session_dir / "session.json"

        if not session_file.exists():
            raise FileNotFoundError(f"Session file not found: {session_file}")

        with open(session_file, 'r', encoding='utf-8') as f:
            self._data = json.load(f)

        return self

    def reload(self) -> 'XhsSession':
        """重新加载 session.json"""
        return self.load(self._session_dir)

    def _save(self) -> None:
        """保存 session 到文件"""
        self._data['updated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        session_file = self._session_dir / "session.json"
        temp_file = session_file.with_suffix('.tmp')

        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

        temp_file.replace(session_file)

    def update_status(self, status: str) -> None:
        """
        更新 session 状态

        Args:
            status: 新状态 (initialized, researching, content_generated, etc.)
        """
        self._data['status'] = status
        self._save()

    def update_step(self, step_id: str, status: str,
                    data: Optional[Dict[str, Any]] = None) -> None:
        """
        更新步骤状态

        Args:
            step_id: 步骤 ID (research, generate, validate, etc.)
            status: 状态 (pending, in_progress, completed, failed)
            data: 附加数据
        """
        if 'steps' not in self._data:
            self._data['steps'] = {}

        if step_id not in self._data['steps']:
            self._data['steps'][step_id] = {
                'status': 'pending',
                'attempts': 0
            }

        step = self._data['steps'][step_id]
        step['status'] = status

        if status in ['in_progress', 'completed', 'failed']:
            step['attempts'] = step.get('attempts', 0) + 1

        now_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        if status == 'in_progress':
            step['started_at'] = now_iso
        elif status == 'completed':
            step['completed_at'] = now_iso
        elif status == 'failed':
            step['failed_at'] = now_iso

        if data:
            if 'data' not in step:
                step['data'] = {}
            step['data'].update(data)

        self._save()

    def get_step_status(self, step_id: str) -> str:
        """获取步骤状态"""
        return self._data.get('steps', {}).get(step_id, {}).get('status', 'unknown')

    def get_step_data(self, step_id: str) -> Dict[str, Any]:
        """获取步骤数据"""
        return self._data.get('steps', {}).get(step_id, {}).get('data', {})

    def set_title(self, title: str, subtitle: str = "") -> None:
        """设置标题和副标题"""
        self._data['title'] = title
        if subtitle:
            self._data['subtitle'] = subtitle
        self._save()

    # 文件操作辅助方法

    def read_file(self, filename: str) -> str:
        """读取 session 目录中的文件"""
        file_path = self._session_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return file_path.read_text(encoding='utf-8')

    def write_file(self, filename: str, content: str) -> None:
        """写入文件到 session 目录"""
        file_path = self._session_dir / filename
        file_path.write_text(content, encoding='utf-8')

    def file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        return (self._session_dir / filename).exists()

    def get_file_path(self, filename: str) -> Path:
        """获取文件路径"""
        return self._session_dir / filename

    # 调试日志方法

    def log(self, level: str, step: str, message: str,
            data: Optional[Dict] = None, exc_info: bool = False) -> None:
        """记录调试日志到 debug.log"""
        log_path = self._session_dir / "debug.log"

        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

        log_entry = {
            'timestamp': timestamp,
            'step': step,
            'level': level,
            'message': message
        }

        if data:
            log_entry['data'] = data

        if exc_info:
            import traceback
            log_entry['traceback'] = traceback.format_exc()

        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def to_dict(self) -> Dict[str, Any]:
        """返回 session 数据的副本"""
        return self._data.copy()

    def __repr__(self) -> str:
        return f"XhsSession(id={self.session_id}, status={self.status}, topic={self.topic})"
