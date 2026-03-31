#!/usr/bin/env python3
"""
DEPRECATED: 此脚本的功能已整合到 steps.py 的 Step4PrepareImg 中。
变量解析现在通过各 vertical 的 cover_config.prompt_variables 配置驱动。
此文件保留用于向后兼容，将在未来版本中移除。

---
动态封面 prompt 构建器
用法: python3 build_dynamic_cover_prompt.py <vertical_config_path> <topic> [vertical]
输出: 填充好的封面 prompt（stdout），调试信息输出到 stderr
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


_ERROR_INDICATORS = [
    'rate limit', 'usage limit', 'unable to search', 'unable to retrieve',
    'cannot search', 'cannot retrieve', 'i apologize', 'apologize',
    'not available', 'no information', 'try checking', 'reset until',
    'i cannot', "i can't", 'service unavailable', 'search service',
    'recommend checking', 'for the most current',
]

def is_error_response(text: str) -> bool:
    if not text:
        return True
    t = text.lower()
    return any(ind in t for ind in _ERROR_INDICATORS)


def search_via_claude(prompt: str, timeout: int = 60) -> Optional[str]:
    """通过 Claude CLI 执行搜索"""
    try:
        result = subprocess.run(
            ['claude', '--dangerously-skip-permissions', '-p', prompt],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0 and result.stdout.strip():
            out = result.stdout.strip()
            if not is_error_response(out):
                return out
    except Exception as e:
        print(f"# search error: {e}", file=sys.stderr)
    return None


def fetch_price(stock_code: str) -> Optional[str]:
    """搜索股票价格"""
    prompt = f"""Search for: "{stock_code} stock price today"
Today: {datetime.now().strftime('%Y-%m-%d')}
Return ONLY the current price in format $XXX.XX with dollar sign. No explanation."""
    out = search_via_claude(prompt, timeout=60)
    if out:
        match = re.search(r'\$\s*(\d{1,5}\.\d{2})', out)
        if match:
            val = float(match.group(1))
            if val >= 1.0:
                return f'${match.group(1)}'
    return None


def fetch_change(stock_code: str) -> Optional[str]:
    """搜索股票涨跌幅"""
    prompt = f"""Search for: "{stock_code} stock percent change today"
Today: {datetime.now().strftime('%Y-%m-%d')}
Return ONLY today's percent change like +1.5% or -2.3%. No explanation."""
    out = search_via_claude(prompt, timeout=60)
    if out:
        match = re.search(r'([+-]?\d+\.?\d*)%', out)
        if match:
            pct = match.group(1)
            if not pct.startswith(('+', '-')):
                pct = '+' + pct
            return f'{pct}%'
    return None


def fetch_reason(stock_code: str) -> Optional[str]:
    """搜索股票变动原因"""
    prompt = f"""Search for: "{stock_code} stock news today catalyst"
Today: {datetime.now().strftime('%Y-%m-%d')}
What is the main reason {stock_code} stock is moving today?
Return ONLY 2-5 English words. Examples: 'AI chip demand', 'earnings beat expectations'.
Do NOT include 'According to', 'based on', or any URL."""
    out = search_via_claude(prompt, timeout=45)
    if out:
        line = out.strip().split('\n')[0]
        line = re.sub(r'^["\']|["\']$', '', line)
        line = re.sub(r'[.!?;,:\-]+$', '', line).lower()
        words = line.split()[:5]
        line = ' '.join(words)
        invalid = ['according to', 'based on', 'search result', 'unable to',
                   'not available', 'rate limit', 'usage limit', 'i found']
        if 2 <= len(words) <= 5 and line.isascii() and not any(p in line for p in invalid):
            return line
    return None


def fetch_product_name(stock_code: str) -> Optional[str]:
    """获取公司旗舰产品描述"""
    prompt = f"""For stock ticker '{stock_code}', what is this company's single most iconic product or building?
Return ONLY 2-6 words describing the product/building. Examples: 'iPhone smartphone', 'GeForce GPU chip'.
No explanation."""
    out = search_via_claude(prompt, timeout=30)
    if out:
        line = out.strip().split('\n')[0]
        line = re.sub(r'^["\']|["\']$', '', line)
        for prefix in ['based on my knowledge:', 'based on ', 'according to ', 'step 1:', 'the company']:
            if line.lower().startswith(prefix):
                line = line[len(prefix):].strip()
        words = line.split()[:6]
        line = ' '.join(words).rstrip('.,;:').lower()
        if len(line) >= 3:
            return line
    return None


def resolve_variables(stock_code: str, var_configs: dict, use_mock: bool = False) -> dict:
    """解析所有变量"""
    ctx = {
        'stock_code': stock_code,
        'topic': stock_code,
        'date': datetime.now().strftime('%b %d').upper(),
    }

    # 获取 price
    price = fetch_price(stock_code)
    if not price:
        price = '---'
    print(f"# price={price}", file=sys.stderr)
    ctx['price'] = price

    # 获取 change
    change = fetch_change(stock_code)
    if not change:
        change = '0.0%'
    print(f"# change={change}", file=sys.stderr)
    ctx['change'] = change

    # 计算 trend_arrow 和 color_context
    is_positive = '+' in change
    ctx['trend_arrow'] = '▲' if is_positive else '▼'
    if is_positive:
        ctx['color_context'] = f"CRITICAL COLOR RULE: The text for '{{trend_arrow}} {{change}}' MUST be rendered in Vibrant Green (#28b528) to signify growth."
    else:
        ctx['color_context'] = f"CRITICAL COLOR RULE: The text for '{{trend_arrow}} {{change}}' MUST be rendered in Blood Red (#ad0d0d) to signify decline."

    # 获取 reason
    reason = fetch_reason(stock_code)
    if not reason:
        reason = 'market update'
    print(f"# reason={reason}", file=sys.stderr)
    ctx['reason'] = reason

    # 获取 product_name
    product_name = fetch_product_name(stock_code)
    if not product_name:
        product_name = f'{stock_code} product'
    print(f"# product_name={product_name}", file=sys.stderr)
    ctx['product_name'] = product_name

    # lighting_style 和 calendar_color 根据涨跌决定
    if is_positive:
        ctx['lighting_style'] = 'Warm Sunny Lighting (Green/Gold accents).'
        ctx['calendar_color'] = 'Orange or White Block'
    else:
        ctx['lighting_style'] = 'Cool Overcast Lighting (Red/Grey accents).'
        ctx['calendar_color'] = 'Dark Grey or Blue Block'

    return ctx


def fill_template(template: str, ctx: dict) -> str:
    """填充模板变量（支持嵌套引用）"""
    for _ in range(3):
        prev = template
        for k, v in ctx.items():
            template = template.replace('{' + k + '}', str(v))
        if template == prev:
            break
    return template


def main():
    if len(sys.argv) < 3:
        print("Usage: build_dynamic_cover_prompt.py <vertical_config_path> <topic> [vertical]", file=sys.stderr)
        sys.exit(1)

    vertical_config_path = Path(sys.argv[1])
    topic = sys.argv[2]
    vertical = sys.argv[3] if len(sys.argv) > 3 else ''

    if not vertical_config_path.exists():
        print(f"# Error: config not found: {vertical_config_path}", file=sys.stderr)
        sys.exit(1)

    with open(vertical_config_path) as f:
        config = json.load(f)

    cover_config = config.get('cover_config', {})
    prompt_template = cover_config.get('background_prompt_template', '')
    var_configs = cover_config.get('prompt_variables', {})

    if not prompt_template:
        style_prefix = cover_config.get('style_prefix', 'Modern background')
        print(f"{style_prefix}, clean modern background, no text")
        sys.exit(0)

    use_mock = os.environ.get('XHS_TEST_MODE', 'false').lower() == 'true'
    stock_code = topic.upper()

    print(f"# Building dynamic prompt for {stock_code} (mock={use_mock})", file=sys.stderr)

    ctx = resolve_variables(stock_code, var_configs, use_mock=use_mock)
    prompt = fill_template(prompt_template, ctx)

    print(prompt)


if __name__ == '__main__':
    main()

