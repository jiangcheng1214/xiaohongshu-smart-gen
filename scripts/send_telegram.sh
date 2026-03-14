#!/bin/bash
# 发送到 Telegram
# 用法: ./send_telegram.sh "标题" "正文内容" "封面图路径"

set -e

TITLE="$1"
BODY="$2"
COVER="${3:-}"
ACCOUNT="${TELEGRAM_ACCOUNT:-default}"
TARGET="${TELEGRAM_TARGET:-}"

# 展开 ~ 路径
if [[ -n "$COVER" ]]; then
    COVER="${COVER/#\~/$HOME}"
fi

# 构建消息
MESSAGE="📱 $TITLE

$BODY

---
生成时间: $(date '+%Y-%m-%d %H:%M')"

# 发送
if [[ -n "$COVER" && -f "$COVER" ]]; then
  echo "发送封面图: $COVER"
  if [[ -n "$TARGET" ]]; then
    openclaw message send \
      --channel telegram \
      --account "$ACCOUNT" \
      --target "$TARGET" \
      --message "$MESSAGE" \
      --media "$COVER"
  else
    # 从 Telegram 激活时，无需指定 target
    openclaw message send \
      --channel telegram \
      --account "$ACCOUNT" \
      --message "$MESSAGE" \
      --media "$COVER"
  fi
else
  echo "封面图不存在或未指定，只发送文字内容"
  if [[ -n "$TARGET" ]]; then
    openclaw message send \
      --channel telegram \
      --account "$ACCOUNT" \
      --target "$TARGET" \
      --message "$MESSAGE"
  else
    openclaw message send \
      --channel telegram \
      --account "$ACCOUNT" \
      --message "$MESSAGE"
  fi
fi

echo "Sent to Telegram: $TITLE"
