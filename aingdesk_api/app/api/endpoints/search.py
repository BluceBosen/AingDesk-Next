from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.search_service import SearchService
from app.models.response import ResponseHandler

router = APIRouter(tags=["search"])
search_service = SearchService()

# 请求模型
class SearchRequest(BaseModel):
    query: str
    searchProvider: Optional[str] = "baidu"



@router.post("/search", summary="执行搜索查询")
async def search(request: SearchRequest):
    """执行搜索查询
    
    执行网络搜索查询，支持多个搜索提供商
    
    参数说明：
    - **query**: 搜索关键词（必填）
    - **searchProvider**: 搜索提供商，默认baidu（可选）
    """
    try:
        # 参数检查
        if not request.query:
            return ResponseHandler.error("请输入搜索内容", None, 400)
            
        # 使用默认搜索提供商（如果未提供）
        search_provider = request.searchProvider or "baidu"
        
        # 执行搜索
        result = await search_service.search(request.query, search_provider)
        
        return ResponseHandler.success("搜索成功", result)
    except Exception as e:
        return ResponseHandler.error(f"搜索失败: {str(e)}")

# 扩展API，可根据需要添加

@router.get("/search_providers", summary="获取所有可用的搜索提供商")
async def get_search_providers():
    """获取所有可用的搜索提供商
    
    获取系统支持的所有搜索提供商列表
    """
    try:
        providers = await search_service.get_search_providers()
        return ResponseHandler.success("获取成功", providers)
    except Exception as e:
        return ResponseHandler.error(f"获取搜索提供商失败: {str(e)}")