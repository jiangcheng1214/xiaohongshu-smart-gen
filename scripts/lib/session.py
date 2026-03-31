#!/usr/bin/env python3
"""
小红书内容生成 - Session 管理

Session 负责管理单个内容生成的状态、文件和元数据。
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class XhsSession:
    """小红书内容生成 Session"""

    def __init__(self, workspace: Path, vertical: str = "", topic: str = ""):
        self.workspace = Path(workspace)
        self.vertical = vertical
        self.topic = topic
        self.session_dir: Optional[Path] = None
        self._data: dict[str, Any] = {}

    @property
    def session_id(self) -> str:
        """Session ID"""
        return self._data.get('id', '')

    @property
    def status(self) -> str:
        """Session 状态"""
        return self._data.get('status', 'initialized')

    def create(self, vertical: str, topic: str) -> None:
        """创建新 session"""
        import time

        self.vertical = vertical
        self.topic = topic

        # 生成安全的文件名
        safe_topic = re.sub(r'[^\w\u4e00-\u9fff-]', '_', topic)[:50]
        safe_vertical = re.sub(r'[^\w\u4e00-\u9fff-]', '_', vertical)[:30]
        timestamp = int(time.time())
        # 文件夹命名格式: xhs-session-{timestamp}-{vertical}-{topic}
        session_id = f"xhs-session-{timestamp}-{safe_vertical}-{safe_topic}"

        self.session_dir = self.workspace / session_id
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        (self.session_dir / "images").mkdir(exist_ok=True)

        # 初始化元数据
        now = datetime.now(timezone.utc).isoformat()
        self._data = {
            'id': session_id,
            'vertical': vertical,
            'topic': topic,
            'status': 'initialized',
            'created_at': now,
            'updated_at': now,
            'steps': {},
        }

        self._save_metadata()

    def load(self, session_dir: Path) -> None:
        """从目录加载已有 session"""
        self.session_dir = Path(session_dir)
        metadata_file = self.session_dir / "session.json"

        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                self._data = json.load(f)

            self.vertical = self._data.get('vertical', '')
            self.topic = self._data.get('topic', '')

    def _save_metadata(self) -> None:
        """保存元数据到文件"""
        if not self.session_dir:
            return

        self._data['updated_at'] = datetime.now(timezone.utc).isoformat()

        with open(self.session_dir / "session.json", 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def update_step(self, step_name: str, status: str, data: Optional[dict[str, Any]] = None) -> None:
        """更新步骤状态"""
        if 'steps' not in self._data:
            self._data['steps'] = {}

        self._data['steps'][step_name] = {
            'status': status,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }

        if data:
            self._data['steps'][step_name].update(data)

        self._save_metadata()

    def get_step_data(self, step_name: str) -> Optional[dict[str, Any]]:
        """获取步骤数据"""
        return self._data.get('steps', {}).get(step_name)

    def log(self, level: str, step: str, message: str,
            extra: Optional[dict[str, Any]] = None, exc_info: bool = False, **kwargs) -> None:
        """记录日志"""
        # 简化版日志，可以扩展
        if extra:
            print(f"[{level.upper()}] {step}: {message} {extra}")
        else:
            print(f"[{level.upper()}] {step}: {message}")

    def set_title(self, title: str, subtitle: str) -> None:
        """设置标题和副标题"""
        if 'generate' not in self._data.get('steps', {}):
            self.update_step('generate', 'in_progress', {})

        self._data.setdefault('steps', {}).setdefault('generate', {})['data'] = {
            'title': title,
            'subtitle': subtitle,
        }
        self._save_metadata()

    def write_file(self, filename: str, content: str) -> Path:
        """写入文件到 session 目录"""
        if not self.session_dir:
            raise RuntimeError("Session not initialized")

        file_path = self.session_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return file_path

    def read_file(self, filename: str) -> str:
        """从 session 目录读取文件"""
        if not self.session_dir:
            raise RuntimeError("Session not initialized")

        file_path = self.session_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def file_exists(self, filename: str) -> bool:
        """检查文件是否存在"""
        if not self.session_dir:
            return False

        return (self.session_dir / filename).exists()

    def get_file_path(self, filename: str) -> Path:
        """获取文件路径"""
        if not self.session_dir:
            raise RuntimeError("Session not initialized")

        return self.session_dir / filename

    def set_status(self, status: str) -> None:
        """设置 session 状态"""
        self._data['status'] = status
        self._save_metadata()

    @staticmethod
    def find_existing(topic: str, workspace: Path) -> Optional[Path]:
        """查找已有 session"""
        safe_topic = re.sub(r'[^\w\u4e00-\u9fff-]', '_', topic)[:50]

        # 支持新旧两种格式的 session 文件夹
        for session_dir in workspace.glob("xhs-session-*"):
            metadata_file = session_dir / "session.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if data.get('topic') == topic:
                        return session_dir
                except Exception:
                    pass

        # 兼容旧格式
        for session_dir in workspace.glob("xhs_session_*"):
            metadata_file = session_dir / "session.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if data.get('topic') == topic:
                        return session_dir
                except Exception:
                    pass

        return None
