from sqlmodel import create_engine, Session, SQLModel

from app.core.config import settings

# 统一创建 engine
engine = create_engine(settings.DATABASE_URL, echo=settings.SQL_ECHO)


def get_session():
    """依赖注入使用的 Session 生成器"""
    with Session(engine) as session:
        yield session


def init_db():
    # 这一步会扫描所有继承自 SQLModel 的类，自动生成 CREATE TABLE 语句
    SQLModel.metadata.create_all(engine)
