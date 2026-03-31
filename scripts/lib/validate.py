#!/usr/bin/env python3
"""
小红书内容生成 - 内容验证

提供内容质量验证功能。
"""

import re
from typing import Any, Dict, List, Tuple


def validate_content(
    content: str,
    title: str,
    subtitle: str,
    rules: List[Dict[str, Any]],
    topic: str = "",
    min_score: int = 5
) -> Dict[str, Any]:
    """
    验证生成的内容是否符合垂类规范

    Args:
        content: 正文内容
        title: 标题
        subtitle: 副标题
        rules: 验证规则列表
        topic: 话题（可选）
        min_score: 最低通过分数

    Returns:
        包含 passed, feedback, score, checks 等字段的字典
    """
    results = []
    total_score = 0

    for rule in rules:
        rule_id = rule.get('id', '')
        description = rule.get('description', '')

        if rule_id == 'has_title_subtitle':
            passed, score, feedback = _check_title_subtitle(title, subtitle, rule)

        elif rule_id == 'length_in_range':
            params = rule.get('params', {})
            min_len = params.get('min', 0)
            max_len = params.get('max', 10000)
            passed, score, feedback = _check_length(content, min_len, max_len)

        elif rule_id == 'no_forbidden_expressions':
            forbidden = rule.get('forbidden', [])
            passed, score, feedback = _check_no_forbidden(content, forbidden)

        elif rule_id == 'no_bullet_points':
            passed, score, feedback = _check_no_bullet_points(content)

        elif rule_id == 'has_data_points':
            passed, score, feedback = _check_data_points(content)

        elif rule_id == 'follows_structure':
            passed, score, feedback = _check_structure(content)

        elif rule_id == 'topic_relevance':
            passed, score, feedback = (True, 1, "主题相关（需人工复核）")

        else:
            passed, score, feedback = (True, 1, "未实现该规则")

        total_score += score
        results.append({
            'rule': rule_id,
            'description': description,
            'passed': passed,
            'score': score,
            'feedback': feedback
        })

    success = total_score >= min_score
    feedback = f"得分: {total_score}/{len(results)}"

    # 构建返回字典
    return {
        'passed': success,
        'score': total_score,
        'feedback': feedback,
        'checks': {r['rule']: r['passed'] for r in results},
        'details': results,
    }


def _check_title_subtitle(title: str, subtitle: str, rule: dict) -> Tuple[bool, int, str]:
    """检查标题和副标题"""
    title_len = len(title) if title else 0
    subtitle_len = len(subtitle) if subtitle else 0

    if 4 <= title_len <= 8 and 8 <= subtitle_len <= 15:
        return True, 1, "标题和副标题长度符合要求"

    if title_len < 4 or title_len > 8:
        return False, 0, f"标题长度 {title_len} 字，要求 4-8 字"

    if subtitle_len < 8 or subtitle_len > 15:
        return False, 0, f"副标题长度 {subtitle_len} 字，要求 8-15 字"

    return False, 0, "标题或副标题不符合要求"


def _check_length(content: str, min_len: int, max_len: int) -> Tuple[bool, int, str]:
    """检查内容长度"""
    content_len = len(content) if content else 0

    if min_len <= content_len <= max_len:
        return True, 1, f"内容长度 {content_len} 字，符合要求"

    if content_len < min_len:
        return False, 0, f"内容长度 {content_len} 字，少于最少 {min_len} 字"

    return False, 0, f"内容长度 {content_len} 字，超过最大 {max_len} 字"


def _check_no_forbidden(content: str, forbidden: List[str]) -> Tuple[bool, int, str]:
    """检查禁用词"""
    found = []
    for word in forbidden:
        if word in content:
            found.append(word)

    if not found:
        return True, 1, "无禁用词"

    return False, 0, f"发现禁用词: {', '.join(found)}"


def _check_no_bullet_points(content: str) -> Tuple[bool, int, str]:
    """检查是否使用了列表符号"""
    bullet_patterns = [r'^\s*[-*•]\s', r'^\s*\d+\.\s']

    for line in content.split('\n'):
        line = line.strip()
        if not line:
            continue
        for pattern in bullet_patterns:
            if re.match(pattern, line):
                return False, 0, "发现列表符号，小红书内容应段落式"

    return True, 1, "无列表符号"


def _check_data_points(content: str) -> Tuple[bool, int, str]:
    """检查是否包含数据点"""
    # 检查是否包含数字、百分比等
    has_number = bool(re.search(r'\d+', content))
    has_percent = bool(re.search(r'\d+%', content))

    if has_number or has_percent:
        return True, 1, "包含数据点"

    return False, 0, "缺少数据点"


def _check_structure(content: str) -> Tuple[bool, int, str]:
    """检查内容结构"""
    lines = [l.strip() for l in content.split('\n') if l.strip()]

    # 检查是否有足够的段落
    if len(lines) >= 3:
        return True, 1, f"有 {len(lines)} 个段落，结构合理"

    return False, 0, f"只有 {len(lines)} 个段落，结构过于简单"
