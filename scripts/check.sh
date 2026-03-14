#!/bin/bash
# xiaohongshu-content-finance 技能依赖检查脚本
# 用法: ./check.sh [--verbose]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 检查结果统计
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0

# 打印函数
print_header() {
    echo -e "${BLUE}▶${NC} $1"
}

print_ok() {
    echo -e "${GREEN}✓${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    CHECKS_WARNING=$((CHECKS_WARNING + 1))
}

print_info() {
    echo -e "${CYAN}ℹ${NC} $1"
}

# 检查命令是否存在
check_command() {
    command -v "$1" &> /dev/null
}

# 检查 ImageMagick
check_imagemagick() {
    print_header "ImageMagick (图片处理)"

    if check_command magick; then
        local version=$(magick -version 2>/dev/null | head -n1 | sed -n 's/.*Version: ImageMagick \([0-9.]*\).*/\1/p' || echo "unknown")
        print_ok "ImageMagick 已安装 (版本: $version)"
        return 0
    fi

    if check_command convert; then
        local version=$(convert -version 2>/dev/null | head -n1 | sed -n 's/.*Version: ImageMagick \([0-9.]*\).*/\1/p' || echo "unknown")
        print_ok "ImageMagick 已安装 (版本: $version)"
        return 0
    fi

    print_fail "ImageMagick 未安装"
    print_info "  安装: brew install imagemagick"
    echo
    return 1
}

# 检查 Python 3
check_python3() {
    print_header "Python 3"

    if check_command python3; then
        local version_output=$(python3 --version 2>&1)
        local version=$(echo "$version_output" | sed -n 's/.* \([0-9]\+\.[0-9]\+\.[0-9]\+\).*/\1/p')
        [[ -z "$version" ]] && version=$(echo "$version_output" | sed -n 's/.* \([0-9]\+\.[0-9]\+\).*/\1/p')

        local major=$(echo "$version" | cut -d'.' -f1)
        local minor=$(echo "$version" | cut -d'.' -f2)

        if [[ "$major" == "3" ]] && [[ "$minor" -ge 8 ]] 2>/dev/null; then
            print_ok "Python 3 已安装 (版本: $version)"
        elif [[ -n "$major" ]]; then
            print_warn "Python 版本: $version (建议 3.8+)"
        else
            print_ok "Python 3 已安装"
        fi
        return 0
    fi

    print_fail "Python 3 未安装"
    print_info "  安装: brew install python3"
    echo
    return 1
}

# 检查 uv
check_uv() {
    print_header "uv (Python 包管理器)"

    if check_command uv; then
        local version=$(uv --version 2>&1 | head -n1 | sed -n 's/.*\([0-9]\+\.[0-9]\+\.[0-9]\+\).*/\1/p' || echo "unknown")
        print_ok "uv 已安装 (版本: $version)"
        return 0
    fi

    print_fail "uv 未安装"
    print_info "  安装: curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo
    return 1
}

# 检查 GEMINI_API_KEY
check_gemini_key() {
    print_header "GEMINI_API_KEY"

    local config_file="$HOME/.openclaw/openclaw.json"
    local key_found=false
    local key_source=""

    if [[ -f "$config_file" ]]; then
        if python3 -c "import json; c=json.load(open('$config_file')); print('env' in c and 'GEMINI_API_KEY' in c['env'])" 2>/dev/null | grep -q True; then
            key_found=true
            key_source="配置文件"
        fi
    fi

    if [[ -n "$GEMINI_API_KEY" ]]; then
        key_found=true
        key_source="环境变量"
    fi

    if $key_found; then
        print_ok "GEMINI_API_KEY 已配置 ($key_source)"
    else
        print_fail "GEMINI_API_KEY 未配置"
        print_info "  获取: https://makersuite.google.com/app/apikey"
        print_info "  配置: 添加到 ~/.openclaw/openclaw.json 的 env 字段"
        echo
    fi
    return 0
}

# 检查 nano-banana-pro 技能
check_nano_banana_pro() {
    print_header "nano-banana-pro 技能"

    local skill_path="$HOME/.openclaw/skills/nano-banana-pro"
    local script_path="$skill_path/scripts/generate_image.py"

    if [[ -d "$skill_path" ]]; then
        if [[ -f "$script_path" ]]; then
            print_ok "nano-banana-pro 技能已安装"
        else
            print_warn "nano-banana-pro 技能存在但脚本缺失: $script_path"
        fi
    else
        print_fail "nano-banana-pro 技能未安装"
        print_info "  安装: openclaw skill install nano-banana-pro"
        print_info "  路径: $skill_path"
        echo
    fi
    return 0
}

# 检查 openclaw CLI
check_openclaw() {
    print_header "openclaw CLI"

    if check_command openclaw; then
        local version=$(openclaw --version 2>/dev/null || echo "unknown")
        print_ok "openclaw CLI 已安装"
    else
        print_warn "openclaw CLI 未安装"
        print_info "  安装: npm install -g @openclaw/cli"
        print_info "  影响: Telegram 发送功能将不可用"
        echo
    fi
    return 0
}

# 检查 Telegram 配置
check_telegram() {
    print_header "Telegram 配置"

    if [[ -n "$TELEGRAM_ACCOUNT" ]]; then
        print_ok "TELEGRAM_ACCOUNT: $TELEGRAM_ACCOUNT"
    else
        print_info "TELEGRAM_ACCOUNT 未设置 (将使用默认值: default)"
    fi

    if [[ -n "$TELEGRAM_TARGET" ]]; then
        print_info "TELEGRAM_TARGET: $TELEGRAM_TARGET"
    else
        print_info "TELEGRAM_TARGET 未设置 (从 Telegram 激活时自动回复)"
    fi
    echo
    return 0
}

# 检查字体
check_fonts() {
    print_header "中文字体"

    local font_found=false
    local fonts=(
        "/System/Library/Fonts/STHeiti Medium.ttc"
        "/System/Library/Fonts/STHeiti Light.ttc"
        "/System/Library/Fonts/PingFang.ttc"
        "/System/Library/Fonts/Helvetica.ttc"
    )

    for font in "${fonts[@]}"; do
        if [[ -f "$font" ]]; then
            font_found=true
            print_ok "中文字体已安装: $(basename "$font")"
            break
        fi
    done

    if ! $font_found; then
        print_warn "未找到推荐中文字体，可能影响封面图生成"
    fi
    echo
    return 0
}

# 检查脚本权限
check_permissions() {
    print_header "脚本权限"

    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local scripts=(
        "generate_cover.sh"
        "send_telegram.sh"
        "add_overlay.sh"
    )

    local all_executable=true
    for script in "${scripts[@]}"; do
        local path="$script_dir/$script"
        if [[ -f "$path" ]]; then
            if [[ -x "$path" ]]; then
                print_ok "$script 可执行"
            else
                print_warn "$script 不可执行"
                all_executable=false
            fi
        fi
    done

    if ! $all_executable; then
        print_info "  修复: chmod +x ~/.openclaw/skills/xiaohongshu-content-finance/scripts/*.sh"
    fi
    echo
    return 0
}

# 打印总结
print_summary() {
    echo
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}检查总结${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"

    echo -e "  ${GREEN}通过${NC}: $CHECKS_PASSED"
    echo -e "  ${YELLOW}警告${NC}: $CHECKS_WARNING"
    echo -e "  ${RED}失败${NC}: $CHECKS_FAILED"
    echo

    if [[ $CHECKS_FAILED -eq 0 ]]; then
        echo -e "${GREEN}✓ 所有必需依赖已满足！${NC}"
        echo
        echo -e "使用方法:"
        echo -e "  ${CYAN}/skill:xiaohongshu-content-finance --topic=\"你的主题\" --vertical=\"领域\"${NC}"
        echo
        return 0
    else
        echo -e "${RED}✗ 有 $CHECKS_FAILED 项检查未通过${NC}"
        echo
        echo -e "运行安装脚本:"
        echo -e "  ${CYAN}~/.openclaw/skills/xiaohongshu-content-finance/scripts/install.sh${NC}"
        echo
        return 1
    fi
}

# 主检查流程
main() {
    local verbose=false
    if [[ "$1" == "--verbose" ]] || [[ "$1" == "-v" ]]; then
        verbose=true
    fi

    echo -e "${BLUE}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║          xiaohongshu-content-finance 依赖检查                          ║${NC}"
    echo -e "${BLUE}╚═══════════════════════════════════════════════════════╝${NC}"
    echo

    check_imagemagick
    check_python3
    check_uv
    check_gemini_key
    check_nano_banana_pro
    check_openclaw
    check_telegram
    check_fonts
    check_permissions

    print_summary
}

# 执行主流程
main "$@"
