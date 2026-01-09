from fastapi import APIRouter

# 引入拆分后的 Request 和 Response
from app.schemas.diagnosis import DiagnosisRequest, DiagnosisResponse
from app.schemas.result import Result
from app.services import diagnosis_service

router = APIRouter()


@router.post("/analyze", response_model=Result[DiagnosisResponse])
async def analyze(request: DiagnosisRequest):
    diagnosis_data = await diagnosis_service.diagnose(
        request.kp_code,
        request.question,
        request.student_answer
    )
    print(diagnosis_data)

    # 根据对错封装 Result
    if diagnosis_data.is_correct:
        return Result.success(data=diagnosis_data, msg="回答正确")
    else:
        # diagnosis_data 本身就是 DiagnosisResponse 结构(或字典)
        # Result 序列化时会自动转为驼峰
        return Result.error(data=diagnosis_data, msg="回答错误")
