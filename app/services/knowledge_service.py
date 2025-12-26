import logging
from typing import List

# 导入 Embedding 服务 (需要你自己封装一下 OpenAI/智谱 的 embedding 调用)
from app.infra.llm import get_embedding_vector
# 导入 Repo 层 (假设你已经按照之前建议拆分了 repo)
from app.repositories.knowledge_repo import knowledge_repo
# 导入之前的 Schema 定义
from app.schemas.knowledge import (
    KnowledgeSyncRequest,
    KnowledgeResponse,
    KnowledgeSearchResult
)

# 初始化日志
logger = logging.getLogger(__name__)


async def upsert_knowledge(req: KnowledgeSyncRequest) -> KnowledgeResponse:
    """
    处理知识点同步逻辑：
    1. 接收 Java DTO
    2. 调用 LLM 生成向量
    3. 调用 Repo 存入 PG
    4. 返回结果
    """
    try:
        logger.info(f"[Sync] Start processing knowledge: {req.kp_code} | Subject: {req.subject_code}")

        # --- 步骤 1: 准备向量化文本 ---
        # 技巧：将“标题”和“内容”拼接，能增加检索的语义准确度
        # 如果有 sync_remark，也可以考虑拼进去，或者只做日志记录
        text_to_embed = f"知识点名称: {req.name}\n详细内容: {req.content}"

        # --- 步骤 2: 获取向量 (耗时 I/O) ---
        # 这一步通常调用智谱 AI 或 OpenAI 的 Embedding API
        # 维度通常是 1024 或 1536，需与数据库定义一致
        embedding_vector = await get_embedding_vector(text_to_embed)

        if not embedding_vector:
            raise ValueError("Failed to generate embedding vector")

        # --- 步骤 3: 数据库持久化 ---
        # 调用 repositories 层执行 UPSERT (有则更新，无则插入)
        # 注意：这里我们需要 repositories 返回更新后的 ORM 对象或字典
        saved_record = await knowledge_repo.upsert(
            kp_code=req.kp_code,
            name=req.name,
            subject_code=req.subject_code,
            content=req.content,
            embedding=embedding_vector,
            metadata={"remark": req.sync_remark}  # 存入额外的 JSON metadata
        )

        logger.info(f"[Sync] Successfully saved knowledge: {req.kp_code}")

        # --- 步骤 4: 转换为响应模型 ---
        # 利用 Pydantic v2 的 from_attributes=True 特性
        # 将 ORM 对象/字典 自动转为 Schema
        return KnowledgeResponse.model_validate(saved_record)

    except Exception as e:
        logger.error(f"[Sync] Error processing {req.kp_code}: {str(e)}", exc_info=True)
        # 抛出异常让 API 层捕获并返回 500 或 自定义错误码
        raise e


async def search_related_knowledge(
        query: str,
        subject_code: str = None,
        top_k: int = 3
) -> List[KnowledgeSearchResult]:
    """
    RAG 专用：根据问题搜索相关知识点
    """
    try:
        # 1. 将用户的问题转化为向量 (异步 I/O)
        query_vector = await get_embedding_vector(query)
        if not query_vector:
            return []

        # 2. 向量搜索 (同步 DB 操作)
        # 注意：因为 Repo 是同步的，这里不能加 await，否则会报错
        # 此时 results 是一个列表，每个元素是 (KnowledgeVector, score)
        results = knowledge_repo.search_similar(
            embedding=query_vector,
            subject_code=subject_code,
            limit=top_k
        )

        final_results = []

        # 3. 遍历、过滤并转换为响应模型
        for row in results:
            # SQLModel 的 select(Entity, score) 返回的是一个 Row 对象
            # 可以通过 row.KnowledgeVector 获取实体，row.score 获取分数
            kp_obj = row.KnowledgeVector
            score = row.score

            # 阈值过滤 (假设使用 L2 距离，越小越相似)
            # 如果是 Cosine 距离，逻辑反过来 (score > 0.7)
            if score < 0.5:
                # 4. 关键：转换为 Pydantic 模型
                item = KnowledgeSearchResult(
                    kp_code=kp_obj.kp_code,
                    content=kp_obj.content,
                    score=score
                )
                final_results.append(item)

        return final_results

    except Exception as e:
        logger.error(f"[Search] Error searching for '{query}': {str(e)}", exc_info=True)
        return []
