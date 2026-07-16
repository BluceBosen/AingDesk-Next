from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import os
import json
import shutil
from pathlib import Path

from app.services.model_service import ModelService
from app.core.config import settings
from app.models.response import ResponseHandler

router = APIRouter(tags=["model"])
model_service = ModelService()

# 定义请求模型
class SupplierConfigRequest(BaseModel):
    supplierName: str
    baseUrl: Optional[str] = None
    apiKey: Optional[str] = None

class SupplierNameRequest(BaseModel):
    supplierName: str

class SupplierStatusRequest(BaseModel):
    supplierName: str
    status: str

class ModelStatusRequest(BaseModel):
    supplierName: str
    modelName: str
    status: str

class ModelRequest(BaseModel):
    title: str
    supplierName: str
    modelName: str
    capability: Any

class ModelRemoveRequest(BaseModel):
    supplierName: str
    modelName: str

class SupplierRequest(BaseModel):
    supplierName: str
    supplierTitle: str
    baseUrl: Optional[str] = None
    apiKey: Optional[str] = None

class ModelTitleRequest(BaseModel):
    supplierName: str
    modelName: str
    title: str

class ModelCapabilityRequest(BaseModel):
    supplierName: str
    modelName: str
    capability: Any

class ModelModifyRequest(BaseModel):
    supplierName: str
    modelName: str
    capability: Any
    title: str

# 模型服务的基础路径
MODELS_PATH = os.path.join(settings.DATA_DIR, "models")



# 确保模型目录存在
os.makedirs(MODELS_PATH, exist_ok=True)

# 帮助函数
def get_supplier_path(supplier_name: str) -> str:
    return os.path.join(MODELS_PATH, supplier_name)

def get_supplier_config_path(supplier_name: str) -> str:
    return os.path.join(get_supplier_path(supplier_name), "config.json")

def get_models_file_path(supplier_name: str) -> str:
    return os.path.join(get_supplier_path(supplier_name), "models.json")

def get_embedding_file_path(supplier_name: str) -> str:
    return os.path.join(get_supplier_path(supplier_name), "embedding.json")

async def read_json_file(file_path: str) -> Any:
    try:
        if not os.path.exists(file_path):
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"读取文件 {file_path} 失败: {str(e)}")

async def write_json_file(file_path: str, data: Any) -> None:
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        raise Exception(f"写入文件 {file_path} 失败: {str(e)}")

@router.post("/get_supplier_list", summary="获取模型供应商列表")
async def get_supplier_list():
    """获取模型供应商列表
    
    获取所有可用的模型供应商列表，包含供应商的配置信息
    """
    try:
        # 同步模型供应商模板
        await model_service.sync_supplier_template()
        
        # 获取所有供应商
        suppliers = []
        if os.path.exists(MODELS_PATH):
            for supplier in os.listdir(MODELS_PATH):
                config_file = get_supplier_config_path(supplier)
                if os.path.exists(config_file):
                    try:
                        supplier_info = await read_json_file(config_file)
                        if supplier_info:
                            suppliers.append(supplier_info)
                    except Exception as e:
                        continue
        
        # 根据sort字段排序
        suppliers.sort(key=lambda x: x.get('sort', 0))
        
        return ResponseHandler.success("获取成功", suppliers)
    except Exception as e:
        return ResponseHandler.error(f"获取供应商列表失败: {str(e)}")

@router.post("/get_models_list", summary="获取指定供应商的模型列表")
async def get_models_list(request: SupplierNameRequest):
    """获取指定供应商的模型列表
    
    获取指定供应商的所有可用模型列表，包括常规模型和嵌入模型
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    """
    try:
        # 同步模型供应商模板
        await model_service.sync_supplier_template()
        
        supplier_name = request.supplierName
        config_file = get_supplier_config_path(supplier_name)
        models_file = get_models_file_path(supplier_name)
        
        # 检查供应商是否存在
        if not os.path.exists(config_file):
            return ResponseHandler.error("模型供应商不存在", None, 404)
        
        # 读取供应商信息
        supplier_info = await read_json_file(config_file)
        
        # 读取模型列表
        models = []
        if os.path.exists(models_file):
            models = await read_json_file(models_file) or []
            # 为每个模型设置默认标题
            for model in models:
                if not model.get("title"):
                    model["title"] = f"{supplier_info.get('supplierTitle', supplier_name)}/{model.get('modelName', '')}"
        
        # 读取嵌入模型
        embedding_file = get_embedding_file_path(supplier_name)
        if os.path.exists(embedding_file):
            embedding_models = await read_json_file(embedding_file) or []
            for embedding_model in embedding_models:
                # 检查是否已存在
                existing = any(m.get("modelName") == embedding_model.get("modelName") for m in models)
                if not existing:
                    if not embedding_model.get("title"):
                        embedding_model["title"] = f"{supplier_info.get('supplierTitle', supplier_name)}/{embedding_model.get('modelName', '')}"
                    models.append(embedding_model)
        
        return ResponseHandler.success("获取成功", models)
    except Exception as e:
        return ResponseHandler.error(f"获取模型列表失败: {str(e)}")

@router.post("/add_models", summary="添加模型")
async def add_models(request: ModelRequest):
    """添加模型
    
    向指定供应商添加新的模型配置
    
    参数说明：
    - **title**: 模型标题（必填）
    - **supplierName**: 供应商名称（必填）
    - **modelName**: 模型名称（必填）
    - **capability**: 模型能力列表（必填）
    """
    try:
        # 解析能力信息
        try:
            if isinstance(request.capability, str):
                capability = json.loads(request.capability)
            else:
                capability = request.capability
        except (json.JSONDecodeError, ValueError):
            return ResponseHandler.error("模型能力格式错误", None, 400)
        
        # 创建模型对象
        new_model = {
            "title": request.title,
            "supplierName": request.supplierName,
            "modelName": request.modelName,
            "capability": capability,
            "status": True
        }
        
        # 判断是否为嵌入模型
        is_embedding = any(c == "embedding" for c in capability)
        
        if is_embedding:
            models_file = get_embedding_file_path(request.supplierName)
        else:
            models_file = get_models_file_path(request.supplierName)
        
        # 检查供应商目录是否存在
        supplier_path = get_supplier_path(request.supplierName)
        if not os.path.exists(supplier_path):
            return ResponseHandler.error("模型供应商不存在", None, 404)
        
        # 检查模型文件是否存在，不存在则创建
        if not os.path.exists(models_file):
            await write_json_file(models_file, [])
        
        # 读取现有模型列表
        models = await read_json_file(models_file) or []
        
        # 检查模型是否已存在
        for model in models:
            if model.get("modelName") == request.modelName:
                return ResponseHandler.error("模型已存在", None, 409)
        
        # 添加新模型
        models.append(new_model)
        
        # 保存模型列表
        await write_json_file(models_file, models)
        
        return ResponseHandler.success("添加成功", new_model)
    except Exception as e:
        return ResponseHandler.error(f"添加模型失败: {str(e)}")

@router.post("/remove_models", summary="删除模型")
async def remove_models(request: ModelRemoveRequest):
    """删除模型
    
    删除指定供应商中的指定模型
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **modelName**: 要删除的模型名称（必填）
    """
    try:
        models_file = get_models_file_path(request.supplierName)
        
        # 读取现有模型列表
        if not os.path.exists(models_file):
            return ResponseHandler.error("模型文件不存在", None, 404)
        
        models = await read_json_file(models_file) or []
        
        # 找到并删除指定模型
        new_models = [model for model in models if model.get("modelName") != request.modelName]
        
        if len(new_models) == len(models):
            return ResponseHandler.error("模型不存在", None, 404)
        
        # 保存更新后的模型列表
        await write_json_file(models_file, new_models)
        
        return ResponseHandler.success("删除成功")
    except Exception as e:
        return ResponseHandler.error(f"删除模型失败: {str(e)}")

@router.post("/set_supplier_config", summary="设置供应商配置")
async def set_supplier_config(request: SupplierConfigRequest):
    """设置供应商配置
    
    设置或更新指定供应商的配置信息，包括基础URL和API密钥
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **baseUrl**: 基础URL（可选）
    - **apiKey**: API密钥（可选）
    """
    try:
        if not request.supplierName or not request.supplierName.strip():
            return ResponseHandler.error("供应商名称不能为空", None, 400)
        
        config_file = get_supplier_config_path(request.supplierName)
        
        # 读取现有配置
        if not os.path.exists(config_file):
            return ResponseHandler.error("供应商配置文件不存在", None, 404)
        
        config = await read_json_file(config_file)
        
        # 更新配置
        if request.baseUrl is not None:
            config["baseUrl"] = request.baseUrl
        if request.apiKey is not None:
            config["apiKey"] = request.apiKey
        
        # 保存配置
        await write_json_file(config_file, config)
        
        # 尝试获取在线模型列表
        try:
            await model_service.get_online_models(request.supplierName, request.baseUrl, request.apiKey)
        except Exception as e:
            pass
        
        return ResponseHandler.success("设置成功", config)
    except Exception as e:
        return ResponseHandler.error(f"设置供应商配置失败: {str(e)}")

@router.post("/check_supplier_config", summary="检查供应商配置")
async def check_supplier_config(request: SupplierConfigRequest):
    """检查供应商配置
    
    验证指定供应商的配置是否有效，包括API密钥和网络连接测试
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **baseUrl**: 基础URL（可选）
    - **apiKey**: API密钥（可选）
    """
    try:
        if not request.supplierName or not request.supplierName.strip():
            return ResponseHandler.error("供应商名称不能为空", None, 400)
        
        is_valid = await model_service.check_supplier_config(
            request.supplierName, 
            request.baseUrl, 
            request.apiKey
        )
        if is_valid:
            return ResponseHandler.success("配置有效")
        else:
            return ResponseHandler.error("配置无效", None, 400)
    except Exception as e:
        return ResponseHandler.error(f"连接失败，请检查配置: {str(e)}")

@router.post("/get_supplier_config", summary="获取供应商配置")
async def get_supplier_config(request: SupplierConfigRequest):
    """获取供应商配置
    
    获取指定供应商的完整配置信息
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **baseUrl**: 基础URL（可选）
    - **apiKey**: API密钥（可选）
    """
    try:
        config_file = get_supplier_config_path(request.supplierName)
        if not os.path.exists(config_file):
            return ResponseHandler.error("供应商配置文件不存在", None, 404)
            
        config = await read_json_file(config_file)
        return ResponseHandler.success("获取成功", config)
    except Exception as e:
        return ResponseHandler.error(f"获取供应商配置失败: {str(e)}")

@router.post("/set_supplier_status", summary="设置供应商状态")
async def set_supplier_status(request: SupplierStatusRequest):
    """设置供应商状态
    
    设置指定供应商的启用/禁用状态
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **status**: 状态值，"true"表示启用，"false"表示禁用（必填）
    """
    try:
        config_file = get_supplier_config_path(request.supplierName)
        if not os.path.exists(config_file):
            return ResponseHandler.error("供应商配置文件不存在", None, 404)
            
        config = await read_json_file(config_file)
        status_bool = request.status.lower() == 'true'
        config["status"] = status_bool
        await write_json_file(config_file, config)
        
        return ResponseHandler.success("设置成功")
    except Exception as e:
        return ResponseHandler.error(f"设置供应商状态失败: {str(e)}")

@router.post("/set_model_status", summary="设置模型状态")
async def set_model_status(request: ModelStatusRequest):
    """设置模型状态
    
    设置指定供应商中一个或多个模型的启用/禁用状态
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **modelName**: 模型名称，支持多个模型用逗号分隔（必填）
    - **status**: 状态值，"true"表示启用，"false"表示禁用（必填）
    """
    try:
        models_file = get_models_file_path(request.supplierName)
        if not os.path.exists(models_file):
            return ResponseHandler.error("模型文件不存在", None, 404)
            
        # 支持多个模型名称，用逗号分隔
        model_names = request.modelName.split(",")
        status_bool = request.status.lower() == 'true'
        
        # 修改普通模型状态
        models = await read_json_file(models_file) or []
        for model in models:
            if model.get("modelName") in model_names:
                model["status"] = status_bool
        
        await write_json_file(models_file, models)
        
        # 修改嵌入模型状态
        embedding_file = get_embedding_file_path(request.supplierName)
        if os.path.exists(embedding_file):
            embedding_models = await read_json_file(embedding_file) or []
            for embedding_model in embedding_models:
                if embedding_model.get("modelName") in model_names:
                    embedding_model["status"] = status_bool
            await write_json_file(embedding_file, embedding_models)
        
        return ResponseHandler.success("设置成功")
    except Exception as e:
        return ResponseHandler.error(f"设置模型状态失败: {str(e)}")

@router.post("/add_supplier", summary="添加供应商")
async def add_supplier(request: SupplierRequest):
    """添加供应商
    
    添加新的模型供应商配置
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **supplierTitle**: 供应商显示标题（必填）
    - **baseUrl**: 基础URL（可选）
    - **apiKey**: API密钥（可选）
    """
    try:
        supplier_path = get_supplier_path(request.supplierName)
        if os.path.exists(supplier_path):
            return ResponseHandler.error("供应商已存在", None, 409)
            
        os.makedirs(supplier_path, exist_ok=True)
        config_file = get_supplier_config_path(request.supplierName)
        
        config_data = {
            "supplierName": request.supplierName,
            "supplierTitle": request.supplierTitle,
            "baseUrl": request.baseUrl or "",
            "apiKey": request.apiKey or "",
            "status": True,
            "sort": 999 # Default sort order
        }
        await write_json_file(config_file, config_data)
        
        # Create an empty models.json for the new supplier
        await write_json_file(get_models_file_path(request.supplierName), [])
        
        return ResponseHandler.success("添加成功", config_data)
    except Exception as e:
        return ResponseHandler.error(f"添加供应商失败: {str(e)}")

@router.post("/remove_supplier", summary="删除供应商")
async def remove_supplier(request: SupplierConfigRequest):
    """删除供应商
    
    删除指定的供应商及其所有相关配置和模型数据
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **baseUrl**: 基础URL（可选）
    - **apiKey**: API密钥（可选）
    """
    try:
        supplier_path = get_supplier_path(request.supplierName)
        if not os.path.exists(supplier_path):
            return ResponseHandler.error("供应商不存在", None, 404)
            
        shutil.rmtree(supplier_path)
        return ResponseHandler.success("删除成功")
    except Exception as e:
        return ResponseHandler.error(f"删除供应商失败: {str(e)}")

@router.post("/get_online_models", summary="获取在线模型列表")
async def get_online_models(request: SupplierNameRequest):
    """获取在线模型列表
    
    从指定供应商的在线API获取最新的模型列表
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    """
    try:
        # 首先同步供应商模板，确保配置存在
        await model_service.sync_supplier_template()
        
        # 获取供应商配置
        config_file = get_supplier_config_path(request.supplierName)
        if not os.path.exists(config_file):
            return ResponseHandler.error("供应商配置文件不存在", None, 404)
            
        config = await read_json_file(config_file)
        base_url = config.get("baseUrl", "")
        api_key = config.get("apiKey", "")
        
        # 获取在线模型列表
        models = await model_service.get_online_models(request.supplierName, base_url, api_key)
        return ResponseHandler.success("获取成功", models)
    except Exception as e:
        return ResponseHandler.error(f"获取在线模型失败: {str(e)}")

@router.post("/set_model_title", summary="设置模型标题")
async def set_model_title(request: ModelTitleRequest):
    """设置模型标题
    
    修改指定供应商中指定模型的显示标题
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **modelName**: 模型名称（必填）
    - **title**: 新的模型标题（必填）
    """
    try:
        models_file = get_models_file_path(request.supplierName)
        if not os.path.exists(models_file):
            return ResponseHandler.error("模型文件不存在", None, 404)
            
        models = await read_json_file(models_file) or []
        found = False
        for model in models:
            if model.get("modelName") == request.modelName:
                model["title"] = request.title
                found = True
                break
        
        if not found:
            return ResponseHandler.error("模型不存在", None, 404)
            
        await write_json_file(models_file, models)
        return ResponseHandler.success("设置成功")
    except Exception as e:
        return ResponseHandler.error(f"设置模型标题失败: {str(e)}")

@router.post("/set_model_capability", summary="设置模型能力")
async def set_model_capability(request: ModelCapabilityRequest):
    """设置模型能力
    
    设置或更新指定供应商中指定模型的能力配置
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **modelName**: 模型名称（必填）
    - **capability**: 模型能力配置（必填）
    """
    try:
        models_file = get_models_file_path(request.supplierName)
        if not os.path.exists(models_file):
            return ResponseHandler.error("模型文件不存在", None, 404)
            
        models = await read_json_file(models_file) or []
        found = False
        for model in models:
            if model.get("modelName") == request.modelName:
                model["capability"] = request.capability
                found = True
                break
        
        if not found:
            return ResponseHandler.error("模型不存在", None, 404)
            
        await write_json_file(models_file, models)
        return ResponseHandler.success("设置成功")
    except Exception as e:
        return ResponseHandler.error(f"设置模型能力失败: {str(e)}")

@router.post("/modify_model", summary="修改模型信息")
async def modify_model(request: ModelModifyRequest):
    """修改模型信息
    
    修改指定供应商中指定模型的完整信息，包括标题和能力配置
    
    参数说明：
    - **supplierName**: 供应商名称（必填）
    - **modelName**: 模型名称（必填）
    - **capability**: 模型能力配置（必填）
    - **title**: 模型标题（必填）
    """
    try:
        models_file = get_models_file_path(request.supplierName)
        if not os.path.exists(models_file):
            return ResponseHandler.error("模型文件不存在", None, 404)
            
        models = await read_json_file(models_file) or []
        found = False
        for model in models:
            if model.get("modelName") == request.modelName:
                model["title"] = request.title
                model["capability"] = request.capability
                found = True
                break
        
        if not found:
            return ResponseHandler.error("模型不存在", None, 404)
            
        await write_json_file(models_file, models)
        return ResponseHandler.success("修改成功")
    except Exception as e:
        return ResponseHandler.error(f"修改模型失败: {str(e)}")

@router.get("/sync_templates", summary="同步模型模板")
async def sync_templates():
    """同步模型模板
    
    从远程源同步最新的模型供应商模板和配置
    """
    try:
        await model_service.sync_supplier_template()
        return ResponseHandler.success("同步成功")
    except Exception as e:
        return ResponseHandler.error(f"同步模型模板失败: {str(e)}")