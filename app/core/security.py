import secrets

from fastapi import Security
from fastapi.security import APIKeyHeader
from starlette.responses import JSONResponse

from app.core.config import settings
from app.schemas import Result

# 1. 定义 Header 的名称
# Java 端调用时，必须在 Header 里带上: X-Internal-Token: zentrio_internal_dev_secret
api_key_header = APIKeyHeader(name="X-Internal-Token", auto_error=True)


async def verify_internal_token(api_key: str = Security(api_key_header)):
    """
    验证请求头中的 Token 是否与配置一致
    """
    if not api_key:
        return JSONResponse(
            status_code=200,
            content=Result.unauthorized().dict()
        )

    if not secrets.compare_digest(api_key, settings.API_SECRET_KEY):
        return JSONResponse(
            status_code=200,
            content=Result.forbidden().dict()
        )
    return api_key
