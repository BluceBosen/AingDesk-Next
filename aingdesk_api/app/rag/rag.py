import os
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor

# 只使用新的真实向量数据库实现
from app.rag.vector_lancedb import lancedb_manager
from .utils import PubUtils

class Rag:
    """
    RAG（检索增强生成）类
    使用新的vector_db_real实现，完全替换旧的vector_db
    """
    
    def __init__(self):
        self.doc_table = 'doc_table'
    
    async def check_doc_table(self, table_name: str) -> bool:
        """
        检查文档表是否存在（使用新的真实向量数据库）
        """
        return lancedb_manager.table_exists(table_name)
    
    async def create_doc_table(self, table_name: str, supplier_name: str = "default", model: str = "default", initial_text: str = "初始文档") -> bool:
        """
        创建文档表（使用文档记录表结构，与向量表结构不同）
        """
        try:
            await lancedb_manager.create_doc_table(table_name)
            return True
        except Exception as e:
            print(f"创建文档表失败: {e}")
            return False
    
    async def check_doc_table_schema(self, table_name: str) -> bool:
        """
        检查文档表结构是否符合要求（使用新的真实向量数据库）
        """
        try:
            # 检查表是否存在
            if not await lancedb_manager.table_exists(table_name):
                return False
            
            # 获取表信息
            table_info = await lancedb_manager.get_table_info_async(table_name)
            
            # 检查必要的字段和结构
            required_fields = ['name', 'supplier_name', 'model', 'dimension', 'created_at', 'records']
            for field in required_fields:
                if field not in table_info:
                    return False
            
            # 检查维度是否合理（通常在100-2000之间）
            dimension = table_info.get('dimension', 0)
            if dimension < 100 or dimension > 2000:
                return False
            
            # 检查供应商和模型是否有效
            supplier_name = table_info.get('supplier_name', '')
            model = table_info.get('model', '')
            if not supplier_name or not model:
                return False
            
            return True
            
        except Exception as e:
            print(f"检查文档表结构失败: {e}")
            return False
    
    async def add_document_to_db(self, filename: str, rag_name: str, separators: List[str], chunk_size: int, overlap_size: int) -> Dict[str, Any]:
        """
        添加文档到数据库（使用新的真实向量数据库）
        """
        try:
            # 解析文件路径
            filename = os.path.abspath(filename)
            
            # 确保文档表存在
            await self.create_doc_table(self.doc_table)
            await self.check_doc_table_schema(self.doc_table)
            
            # 获取数据路径
            data_dir = PubUtils.get_data_path()
            rep_data_dir = '{DATA_DIR}'
            
            # 构建文档记录
            doc_record = {
                'doc_id': PubUtils.uuid(),
                'doc_name': os.path.basename(filename),
                'doc_file': filename.replace(data_dir, rep_data_dir),
                'md_file': '',
                'doc_rag': rag_name,
                'doc_abstract': '',
                'doc_keywords': [],
                'is_parsed': 0,
                'update_time': PubUtils.time(),
                'separators': separators,
                'chunk_size': chunk_size,
                'overlap_size': overlap_size,
            }
            
            # 添加记录到数据库（使用新的真实向量数据库）
            success = await lancedb_manager.add_record_async(self.doc_table, doc_record)
            
            if success:
                return doc_record
            else:
                raise Exception("添加文档记录失败")
                
        except Exception as e:
            raise Exception(f"添加文档到数据库失败: {str(e)}")
    
    async def get_rag_info(self, rag_name: str) -> Optional[Dict[str, Any]]:
        """
        获取知识库信息
        """
        try:
            rag_path = os.path.join(PubUtils.get_rag_path(), rag_name)
            config_file = os.path.join(rag_path, "config.json")
            
            if not os.path.exists(config_file):
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                rag_info = json.load(f)
            
            return rag_info
            
        except Exception as e:
            print(f"获取知识库信息失败: {e}")
            return None
    
    async def search_document(self, rag_list: List[str], query_text: str) -> List[Dict[str, Any]]:
        """
        搜索文档（与electron项目保持一致）
        使用真实向量数据库进行文档检索
        """
        try:
            # 生成关键词
            keywords = PubUtils.cut_for_search(query_text)
            
            # 并行执行所有知识库的检索请求
            search_tasks = []
            for rag_name in rag_list:
                rag_info = await self.get_rag_info(rag_name)
                if rag_info:
                    table_name = PubUtils.md5(rag_name)
                    task = self._search_single_rag(table_name, rag_info, query_text, keywords)
                    search_tasks.append(task)
            
            # 等待所有检索完成并合并结果
            if search_tasks:
                results = await asyncio.gather(*search_tasks, return_exceptions=True)
                # 过滤异常结果并扁平化
                flat_results = []
                for result in results:
                    if isinstance(result, list):
                        flat_results.extend(result)
                return flat_results
            else:
                return []
                
        except Exception as e:
            return []
    
    async def _search_single_rag(self, table_name: str, rag_info: Dict[str, Any], query_text: str, keywords: List[str]) -> List[Dict[str, Any]]:
        """
        在单个知识库中检索（使用真实向量数据库）
        支持 searchStrategy/maxRecall/recallAccuracy/vectorWeight/keywordWeight 配置
        """
        try:
            # 使用真实向量数据库进行搜索
            from app.rag.vector_lancedb import LanceDBManager
            from app.services.embedding_service import EmbeddingService
            
            vector_db = LanceDBManager()
            embedding_service = EmbeddingService()
            
            # 从rag_info获取嵌入模型和供应商信息
            supplier_name = rag_info.get('supplierName', 'ollama')
            embedding_model = rag_info.get('embeddingModel', 'bge-m3:latest')
            search_strategy = rag_info.get('searchStrategy', 2)
            max_recall = rag_info.get('maxRecall', 5)
            recall_accuracy = rag_info.get('recallAccuracy', 0.1)
            vector_weight = rag_info.get('vectorWeight', 0.7)
            keyword_weight = rag_info.get('keywordWeight', 0.3)

            # 生成查询向量
            query_embedding = await embedding_service.get_embedding(supplier_name, embedding_model, query_text)
            if query_embedding is None:
                return []

            if search_strategy == 3:
                # 全文检索：当前 LanceDBManager 未实现 FTS，暂时回退到向量检索
                self.logger.warning(f"知识库 {table_name} 配置为全文检索，但当前未实现 FTS，回退到向量检索")

            # 向量搜索，获取更多候选结果以便后续过滤/重排
            search_limit = max(max_recall * 3, 20)
            search_results = await vector_db.search_vectors(
                table_name=table_name,
                query_vector=query_embedding,
                top_k=search_limit
            )

            if not search_results:
                return []

            # 归一化权重
            total_weight = vector_weight + keyword_weight
            if total_weight > 0:
                vector_weight = vector_weight / total_weight
                keyword_weight = keyword_weight / total_weight
            else:
                vector_weight, keyword_weight = 1.0, 0.0

            # 计算综合得分
            formatted_results = []
            for result in search_results:
                text = result.get('doc', '')
                distance = result.get('_distance', 0.0)
                # 将 L2 distance 映射到 [0, 1] 相似度，越大越相似
                vector_similarity = 1.0 / (1.0 + float(distance))

                # 召回精度过滤
                if vector_similarity < recall_accuracy:
                    continue

                keyword_score = 0.0
                if keywords and keyword_weight > 0 and search_strategy in (1, 3):
                    text_lower = text.lower()
                    match_count = sum(1 for kw in keywords if kw.lower() in text_lower)
                    keyword_score = match_count / len(keywords)

                # 混合检索才融合关键词得分；纯向量检索只用向量相似度
                if search_strategy == 1:
                    final_score = vector_similarity * vector_weight + keyword_score * keyword_weight
                else:
                    final_score = vector_similarity

                formatted_results.append({
                    'id': result.get('id', ''),
                    'text': text,
                    'score': final_score,
                    'vector_similarity': vector_similarity,
                    'keyword_score': keyword_score,
                    'metadata': result.get('metadata', {}),
                    'rag_name': table_name
                })

            # 按综合得分降序排序
            formatted_results.sort(key=lambda x: x['score'], reverse=True)

            # 限制返回结果数量
            return formatted_results[:max_recall]

        except Exception as e:
            self.logger.error(f"知识库检索失败: {table_name}, 错误: {e}")
            return []
    
    async def remove_rag_document(self, rag_name: str, doc_id: str) -> bool:
        """
        从知识库中移除文档（使用新的真实向量数据库）
        """
        try:
            # 1. 从文档表中删除记录（使用新的真实向量数据库）
            success = await lancedb_manager.delete_record_async(self.doc_table, f"doc_id='{doc_id}' AND doc_rag='{rag_name}'")
            if not success:
                return False
            
            # 2. 从向量数据库中删除相关向量记录
            table_name = PubUtils.md5(rag_name)
            
            # 删除向量数据库中该文档的所有向量记录
            vector_delete_success = await lancedb_manager.delete_record_async(table_name, doc_id)
            if not vector_delete_success:
                print(f"从向量数据库删除记录失败: doc_id={doc_id}, table_name={table_name}")
                # 即使向量删除失败，也继续尝试删除文件
            
            # 3. 删除相关的文件（包括原始文档、解析后的文本文件等）
            data_dir = PubUtils.get_data_path()
            
            # 获取知识库路径
            rag_path = os.path.join(PubUtils.get_rag_path(), rag_name)
            
            # 删除文档相关的文件
            doc_files = [
                os.path.join(rag_path, "docs", f"{doc_id}.json"),  # 文档元数据
                os.path.join(rag_path, "docs", f"{doc_id}_chunks.json"),  # 文档分块
                os.path.join(rag_path, "docs", f"{doc_id}_text.txt"),  # 文档文本
            ]
            
            for file_path in doc_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"删除文件失败: {file_path}, 错误: {e}")
            
            # 4. 更新知识库配置（如果需要）
            config_file = os.path.join(rag_path, "config.json")
            if os.path.exists(config_file):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 如果配置中有文档计数，更新它
                    if 'doc_count' in config:
                        config['doc_count'] = max(0, config.get('doc_count', 1) - 1)
                        
                        with open(config_file, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=2)
                        
                except Exception as e:
                    print(f"更新知识库配置失败: {e}")
            
            return True
            
        except Exception as e:
            print(f"移除文档失败: {e}")
            return False
    
    async def remove_rag(self, rag_name: str) -> bool:
        """
        删除整个知识库（使用新的真实向量数据库）
        """
        try:
            # 删除知识库目录
            rag_path = os.path.join(PubUtils.get_rag_path(), rag_name)
            if os.path.exists(rag_path):
                import shutil
                shutil.rmtree(rag_path)

            # 删除向量数据库表（使用新的真实向量数据库）
            table_name = PubUtils.md5(rag_name)
            await lancedb_manager.delete_table_async(table_name)
            
            # 从文档表中删除相关记录（使用新的真实向量数据库）
            await lancedb_manager.delete_record_async(self.doc_table, f"doc_rag='{rag_name}'")
            
            return True
        except Exception as e:
            return False
    
    async def reindex_rag(self, rag_name: str) -> bool:
        """
        重新索引整个知识库中的所有文档（使用新的真实向量数据库）
        """
        try:
            # 获取知识库中的所有文档列表
            from app.services.rag_service import RagService
            rag_service = RagService()
            
            doc_list = await rag_service.get_rag_doc_list(rag_name)
            if not doc_list:
                return True
            
            success_count = 0
            total_count = len(doc_list)
            
            # 逐个重新索引文档
            for doc in doc_list:
                try:
                    doc_name = doc.get("docName", "")
                    doc_id = doc.get("docId", "")
                    
                    if doc_name and doc_id:
                        # 获取文档文件路径
                        file_path = await rag_service.get_doc_file_path(rag_name, doc_name)
                        if file_path and os.path.exists(file_path):
                            # 删除旧的索引记录
                            await self.remove_rag_document(rag_name, doc_id)
                            
                            # 重新索引文档
                            result = await self.add_document_to_db(
                                filename=file_path,
                                rag_name=rag_name,
                                separators=["\n\n", "\n", " "],
                                chunk_size=1000,
                                overlap_size=200
                            )
                            
                            if result:
                                success_count += 1
                            else:
                                pass
                        else:
                            pass
                    else:
                        pass
                        
                except Exception as e:
                    continue
            
            return success_count == total_count
            
        except Exception as e:
            return False
    
    async def generate_keywords(self, doc: str, num: int = 5) -> List[str]:
        """
        生成关键词
        """
        try:
            # 简单的关键词提取实现
            words = PubUtils.cut_for_search(doc)
            # 按词频排序并返回前num个
            from collections import Counter
            word_counts = Counter(words)
            return [word for word, count in word_counts.most_common(num)]
        except Exception as e:
            return []
    
    async def generate_abstract(self, doc: str) -> str:
        """
        生成摘要
        """
        try:
            # 简单的摘要生成实现 - 取前200个字符
            return doc[:200] + "..." if len(doc) > 200 else doc
        except Exception as e:
            print(f"生成摘要失败: {e}")
            return ""
    
    async def get_doc_name_by_doc_id(self, doc_id: str) -> str:
        """
        根据文档ID获取文档名称（使用新的真实向量数据库）
        """
        try:
            records = lancedb_manager.query_record(self.doc_table, f"doc_id='{doc_id}'")
            if records:
                return records[0].get('doc_name', '')
            return ''
        except Exception as e:
            print(f"获取文档名称失败: {e}")
            return ""
    
    async def remove_document_from_db(self, rag_name: str, doc_id: str) -> bool:
        """
        从数据库中删除文档（使用新的真实向量数据库）
        对应electron中的deleteDocumentFromDB方法
        """
        try:
            # 从文档表中删除记录
            success = await lancedb_manager.delete_record_async(self.doc_table, f"doc_id='{doc_id}'")
            if not success:
                return False
            
            # 从向量数据库中删除相关向量记录
            table_name = PubUtils.md5(rag_name)
            vector_delete_success = await lancedb_manager.delete_record_async(table_name, doc_id)
            
            return True
        except Exception as e:
            print(f"从数据库删除文档失败: {e}")
            return False