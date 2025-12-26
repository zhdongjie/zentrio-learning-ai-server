from typing import Optional, List, Dict

from pgvector.sqlalchemy import Vector  # 导入 pgvector 扩展
from sqlmodel import SQLModel, Field, Column, JSON


class KnowledgeVector(SQLModel, table=True):
    """知识点向量模型：对应 edu_knowledge_vector 表"""
    __tablename__ = "edu_knowledge_vector"

    kp_code: str = Field(primary_key=True, max_length=64)
    name: str = Field(max_length=128)
    content: str
    # 使用 Column 显式定义 pgvector 维度为 1024
    embedding: Optional[List[float]] = Field(sa_column=Column(Vector(1024)))
    # 使用 JSON 类型存储元数据
    metadata_: Dict = Field(default_factory=dict, sa_column=Column("metadata", JSON))
