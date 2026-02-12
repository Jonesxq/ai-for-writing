"""JWT 工具（当前未在主流程使用，可作为替代鉴权方案）。"""

from datetime import datetime, timedelta
from jose import jwt

# ⚠️ 建议通过环境变量注入密钥。
SECRET_KEY = "CHANGE_ME_TO_ENV_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def create_access_token(data: dict):
    """创建带过期时间的 JWT token。"""
    # 复制 payload，避免调用方数据被修改。
    payload = data.copy()
    # 计算过期时间并写入 payload。
    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload.update({"exp": expire})
    # 编码为 JWT 字符串。
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
