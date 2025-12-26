import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import diagnosis, knowledge
from app.core.config import settings
from app.core.database import init_db
from app.core.security import verify_internal_token

# 初始化日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理
    启动时：初始化数据库连接、创建表
    关闭时：清理资源（如关闭 Redis 连接池等）
    """
    logger.info("🚀 Zentrio AI Service is starting up...")

    try:
        # [数据库初始化]
        # 注意：如果你完全切换到了 Alembic，这行可以注释掉。
        # 但在开发阶段，保留它可以确保新加的表能自动创建。
        init_db()
        logger.info("✅ Database tables checked/created.")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        # 这里可以选择是否抛出异常终止启动，或者仅记录错误
        # raise e

    yield

    logger.info("🛑 Zentrio AI Service is shutting down...")
    # 在这里添加清理逻辑，例如关闭 HTTP Client session 等


# 1. 创建 FastAPI 实例
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Python AI RAG Engine for K12 Education",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI 地址
    redoc_url="/redoc",  # Redoc 地址
    openapi_url=f"{settings.API_PREFIX}/openapi.json"  # OpenAPI 描述文件地址
)

# 2. 配置 CORS (跨域资源共享) - 关键！
# 允许 Java 后端或前端页面调用此接口
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. 注册路由 (Routers)
# 建议：直接拼接 API_PREFIX，保持代码整洁
app.include_router(
    knowledge.router,
    prefix=f"{settings.API_PREFIX}/knowledge",
    tags=["Knowledge Base"],
    dependencies=[Security(verify_internal_token)]
)
app.include_router(
    diagnosis.router,
    prefix=f"{settings.API_PREFIX}/diagnosis",
    tags=["AI Diagnosis"],
    dependencies=[Security(verify_internal_token)]
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 50000,
            "msg": "系统内部繁忙，AI 暂时无法响应",
            "data": str(exc) if settings.DEBUG else None
        }
    )


# 4. 健康检查接口
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.ENVIRONMENT
    }


if __name__ == "__main__":
    # 使用 settings 中的配置启动
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
        log_level=settings.APP_LOG_LEVEL.lower(),  # uvicorn 需要小写
        workers=1  # 生产环境通常配合 gunicorn 使用多个 workers
    )
