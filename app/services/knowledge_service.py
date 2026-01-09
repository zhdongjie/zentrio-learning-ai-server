import logging
from typing import List

from app.infra.llm import get_embedding_vector
from app.repositories.knowledge_repo import knowledge_repo
from app.schemas.knowledge import (
    KnowledgeSyncRequest,
    KnowledgeResponse,
    KnowledgeSearchResult
)

logger = logging.getLogger(__name__)


class KnowledgeService:
    def __init__(self):
        """
        初始化 KnowledgeService
        在这里注入 Repository 依赖，方便后续测试 Mock
        """
        # 将全局的 repo 实例绑定到当前 Service 实例上
        self.repo = knowledge_repo

    async def upsert_knowledge(self, req: KnowledgeSyncRequest) -> KnowledgeResponse:
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
            text_to_embed = f"知识点名称: {req.name}\n详细内容: {req.content}"

            # --- 步骤 2: 获取向量 (耗时 I/O) ---
            embedding_vector = await get_embedding_vector(text_to_embed)

            if not embedding_vector:
                raise ValueError("Failed to generate embedding vector")

            # --- 步骤 3: 数据库持久化 ---
            # 【关键修改】使用 self.repo 调用，而不是全局变量
            saved_record = await self.repo.upsert(
                kp_code=req.kp_code,
                name=req.name,
                subject_code=req.subject_code,
                content=req.content,
                embedding=embedding_vector,
                metadata={"remark": req.sync_remark}
            )

            logger.info(f"[Sync] Successfully saved knowledge: {req.kp_code}")

            # --- 步骤 4: 转换为响应模型 ---
            return KnowledgeResponse.model_validate(saved_record)

        except Exception as e:
            logger.error(f"[Sync] Error processing {req.kp_code}: {str(e)}", exc_info=True)
            raise e

    async def search_related_knowledge(
            self,
            query: str,
            subject_code: str = None,
            top_k: int = 3
    ) -> List[KnowledgeSearchResult]:
        """
        RAG 专用：根据问题搜索相关知识点
        """
        try:
            # 1. 将用户的问题转化为向量
            query_vector = await get_embedding_vector(query)
            if not query_vector:
                return []

            # 2. 向量搜索
            # 【关键修改】使用 self.repo 调用
            results = self.repo.search_similar(
                embedding=query_vector,
                subject_code=subject_code,
                limit=top_k
            )

            final_results = []

            # 3. 遍历、过滤并转换为响应模型
            for row in results:
                kp_obj = row.KnowledgeVector
                score = row.score

                # 阈值过滤 (L2距离越小越好)
                if score < 0.5:
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


# 4. 实例化单例对象 (供 Controller 导入使用)
knowledge_service = KnowledgeService()
