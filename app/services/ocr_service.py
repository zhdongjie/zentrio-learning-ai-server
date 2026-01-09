from fastapi import UploadFile

from app.infra.ocr.provider import get_ocr_client
from app.infra.ocr.utils import preprocess_image_bytes, read_file_bytes
from app.schemas.ocr import OCRResponse, OCRRequest


class OCRService:
    def __init__(self):
        self.ocr_client = get_ocr_client()

    async def recognize(
            self,
            file: UploadFile | None = None,
            request: OCRRequest | None = None
    ) -> OCRResponse:
        """
        OCR 识别服务
        统一处理 文件流 / Base64 / URL / 本地路径
        """

        # 1. 安全提取参数 (防止 request 为 None 时报错)
        img_base64 = request.image_base64 if request else None
        file_url = request.file_url if request else None
        file_path = request.file_path if request else None

        # 2. 读取图片字节流 (调用 utils 中的通用读取逻辑)
        image_bytes = await read_file_bytes(
            file=file,
            image_base64=img_base64,
            file_url=file_url,
            file_path=file_path
        )

        # 3. 预处理 (转 BGR + 放大 + 加白边)
        img = preprocess_image_bytes(image_bytes)

        # 4. 执行识别 (返回已排序的文字列表)
        text_list = self.ocr_client.recognize(img)

        # 5. 拼接完整文本
        # 建议使用换行符 "\n" 而不是空格，保留题目和答案的段落结构
        full_text = "\n".join(text_list)

        return OCRResponse(text_list=text_list, full_text=full_text)


# 导出 Service 实例
ocr_service = OCRService()
