import os
import json
import uuid
import lancedb
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class LanceDBManager:
    """
    真正的LanceDB向量数据库管理器
    使用lancedb库实现，与Electron版本保持一致
    """
    
    # 默认嵌入维度，与Electron版本保持一致
    DIMENSION = 1024
    
    def __init__(self):
        self.db_path = self.get_db_path()
        self.embedding_service = EmbeddingService()
        self.dimension = None
    
    def get_db_path(self) -> str:
        """获取数据库路径"""
        import os
        # 使用项目根目录下的data文件夹
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.join(project_root, 'data', 'rag', 'vector_db_real')
    
    def get_electron_table_name(self, rag_name: str) -> str:
        """
        获取electron格式的表名（MD5哈希）
        electron使用知识库名称的MD5哈希作为向量表名
        """
        import hashlib
        return hashlib.md5(rag_name.encode('utf-8')).hexdigest()
    
    def ensure_database_directory(self) -> None:
        """确保数据库目录存在"""
        os.makedirs(self.db_path, exist_ok=True)
    
    async def table_exists(self, table_name: str) -> bool:
        """
        检查表是否存在 - 使用真正的LanceDB API
        注意：electron使用MD5哈希作为向量表名，所以这里需要检查MD5哈希值
        """
        try:
            self.ensure_database_directory()
            
            # 使用同步连接检查表存在性
            db = lancedb.connect(self.db_path)
            tables = db.table_names()
            
            # 检查原始表名和MD5哈希表名
            if table_name in tables:
                return True
                
            # 如果原始表名不存在，检查MD5哈希版本（兼容electron）
            import hashlib
            md5_table_name = hashlib.md5(table_name.encode('utf-8')).hexdigest()
            if md5_table_name in tables:
                return True
            
            return False
        except Exception as e:
            logger.error(f"检查表存在性失败: {str(e)}")
            # 如果LanceDB API失败，回退到文件系统检查
            import os
            import hashlib
            db_path = os.path.join(self.db_path, table_name + '.lance')
            if os.path.exists(db_path):
                return True
                
            # 检查MD5哈希版本
            md5_table_name = hashlib.md5(table_name.encode('utf-8')).hexdigest()
            md5_db_path = os.path.join(self.db_path, md5_table_name + '.lance')
            return os.path.exists(md5_db_path)
    
    def table_exists_sync(self, table_name: str) -> bool:
        """
        同步版本：检查表是否存在
        """
        import asyncio
        import hashlib
        
        try:
            # 检查当前是否已有事件循环在运行
            try:
                loop = asyncio.get_running_loop()
                # 如果已有事件循环在运行，我们不能直接创建新的循环
                logger.warning(f"已有事件循环在运行，使用简单方式检查表存在性")
                
                # 使用简单的方式：直接检查文件系统
                import os
                db_path = os.path.join(self.db_path, table_name + '.lance')
                if os.path.exists(db_path):
                    return True
                    
                # 检查MD5哈希版本
                md5_table_name = hashlib.md5(table_name.encode('utf-8')).hexdigest()
                md5_db_path = os.path.join(self.db_path, md5_table_name + '.lance')
                return os.path.exists(md5_db_path)
                
            except RuntimeError:
                # 没有运行的事件循环，可以安全创建新的
                pass
            
            # 使用新的事件循环避免"Event loop is closed"错误
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def _table_exists():
                try:
                    self.ensure_database_directory()
                    db = await lancedb.connect_async(self.db_path)
                    tables = await db.table_names()
                    
                    # 检查原始表名和MD5哈希表名
                    if table_name in tables:
                        await db.close()
                        return True
                        
                    # 如果原始表名不存在，检查MD5哈希版本（兼容electron）
                    md5_table_name = hashlib.md5(table_name.encode('utf-8')).hexdigest()
                    result = md5_table_name in tables
                    
                    await db.close()
                    return result
                except Exception as e:
                    logger.error(f"检查表存在性失败: {str(e)}")
                    return False
            
            result = loop.run_until_complete(_table_exists())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"同步检查表存在性失败: {str(e)}")
            return False
    
    async def create_table(self, table_name: str, supplier_name: str, model: str, initial_text: str) -> str:
        """
        创建向量数据库表 - 使用真正的LanceDB API
        """
        try:
            self.ensure_database_directory()
            
            # 使用同步连接创建表
            import lancedb
            db = lancedb.connect(self.db_path)
            
            # 检查表是否已存在
            tables = db.table_names()
            if table_name in tables:
                return table_name  # 表已存在，直接返回
            
            # 使用默认的1024维向量（与Electron版本保持一致）
            embedding = [0.1] * self.DIMENSION
            
            # 更新维度信息
            self.dimension = len(embedding)
            self.embedding_service.set_dimension(self.dimension)
            
            # 创建表结构（与Electron版本保持一致）
            initial_data = [{
                "id": "1",
                "doc": initial_text,
                "vector": embedding,
                "docId": "0",
                "tokens": initial_text,
                "keywords": ["keyword1", "keyword2"]
            }]
            
            # 创建表
            table_obj = db.create_table(table_name, initial_data)
            
            # 删除初始记录
            table_obj.delete("id='1'")
            
            logger.info(f"成功创建向量数据库表: {table_name}")
            return table_name
            
        except Exception as e:
            logger.error(f"创建向量数据库表失败: {str(e)}")
            raise Exception(f"创建向量数据库表失败: {str(e)}")

    async def create_doc_table(self, table_name: str = "doc_table") -> str:
        """
        创建文档记录表 - 与向量表结构不同，使用宽表结构存储文档元数据
        """
        try:
            self.ensure_database_directory()

            import lancedb
            db = lancedb.connect(self.db_path)
            tables = db.table_names()

            # 如果表已存在，检查结构是否符合文档记录表要求
            if table_name in tables:
                try:
                    table_obj = db.open_table(table_name)
                    schema_fields = [field.name for field in table_obj.schema]

                    # 检查必要字段是否存在且类型正确（不能是 null 类型）
                    required_string_fields = ["doc_id", "doc_name", "doc_file", "md_file", "doc_rag", "doc_abstract"]
                    has_valid_string_fields = all(
                        field in schema_fields and "null" not in str(table_obj.schema.field(field).type).lower()
                        for field in required_string_fields
                    )

                    has_list_fields = False
                    try:
                        keywords_type = str(table_obj.schema.field("doc_keywords").type)
                        separators_type = str(table_obj.schema.field("separators").type)
                        has_list_fields = "list" in keywords_type and "list" in separators_type
                    except Exception:
                        has_list_fields = False

                    if has_valid_string_fields and has_list_fields:
                        logger.info(f"文档记录表已存在且结构正确: {table_name}")
                        return table_name
                    else:
                        # 结构不匹配（旧向量表结构、null 类型字段或列表类型推断错误），删除重建
                        logger.warning(f"文档记录表结构不匹配，删除重建: {table_name}")
                        db.drop_table(table_name)
                except Exception as e:
                    logger.warning(f"检查文档记录表结构失败，尝试删除重建: {e}")
                    try:
                        db.drop_table(table_name)
                    except Exception:
                        pass

            # 创建文档记录表，初始数据定义 schema
            initial_data = [{
                "doc_id": "0",
                "doc_name": "initial",
                "doc_file": "placeholder",
                "md_file": "placeholder",
                "doc_rag": "placeholder",
                "doc_abstract": "initial abstract",
                "doc_keywords": ["keyword1"],
                "is_parsed": 0,
                "update_time": 0,
                "separators": ["\n\n"],
                "chunk_size": 0,
                "overlap_size": 0
            }]

            table_obj = db.create_table(table_name, initial_data)
            table_obj.delete("doc_id='0'")

            logger.info(f"成功创建文档记录表: {table_name}")
            return table_name

        except Exception as e:
            logger.error(f"创建文档记录表失败: {str(e)}")
            raise Exception(f"创建文档记录表失败: {str(e)}")

    async def add_vectors(self, table_name: str, vectors: List[Dict[str, Any]]) -> bool:
        """
        添加向量到表 - 使用真正的LanceDB API
        """
        try:
            self.ensure_database_directory()
            
            # 连接数据库
            db = await lancedb.connect_async(self.db_path)
            
            # 检查表是否存在
            if not await self.table_exists(table_name):
                raise Exception(f"表 '{table_name}' 不存在")
            
            # 打开表
            table_obj = await db.open_table(table_name)
            
            if not table_obj:
                raise Exception(f"无法打开表 '{table_name}'")
            
            # 准备数据
            records = []
            for vector_data in vectors:
                record = {
                    "id": vector_data.get("id", str(uuid.uuid4())),
                    "doc": vector_data.get("doc", ""),
                    "docId": vector_data.get("doc_id", ""),
                    "chunk_id": vector_data.get("chunk_id", ""),
                    "vector": vector_data.get("vector", []),
                    "keywords": vector_data.get("keywords", []),
                    "metadata": vector_data.get("metadata", {}),
                    "tokens": vector_data.get("doc", "")  # 用于全文搜索
                }
                records.append(record)
            
            # 添加记录
            logger.info(f"准备添加 {len(records)} 条记录到表 {table_name}")
            await table_obj.add(records)
            
            logger.info(f"成功添加 {len(vectors)} 个向量到表 {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"添加向量失败: {str(e)}")
            return False
    
    def add_vectors_sync(self, table_name: str, vectors: List[Dict[str, Any]]) -> bool:
        """
        同步版本：添加向量到表
        """
        import asyncio
        try:
            return asyncio.run(self.add_vectors(table_name, vectors))
        except Exception as e:
            logger.error(f"同步添加向量失败: {str(e)}")
            return False
    
    async def search_vectors(self, table_name: str, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        搜索相似向量 - 使用真正的LanceDB API
        """
        try:
            self.ensure_database_directory()
            
            # 连接数据库
            db = await lancedb.connect_async(self.db_path)
            
            # 检查表是否存在
            if not await self.table_exists(table_name):
                logger.warning(f"表 '{table_name}' 不存在")
                return []
            
            # 打开表
            table_obj = await db.open_table(table_name)
            
            if not table_obj:
                logger.warning(f"无法打开表 '{table_name}'")
                return []
            
            # 执行向量搜索
            results = await table_obj.vector_search(query_vector).limit(top_k).to_list()
            
            # 格式化结果
            formatted_results = []
            for result in results:
                formatted_result = {
                    "id": result.get("id", ""),
                    "doc": result.get("doc", ""),
                    "doc_id": result.get("docId", ""),
                    "chunk_id": result.get("chunk_id", ""),
                    "keywords": result.get("keywords", []),
                    "metadata": result.get("metadata", {}),
                    "score": result.get("_distance", 0.0)
                }
                formatted_results.append(formatted_result)
            
            logger.info(f"在表 {table_name} 中找到 {len(formatted_results)} 个相似向量")
            return formatted_results
            
        except Exception as e:
            logger.error(f"搜索向量失败: {str(e)}")
            return []
    
    async def search(self, query_vector: List[float], query_text: str, keywords: List[str] = None,
                    limit: int = 5, vector_weight: float = 0.7, keyword_weight: float = 0.3) -> List[Dict[str, Any]]:
        """
        混合搜索（向量和关键词）
        
        注意：此方法需要在调用时传入正确的表名，通过search_vectors方法参数传递
        """
        try:
            logger.error("search方法需要指定表名，请使用search_vectors方法代替")
            return []
        except Exception as e:
            logger.error(f"混合搜索失败: {str(e)}")
            return []
    
    async def delete_table_async(self, table_name: str) -> bool:
        """
        删除表 - 纯异步版本
        """
        try:
            # 使用异步方式检查表是否存在
            if not await self.table_exists(table_name):
                return True  # 表不存在也算删除成功

            import hashlib
            import shutil

            db = await lancedb.connect_async(self.db_path)
            dropped_names = []

            # 检查原始表名
            tables = await db.table_names()
            if table_name in tables:
                await db.drop_table(table_name)
                dropped_names.append(table_name)

            # 检查MD5哈希版本（兼容electron）
            md5_table_name = hashlib.md5(table_name.encode('utf-8')).hexdigest()
            if md5_table_name in tables:
                await db.drop_table(md5_table_name)
                dropped_names.append(md5_table_name)

            await db.close()

            if not dropped_names:
                logger.warning(f"向量表不存在: {table_name}")
                return False

            # 强制删除底层 .lance 目录，避免 LanceDB 残留文件
            for name in dropped_names:
                try:
                    lance_dir = os.path.join(self.db_path, f"{name}.lance")
                    if os.path.exists(lance_dir):
                        shutil.rmtree(lance_dir)
                        logger.info(f"已删除向量表底层目录: {lance_dir}")
                except Exception as clean_e:
                    logger.warning(f"删除向量表底层目录失败: {clean_e}")

            logger.info(f"成功删除向量表: {table_name}")
            return True

        except Exception as e:
            logger.error(f"删除向量表失败: {table_name}, 错误: {str(e)}")
            return False
    
    async def query_record_async(self, table_name: str, condition: str) -> List[Dict[str, Any]]:
        """
        查询记录 - 纯异步实现
        """
        try:
            if not await self.table_exists(table_name):
                logger.warning(f"表不存在: {table_name}")
                return []
            
            # 使用同步连接进行查询
            import lancedb
            db = lancedb.connect(self.db_path)
            table_obj = db.open_table(table_name)
            
            # 使用to_pandas获取所有数据，然后根据条件筛选
            import pandas as pd
            df = table_obj.to_pandas()
            
            # 解析条件并筛选数据
            # 简单的条件解析：docId='test_doc_123'
            if "=" in condition:
                field, value = condition.split("=")
                field = field.strip()
                value = value.strip().strip("'")
                
                # 筛选数据
                if field in df.columns:
                    filtered_df = df[df[field] == value]
                    results = filtered_df.to_dict('records')
                else:
                    logger.warning(f"字段 {field} 不存在于表中")
                    results = []
            else:
                results = []
            
            logger.info(f"成功查询记录: {table_name}, 条件: {condition}, 结果数: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"查询记录失败: {table_name}, 条件: {condition}, 错误: {str(e)}")
            return []
    
    def query_record(self, table_name: str, condition: str) -> List[Dict[str, Any]]:
        """
        查询记录 - 同步版本 (已废弃，仅用于向后兼容)
        """
        logger.warning("query_record 同步方法已废弃，请使用 query_record_async 异步方法")
        return []
    
    async def add_vectors_async(self, table_name: str, vectors: List[Dict[str, Any]]) -> bool:
        """
        添加向量到向量数据库（兼容rag_service.py中的调用）
        """
        try:
            if not await self.table_exists(table_name):
                logger.warning(f"表不存在: {table_name}")
                return False
            
            # 使用同步连接进行添加
            import lancedb
            db = lancedb.connect(self.db_path)
            table_obj = db.open_table(table_name)
            
            # 转换数据格式以匹配表结构
            formatted_vectors = []
            for vector_data in vectors:
                formatted_data = {
                    "id": vector_data.get("id", ""),
                    "doc": vector_data.get("doc", ""),
                    "vector": vector_data.get("vector", []),
                    "docId": vector_data.get("doc_id", ""),
                    "tokens": vector_data.get("doc", ""),  # 使用doc作为tokens
                    "keywords": vector_data.get("metadata", {}).get("keywords", []) if isinstance(vector_data.get("metadata"), dict) else []
                }
                formatted_vectors.append(formatted_data)
            
            # 批量添加记录
            if formatted_vectors:
                table_obj.add(formatted_vectors)
                logger.info(f"成功添加 {len(formatted_vectors)} 个向量到表: {table_name}")
                return True
            else:
                logger.warning(f"没有有效的向量数据需要添加")
                return False
                
        except Exception as e:
            logger.error(f"添加向量失败: {table_name}, 错误: {str(e)}")
            return False
    
    async def add_record_async(self, table_name: str, data: dict) -> bool:
        """
        添加记录 - 纯异步实现
        """
        try:
            if not await self.table_exists(table_name):
                logger.warning(f"表不存在: {table_name}")
                return False
            
            # 使用同步连接进行添加
            import lancedb
            db = lancedb.connect(self.db_path)
            table_obj = db.open_table(table_name)
            
            # 清理记录中的 None 值，避免 LanceDB 写入失败
            cleaned_data = {}
            for key, value in data.items():
                if value is None:
                    if key in ('doc_keywords', 'separators'):
                        cleaned_data[key] = []
                    elif key in ('is_parsed', 'update_time', 'chunk_size', 'overlap_size'):
                        cleaned_data[key] = 0
                    else:
                        cleaned_data[key] = ''
                else:
                    cleaned_data[key] = value

            # 添加记录
            table_obj.add([cleaned_data])

            logger.info(f"成功添加记录: {table_name}")
            return True
            
        except Exception as e:
            logger.error(f"添加记录失败: {table_name}, 错误: {str(e)}")
            try:
                logger.error(f"待写入数据: {cleaned_data}")
                if table_obj:
                    logger.error(f"表结构: {table_obj.schema}")
            except Exception:
                pass
            return False
    
    async def delete_record_async(self, table_name: str, condition: str) -> bool:
        """
        删除记录 - 纯异步实现
        """
        try:
            if not await self.table_exists(table_name):
                logger.warning(f"表不存在: {table_name}")
                return False
            
            # 使用同步连接进行删除
            import lancedb
            db = lancedb.connect(self.db_path)
            table_obj = db.open_table(table_name)
            
            # 解析条件并删除记录
            # 简单的条件解析：docId='test_doc_123'
            if "=" in condition:
                field, value = condition.split("=")
                field = field.strip()
                value = value.strip().strip("'")
                
                # 构建删除条件 - 使用正确的字段名，注意字段名的大小写
                if field.lower() == "docid":
                    field = "docId"  # 使用正确的字段名
                
                # 使用正确的引号格式
                delete_condition = f'{field} = "{value}"'
                logger.info(f"尝试删除条件: {delete_condition}")
                
                # 先尝试直接删除
                try:
                    table_obj.delete(delete_condition)
                    logger.info(f"成功删除记录: {table_name}, 条件: {delete_condition}")
                    return True
                except Exception as delete_e:
                    logger.warning(f"第一次删除尝试失败: {str(delete_e)}")
                    
                    # 尝试使用不同的引号格式
                    alt_condition = f"{field} = '{value}'"
                    logger.info(f"尝试替代条件: {alt_condition}")
                    try:
                        table_obj.delete(alt_condition)
                        logger.info(f"成功删除记录: {table_name}, 条件: {alt_condition}")
                        return True
                    except Exception as alt_e:
                        logger.warning(f"第二次删除尝试失败: {str(alt_e)}")
                        
                        # 尝试使用原始条件格式
                        logger.info(f"尝试原始条件: {condition}")
                        try:
                            table_obj.delete(condition)
                            logger.info(f"成功删除记录: {table_name}, 条件: {condition}")
                            return True
                        except Exception as orig_e:
                            logger.warning(f"第三次删除尝试失败: {str(orig_e)}")
                            
                            # 尝试使用SQL表达式格式
                            sql_condition = f'"{field}" = \'{value}\''
                            logger.info(f"尝试SQL条件: {sql_condition}")
                            table_obj.delete(sql_condition)
                            logger.info(f"成功删除记录: {table_name}, 条件: {sql_condition}")
                            return True
            else:
                logger.error(f"无法解析删除条件: {condition}")
                return False
            
        except Exception as e:
            logger.error(f"删除记录失败: {table_name}, 条件: {condition}, 错误: {str(e)}")
            return False
    
    async def get_table_info_async(self, table_name: str) -> Dict[str, Any]:
        """
        获取表信息 - 纯异步实现
        """
        try:
            if not await self.table_exists(table_name):
                logger.warning(f"表不存在: {table_name}")
                return {}
            
            db = await lancedb.connect_async(self.db_path)
            table_obj = await db.open_table(table_name)
            
            # 获取表信息
            info = {
                "name": table_name,
                "count": await table_obj.count_rows(),
                "schema": str(table_obj.schema)
            }
            
            await db.close()
            logger.info(f"成功获取表信息: {table_name}, 记录数: {info['count']}")
            return info
            
        except Exception as e:
            logger.error(f"获取表信息失败: {table_name}, 错误: {str(e)}")
            return {}
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        获取表信息 - 同步版本 (已废弃，仅用于向后兼容)
        """
        logger.warning("get_table_info 同步方法已废弃，请使用 get_table_info_async 异步方法")
        return {}


# 创建全局实例
lancedb_manager = LanceDBManager()