from datetime import datetime
from typing import Optional

from pydantic import Field

from app.schemas import BaseSchema


# 1. 基础类 (Base)
class KnowledgeBase(BaseSchema):
    kp_code: str = Field(..., description="知识点唯一编码")
    name: str = Field(..., description="知识点名称")
    subject_code: str = Field(..., description="学科编码")
    content: str = Field(..., description="知识点详情内容")


# 2. 请求类 (Request / Create)
class KnowledgeSyncRequest(KnowledgeBase):
    # 允许 Java 端同步时带个备注，后续可能用于日志记录
    sync_remark: Optional[str] = None


# 3. 更新类 (Update)
# 注意：更新类通常不继承 KnowledgeBase，因为 Base 里的字段是必填的(...)
# 而更新时，往往只想更新 name，不想更新 content。所以字段全是 Optional。
class KnowledgeUpdate(BaseSchema):
    name: Optional[str] = None
    content: Optional[str] = None
    # update 通常不需要传 kp_code (在 URL 中传) 或 subject_code (不允许改)


# 4. 响应类 (Response / Read)
class KnowledgeResponse(KnowledgeBase):
    # 这些是数据库里的字段，Python 读取后返回给 Java
    vector_dim: int = Field(default=1024, description="向量维度")
    # 建议允许为 None，或者确保 DB 一定有值。不要用 default_factory=now
    created_at: Optional[datetime] = Field(None, description="创建时间")


# 5. 搜索结果 (RAG 专用)
class KnowledgeSearchResult(BaseSchema):
    kp_code: str
    content: str
    score: float = Field(..., description="向量相似度得分")
