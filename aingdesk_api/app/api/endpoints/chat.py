from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import uuid
import json
import asyncio
from datetime import datetime
from app.services.chat_service import ChatService
from app.services.model_service import ModelService
from app.core.config import settings
from app.models.response import ResponseHandler

router = APIRouter(tags=["chat"])
chat_service = ChatService()
model_service = ModelService()

# 请求模型
class ChatCreateRequest(BaseModel):
    model: str
    parameters: str = ""  # 与Electron端保持一致，使用string类型
    title: str
    supplierName: Optional[str] = None
    agent_name: Optional[str] = None

class ChatRequest(BaseModel):
    context_id: str
    supplierName: Optional[str] = None
    model: str
    parameters: Optional[str] = None  # 与Electron端保持一致，使用string类型
    user_content: str
    search: Optional[str] = None
    searchProvider: Optional[str] = "baidu"
    images: Optional[str] = None
    doc_files: Optional[str] = None
    rag_list: Optional[List[str]] = None
    regenerate_id: Optional[str] = None
    rag_results: Optional[List[Any]] = None
    search_results: Optional[List[Any]] = None
    compare_id: Optional[str] = None
    mcp_servers: Optional[List[str]] = None

class ModifyChatTitleRequest(BaseModel):
    context_id: str
    title: str

class ChatHistoryDeleteRequest(BaseModel):
    context_id: str
    id: str

class StopGenerateRequest(BaseModel):
    context_id: str

class GetChatInfoRequest(BaseModel):
    context_id: str

class RemoveChatRequest(BaseModel):
    context_id: str

@router.post("/get_chat_list", summary="获取对话列表")
async def get_chat_list():
    """获取对话列表
    
    获取当前用户的所有对话列表，包含对话的基本信息
    """
    try:
        chat_list = await chat_service.get_chat_list()
        return ResponseHandler.success("对话列表获取成功", chat_list)
    except Exception as e:
        return ResponseHandler.error(f"获取对话列表失败: {str(e)}")

@router.post("/create_chat", summary="创建新的对话")
async def create_chat(request: ChatCreateRequest):
    """创建新的对话
    
    创建新的对话会话，用于与AI模型进行交互
    
    参数说明：
    - **model**: 使用的AI模型名称（必填）
    - **parameters**: 模型参数配置，如温度、最大token数等（可选）
    - **title**: 对话标题（必填）
    - **supplierName**: 模型供应商名称（可选）
    - **agent_name**: 关联的智能体名称（可选）
    """
    try:
        # 创建新对话并获取相关数据
        data = await chat_service.create_chat(
            model=request.model,
            parameters=request.parameters,
            title=request.title,
            supplier_name=request.supplierName,
            agent_name=request.agent_name or ""
        )
        return ResponseHandler.success("对话创建成功", data)
    except Exception as e:
        return ResponseHandler.error(f"创建对话失败: {str(e)}")

@router.post("/get_model_list", summary="获取模型列表")
async def get_model_list():
    """获取模型列表
    
    获取所有可用的AI模型列表，包括各供应商的模型信息
    返回包含供应商分类的模型列表和常用模型Top5
    """
    try:
        # 清空模型信息列表（Python端不需要，因为是新请求）
        
        # 获取Ollama模型列表并过滤嵌入模型
        ollama_models = await model_service.get_ollama_models()
        
        # 过滤掉嵌入模型（与Electron端保持一致）
        filtered_ollama_models = []
        for model in ollama_models:
            # 确保model是字典格式
            if not isinstance(model, dict):
                continue
                
            model_name = model.get("model", "").lower()
            
            # 检查是否为嵌入模型（与Electron端过滤逻辑保持一致）
            if any(keyword in model_name for keyword in ["embed", "bge-m3", "all-minilm", "multilingual", "r1-1776"]):
                continue
                
            filtered_ollama_models.append(model)
        
        # 获取所有供应商模型
        result = await model_service.get_supplier_models()
        
        # 添加Ollama模型到结果中
        if filtered_ollama_models:
            result["ollama"] = filtered_ollama_models
        
        # 计算常用模型Top5（不覆盖原有的result）
        top5_result = await model_service.get_model_top5(result)
        
        # 合并TOP5结果到原有result中
        if "commonModelList" in top5_result and top5_result["commonModelList"]:
            result["commonModelList"] = top5_result["commonModelList"]
        
        return ResponseHandler.success("大模型列表获取成功", result)
    except Exception as e:
        return ResponseHandler.error(f"获取模型列表失败: {str(e)}")

@router.post("/chat", summary="开始对话")
async def chat(request: ChatRequest, req: Request):
    """开始对话
    
    开始与AI模型的对话，支持流式响应
    
    参数说明：
    - **context_id**: 对话上下文ID（必填）
    - **supplierName**: 模型供应商名称（可选）
    - **model**: 使用的AI模型名称（必填）
    - **parameters**: 模型参数配置（可选）
    - **user_content**: 用户输入内容（必填）
    - **search**: 搜索关键词（可选）
    - **rag_list**: RAG知识库名称列表（可选）
    - **regenerate_id**: 重新生成的消息ID（可选）
    - **images**: 图片信息，base64编码（可选）
    - **doc_files**: 文档文件列表（可选）
    - **rag_results**: RAG搜索结果（可选）
    - **search_results**: 搜索结果（可选）
    - **compare_id**: 对比ID（可选）
    - **mcp_servers**: MCP服务器列表（可选）
    """
    try:
        # 创建响应流
        async def generate_stream():
            async for chunk in chat_service.chat(
                context_id=request.context_id,
                supplier_name=request.supplierName,
                model=request.model,
                parameters=request.parameters,
                user_content=request.user_content,
                search=request.search,
                search_provider=request.searchProvider or "baidu",
                rag_list=request.rag_list,
                regenerate_id=request.regenerate_id,
                images=request.images,
                doc_files=request.doc_files,
                rag_results=request.rag_results or [],
                search_results=request.search_results or [],
                compare_id=request.compare_id,
                mcp_servers=request.mcp_servers or []
            ):
                # 处理不同类型的chunk数据
                if isinstance(chunk, dict):
                    if chunk.get("error"):
                        yield json.dumps({"error": chunk["error"]}, ensure_ascii=False)
                        break
                    if chunk.get("event") == "done":
                        yield json.dumps(chunk, ensure_ascii=False)
                        break
                    # 流式文本内容
                    text = chunk.get("text", "")
                    if text:
                        yield text
                else:
                    # 对于字符串类型的内容，直接返回
                    yield str(chunk)

            yield "[DONE]\n\n"

        return StreamingResponse(generate_stream(), media_type="text/event-stream")
    except Exception as e:
        return ResponseHandler.error(f"聊天失败: {str(e)}")

@router.post("/get_chat_info", summary="获取指定对话信息")
async def get_chat_info(request: GetChatInfoRequest):
    """获取指定对话信息
    
    获取指定对话的详细信息和历史记录
    
    参数说明：
    - **context_id**: 对话上下文ID（必填）
    """
    try:
        data = await chat_service.get_chat_history(request.context_id)
        return ResponseHandler.success("对话信息获取成功", data)
    except Exception as e:
        return ResponseHandler.error(f"获取对话信息失败: {str(e)}")

@router.post("/remove_chat", summary="删除指定对话")
async def remove_chat(request: RemoveChatRequest):
    """删除指定对话
    
    删除一个或多个对话，支持批量删除
    
    参数说明：
    - **context_id**: 对话上下文ID，多个ID用逗号分隔（必填）
    """
    try:
        uuids = request.context_id.split(',')
        for uuid_item in uuids:
            await chat_service.delete_chat(uuid_item)
        return ResponseHandler.success("对话删除成功")
    except Exception as e:
        return ResponseHandler.error(f"删除对话失败: {str(e)}")

@router.post("/modify_chat_title", summary="修改对话标题")
async def modify_chat_title(request: ModifyChatTitleRequest):
    """修改对话标题
    
    修改指定对话的标题
    
    参数说明：
    - **context_id**: 对话上下文ID（必填）
    - **title**: 新的对话标题（必填）
    """
    try:
        success = await chat_service.update_chat_title(request.context_id, request.title)
        if success:
            return ResponseHandler.success("标题修改成功")
        else:
            return ResponseHandler.error("标题修改失败", None, 400)
    except Exception as e:
        return ResponseHandler.error(f"修改标题失败: {str(e)}")

@router.post("/delete_chat_history", summary="删除对话中的某条消息")
async def delete_chat_history(request: ChatHistoryDeleteRequest):
    """删除对话中的某条消息
    
    删除指定对话中的单条历史消息
    
    参数说明：
    - **context_id**: 对话上下文ID（必填）
    - **id**: 要删除的消息ID（必填）
    """
    try:
        # 删除对话历史记录 - 与Electron端实现保持一致
        await chat_service.delete_chat_history(request.context_id, request.id)
        # 返回成功响应 - 与Electron端保持一致
        return ResponseHandler.success("对话历史删除成功")
    except Exception as e:
        return ResponseHandler.error(f"删除消息失败: {str(e)}")

@router.post("/stop_generate", summary="停止生成响应")
async def stop_generate(request: StopGenerateRequest):
    """停止生成响应
    
    停止当前正在进行的AI响应生成
    
    参数说明：
    - **context_id**: 对话上下文ID（必填）
    """
    try:
        await chat_service.stop_generate(request.context_id)
        return ResponseHandler.success("已停止生成响应")
    except Exception as e:
        return ResponseHandler.error(f"停止生成失败: {str(e)}")

@router.post("/get_last_chat_history", summary="获取最后一条聊天记录")
async def get_last_chat_history(request: GetChatInfoRequest):
    """获取最后一条聊天记录
    
    获取指定对话中的最后一条聊天记录
    
    参数说明：
    - **context_id**: 对话上下文ID（必填）
    """
    try:
        # 获取最后一条历史记录 - 与Electron端实现保持一致
        data = await chat_service.get_last_chat_history(request.context_id)
        # 返回成功响应 - 与Electron端保持一致
        return ResponseHandler.success("最后一条历史对话记录获取成功", data)
    except Exception as e:
        return ResponseHandler.error(f"获取最后一条聊天记录失败: {str(e)}")