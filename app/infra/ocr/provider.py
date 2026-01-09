from app.infra.ocr.rapidocr_client import OCRClient

_ocr_instance: OCRClient | None = None


def get_ocr_client() -> OCRClient:
    """
    OCR Client Provider
    - 延迟初始化
    - 单例
    """
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = OCRClient()
    return _ocr_instance
