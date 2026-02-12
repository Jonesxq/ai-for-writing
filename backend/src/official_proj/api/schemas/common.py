"""通用 API 响应结构与快捷返回方法。"""

from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一响应体：code/msg/data。"""

    code: int
    msg: str
    data: Optional[T] = None


def success(data=None, msg: str = "success", code: int = 200):
    """构造成功响应。"""
    return ApiResponse(
        code=code,
        msg=msg,
        data=data
    )


def error(msg: str="操作失败，原因见日志", code: int = -1):
    """构造失败响应。"""
    return ApiResponse(
        code=code,
        msg=msg,
        data=None
    )
