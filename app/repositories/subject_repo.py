from sqlmodel import Session, select

from app.core.database import engine as global_engine
from app.models.subject_config import SubjectConfig


class SubjectRepo:
    """学科配置仓储层"""

    def __init__(self, db_engine=None):
        # 如果初始化没传 engine，就用全局默认的
        self.engine = db_engine or global_engine

    def get_config(self, subject_name: str) -> SubjectConfig:
        """
        获取学科配置，失败时逐级降级：
        1. 指定学科 -> 2. default 学科 -> 3. 硬编码兜底
        """
        # 硬编码兜底方案
        hard_fallback = SubjectConfig(
            subject_name="default",
            role_name="知衡 Edu 首席导师",
            style_desc="专业、启发式",
            focus_points="逻辑思维与核心概念"
        )

        try:
            with Session(self.engine) as session:
                # 1. 尝试查询具体学科
                statement = select(SubjectConfig).where(SubjectConfig.subject_name == subject_name)
                result = session.exec(statement).first()
                if result:
                    return result

                # 2. 尝试查询数据库中的 default 配置
                fallback_stmt = select(SubjectConfig).where(SubjectConfig.subject_name == "default")
                res_default = session.exec(fallback_stmt).first()

                return res_default if res_default else hard_fallback
        except Exception as e:
            # 记录日志建议在这里做，print仅作演示
            print(f"Error fetching subject config: {e}")
            return hard_fallback


# 实例化一个全局对象供 Service 调用，或者使用依赖注入
subject_repo = SubjectRepo()
