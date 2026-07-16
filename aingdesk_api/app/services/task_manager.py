"""
异步任务管理器
用于管理文档上传和处理的后台任务
"""
import asyncio
import uuid
import time
import json
import os
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)


def run_async_in_thread(coro_func: Callable, *args, **kwargs) -> Any:
    """
    在线程中运行异步函数的通用工具函数
    
    解决Python线程池中不能直接使用await的问题，
    为每个线程创建独立的事件循环来执行异步任务。
    
    Args:
        coro_func: 异步函数或可调用对象
        *args, **kwargs: 传递给异步函数的参数
        
    Returns:
        异步函数的执行结果
        
    Example:
        # 在线程中执行异步函数
        result = run_async_in_thread(async_upload_function, "file.pdf")
    """
    # 创建新的事件循环（每个线程需要独立的事件循环）
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # 创建协程并运行到完成
        if asyncio.iscoroutinefunction(coro_func):
            coro = coro_func(*args, **kwargs)
        else:
            # 如果传入的是普通函数，直接调用
            return coro_func(*args, **kwargs)
        return loop.run_until_complete(coro)
    finally:
        # 清理事件循环和相关资源
        loop.close()
        # 清理当前线程的事件循环引用，避免内存泄漏
        asyncio.set_event_loop(None)

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"          # 等待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"       # 处理完成
    FAILED = "failed"            # 处理失败
    CANCELLED = "cancelled"      # 已取消

class TaskType(Enum):
    """任务类型枚举"""
    DOCUMENT_UPLOAD = "document_upload"  # 文档上传和处理

class TaskInfo:
    """任务信息类"""
    def __init__(self, task_id: str, task_type: TaskType, params: Dict[str, Any]):
        self.task_id = task_id
        self.task_type = task_type
        self.status = TaskStatus.PENDING
        self.params = params
        self.result: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.created_time = datetime.now()
        self.started_time: Optional[datetime] = None
        self.completed_time: Optional[datetime] = None
        self.progress = 0  # 进度百分比
        self.message = ""   # 状态消息

class AsyncTaskManager:
    """异步任务管理器"""
    
    def __init__(self, max_workers: int = 4, max_tasks: int = 1000):
        """
        初始化任务管理器
        
        Args:
            max_workers: 最大工作线程数
            max_tasks: 最大任务数量
        """
        self.max_workers = max_workers
        self.max_tasks = max_tasks
        self.tasks: Dict[str, TaskInfo] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()
        self.running = True
        
        # 启动后台任务处理线程
        self._start_task_processor()
    
    def _start_task_processor(self):
        """启动任务处理线程"""
        def process_tasks():
            while self.running:
                try:
                    self._process_pending_tasks()
                    time.sleep(2)  # 每秒检查一次
                except Exception as e:
                    logger.error(f"任务处理线程异常: {e}")
        
        thread = threading.Thread(target=process_tasks, daemon=True)
        thread.start()
    
    def _process_pending_tasks(self):
        """处理待处理任务"""
        with self.lock:
            pending_tasks = [
                task for task in self.tasks.values() 
                if task.status == TaskStatus.PENDING
            ]
            
            # 限制并发任务数量
            processing_count = sum(
                1 for task in self.tasks.values() 
                if task.status == TaskStatus.PROCESSING
            )
            
            available_slots = self.max_workers - processing_count
            
            for task in pending_tasks[:available_slots]:
                self._submit_task(task)
    
    def _submit_task(self, task_info: TaskInfo):
        """提交任务到线程池"""
        task_info.status = TaskStatus.PROCESSING
        task_info.started_time = datetime.now()
        task_info.message = "任务开始处理"
        
        def run_task():
            try:
                # 根据任务类型执行相应的处理函数
                if task_info.task_type == TaskType.DOCUMENT_UPLOAD:
                    result = self._process_document_upload(task_info)
                    task_info.result = result
                    task_info.status = TaskStatus.COMPLETED
                    task_info.progress = 100
                    task_info.message = "文档处理完成"
                else:
                    raise ValueError(f"不支持的任务类型: {task_info.task_type}")
                    
            except Exception as e:
                logger.error(f"任务 {task_info.task_id} 处理失败: {e}")
                task_info.error = str(e)
                task_info.status = TaskStatus.FAILED
                task_info.message = f"处理失败: {str(e)}"
            finally:
                task_info.completed_time = datetime.now()
        
        self.executor.submit(run_task)
    
    def _process_document_upload(self, task_info: TaskInfo) -> Dict[str, Any]:
        """处理文档上传任务"""
        from app.services.rag_service import RagService
        
        params = task_info.params
        rag_name = params["rag_name"]
        file_path = params["file_path"]
        separators = params["separators"]
        chunk_size = params["chunk_size"]
        overlap_size = params["overlap_size"]
        filename = params["filename"]
        doc_id = params.get("doc_id")  # 获取传递的doc_id
        
        # 模拟处理进度
        task_info.progress = 10
        task_info.message = "开始解析文档..."
        
        # 调用RagService处理文档
        rag_service = RagService()
        
        task_info.progress = 30
        task_info.message = "文档解析中..."
        
        # 记录开始时间
        start_time = time.time()
        
        # 这里调用实际的文档处理方法（注意：upload_doc_sync现在是异步方法）
        # 使用通用工具函数来执行异步任务，避免线程中的事件循环冲突问题
        
        async def _upload_document():
            """异步执行文档上传任务"""
            return await rag_service.upload_doc_sync(
                rag_name, file_path, separators, chunk_size, overlap_size, filename, doc_id
            )
        
        # 使用通用工具函数在线程中执行异步任务
        # 这样可以避免与线程中可能存在的其他事件循环冲突
        result = run_async_in_thread(_upload_document)
        
        task_info.progress = 80
        task_info.message = "创建向量索引中..."
        
        # 模拟一些额外处理时间
        time.sleep(1)
        
        task_info.progress = 100
        task_info.message = "文档处理完成"
        
        # 清理临时文件
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.warning(f"清理临时文件失败: {e}")
        
        process_time = time.time() - start_time
        
        return {
            "doc_id": result.get("doc_id", ""),
            "filename": filename,
            "chunks_count": result.get("chunks_count", 0),
            "process_time": round(process_time, 2)
        }
    
    def submit_task(self, task_type: TaskType, params: Dict[str, Any]) -> str:
        """
        提交新任务
        
        Args:
            task_type: 任务类型
            params: 任务参数
            
        Returns:
            任务ID
        """
        with self.lock:
            # 清理过期任务（防止内存溢出）
            self._cleanup_old_tasks()
            
            # 检查任务数量限制
            if len(self.tasks) >= self.max_tasks:
                raise Exception(f"任务数量超过限制: {self.max_tasks}")
            
            # 生成任务ID
            task_id = str(uuid.uuid4())
            
            # 创建任务信息
            task_info = TaskInfo(task_id, task_type, params)
            self.tasks[task_id] = task_info
            
            logger.info(f"提交任务: {task_id}, 类型: {task_type.value}")
            return task_id
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        with self.lock:
            task_info = self.tasks.get(task_id)
            if not task_info:
                return None
            
            return {
                "task_id": task_info.task_id,
                "task_type": task_info.task_type.value,
                "status": task_info.status.value,
                "progress": task_info.progress,
                "message": task_info.message,
                "result": task_info.result,
                "error": task_info.error,
                "created_time": task_info.created_time.isoformat(),
                "started_time": task_info.started_time.isoformat() if task_info.started_time else None,
                "completed_time": task_info.completed_time.isoformat() if task_info.completed_time else None,
                "elapsed_time": self._get_elapsed_time(task_info)
            }
    
    def _get_elapsed_time(self, task_info: TaskInfo) -> float:
        """获取任务耗时（秒）"""
        if not task_info.started_time:
            return 0.0
        
        end_time = task_info.completed_time or datetime.now()
        return (end_time - task_info.started_time).total_seconds()
    
    def _cleanup_old_tasks(self):
        """清理过期任务（保留最近24小时）"""
        current_time = datetime.now()
        expired_tasks = []
        
        for task_id, task_info in self.tasks.items():
            # 清理已完成超过24小时的任务
            if (task_info.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and 
                task_info.completed_time and 
                (current_time - task_info.completed_time).total_seconds() > 86400):
                expired_tasks.append(task_id)
        
        # 清理过期任务
        for task_id in expired_tasks:
            del self.tasks[task_id]
            logger.info(f"清理过期任务: {task_id}")
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        with self.lock:
            task_info = self.tasks.get(task_id)
            if not task_info:
                return False
            
            # 只能取消待处理状态的任务
            if task_info.status != TaskStatus.PENDING:
                return False
            
            task_info.status = TaskStatus.CANCELLED
            task_info.message = "任务已取消"
            return True
    
    def get_all_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取所有任务列表"""
        with self.lock:
            # 按创建时间倒序排列
            sorted_tasks = sorted(
                self.tasks.values(), 
                key=lambda x: x.created_time, 
                reverse=True
            )
            
            return [
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "status": task.status.value,
                    "progress": task.progress,
                    "message": task.message,
                    "created_time": task.created_time.isoformat(),
                    "started_time": task.started_time.isoformat() if task.started_time else None,
                    "completed_time": task.completed_time.isoformat() if task.completed_time else None
                }
                for task in sorted_tasks[:limit]
            ]
    
    def shutdown(self):
        """关闭任务管理器"""
        self.running = False
        self.executor.shutdown(wait=True)

# 创建全局任务管理器实例
task_manager = AsyncTaskManager(max_workers=4, max_tasks=1000)