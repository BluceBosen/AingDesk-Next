from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import os
import json
import platform
import subprocess
import shutil
from pathlib import Path

# 可选导入psutil，如果不存在则提供备用方案
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not available. Some system info features will be limited.")

from app.services.manager_service import ManagerService
from app.core.config import settings
from app.models.response import ResponseHandler

router = APIRouter(tags=["manager"])
manager_service = ManagerService()

# 请求模型
class ModelInstallRequest(BaseModel):
    model: str
    parameters: Optional[str] = ""

class ModelInstallProgressRequest(BaseModel):
    model: str
    parameters: Optional[str] = ""

class ModelRemoveRequest(BaseModel):
    model: str
    parameters: Optional[str] = ""

class ManagerInstallRequest(BaseModel):
    manager_name: str
    models_path: Optional[str] = None

class ManagerInstallProgressRequest(BaseModel):
    manager_name: str

class OllamaModelSavePathRequest(BaseModel):
    save_path: str

class OllamaHostRequest(BaseModel):
    ollama_host: str



@router.post("/get_model_manager", summary="获取模型管理器信息")
async def get_model_manager():
    """获取模型管理器信息
    
    获取当前模型管理器（Ollama）的详细信息，包括版本、模型列表和运行状态
    """
    try:
        # 创建 OllamaService 实例
        from app.services.ollama_service import OllamaService
        ollama_service = OllamaService()
        
        # 获取 Ollama 版本信息
        version = await ollama_service.version()
        
        # 检查服务是否启动
        if version:
            is_running = await ollama_service.is_running()
            if not is_running:
                if not await ollama_service.start():
                    print("Ollama 服务启动失败")
        
        # 构建模型管理器信息对象 - 与Electron实现保持一致
        model_manager = {
            "manager_name": "ollama",
            "version": version,
            "models": await ollama_service.model_list(),  # 使用OllamaService的model_list方法，包含完整模型列表
            "status": len(version) > 0 if version else False,
            "ollama_host": await manager_service.get_ollama_host()
        }
        
        return ResponseHandler.success("模型管理器信息获取成功", model_manager)
    except Exception as e:
        return ResponseHandler.error(f"获取模型管理器信息失败: {str(e)}")

@router.post("/install_model", summary="安装模型")
async def install_model(request: ModelInstallRequest, background_tasks: BackgroundTasks):
    """安装模型
    
    在后台安装指定的AI模型
    
    参数说明：
    - **model**: 模型名称（必填）
    - **parameters**: 模型参数配置（可选）
    """
    try:
        # 在后台任务中安装模型
        background_tasks.add_task(manager_service.install_model, request.model, request.parameters or "")
        return ResponseHandler.success("模型安装已开始，正在后台进行", {"model": request.model})
    except Exception as e:
        return ResponseHandler.error(f"安装模型失败: {str(e)}")

@router.post("/get_model_install_progress", summary="获取模型安装进度")
async def get_model_install_progress(request: ModelInstallProgressRequest):
    """获取模型安装进度
    
    获取指定模型的安装进度信息
    
    参数说明：
    - **model**: 模型名称（必填）
    - **parameters**: 模型参数配置（可选）
    """
    try:
        progress = await manager_service.get_model_install_progress(request.model, request.parameters or "")
        return ResponseHandler.success("获取安装进度成功", progress)
    except Exception as e:
        return ResponseHandler.error(f"获取安装进度失败: {str(e)}")

@router.post("/remove_model", summary="删除模型")
async def remove_model(request: ModelRemoveRequest):
    """删除模型
    
    删除指定的AI模型
    
    参数说明：
    - **model**: 模型名称（必填）
    - **parameters**: 模型参数配置（可选）
    """
    try:
        result = await manager_service.remove_model(request.model, request.parameters or "")
        return ResponseHandler.success("删除成功", result)
    except Exception as e:
        return ResponseHandler.error(f"删除模型失败: {str(e)}")

@router.post("/install_model_manager", summary="安装模型管理器")
async def install_model_manager(request: ManagerInstallRequest, background_tasks: BackgroundTasks):
    """安装模型管理器
    
    安装指定的模型管理器（目前仅支持Ollama）
    
    参数说明：
    - **manager_name**: 管理器名称，目前仅支持"ollama"（必填）
    - **models_path**: 模型存储路径（可选）
    """
    try:
        # 检查是否支持该模型管理器
        if request.manager_name != "ollama":
            return ResponseHandler.error("不支持的管理器", None, 400)
        
        # 检查模型存储路径
        if request.models_path and request.models_path.strip():
            if not os.path.exists(request.models_path):
                return ResponseHandler.error("指定模型存储路径不存在", None, 400)
            await manager_service.set_ollama_model_save_path(request.models_path)
        
        # 在后台任务中安装Ollama
        background_tasks.add_task(manager_service.install_ollama)
        return ResponseHandler.success("正在安装,请稍后...")
    except Exception as e:
        return ResponseHandler.error(f"安装模型管理器失败: {str(e)}")

@router.post("/get_model_manager_install_progress", summary="获取模型管理器安装进度")
async def get_model_manager_install_progress(request: ManagerInstallProgressRequest):
    """获取模型管理器安装进度
    
    获取模型管理器的安装进度信息
    
    参数说明：
    - **manager_name**: 管理器名称，目前仅支持"ollama"（必填）
    """
    try:
        if request.manager_name != "ollama":
            return ResponseHandler.error("不支持的管理器", None, 400)
            
        progress = await manager_service.get_ollama_install_progress()
        return ResponseHandler.success("获取安装进度成功", progress)
    except Exception as e:
        return ResponseHandler.error(f"获取安装进度失败: {str(e)}")

@router.post("/get_configuration_info", summary="获取电脑配置信息")
async def get_configuration_info():
    """获取电脑配置信息
    
    获取当前电脑的详细硬件配置信息，包括CPU、内存、GPU、操作系统等
    """
    try:
        config_info = manager_service.get_configuration_info()
        return ResponseHandler.success("获取配置信息成功", config_info)
    except Exception as e:
        return ResponseHandler.error(f"获取配置信息失败: {str(e)}")

@router.post("/get_disk_list", summary="获取磁盘信息")
async def get_disk_list():
    """获取磁盘信息
    
    获取系统中所有磁盘分区的详细信息，包括容量和使用情况
    """
    try:
        disk_list = []
        
        if PSUTIL_AVAILABLE:
            disk_partitions = psutil.disk_partitions()
            
            for partition in disk_partitions:
                try:
                    partition_usage = psutil.disk_usage(partition.mountpoint)
                    disk_info = {
                        "mountpoint": partition.mountpoint,
                        "total": partition_usage.total,
                        "used": partition_usage.used,
                        "free": partition_usage.free,
                        "progress": int((partition_usage.used / partition_usage.total) * 100) if partition_usage.total > 0 else 0
                    }
                    disk_list.append(disk_info)
                except PermissionError:
                    # 跳过无权限访问的分区
                    continue
                except Exception:
                    # 跳过其他错误的分区
                    continue
        else:
            # 提供默认磁盘信息
            disk_list.append({
                "mountpoint": "C:\\",
                "total": 500 * 1024 * 1024 * 1024,  # 默认500GB
                "used": 200 * 1024 * 1024 * 1024,   # 默认200GB已使用
                "free": 300 * 1024 * 1024 * 1024,   # 默认300GB可用
                "progress": 40  # 40%使用率
            })
        
        return ResponseHandler.success("获取磁盘信息成功", disk_list)
    except Exception as e:
        return ResponseHandler.error(f"获取磁盘信息失败: {str(e)}")

@router.post("/set_ollama_model_save_path", summary="修改Ollama模型保存路径")
async def set_ollama_model_save_path(request: OllamaModelSavePathRequest):
    """修改Ollama模型保存路径
    
    修改Ollama模型的默认保存路径
    
    参数说明：
    - **save_path**: 新的模型保存路径（必填）
    """
    try:
        result = await manager_service.set_ollama_model_save_path(request.save_path)
        return ResponseHandler.success("修改成功", result)
    except Exception as e:
        return ResponseHandler.error(f"修改模型保存路径失败: {str(e)}")

@router.post("/reconnect_model_download", summary="重连模型下载任务")
async def reconnect_model_download():
    """重连模型下载任务
    
    断开并重连模型下载任务，用于断点续传下载
    """
    try:
        result = await manager_service.reconnect_model_download()
        return ResponseHandler.success("将为您重新下载，并断点续传。", result)
    except Exception as e:
        return ResponseHandler.error(f"重连模型下载失败: {str(e)}")

@router.post("/set_ollama_host", summary="设置Ollama连接地址")
async def set_ollama_host(request: OllamaHostRequest):
    """设置Ollama连接地址
    
    设置连接到Ollama服务的地址和端口
    
    参数说明：
    - **ollama_host**: Ollama服务地址，格式为host:port（必填）
    """
    try:
        result = await manager_service.set_ollama_host(request.ollama_host)
        if result:
            return ResponseHandler.success("设置成功", result)
        else:
            return ResponseHandler.error("指定接口地址连接失败", None, 400)
    except Exception as e:
        return ResponseHandler.error(f"设置ollama连接地址失败: {str(e)}")

@router.post("/get_ollama_executable_path", summary="获取Ollama可执行文件路径")
async def get_ollama_executable_path():
    """获取Ollama可执行文件路径
    
    获取Ollama可执行文件在系统中的完整路径
    """
    try:
        path = manager_service.get_ollama_executable_path()
        return ResponseHandler.success("获取Ollama可执行文件路径成功", {"path": path})
    except Exception as e:
        return ResponseHandler.error(f"获取Ollama可执行文件路径失败: {str(e)}")

# 额外的API接口

@router.get("/system_info", summary="获取系统基础信息")
async def get_system_info():
    """获取系统基础信息
    
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
        
        if PSUTIL_AVAILABLE:
            info.update({
                "cpu_count": psutil.cpu_count(),
                "memory_total": psutil.virtual_memory().total,
                "memory_available": psutil.virtual_memory().available,
            })
        else:
            info.update({
                "cpu_count": os.cpu_count() or 1,
                "memory_total": 8 * 1024 * 1024 * 1024,  # 默认8GB
                "memory_available": 4 * 1024 * 1024 * 1024,  # 默认4GB
            })
        
        return ResponseHandler.success("获取成功", info)
    except Exception as e:
        return ResponseHandler.error(f"获取系统信息失败: {str(e)}")

@router.get("/process_info", summary="获取当前进程信息")
async def get_process_info():
    """获取当前进程信息
    
    获取当前运行的进程信息，包括PID、内存使用等
    """
    try:
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            info = {
                "pid": process.pid,
                "name": process.name(),
                "cpu_percent": process.cpu_percent(),
                "memory_info": process.memory_info()._asdict(),
                "create_time": process.create_time(),
                "status": process.status(),
            }
        else:
            info = {
                "pid": os.getpid(),
                "name": "python",
                "cpu_percent": 0.0,
                "memory_info": {"rss": 100 * 1024 * 1024, "vms": 200 * 1024 * 1024},
                "create_time": 0,
                "status": "running",
            }
        
        return ResponseHandler.success("获取成功", info)
    except Exception as e:
        return ResponseHandler.error(f"获取进程信息失败: {str(e)}")