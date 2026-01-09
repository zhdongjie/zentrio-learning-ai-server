# # app/middleware/exception_handler.py
# import logging
#
# from fastapi import Request, HTTPException
# from fastapi.responses import JSONResponse
# from starlette.exceptions import HTTPException as StarletteHTTPException
#
# from app.schemas import ErrorResponse, ErrorCode
#
# logger = logging.getLogger(__name__)
#
#
# async def global_exception_handler(request: Request, exc: Exception):
#     """
#     全局异常处理器
#     """
#     logger.error(f"全局异常: {exc}", exc_info=True)
#
#     if isinstance(exc, HTTPException):
#         # FastAPI的HTTP异常
#         return JSONResponse(
#             status_code=exc.status_code,
#             content=ErrorResponse.from_error_code(
#                 error_code=get_error_code(exc.status_code),
#                 message=exc.detail,
#                 suggestion=get_suggestion(exc.status_code)
#             ).dict()
#         )
#     elif isinstance(exc, StarletteHTTPException):
#         # Starlette的HTTP异常
#         return JSONResponse(
#             status_code=exc.status_code,
#             content=ErrorResponse.from_error_code(
#                 error_code=get_error_code(exc.status_code),
#                 message=str(exc.detail),
#                 suggestion=get_suggestion(exc.status_code)
#             ).dict()
#         )
#     else:
#         # 其他异常
#         import os
#         if os.getenv("ENVIRONMENT") == "production":
#             message = "服务器内部错误"
#             details = None
#         else:
#             message = str(exc)
#             details = {"exception_type": exc.__class__.__name__}
#
#         return JSONResponse(
#             status_code=500,
#             content=ErrorResponse.from_error_code(
#                 error_code=ErrorCode.SYSTEM_ERROR,
#                 message=message,
#                 details=details
#             ).dict()
#         )
#
#
# def get_error_code(status_code: int) -> ErrorCode:
#     """根据HTTP状态码获取错误代码"""
#     error_mapping = {
#         400: ErrorCode.PARAM_ERROR,
#         401: ErrorCode.UNAUTHORIZED,
#         403: ErrorCode.FORBIDDEN,
#         404: ErrorCode.NOT_FOUND,
#         500: ErrorCode.SYSTEM_ERROR,
#     }
#     return error_mapping.get(status_code, ErrorCode.SYSTEM_ERROR)
#
#
# def get_suggestion(status_code: int) -> str:
#     """根据状态码获取解决建议"""
#     suggestions = {
#         400: "请检查请求参数是否正确",
#         401: "请登录后重试",
#         403: "您没有权限执行此操作",
#         404: "请求的资源不存在",
#         500: "请联系系统管理员",
#     }
#     return suggestions.get(status_code, "请稍后重试")
