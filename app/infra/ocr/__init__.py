"""
OCR 基础设施模块
对外暴露统一 OCR 能力入口
"""

from .provider import get_ocr_client
from .utils import read_file_bytes, preprocess_image_bytes

__all__ = [
    "get_ocr_client",
    "preprocess_image_bytes",
    "read_file_bytes",
]
