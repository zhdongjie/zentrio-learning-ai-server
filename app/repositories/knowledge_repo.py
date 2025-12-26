from typing import Optional, Tuple, Dict, List, Sequence

from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from app.core.database import engine as global_engine
from app.models.knowledge_vector import KnowledgeVector


class KnowledgeRepo:
    """知识库向量仓储层"""

    def __init__(self, db_engine=None):
        # 如果初始化没传 engine，就用全局默认的
        self.engine = db_engine or global_engine

    def get_content_with_metadata(self, kp_code: str) -> Optional[Tuple[str, Dict]]:
        with Session(self.engine) as session:
            statement = select(KnowledgeVector).where(KnowledgeVector.kp_code == kp_code)
            kv = session.exec(statement).first()
            return (kv.content, kv.metadata_) if kv else None

    def search_similar(
            self,
            embedding: List[float],
            subject_code: Optional[str] = None,
            limit: int = 3
    ) -> Sequence[Tuple[KnowledgeVector, float]]:
        """
        向量相似度搜索
        :param embedding: 查询向量
        :param subject_code: (可选) 学科编码，用于缩小搜索范围
        :param limit: 返回条数
        :return: List[(KnowledgeVector对象, 距离分数)]
        """
        if not embedding:
            return []

        with Session(self.engine) as session:
            # 1. 定义距离表达式 (L2 欧氏距离)
            # 越小越相似 (0代表完全一样)
            distance_expr = KnowledgeVector.embedding.l2_distance(embedding)

            # 2. 构建基础查询
            statement = select(KnowledgeVector, distance_expr.label("score"))

            # 3. 动态添加过滤条件 (关键优化)
            # 如果业务传了学科，就只在对应学科下搜，大幅提高准确率
            if subject_code:
                statement = statement.where(KnowledgeVector.subject_code == subject_code)

            # 4. 排序与限制
            statement = statement.order_by(distance_expr).limit(limit)

            # 5. 执行
            # 返回的是 Row 对象列表，但在 Python 中行为表现与 Tuple[(KV, float)] 一致
            results = session.exec(statement).all()

            return results

    def upsert(self, kp_code: str, name: str, subject_code: str, content: str, embedding: List[float], metadata: Dict):
        """
        使用 PostgreSQL 原生 ON CONFLICT 实现原子级 Upsert
        注意：这里去掉了 async，因为内部 Session 是同步的
        """
        with Session(self.engine) as session:
            # 1. 构建 Insert 语句
            insert_stmt = insert(KnowledgeVector).values(
                kp_code=kp_code,
                name=name,
                subject_code=subject_code,
                content=content,
                embedding=embedding,
                metadata_=metadata
            )

            # 2. 定义冲突更新逻辑 (ON CONFLICT DO UPDATE)
            # excluded 代表“试图插入但冲突的那一行新数据”
            do_update_stmt = insert_stmt.on_conflict_do_update(
                index_elements=['kp_code'],  # 冲突索引
                set_={
                    "name": insert_stmt.excluded.name,
                    "subject_code": insert_stmt.excluded.subject_code,
                    "content": insert_stmt.excluded.content,
                    "embedding": insert_stmt.excluded.embedding,
                    "metadata_": insert_stmt.excluded.metadata_,
                }
            )

            # 3. 执行
            session.exec(do_update_stmt)
            session.commit()

            # 4. 如果需要返回对象，可以再查一次 (通常 upsert 不需要返回完整对象，除非为了拿到自增ID)
            # 为了配合 Service 层逻辑，这里可以简单返回个 True 或重新查询
            # return self.get_content_with_metadata(kp_code)
            return True


# 实例化对象
knowledge_repo = KnowledgeRepo()
