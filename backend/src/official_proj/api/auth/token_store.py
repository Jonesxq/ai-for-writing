"""简单的内存 token 存储（开发期使用）。"""

# official_proj/auth/token_store.py
import uuid

# 内存中的 token -> user_id 映射（服务重启即失效）。
TOKEN_STORE: dict[str, int] = {}


def create_token(user_id: int) -> str:
    """生成随机 token 并写入内存映射。"""
    token = str(uuid.uuid4())
    TOKEN_STORE[token] = user_id
    return token


def get_user_id(token: str) -> int | None:
    """根据 token 获取对应的用户 ID。"""
    return TOKEN_STORE.get(token)
