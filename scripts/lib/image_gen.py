#!/usr/bin/env python3
"""
图片生成模块

使用 Gemini API 生成封面图片。
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional


# ─── 技能自动安装 ─────────────────────────────────────────────────────────────

def _ensure_skill_installed(skill_name: str = "nano-banana-pro") -> Path:
    """
    确保 skill 已安装到全局目录
    如果不存在，从沙箱自动复制

    Args:
        skill_name: 技能名称

    Returns:
        技能安装目录
    """
    global_skills_dir = Path.home() / ".openclaw" / "skills"
    skill_dir = global_skills_dir / skill_name

    # 如果已安装，直接返回
    if skill_dir.exists():
        return skill_dir

    # 尝试从沙箱复制
    sandboxes_dir = Path.home() / ".openclaw" / "sandboxes"
    source_skill = None

    if sandboxes_dir.exists():
        for sandbox in sandboxes_dir.glob("agent-main-*"):
            candidate = sandbox / "skills" / skill_name
            if candidate.exists():
                source_skill = candidate
                break

    if not source_skill:
        raise FileNotFoundError(
            f"Cannot install {skill_name}: not found in any sandbox. "
            f"Please install it manually to ~/.openclaw/skills/{skill_name}/"
        )

    # 创建目标目录并复制
    skill_dir.mkdir(parents=True, exist_ok=True)

    # 复制所有文件和目录
    for item in source_skill.iterdir():
        dest = skill_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    print(f"✓ Installed {skill_name} to {skill_dir}")
    return skill_dir


# ─── 图片生成 ───────────────────────────────────────────────────────────────────


def generate_image(prompt: str, output_path: Path,
                  api_key: str = "", resolution: str = "1K",
                  reference_image: Optional[Path] = None,
                  aspect_ratio: str = "1:1") -> bool:
    """
    生成图片

    Args:
        prompt: 图片生成提示词
        output_path: 输出文件路径
        api_key: Gemini API key
        resolution: 分辨率 (1K, 2K, 4K)
        reference_image: 参考图片路径（用于保持一致性）
        aspect_ratio: 宽高比 (1:1, 3:4, 16:9 等)，传递给 nano-banana-pro

    Returns:
        bool: 是否成功
    """
    skill_name = "nano-banana-pro"
    script_name = "generate_image.py"

    # 确保技能已安装到全局目录
    skill_dir = _ensure_skill_installed(skill_name)

    # 生成脚本路径（优先级：环境变量 > 全局安装 > 当前项目）
    generate_script = None

    # 1. 环境变量指定
    if env_path := os.environ.get("NANO_BANANA_SCRIPT"):
        candidate = Path(env_path)
        if candidate.exists():
            generate_script = candidate

    # 2. 全局技能目录
    if not generate_script:
        candidate = skill_dir / "scripts" / script_name
        if candidate.exists():
            generate_script = candidate

    # 3. 当前项目 lib 目录（开发模式）
    if not generate_script:
        current_dir = Path(__file__).parent
        candidate = current_dir / skill_name / script_name
        if candidate.exists():
            generate_script = candidate

    if not generate_script:
        raise FileNotFoundError(
            f"{script_name} not found after installation. "
            f"Expected at: {skill_dir / 'scripts' / script_name}"
        )

    # 构建命令
    cmd = ['uv', 'run', str(generate_script),
           '--prompt', prompt,
           '--filename', str(output_path),
           '--resolution', resolution,
           '--aspect-ratio', aspect_ratio]

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
