from typing import TypeVar, Generic, Optional

from pydantic import Field

from app.core.constants import ResponseCode
from app.schemas import BaseSchema

# 定义泛型变量 T
T = TypeVar("T")


class Result(BaseSchema, Generic[T]):
    """对齐 Java Result<T> 的通用包装类"""
    # 默认 code 设为成功
    code: int = Field(ResponseCode.SUCCESS.value, description="业务状态码")
    msg: str = Field("success", description="提示消息")
    data: Optional[T] = Field(None, description="业务数据")

    @classmethod
    def success(cls, data: T = None, msg: str = "success"):
        """回答正确时的返回"""
        return cls(code=ResponseCode.SUCCESS.value, msg=msg, data=data)

    @classmethod
    def unauthorized(cls):
        """未授权时的返回 (40100)"""
        return cls(code=ResponseCode.UNAUTHORIZED.value, msg="Missing API Key", data=None)

    @classmethod
    def forbidden(cls):
        """无权限时的返回 (40300)"""
        return cls(code=ResponseCode.FORBIDDEN.value, msg="Could not validate credentials", data=None)

    @classmethod
    def error(cls, data: T = None, msg: str = "answer error"):
        """回答错误时的返回 (40000)"""
        return cls(code=ResponseCode.ANSWER_ERROR.value, msg=msg, data=data)

    @classmethod
    def fatal(cls, msg: str = "system error"):
        """系统级错误返回"""
        return cls(code=ResponseCode.SYSTEM_ERROR.value, msg=msg, data=None)
