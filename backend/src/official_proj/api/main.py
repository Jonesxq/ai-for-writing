"""FastAPI 应用入口与全局中间件配置。"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from official_proj.api.routers.auth import router as auth_router
from official_proj.api.routers.novel import router as novel_router

# 创建 FastAPI 应用实例（由 uvicorn 启动）。
app = FastAPI(title="AI写作平台")

# 允许本地 Vite 开发服务器在开发期访问接口。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 登录 / 注册
app.include_router(auth_router)

# ✅ 小说 / 写作（需要登录）
app.include_router(novel_router)
