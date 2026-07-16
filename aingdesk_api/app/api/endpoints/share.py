from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import os
import json
import time
import uuid
import shutil
from pathlib import Path

from app.services.share_service import ShareService
from app.core.config import settings
from app.models.response import ResponseHandler

router = APIRouter(tags=["share"])
share_service = ShareService()

# 请求模型
class ShareCreateRequest(BaseModel):
    supplierName: Optional[str] = None
    model: str
    parameters: str
    title: str
    password: Optional[str] = None
    rag_list: Optional[str] = None
    agent_name: Optional[str] = None
    mcp_servers: Optional[List[str]] = None

class ShareModifyRequest(BaseModel):
    share_id: str
    supplierName: Optional[str] = None
    model: str
    parameters: str
    title: str
    password: Optional[str] = None
    rag_list: Optional[str] = None
    agent_name: Optional[str] = None
    mcp_servers: Optional[List[str]] = None

class ShareRemoveRequest(BaseModel):
    share_id: str

class ShareHistoryRequest(BaseModel):
    share_id: str

class ShareServiceStatusRequest(BaseModel):
    status: str

# 常量
SHARE_URL = "https://share.aingdesk.com"



# 获取share路径
def get_share_path():
    share_path = os.path.join(settings.DATA_DIR, "share")
    os.makedirs(share_path, exist_ok=True)
    return share_path

# 获取share配置文件路径
def get_share_config_path(share_id: str):
    return os.path.join(get_share_path(), share_id, "config.json")

# 获取share上下文路径
def get_share_context_path(share_id: str):
    return os.path.join(get_share_path(), share_id, "context")

# 读取JSON文件
def read_json_file(file_path: str) -> Optional[Dict]:
    try:
        if not os.path.isfile(file_path):
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"读取JSON文件失败: {str(e)}")
        return None

# 保存JSON文件
def save_json_file(file_path: str, data: Dict):
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception as e:
        print(f"保存JSON文件失败: {str(e)}")

# 生成UUID
def generate_uuid():
    return str(uuid.uuid4())

# 获取当前时间戳
def get_time():
    return int(time.time())

@router.get("/get_share_list", summary="获取分享列表")
async def get_share_list():
    """获取分享列表
    
    获取所有已创建的分享列表，包含分享的基本信息和访问URL
    """
    try:
        share_path = get_share_path()
        share_list = []
        share_id_prefix = settings.SHARE_ID_PREFIX or "none"
        
        if os.path.exists(share_path):
            for share_id_path in os.listdir(share_path):
                share_id = os.path.basename(share_id_path)
                share_config_path = get_share_config_path(share_id)
                
                if os.path.exists(share_config_path):
                    share_config = read_json_file(share_config_path)
                    if share_config:
                        # 添加URL
                        share_config["url"] = f"{SHARE_URL}/{share_id_prefix}/{share_id}"
                        
                        # 获取聊天历史
                        history_result = await share_service.get_share_chat_history(share_id)
                        share_config["chats"] = history_result.get("message", [])
                        
                        # 确保rag_list存在
                        if "rag_list" not in share_config:
                            share_config["rag_list"] = []
                            
                        # 确保supplierName存在
                        if "supplierName" not in share_config:
                            share_config["supplierName"] = "ollama"
                            
                        share_list.append(share_config)
        
        # 按创建时间排序
        share_list.sort(key=lambda x: x.get("create_time", 0), reverse=True)
        
        return ResponseHandler.success("分享列表获取成功", share_list)
    except Exception as e:
        return ResponseHandler.error(f"获取分享列表失败: {str(e)}")

@router.post("/remove_share", summary="删除分享")
async def remove_share(request: ShareRemoveRequest):
    """删除分享
    
    删除指定的分享
    
    参数说明：
    - **share_id**: 分享ID（必填）
    """
    try:
        share_path = os.path.join(get_share_path(), request.share_id)
        
        if os.path.exists(share_path):
            try:
                shutil.rmtree(share_path)
            except Exception as e:
                print(f"删除分享目录失败: {str(e)}")
                return ResponseHandler.error("删除失败")
        
        return ResponseHandler.success("删除成功")
    except Exception as e:
        return ResponseHandler.error(f"删除分享失败: {str(e)}")

@router.post("/create_share", summary="创建分享")
async def create_share(request: ShareCreateRequest):
    """创建分享
    
    创建新的对话分享，支持设置密码保护和配置信息
    
    参数说明：
    - **supplierName**: 模型供应商名称，默认ollama（可选）
    - **model**: 模型名称（必填）
    - **parameters**: 模型参数配置（必填）
    - **title**: 分享标题（必填）
    - **password**: 访问密码，为空表示无密码（可选）
    - **rag_list**: 知识库列表，JSON格式字符串（可选）
    - **agent_name**: 智能体名称（可选）
    - **mcp_servers**: MCP服务器列表（可选）
    """
    try:
        share_id = generate_uuid()
        share_path = os.path.join(get_share_path(), share_id)
        
        # 创建分享目录
        try:
            os.makedirs(share_path, exist_ok=True)
        except Exception as e:
            print(f"创建分享目录失败: {str(e)}")
            return ResponseHandler.error("创建分享目录失败")
        
        # 解析rag_list
        rag_list = []
        if request.rag_list:
            try:
                rag_list = json.loads(request.rag_list)
            except:
                pass
        
        # 准备配置
        share_config = {
            "supplierName": request.supplierName or "ollama",
            "rag_list": rag_list,
            "share_id": share_id,
            "model": request.model,
            "parameters": request.parameters,
            "title": request.title,
            "agent_name": request.agent_name or "",
            "password": request.password,
            "mcp_servers": request.mcp_servers or [],
            "create_time": get_time(),
        }
        
        # 保存配置
        share_config_path = get_share_config_path(share_id)
        save_json_file(share_config_path, share_config)
        
        # 生成URL
        share_id_prefix = settings.SHARE_ID_PREFIX or "none"
        url = f"{SHARE_URL}/{share_id_prefix}/{share_id}"
        
        return ResponseHandler.success("创建成功", {"url": url, "password": request.password})
    except Exception as e:
        return ResponseHandler.error(f"创建分享失败: {str(e)}")

@router.post("/modify_share", summary="修改分享")
async def modify_share(request: ShareModifyRequest):
    """修改分享
    
    修改已存在的分享配置信息
    
    参数说明：
    - **share_id**: 分享ID（必填）
    - **supplierName**: 模型供应商名称（可选）
    - **model**: 模型名称（必填）
    - **parameters**: 模型参数配置（必填）
    - **title**: 分享标题（必填）
    - **password**: 访问密码，为空表示无密码（可选）
    - **rag_list**: 知识库列表，JSON格式字符串（可选）
    - **agent_name**: 智能体名称（可选）
    - **mcp_servers**: MCP服务器列表（可选）
    """
    try:
        share_path = os.path.join(get_share_path(), request.share_id)
        
        if not os.path.exists(share_path):
            return ResponseHandler.error("分享不存在")
        
        # 解析rag_list
        rag_list = []
        if request.rag_list:
            try:
                rag_list = json.loads(request.rag_list)
            except:
                pass
        
        # 读取现有配置
        share_config_path = get_share_config_path(request.share_id)
        old_config = read_json_file(share_config_path) or {}
        
        # 更新配置
        share_config = {
            **old_config,
            "supplierName": request.supplierName or old_config.get("supplierName", "ollama"),
            "rag_list": rag_list,
            "model": request.model,
            "parameters": request.parameters,
            "title": request.title,
            "agent_name": request.agent_name or old_config.get("agent_name", ""),
            "password": request.password,
            "mcp_servers": request.mcp_servers or old_config.get("mcp_servers", []),
        }
        
        # 保存配置
        save_json_file(share_config_path, share_config)
        
        # 生成URL
        share_id_prefix = settings.SHARE_ID_PREFIX or "none"
        url = f"{SHARE_URL}/{share_id_prefix}/{request.share_id}"
        
        return ResponseHandler.success("修改成功", {"url": url, "password": request.password})
    except Exception as e:
        return ResponseHandler.error(f"修改分享失败: {str(e)}")

@router.post("/get_share_chat_history", summary="获取分享聊天历史")
async def get_share_chat_history(request: ShareHistoryRequest):
    """获取分享聊天历史
    
    获取指定分享的所有聊天记录
    
    参数说明：
    - **share_id**: 分享ID（必填）
    """
    try:
        history = await share_service.get_share_chat_history(request.share_id)
        return ResponseHandler.success("获取成功", history)
    except Exception as e:
        return ResponseHandler.error(f"获取分享聊天历史失败: {str(e)}")

@router.post("/set_share_service_status", summary="设置分享服务状态")
async def set_share_service_status(request: ShareServiceStatusRequest):
    """设置分享服务状态
    
    设置分享服务的运行状态
    
    参数说明：
    - **status**: 服务状态，true/false（必填）
    """
    try:
        # 这里只是一个占位符，实际的服务状态管理需要更复杂的逻辑
        # 可以在此处更新某个配置或数据库中的状态
        status_bool = request.status.lower() == 'true'
        print(f"Setting share service status to: {status_bool}")
        return ResponseHandler.success("分享服务状态设置成功")
    except Exception as e:
        return ResponseHandler.error(f"设置分享服务状态失败: {str(e)}")

# 以下是扩展API，可以根据需要添加

@router.get("/share_status", summary="获取分享服务状态")
async def get_share_status():
    """获取分享服务状态
    
    获取当前分享服务的运行状态
    """
    try:
        # 这里只是一个占位符，实际的服务状态获取需要更复杂的逻辑
        # 可以在此处从某个配置或数据库中读取状态
        status = "running" # 模拟状态
        return ResponseHandler.success("获取成功", {"status": status})
    except Exception as e:
        return ResponseHandler.error(f"获取分享服务状态失败: {str(e)}")

@router.websocket("/ws/{share_id}")
async def websocket_endpoint(websocket: WebSocket, share_id: str):
    """WebSocket连接
    
    建立WebSocket连接，用于分享对话的实时聊天
    
    参数说明：
    - **share_id**: 分享ID（必填）
    - **websocket**: WebSocket连接对象
    """
    await websocket.accept()
    
    # 注册连接
    await share_service.register_connection(share_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_json()
            await share_service.handle_share_message(share_id, data, websocket)
    except WebSocketDisconnect:
        # 客户端断开连接
        await share_service.unregister_connection(share_id, websocket)
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await share_service.unregister_connection(share_id, websocket)