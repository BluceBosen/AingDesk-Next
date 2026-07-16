from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, Depends
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
import os
import json
import tempfile
from app.services.model_service import ModelService
from app.services.rag_service import RagService
from app.services.ollama_service import OllamaService
from app.core.config import settings
from app.models.response import ResponseHandler
from app.rag.rag import Rag
from app.rag.utils import PubUtils
from app.rag.vector_lancedb import LanceDBManager
from app.services.task_manager import task_manager, TaskType

router = APIRouter(tags=["rag"])
rag_service = RagService()
model_service = ModelService()
ollama_service = OllamaService()

# 请求模型
class RagCreateRequest(BaseModel):
    ragName: str
    ragDesc: str
    embeddingModel: Optional[str] = None
    supplierName: Optional[str] = None
    searchStrategy: Optional[int] = 2  # 检索策略 1=混合检索 2=向量检索 3=全文检索
    maxRecall: Optional[int] = 5  # 最大召回数
    recallAccuracy: Optional[float] = 0.1  # 召回精度
    resultReordering: Optional[int] = 1  # 结果重排序 1=开启 0=关闭
    rerankModel: Optional[str] = ""  # 重排序模型
    queryRewrite: Optional[int] = 0  # 查询重写 1=开启 0=关闭
    vectorWeight: Optional[float] = 0.7  # 向量权重
    keywordWeight: Optional[float] = 0.3  # 关键词权重
    savePath: Optional[str] = None  # 保存路径

class RagRemoveRequest(BaseModel):
    ragName: str

class RagModifyRequest(BaseModel):
    ragName: str
    ragDesc: str
    searchStrategy: Optional[int] = None
    maxRecall: Optional[int] = None
    recallAccuracy: Optional[float] = None
    resultReordering: Optional[int] = None
    rerankModel: Optional[str] = None
    queryRewrite: Optional[int] = None
    vectorWeight: Optional[float] = None
    keywordWeight: Optional[float] = None

class DocUploadRequest(BaseModel):
    ragName: str
    filePath: str
    separators: Optional[List[str]] = None
    chunkSize: Optional[int] = None
    overlapSize: Optional[int] = None

class RagDocListRequest(BaseModel):
    ragName: str

class DocContentRequest(BaseModel):
    ragName: str
    docName: str

class DocRemoveRequest(BaseModel):
    ragName: str
    docIdList: str

class DocReindexRequest(BaseModel):
    ragName: str
    docId: str

class RagReindexRequest(BaseModel):
    ragName: str

class RagSearchRequest(BaseModel):
    ragList: str
    queryText: str

class ChunkTestRequest(BaseModel):
    filename: str
    chunkSize: int
    overlapSize: int
    separators: List[str]

class OptimizeTableRequest(BaseModel):
    ragName: str

class DocChunkListRequest(BaseModel):
    ragName: str
    docId: str

class TestChunkRequest(BaseModel):
    text: str
    chunk_size: int = 1000
    chunk_overlap: int = 200





@router.get("/rag_status", summary="获取知识库状态")
async def rag_status():
    """获取知识库状态
    
    检查知识库组件是否正常运行，包括嵌入模型是否可用
    """
    try:
        # 检查是否有嵌入模型
        result = await model_service.get_supplier_embedding_models()
        if result and any(result.values()):
            return ResponseHandler.success("知识库组件正常")
        
        # 检查Ollama嵌入模型
        ollama_models = await ollama_service.get_embedding_model_list()
        if ollama_models and len(ollama_models) > 0:
            return ResponseHandler.success("知识库组件正常")
            
        return ResponseHandler.error("请选安装或接入嵌入模型", None, 400)
    except Exception as e:
        return ResponseHandler.error(f"请选安装或接入嵌入模型: {str(e)}")

@router.get("/get_embedding_models", summary="获取嵌入模型列表")
async def get_embedding_models():
    """获取嵌入模型列表
    
    获取所有可用的嵌入模型列表，包括供应商模型和Ollama模型
    """
    try:
        result = await model_service.get_supplier_embedding_models()
        result['ollama'] = await ollama_service.get_embedding_model_list()
        return ResponseHandler.success("获取成功", result)
    except Exception as e:
        return ResponseHandler.error(f"获取嵌入模型列表失败: {str(e)}")

@router.post("/create_rag", summary="创建知识库")
async def create_rag(request: RagCreateRequest):
    """
    创建知识库
    与electron项目create_rag方法保持完全一致
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    - **ragDesc**: 知识库描述（必填）
    - **embeddingModel**: 嵌入模型名称（可选）
    - **supplierName**: 供应商名称（可选）
    - **searchStrategy**: 检索策略 1=混合检索 2=向量检索 3=全文检索（可选）
    - **maxRecall**: 最大召回数（可选）
    - **recallAccuracy**: 召回精度（可选）
    - **resultReordering**: 结果重排序 1=开启 0=关闭（可选）
    - **rerankModel**: 重排序模型（可选）
    - **queryRewrite**: 查询重写 1=开启 0=关闭（可选）
    - **vectorWeight**: 向量权重（可选）
    - **keywordWeight**: 关键词权重（可选）
    - **savePath**: 保存路径（可选）
    """
    try:
        # 设置默认值（与electron项目一致）
        search_strategy = request.searchStrategy if request.searchStrategy is not None else 2
        max_recall = request.maxRecall if request.maxRecall is not None else 5
        recall_accuracy = request.recallAccuracy if request.recallAccuracy is not None else 0.1
        result_reordering = request.resultReordering if request.resultReordering is not None else 1
        rerank_model = request.rerankModel if request.rerankModel is not None else ''
        query_rewrite = request.queryRewrite if request.queryRewrite is not None else 0
        vector_weight = request.vectorWeight if request.vectorWeight is not None else 0.7
        keyword_weight = request.keywordWeight if request.keywordWeight is not None else 0.3
        
        # 参数检查
        if not request.ragName:
            return ResponseHandler.error("知识库名称不能为空")
        
        if request.ragName == 'vector_db':
            return ResponseHandler.error("知识库名称不能为vector_db")
            
        # 默认值设置
        embedding_model = request.embeddingModel if request.embeddingModel else "bge-m3:latest"
        supplier_name = request.supplierName if request.supplierName else "ollama"
        
        # 知识库保存路径
        rag_path = os.path.join(PubUtils.get_rag_path(), request.ragName)
        
        # 检查知识库是否存在
        if PubUtils.file_exists(rag_path):
            return ResponseHandler.error("指定知识库名称已存在")
            
        # 创建知识库目录
        PubUtils.mkdir(rag_path)
        
        # 创建知识库描述文件
        config_data = {
            "ragName": request.ragName,
            "ragDesc": request.ragDesc,
            "ragCreateTime": PubUtils.time(),
            "supplierName": supplier_name,
            "embeddingModel": embedding_model,
            "searchStrategy": search_strategy,
            "maxRecall": max_recall,
            "recallAccuracy": recall_accuracy,
            "resultReordering": result_reordering,
            "rerankModel": rerank_model,
            "queryRewrite": query_rewrite,
            "vectorWeight": vector_weight,
            "keywordWeight": keyword_weight
        }
        
        config_file_path = os.path.join(rag_path, "config.json")
        PubUtils.write_file(config_file_path, json.dumps(config_data, ensure_ascii=False, indent=4))
            
        # 创建知识库原始文件目录
        PubUtils.mkdir(os.path.join(rag_path, "source"))
        
        # 创建知识库markdown文件目录
        PubUtils.mkdir(os.path.join(rag_path, "markdown"))
        
        # 创建图片目录
        PubUtils.mkdir(os.path.join(rag_path, "images"))

        # 确保文档记录表存在
        try:
            from app.rag.rag import Rag
            rag_instance = Rag()
            await rag_instance.create_doc_table('doc_table')
        except Exception as table_e:
            logger.warning(f"创建文档记录表失败: {table_e}")

        return ResponseHandler.success("知识库创建成功")
    except Exception as e:
        return ResponseHandler.error(f"创建知识库失败: {str(e)}")

@router.post("/remove_rag", summary="删除知识库")
async def remove_rag(request: RagRemoveRequest):
    """删除知识库
    与electron项目remove_rag方法保持完全一致
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    """
    try:
        if request.ragName == 'vector_db':
            return ResponseHandler.error("知识库名称不能为vector_db")
            
        if not request.ragName:
            return ResponseHandler.error("知识库名称不能为空")
            
        # 知识库路径
        rag_path = os.path.join(PubUtils.get_rag_path(), request.ragName)
        
        # 检查知识库是否存在
        if not PubUtils.file_exists(rag_path):
            return ResponseHandler.error("指定知识库不存在")
            
        # 删除知识库所有文档和向量索引
        rag_instance = Rag()
        await rag_instance.remove_rag(request.ragName)
        
        # 删除知识库目录
        PubUtils.remove_dir(rag_path)
        
        # 删除索引标记
        index_tip_file = os.path.join(PubUtils.get_rag_path(), 'index_tips', PubUtils.md5(request.ragName) + ".pl")
        if PubUtils.file_exists(index_tip_file):
            PubUtils.remove_file(index_tip_file)
            
        return ResponseHandler.success("知识库删除成功")
    except Exception as e:
        return ResponseHandler.error(f"删除知识库失败: {str(e)}")

@router.get("/get_embedding_map", summary="获取嵌入模型映射")
async def get_embedding_map():
    """获取嵌入模型映射
    与electron项目get_embedding_map方法保持完全一致
    
    返回所有可用的嵌入模型映射关系
    """
    try:
        # 获取Ollama嵌入模型列表
        ollama_embedding_list = await ollama_service.get_embedding_model_list()
        # 获取供应商嵌入模型列表
        supplier_embedding_list = await model_service.get_supplier_embedding_models()

        # 构建嵌入模型映射（与electron项目一致）
        embedding_map = {}
        
        # 处理Ollama模型
        ollama_map = {}
        for embed in ollama_embedding_list:
            ollama_map[embed.get('model', '')] = True
        embedding_map['ollama'] = ollama_map
        
        # 处理供应商模型
        for supplier_title, models in supplier_embedding_list.items():
            supplier_map = {}
            supplier_name = ''
            for embed in models:
                supplier_name = embed.get('supplierName', '')
                supplier_map[embed.get('model', '')] = True
            if not supplier_name:
                supplier_name = supplier_title
            embedding_map[supplier_name] = supplier_map
        
        return ResponseHandler.success("获取嵌入模型映射成功", embedding_map)
    except Exception as e:
        return ResponseHandler.error(f"获取嵌入模型映射失败: {str(e)}")

@router.get("/get_rag_list", summary="获取知识库列表")
async def get_rag_list():
    """
    获取知识库列表
    与electron项目get_rag_list方法保持完全一致
    
    获取所有已创建的知识库列表及其配置信息
    """
    try:
        # 获取知识库根目录
        rag_root_path = PubUtils.get_rag_path()
        
        if not PubUtils.file_exists(rag_root_path):
            return ResponseHandler.success("获取知识库列表成功", [])
        
        # 获取所有知识库目录
        rag_dirs = PubUtils.read_dir(rag_root_path)
        rag_list = []
        
        for rag_dir in rag_dirs:
            rag_path = os.path.join(rag_root_path, rag_dir)
            if PubUtils.is_directory(rag_path) and rag_dir != 'vector_db' and rag_dir != 'index_tips':
                config_path = os.path.join(rag_path, "config.json")
                if PubUtils.file_exists(config_path):
                    try:
                        config_content = PubUtils.read_file(config_path)
                        config = json.loads(config_content)
                        
                        # 补全缺失字段（与electron项目一致）
                        if not config.get('vectorWeight'):
                            config['ragCreateTime'] = PubUtils.time()  # 创建时间
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
                            PubUtils.write_file(config_path, json.dumps(config, ensure_ascii=False, indent=4))
                        
                        if not config.get('supplierName'):
                            config['supplierName'] = 'ollama'
                            PubUtils.write_file(config_path, json.dumps(config, ensure_ascii=False, indent=4))
                        
                        # 检查嵌入模型是否存在
                        config['embeddingModelExist'] = True
                        config['errorMsg'] = ''
                        
                        # 获取嵌入模型列表进行存在性检查
                        try:
                            embedding_list = await ollama_service.get_embedding_model_list()
                            embedding_models = [model.get('model', '') for model in embedding_list]
                            
                            if config.get('embeddingModel') not in embedding_models:
                                config['embeddingModelExist'] = False
                                config['errorMsg'] = f"指定嵌入模型不存在: {config.get('embeddingModel', '')}"
                        except Exception as e:
                            pass
                        
                        rag_list.append(config)
                    except Exception as e:
                        continue
        
        return ResponseHandler.success("获取知识库列表成功", rag_list)
    except Exception as e:
        return ResponseHandler.error(f"获取知识库列表失败: {str(e)}")

@router.post("/modify_rag", summary="修改知识库")
async def modify_rag(request: RagModifyRequest):
    """
    修改知识库
    与electron项目modify_rag方法保持完全一致
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    - **ragDesc**: 知识库描述（必填）
    - **searchStrategy**: 检索策略（可选）
    - **maxRecall**: 最大召回数（可选）
    - **recallAccuracy**: 召回精度（可选）
    - **resultReordering**: 结果重排序（可选）
    - **rerankModel**: 重排序模型（可选）
    - **queryRewrite**: 查询重写（可选）
    - **vectorWeight**: 向量权重（可选）
    - **keywordWeight**: 关键词权重（可选）
    """
    try:
        # 检查参数
        if not request.ragName:
            return ResponseHandler.error("知识库名称不能为空")
        
        if request.ragName == 'vector_db':
            return ResponseHandler.error("知识库名称不能为vector_db")
        
        # 知识库保存路径
        rag_path = os.path.join(PubUtils.get_rag_path(), request.ragName)
        
        # 检查知识库是否存在
        if not PubUtils.file_exists(rag_path):
            return ResponseHandler.error("知识库不存在")

        rag_desc_file = os.path.join(rag_path, "config.json")
        rag_config = {}
        
        if PubUtils.file_exists(rag_desc_file):
            config_content = PubUtils.read_file(rag_desc_file)
            rag_config = json.loads(config_content)

        # 更新配置（与electron项目一致）
        rag_config["ragDesc"] = request.ragDesc
        rag_config["searchStrategy"] = request.searchStrategy if request.searchStrategy is not None else rag_config.get("searchStrategy")
        rag_config["maxRecall"] = request.maxRecall if request.maxRecall is not None else rag_config.get("maxRecall")
        rag_config["recallAccuracy"] = request.recallAccuracy if request.recallAccuracy is not None else rag_config.get("recallAccuracy")
        rag_config["resultReordering"] = request.resultReordering if request.resultReordering is not None else rag_config.get("resultReordering")
        rag_config["rerankModel"] = request.rerankModel if request.rerankModel is not None else rag_config.get("rerankModel")
        rag_config["queryRewrite"] = request.queryRewrite if request.queryRewrite is not None else rag_config.get("queryRewrite")
        rag_config["vectorWeight"] = request.vectorWeight if request.vectorWeight is not None else rag_config.get("vectorWeight")
        rag_config["keywordWeight"] = request.keywordWeight if request.keywordWeight is not None else rag_config.get("keywordWeight")
        
        PubUtils.write_file(rag_desc_file, json.dumps(rag_config, ensure_ascii=False, indent=4))
            
        return ResponseHandler.success("知识库修改成功")
    except Exception as e:
        return ResponseHandler.error(f"修改知识库失败: {str(e)}")

@router.post("/upload_doc", summary="上传文档并解析")
async def upload_doc(
    ragName: str = Form(...),
    file: UploadFile = File(...),
    separators: str = Form(default="[\"\\n\\n\", \"\\n\", \" \", \"\"]"),
    chunkSize: int = Form(default=1000),
    overlapSize: int = Form(default=200),
    overSameFile: Optional[int] = Form(default=None)
):
    """
    异步上传文档到知识库
    使用后台任务处理文档上传和解析
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    - **file**: 上传的文件（必填）
    - **separators**: 分隔符列表，JSON格式字符串（可选）
    - **chunkSize**: 分块大小（可选，默认1000）
    - **overlapSize**: 重叠大小（可选，默认200）
    - **overSameFile**: 同文件处理方式（可选，默认null覆盖，1不覆盖，2重命名）
    
    返回：
    - 任务ID，用于查询处理状态
    """
    try:
        # 参数检查
        if not ragName:
            return ResponseHandler.error("知识库名称不能为空")
        
        if ragName == 'vector_db':
            return ResponseHandler.error("知识库名称不能为vector_db")
        
        if not file.filename:
            return ResponseHandler.error("请选择要上传的文件")
        
        # 解析分隔符
        try:
            separators_list = json.loads(separators)
        except json.JSONDecodeError:
            separators_list = ["\n\n", "\n", " ", ""]
        
        # 处理默认参数
        if not separators_list:
            separators_list = []
        if not chunkSize:
            chunkSize = 1000
        if not overlapSize:
            overlapSize = 200
        
        # 知识库路径配置
        rag_path = os.path.join(PubUtils.get_rag_path(), ragName)
        
        # 检查知识库是否存在
        if not PubUtils.file_exists(rag_path):
            return ResponseHandler.error("指定的知识库不存在")
        
        # 处理文件名，根据 overSameFile 参数决定覆盖/不覆盖/重命名
        original_filename = file.filename
        file_extension = os.path.splitext(original_filename)[1]
        base_filename = os.path.splitext(original_filename)[0]
        
        source_dir = os.path.join(rag_path, "source")
        target_file_path = os.path.join(source_dir, original_filename)
        final_filename = original_filename
        
        if PubUtils.file_exists(target_file_path):
            if overSameFile == 1:
                return ResponseHandler.error("该文件已存在")
            elif overSameFile == 2:
                # 重命名：自动添加序号
                counter = 1
                while PubUtils.file_exists(target_file_path):
                    final_filename = f"{base_filename}_{counter}{file_extension}"
                    target_file_path = os.path.join(source_dir, final_filename)
                    counter += 1
            else:
                # 覆盖：查找同名文档并删除旧文档
                doc_list = await rag_service.get_rag_doc_list(ragName)
                old_doc_ids = [
                    doc["docId"] for doc in doc_list if doc["docName"] == original_filename
                ]
                if old_doc_ids:
                    await rag_service.remove_doc(ragName, old_doc_ids)
        
        # 保存文件到临时目录
        temp_file_path = None
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
                content = await file.read()
                # 文件大小限制 20MB
                MAX_FILE_SIZE = 20 * 1024 * 1024
                if len(content) > MAX_FILE_SIZE:
                    return ResponseHandler.error("文件大小超出限制，最大支持 20MB")
                tmp_file.write(content)
                temp_file_path = tmp_file.name
        except Exception as e:
            return ResponseHandler.error(f"文件保存失败: {str(e)}")

        # 预生成文档ID，用于前端跟踪
        import uuid
        doc_id = str(uuid.uuid4())
        
        # 提交异步任务
        task_params = {
            "rag_name": ragName,
            "file_path": temp_file_path,
            "separators": separators_list,
            "chunk_size": chunkSize,
            "overlap_size": overlapSize,
            "filename": final_filename,
            "doc_id": doc_id  # 传递预生成的doc_id
        }
        
        task_id = task_manager.submit_task(TaskType.DOCUMENT_UPLOAD, task_params)
        
        return ResponseHandler.success("文档上传任务已提交", {
            "task_id": task_id,
            "filename": final_filename,
            "doc_id": doc_id,
            "status": "pending"
        })
        
    except Exception as e:
        return ResponseHandler.error(f"提交文档上传任务失败: {str(e)}")





@router.post("/get_rag_doc_list", summary="获取知识库文档列表")
async def get_rag_doc_list(request: RagDocListRequest):
    """
    获取知识库文档列表
    与electron项目get_rag_doc_list方法保持完全一致
    
    获取指定知识库中的所有文档列表
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    """
    try:
        # 检查参数
        if not request.ragName:
            return ResponseHandler.error("知识库名称不能为空")
        
        doc_list = await rag_service.get_rag_doc_list(request.ragName)
        
        return ResponseHandler.success("获取成功", doc_list)
    except Exception as e:
        return ResponseHandler.error(f"获取知识库文档列表失败: {str(e)}")

@router.post("/get_doc_content", summary="获取文档内容")
async def get_doc_content(request: DocContentRequest):
    """
    获取文档内容
    与electron项目get_doc_content方法保持完全一致
    
    获取指定知识库中某个文档的解析内容
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    - **docName**: 文档名称（必填）
    """
    try:
        content = await rag_service.get_doc_content(request.ragName, request.docName)
        
        if content is not None:
            return ResponseHandler.success("获取成功", content)
        else:
            return ResponseHandler.error("文档不存在")
    except Exception as e:
        return ResponseHandler.error(f"获取文档内容失败: {str(e)}")

@router.post("/download_doc", summary="下载知识库文档")
async def download_doc(request: DocContentRequest):
    """下载知识库文档
    与electron项目download_doc方法保持完全一致
    
    下载指定知识库中的文档文件
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    - **docName**: 文档名称（必填）
    """
    try:
        # 检查参数
        if not request.ragName or not request.docName:
            return ResponseHandler.error("知识库名称和文档名称不能为空")
        
        file_path = await rag_service.get_doc_file_path(request.ragName, request.docName)
        
        if file_path and os.path.exists(file_path):
            # 返回文件流，与Electron版本保持一致
            filename = os.path.basename(file_path)
            return FileResponse(
                path=file_path,
                filename=filename,
                media_type='application/octet-stream'
            )
        else:
            return ResponseHandler.error("文档不存在")
    except Exception as e:
        return ResponseHandler.error(f"下载知识库文档失败: {str(e)}")

@router.post("/remove_doc", summary="删除知识库文档")
async def remove_doc(request: DocRemoveRequest):
    """删除知识库文档
    与electron项目remove_doc方法保持完全一致
    
    删除指定知识库中的一个或多个文档
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    - **docIdList**: 文档ID列表，用逗号分隔（必填）
    """
    try:
        # 检查参数
        if not request.ragName or not request.docIdList:
            return ResponseHandler.error("知识库名称和文档ID列表不能为空")

        # 兼容前端 JSON 数组格式（["id1","id2"]）和逗号分隔格式（id1,id2）
        doc_id_list_str = request.docIdList.strip()
        if doc_id_list_str.startswith('['):
            try:
                doc_ids = json.loads(doc_id_list_str)
            except json.JSONDecodeError:
                doc_ids = [doc_id.strip() for doc_id in doc_id_list_str.split(',')]
        else:
            doc_ids = [doc_id.strip() for doc_id in doc_id_list_str.split(',')]

        success = await rag_service.remove_doc(request.ragName, doc_ids)
        
        if success:
            return ResponseHandler.success("文档删除成功")
        else:
            return ResponseHandler.error("删除失败")
    except Exception as e:
        return ResponseHandler.error(f"删除知识库文档失败: {str(e)}")

@router.post("/reindex_document", summary="重新索引文档")
async def reindex_document(request: DocReindexRequest):
    """重新索引文档
    与electron项目reindex_document方法保持完全一致
    
    重新为指定文档生成向量索引
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    - **docId**: 文档ID（必填）
    """
    try:
        
        result = await rag_service.reindex_document(request.ragName, request.docId)
        
        if not result:
            return ResponseHandler.error("操作失败")
        
        return ResponseHandler.success("操作成功")
    except Exception as e:
        return ResponseHandler.error(f"重新索引文档失败: {str(e)}")

@router.post("/reindex_rag", summary="重新索引知识库")
async def reindex_rag(request: RagReindexRequest):
    """
    重新索引知识库
    与electron项目reindex_rag方法保持完全一致
    
    重新为整个知识库生成向量索引
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    """
    try:
        # 重新生成知识库索引（与electron项目一致）
        rag = Rag()
        result = await rag.reindex_rag(request.ragName)
        
        if not result:
            return ResponseHandler.error("操作失败")
        
        return ResponseHandler.success("操作成功")
    except Exception as e:
        return ResponseHandler.error(f"重新索引知识库失败: {str(e)}")

@router.post("/search_document", summary="搜索文档")
async def search_document(request: RagSearchRequest):
    """搜索文档
    与electron项目search_document方法保持完全一致
    
    在指定的知识库中搜索相关内容，支持多知识库联合搜索
    
    参数说明：
    - **ragList**: 知识库名称列表，用逗号分隔（必填）
    - **queryText**: 搜索查询文本（必填）
    """
    try:
        # 检索知识库（与electron项目一致）
        rag = Rag()
        rag_names = request.ragList.split(',')
        result = await rag.search_document(rag_names, request.queryText)
        
        return ResponseHandler.success("操作成功", result)
    except Exception as e:
        return ResponseHandler.error(f"搜索文档失败: {str(e)}")

@router.get("/images", summary="获取图片")
async def get_images(r: str, n: str):
    """获取图片
    与electron项目images方法保持完全一致
    
    获取知识库中的图片文件
    
    参数说明：
    - **r**: 知识库名称（必填）
    - **n**: 图片名称（必填）
    """
    try:
        # 检查参数
        if not r:
            return ResponseHandler.error("知识库名称不能为空")
        if not n:
            return ResponseHandler.error("图片名称不能为空")
        
        # 知识库保存路径
        rag_path = os.path.join(PubUtils.get_rag_path(), r)
        
        # 检查知识库是否存在
        if not PubUtils.file_exists(rag_path):
            return ResponseHandler.error("知识库不存在")
        
        # 检查图片是否存在
        img_file = os.path.join(rag_path, "images", n)
        
        if PubUtils.file_exists(img_file):
            return FileResponse(
                path=img_file,
                filename=n,
                media_type='image/*'
            )
        
        return ResponseHandler.error("图片不存在")
    except Exception as e:
        return ResponseHandler.error(f"获取图片失败: {str(e)}")

@router.post("/test_chunk", summary="测试文档分块")
async def test_chunk(request: ChunkTestRequest):
    """测试文档分块
    
    测试指定文档的分块效果，用于验证分块参数配置
    
    参数说明：
    - **filename**: 测试文件名（必填）
    - **chunkSize**: 文本块大小（必填）
    - **overlapSize**: 文本重叠大小（必填）
    - **separators**: 文本分隔符列表（必填）
    """
    try:
        if not request.filename:
            return ResponseHandler.error("文件名不能为空", None, 400)
            
        # 由于是测试分块，这里假设文件存在于某个临时位置或已上传
        # 实际应用中可能需要更复杂的逻辑来获取文件内容
        # 暂时使用一个占位符路径，实际需要根据前端上传的文件路径来确定
        test_file_path = os.path.join(settings.DATA_DIR, "temp", request.filename)
        if not os.path.exists(test_file_path):
            return ResponseHandler.error("测试文件不存在", None, 404)
            
        chunks = await rag_service.test_chunk(
            file_path=test_file_path,
            chunk_size=request.chunkSize,
            overlap_size=request.overlapSize,
            separators=request.separators
        )
        return ResponseHandler.success("分块测试成功", chunks)
    except Exception as e:
        return ResponseHandler.error(f"分块测试失败: {str(e)}")

@router.post("/optimize_table", summary="优化知识库向量表")
async def optimize_table(request: OptimizeTableRequest):
    """优化知识库向量表
    
    优化指定知识库的向量索引表，提升检索性能和存储效率
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    """
    try:
        if not request.ragName:
            return ResponseHandler.error("知识库名称不能为空", None, 400)
            
        success = await rag_service.optimize_table(request.ragName)
        if success:
            return ResponseHandler.success("向量表优化成功")
        else:
            return ResponseHandler.error("向量表优化失败", None, 400)
    except Exception as e:
        return ResponseHandler.error(f"优化向量表失败: {str(e)}")

@router.post("/get_doc_chunk_list", summary="获取文档分块列表")
async def get_doc_chunk_list(request: DocChunkListRequest):
    """获取文档分块列表
    
    获取指定知识库中指定文档的所有文本分块列表，包含分块内容和索引信息
    
    参数说明：
    - **ragName**: 知识库名称（必填）
    - **docId**: 文档ID（必填）
    """
    try:
        if not request.ragName or not request.docId:
            return ResponseHandler.error("知识库名称和文档ID不能为空", None, 400)
            
        chunks = await rag_service.get_doc_chunk_list(request.ragName, request.docId)
        return ResponseHandler.success("获取成功", chunks)
    except Exception as e:
        return ResponseHandler.error(f"获取失败: {str(e)}")