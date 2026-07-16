from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import os
import json
import subprocess
import platform
import asyncio
from pathlib import Path

from app.services.mcp_service import McpService
from app.core.config import settings
from app.models.response import ResponseHandler

router = APIRouter(tags=["mcp"])
mcp_service = McpService()

# 请求模型
class McpServerListRequest(BaseModel):
    pass

class CommonServerListRequest(BaseModel):
    pass

class McpServerInfoRequest(BaseModel):
    name: str

class McpServerModifyRequest(BaseModel):
    name: str
    description: str
    type: str  # "stdio" | "sse"
    command: str
    baseUrl: Optional[str] = ""
    env: Optional[Dict[str, str]] = {}
    args: Optional[List[str]] = []
    is_active: bool

class McpServerRemoveRequest(BaseModel):
    name: str

class McpServerAddRequest(BaseModel):
    name: str
    description: str
    type: str  # "stdio" | "sse"
    command: str
    baseUrl: Optional[str] = ""
    env: Optional[Dict[str, str]] = {}
    args: Optional[List[str]] = []

class McpToolsModifyRequest(BaseModel):
    name: str
    tools: Dict[str, bool]

class McpToolsRequest(BaseModel):
    name: str

class McpStatusRequest(BaseModel):
    pass

class InstallNpxRequest(BaseModel):
    pass

class InstallUvRequest(BaseModel):
    pass

class McpConfigBodyRequest(BaseModel):
    mcp_config_body: str

class RegistryListRequest(BaseModel):
    pass

class SyncCloudMcpRequest(BaseModel):
    pass



@router.post("/get_mcp_server_list", summary="获取已安装的MCP服务器列表")
async def get_mcp_server_list(request: McpServerListRequest):
    """获取已安装的MCP服务器列表 - 与Electron端实现保持一致
    
    获取所有已安装的MCP服务器列表，包含服务器信息和工具列表
    """
    try:
        # 获取MCP服务器列表 - 与Electron端get_mcp_servers保持一致
        servers = await mcp_service.get_mcp_servers()
        
        # 获取每个服务器的工具列表 - 与Electron端逻辑保持一致
        for server in servers:
            server['tools'] = await mcp_service.read_mcp_tools(server['name'])
        
        # 返回成功响应 - 与Electron端pub.return_success保持一致
        return ResponseHandler.success("获取成功", servers)
    except Exception as e:
        return ResponseHandler.error(f"获取MCP服务器列表失败: {str(e)}")

@router.post("/get_common_server_list", summary="获取常用的MCP服务器列表")
async def get_common_server_list(request: CommonServerListRequest):
    """获取常用的MCP服务器列表 - 与Electron端实现保持一致
    
    获取预定义的常用MCP服务器列表，包含安装状态信息
    """
    try:
        # 获取常用MCP服务器配置 - 与Electron端read_common_mcp_config保持一致
        common_servers = await mcp_service.read_common_mcp_config()
        # 获取已安装的MCP服务器列表 - 与Electron端get_mcp_servers保持一致
        installed_servers = await mcp_service.get_mcp_servers()
        
        # 判断是否已安装 - 与Electron端逻辑保持一致
        if common_servers and common_servers:
            for server in common_servers:
                if installed_servers and len(installed_servers) > 0:
                    # 查找已安装的服务器 - 与Electron端find逻辑保持一致
                    installed_server = next((s for s in installed_servers if s.get('name') == server.get('name')), None)
                    server['is_install'] = bool(installed_server)
                else:
                    server['is_install'] = False
        
        # 返回成功响应 - 与Electron端pub.return_success保持一致
        return ResponseHandler.success("获取成功", common_servers)
    except Exception as e:
        return ResponseHandler.error(f"获取常用MCP服务器列表失败: {str(e)}")

@router.post("/get_mcp_server_info", summary="获取MCP服务器信息")
async def get_mcp_server_info(request: McpServerInfoRequest):
    """获取MCP服务器信息 - 与Electron端实现保持一致
    
    获取指定MCP服务器的详细信息和工具列表
    
    参数说明：
    - **name**: 服务器名称（必填）
    """
    try:
        # 获取MCP服务器列表 - 与Electron端get_mcp_servers保持一致
        servers = await mcp_service.get_mcp_servers()
        # 查找指定服务器 - 与Electron端逻辑保持一致
        server = next((s for s in servers if s.get('name') == request.name), None)
        
        if not server:
            return ResponseHandler.error("未找到该服务器")
        
        # 获取服务器工具列表 - 与Electron端逻辑保持一致
        # TODO: 需要根据服务器类型获取对应的工具列表
        tools = await mcp_service.read_mcp_tools(request.name)
        server['tools'] = tools
        
        # 返回成功响应 - 与Electron端pub.return_success保持一致
        return ResponseHandler.success("获取成功", server)
    except Exception as e:
        return ResponseHandler.error(f"获取MCP服务器信息失败: {str(e)}")

@router.post("/modify_mcp_server", summary="修改MCP服务器信息")
async def modify_mcp_server(request: McpServerModifyRequest):
    """修改MCP服务器信息 - 与Electron端实现保持一致
    
    修改指定MCP服务器的配置信息
    
    参数说明：
    - **name**: 服务器名称（必填）
    - **description**: 服务器描述（必填）
    - **type**: 服务器类型，支持stdio或sse（必填）
    - **command**: 启动命令（必填）
    - **baseUrl**: 基础URL，SSE类型时必填（可选）
    - **env**: 环境变量字典（可选）
    - **args**: 启动参数列表（可选）
    - **is_active**: 是否激活（必填）
    """
    try:
        # 读取MCP配置 - 与Electron端read_mcp_config保持一致
        servers = await mcp_service.get_mcp_servers()
        
        # 查找指定服务器 - 与Electron端find逻辑保持一致
        server = next((s for s in servers if s.get('name') == request.name), None)
        if not server:
            return ResponseHandler.error("未找到该服务器")
        
        # 更新服务器配置 - 与Electron端字段赋值保持一致
        server['description'] = request.description
        server['type'] = request.type
        server['command'] = request.command
        server['baseUrl'] = request.baseUrl
        server['env'] = request.env
        server['args'] = request.args
        server['isActive'] = request.is_active
        
        # 保存配置文件 - 与Electron端save_mcp_config保持一致
        success = await mcp_service.save_mcp_config(servers)
        
        # 返回成功响应 - 与Electron端pub.return_success保持一致
        if success:
            return ResponseHandler.success("修改成功")
        else:
            return ResponseHandler.error("修改失败")
    except Exception as e:
        return ResponseHandler.error(f"修改MCP服务器失败: {str(e)}")

@router.post("/remove_mcp_server", summary="卸载MCP服务器")
async def remove_mcp_server(request: McpServerRemoveRequest):
    """卸载MCP服务器 - 与Electron端实现保持一致
    
    卸载指定的MCP服务器
    
    参数说明：
    - **name**: 服务器名称（必填）
    """
    try:
        # 读取MCP配置 - 与Electron端read_mcp_config保持一致
        servers = await mcp_service.get_mcp_servers()
        
        # 查找服务器索引 - 与Electron端findIndex逻辑保持一致
        server_index = next((i for i, s in enumerate(servers) if s.get('name') == request.name), -1)
        if server_index == -1:
            return ResponseHandler.error("未找到该服务器")
        
        # 删除服务器 - 与Electron端splice逻辑保持一致
        servers.pop(server_index)
        
        # 保存配置文件 - 与Electron端save_mcp_config保持一致
        success = await mcp_service.save_mcp_config(servers)
        
        # 返回成功响应 - 与Electron端pub.return_success保持一致
        if success:
            return ResponseHandler.success("卸载成功")
        else:
            return ResponseHandler.error("卸载失败")
    except Exception as e:
        return ResponseHandler.error(f"卸载MCP服务器失败: {str(e)}")

@router.post("/add_mcp_server", summary="添加MCP服务器")
async def add_mcp_server(request: McpServerAddRequest):
    """添加MCP服务器 - 与Electron端实现保持一致
    
    添加新的MCP服务器到系统中
    
    参数说明：
    - **name**: 服务器名称（必填）
    - **description**: 服务器描述（必填）
    - **type**: 服务器类型，支持stdio或sse（必填）
    - **command**: 启动命令（必填）
    - **baseUrl**: 基础URL，SSE类型时必填（可选）
    - **env**: 环境变量字典（可选）
    - **args**: 启动参数列表（可选）
    """
    try:
        # 获取MCP服务器列表 - 与Electron端get_mcp_servers保持一致
        servers = await mcp_service.get_mcp_servers()
        
        # 判断是否已存在 - 与Electron端find逻辑保持一致
        existing_server = next((s for s in servers if s.get('name') == request.name), None)
        if existing_server:
            return ResponseHandler.error("该服务器已存在")
        
        # 处理字符串类型的参数 - 与Electron端类型检查保持一致
        env_data = request.env
        if isinstance(env_data, str):
            try:
                env_data = json.loads(env_data)
            except json.JSONDecodeError:
                return ResponseHandler.error("环境变量格式错误")
        
        args_data = request.args
        if isinstance(args_data, str):
            try:
                args_data = json.loads(args_data)
            except json.JSONDecodeError:
                return ResponseHandler.error("参数格式错误")
        
        # 添加服务器 - 与Electron端服务器对象保持一致
        new_server = {
            'name': request.name,
            'description': request.description,
            'type': request.type,
            'command': request.command,
            'baseUrl': request.baseUrl,
            'env': env_data,
            'args': args_data,
            'isActive': True
        }
        
        servers.append(new_server)
        
        # 保存配置文件 - 与Electron端save_mcp_config保持一致
        success = await mcp_service.save_mcp_config(servers)
        
        # 返回成功响应 - 与Electron端pub.return_success保持一致
        if success:
            return ResponseHandler.success("添加成功")
        else:
            return ResponseHandler.error("添加失败")
    except Exception as e:
        return ResponseHandler.error(f"添加MCP服务器失败: {str(e)}")

@router.post("/modify_mcp_tools", summary="修改MCP服务器工具信息")
async def modify_mcp_tools(request: McpToolsModifyRequest):
    """修改MCP服务器工具信息 - 与Electron端实现保持一致
    
    修改指定MCP服务器的工具启用/禁用状态
    
    参数说明：
    - **name**: 服务器名称（必填）
    - **tools**: 工具状态字典，键为工具名，值为是否启用（必填）
    """
    try:
        # 统一调用 service 层，service 内部会同步更新 mcp-server.json 和 mcp_tools 缓存
        success = await mcp_service.modify_mcp_tools(request.name, request.tools)
        if success:
            return ResponseHandler.success("修改成功")
        else:
            return ResponseHandler.error("修改失败")
    except Exception as e:
        return ResponseHandler.error(f"修改MCP工具失败: {str(e)}")

@router.post("/get_mcp_tools", summary="获取MCP服务器工具信息")
async def get_mcp_tools(request: McpToolsRequest):
    """获取MCP服务器工具信息 - 与Electron端实现保持一致
    
    获取指定MCP服务器的所有工具信息
    
    参数说明：
    - **name**: 服务器名称（必填）
    """
    try:
        # 读取MCP配置 - 与Electron端read_mcp_config保持一致
        servers = await mcp_service.get_mcp_servers()
        
        # 查找指定服务器 - 与Electron端find逻辑保持一致
        server = next((s for s in servers if s.get('name') == request.name), None)
        if not server:
            return ResponseHandler.error("未找到该服务器")
        
        # 通过MCP协议真正获取工具列表 - 与Electron端getTools逻辑保持一致
        tools = await mcp_service.get_mcp_tools(request.name)

        # 返回成功响应 - 与Electron端pub.return_success保持一致
        return ResponseHandler.success("获取成功", tools)
    except Exception as e:
        return ResponseHandler.error(f"获取MCP工具失败: {str(e)}")

@router.post("/get_status", summary="检查环境状态")
async def get_status(request: McpStatusRequest):
    """检查环境状态 - 与Electron端实现保持一致
    
    检查MCP运行所需的Node.js、Python等环境状态
    """
    try:
        # 获取bun二进制文件路径 - 与Electron端get_bun_bin保持一致
        bun_file = mcp_service.get_bun_bin()
        
        # 检查bun文件是否存在 - 与Electron端file_exists逻辑保持一致
        is_bun = 1 if os.path.exists(bun_file) else 0
        
        # 如果未安装且正在安装中 - 与Electron端全局变量逻辑保持一致
        # TODO: 需要实现全局安装状态跟踪
        # if is_bun == 0 and global.bun_install:
        #     is_bun = 2
        
        # 获取uv二进制文件路径 - 与Electron端get_uv_bin保持一致
        uv_file = mcp_service.get_uv_bin()
        
        # 检查uv文件是否存在 - 与Electron端file_exists逻辑保持一致
        is_uv = 1 if os.path.exists(uv_file) else 0
        
        # 如果未安装且正在安装中 - 与Electron端全局变量逻辑保持一致
        # TODO: 需要实现全局安装状态跟踪
        # if is_uv == 0 and global.uv_install:
        #     is_uv = 2
        
        # 返回状态信息 - 与Electron端返回格式保持一致
        status = {
            "node_npx": is_bun,
            "python_uv": is_uv
        }
        
        return ResponseHandler.success("获取成功", status)
    except Exception as e:
        return ResponseHandler.error(f"获取状态失败: {str(e)}")

@router.post("/install_npx", summary="安装Node.js环境")
async def install_npx(request: InstallNpxRequest, background_tasks: BackgroundTasks):
    """安装Node.js环境 - 与Electron端实现保持一致
    
    在后台安装Node.js运行环境，用于支持基于Node.js的MCP服务器
    """
    try:
        # 在后台安装 - 与Electron端保持一致
        background_tasks.add_task(mcp_service.install_npx)
        return ResponseHandler.success("正在安装Node.js环境，请稍后...")
    except Exception as e:
        return ResponseHandler.error(f"安装Node.js环境失败: {str(e)}")

@router.post("/install_uv", summary="安装Python环境")
async def install_uv(request: InstallUvRequest):
    """安装Python环境 - 与Electron端实现保持一致
    
    安装MCP运行所需的Python环境
    """
    try:
        # 获取uv二进制文件路径 - 与Electron端get_uv_bin保持一致
        uv_file = mcp_service.get_uv_bin()
        
        # 检查是否已安装 - 与Electron端file_exists逻辑保持一致
        if os.path.exists(uv_file):
            return ResponseHandler.success("已安装")
        
        # TODO: 需要实现全局安装状态跟踪 - 与Electron端global.uvInstall保持一致
        # global.uv_install = True
        
        # 获取二进制文件路径和操作系统路径 - 与Electron端保持一致
        bin_path = mcp_service.get_bin_path()
        os_path = mcp_service.get_os_path()
        
        # 构建下载URL - 与Electron端保持一致
        download_url = f"https://aingdesk.bt.cn/bin/{os_path}/uv.zip"
        uvzip_file = os.path.join(bin_path, 'uv.zip')
        
        # 下载文件 - 与Electron端download_file保持一致
        await mcp_service.download_file(download_url, uvzip_file)
        
        # 解压缩 - 与Electron端unzip逻辑保持一致
        import zipfile
        with zipfile.ZipFile(uvzip_file, 'r') as zip_ref:
            zip_ref.extractall(bin_path)
        
        # 删除压缩包 - 与Electron端保持一致
        os.remove(uvzip_file)
        
        return ResponseHandler.success("安装成功")
    except Exception as e:
        return ResponseHandler.error(f"安装失败: {str(e)}")

@router.post("/get_mcp_config_body", summary="获取MCP配置文件内容")
async def get_mcp_config_body():
    """获取MCP配置文件内容 - 与Electron端实现保持一致
    
    获取MCP配置文件的完整内容
    """
    try:
        # 读取MCP配置 - 与Electron端read_mcp_config保持一致
        mcp_config = await mcp_service.read_mcp_config()
        
        # 检查配置是否存在 - 与Electron端逻辑保持一致
        if mcp_config and mcp_config.get('mcpServers'):
            # 返回格式化的配置内容 - 与Electron端返回格式保持一致
            return ResponseHandler.success("获取成功", {
                "mcp_config_body": json.dumps(mcp_config, indent=4, ensure_ascii=False)
            })
        else:
            return ResponseHandler.error("未找到MCP配置")
    except Exception as e:
        return ResponseHandler.error(f"获取配置失败: {str(e)}")

@router.post("/save_mcp_config_body", summary="保存MCP配置文件内容")
async def save_mcp_config_body(request: McpConfigBodyRequest):
    """保存MCP配置文件内容 - 与Electron端实现保持一致
    
    保存MCP配置文件的完整内容
    """
    try:
        # 读取当前MCP配置 - 与Electron端read_mcp_config保持一致
        mcp_config = await mcp_service.read_mcp_config()
        
        # 检查配置是否存在 - 与Electron端逻辑保持一致
        if mcp_config and mcp_config.get('mcpServers'):
            try:
                # 解析新的配置内容 - 与Electron端JSON.parse保持一致
                new_mcp_config = json.loads(request.mcp_config_body)
                
                # 验证配置格式 - 与Electron端验证逻辑保持一致
                if not new_mcp_config.get('mcpServers'):
                    return ResponseHandler.error("配置文件格式错误")
                
                # 获取服务器列表并保存 - 与Electron端save_mcp_config保持一致
                mcp_servers = new_mcp_config['mcpServers']
                await mcp_service.save_mcp_config(mcp_servers)
                
                return ResponseHandler.success("保存成功")
            except json.JSONDecodeError as e:
                return ResponseHandler.error("配置文件格式错误")
        else:
            return ResponseHandler.error("未找到MCP配置")
    except Exception as e:
        return ResponseHandler.error(f"保存配置失败: {str(e)}")

@router.post("/get_registry_list", summary="获取pypi和npm的源列表")
async def get_registry_list(request: RegistryListRequest):
    """获取pypi和npm的源列表 - 与Electron端实现保持一致
    
    获取Python和Node.js的包管理器源列表
    """
    try:
        # 定义默认源列表 - 与Electron端defaultList保持一致
        default_list = {
            "pypi": [
                {
                    "name": "pypi",
                    "url": "https://pypi.python.org/simple",
                    "description": "Python官方源"
                },
                {
                    "name": "清华大学源",
                    "url": "https://pypi.tuna.tsinghua.edu.cn/simple",
                    "description": "清华大学源，适合中国用户"
                }
            ],
            "npm": [
                {
                    "name": "npm",
                    "url": "https://registry.npmjs.org",
                    "description": "npm官方源"
                },
                {
                    "name": "淘宝源",
                    "url": "https://registry.npmmirror.com",
                    "description": "淘宝源，适合中国用户"
                }
            ]
        }
        
        # 获取资源路径 - 与Electron端get_resource_path保持一致
        resource_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'public', 'dist', 'index_list.json')
        
        # 检查文件是否存在 - 与Electron端file_exists逻辑保持一致
        if os.path.exists(resource_path):
            # 读取自定义源列表 - 与Electron端read_json保持一致
            with open(resource_path, 'r', encoding='utf-8') as f:
                default_list = json.load(f)
        
        return ResponseHandler.success("获取成功", default_list)
    except Exception as e:
        return ResponseHandler.error(f"获取源列表失败: {str(e)}")

@router.post("/sync_cloud_mcp", summary="同步云端的MCP配置文件")
async def sync_cloud_mcp(request: SyncCloudMcpRequest):
    """同步云端的MCP配置文件
    
    从云端同步MCP配置文件，保持配置最新
    """
    try:
        result = await mcp_service.sync_cloud_mcp()
        return ResponseHandler.success("同步成功", result)
    except Exception as e:
        return ResponseHandler.error(f"同步云端MCP配置失败: {str(e)}")

# 额外的辅助API

@router.get("/environment_check", summary="检查所有环境依赖")
async def environment_check():
    """检查所有环境依赖
    
    检查系统中所有MCP运行所需的环境依赖状态
    """
    try:
        env_status = {
            "python": await mcp_service.check_python(),
            "node": await mcp_service.check_node(),
            "npm": await mcp_service.check_npm(),
            "uv": await mcp_service.check_uv_exists(),
            "bun": await mcp_service.check_bun_exists()
        }
        return ResponseHandler.success("检查完成", env_status)
    except Exception as e:
        return ResponseHandler.error(f"环境检查失败: {str(e)}")

@router.get("/supported_protocols", summary="获取支持的MCP协议类型")
async def get_supported_protocols():
    """获取支持的MCP协议类型
    
    获取系统支持的MCP协议类型列表
    """
    try:
        protocols = ["stdio", "sse"]
        return ResponseHandler.success("获取成功", protocols)
    except Exception as e:
        return ResponseHandler.error(f"获取协议类型失败: {str(e)}")