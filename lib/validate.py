#!/usr/bin/env python3
"""
内容验证模块

提供小红书内容质量验证功能。
"""

import re
from typing import Any, Dict, List


def validate_content(content: str, title: str = "", subtitle: str = "",
                    rules: List = None, topic: str = "",
                    min_score: int = 5) -> Dict[str, Any]:
    """
    验证内容质量

    Args:
        content: 正文内容
        title: 标题
        subtitle: 副标题
        rules: 验证规则列表
        topic: 话题
        min_score: 最低通过分数

    Returns:
        包含验证结果的字典:
        {
            'passed': bool,
            'score': int,
            'feedback': str,
            'checks': dict
        }
    """
    checks = {}
    score = 0
    issues = []

    # 1. 标题长度检查 (4-8字)
    if title:
        title_len = len(title)
        checks['title_length'] = 4 <= title_len <= 8
        if checks['title_length']:
            score += 2
        else:
            issues.append(f'标题长度应为4-8字，当前为{title_len}字')
    else:
        checks['title_length'] = False
        issues.append('缺少标题')

    # 2. 副标题长度检查 (8-15字)
    if subtitle:
        subtitle_len = len(subtitle)
        checks['subtitle_length'] = 8 <= subtitle_len <= 15
        if checks['subtitle_length']:
            score += 1
        else:
            issues.append(f'副标题长度应为8-15字，当前为{subtitle_len}字')
    else:
        checks['subtitle_length'] = False
        issues.append('缺少副标题')

    # 3. 内容长度检查 (300-800字)
    content_len = len(content)
    checks['content_length'] = 300 <= content_len <= 800
    if checks['content_length']:
        score += 2
    else:
        if content_len < 300:
            issues.append(f'内容过短，当前{content_len}字，建议至少300字')
        else:
            issues.append(f'内容过长，当前{content_len}字，建议不超过800字')

    # 4. AI 痕迹检查
    ai_phrases = [
        '值得注意的是', '综上所述', '然而', '此外', '另外',
        '首先，其次，最后', '一方面，另一方面',
        '总的来说', '整体来看', '从以上分析可以看出'
    ]
    ai_traces_found = []
    for phrase in ai_phrases:
        if phrase in content:
            ai_traces_found.append(phrase)

    checks['no_ai_traces'] = len(ai_traces_found) == 0
    if checks['no_ai_traces']:
        score += 2
    else:
        issues.append(f'发现AI痕迹表达: {", ".join(ai_traces_found)}')

    # 5. Bullet point 检查
    bullet_patterns = [
        r'①|②|③|④|⑤|⑥|⑦|⑧|⑨|⑩',
        r'●|■|▲|▼|◆|◇',
        r'^\s*\d+\.\s',
        r'^\s*-\s',
        r'^\s*\*\s'
    ]
    has_bullets = False
    for pattern in bullet_patterns:
        if re.search(pattern, content, re.MULTILINE):
            has_bullets = True
            break

    checks['no_bullets'] = not has_bullets
    if checks['no_bullets']:
        score += 1
    else:
        issues.append('内容包含bullet point，应使用自然段落')

    # 6. 标点符号检查（不应有冒号分隔标题）
    checks['no_colon_in_title'] = '：' not in title and ':' not in title
    if checks['no_colon_in_title']:
        score += 1
    else:
        issues.append('标题中不应使用冒号')

    # 7. 数据真实性检查（简单检查）
    has_data = bool(re.search(r'\d+\.?\d*%|\$\d+|\d+亿|\d+万', content))
    checks['has_data'] = has_data
    if has_data:
        score += 1

    # 计算最终分数和结果
    final_score = min(score, 10)
    passed = final_score >= min_score

    # 生成反馈
    if passed:
        feedback = f"内容质量良好，得分 {final_score}/10。"
    else:
        feedback = "需要改进: " + "；".join(issues[:3])

    return {
        'passed': passed,
        'score': final_score,
        'feedback': feedback,
        'checks': checks,
        'issues': issues
    }
