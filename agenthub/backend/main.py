"""AgentHub MVP - FastAPI主应用"""
import sys
import os
from pathlib import Path

# 允许直接运行和模块导入两种方式
_current_dir = Path(__file__).parent.resolve()
_root_dir = _current_dir.parent.parent
sys.path.insert(0, str(_root_dir))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn

from agenthub.backend.services.sse_manager import sse_manager


API_KEY = os.getenv("API_KEY", "dev-secret-key")
PORT = int(os.getenv("PORT", "7010"))


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
# 注意: allow_origins=["*"] + allow_credentials=True 违反 CORS 规范
# 浏览器会拒绝 credentials: "include" 的请求（如 SSE fetch）
# 必须列出具体 origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:7000",
        "http://localhost:7005",
        "http://127.0.0.1:7000",
        "http://127.0.0.1:7005",
    ],
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
from agenthub.backend.routers import messages, events, tasks, agents
app.include_router(messages.router)
app.include_router(events.router)
app.include_router(tasks.router)
app.include_router(agents.router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "subscribers": sse_manager.get_subscriber_count()}


@app.get("/")
async def root():
    """根路径"""
    return {"message": "AgentHub MVP API", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=True)