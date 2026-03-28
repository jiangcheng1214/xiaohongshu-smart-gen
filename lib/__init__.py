"""
小红书内容生成 - Python 重构版本

纯 Python 实现的小红书内容生成 7 步流水线，替代原有的 shell 脚本。
"""

__version__ = "2.0.0"

from .session import XhsSession
from .steps import (
    Step1Research,
    Step2Generate,
    Step3Validate,
    Step4PrepareImg,
    Step5GenImg,
    Step6Overlay,
    Step7Deliver
)
from .pipeline import Pipeline

__all__ = [
    'XhsSession',
    'Pipeline',
    'Step1Research',
    'Step2Generate',
    'Step3Validate',
    'Step4PrepareImg',
    'Step5GenImg',
    'Step6Overlay',
    'Step7Deliver'
]
