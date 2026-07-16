from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import os
import json
import time
from pathlib import Path
from app.models.response import ResponseHandler
from app.core.config import settings
from app.services.task_manager import task_manager, TaskType

router = APIRouter(tags=["index"])

# 请求模型
class SetLanguageRequest(BaseModel):
    language: str = Field(..., description="要设置的语言")

class SetDataSavePathRequest(BaseModel):
    newPath: str = Field(..., description="新的数据保存路径")

class WriteLogsRequest(BaseModel):
    logs: str = Field(..., description="日志内容")

# 工具函数
def get_language_path() -> str:
    """获取语言文件路径"""
    language_path = os.path.join(settings.DATA_DIR, "lang")
    os.makedirs(language_path, exist_ok=True)
    return language_path

def get_system_data_path() -> str:
    """获取系统数据路径"""
    return settings.DATA_DIR

def read_file(file_path: str) -> str:
    """读取文件内容"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    except Exception:
        return ""

def write_json(file_path: str, data: Dict[str, Any]) -> bool:
    """写入JSON文件"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception:
        return False

def read_json(file_path: str) -> Dict[str, Any]:
    """读取JSON文件"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def file_exists(file_path: str) -> bool:
    """检查文件是否存在"""
    return os.path.exists(file_path)

def readdir(path: str) -> list:
    """读取目录内容"""
    try:
        return os.listdir(path)
    except Exception:
        return []

def get_version() -> str:
    """获取版本信息"""
    # 从package.json或配置文件读取版本
    package_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "package.json")
    try:
        with open(package_path, 'r', encoding='utf-8') as f:
            package_data = json.load(f)
            return package_data.get("version", "1.0.0")
    except:
        return "1.0.0"

def get_language() -> str:
    """获取当前语言"""
    # 从配置文件读取当前语言
    config_path = os.path.join(get_system_data_path(), "config.json")
    config = read_json(config_path)
    return config.get("language", "zh")

# API接口
@router.get("/get_version", summary="获取版本信息")
async def get_version_api():
    """获取应用版本信息"""
    try:
        version = get_version()
        return ResponseHandler.success("获取成功", {"version": version})
    except Exception as e:
        return ResponseHandler.error(f"获取版本信息失败: {str(e)}")

@router.get("/get_languages", summary="获取语言列表")
async def get_languages():
    """获取当前语言和支持的语言列表"""
    try:
        settings_file_path = os.path.join(get_language_path(), 'settings.json')
        file_content = read_file(settings_file_path)
        
        # 默认语言列表
        if not file_content:
            file_content = """[
                {
                    "name": "zh",
                    "google": "zh-cn",
                    "title": "简体中文",
                    "cn": "简体中文"
                },
                {
                    "name": "en",
                    "google": "en",
                    "title": "English",
                    "cn": "英语"
                }
            ]"""
        
        current_language = get_language()
        languages = json.loads(file_content)
        
        data = {
            "languages": languages,
            "current": current_language
        }
        
        return ResponseHandler.success("获取成功", data)
    except Exception as e:
        return ResponseHandler.error(f"获取语言列表失败: {str(e)}")

@router.post("/set_language", summary="设置当前语言")
async def set_language(request: SetLanguageRequest):
    """设置当前语言"""
    try:
        language = request.language
        
        # 更新配置文件
        config_path = os.path.join(get_system_data_path(), "config.json")
        config = read_json(config_path)
        config["language"] = language
        write_json(config_path, config)
        
        return ResponseHandler.success("设置成功", None)
    except Exception as e:
        return ResponseHandler.error(f"设置语言失败: {str(e)}")

@router.get("/get_client_language", summary="获取客户端语言包")
async def get_client_language():
    """获取客户端语言包"""
    try:
        return await get_language_pack("client")
    except Exception as e:
        return ResponseHandler.error(f"获取客户端语言包失败: {str(e)}")

@router.get("/get_server_language", summary="获取服务端语言包")
async def get_server_language():
    """获取服务端语言包"""
    try:
        return await get_language_pack("server")
    except Exception as e:
        return ResponseHandler.error(f"获取服务端语言包失败: {str(e)}")

async def get_language_pack(type: str):
    """通用的获取语言包方法"""
    current_language = get_language()
    language_file_path = os.path.join(get_language_path(), f"{current_language}/{type}.json")
    
    # 如果文件不存在，使用默认中文
    if not file_exists(language_file_path):
        language_file_path = os.path.join(get_language_path(), f"zh/{type}.json")
    
    file_content = read_file(language_file_path)
    if not file_content:
        file_content = "{}"
    
    language_pack = json.loads(file_content)
    return ResponseHandler.success("获取成功", language_pack)

@router.post("/write_logs", summary="写入日志")
async def write_logs(request: WriteLogsRequest):
    """接收前端错误日志，并写入到日志文件"""
    try:
        logs = request.logs
        # 记录到日志文件
        log_path = os.path.join(get_system_data_path(), "logs", "frontend.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {logs}\n")
        
        return ResponseHandler.success("写入成功")
    except Exception as e:
        return ResponseHandler.error(f"写入日志失败: {str(e)}")

@router.get("/get_data_save_path", summary="获取数据保存路径")
async def get_data_save_path():
    """获取数据保存路径配置"""
    try:
        save_path_config_file = os.path.join(get_system_data_path(), 'save_path.json')
        
        if not file_exists(save_path_config_file):
            current_path = get_system_data_path()
            config = {
                "oldPath": "",
                "currentPath": current_path,
                "isMove": False,
                "isMoveSuccess": False,
                "isClearOldPath": False,
                "dataSize": 0,
                "copyStatus": {
                    "status": 0,  # 0:未开始,1:正在复制,2:复制完成,-1:复制失败
                    "speed": 0,
                    "total": 0,
                    "current": 0,
                    "percent": 0,
                    "startTime": 0,
                    "endTime": 0,
                    "fileTotal": 0,
                    "fileCurrent": 0,
                    "message": "",
                    "error": ""
                }
            }
            write_json(save_path_config_file, config)
        
        save_path_config = read_json(save_path_config_file)
        return ResponseHandler.success("获取成功", save_path_config)
    except Exception as e:
        return ResponseHandler.error(f"获取数据保存路径失败: {str(e)}")

@router.post("/set_data_save_path", summary="设置数据保存路径")
async def set_data_save_path(request: SetDataSavePathRequest):
    """设置数据保存路径"""
    try:
        new_path = request.newPath
        
        if not new_path:
            return ResponseHandler.error("请选择目录", None, 400)
        
        if not os.path.exists(new_path):
            return ResponseHandler.error("指定的目录不存在", None, 400)
        
        # 检查目录是否为空
        files = readdir(new_path)
        if files and len(files) > 0:
            return ResponseHandler.error("指定的目录不是空目录", None, 400)
        
        save_path_config_file = os.path.join(get_system_data_path(), 'save_path.json')
        if not file_exists(save_path_config_file):
            return ResponseHandler.error("配置文件不存在，请先调用获取数据保存路径接口", None, 400)
        
        save_path_config = read_json(save_path_config_file)
        
        # 更新配置
        save_path_config["oldPath"] = save_path_config["currentPath"]
        save_path_config["currentPath"] = new_path
        save_path_config["isMove"] = True
        save_path_config["isMoveSuccess"] = False
        
        # 重置复制状态
        save_path_config["copyStatus"] = {
            "status": 0,
            "speed": 0,
            "total": 0,
            "current": 0,
            "percent": 0,
            "startTime": 0,
            "endTime": 0,
            "fileTotal": 0,
            "fileCurrent": 0,
            "message": "",
            "error": ""
        }
        
        write_json(save_path_config_file, save_path_config)
        
        return ResponseHandler.success("设置成功,正在复制数据，请稍后查看进度")
    except Exception as e:
        return ResponseHandler.error(f"设置数据保存路径失败: {str(e)}")

# 任务管理相关接口
@router.get("/task_status/{task_id}", summary="查询任务状态")
async def get_task_status(task_id: str):
    """
    查询异步任务状态
    
    参数说明：
    - **task_id**: 任务ID（必填）
    
    返回：
    - 任务状态信息，包括进度、状态、结果等
    """
    try:

        task_status = task_manager.get_task_status(task_id)

        if task_status is None:
            return ResponseHandler.error("任务不存在")

        return ResponseHandler.success("获取任务状态成功", task_status)

    except Exception as e:
        return ResponseHandler.error(f"查询任务状态失败: {str(e)}")

@router.get("/task_list", summary="获取任务列表")
async def get_task_list(
    limit: int = Query(default=50, ge=1, le=1000, description="返回任务数量限制")
):
    """
    获取异步任务列表
    
    参数说明：
    - **limit**: 返回任务数量限制（可选，默认50，最大1000）
    
    返回：
    - 任务列表，按创建时间倒序排列
    """
    try:

        task_list = task_manager.get_all_tasks(limit)

        return ResponseHandler.success("获取任务列表成功", task_list)

    except Exception as e:
        return ResponseHandler.error(f"获取任务列表失败: {str(e)}")

@router.post("/cancel_task/{task_id}", summary="取消任务")
async def cancel_task(task_id: str):
    """
    取消异步任务
    
    只能取消状态为pending的任务
    
    参数说明：
    - **task_id**: 任务ID（必填）
    
    返回：
    - 取消结果
    """
    try:


        success = task_manager.cancel_task(task_id)

        if success:
            return ResponseHandler.success("任务取消成功")
        else:
            return ResponseHandler.error("任务不存在或无法取消（只能取消待处理状态的任务）")

    except Exception as e:
        return ResponseHandler.error(f"取消任务失败: {str(e)}")