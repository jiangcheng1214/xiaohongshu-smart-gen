#!/bin/bash
# 生成小红书封面图（3:4 竖版）- 两步法：背景+文字
# 用法: ./generate_cover.sh "标题" "副标题" "输出路径"

set -e

TITLE="$1"
SUBTITLE="${2:-}"
OUTPUT="${3:-/tmp/xhs_cover_$(date +%s).png}"
TEMP_BG="/tmp/xhs_cover_bg_$(date +%s).png"
NANO_BANANA_SCRIPT="/opt/homebrew/lib/node_modules/openclaw/skills/nano-banana-pro/scripts/generate_image.py"

# Logo 路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGO_PATH="$SCRIPT_DIR/../assets/logo.png"

# 从 openclaw.json 读取 GEMINI_API_KEY
CONFIG_FILE="$HOME/.openclaw/openclaw.json"
if [[ -f "$CONFIG_FILE" ]]; then
    API_KEY=$(cat "$CONFIG_FILE" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    key = d.get('env', {}).get('GEMINI_API_KEY', '')
    if not key:
        key = d.get('skills', {}).get('entries', {}).get('nano-banana-pro', {}).get('apiKey', '')
    print(key)
except:
    pass
" 2>/dev/null)
fi

if [[ -z "$API_KEY" ]]; then
    API_KEY="${GEMINI_API_KEY:-}"
fi

# 第一步：生成背景图
echo "Step 1: Generating background..."
BG_PROMPT="Modern city skyline at night, Shanghai Lujiazui skyscrapers with city lights, urban night photography, cinematic lighting, 3:4 portrait, no text, no words, no letters."

TEMP_OUTPUT=$(mktemp)

if [[ -n "$API_KEY" ]]; then
    if ! uv run "$NANO_BANANA_SCRIPT" \
        --prompt "$BG_PROMPT" \
        --filename "$TEMP_BG" \
        --aspect-ratio 3:4 \
        --resolution 2K \
        --api-key "$API_KEY" 2>&1 | tee "$TEMP_OUTPUT" | grep -v "^MEDIA:"; then
        cat "$TEMP_OUTPUT" >&2
        rm -f "$TEMP_OUTPUT"
        echo "生成背景图失败"
        exit 1
    fi
else
    if ! uv run "$NANO_BANANA_SCRIPT" \
        --prompt "$BG_PROMPT" \
        --filename "$TEMP_BG" \
        --aspect-ratio 3:4 \
        --resolution 2K 2>&1 | tee "$TEMP_OUTPUT" | grep -v "^MEDIA:"; then
        cat "$TEMP_OUTPUT" >&2
        rm -f "$TEMP_OUTPUT"
        echo "生成背景图失败"
        exit 1
    fi
fi
rm -f "$TEMP_OUTPUT"

if [[ ! -f "$TEMP_BG" ]]; then
    echo "背景图文件未生成: $TEMP_BG"
    exit 1
fi

# 第二步：添加文字叠加
echo "Step 2: Adding text overlay..."

if command -v magick &> /dev/null; then
    MAGICK="magick"
elif command -v convert &> /dev/null; then
    MAGICK="convert"
else
    echo "警告: 未找到 ImageMagick"
    cp "$TEMP_BG" "$OUTPUT"
    rm -f "$TEMP_BG"
    echo "$OUTPUT"
    exit 0
fi

# 检查 Logo 是否存在
if [[ ! -f "$LOGO_PATH" ]]; then
    echo "警告: Logo 文件不存在: $LOGO_PATH，将使用默认文字 Logo"
    USE_TEXT_LOGO=true
else
    USE_TEXT_LOGO=false
fi

MAGICK_FONT_BOLD="/System/Library/Fonts/STHeiti Medium.ttc"
MAGICK_FONT_LIGHT="/System/Library/Fonts/STHeiti Light.ttc"

[[ ! -f "$MAGICK_FONT_BOLD" ]] && MAGICK_FONT_BOLD="STHeiti-Medium"
[[ ! -f "$MAGICK_FONT_LIGHT" ]] && MAGICK_FONT_LIGHT="STHeiti-Light"

# 获取图片尺寸
DIMENSIONS=$("$MAGICK" "$TEMP_BG" -ping -format "%w %h" info:)
WIDTH=$(echo $DIMENSIONS | cut -d' ' -f1)
HEIGHT=$(echo $DIMENSIONS | cut -d' ' -f2)

# Logo 位置: 左上角
LOGO_X=$((WIDTH * 28 / 100))
LOGO_Y=$((HEIGHT * 41 / 100))

# 横幅遮罩尺寸
BAND_WIDTH=$WIDTH
BAND_HEIGHT=$((HEIGHT * 22 / 100))

TEMP1=$(mktemp).png
cleanup() {
    rm -f "$TEMP1" "$TEMP_BG"
}
trap cleanup EXIT

# 中央横幅遮罩
"$MAGICK" "$TEMP_BG" \
    \( -size "${BAND_WIDTH}x${BAND_HEIGHT}" \
       xc:"rgba(0,0,0,0.75)" \
       -gravity center \) \
    -compose over -composite "$TEMP1"

# 大标题
"$MAGICK" "$TEMP1" \
    -font "$MAGICK_FONT_BOLD" -pointsize 150 \
    -fill "rgba(0,0,0,0.5)" \
    -gravity center \
    -annotate +2+12 "$TITLE" \
    -font "$MAGICK_FONT_BOLD" -pointsize 150 \
    -fill "white" \
    -gravity center \
    -annotate +0+10 "$TITLE" \
    "$TEMP1"

# 副标题（间距加倍）
"$MAGICK" "$TEMP1" \
    \( -size "120x3" xc:"rgba(255,100,100,0.8)" \) \
    -gravity center -geometry +0+160 -compose over -composite \
    -font "$MAGICK_FONT_LIGHT" -pointsize 38 \
    -fill "rgba(255,255,255,0.95)" \
    -gravity center \
    -annotate +0+200 "${SUBTITLE:-量化分析}" \
    "$TEMP1"

# Logo（使用本地图片或文字）
if [[ "$USE_TEXT_LOGO" = true ]]; then
    # 使用文字 Logo
    "$MAGICK" "$TEMP1" \
        \( -size "170x55" xc:none \
           -fill "#E84142" \
           -draw "roundrectangle 0,0 170,55 10,10" \
           -fill "white" \
           -font "$MAGICK_FONT_BOLD" -pointsize 28 \
           -gravity center -annotate +0+1 "小红书财经" \
        \) \
        -gravity northwest -geometry "+${LOGO_X}+${LOGO_Y}" \
        -compose over -composite \
        "$OUTPUT"
else
    # 使用本地 Logo 图片
    LOGO_SIZE=$((WIDTH * 10 / 100))
    TEMP_LOGO=$(mktemp).png
    "$MAGICK" "$LOGO_PATH" -resize "${LOGO_SIZE}x${LOGO_SIZE}" "$TEMP_LOGO"
    "$MAGICK" "$TEMP1" "$TEMP_LOGO" -geometry "+${LOGO_X}+${LOGO_Y}" -compose over -composite "$OUTPUT"
    rm -f "$TEMP_LOGO"
fi

echo "Step 3: Cover generated at $OUTPUT"
echo "$OUTPUT"
