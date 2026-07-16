import os
import json
import uuid
import shutil
import time
from typing import List, Dict, Optional, Any, BinaryIO
from datetime import datetime
import asyncio
import tempfile
import hashlib
import logging

import fitz  # PyMuPDF
import jieba
import numpy as np
from fastapi import UploadFile

from app.core.config import settings
from app.models.rag import KnowledgeBase, Document, KnowledgeBaseCreate, KnowledgeBaseUpdate, TextChunk, SearchResult
from app.rag.utils import PubUtils
from app.services.model_service import ModelService
from app.services.embedding_service import EmbeddingService
from app.rag.vector_lancedb import lancedb_manager
from app.utils.document_parser import parse_document, is_supported_file_type

class RagService:
    def __init__(self):
        self.model_service = ModelService()
        self.embedding_service = EmbeddingService()
        self.rag_root_dir = os.path.join(settings.DATA_DIR, "rag")
        os.makedirs(self.rag_root_dir, exist_ok=True)
        self.index_tips_dir = os.path.join(self.rag_root_dir, "index_tips")
        os.makedirs(self.index_tips_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        # 文档表名，与electron项目保持一致
        self.doc_table = 'doc_table'

    def _get_rag_path(self, rag_name: str) -> str:
        return os.path.join(self.rag_root_dir, rag_name)

    def _get_rag_config_path(self, rag_name: str) -> str:
        return os.path.join(self._get_rag_path(rag_name), "config.json")

    def _get_doc_source_path(self, rag_name: str, doc_id: str) -> str:
        return os.path.join(self._get_rag_path(rag_name), "source", doc_id)

    def _get_doc_markdown_path(self, rag_name: str, doc_id: str) -> str:
        return os.path.join(self._get_rag_path(rag_name), "markdown", doc_id)

    def _get_rag_index_tip_path(self, rag_name: str) -> str:
        return os.path.join(self.index_tips_dir, hashlib.md5(rag_name.encode()).hexdigest() + ".pl")

    async def _read_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return None

    async def _write_json_file(self, file_path: str, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)


    async def remove_rag(self, rag_name: str) -> bool:
        """
        删除知识库及其所有关联文件和索引
        """
        rag_path = self._get_rag_path(rag_name)
        if os.path.exists(rag_path):
            shutil.rmtree(rag_path)
        
        index_tip_file = self._get_rag_index_tip_path(rag_name)
        if os.path.exists(index_tip_file):
            os.unlink(index_tip_file)

        return True

    async def get_rag_list(self) -> List[Dict[str, Any]]:
        """
        获取所有知识库列表，包含文档数量和索引状态
        与electron项目get_rag_list方法保持完全一致
        """
        rag_list = []
        if os.path.exists(self.rag_root_dir):
            for item in os.listdir(self.rag_root_dir):
                item_path = os.path.join(self.rag_root_dir, item)
                if os.path.isdir(item_path) and item not in ["index_tips", "vector_db"]:
                    config_file = self._get_rag_config_path(item)
                    if os.path.exists(config_file):
                        try:
                            config = await self._read_json_file(config_file)
                            if config:
                                # 补全缺失字段，与electron实现保持一致
                                if not config.get('vectorWeight'):
                                    config['ragCreateTime'] = int(time.time())  # 创建时间
                                    config['embeddingModel'] = 'bge-m3:latest'  # 嵌入模型
                                    config['searchStrategy'] = 1  # 检索策略 1=混合检索 2=向量检索 3=全文检索
                                    config['maxRecall'] = 5  # 最大召回数
                                    config['recallAccuracy'] = 0.1  # 召回精度
                                    config['resultReordering'] = 1  # 结果重排序 1=开启 0=关闭
                                    config['rerankModel'] = ''  # 重排序模型
                                    config['queryRewrite'] = 0  # 查询重写 1=开启 0=关闭
                                    config['vectorWeight'] = 0.7  # 向量权重
                                    config['keywordWeight'] = 0.3  # 关键词权重
                                    
                                    # 重新写入文件
                                    await self._write_json_file(config_file, config)
                                
                                if not config.get('supplierName'):
                                    config['supplierName'] = 'ollama'
                                    await self._write_json_file(config_file, config)
                                
                                # 检查嵌入模型是否存在
                                config['embeddingModelExist'] = True
                                config['errorMsg'] = ''
                                
                                # 获取嵌入模型映射（简化版本）
                                try:
                                    from ..services.ollama_service import OllamaService
                                    ollama_service = OllamaService()
                                    embedding_list = await ollama_service.get_embedding_model_list()
                                    embedding_models = [model.get('model', '') for model in embedding_list]
                                    
                                    if config.get('embeddingModel') not in embedding_models:
                                        config['embeddingModelExist'] = False
                                        config['errorMsg'] = f"指定嵌入模型不存在: {config.get('embeddingModel', '')}"
                                except Exception as e:
                                    pass
                                
                                source_dir = os.path.join(item_path, "source")
                                doc_count = len(os.listdir(source_dir)) if os.path.exists(source_dir) else 0
                                config['docCount'] = doc_count
                                
                                index_tip_file = self._get_rag_index_tip_path(item)
                                config['indexStatus'] = os.path.exists(index_tip_file)
                                
                                rag_list.append(config)
                        except Exception as e:
                            continue
        
        rag_list.sort(key=lambda x: x.get('ragCreateTime', 0), reverse=True)
        return rag_list

    async def upload_doc(
        self, 
        rag_name: str, 
        file_path: str, 
        separators: List[str] = None, 
        chunk_size: int = 1000, 
        overlap_size: int = 200,
        final_filename: str = None
    ) -> Dict[str, Any]:
        """
        上传文档并进行解析、分块、嵌入和存储（异步版本）
        与electron项目upload_doc方法保持完全一致
        
        参数:
        - rag_name: 知识库名称
        - file_path: 文件路径
        - separators: 分隔符列表
        - chunk_size: 分块大小
        - overlap_size: 重叠大小
        - final_filename: 最终文件名（可选）
        
        返回:
        - 包含doc_id和文件信息的字典
        """
        # 调用同步版本
        return await self.upload_doc_sync(
            rag_name, file_path, separators, chunk_size, overlap_size, final_filename
        )
    
    async def upload_doc_sync(
        self, 
        rag_name: str, 
        file_path: str, 
        separators: List[str] = None, 
        chunk_size: int = 1000, 
        overlap_size: int = 200,
        final_filename: str = None,
        doc_id: str = None
    ) -> Dict[str, Any]:
        """
        上传文档并进行解析、分块、嵌入和存储（同步版本）
        用于后台任务处理
        
        参数:
        - rag_name: 知识库名称
        - file_path: 文件路径
        - separators: 分隔符列表
        - chunk_size: 分块大小
        - overlap_size: 重叠大小
        - final_filename: 最终文件名（可选）
        
        返回:
        - 包含doc_id和文件信息的字典
        """
        try:
            # 确保知识库存在
            rag_path = self._get_rag_path(rag_name)
            if not os.path.exists(rag_path):
                raise Exception("知识库不存在")
            
            # 使用传递的doc_id或生成新的
            if doc_id is None:
                doc_id = str(uuid.uuid4())
            source_dir = os.path.join(rag_path, "source")
            markdown_dir = os.path.join(rag_path, "markdown")
            
            os.makedirs(source_dir, exist_ok=True)
            os.makedirs(markdown_dir, exist_ok=True)

            # 确定目标文件路径
            if final_filename:
                dest_file_path = os.path.join(source_dir, final_filename)
            else:
                dest_file_path = os.path.join(source_dir, f"{doc_id}_{os.path.basename(file_path)}")
            
            # 复制文件
            shutil.copyfile(file_path, dest_file_path)

            # 解析文件类型
            file_ext = os.path.splitext(dest_file_path)[1].lower()
            file_type = "unknown"
            if file_ext == ".pdf": file_type = "pdf"
            elif file_ext == ".txt": file_type = "text"
            elif file_ext in [".doc", ".docx"]: file_type = "word"
            elif file_ext in [".xls", ".xlsx"]: file_type = "excel"
            elif file_ext in [".csv", ".html", ".htm", ".md", ".json", ".log"]:
                file_type = "text"  # 这些文件都按文本处理

            # 提取文本分块
            extracted_chunks = self._extract_text_sync(
                dest_file_path, file_type, chunk_size, overlap_size, separators, doc_id
            )

            # 保存分块数据
            chunks_file_path = os.path.join(markdown_dir, f"{doc_id}.json")
            with open(chunks_file_path, "w", encoding="utf-8") as f:
                json.dump([chunk.dict() for chunk in extracted_chunks], f, ensure_ascii=False, indent=2)

            # 生成文档摘要和关键词
            from app.rag.rag import Rag
            rag_instance = Rag()
            full_text = "\n".join([chunk.text for chunk in extracted_chunks])
            doc_abstract = await rag_instance.generate_abstract(full_text)
            doc_keywords = await rag_instance.generate_keywords(full_text, 5)

            # 生成向量并存储到向量数据库
            vector_db = lancedb_manager
            
            # 读取配置文件获取嵌入模型及供应商
            config_path = self._get_rag_config_path(rag_name)
            config = self._read_json_file_sync(config_path)
            supplier_name = config.get('supplierName', 'ollama') if config else 'ollama'
            embedding_model = config.get('embeddingModel', 'bge-m3:latest') if config else 'bge-m3:latest'
            
            # 检查向量表是否存在，如果不存在则创建
            try:
                # 使用MD5处理表名，与Electron保持一致
                import hashlib
                table_name = hashlib.md5(rag_name.encode('utf-8')).hexdigest()
                
                # 使用异步方式检查表是否存在
                if not await vector_db.table_exists(table_name):
                    # 使用第一个分块作为初始文本创建表
                    initial_text = extracted_chunks[0].text if extracted_chunks else "初始文档"
                    await vector_db.create_table(
                        table_name=table_name,
                        supplier_name="ollama",
                        model=embedding_model,
                        initial_text=initial_text
                    )
                    self.logger.info(f"成功创建向量表: {rag_name} (表名: {table_name}), 使用嵌入模型: {embedding_model}")
            except Exception as e:
                self.logger.error(f"检查或创建向量表失败: {rag_name}, 错误: {e}")
                # 如果创建表失败，继续尝试添加向量，让add_vectors_async处理错误
            
            for i, chunk in enumerate(extracted_chunks):
                try:
                    # 生成向量（同步调用）- 使用配置文件中的供应商及嵌入模型
                    embedding = self.embedding_service.get_embedding_sync(supplier_name, embedding_model, chunk.text)
                    if embedding is not None:
                        # 存储到向量数据库（异步调用）
                        await vector_db.add_vectors_async(
                            table_name=table_name,  # 使用MD5处理后的表名
                            vectors=[{
                                "id": f"{doc_id}_{i}",
                                "doc": chunk.text,
                                "doc_id": doc_id,
                                "chunk_id": f"{doc_id}_{i}",
                                "vector": embedding,
                                "metadata": {
                                    "document_id": doc_id,
                                    "chunk_index": i,
                                    "file_name": os.path.basename(dest_file_path),
                                    "page_number": chunk.page_number if hasattr(chunk, 'page_number') else None,
                                    "total_chunks": len(extracted_chunks)
                                }
                            }]
                        )
                        self.logger.info(f"已添加向量到数据库: {doc_id}_{i}")
                    else:
                        self.logger.warning(f"生成向量失败: {doc_id}_{i}")
                except Exception as e:
                    self.logger.error(f"处理向量时出错 {doc_id}_{i}: {e}")
                    # 继续处理其他分块，不中断整个流程

            # 向doc_table添加文档记录
            try:
                from app.rag.rag import Rag
                rag_instance = Rag()

                # 确保文档记录表存在
                await rag_instance.create_doc_table('doc_table')

                # 构建文档记录，使用现有的doc_id
                doc_record = {
                    'doc_id': doc_id,
                    'doc_name': os.path.basename(dest_file_path),
                    'doc_file': dest_file_path.replace(PubUtils.get_data_path(), '{DATA_DIR}'),
                    'md_file': '',
                    'doc_rag': rag_name,
                    'doc_abstract': doc_abstract,
                    'doc_keywords': doc_keywords,
                    'is_parsed': 3,  # 标记为已完成（解析+嵌入）
                    'update_time': PubUtils.time(),
                    'separators': separators if separators else [],
                    'chunk_size': chunk_size,
                    'overlap_size': overlap_size,
                }
                
                # 直接调用lancedb_manager添加记录
                success = await lancedb_manager.add_record_async(rag_instance.doc_table, doc_record)
                if success:
                    self.logger.info(f"成功向doc_table添加文档记录: {doc_id}")
                else:
                    self.logger.error(f"向doc_table添加文档记录失败")
            except Exception as e:
                self.logger.error(f"向doc_table添加文档记录失败: {e}")
                # 不中断主流程，继续执行

            # 更新索引状态
            index_tip_file = self._get_rag_index_tip_path(rag_name)
            with open(index_tip_file, "w") as f:
                f.write(f"indexed: {doc_id}")

            # 更新配置文件
            config_path = self._get_rag_config_path(rag_name)
            config = self._read_json_file_sync(config_path)
            if config:
                config["separators"] = separators if separators else []
                config["chunkSize"] = chunk_size
                config["overlapSize"] = overlap_size
                with open(config_path, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)

            return {
                "doc_id": doc_id,
                "filename": os.path.basename(dest_file_path),
                "file_path": dest_file_path,
                "chunks_count": len(extracted_chunks)
            }
            
        except Exception as e:
            # 清理已复制的文件
            if 'dest_file_path' in locals() and os.path.exists(dest_file_path):
                try:
                    os.remove(dest_file_path)
                except:
                    pass
            raise Exception(f"文档上传失败: {str(e)}")
    
    def _read_json_file_sync(self, file_path: str) -> Optional[Dict[str, Any]]:
        """同步读取JSON文件"""
        if not os.path.exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading JSON file {file_path}: {e}")
            return None



    async def _get_rag_doc_list_from_filesystem(self, rag_name: str) -> List[Dict[str, Any]]:
        """
        从文件系统获取知识库文档列表（数据库查询失败时的回退方案）
        """
        doc_list = []
        rag_path = self._get_rag_path(rag_name)
        source_dir = os.path.join(rag_path, "source")
        markdown_dir = os.path.join(rag_path, "markdown")

        # 创建一个映射，从document_id到分块文件信息
        doc_chunks_map = {}
        if os.path.exists(markdown_dir):
            for json_file in os.listdir(markdown_dir):
                if json_file.endswith('.json'):
                    json_path = os.path.join(markdown_dir, json_file)
                    try:
                        chunks_data = await self._read_json_file(json_path)
                        if chunks_data and len(chunks_data) > 0:
                            # 从第一个分块获取document_id
                            first_chunk = chunks_data[0]
                            document_id = first_chunk.get("document_id", "")
                            if document_id:
                                doc_chunks_map[document_id] = {
                                    "chunks_file": json_file,
                                    "chunks_count": len(chunks_data)
                                }
                    except Exception as e:
                        pass

        if os.path.exists(source_dir):
            for filename in os.listdir(source_dir):
                if filename.startswith(".."): continue

                parts = filename.split('_', 1)
                file_base_name_without_ext = os.path.splitext(parts[1] if len(parts) > 1 else filename)[0]
                
                # 优先使用分块数据中的document_id
                doc_id = None
                original_filename = parts[1] if len(parts) > 1 else filename

                file_path = os.path.join(source_dir, filename)
                if not os.path.isfile(file_path): continue
                
                file_stat = os.stat(file_path)
                doc_size = file_stat.st_size
                doc_create_time = int(file_stat.st_ctime)

                # 确定文档状态和正确的doc_id
                doc_status = "pending"
                
                # 首先检查文件名的第一部分是否是UUID格式且在分块映射中
                if len(parts) > 1 and len(parts[0]) == 36 and parts[0] in doc_chunks_map:
                    doc_status = "completed"
                    doc_id = parts[0]  # 使用文件名的第一部分作为doc_id
                # 检查基础文件名是否在分块映射中
                elif file_base_name_without_ext in doc_chunks_map:
                    doc_status = "completed"
                    doc_id = file_base_name_without_ext  # 使用正确的doc_id
                # 检查文件名的第一部分是否在分块映射中
                elif len(parts) > 1 and parts[0] in doc_chunks_map:
                    doc_status = "completed"
                    doc_id = parts[0]  # 使用文件名的第一部分作为doc_id
                
                # 如果没有找到对应的doc_id，使用默认规则
                if doc_id is None:
                    doc_id = parts[0] if len(parts) > 1 and len(parts[0]) == 36 else file_base_name_without_ext
                
                doc_list.append({
                    "docId": doc_id,
                    "docName": original_filename,
                    "docSize": doc_size,
                    "docStatus": doc_status,
                    "docCreateTime": doc_create_time
                })
        
        return doc_list

    async def get_rag_doc_list(self, rag_name: str) -> List[Dict[str, Any]]:
        """
        获取知识库文档列表，包含文档ID、名称、大小、状态和创建时间
        与electron项目保持一致：从数据库查询文档列表
        """
        try:
            # 使用数据库查询文档列表（与electron项目保持一致）
            from app.rag.vector_lancedb import lancedb_manager
            
            # 查询指定知识库的所有文档
            records = await lancedb_manager.query_record_async(self.doc_table, f"doc_rag='{rag_name}'")

            doc_list = []
            for record in records:
                # 从数据库记录中提取文档信息
                doc_id = record.get('doc_id', '')
                doc_name = record.get('doc_name', '')
                is_parsed = record.get('is_parsed', 0)
                update_time = record.get('update_time', 0)
                
                # 获取文件大小（从source目录）
                rag_path = self._get_rag_path(rag_name)
                source_dir = os.path.join(rag_path, "source")
                doc_size = 0
                
                # 尝试找到对应的源文件
                source_file = None
                if os.path.exists(source_dir):
                    for filename in os.listdir(source_dir):
                        # 查找文件名包含doc_id的文件（格式：doc_id_filename）
                        if filename.startswith(f"{doc_id}_"):
                            source_file = os.path.join(source_dir, filename)
                            break
                        # 如果找不到，查找文件名等于doc_name的文件
                        elif filename == doc_name:
                            source_file = os.path.join(source_dir, filename)
                            break
                
                # 获取文件大小
                if source_file and os.path.exists(source_file):
                    doc_size = os.path.getsize(source_file)
                
                # 确定文档状态，与 AiSpace / AingDesk-1.2.4 保持一致
                # 0=待解析 2=已解析待嵌入 3=已完成 -1=失败
                doc_status = "pending"
                if is_parsed == 3:
                    doc_status = "completed"
                elif is_parsed == 2:
                    doc_status = "processing"
                elif is_parsed == -1:
                    doc_status = "failed"
                
                doc_list.append({
                    "docId": doc_id,
                    "docName": doc_name,
                    "docSize": doc_size,
                    "docStatus": doc_status,
                    "is_parsed": is_parsed,
                    "docCreateTime": update_time
                })
            
            return doc_list
            
        except Exception as e:
            print(f"获取知识库文档列表失败: {e}")
            # 如果数据库查询失败，回退到文件系统扫描
            return await self._get_rag_doc_list_from_filesystem(rag_name)

    async def get_doc_content(self, rag_name: str, doc_name: str) -> Optional[str]:
        """
        获取文档内容（从markdown目录读取）
        与electron项目get_doc_content方法保持完全一致
        """
        try:
            # 首先尝试直接查找 - 如果doc_name就是doc_id（UUID格式）
            json_file = os.path.join(self.rag_root_dir, rag_name, "markdown", f"{doc_name}.json")
            if os.path.exists(json_file):
                chunks_data = await self._read_json_file(json_file)
                if chunks_data and len(chunks_data) > 0:
                    # 合并所有分块的文本内容
                    content = "\n".join([chunk.get("text", "") for chunk in chunks_data])
                    return content
            
            # 如果直接查找失败，获取文档列表来找到正确的doc_id和分块文件
            doc_list = await self.get_rag_doc_list(rag_name)
            target_doc_id = None
            
            for doc in doc_list:
                if doc["docName"] == doc_name or doc["docId"] == doc_name:
                    target_doc_id = doc["docId"]
                    break
            
            # 用找到的doc_id再次尝试 - 需要找到对应的分块文件
            if target_doc_id:
                # 重新构建分块映射来找到正确的分块文件
                markdown_dir = os.path.join(self.rag_root_dir, rag_name, "markdown")
                if os.path.exists(markdown_dir):
                    for json_file in os.listdir(markdown_dir):
                        if json_file.endswith('.json'):
                            json_path = os.path.join(markdown_dir, json_file)
                            try:
                                chunks_data = await self._read_json_file(json_path)
                                if chunks_data and len(chunks_data) > 0:
                                    # 检查这个分块文件是否匹配我们的doc_id
                                    first_chunk = chunks_data[0]
                                    document_id = first_chunk.get("document_id", "")
                                    if document_id == target_doc_id:
                                        # 合并所有分块的文本内容
                                        content = "\n".join([chunk.get("text", "") for chunk in chunks_data])
                                        return content
                            except Exception as e:
                                pass
            
            # 回退到尝试读取Markdown文件（兼容旧格式）
            md_file = os.path.join(self.rag_root_dir, rag_name, "markdown", f"{doc_name}.md")
            if os.path.exists(md_file):
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 替换URL占位符（与electron项目一致）
                content = content.replace("{URL}", "http://127.0.0.1:7071")
                return content
            
            return None
        except Exception as e:
            return None

    async def get_doc_file_path(self, rag_name: str, doc_name: str) -> Optional[str]:
        """
        获取文档文件路径
        与electron项目download_doc方法保持完全一致
        """
        try:
            # 构建source目录路径（与electron项目一致）
            source_dir = os.path.join(self.rag_root_dir, rag_name, "source")
            
            if not os.path.exists(source_dir):
                return None
            
            # 遍历source目录查找文件（与electron项目一致）
            for filename in os.listdir(source_dir):
                if filename == doc_name:
                    return os.path.join(source_dir, filename)
            
            return None
        except Exception as e:
            return None

    async def remove_doc(self, rag_name: str, doc_ids: List[str]) -> bool:
        """
        从知识库中删除文档及其所有关联文件和索引
        """
        success = True
        rag_path = self._get_rag_path(rag_name)
        source_dir = os.path.join(rag_path, "source")
        markdown_dir = os.path.join(rag_path, "markdown")

        for doc_id in doc_ids:
            original_filename = None
            doc_list = await self.get_rag_doc_list(rag_name)
            for doc in doc_list:
                if doc["docId"] == doc_id:
                    original_filename = doc["docName"]
                    break
            
            if original_filename:
                # 尝试删除 doc_id_文件名 格式
                source_file_to_delete = os.path.join(source_dir, f"{doc_id}_{original_filename}")
                if os.path.exists(source_file_to_delete):
                    os.unlink(source_file_to_delete)
                else:
                    # 尝试删除原始文件名格式（兼容 upload_doc 覆盖模式）
                    source_file_to_delete = os.path.join(source_dir, original_filename)
                    if os.path.exists(source_file_to_delete):
                        os.unlink(source_file_to_delete)

            markdown_file_to_delete = os.path.join(markdown_dir, f"{doc_id}.json")
            if os.path.exists(markdown_file_to_delete): os.unlink(markdown_file_to_delete)

            # 从 LanceDB 文档表及向量表中删除该文档记录
            from app.rag.rag import Rag
            rag_instance = Rag()
            await rag_instance.remove_document_from_db(rag_name, doc_id)

        return success

    async def reindex_document(self, rag_name: str, doc_id: str) -> bool:
        """
        重新索引文档
        与electron项目reindex_document方法保持完全一致
        """
        try:
            # 获取文档名称
            doc_list = await self.get_rag_doc_list(rag_name)
            doc_name = None
            for doc in doc_list:
                if doc["docId"] == doc_id:
                    doc_name = doc["docName"]
                    break
            
            if not doc_name:
                return False
            
            # 获取文档文件路径
            file_path = await self.get_doc_file_path(rag_name, doc_name)
            if not file_path:
                return False
            
            # 删除旧的索引记录
            from app.rag.rag import Rag
            rag_instance = Rag()
            await rag_instance.remove_document_from_db(rag_name, doc_id)
            
            # 获取知识库配置中的分块参数
            config_path = self._get_rag_config_path(rag_name)
            config = await self._read_json_file(config_path)
            if not config:
                print(f"无法获取知识库配置: {rag_name}")
                return False
            
            # 从配置中获取分块参数，如果不存在则使用默认值
            separators = config.get("separators", ["\n\n", "\n", " "])
            chunk_size = config.get("chunk_size", 1000)
            overlap_size = config.get("overlap_size", 200)
            
            # 重新索引文档 - 使用知识库配置参数
            result = await rag_instance.add_document_to_db(file_path, rag_name, separators, chunk_size, overlap_size)
            return result is not None
        except Exception as e:
            print(f"重新索引文档失败: {e}")
            return False

    async def reindex_rag(self, rag_name: str) -> bool:
        """
        重新索引整个知识库中的所有文档
        """
        success = True
        doc_list = await self.get_rag_doc_list(rag_name)
        for doc in doc_list:
            if not await self.reindex_document(rag_name, doc["docId"]):
                success = False
        return success

    async def search_knowledge_base_multiple(
        self, 
        rag_names: List[str], 
        query: str, 
        limit: int = 5
    ) -> List[SearchResult]:
        """
        在多个知识库中搜索文档
        """
        all_results = []
        for rag_name in rag_names:
            results = await self.search_knowledge_base(rag_name, query, limit)
            all_results.extend(results)
        return all_results

    async def test_chunk(
        self, 
        file_path: str, 
        chunk_size: int = 1000, 
        overlap_size: int = 200, 
        separators: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        测试文档分块效果
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        file_type = "unknown"
        if file_ext == ".pdf": file_type = "pdf"
        elif file_ext == ".txt": file_type = "text"
        elif file_ext in [".doc", ".docx"]: file_type = "word"
        elif file_ext in [".xls", ".xlsx"]: file_type = "excel"
        elif file_ext in [".csv", ".html", ".htm", ".md", ".json", ".log"]:
            file_type = "text"  # 这些文件都按文本处理
        
        chunks = await self._extract_text(file_path, file_type, chunk_size, overlap_size, separators)
        return [chunk.dict() for chunk in chunks]

    async def optimize_table(self, rag_name: str) -> bool:
        """
        优化知识库向量表（占位符）
        """
        return True

    async def get_doc_chunk_list(self, rag_name: str, doc_id: str) -> List[Dict[str, Any]]:
        """
        获取文档分块列表
        """
        rag_path = self._get_rag_path(rag_name)
        markdown_dir = os.path.join(rag_path, "markdown")
        chunks_file_path = os.path.join(markdown_dir, f"{doc_id}.json")

        if os.path.exists(chunks_file_path):
            chunks_data = await self._read_json_file(chunks_file_path)
            if chunks_data:
                return chunks_data
        return []

    async def search_knowledge_base(
        self, 
        kb_id: str, 
        query: str, 
        limit: int = 5
    ) -> List[SearchResult]:
        """
        在知识库中搜索（使用真实向量数据库）
        """
        try:
            # 获取知识库配置
            config_path = self._get_rag_config_path(kb_id)
            config = self._read_json_file_sync(config_path)
            if not config:
                return []
            
            # 使用真实向量数据库进行搜索
            vector_db = lancedb_manager
            
            # 从配置中获取嵌入模型和供应商信息
            supplier_name = config.get('supplierName', 'ollama')
            embedding_model = config.get('embeddingModel', 'bge-m3:latest')
            
            # 生成查询向量
            query_embedding = await self.embedding_service.get_embedding(supplier_name, embedding_model, query)
            if query_embedding is None:
                self.logger.warning(f"生成查询向量失败: {query}")
                return []
            
            # 生成关键词
            from app.rag.utils import PubUtils
            keywords = PubUtils.cut_for_search(query)
            
            # 使用MD5处理表名
            import hashlib
            table_name = hashlib.md5(kb_id.encode('utf-8')).hexdigest()
            
            # 执行向量搜索
            search_results = await vector_db.search_vectors(
                table_name=table_name,
                supplier_name="ollama",
                model_name="nomic-embed-text", 
                query_text=query,
                top_k=limit
            )
            
            # 格式化搜索结果
            formatted_results = []
            for result in search_results:
                formatted_results.append(SearchResult(
                    text=result.get('text', ''),
                    metadata=result.get('metadata', {}),
                    score=result.get('score', 0.0)
                ))
            
            self.logger.info(f"知识库搜索完成: {kb_id}, 查询: {query}, 结果数: {len(formatted_results)}")
            return formatted_results
            
        except Exception as e:
            self.logger.error(f"知识库搜索失败: {kb_id}, 查询: {query}, 错误: {e}")
            return []

    async def _extract_text(
        self, 
        file_path: str, 
        file_type: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        doc_id: Optional[str] = None
    ) -> List[TextChunk]:
        """异步版本，调用同步版本"""
        return self._extract_text_sync(file_path, file_type, chunk_size, chunk_overlap, separators, doc_id)
    
    def _extract_text_sync(
        self, 
        file_path: str, 
        file_type: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None,
        doc_id: Optional[str] = None
    ) -> List[TextChunk]:
        """同步版本，用于后台任务处理"""
        text = ""
        
        # 使用新的文档解析器
        try:
            if is_supported_file_type(file_path):
                result = parse_document(file_path)
                if result['success']:
                    text = result['content']
                else:
                    text = f"文档解析失败: {result['error']}"
            else:
                # 回退到原始实现
                if file_type == "pdf":
                    with fitz.open(file_path) as doc:
                        for page in doc:
                            text += page.get_text()
                elif file_type == "text":
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()
                else:
                    text = f"不支持的文件类型: {file_type}"
        except Exception as e:
            text = f"文档解析异常: {str(e)}"
        
        if separators is None:
            separators = ["\n\n", "\n", " "]

        doc_id_from_path = doc_id or os.path.splitext(os.path.basename(file_path))[0].split('_', 1)[0]
        return self._create_chunks_sync(text, doc_id_from_path, chunk_size, chunk_overlap, separators)

    def _create_chunks(
        self, 
        text: str, 
        doc_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ) -> List[TextChunk]:
        """异步版本，调用同步版本"""
        return self._create_chunks_sync(text, doc_id, chunk_size, chunk_overlap, separators)
    
    def _create_chunks_sync(
        self, 
        text: str, 
        doc_id: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ) -> List[TextChunk]:
        """同步版本，用于后台任务处理"""
        chunks = []
        if not text: return chunks

        if separators is None:
            separators = ["\n\n", "\n", " "]

        # 过滤掉空字符串分隔符，避免分割异常
        separators = [sep for sep in separators if sep.strip()]
        if not separators:
            separators = ["\n\n", "\n", " "]

        current_chunk = ""
        current_length = 0
        
        parts = [text]
        for sep in separators:
            new_parts = []
            for part in parts:
                new_parts.extend(part.split(sep))
            parts = new_parts
        
        parts = [p.strip() for p in parts if p.strip()]

        for part in parts:
            if current_length + len(part) + len(separators[0]) <= chunk_size:
                current_chunk += (part + separators[0])
                current_length += len(part) + len(separators[0])
            else:
                if current_chunk.strip():
                    chunks.append(TextChunk(
                        id=str(uuid.uuid4()),
                        document_id=doc_id,
                        text=current_chunk.strip(),
                        metadata={}
                    ))
                current_chunk = part + separators[0]
                current_length = len(part) + len(separators[0])

                if current_length > chunk_size and chunk_overlap > 0:
                    sub_chunks = self._create_chunks_sync(part, doc_id, chunk_size, chunk_overlap, separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                    current_length = 0
                    
        if current_chunk.strip():
            chunks.append(TextChunk(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                text=current_chunk.strip(),
                metadata={}
            ))
            
        return chunks