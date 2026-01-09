import os
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ===============================
    # LLM / 智谱 配置
    # ===============================
    TEMPERATURE: float = Field(
        default=0.2,
        description="LLM temperature, lower is more deterministic"
    )

    ZHIPU_API_KEY: str = Field(..., description="Zhipu AI API Key")
    ZHIPU_API_BASE: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4",
        description="Zhipu API base url"
    )

    ZHIPU_MODEL_EMBEDDING: str = "embedding-2"
    ZHIPU_MODEL_GLM: str = "glm-4-flash"

    ZHIPU_EMBEDDING_DIM: int = Field(default=4096, description="Embedding vector dimension")

    # ===============================
    # PostgreSQL / pgvector
    # ===============================
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    SQL_ECHO: bool = False

    # ===============================
    # 应用 / Uvicorn
    # ===============================
    APP_NAME: str = "FastAPI Server"
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    APP_RELOAD: bool = False
    APP_LOG_LEVEL: str = "INFO"
    API_PREFIX: str = "/app/v1"
    ENVIRONMENT: str = "dev"
    BACKEND_CORS_ORIGINS: List[str] = ["*"]
    API_SECRET_KEY: str = "zentrio_internal_secret_123"

    # ===============================
    # 派生属性（不会出现在 .env）
    # ===============================
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    # === OCR Configuration ===
    # 是否启用 OCR 功能
    OCR_ENABLED: bool = True
    # OCR 线程数 (根据 CPU 核数调整，0 为自动)
    OCR_NUM_THREADS: int = 0
    # 限制图像长边，太大的图缩放以提升速度，默认 960
    OCR_DET_LIMIT_SIDE_LEN: int = 960
    # 识别置信度阈值
    OCR_TEXT_SCORE_THRESH: float = 0.5
    # OCR 默认语言
    OCR_LANG: str = "ch"

    # ===============================
    # Settings 行为配置
    # ===============================
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
