#!/bin/bash
# xiaohongshu-content-finance 技能一键安装脚本
# 用法: ./install.sh [--check-only]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_info() {
    echo -e "    $1"
}

# 检查命令是否存在
check_command() {
    command -v "$1" &> /dev/null
}

# 检查并安装 Homebrew
check_brew() {
    print_header "检查 Homebrew"
    if check_command brew; then
        print_success "Homebrew 已安装"
        return 0
    fi

    print_warning "Homebrew 未安装"
    read -p "是否安装 Homebrew? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [[ $? -eq 0 ]]; then
            print_success "Homebrew 安装成功"
            # 添加到 PATH（适用于 Apple Silicon）
            if [[ -d "/opt/homebrew/bin" ]]; then
                export PATH="/opt/homebrew/bin:$PATH"
            fi
            return 0
        else
            print_error "Homebrew 安装失败"
            return 1
        fi
    else
        print_error "需要 Homebrew 来安装依赖"
        return 1
    fi
}

# 检查并安装 ImageMagick
check_imagemagick() {
    print_header "检查 ImageMagick"

    if check_command magick; then
        local version=$(magick -version | head -n1)
        print_success "ImageMagick 已安装: $version"
        return 0
    fi

    if check_command convert; then
        local version=$(convert -version | head -n1)
        print_success "ImageMagick 已安装: $version"
        return 0
    fi

    print_warning "ImageMagick 未安装"
    read -p "是否安装 ImageMagick? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        brew install imagemagick
        if [[ $? -eq 0 ]]; then
            print_success "ImageMagick 安装成功"
            return 0
        else
            print_error "ImageMagick 安装失败"
            return 1
        fi
    else
        print_error "需要 ImageMagick 来生成封面图"
        return 1
    fi
}

# 检查 Python 3
check_python3() {
    print_header "检查 Python 3"

    if check_command python3; then
        local version=$(python3 --version)
        print_success "Python 已安装: $version"
        return 0
    fi

    print_warning "Python 3 未安装"
    print_info "macOS 通常自带 Python 3，或通过 Homebrew 安装"
    read -p "是否安装 Python 3? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        brew install python3
        if [[ $? -eq 0 ]]; then
            print_success "Python 3 安装成功"
            return 0
        else
            print_error "Python 3 安装失败"
            return 1
        fi
    else
        print_error "需要 Python 3 来运行脚本"
        return 1
    fi
}

# 检查并安装 uv
check_uv() {
    print_header "检查 uv (Python 包管理器)"

    if check_command uv; then
        local version=$(uv --version)
        print_success "uv 已安装: $version"
        return 0
    fi

    print_warning "uv 未安装"
    read -p "是否安装 uv? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        if [[ $? -eq 0 ]]; then
            # 添加到 PATH
            export PATH="$HOME/.cargo/bin:$PATH"
            # 也可能是 .local/bin
            if [[ -d "$HOME/.local/bin" ]]; then
                export PATH="$HOME/.local/bin:$PATH"
            fi
            print_success "uv 安装成功"
            return 0
        else
            print_error "uv 安装失败"
            return 1
        fi
    else
        print_error "需要 uv 来运行 Python 依赖"
        return 1
    fi
}

# 检查 GEMINI_API_KEY
check_gemini_key() {
    print_header "检查 GEMINI_API_KEY"

    local config_file="$HOME/.openclaw/openclaw.json"
    local key_found=false

    if [[ -f "$config_file" ]]; then
        if grep -q "GEMINI_API_KEY" "$config_file" 2>/dev/null; then
            print_success "GEMINI_API_KEY 已配置"
            return 0
        fi
    fi

    if [[ -n "$GEMINI_API_KEY" ]]; then
        print_success "GEMINI_API_KEY 环境变量已设置"
        return 0
    fi

    print_warning "GEMINI_API_KEY 未配置"
    print_info "用于 AI 封面图生成"
    echo
    print_info "获取 API Key:"
    print_info "  1. 访问 https://makersuite.google.com/app/apikey"
    print_info "  2. 创建新的 API Key"
    echo
    read -p "是否现在配置? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "请输入 GEMINI_API_KEY: " -s api_key
        echo

        if [[ -z "$api_key" ]]; then
            print_error "API Key 不能为空"
            return 1
        fi

        # 创建配置目录
        mkdir -p "$(dirname "$config_file")"

        # 更新或创建配置文件
        if [[ -f "$config_file" ]]; then
            # 使用 Python 来更新 JSON
            python3 -c "
import json
import sys

config_file = '$config_file'
api_key = '$api_key'

try:
    with open(config_file, 'r') as f:
        config = json.load(f)
except:
    config = {}

if 'env' not in config:
    config['env'] = {}
config['env']['GEMINI_API_KEY'] = api_key

with open(config_file, 'w') as f:
    json.dump(config, f, indent=2)
" 2>/dev/null
        else
            echo '{"env":{"GEMINI_API_KEY":"'"$api_key"'"}}' > "$config_file"
        fi

        print_success "GEMINI_API_KEY 已保存到 $config_file"
        return 0
    else
        print_warning "跳过 API Key 配置，后续使用时需要手动设置"
        return 0
    fi
}

# 检查并安装 nano-banana-pro 技能
check_nano_banana_pro() {
    print_header "检查 nano-banana-pro 技能"

    local skill_path="$HOME/.openclaw/skills/nano-banana-pro"

    if [[ -d "$skill_path" ]]; then
        print_success "nano-banana-pro 技能已安装"
        return 0
    fi

    print_warning "nano-banana-pro 技能未安装"
    print_info "用于 AI 背景图生成"
    echo
    read -p "是否安装 nano-banana-pro 技能? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # 假设通过 openclaw CLI 安装
        if check_command openclaw; then
            openclaw skill install nano-banana-pro 2>/dev/null || {
                print_warning "无法通过 CLI 安装，请手动克隆"
                print_info "git clone https://github.com/your-repo/nano-banana-pro.git $skill_path"
            }
        else
            print_info "请手动安装 nano-banana-pro 技能"
            print_info "安装路径: $skill_path"
        fi
        return 0
    else
        print_warning "nano-banana-pro 未安装，封面图生成可能失败"
        return 0
    fi
}

# 检查 openclaw CLI
check_openclaw() {
    print_header "检查 openclaw CLI"

    if check_command openclaw; then
        local version=$(openclaw --version 2>/dev/null || echo "unknown")
        print_success "openclaw CLI 已安装: $version"
        return 0
    fi

    print_warning "openclaw CLI 未安装"
    print_info "需要 openclaw CLI 来发送 Telegram 消息"
    echo
    read -p "是否现在安装 openclaw CLI? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "请访问 https://github.com/openclaw/openclaw 获取安装说明"
        npm install -g @openclaw/cli 2>/dev/null || {
            print_error "openclaw CLI 安装失败，请手动安装"
            return 1
        }
        return 0
    else
        print_warning "跳过 openclaw CLI 安装，Telegram 发送功能将不可用"
        return 0
    fi
}

# 检查 Telegram 配置
check_telegram() {
    print_header "检查 Telegram 配置"

    if [[ -n "$TELEGRAM_ACCOUNT" ]]; then
        print_success "TELEGRAM_ACCOUNT 已设置: $TELEGRAM_ACCOUNT"
    else
        print_info "TELEGRAM_ACCOUNT 未设置（将使用默认值: default）"
    fi

    if [[ -n "$TELEGRAM_TARGET" ]]; then
        print_success "TELEGRAM_TARGET 已设置: $TELEGRAM_TARGET"
    else
        print_info "TELEGRAM_TARGET 未设置（从 Telegram 激活时自动回复）"
    fi

    return 0
}

# 设置脚本权限
setup_permissions() {
    print_header "设置脚本权限"

    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    chmod +x "$script_dir/generate_cover.sh" 2>/dev/null
    chmod +x "$script_dir/send_telegram.sh" 2>/dev/null
    chmod +x "$script_dir/add_overlay.sh" 2>/dev/null
    chmod +x "$script_dir/install.sh" 2>/dev/null
    chmod +x "$script_dir/check.sh" 2>/dev/null

    print_success "脚本权限已设置"
}

# 主安装流程
main() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════╗"
    echo "║          xiaohongshu-content-finance 技能安装向导                      ║"
    echo "║      小红书内容生成系统 - 一键安装                      ║"
    echo "╚═══════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    local check_only=false
    if [[ "$1" == "--check-only" ]]; then
        check_only=true
        print_info "仅检查模式，不进行安装"
    fi

    local failed=0

    # 检查/安装依赖
    check_brew || failed=$((failed + 1))
    check_imagemagick || failed=$((failed + 1))
    check_python3 || failed=$((failed + 1))
    check_uv || failed=$((failed + 1))
    check_gemini_key || failed=$((failed + 1))
    check_nano_banana_pro || failed=$((failed + 1))
    check_openclaw || failed=$((failed + 1))
    check_telegram || failed=$((failed + 1))
    setup_permissions

    # 总结
    echo
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}安装总结${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

    if [[ $failed -eq 0 ]]; then
        print_success "所有依赖检查完成！"
        echo
        print_info "使用方法:"
        print_info "  /skill:xiaohongshu-content-finance --topic=\"你的主题\" --vertical=\"领域\""
        echo
        return 0
    else
        print_warning "有 $failed 项检查未通过，部分功能可能不可用"
        echo
        print_info "运行以下命令重新检查:"
        print_info "  ~/.openclaw/skills/xiaohongshu-content-finance/scripts/check.sh"
        echo
        return 1
    fi
}

# 执行主流程
main "$@"
