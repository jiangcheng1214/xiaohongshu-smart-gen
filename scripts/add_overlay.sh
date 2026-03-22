#!/bin/bash
# 为已生成的图片添加文字元素和 Logo
# 用法: ./add_overlay.sh "输入图片" "标题" "副标题" "输出路径" [Logo路径]

set -e

INPUT="$1"
TITLE="$2"
SUBTITLE="${3:-}"
OUTPUT="${4:-/tmp/xhs_cover_overlay_$(date +%s).png}"
LOGO_PATH="${5:-}"

if [[ -z "$INPUT" || -z "$TITLE" ]]; then
    echo "用法: $0 \"输入图片\" \"标题\" [\"副标题\"] [\"输出路径\"] [\"Logo路径\"]" >&2
    exit 1
fi

if [[ ! -f "$INPUT" ]]; then
    echo "错误: 输入文件不存在: $INPUT" >&2
    exit 1
fi

# 如果没有提供Logo路径，尝试自动获取
if [[ -z "$LOGO_PATH" ]]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

    # 回退到 default.png
    LOGO_PATH="$SKILL_DIR/assets/logo/default.png"
fi

# 检查 Logo 文件是否存在
if [[ ! -f "$LOGO_PATH" ]]; then
    echo "警告: Logo 文件不存在: $LOGO_PATH，继续生成不带Logo的封面" >&2
    LOGO_PATH=""
fi

if command -v magick &> /dev/null; then
    MAGICK="magick"
elif command -v convert &> /dev/null; then
    MAGICK="convert"
else
    echo "错误: 未找到 ImageMagick" >&2
    exit 1
fi

# 字体配置
MAGICK_FONT_BOLD="/System/Library/Fonts/STHeiti Medium.ttc"
MAGICK_FONT_LIGHT="/System/Library/Fonts/STHeiti Light.ttc"

[[ ! -f "$MAGICK_FONT_BOLD" ]] && MAGICK_FONT_BOLD="STHeiti-Medium"
[[ ! -f "$MAGICK_FONT_LIGHT" ]] && MAGICK_FONT_LIGHT="STHeiti-Light"

echo "添加文字叠加..." >&2
[[ -n "$LOGO_PATH" ]] && echo "使用 Logo: $(basename $LOGO_PATH)" >&2

# 获取图片尺寸
DIMENSIONS=$("$MAGICK" "$INPUT" -ping -format "%w %h" info:)
WIDTH=$(echo $DIMENSIONS | cut -d' ' -f1)
HEIGHT=$(echo $DIMENSIONS | cut -d' ' -f2)

# Logo 位置: 左上角
LOGO_X=$((WIDTH * 5 / 100))
LOGO_Y=$((HEIGHT * 4 / 100))

# 横幅遮罩尺寸
BAND_WIDTH=$WIDTH
BAND_HEIGHT=$((HEIGHT * 18 / 100))

TEMP1=$(mktemp).png
cleanup() {
    rm -f "$TEMP1"
}
trap cleanup EXIT

# 第一步：中央横幅遮罩
"$MAGICK" "$INPUT" \
    \( -size "${BAND_WIDTH}x${BAND_HEIGHT}" \
       xc:"rgba(0,0,0,0.45)" \
       -gravity center \) \
    -geometry +0-10 \
    -compose over -composite "$TEMP1"

# 第二步：大标题（带阴影效果）
"$MAGICK" "$TEMP1" \
    -font "$MAGICK_FONT_BOLD" -pointsize 130 \
    -fill "rgba(0,0,0,0.55)" \
    -gravity center \
    -annotate +0-12 "$TITLE" \
    -font "$MAGICK_FONT_BOLD" -pointsize 100 \
    -fill "white" \
    -gravity center \
    -annotate +0+10 "$TITLE" \
    "$TEMP1"

# 第三步：副标题（带装饰线）
if [[ -n "$SUBTITLE" ]]; then
    "$MAGICK" "$TEMP1" \
        \( -size "120x3" xc:"rgba(255,100,100,0.8)" \) \
        -gravity center -geometry +0+140 -compose over -composite \
        -font "$MAGICK_FONT_LIGHT" -pointsize 45 \
        -fill "rgba(255,255,255,0.95)" \
        -gravity center \
        -annotate +0+180 "$SUBTITLE" \
        "$TEMP1"
fi

# 第四步：Logo（如果存在）
if [[ -n "$LOGO_PATH" && -f "$LOGO_PATH" ]]; then
    LOGO_SIZE=$((WIDTH * 22 / 100))
    TEMP_LOGO=$(mktemp).png
    "$MAGICK" "$LOGO_PATH" -resize "${LOGO_SIZE}x${LOGO_SIZE}" "$TEMP_LOGO"
    "$MAGICK" "$TEMP1" "$TEMP_LOGO" -geometry "+${LOGO_X}+${LOGO_Y}" -compose over -composite "$OUTPUT"
    rm -f "$TEMP_LOGO"
else
    cp "$TEMP1" "$OUTPUT"
fi

echo "完成: $OUTPUT" >&2
echo "$OUTPUT"
