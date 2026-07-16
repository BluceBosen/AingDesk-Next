from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os
import json
import random
import string
import time
from pathlib import Path
from app.models.response import ResponseHandler

# 暂时注释掉对AgentService的导入
# from app.services.agent_service import AgentService

# 尝试导入settings，如果失败则创建一个简单的替代品
try:
    from app.core.config import settings
    DATA_DIR = settings.DATA_DIR
    Agent_Path = os.path.join(DATA_DIR, "agent")
    System_Agent_Path = os.path.join(Agent_Path, "system")
    os.makedirs(Agent_Path, exist_ok=True)
    os.makedirs(System_Agent_Path, exist_ok=True)
except ImportError:
    print("Warning: Could not import settings from app.core.config. Using fallback.")
    # 创建一个简单的替代路径
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data")
    os.makedirs(DATA_DIR, exist_ok=True)

router = APIRouter(tags=["agent"])
# 暂时注释掉对AgentService的实例化
# agent_service = AgentService()

# 请求模型
class AgentCreateRequest(BaseModel):
    agent_type: Optional[str] = Field(None, description="智能体类型，如default、assistant等")
    agent_name: Optional[str] = Field(None, description="智能体名称，如不提供则自动生成")
    agent_title: str = Field(..., description="智能体标题")
    description: Optional[str] = Field(None, description="智能体描述")
    prompt: str = Field(..., description="智能体提示词")
    icon: Optional[str] = Field(None, description="智能体图标，base64编码")
    rag_ids: Optional[List[str]] = Field(None, description="关联的知识库ID列表")
    mcp_tool: Optional[List[str]] = Field(None, description="关联的MCP工具列表")

class AgentListRequest(BaseModel):
    agent_type: Optional[str] = Field(None, description="智能体类型，如不提供则返回所有类型")
    agent_title: Optional[str] = Field(None, description="智能体标题关键词，用于模糊搜索")

class AgentModifyRequest(BaseModel):
    agent_type: Optional[str] = Field(None, description="智能体类型")
    agent_name: str = Field(..., description="智能体名称")
    agent_title: str = Field(..., description="智能体标题")
    description: Optional[str] = Field(None, description="智能体描述")
    prompt: str = Field(..., description="智能体提示词")
    icon: Optional[str] = Field(None, description="智能体图标，base64编码")
    is_collect: Optional[bool] = Field(None, description="是否收藏")
    rag_ids: Optional[List[str]] = Field(None, description="关联的知识库ID列表")
    mcp_tool: Optional[List[str]] = Field(None, description="关联的MCP工具列表")

class AgentCollectRequest(BaseModel):
    agent_name: str = Field(..., description="智能体名称")
    is_collect: bool = Field(..., description="是否收藏")

class AgentRemoveRequest(BaseModel):
    agent_name: str = Field(..., description="智能体名称")

class AgentInfoRequest(BaseModel):
    agent_name: str = Field(..., description="智能体名称")



# 随机字符串生成
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# 读取智能体配置
def read_agent_config(agent_name: str):
    agent_config_file = os.path.join(Agent_Path, agent_name + ".json")
    if os.path.exists(agent_config_file):
        try:
            with open(agent_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取智能体配置文件失败: {str(e)}")
            return None

    system_agent_config_file = os.path.join(System_Agent_Path, agent_name + ".json")
    if os.path.exists(system_agent_config_file):
        try:
            with open(system_agent_config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取智能体配置文件失败: {str(e)}")
            return None

    return None

# 写入智能体配置
def write_agent_config(agent_name: str, config: dict):
    agent_config_file = os.path.join(Agent_Path, agent_name + ".json")
    with open(agent_config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

@router.post("/create_agent", summary="创建智能体")
async def create_agent(request: AgentCreateRequest):
    """创建新的智能体
    
    创建新的AI智能体，支持自定义名称、提示词和图标
    
    参数说明：
    - **agent_type**: 智能体类型，如不提供则使用"default" 
    - **agent_name**: 智能体名称，如不提供则自动生成随机名称
    - **agent_title**: 智能体标题（必填）
    - **prompt**: 智能体提示词（必填）
    - **icon**: 智能体图标，base64编码（可选）
    """
    try:
        agent_name = request.agent_name
        
        # 如果没有指定名称，生成随机名称
        if not agent_name:
            while True:
                agent_name = random_string(8)
                agent_config_file = os.path.join(Agent_Path, agent_name + ".json")
                if not os.path.exists(agent_config_file):
                    break
        
        # 设置默认值
        agent_type = request.agent_type or "default"
        icon = request.icon or ""
        
        # 创建配置
        agent_config = {
            "agent_name": agent_name,
            "agent_title": request.agent_title,
            "description": request.description or "",
            "prompt": request.prompt,
            "agent_type": agent_type,
            "icon": icon,
            "rag_ids": request.rag_ids or [],
            "mcp_tool": request.mcp_tool or [],
            "create_time": int(time.time()),
            "is_system": False,
            "is_collect": False
        }
        
        # 保存配置
        write_agent_config(agent_name, agent_config)
        
        return ResponseHandler.success("创建成功")
    except Exception as e:
        return ResponseHandler.error(f"创建智能体失败: {str(e)}")

@router.post("/get_agent_list", summary="获取智能体列表")
async def get_agent_list(request: AgentListRequest = None):
    """获取所有可用的智能体列表
    
    获取所有智能体列表，支持按类型过滤
    
    参数说明：
    - **agent_type**: 智能体类型，可选，用于过滤特定类型的智能体
    """
    try:
        agent_list = []
        
        # 获取系统智能体列表
        system_agent_path = System_Agent_Path
        if os.path.exists(system_agent_path):
            for agent_file in os.listdir(system_agent_path):
                if agent_file.endswith('.json'):
                    agent_name = os.path.splitext(agent_file)[0]
                    agent_config = read_agent_config(agent_name)
                    if agent_config:
                        agent_list.append(agent_config)
        
        # 获取用户智能体列表
        user_agent_path = Agent_Path
        if os.path.exists(user_agent_path):
            for agent_file in os.listdir(user_agent_path):
                if agent_file.endswith('.json'):
                    agent_name = os.path.splitext(agent_file)[0]
                    agent_config = read_agent_config(agent_name)
                    if agent_config:
                        agent_list.append(agent_config)
        
        # 根据创建时间排序
        agent_list.sort(key=lambda x: x.get('create_time', 0), reverse=True)
        
        # 如果指定了类型，进行过滤
        if request and request.agent_type:
            agent_list = [agent for agent in agent_list if agent.get('agent_type') == request.agent_type]
        
        # 如果指定了标题关键词，进行模糊过滤
        if request and request.agent_title:
            keyword = request.agent_title
            agent_list = [agent for agent in agent_list if keyword in agent.get('agent_title', '')]
        
        return ResponseHandler.success("获取成功", agent_list)
    except Exception as e:
        return ResponseHandler.error(f"获取智能体列表失败: {str(e)}")

@router.post("/modify_agent", summary="修改智能体")
async def modify_agent(request: AgentModifyRequest):
    """修改现有智能体的配置信息
    
    修改现有智能体的标题、提示词、类型和图标信息
    
    参数说明：
    - **agent_name**: 智能体名称（必填）
    - **agent_title**: 智能体标题（可选）
    - **prompt**: 智能体提示词（可选）
    - **agent_type**: 智能体类型（可选）
    - **icon**: 智能体图标，base64编码（可选）
    """
    try:
        # 参数校验
        if not request.agent_name or not request.agent_name.strip():
            return ResponseHandler.error("智能体名称不能为空")
        if not request.agent_title or not request.agent_title.strip():
            return ResponseHandler.error("智能体标题不能为空")
        if not request.prompt or not request.prompt.strip():
            return ResponseHandler.error("智能体提示不能为空")
        
        # 读取现有配置
        agent_config = read_agent_config(request.agent_name)
        if not agent_config:
            return ResponseHandler.error("智能体不存在", None, 404)
        
        # 检查是否是系统智能体
        if agent_config.get('is_system', False):
            return ResponseHandler.error("系统智能体不可修改", None, 403)
        
        # 更新配置
        if request.agent_type:
            agent_config['agent_type'] = request.agent_type
        agent_config['agent_title'] = request.agent_title
        if request.description is not None:
            agent_config['description'] = request.description
        agent_config['prompt'] = request.prompt
        if request.icon:
            agent_config['icon'] = request.icon
        if request.is_collect is not None:
            agent_config['is_collect'] = request.is_collect
        if request.rag_ids is not None:
            agent_config['rag_ids'] = request.rag_ids
        if request.mcp_tool is not None:
            agent_config['mcp_tool'] = request.mcp_tool
        
        # 保存配置
        write_agent_config(request.agent_name, agent_config)
        
        return ResponseHandler.success("修改成功")
    except Exception as e:
        return ResponseHandler.error(f"修改智能体失败: {str(e)}")

@router.post("/remove_agent", summary="删除智能体")
async def remove_agent(request: AgentRemoveRequest):
    """删除指定的智能体
    
    删除指定的智能体，系统智能体不可删除
    
    参数说明：
    - **agent_name**: 要删除的智能体名称
    """
    try:
        # 参数校验
        if not request.agent_name or not request.agent_name.strip():
            return ResponseHandler.error("智能体名称不能为空")
        # 读取配置
        agent_config = read_agent_config(request.agent_name)
        if not agent_config:
            return ResponseHandler.error("智能体不存在", None, 404)
        
        # 检查是否是系统智能体
        if agent_config.get('is_system', False):
            return ResponseHandler.error("系统智能体不可删除", None, 403)
        
        # 删除配置文件
        agent_config_file = os.path.join(Agent_Path, request.agent_name + ".json")
        if os.path.exists(agent_config_file):
            os.remove(agent_config_file)
        
        return ResponseHandler.success("删除成功")
    except Exception as e:
        return ResponseHandler.error(f"删除智能体失败: {str(e)}")

@router.post("/get_agent_info", summary="获取智能体详情")
async def get_agent_info(request: AgentInfoRequest):
    """获取指定智能体的详细信息
    
    获取指定智能体的详细信息，包括配置和元数据
    
    参数说明：
    - **agent_name**: 智能体名称
    """
    try:
        agent_config = read_agent_config(request.agent_name)
        if not agent_config:
            return ResponseHandler.error("智能体不存在", None, 404)
        
        return ResponseHandler.success("获取成功", agent_config)
    except Exception as e:
        return ResponseHandler.error(f"获取智能体信息失败: {str(e)}")

# 以下是额外的API，用于扩展功能

@router.get("/agent_type_list", summary="获取智能体类型")
async def get_agent_types():
    """获取所有智能体类型
    
    获取系统中所有可用的智能体类型列表，包括系统智能体和用户自定义智能体的类型
    """
    try:
        agent_types = set()
        agent_types.add("全部助手")
        agent_types.add("精选推荐")
        agent_types.add("我的收藏")
        agent_types.add("生活答疑")
        agent_types.add("数据分析")
        agent_types.add("日常办公")
        
        # 获取系统智能体类型
        system_agent_path = System_Agent_Path
        if os.path.exists(system_agent_path):
            for agent_file in os.listdir(system_agent_path):
                if agent_file.endswith('.json'):
                    agent_name = os.path.splitext(agent_file)[0]
                    agent_config = read_agent_config(agent_name)
                    if agent_config and 'agent_type' in agent_config:
                        agent_types.add(agent_config['agent_type'])
        
        # 获取用户智能体类型
        user_agent_path = Agent_Path
        if os.path.exists(user_agent_path):
            for agent_file in os.listdir(user_agent_path):
                if agent_file.endswith('.json'):
                    agent_name = os.path.splitext(agent_file)[0]
                    agent_config = read_agent_config(agent_name)
                    if agent_config and 'agent_type' in agent_config:
                        agent_types.add(agent_config['agent_type'])
        
        return ResponseHandler.success("获取成功", list(agent_types))
    except Exception as e:
        return ResponseHandler.error(f"获取智能体类型失败: {str(e)}")

@router.post("/collect_agent", summary="收藏/取消收藏智能体")
async def collect_agent(request: AgentCollectRequest):
    """收藏或取消收藏智能体

    修改智能体的收藏状态，系统智能体也支持收藏
    """
    try:
        # 参数校验
        if not request.agent_name or not request.agent_name.strip():
            return ResponseHandler.error("智能体名称不能为空")
        agent_config = read_agent_config(request.agent_name)
        if not agent_config:
            return ResponseHandler.error("智能体不存在", None, 404)

        agent_config['is_collect'] = request.is_collect
        write_agent_config(request.agent_name, agent_config)

        return ResponseHandler.success("修改是否收藏成功")
    except Exception as e:
        return ResponseHandler.error(f"修改收藏状态失败: {str(e)}")

@router.post("/get_collect_agent_list", summary="获取收藏智能体列表")
async def get_collect_agent_list(request: AgentListRequest = None):
    """获取收藏的智能体列表

    获取所有 is_collect 为 true 的智能体，支持按标题关键词过滤
    """
    try:
        agent_list = []
        keyword = (request.agent_title or "") if request else ""

        # 遍历系统智能体
        system_agent_path = System_Agent_Path
        if os.path.exists(system_agent_path):
            for agent_file in os.listdir(system_agent_path):
                if agent_file.endswith('.json'):
                    agent_name = os.path.splitext(agent_file)[0]
                    agent_config = read_agent_config(agent_name)
                    if agent_config and agent_config.get('is_collect', False):
                        if not keyword or keyword in agent_config.get('agent_title', ''):
                            agent_list.append(agent_config)

        # 遍历用户智能体
        user_agent_path = Agent_Path
        if os.path.exists(user_agent_path):
            for agent_file in os.listdir(user_agent_path):
                if agent_file.endswith('.json'):
                    agent_name = os.path.splitext(agent_file)[0]
                    agent_config = read_agent_config(agent_name)
                    if agent_config and agent_config.get('is_collect', False):
                        if not keyword or keyword in agent_config.get('agent_title', ''):
                            agent_list.append(agent_config)

        # 按创建时间降序排序
        agent_list.sort(key=lambda x: x.get('create_time', 0), reverse=True)

        return ResponseHandler.success("获取成功", agent_list)
    except Exception as e:
        return ResponseHandler.error(f"获取收藏智能体列表失败: {str(e)}")

@router.post("/get_system_agent_list", summary="获取系统智能体列表")
async def get_system_agent_list(request: AgentListRequest = None):
    """获取系统（内置）智能体列表

    只返回 system 目录下的智能体，支持按标题关键词过滤
    """
    try:
        agent_list = []
        keyword = (request.agent_title or "") if request else ""

        system_agent_path = System_Agent_Path
        if os.path.exists(system_agent_path):
            for agent_file in os.listdir(system_agent_path):
                if agent_file.endswith('.json'):
                    agent_name = os.path.splitext(agent_file)[0]
                    agent_config = read_agent_config(agent_name)
                    if agent_config:
                        if not keyword or keyword in agent_config.get('agent_title', ''):
                            agent_list.append(agent_config)

        # 按创建时间降序排序
        agent_list.sort(key=lambda x: x.get('create_time', 0), reverse=True)

        return ResponseHandler.success("获取成功", agent_list)
    except Exception as e:
        return ResponseHandler.error(f"获取系统智能体列表失败: {str(e)}")