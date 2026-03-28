"""
图片搜索模块 - 跨平台实现
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from ..config import Config
from ..lib.paths import PathManager
from .session import Session


class ImageSearcher:
    """图片搜索器 (跨平台)"""

    # 默认搜索查询模板
    DEFAULT_QUERIES = ["{topic}", "{topic} 评测", "{topic} 测评"]

    def __init__(self, config: Config | None = None, path_manager: PathManager | None = None):
        self.config = config or Config()
        self.path_manager = path_manager or PathManager(self.config)

    def search(self, session: Session, count: int = 3) -> list[Path]:
        """搜索并下载参考图片

        Args:
            session: Session 对象
            count: 目标图片数量

        Returns:
            下载的图片路径列表
        """
        print(f"# === 图片搜索 ===", file=sys.stderr)
        print(f"# Topic: {session.topic}", file=sys.stderr)
        print(f"# Vertical: {session.vertical}", file=sys.stderr)

        # 创建图片目录
        images_dir = self.path_manager.get_session_dir(session.id) / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        # 加载垂类配置获取搜索关键词
        vertical_config = self._load_vertical_config(session.vertical)
        keywords = vertical_config.get("keywords", [])[:5]

        # 构建搜索查询
        queries = self._build_queries(session.topic, keywords)

        # 尝试 AI 图片搜索
        downloaded = self._ai_search(images_dir, queries, count)

        # 如果 AI 搜索失败，创建占位符
        if not downloaded:
            print(f"# AI 搜索不可用，创建占位符图片", file=sys.stderr)
            downloaded = self._create_placeholders(images_dir, session.topic, count)

        # 更新 session
        session.images_dir = str(images_dir)
        session.images_updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        session.images_count = len(downloaded)

        # 添加 debug 信息
        session.debug = session.debug or {}
        session.debug["images"] = {
            "vertical": session.vertical,
            "topic": session.topic,
            "queries": queries,
            "downloaded": len(downloaded),
            "directory": str(images_dir)
        }

        session.save(self.path_manager.get_session_dir(session.id))

        print(f"# ✓ 图片搜索完成，共 {len(downloaded)} 张", file=sys.stderr)
        print(str(images_dir))
        return downloaded

    def _load_vertical_config(self, vertical: str) -> dict:
        """加载垂类配置"""
        config_file = self.path_manager.get_verticals_dir() / f"{vertical}.json"
        if not config_file.exists():
            return {}
        with open(config_file, encoding="utf-8") as f:
            return json.load(f)

    def _build_queries(self, topic: str, keywords: list[str]) -> list[str]:
        """构建搜索查询列表"""
        # 基础查询
        queries = [q.format(topic=topic) for q in self.DEFAULT_QUERIES]

        # 添加关键词组合
        for keyword in keywords[:2]:
            queries.append(f"{topic} {keyword}")

        return queries

    def _ai_search(self, images_dir: Path, queries: list[str], count: int) -> list[Path]:
        """使用 AI 图片搜索"""
        # 查找 nano-banana-pro 的搜索脚本
        search_script = self._find_search_script()
        if not search_script:
            return []

        downloaded = []
        for i, query in enumerate(queries):
            if len(downloaded) >= count:
                break

            output_file = images_dir / f"image_{i}.jpg"

            print(f"# 搜索: {query}", file=sys.stderr)

            if self._run_search(search_script, query, output_file):
                if output_file.exists():
                    downloaded.append(output_file)
                    print(f"# ✓ 下载图片: {output_file.name}", file=sys.stderr)

        return downloaded

    def _find_search_script(self) -> Optional[Path]:
        """查找 nano-banana-pro 搜索脚本"""
        # 可能的路径
        possible_paths = [
            Path("/opt/homebrew/lib/node_modules/openclaw/skills/nano-banana-pro/scripts/search_images.py"),
            Path.home() / ".openclaw/skills/nano-banana-pro/scripts/search_images.py",
            Path.home() / ".nvm/versions/node/*/lib/node_modules/openclaw/skills/nano-banana-pro/scripts/search_images.py",
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def _run_search(self, script: Path, query: str, output: Path) -> bool:
        """运行搜索脚本"""
        try:
            cmd = [
                "uv", "run", str(script),
                "--query", query,
                "--output", str(output),
                "--count", "1"
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                encoding="utf-8"
            )

            return result.returncode == 0

        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False

    def _create_placeholders(self, images_dir: Path, topic: str, count: int) -> list[Path]:
        """创建占位符图片 (跨平台)"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            placeholders = []

            for i in range(count):
                output_file = images_dir / f"image_{i}.jpg"

                # 创建 800x600 渐变背景
                img = Image.new("RGB", (800, 600), color="#302b63")
                draw = ImageDraw.Draw(img)

                # 尝试加载字体
                font = self._get_font(48)
                if font:
                    # 绘制话题文字
                    text = topic[:20]  # 限制长度
                    bbox = draw.textbbox((0, 0), text, font=font)
                    text_width = bbox[2] - bbox[0]
                    text_x = (800 - text_width) // 2
                    text_y = 300 - 24

                    # 绘制阴影
                    draw.text((text_x + 2, text_y + 2), text, font=font, fill="#000000")
                    # 绘制主文字
                    draw.text((text_x, text_y), text, font=font, fill="#ffffff")

                # 保存
                img.save(output_file, "JPEG", quality=85)
                placeholders.append(output_file)
                print(f"# ✓ 创建占位符: {output_file.name}", file=sys.stderr)

            return placeholders

        except ImportError:
            # Pillow 未安装，创建最小的占位文件
            return self._create_minimal_placeholders(images_dir, count)

    def _get_font(self, size: int):
        """获取字体对象"""
        try:
            from PIL import ImageFont

            # 尝试常见字体路径
            font_paths = [
                # macOS
                "/System/Library/Fonts/PingFang.ttc",
                "/System/Library/Fonts/STHeiti Medium.ttc",
                # Linux
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                # Windows
                "C:\\Windows\\Fonts\\msyh.ttc",
                "C:\\Windows\\Fonts\\simsun.ttc",
            ]

            for font_path in font_paths:
                if Path(font_path).exists():
                    return ImageFont.truetype(font_path, size)

            # 回退到默认字体
            return ImageFont.load_default()

        except (ImportError, OSError):
            return None

    def _create_minimal_placeholders(self, images_dir: Path, count: int) -> list[Path]:
        """创建最小的占位符文件 (1x1 PNG)"""
        import struct

        placeholders = []

        # 创建一个最小的 PNG 文件头
        minimal_png = (
            b'\x89PNG\r\n\x1a\n'
            + struct.pack(">I", 13)
            + b'IHDR'
            + struct.pack(">II", 1, 1)  # 1x1 像素
            + b'\x08\x02\x00\x00\x00'  # 8-bit RGB
            + struct.pack(">I", 0x5c6e63ef)  # CRC
            + struct.pack(">I", 12)
            + b'IDAT'
            + b'\x78\x9c\x62\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4'
            + struct.pack(">I", 0x849ddfe8)  # CRC
            + struct.pack(">I", 0)
            + b'IEND'
            + struct.pack(">I", 0xae426082)  # CRC
        )

        for i in range(count):
            output_file = images_dir / f"image_{i}.png"
            output_file.write_bytes(minimal_png)
            placeholders.append(output_file)
            print(f"# ✓ 创建最小占位符: {output_file.name}", file=sys.stderr)

        return placeholders
