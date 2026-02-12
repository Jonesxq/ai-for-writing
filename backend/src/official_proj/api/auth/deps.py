"""从 token 解析当前用户的依赖函数。"""

# official_proj/auth/deps.py
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from official_proj.api.auth.token_store import get_user_id

# 使用 HTTP Bearer 读取 Authorization: Bearer <token>。
security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """根据传入的 Bearer token 解析用户 ID。"""
    # Header 格式：Authorization: Bearer xxxxx
    token = credentials.credentials
    user_id = get_user_id(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user_id
