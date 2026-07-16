import os
import json
import asyncio
import uuid
import subprocess
from typing import List, Dict, Optional, AsyncGenerator, Any
from datetime import datetime
import warnings

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    warnings.warn("aiohttp package not installed. Some ModelService features might not work.")
    AIOHTTP_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    warnings.warn("httpx package not installed. Some ModelService features might not work.")
    HTTPX_AVAILABLE = False

from app.core.config import settings
from app.models.model import Model, ModelCreateRequest, ModelUpdateRequest

class ModelService:
    def __init__(self):
        self.models_dir = os.path.join(settings.DATA_DIR, "models")
        os.makedirs(self.models_dir, exist_ok=True)
        
        self.models_file = os.path.join(self.models_dir, "models.json")
        if not os.path.exists(self.models_file):
            with open(self.models_file, "w", encoding="utf-8") as f:
                json.dump([], f)
        
        # 初始化本地模型状态
        self.download_tasks = {}
        
    async def list_models(self) -> List[Model]:
        """
        获取所有可用的AI模型列表
        """
        try:
            with open(self.models_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            return [Model(**model_data) for model_data in data]
        except Exception as e:
            return []
    
    async def get_model(self, model_id: str) -> Optional[Model]:
        """
        获取特定模型的详细信息
        """
        models = await self.list_models()
        for model in models:
            if model.id == model_id:
                return model
        return None
    
    async def create_model(self, request: ModelCreateRequest) -> Model:
        """
        创建/添加新的AI模型
        """
        # 生成新模型
        model = Model(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            type=request.type,
            provider=request.provider,
            model_name=request.model_name,
            api_key=request.api_key,
            api_base_url=request.api_base_url,
            parameters=request.parameters,
            local_path=request.local_path,
        )
        
        # 检查本地模型的路径
        if model.type == "local" and model.local_path and not os.path.exists(model.local_path):
            model.status = "error"
            model.error_message = f"Model path {model.local_path} does not exist"
        
        # 保存模型
        await self._save_model(model)
        
        return model
    
    async def update_model(self, model_id: str, request: ModelUpdateRequest) -> Optional[Model]:
        """
        更新模型信息
        """
        model = await self.get_model(model_id)
        if not model:
            return None
            
        # 更新字段
        if request.name is not None:
            model.name = request.name
        if request.description is not None:
            model.description = request.description
        if request.api_key is not None:
            model.api_key = request.api_key
        if request.api_base_url is not None:
            model.api_base_url = request.api_base_url
        if request.parameters is not None:
            model.parameters = request.parameters
        if request.local_path is not None:
            model.local_path = request.local_path
        if request.status is not None:
            model.status = request.status
            
        model.updated_at = datetime.now()
        
        # 保存更新后的模型
        await self._save_model(model)
        
        return model
    
    async def delete_model(self, model_id: str) -> bool:
        """
        删除AI模型
        """
        models = await self.list_models()
        
        filtered_models = [model for model in models if model.id != model_id]
        
        if len(filtered_models) == len(models):
            # 没有找到要删除的模型
            return False
            
        # 保存更新后的模型列表
        with open(self.models_file, "w", encoding="utf-8") as f:
            json.dump([model.dict() for model in filtered_models], f, ensure_ascii=False, indent=2, default=str)
            
        return True
    
    async def get_model_status(self, model_id: str) -> Dict[str, Any]:
        """
        获取模型的状态
        """
        model = await self.get_model(model_id)
        if not model:
            return {"status": "not_found", "message": "Model not found"}
            
        # 对于本地模型，检查下载状态
        if model.type == "local":
            if model_id in self.download_tasks:
                if self.download_tasks[model_id].done():
                    # 下载完成，检查结果
                    try:
                        result = self.download_tasks[model_id].result()
                        del self.download_tasks[model_id]
                        return {"status": "completed", "message": "Download completed"}
                    except Exception as e:
                        del self.download_tasks[model_id]
                        model.status = "error"
                        model.error_message = str(e)
                        await self._save_model(model)
                        return {"status": "error", "message": str(e)}
                else:
                    # 下载仍在进行中
                    return {"status": "downloading", "message": "Model is downloading"}
        
        return {"status": model.status, "message": model.error_message or ""}
    
    async def download_model(self, model_id: str) -> None:
        """
        下载本地模型
        """
        model = await self.get_model(model_id)
        if not model or model.type != "local":
            return
            
        # 更新模型状态
        model.status = "downloading"
        await self._save_model(model)
        
        try:
            if model.provider == "ollama":
                # 使用Ollama下载模型
                cmd = ["ollama", "pull", model.model_name]
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode != 0:
                    raise Exception(f"Failed to download model: {stderr.decode()}")
                
                # 更新模型状态
                model.status = "active"
                await self._save_model(model)
            else:
                raise Exception(f"Unsupported provider for local models: {model.provider}")
        except Exception as e:
            # 更新模型状态为错误
            model.status = "error"
            model.error_message = str(e)
            await self._save_model(model)
            raise
    
    async def generate_text(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        生成文本
        已从model_engines重构到ollama_service，此方法已废弃
        """
        # 模型引擎已从model_engines移除，抛出异常
        raise NotImplementedError("文本生成功能已从model_engines重构到ollama_service")
    
    async def generate_text_stream(
        self,
        model_id: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式生成文本 - 根据模型ID路由到对应的服务
        """
        try:
            # 解析模型ID，获取供应商名称
            model_parts = model_id.split("/")
            if len(model_parts) >= 2:
                supplier_name = model_parts[0].lower()
                actual_model_id = model_id
            else:
                # 如果没有供应商前缀，默认为ollama
                supplier_name = "ollama"
                actual_model_id = f"ollama/{model_id}"
            
            # 根据供应商路由到对应的服务
            if supplier_name == "ollama":
                # 导入ollama_service并调用其generate_text_stream方法
                from app.services.ollama_service import OllamaService
                ollama_service = OllamaService()
                
                async for chunk in ollama_service.generate_text_stream(
                    model_id=actual_model_id,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                ):
                    yield chunk
            else:
                # 其他供应商的处理可以在这里添加
                raise NotImplementedError(f"供应商 {supplier_name} 的流式文本生成功能尚未实现")
                
        except Exception as e:
            yield {
                "error": str(e),
                "done": True
            }
    
    async def get_supplier_models(self) -> Dict[str, Any]:
        """
        获取所有供应商的模型列表。
        此方法会读取本地配置，并尝试从在线服务获取模型信息。
        """
        return await self.read_supplier_models("models.json", self.get_model_context_length)

    async def get_supplier_embedding_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取供应商嵌套模型列表"""
        return await self.read_supplier_models("embedding.json", lambda model: 512)

    async def get_ollama_models(self) -> List[Dict[str, Any]]:
        """
        获取 Ollama 本地模型列表，包含完整的模型信息字段
        与Electron端保持一致，构建包含size、contextLength、capability等字段的模型信息
        """
        try:
            # 从ollama_service获取模型列表
            from app.services.ollama_service import OllamaService
            ollama_service = OllamaService()
            
            # 获取Ollama模型列表
            ollama_models = await ollama_service.model_list()
            if not ollama_models:
                return []
            
            # 构建与Electron端一致的模型信息格式
            result_models = []
            for model in ollama_models:
                if not model.get("install", False):
                    continue
                    
                model_name = model.get("full_name", "")
                if not model_name:
                    continue
                
                # 构建模型信息（与Electron端保持一致）
                model_info = {
                    "title": f"Ollama/{model_name}",
                    "supplierName": "ollama",
                    "model": model_name,
                    "size": model.get("size", 0),
                    "contextLength": 0,  # Electron端设置为0
                    "capability": model.get("capability", ["llm"])
                }
                
                result_models.append(model_info)
            
            return result_models
            
        except Exception as e:
            return []

    async def _save_model(self, model: Model) -> None:
        """
        保存模型到JSON文件。
        """
        models = await self.list_models()
        # 移除旧版本，添加新版本
        models = [m for m in models if m.id != model.id]
        models.append(model)
        
        with open(self.models_file, "w", encoding="utf-8") as f:
            json.dump([m.dict() for m in models], f, ensure_ascii=False, indent=2, default=str)

    def _get_engine(self, provider: str):
        """
        根据提供者获取对应的模型引擎实例。
        已从model_engines重构到ollama_service，此方法已废弃
        """
        # 引擎映射已移除，返回None
        return None
    
    async def _save_model(self, model: Model) -> None:
        """
        保存模型到文件
        """
        models = await self.list_models()
        
        # 查找并替换或添加模型
        found = False
        for i, existing_model in enumerate(models):
            if existing_model.id == model.id:
                models[i] = model
                found = True
                break
                
        if not found:
            models.append(model)
            
        # 保存更新后的模型列表
        with open(self.models_file, "w", encoding="utf-8") as f:
            json.dump([model.dict() for model in models], f, ensure_ascii=False, indent=2, default=str)

    async def get_model_top5(self, all_models: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取常用模型TOP5，基于使用频率排序
        """
        result = {}
        common_models = []
        
        # 获取模型使用统计
        model_total_list = self.get_model_used_total_list()
        
        # 扁平化所有模型列表并计算使用次数
        for provider, models in all_models.items():
            for model_data in models:
                supplier_name = model_data.get("supplierName", provider)
                model_name = model_data.get("model", model_data.get("name", ""))
                
                # 获取使用次数
                key = f"{supplier_name}/{model_name}"
                used_total = model_total_list.get(key, 0)
                
                # 构建模型信息
                model_info = {
                    "title": model_data.get("title", f"{supplier_name}/{model_name}"),
                    "supplierName": supplier_name,
                    "supplierTitle": model_data.get("supplierTitle", supplier_name),
                    "model": model_name,
                    "size": model_data.get("size", 0),
                    "contextLength": model_data.get("contextLength", self.get_model_context_length(model_name)),
                    "capability": model_data.get("capability", ["llm"]),
                    "usedTotal": used_total
                }
                common_models.append(model_info)
        
        # 按使用次数降序排序
        common_models.sort(key=lambda x: x["usedTotal"], reverse=True)
        
        # 取前5个作为TOP5
        top5_models = common_models[:5]
        
        # 如果存在常用模型，添加到结果中
        if top5_models:
            result["commonModelList"] = top5_models
        
        return result

    def _get_models_file_path(self, supplier_name: str) -> str:
        """获取供应商模型文件路径"""
        return os.path.join(self.models_dir, supplier_name, "models.json")
    
    def _get_embedding_file_path(self, supplier_name: str) -> str:
        """获取供应商嵌入模型文件路径"""
        return os.path.join(self.models_dir, supplier_name, "embedding.json")
    
    def _read_models(self, supplier_name: str) -> List[Dict[str, Any]]:
        """读取供应商模型列表"""
        models_file = self._get_models_file_path(supplier_name)
        if not os.path.exists(models_file):
            return []
        
        try:
            with open(models_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    
    def _read_embedding_models(self, supplier_name: str) -> List[Dict[str, Any]]:
        """读取供应商嵌入模型列表"""
        embedding_file = self._get_embedding_file_path(supplier_name)
        if not os.path.exists(embedding_file):
            return []
        
        try:
            with open(embedding_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    
    async def _save_models(self, supplier_name: str, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """保存模型列表到文件"""
        models_file = self._get_models_file_path(supplier_name)
        os.makedirs(os.path.dirname(models_file), exist_ok=True)
        
        with open(models_file, "w", encoding="utf-8") as f:
            json.dump(models, f, ensure_ascii=False, indent=4)
        
        return models
    
    async def _save_embedding_models(self, supplier_name: str, models: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """保存嵌入模型列表到文件"""
        embedding_file = self._get_embedding_file_path(supplier_name)
        os.makedirs(os.path.dirname(embedding_file), exist_ok=True)
        
        with open(embedding_file, "w", encoding="utf-8") as f:
            json.dump(models, f, ensure_ascii=False, indent=4)
        
        return models
    
    async def get_online_models(self, supplier_name: str, base_url: Optional[str], api_key: Optional[str]) -> List[Dict[str, Any]]:
        """
        获取在线模型列表。
        此方法应根据供应商类型调用相应的API来获取模型信息。
        """
        models = []
        
        # 获取现有模型列表
        existing_models = self._read_models(supplier_name)
        
        if supplier_name == "openai":
            # 示例：调用OpenAI API来获取模型列表
            if api_key and base_url:
                try:
                    openai_engine = self.engines.get("openai")
                    if openai_engine and hasattr(openai_engine, "list_models") and AIOHTTP_AVAILABLE:
                        online_models = await openai_engine.list_models(api_key=api_key, base_url=base_url)
                        
                        # 合并在线模型到现有模型列表
                        for online_model in online_models:
                            if not any(item.get("modelName") == online_model.get("id") for item in existing_models):
                                model_info = {
                                    "title": "",
                                    "supplierName": supplier_name,
                                    "modelName": online_model.get("id", ""),
                                    "capability": ["llm"],
                                    "status": True
                                }
                                existing_models.append(model_info)
                        
                        # 保存更新后的模型列表
                        await self._save_models(supplier_name, existing_models)
                        return existing_models
                        
                except Exception as e:
                    pass
        
        # 对于SiliconFlow供应商，还需要获取嵌入模型
        if supplier_name == "SiliconFlow":
            await self._get_online_embedding_models(supplier_name, base_url, api_key)
        
        return existing_models
    
    async def _get_online_embedding_models(self, supplier_name: str, base_url: Optional[str], api_key: Optional[str]) -> List[Dict[str, Any]]:
        """获取在线嵌入模型列表"""
        existing_embedding_models = self._read_embedding_models(supplier_name)
        
        if supplier_name == "SiliconFlow" and api_key and base_url:
            try:
                openai_engine = self.engines.get("openai")
                if openai_engine and hasattr(openai_engine, "list_models") and AIOHTTP_AVAILABLE:
                    # 获取嵌入模型
                    embedding_models = await openai_engine.list_models(api_key=api_key, base_url=base_url, model_type="embedding")
                    
                    # 合并在线嵌入模型到现有模型列表
                    for embedding_model in embedding_models:
                        if not any(item.get("modelName") == embedding_model.get("id") for item in existing_embedding_models):
                            model_info = {
                                "title": "",
                                "supplierName": supplier_name,
                                "modelName": embedding_model.get("id", ""),
                                "capability": ["embedding"],
                                "status": True
                            }
                            existing_embedding_models.append(model_info)
                    
                    # 保存更新后的嵌入模型列表
                    await self._save_embedding_models(supplier_name, existing_embedding_models)
                    
            except Exception as e:
                pass
        
        return existing_embedding_models

    async def sync_supplier_template(self) -> None:
        """
        同步模型供应商模板。
        此方法用于初始化或更新本地的供应商配置模板。
        例如，可以从预定义的模板文件或远程源同步。
        """
        # 实际实现可能包括：
        # - 读取默认供应商模板
        # - 与现有配置合并或更新
        # - 确保关键供应商（如ollama, openai）的默认配置存在
        
        # 示例：确保Ollama的默认供应商配置存在
        ollama_supplier_path = os.path.join(self.models_dir, "ollama")
        ollama_config_file = os.path.join(ollama_supplier_path, "config.json")
        
        if not os.path.exists(ollama_supplier_path):
            os.makedirs(ollama_supplier_path, exist_ok=True)
            
        if not os.path.exists(ollama_config_file):
            default_ollama_config = {
                "supplierName": "ollama",
                "supplierTitle": "Ollama 本地模型",
                "baseUrl": settings.OLLAMA_BASE_URL,
                "apiKey": "",
                "status": True,
                "sort": 100 # 示例排序值
            }
            with open(ollama_config_file, "w", encoding="utf-8") as f:
                json.dump(default_ollama_config, f, ensure_ascii=False, indent=4)
                
    async def check_supplier_config(self, supplier_name: str, base_url: Optional[str], api_key: Optional[str]) -> bool:
        """
        检查供应商配置是否有效。
        此方法应根据供应商类型执行不同的检查逻辑。
        例如，对于API供应商，可能尝试连接API；对于本地Ollama，可能检查服务是否运行。
        """
        if supplier_name == "ollama":
            # 对于Ollama，可以尝试 ping Ollama 服务来验证其可用性
            # 更完整的实现会尝试发起一个简单的/api/tags请求
            if base_url is None: # Use the configured base_url if not provided
                base_url = settings.OLLAMA_BASE_URL
            
            if not AIOHTTP_AVAILABLE:
                warnings.warn("aiohttp package not installed. OllamaEngine will not work.")
                return False
                
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{base_url}/api/tags", timeout=5) as response:
                        return response.status == 200
            except Exception as e:
                return False
        else:
            # 对于其他供应商（OpenAI标准API），尝试连接API测试配置有效性
            if not HTTPX_AVAILABLE:
                warnings.warn("httpx package not installed. Cannot test API connection.")
                return bool(api_key and base_url)  # 回退到简单的非空检查
            
            if not api_key or not base_url:
                return False
                
            return await self._test_api_connection(base_url, api_key)
    
    async def _test_api_connection(self, base_url: str, api_key: str) -> bool:
        """
        测试API连接是否有效（支持OpenAI标准API）
        """
        try:
            # 构建请求URL，确保正确的路径格式
            if base_url.endswith("/"):
                base_url = base_url[:-1]
            if base_url.endswith("/v1"):
                test_url = base_url + "/models"
            else:
                test_url = base_url + "/v1/models"
            
            # 设置超时时间
            timeout = httpx.Timeout(connect=10.0, read=10.0, write=10.0, pool=10.0)
            
            # 构建请求
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    test_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    print(f"供应商API连接测试成功，状态码: {response.status_code}")
                    return True
                else:
                    print(f"供应商API连接测试失败，状态码: {response.status_code}, 响应: {response.text}")
                    return False
                    
        except Exception as e:
            print(f"测试供应商API连接时出错: {e}")
            return False
    
    def get_model_used_total_list(self) -> Dict[str, int]:
        """
        获取模型使用次数列表
        """
        total_file = os.path.join(settings.DATA_DIR, 'modelTotal.json')
        if not os.path.exists(total_file):
            return {}
        
        try:
            with open(total_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    
    def get_model_used_total(self, supplier_name: str, model_name: str) -> int:
        """
        获取模型使用次数
        """
        total_obj = self.get_model_used_total_list()
        key = f"{supplier_name}/{model_name}"
        return total_obj.get(key, 0)
    
    def set_model_used_total(self, supplier_name: str, model_name: str) -> None:
        """
        统计模型使用次数
        """
        total_file = os.path.join(settings.DATA_DIR, 'modelTotal.json')
        
        # 读取现有统计
        models = self.get_model_used_total_list()
        
        # 更新使用次数
        key = f"{supplier_name}/{model_name}"
        models[key] = models.get(key, 0) + 1
        
        # 保存到文件
        try:
            with open(total_file, 'w', encoding='utf-8') as f:
                json.dump(models, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存模型使用统计失败: {e}")

    def get_model_context_length(self, model: str) -> int:
        """
        获取模型上下文长度
        """
        model_context_obj = {
            "qwq": 32768,
            "qwen2.5": 32768,
            "qwen": 32768,
            "deepseek": 32768,
            "phi": 16384,
            "gemma2": 8192,
            "smollm": 8192,
            "llama": 32768,
            "glm": 32768,
            "qvq": 32768,
        }
        
        model_str_lower = model.lower()
        for key, value in model_context_obj.items():
            if model_str_lower in key:
                return value
        return 32768
    
    def _is_tools_model(self, model: str) -> bool:
        """
        判断模型是否支持工具调用
        """
        not_tools = ['deepseek-r1', 'deepseek-v3', 'deepseek-reasoner', 'lite', 'gemma2', 'smollm', 'llama', 'glm', 'qvq']
        model_str_lower = model.lower()
        return not any(item in model_str_lower for item in not_tools)
    
    def _get_capability(self, model: str, capability: List[str]) -> List[str]:
        """
        获取模型能力
        """
        if not capability:
            capability = ["llm"]
        
        model_str_lower = model.lower()
        
        if "embedding" in capability:
            return capability
        
        if "llm" in capability:
            if "tools" in capability:
                return capability
            if self._is_tools_model(model_str_lower):
                capability.append("tools")
            return capability
        
        return capability
    
    async def read_supplier_models(self, file_name: str, context_length_func) -> Dict[str, List[Dict[str, Any]]]:
        """
        读取供应商模型列表的通用函数
        """
        result = {}
        
        # 检查供应商目录是否存在
        if not os.path.exists(self.models_dir):
            return result
        
        # 遍历所有供应商
        for supplier in os.listdir(self.models_dir):
            supplier_path = os.path.join(self.models_dir, supplier)
            supplier_config_file = os.path.join(supplier_path, "config.json")
            model_config_file = os.path.join(supplier_path, file_name)
            
            # 检查必要的文件是否存在
            if not os.path.isdir(supplier_path) or not os.path.exists(supplier_config_file) or not os.path.exists(model_config_file):
                continue
            
            try:
                # 读取供应商配置
                with open(supplier_config_file, "r", encoding="utf-8") as f:
                    supplier_config = json.load(f)
                
                # 读取模型配置
                with open(model_config_file, "r", encoding="utf-8") as f:
                    models = json.load(f)
                
                # 验证必要的字段
                if not supplier_config.get("supplierName") or not models:
                    continue
                
                # 检查供应商状态
                if not supplier_config.get("apiKey") or not supplier_config.get("baseUrl") or supplier_config.get("status") is False:
                    continue
                
                # 构建模型列表
                new_models = []
                for model in models:
                    model_info = {
                        "title": model.get("title") or f"{supplier_config.get('supplierTitle', supplier_config.get('supplierName'))}/{model.get('modelName', '')}",
                        "supplierName": supplier_config["supplierName"],
                        "supplierTitle": supplier_config.get("supplierTitle", supplier_config["supplierName"]),
                        "model": model.get("modelName", ""),
                        "size": 0,
                        "contextLength": context_length_func(model.get("modelName", "")),
                        "capability": self._get_capability(model.get("modelName", ""), model.get("capability", []))
                    }
                    new_models.append(model_info)
                
                result[supplier_config.get("supplierTitle", supplier_config["supplierName"])] = new_models
                
            except Exception as e:
                continue
        
        return result