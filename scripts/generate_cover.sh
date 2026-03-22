#!/bin/bash
# 生成小红书封面图（3:4 竖版）- 两步法：背景+文字
# 用法: ./generate_cover.sh <vertical> "标题" "副标题" "输出路径"

set -e

VERTICAL="${1:-finance}"
TITLE="$2"
SUBTITLE="${3:-}"
OUTPUT="${4:-/tmp/xhs_cover_$(date +%s).png}"
TEMP_BG="/tmp/xhs_cover_bg_$(date +%s).png"
NANO_BANANA_SCRIPT="/opt/homebrew/lib/node_modules/openclaw/skills/nano-banana-pro/scripts/generate_image.py"

# 技能目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 加载垂类配置
VERTICAL_CONFIG="$SKILL_DIR/verticals/$VERTICAL.json"

# 检查垂类配置是否存在
if [[ ! -f "$VERTICAL_CONFIG" ]]; then
    echo "Warning: Vertical config not found: $VERTICAL_CONFIG" >&2
    echo "Using default finance configuration" >&2
    VERTICAL_CONFIG="$SKILL_DIR/verticals/finance.json"
fi

# 获取 Logo 路径（带三级回退逻辑）
get_logo_path() {
    local config="$1"
    local skill_dir="$2"

    # 1. 尝试配置中的 logo_file
    local logo_file=$(python3 -c "import json; c=json.load(open('$config')); print(c['cover_config'].get('logo_file', ''))" 2>/dev/null || echo "")
    if [[ -n "$logo_file" ]]; then
        local config_path="$skill_dir/assets/logo/$logo_file"
        if [[ -f "$config_path" ]]; then
            echo "$config_path"
            return 0
        fi
    fi

    # 2. 尝试 {vertical}.png
    local vertical_path="$skill_dir/assets/logo/$VERTICAL.png"
    if [[ -f "$vertical_path" ]]; then
        echo "$vertical_path"
        return 0
    fi

    # 3. 回退到 default.png
    echo "$skill_dir/assets/logo/default.png"
    return 0
}

LOGO_PATH=$(get_logo_path "$VERTICAL_CONFIG" "$SKILL_DIR")

# 提取其他配置
DEFAULT_SUBTITLE=$(python3 -c "import json; c=json.load(open('$VERTICAL_CONFIG')); print(c['cover_config'].get('default_subtitle', '分享'))" 2>/dev/null || echo "分享")
STYLE_PREFIX=$(python3 -c "import json; c=json.load(open('$VERTICAL_CONFIG')); print(c['cover_config'].get('style_prefix', 'Modern background'))" 2>/dev/null || echo "Modern background")

# 如果没有提供副标题，使用垂类默认值
if [[ -z "$SUBTITLE" ]]; then
    SUBTITLE="$DEFAULT_SUBTITLE"
fi

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
echo "# Generating background for vertical: $VERTICAL..." >&2

# 从配置加载配色方案和装饰元素
COLOR_SCHEMES_FILE=$(mktemp)
DECORATION_FILE=$(mktemp)

python3 -c "
import json
try:
    c = json.load(open('$VERTICAL_CONFIG'))
    schemes = c['cover_config'].get('color_schemes', ['deep blue to purple gradient'])
    for s in schemes:
        print(s)
except:
    print('deep blue to purple gradient')
" > "$COLOR_SCHEMES_FILE"

python3 -c "
import json
try:
    c = json.load(open('$VERTICAL_CONFIG'))
    decors = c['cover_config'].get('decorations', ['subtle geometric patterns'])
    for d in decors:
        print(d)
except:
    print('subtle geometric patterns')
" > "$DECORATION_FILE"

# 计算行数并随机选择
COLOR_COUNT=$(wc -l < "$COLOR_SCHEMES_FILE" | tr -d ' ')
DECOR_COUNT=$(wc -l < "$DECORATION_FILE" | tr -d ' ')

COLOR_IDX=$((RANDOM % COLOR_COUNT + 1))
DECOR_IDX=$((RANDOM % DECOR_COUNT + 1))

SELECTED_COLOR=$(sed -n "${COLOR_IDX}p" "$COLOR_SCHEMES_FILE")
SELECTED_DECOR=$(sed -n "${DECOR_IDX}p" "$DECORATION_FILE")

rm -f "$COLOR_SCHEMES_FILE" "$DECORATION_FILE"

# 构建 prompt
TEMP_PROMPT=$(mktemp)
cat > "$TEMP_PROMPT" << EOF
${STYLE_PREFIX}, ${SELECTED_COLOR}, ${SELECTED_DECOR}, clean modern background in elegant design, flat style, 3:4 portrait, no text, no words, no letters, minimal aesthetic.
EOF

echo "# Color scheme: ${SELECTED_COLOR}" >&2
echo "# Decoration: ${SELECTED_DECOR}" >&2
echo "# Logo: $(basename $LOGO_PATH)" >&2
echo "# Subtitle: ${SUBTITLE}" >&2

TEMP_OUTPUT=$(mktemp)

# 尝试生成背景图
API_SUCCESS=false
if [[ -n "$API_KEY" ]]; then
    if uv run "$NANO_BANANA_SCRIPT" \
        --prompt "$(cat "$TEMP_PROMPT")" \
        --filename "$TEMP_BG" \
        --aspect-ratio 3:4 \
        --resolution 1K \
        --api-key "$API_KEY" 2>&1 | tee "$TEMP_OUTPUT" | grep -v "^MEDIA:"; then
        if [[ -f "$TEMP_BG" ]]; then
            API_SUCCESS=true
        fi
    fi
else
    if uv run "$NANO_BANANA_SCRIPT" \
        --prompt "$(cat "$TEMP_PROMPT")" \
        --filename "$TEMP_BG" \
        --aspect-ratio 3:4 \
        --resolution 1K 2>&1 | tee "$TEMP_OUTPUT" | grep -v "^MEDIA:"; then
        if [[ -f "$TEMP_BG" ]]; then
            API_SUCCESS=true
        fi
    fi
fi
rm -f "$TEMP_OUTPUT"

# 如果 API 失败，使用本地生成的复杂背景
if [[ "$API_SUCCESS" = false ]]; then
    echo "# AI 背景生成失败，使用备用复杂背景" >&2

    # 从配色方案中提取颜色关键词，转换为具体颜色
    case "$SELECTED_COLOR" in
        *blue*|*violet*|*purple*|*navy*)
            PRIMARY_COLOR="#0f0c29"
            SECONDARY_COLOR="#302b63"
            ACCENT_COLOR="#24243e"
            ;;
        *gold*|*amber*|*orange*|*peach*|*honey*|*coral*)
            PRIMARY_COLOR="#1a1a2e"
            SECONDARY_COLOR="#4a3f35"
            ACCENT_COLOR="#c9a227"
            ;;
        *green*|*teal*)
            PRIMARY_COLOR="#0d1b1e"
            SECONDARY_COLOR="#1b3a35"
            ACCENT_COLOR="#2d6a4f"
            ;;
        *pink*|*rose*)
            PRIMARY_COLOR="#1a0b14"
            SECONDARY_COLOR="#3d1f2d"
            ACCENT_COLOR="#c9184a"
            ;;
        *)
            PRIMARY_COLOR="#0f0c29"
            SECONDARY_COLOR="#302b63"
            ACCENT_COLOR="#24243e"
            ;;
    esac

    # 使用 ImageMagick 创建复杂背景
    if command -v magick &> /dev/null; then
        MAGICK="magick"
    elif command -v convert &> /dev/null; then
        MAGICK="convert"
    else
        echo "未找到 ImageMagick，无法生成备用背景" >&2
        exit 1
    fi

    # 创建渐变背景
    "$MAGICK" -size "1080x1440" gradient:"${PRIMARY_COLOR}-${SECONDARY_COLOR}" "$TEMP_BG"

    # 添加几何装饰图案
    TEMP_PATTERN=$(mktemp).png
    "$MAGICK" -size "1080x1440" xc:none \
        -draw "circle 540,720 540,100" \
        -draw "circle 200,300 200,50" \
        -draw "circle 880,1140 880,50" \
        -fill "rgba(255,255,255,0.03)" -draw "rectangle 100,100 980,1340" \
        "$TEMP_PATTERN"

    # 合成
    "$MAGICK" "$TEMP_BG" "$TEMP_PATTERN" -compose over -composite "$TEMP_BG"
    rm -f "$TEMP_PATTERN"
fi

if [[ ! -f "$TEMP_BG" ]]; then
    echo "背景图文件未生成: $TEMP_BG" >&2
    exit 1
fi

# 保存原始背景图副本
BG_BACKUP="${OUTPUT%.png}_bg.png"
cp "$TEMP_BG" "$BG_BACKUP"

# 第二步：调用 add_overlay.sh 添加文字叠加
echo "# Adding text overlay..." >&2
"$SCRIPT_DIR/add_overlay.sh" "$TEMP_BG" "$TITLE" "$SUBTITLE" "$OUTPUT" "$LOGO_PATH"

# 清理临时文件
rm -f "$TEMP_BG" "$TEMP_PROMPT"

# 输出封面路径
echo "$OUTPUT"
