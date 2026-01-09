# app/infra/ocr/rapidocr_client.py
import logging
from typing import List, Optional

import numpy as np
from rapidocr_onnxruntime import RapidOCR

from app.core.config import settings
# 假设 utils.py 在同级目录下，稍后我们会去实现它
from .utils import extract_text_from_ocr_results

logger = logging.getLogger(__name__)


class OCRClient:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        单例模式：确保全局只初始化一次 OCR 引擎
        """
        if cls._instance is None:
            cls._instance = super(OCRClient, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """
        初始化 OCR 客户端 (仅在第一次创建时执行加载)
        """
        if getattr(self, "_initialized", False):
            return

        self.engine: Optional[RapidOCR] = None

        if settings.OCR_ENABLED:
            try:
                logger.info(f"Initializing RapidOCR Engine (lang={settings.OCR_LANG})...")
                # 从配置加载参数
                self.engine = RapidOCR(
                    num_threads=settings.OCR_NUM_THREADS,
                    det_limit_side_len=settings.OCR_DET_LIMIT_SIDE_LEN,
                    det_limit_type='min',
                    text_score=settings.OCR_TEXT_SCORE_THRESH,
                    lang=settings.OCR_LANG
                )
                logger.info("RapidOCR Engine initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize RapidOCR: {e}")
                self.engine = None
        else:
            logger.warning("OCR feature is disabled in settings.")

        self._initialized = True

    def recognize(self, image: np.ndarray) -> List[str]:
        """
        识别图片文字，返回排序后的文字列表
        :param image: OpenCV 格式的 numpy 数组 (BGR)
        """
        if not self.engine:
            logger.warning("OCR engine is not initialized or disabled.")
            return []

        try:
            # RapidOCR 调用返回元组: (result, elapse_time)
            # result 结构: [[box, text, score], ...]
            ocr_result, _ = self.engine(image)

            if not ocr_result:
                return []

            # 调用工具函数提取并排序文字
            return extract_text_from_ocr_results(ocr_result)

        except Exception as e:
            logger.error(f"OCR inference failed: {e}")
            raise e


# 导出全局单例，方便其他模块直接 import ocr_client 使用
ocr_client = OCRClient()
