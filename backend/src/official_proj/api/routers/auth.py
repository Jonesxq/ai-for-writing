"""用户注册与登录的认证接口。"""

# official_proj/api/auth.py
from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session

from official_proj.api.auth.token_store import create_token
from official_proj.api.schemas.common import ApiResponse, success
from official_proj.api.schemas.novel import AuthReq
from official_proj.db.mysql_db.dao.user_dao import UserDAO
from official_proj.db.mysql_db.mysql import get_session

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=ApiResponse[None]
)
def register(
    req: AuthReq,
    session: Session = Depends(get_session)
):
    """创建用户记录（若用户名未被占用）。"""
    dao = UserDAO(session)

    # 在应用层做用户名唯一性校验。
    if dao.get_by_username(req.username):
        raise HTTPException(
            status_code=400,
            detail="用户名已存在"
        )

    # 将用户写入 MySQL。
    dao.create(req.username, req.password)

    return success(msg="注册成功")


@router.post(
    "/login",
    response_model=ApiResponse[dict]
)
def login(
    req: AuthReq,
    session: Session = Depends(get_session)
):
    """校验账号密码并返回 token。"""
    dao = UserDAO(session)
    user = dao.get_by_username(req.username)

    # 账号或密码错误直接拒绝。
    if not user or user.password != req.password:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )

    # 生成并返回内存中的 token。
    token = create_token(user.id)

    return success(
        data={"token": token}
    )
