from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from app.schemas import Result
from app.schemas.ocr import OCRResponse, OCRRequest
from app.services import ocr_service

router = APIRouter()


@router.post("/recognize", response_model=Result[OCRResponse])
async def recognize_image(
        file: UploadFile = File(None),
        filename: str = Form(None),
        image_base64: str = Form(None, alias="imageBase64"),
        file_url: str = Form(None, alias="fileUrl"),
        file_path: str = Form(None, alias="filePath"),
):
    """
    OCR 识别图片文字
    支持：
    - 上传文件 UploadFile
    - Base64
    - file_url
    - file_path (服务器本地路径)
    """
    try:
        request = OCRRequest(
            filename=filename,
            image_base64=image_base64,
            file_url=file_url,
            file_path=file_path,
        )
        response = await ocr_service.recognize(file=file, request=request)
        print(response.full_text)
        for i in response.text_list:
            print(i)
        return Result.success(data=response)
    except HTTPException as e:
        # 直接返回已知 HTTP 异常
        raise e
    except Exception as e:
        # 生产环境可隐藏详细异常
        return Result.error(msg=f"OCR 识别失败: {str(e)}")
