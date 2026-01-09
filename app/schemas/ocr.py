from typing import Optional, List

from pydantic import Field

from app.schemas import BaseSchema


class OCRRequest(BaseSchema):
    """
    OCR 识别请求 (支持多种图片来源)
    """
    filename: Optional[str] = Field(None, description="文件名")
    image_base64: Optional[str] = Field(None, description="图片内容 Base64")
    file_url: Optional[str] = Field(None, description="图片在线 URL")
    file_path: Optional[str] = Field(None, description="服务器本地文件路径")


class OCRResponse(BaseSchema):
    """
    OCR 识别结果
    """
    text_list: List[str] = Field(..., description="识别出的文字列表")
    full_text: str = Field(..., description="拼接后的完整文本")
