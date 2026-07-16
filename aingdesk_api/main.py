import asyncio
import os
import sys
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import traceback

# Windows 下默认 SelectorEventLoop 不支持 asyncio 子进程，
# uvicorn reload 模式可能导致该问题，必须在创建事件循环前设置为 ProactorEventLoop。
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("AiDesk")

# 创建数据目录
data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(data_dir, exist_ok=True)

# 项目信息
PROJECT_NAME = "AiDesk API"
API_VERSION = "1.0.0"

# 创建应用实例
app = FastAPI(
    title=PROJECT_NAME,
    description="AiDesk API - AI assistant with knowledge base, model APIs, and intelligent agents",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# 设置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )

# 状态检查端点
@app.get("/status")
async def status():
    return {"status": "ok", "version": API_VERSION}

try:
    # 尝试导入并包含所有API路由
    from app.api.routes import api_router
    app.include_router(api_router, prefix="")
    logger.info("API routes loaded successfully")
except ImportError as e:
    logger.error(f"Error loading API routes: {str(e)}")
    
    # 提供备用的简单路由
    @app.get("/status")
    async def api_status():
        return {
            "status": "limited",
            "message": "API routes failed to load. Only basic functionality is available.",
            "error": str(e)
        }
    
    # 直接导入agent路由
    try:
        from app.api.endpoints.agent import router as agent_router
        app.include_router(agent_router, prefix="/agent", tags=["agent"])
        logger.info("Agent routes loaded successfully")
    except Exception as ae:
        logger.error(f"Error loading agent routes: {str(ae)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        logger.info("Starting AiDesk API server...")
        uvicorn.run("main:app", host="0.0.0.0", port=7071, reload=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1) 