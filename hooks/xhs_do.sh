#!/bin/bash
# 小红书内容生成 - 确定性执行命令 (Python 入口)
# 用法: xhs-do <垂类> "<精确话题>"
#
# 设计原则:
# 1. 话题必须用引号包裹，防止AI解读
# 2. 不做任何自动纠正或推断
# 3. 使用用户提供的精确输入

# 解析实际脚本路径（处理symlink情况）
SCRIPT_SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SCRIPT_SOURCE" ]; do
    SCRIPT_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")" && pwd)"
    SCRIPT_SOURCE="$(readlink "$SCRIPT_SOURCE")"
    [[ $SCRIPT_SOURCE != /* ]] && SCRIPT_SOURCE="$SCRIPT_DIR/$SCRIPT_SOURCE"
done
SKILL_DIR="$(cd "$(dirname "$SCRIPT_SOURCE")/.." && pwd)"

VERTICAL="${1:-finance}"
TOPIC="${2:-}"
ACTION="${3:---all}"

if [[ -z "$TOPIC" ]]; then
    echo "用法: xhs-do <垂类> <精确话题> [action]" >&2
    echo "" >&2
    echo "Actions:" >&2
    echo "  --init    初始化新session" >&2
    echo "  --content 生成文字内容" >&2
    echo "  --images  搜索参考图片" >&2
    echo "  --cover   生成封面" >&2
    echo "  --all     执行全部步骤 (默认)" >&2
    echo "  --send    发送到Telegram" >&2
    echo "" >&2
    echo "示例:" >&2
    echo "  xhs-do finance \"错过了lite怎么办\"" >&2
    echo "  xhs-do tech \"GTC大会总结\"" >&2
    echo "  xhs-do beauty \"春季口红推荐\"" >&2
    exit 1
fi

echo "# === 小红书内容生成（确定性模式）===" >&2
echo "# 垂类: $VERTICAL" >&2
echo "# 话题: $TOPIC" >&2
echo "# 模式: STRICT - 使用精确输入，不做AI纠正" >&2
echo "" >&2

# 调用 Python 版本
python3 "$SKILL_DIR/scripts/xhs_do.py" "$VERTICAL" "$TOPIC" "$ACTION"
