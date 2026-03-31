#!/usr/bin/env python3
"""
小红书封面 Logo 叠加

用法:
    python add_logo.py <input> <logo> <output>

参数:
    input  - 背景图路径
    logo   - Logo 图片路径
    output - 输出路径
"""

import sys
import platform
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("错误: 需要安装 Pillow: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def add_logo(input_path: str, logo_path: str, output_path: str) -> bool:
    """在图片上添加 Logo

    Args:
        input_path: 背景图路径
        logo_path: Logo 图片路径
        output_path: 输出路径

    Returns:
        是否成功
    """
    try:
        # 加载背景图
        img = Image.open(input_path).convert("RGBA")
        width, height = img.size

        # 加载 Logo
        logo = Image.open(logo_path).convert("RGBA")

        # 计算 Logo 大小（图片宽度的 18%）
        logo_size = int(width * 0.18)
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

        # Logo 位置（左上角）
        logo_x = int(width * 0.04)
        logo_y = int(height * 0.04)

        # 叠加 Logo
        img.paste(logo, (logo_x, logo_y), logo)

        # 转为 RGB 并保存
        img = img.convert("RGB")
        img.save(output_path, "PNG", quality=95)

        print(f"# ✓ Logo 添加完成: {output_path}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"# ✗ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 4:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    logo_path = sys.argv[2]
    output_path = sys.argv[3]

    success = add_logo(input_path, logo_path, output_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
