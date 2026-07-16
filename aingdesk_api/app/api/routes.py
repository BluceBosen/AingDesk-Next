from fastapi import APIRouter
from app.api.endpoints import chat, model, rag, agent, share, manager, mcp, search, index
from app.api.endpoints import os as os_endpoints

# 创建主路由
api_router = APIRouter()

# 按字母顺序添加各模块的路由
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(index.router, prefix="/index", tags=["index"])
api_router.include_router(mcp.router, prefix="/mcp", tags=["mcp"])
api_router.include_router(manager.router, prefix="/manager", tags=["manager"])
api_router.include_router(model.router, prefix="/model", tags=["model"])
api_router.include_router(os_endpoints.router, prefix="/os", tags=["os"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(share.router, prefix="/share", tags=["share"])