"""AgentHub MVP - FastAPI主应用"""
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from routers import messages
from services.sse_manager import sse_manager


API_KEY = os.getenv("API_KEY", "dev-secret-key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    yield
    # 关闭时清理


app = FastAPI(
    title="AgentHub MVP API",
    description="多Agent协作平台的API服务",
    version="1.0.0",
    lifespan=lifespan
)


# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API Key验证中间件
@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    """验证API Key的中间件"""
    if request.url.path.startswith("/api") and request.method != "OPTIONS":
        key = request.headers.get("X-API-Key")
        if key != API_KEY:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid API Key"}
            )
    return await call_next(request)


# 注册路由
from routers import messages, events
app.include_router(messages.router)
app.include_router(events.router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "subscribers": sse_manager.get_subscriber_count()}


@app.get("/")
async def root():
    """根路径"""
    return {"message": "AgentHub MVP API", "version": "1.0.0"}