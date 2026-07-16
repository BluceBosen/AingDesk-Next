import os
import json
import hashlib
import asyncio
from typing import List, Dict, Optional, Any
from datetime import datetime
import aiohttp
import requests
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    EmbeddingService 类，提供文本向量嵌入服务
    支持 Ollama 和其他供应商的嵌入模型
    """
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.ollama_url = "http://localhost:11434"  # 兼容旧代码
        self.cache_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "embedding_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.dimension = 1024  # 默认嵌入维度，与Electron版本保持一致
        
    async def get_embedding(self, supplier_name: str, model: str, text: str) -> List[float]:
        """
        获取文本的向量嵌入
        
        Args:
            supplier_name: 供应商名称 (如 'ollama')
            model: 模型名称 (如 'nomic-embed-text')
            text: 需要嵌入的文本
            
        Returns:
            List[float]: 向量嵌入数组
            
        Raises:
            Exception: 如果嵌入生成失败
        """
        # 生成缓存键
        cache_key = hashlib.md5(f"{supplier_name}-{model}-{text}".encode()).hexdigest()
        
        # 检查缓存
        cached_embedding = await self._get_embedding_cache(cache_key)
        if cached_embedding:
            logger.info(f"从缓存获取嵌入向量: {model}")
            return cached_embedding
        
        try:
            embedding = []
            
            if supplier_name == "ollama":
                # 使用 Ollama 服务生成嵌入
                embedding = await self._get_ollama_embedding(model, text)
            else:
                # 使用第三方模型服务
                embedding = await self._get_supplier_embedding(supplier_name, model, text)
            
            # 验证嵌入维度
            if not embedding or len(embedding) == 0:
                raise Exception(f"嵌入生成失败: 模型 {model} 返回空嵌入")
            
            # 维度不匹配时进行处理
            if len(embedding) != self.dimension:
                if len(embedding) < self.dimension:
                    # 不足的维度以0填充
                    padding = [0.0] * (self.dimension - len(embedding))
                    embedding = embedding + padding
                else:
                    # 超出的维度抛出异常（与Electron版本保持一致）
                    raise Exception(f"嵌入维度超出预期: 期望 {self.dimension} 维，实际 {len(embedding)} 维")
                    
            # 缓存嵌入向量
            await self._set_embedding_cache(cache_key, embedding)
            
            logger.info(f"成功生成嵌入向量: {model}, 维度: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"生成嵌入时出错: {str(e)}")
            raise Exception(f"生成嵌入时出错: {str(e)}")
    
    def _get_ollama_embedding_sync(self, model: str, text: str) -> List[float]:
        """
        同步版本：使用 Ollama 服务生成嵌入向量
        
        Args:
            model: 模型名称 (如 'nomic-embed-text')
            text: 输入文本
            
        Returns:
            List[float]: 嵌入向量
        """
        try:
            url = f"{self.ollama_url}/api/embeddings"
            data = {
                "model": model,
                "prompt": text
            }
            
            # 使用同步的requests库
            response = requests.post(url, json=data, timeout=30)
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding", [])
                
                if not embedding:
                    raise Exception("Ollama 返回空嵌入向量")
                    
                return embedding
            else:
                error_text = response.text
                raise Exception(f"Ollama API 错误: {response.status_code} - {error_text}")
                
        except requests.RequestException as e:
            raise Exception(f"Ollama 连接错误: {str(e)}")
        except Exception as e:
            raise Exception(f"Ollama 嵌入生成错误: {str(e)}")
    
    def _get_supplier_embedding_sync(self, supplier_name: str, model: str, text: str) -> List[float]:
        """
        同步版本：使用第三方供应商 API 生成嵌入向量
        
        Args:
            supplier_name: 供应商名称
            model: 模型名称
            text: 输入文本
            
        Returns:
            List[float]: 嵌入向量
        """
        # 这里可以实现其他供应商的嵌入 API 调用
        # 例如 OpenAI、Cohere、Hugging Face 等
        raise NotImplementedError(f"供应商 {supplier_name} 的嵌入生成尚未实现")
    
    async def _get_ollama_embedding(self, model: str, text: str) -> List[float]:
        """
        使用 Ollama 服务生成嵌入向量（异步版本）
        
        Args:
            model: 模型名称 (如 'nomic-embed-text')
            text: 输入文本
            
        Returns:
            List[float]: 嵌入向量
        """
        return self._get_ollama_embedding_sync(model, text)
    
    async def _get_supplier_embedding(self, supplier_name: str, model: str, text: str) -> List[float]:
        """
        使用第三方供应商 API 生成嵌入向量（异步版本）
        
        Args:
            supplier_name: 供应商名称
            model: 模型名称
            text: 输入文本
            
        Returns:
            List[float]: 嵌入向量
        """
        return self._get_supplier_embedding_sync(supplier_name, model, text)
    
    def _get_embedding_cache_sync(self, cache_key: str) -> Optional[List[float]]:
        """
        同步版本：从缓存获取嵌入向量
        
        Args:
            cache_key: 缓存键
            
        Returns:
            Optional[List[float]]: 缓存的嵌入向量，如果不存在则返回 None
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                embedding = json.load(f)
                
            # 更新文件访问时间
            os.utime(cache_file, None)
            
            return embedding
            
        except Exception as e:
            logger.warning(f"读取嵌入缓存失败: {str(e)}")
            return None
    
    async def _get_embedding_cache(self, cache_key: str) -> Optional[List[float]]:
        """
        从缓存获取嵌入向量（异步版本）
        
        Args:
            cache_key: 缓存键
            
        Returns:
            Optional[List[float]]: 缓存的嵌入向量，如果不存在则返回 None
        """
        return self._get_embedding_cache_sync(cache_key)
    
    def _set_embedding_cache_sync(self, cache_key: str, embedding: List[float]) -> None:
        """
        同步版本：设置嵌入向量缓存
        
        Args:
            cache_key: 缓存键
            embedding: 嵌入向量
        """
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
        
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(embedding, f, ensure_ascii=False, indent=2)
                
            # 清理过期缓存 - 使用同步版本
            self._clear_expired_cache_sync()
            
        except Exception as e:
            logger.warning(f"写入嵌入缓存失败: {str(e)}")

    def _clear_expired_cache_sync(self, max_age_days: int = 7) -> None:
        """
        同步版本：清理过期的嵌入缓存
        
        Args:
            max_age_days: 最大缓存天数
        """
        try:
            current_time = datetime.now().timestamp()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            for filename in os.listdir(self.cache_dir):
                if not filename.endswith(".json"):
                    continue
                    
                file_path = os.path.join(self.cache_dir, filename)
                
                try:
                    file_stat = os.stat(file_path)
                    file_age = current_time - file_stat.st_mtime
                    
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        logger.info(f"删除过期嵌入缓存: {filename}")
                        
                except Exception as e:
                    logger.warning(f"清理缓存文件失败 {filename}: {str(e)}")
                    
        except Exception as e:
            logger.warning(f"清理过期缓存失败: {str(e)}")

    async def _set_embedding_cache(self, cache_key: str, embedding: List[float]) -> None:
        """
        设置嵌入向量缓存（异步版本）
        
        Args:
            cache_key: 缓存键
            embedding: 嵌入向量
        """
        self._set_embedding_cache_sync(cache_key, embedding)

    async def _clear_expired_cache(self, max_age_days: int = 7) -> None:
        """
        清理过期的嵌入缓存（异步版本）
        
        Args:
            max_age_days: 最大缓存天数
        """
        self._clear_expired_cache_sync(max_age_days)
    
    def set_dimension(self, dimension: int) -> None:
        """
        设置嵌入维度
        
        Args:
            dimension: 嵌入维度
        """
        self.dimension = dimension
        logger.info(f"设置嵌入维度: {dimension}")

    def get_embedding_sync(self, supplier_name: str, model: str, text: str) -> List[float]:
        """
        同步版本：获取文本的向量嵌入
        
        Args:
            supplier_name: 供应商名称 (如 'ollama')
            model: 模型名称 (如 'nomic-embed-text')
            text: 需要嵌入的文本
            
        Returns:
            List[float]: 向量嵌入数组
            
        Raises:
            Exception: 如果嵌入生成失败
        """
        # 直接调用同步版本的实现，避免事件循环冲突
        try:
            # 处理空文本
            if not text or text.strip() == "":
                logger.warning("输入文本为空，返回零向量")
                return [0.0] * self.dimension
            
            # 生成缓存键
            cache_key = hashlib.md5(f"{supplier_name}-{model}-{text}".encode()).hexdigest()
            
            # 检查缓存 - 使用同步版本
            cached_embedding = self._get_embedding_cache_sync(cache_key)
            if cached_embedding:
                logger.info(f"从缓存获取嵌入向量: {model}")
                return cached_embedding
            
            embedding = []
            
            if supplier_name == "ollama":
                # 使用 Ollama 服务生成嵌入 - 使用同步版本
                embedding = self._get_ollama_embedding_sync(model, text)
            else:
                # 使用第三方模型服务 - 使用同步版本
                embedding = self._get_supplier_embedding_sync(supplier_name, model, text)
            
            # 验证嵌入维度
            if not embedding or len(embedding) == 0:
                logger.warning(f"模型 {model} 返回空嵌入，返回零向量")
                return [0.0] * self.dimension
            
            # 维度不匹配时进行处理
            if len(embedding) != self.dimension:
                if len(embedding) < self.dimension:
                    # 不足的维度以0填充
                    padding = [0.0] * (self.dimension - len(embedding))
                    embedding = embedding + padding
                else:
                    # 超出的维度抛出异常（与Electron版本保持一致）
                    raise Exception(f"嵌入维度超出预期: 期望 {self.dimension} 维，实际 {len(embedding)} 维")
                    
            # 缓存嵌入向量 - 使用同步版本
            self._set_embedding_cache_sync(cache_key, embedding)
            
            logger.info(f"成功生成嵌入向量: {model}, 维度: {len(embedding)}")
            return embedding
            
        except Exception as e:
            logger.error(f"生成嵌入时出错: {str(e)}，返回零向量")
            return [0.0] * self.dimension
    
    def get_dimension(self) -> int:
        """
        获取当前嵌入维度
        
        Returns:
            int: 嵌入维度
        """
        return self.dimension