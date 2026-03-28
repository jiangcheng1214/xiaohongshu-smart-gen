#!/usr/bin/env python3
"""
图片生成模块

使用 Gemini API 生成封面图片。
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Optional


def generate_image(prompt: str, output_path: Path,
                  api_key: str = "", resolution: str = "1K",
                  reference_image: Optional[Path] = None) -> bool:
    """
    生成图片

    Args:
        prompt: 图片生成提示词
        output_path: 输出文件路径
        api_key: Gemini API key
        resolution: 分辨率 (1K, 2K)
        reference_image: 参考图片路径（用于保持一致性）

    Returns:
        bool: 是否成功
    """
    # 查找 generate_image.py 脚本
    script_paths = [
        Path.home() / ".openclaw" / "sandboxes" / "agent-main-f331f052" /
            "skills" / "nano-banana-pro" / "scripts" / "generate_image.py",
        Path.home() / ".openclaw" / "skills" / "nano-banana-pro" / "scripts" / "generate_image.py",
    ]

    generate_script = None
    for path in script_paths:
        if path.exists():
            generate_script = path
            break

    if not generate_script:
        raise FileNotFoundError(
            "generate_image.py not found. Please ensure nano-banana-pro skill is installed."
        )

    # 构建命令
    cmd = ['uv', 'run', str(generate_script),
           '--prompt', prompt,
           '--filename', str(output_path),
           '--resolution', resolution]

    # 添加参考图片
    if reference_image and reference_image.exists():
        cmd.extend(['--input-image', str(reference_image)])

    if api_key:
        cmd.extend(['--api-key', api_key])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            error_output = (result.stdout + '\n' + result.stderr)[:500]
            raise RuntimeError(f'Image generation failed: {error_output}')

        if not output_path.exists():
            raise FileNotFoundError('Output file not created')

        return True

    except subprocess.TimeoutExpired:
        raise RuntimeError('Image generation timed out')
    except Exception as e:
        raise RuntimeError(f'Image generation error: {str(e)}')


def get_api_key() -> str:
    """从配置文件获取 API key"""
    config_file = Path.home() / '.openclaw' / 'openclaw.json'
    if not config_file.exists():
        return ''

    with open(config_file) as f:
        data = json.load(f)

    api_key = data.get('env', {}).get('GEMINI_API_KEY', '')
    if not api_key:
        api_key = data.get('skills', {}).get('entries', {}).get(
            'nano-banana-pro', {}
        ).get('apiKey', '')

    return api_key
