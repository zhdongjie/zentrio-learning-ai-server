# =======================================================
# 1. LLM 客户端 (用于对话/诊断)
# =======================================================
from langchain_openai import ChatOpenAI

from app.core.config import settings

llm = ChatOpenAI(
    model=settings.ZHIPU_MODEL_GLM,  # 例如 "glm-4"
    openai_api_key=settings.ZHIPU_API_KEY,
    openai_api_base=settings.ZHIPU_API_BASE,
    temperature=settings.TEMPERATURE,
)
