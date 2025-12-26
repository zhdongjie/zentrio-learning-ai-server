import logging
from typing import List

from langchain_openai import OpenAIEmbeddings

from app.core.config import settings

logger = logging.getLogger(__name__)
# =======================================================
# Embedding 客户端 (用于向量化)
# =======================================================
# 全局初始化 Embedding 客户端，避免每次调用函数都重新创建对象
# 智谱 embedding-2 维度为 1024
embedding_client = OpenAIEmbeddings(
    model=settings.ZHIPU_MODEL_EMBEDDING,
    openai_api_key=settings.ZHIPU_API_KEY,
    openai_api_base=settings.ZHIPU_API_BASE,
    # 禁用自动检查 token 长度，防止一些不必要的警告
    check_embedding_ctx_length=False
)


async def get_embedding_vector(text: str) -> List[float]:
    """
    调用智谱 AI 生成文本向量 (1024维)
    """
    if not text or not text.strip():
        logger.warning("Attempted to embed empty text")
        return []

    try:
        # 1. 文本预处理：去除换行符
        # 经验之谈：换行符有时会干扰 embedding 的语义判定，建议替换为空格
        cleaned_text = text.replace("\n", " ")

        # 2. 异步调用 Embedding
        # aembed_query 是 LangChain 提供的异步方法，专门用于单个查询文本
        vector = await embedding_client.aembed_query(cleaned_text)

        # 3. 维度安全检查 (可选，但在初期调试很有用)
        if len(vector) != 1024:
            logger.error(f"Embedding dimension mismatch! Expected 1024, got {len(vector)}")
            # 这里可以选择报错，或者根据业务决定是否截断/填充
            # raise ValueError("Dimension mismatch")

        return vector

    except Exception as e:
        # 记录详细的错误堆栈，方便排查是网络问题还是 401 鉴权问题
        logger.error(f"Failed to generate embedding: {str(e)}", exc_info=True)
        # 发生错误时返回空列表，上层业务(knowledge_service)检测到空列表应抛出异常
        return []
