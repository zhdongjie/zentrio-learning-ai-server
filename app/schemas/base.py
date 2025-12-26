from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    # 核心配置
    model_config = ConfigDict(
        alias_generator=to_camel,  # 序列化时：将字段名转为驼峰（给 Java 看）
        populate_by_name=True,  # 反序列化时：支持按别名（驼峰）读取输入（接 Java 的请求）
        from_attributes=True  # 支持从对象属性读取
    )
