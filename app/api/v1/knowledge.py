from fastapi import APIRouter

from app.schemas import Result
from app.schemas.knowledge import KnowledgeSyncRequest, KnowledgeResponse
from app.services import knowledge_service

router = APIRouter()


# 接收请求使用 Request 模型
@router.post("/sync", response_model=Result[KnowledgeResponse])
async def sync_knowledge(request: KnowledgeSyncRequest):
    try:
        data = await knowledge_service.upsert_knowledge(request)
        return Result.success(data=data, msg="同步成功")
    except Exception as e:
        # 生产环境建议隐藏具体错误信息，只打印日志
        return Result.error(msg=f"同步失败: {str(e)}")
