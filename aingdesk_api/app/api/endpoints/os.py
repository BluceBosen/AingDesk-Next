from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import platform
import subprocess
import base64
from pathlib import Path

from app.services.os_service import OsService
from app.core.config import settings
from app.models.response import ResponseHandler

router = APIRouter(tags=["os"])
os_service = OsService()

# 请求模型
class DirectoryRequest(BaseModel):
    id: str

class WindowRequest(BaseModel):
    id: Optional[str] = None
    url: Optional[str] = None
    width: Optional[int] = 800
    height: Optional[int] = 600

class CommunicateRequest(BaseModel):
    from_window: str
    to_window: str
    channel: str
    data: Any

class NotificationRequest(BaseModel):
    title: Optional[str] = None
    subtitle: Optional[str] = None
    body: Optional[str] = None
    silent: Optional[bool] = False



@router.get("/message_show", summary="显示消息对话框")
async def message_show():
    """显示消息对话框
    
    显示系统消息对话框（服务器端模拟实现）
    """
    try:
        # 由于这是服务器端API，我们不能显示真正的对话框
        # 只能模拟返回
        return ResponseHandler.success("消息对话框已显示")
    except Exception as e:
        return ResponseHandler.error(f"显示消息对话框失败: {str(e)}")

@router.get("/message_show_confirm", summary="显示确认对话框")
async def message_show_confirm():
    """显示确认对话框
    
    显示系统确认对话框（服务器端模拟实现）
    """
    try:
        # 由于这是服务器端API，我们不能显示真正的对话框
        # 只能模拟返回
        return ResponseHandler.success("确认对话框已点击确认")
    except Exception as e:
        return ResponseHandler.error(f"显示确认对话框失败: {str(e)}")

@router.get("/select_folder", summary="选择文件夹")
async def select_folder():
    """选择文件夹
    
    显示系统文件夹选择对话框（服务器端模拟实现）
    """
    try:
        # 由于这是服务器端API，我们不能显示文件选择对话框
        # 只能返回默认路径
        return ResponseHandler.success("文件夹选择成功", os.path.join(settings.DATA_DIR, "selected_folder"))
    except Exception as e:
        return ResponseHandler.error(f"选择文件夹失败: {str(e)}")

@router.post("/open_directory", summary="打开目录")
async def open_directory(request: DirectoryRequest):
    """打开目录
    
    打开指定的目录路径（服务器端模拟实现）
    
    参数说明：
    - **id**: 目录ID（必填）
    """
    try:
        # 参数检查
        if not request.id:
            return ResponseHandler.error("目录ID不能为空")
            
        # 由于这是服务器端API，我们不能真正打开目录
        # 只能模拟返回成功
        return ResponseHandler.success("目录已尝试打开")
    except Exception as e:
        return ResponseHandler.error(f"打开目录失败: {str(e)}")

@router.get("/select_pic", summary="选择图片")
async def select_pic():
    """选择图片
    
    显示系统图片选择对话框（服务器端模拟实现）
    """
    try:
        # 由于这是服务器端API，我们不能显示文件选择对话框
        # 只能返回空或默认图像
        return ResponseHandler.success("图片选择成功", None)
    except Exception as e:
        return ResponseHandler.error(f"选择图片失败: {str(e)}")

@router.post("/create_window", summary="创建新窗口")
async def create_window(request: WindowRequest):
    """创建新窗口
    
    创建新的系统窗口（服务器端模拟实现）
    
    参数说明：
    - **id**: 窗口ID（可选）
    - **url**: 窗口URL（可选）
    - **width**: 窗口宽度，默认800（可选）
    - **height**: 窗口高度，默认600（可选）
    """
    try:
        # 由于这是服务器端API，我们不能真正创建窗口
        # 只能模拟返回窗口ID
        window_id = await os_service.create_window(request.dict())
        return ResponseHandler.success("窗口创建成功", {"window_id": window_id})
    except Exception as e:
        return ResponseHandler.error(f"创建窗口失败: {str(e)}")

@router.post("/get_wcid", summary="获取窗口内容ID")
async def get_wcid(request: WindowRequest):
    """获取窗口内容ID
    
    获取窗口的内容ID（服务器端模拟实现）
    
    参数说明：
    - **id**: 窗口ID（可选）
    - **url**: 窗口URL（可选）
    - **width**: 窗口宽度（可选）
    - **height**: 窗口高度（可选）
    """
    try:
        # 由于这是服务器端API，我们只能模拟返回窗口内容ID
        wcid = await os_service.get_wcid(request.dict())
        return ResponseHandler.success("窗口内容ID获取成功", {"wcid": wcid})
    except Exception as e:
        return ResponseHandler.error(f"获取窗口内容ID失败: {str(e)}")

@router.post("/window1_to_window2", summary="窗口间通信1")
async def window1_to_window2(request: CommunicateRequest):
    """窗口间通信1
    
    从窗口1向窗口2发送消息（服务器端模拟实现）
    
    参数说明：
    - **from_window**: 源窗口ID（必填）
    - **to_window**: 目标窗口ID（必填）
    - **channel**: 通信通道（必填）
    - **data**: 传输数据（必填）
    """
    try:
        await os_service.communicate(request.dict())
        return ResponseHandler.success("窗口通信成功")
    except Exception as e:
        return ResponseHandler.error(f"窗口通信失败: {str(e)}")

@router.post("/window2_to_window1", summary="窗口间通信2")
async def window2_to_window1(request: CommunicateRequest):
    """窗口间通信2
    
    从窗口2向窗口1发送消息（服务器端模拟实现）
    
    参数说明：
    - **from_window**: 源窗口ID（必填）
    - **to_window**: 目标窗口ID（必填）
    - **channel**: 通信通道（必填）
    - **data**: 传输数据（必填）
    """
    try:
        await os_service.communicate(request.dict())
        return ResponseHandler.success("窗口通信成功")
    except Exception as e:
        return ResponseHandler.error(f"窗口通信失败: {str(e)}")

@router.post("/send_notification", summary="发送系统通知")
async def send_notification(request: NotificationRequest):
    """发送系统通知
    
    发送系统通知消息（服务器端模拟实现）
    
    参数说明：
    - **title**: 通知标题（可选）
    - **subtitle**: 通知副标题（可选）
    - **body**: 通知内容（可选）
    - **silent**: 是否静默通知（可选）
    """
    try:
        # 构建通知选项
        options = {}
        if request.title:
            options["title"] = request.title
        if request.subtitle:
            options["subtitle"] = request.subtitle
        if request.body:
            options["body"] = request.body
        if request.silent is not None:
            options["silent"] = request.silent
            
        # 由于这是服务器端API，我们不能真正发送系统通知
        # 只能模拟返回成功
        return ResponseHandler.success("系统通知已发送")
    except Exception as e:
        return ResponseHandler.error(f"发送通知失败: {str(e)}")

# 额外的API，提供系统信息

@router.get("/system_info", summary="获取系统信息")
async def system_info():
    """获取系统信息
    
    获取当前系统的基础信息，包括平台、架构、Python版本等
    """
    try:
        info = {
            "platform": platform.system(),
            "version": platform.version(),
            "architecture": platform.architecture(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
        }
        return ResponseHandler.success("获取成功", info)
    except Exception as e:
        return ResponseHandler.error(f"获取系统信息失败: {str(e)}")