from typing import List, Optional

from pydantic import Field

from app.schemas.base import BaseSchema


# ==========================================
# 1. Request Schema (入参: Java -> Python)
# ==========================================
class DiagnosisRequest(BaseSchema):
    """
    接收来自 Java 端的诊断请求
    Java 传: kpCode, question, studentAnswer (JSON)
    Python 收: kp_code, question, student_answer
    """
    kp_code: str = Field(..., description="知识点编码")
    question: str = Field(..., description="题目内容/题干")
    student_answer: str = Field(..., description="学生的作答内容(文本或OCR结果)")

    # 可选：如果有教材版本上下文
    textbook_version: Optional[str] = Field(None, description="教材版本，用于AI上下文")


# ==========================================
# 2. Response Schema (出参: Python -> Java)
# ==========================================
class DiagnosisResponse(BaseSchema):
    """
    返回给 Java 端的诊断结果
    Python 回: is_correct, error_type...
    Java 收: isCorrect, errorType...
    """
    # 1. 核心状态
    is_correct: bool = Field(..., description="学生回答是否完全正确")

    # 2. 错因分析
    error_type: Optional[str] = Field(None, description="错因分类，正确时可为空")

    # 3. 深度诊断
    analysis: str = Field(..., description="深度分析内容")

    # 4. 改进建议
    suggested_actions: List[str] = Field(default_factory=list, description="改进建议")
