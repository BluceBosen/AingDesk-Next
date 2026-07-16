from typing import Any, Optional
from pydantic import BaseModel


class ApiResponse(BaseModel):
    """统一的API响应模型"""
    status: int
    code: int
    msg: str
    error_msg: str
    message: Any


class ResponseHandler:
    """统一的响应处理器"""
    
    @staticmethod
    def success(message: str, data: Any = None, code: int = 200) -> dict:
        """处理成功响应
        
        Args:
            message: 成功消息
            data: 返回的数据
            code: HTTP状态码
            
        Returns:
            dict: 统一格式的成功响应
        """
        return {
            "status": 0,
            "code": code,
            "msg": message,
            "error_msg": "",
            "message": data if data is not None else ""
        }
    
    @staticmethod
    def error(message: str, error_detail: Optional[str] = None, code: int = 500) -> dict:
        """处理错误响应
        
        Args:
            message: 错误消息
            error_detail: 详细错误信息
            code: HTTP状态码
            
        Returns:
            dict: 统一格式的错误响应
        """
        return {
            "status": -1,
            "code": code,
            "msg": message,
            "error_msg": error_detail if error_detail else "",
            "message": ""
        }
    
    @staticmethod
    def handle_result(success: bool, message: str, data: Any = None, code: int = 200) -> dict:
        """统一的结果处理函数，与electron项目保持一致的响应格式
        
        Args:
            success: 是否成功
            message: 消息内容
            data: 返回的数据或错误详情
            code: HTTP状态码
            
        Returns:
            dict: 统一格式的响应
        """
        if success:
            return ResponseHandler.success(message, data, code)
        else:
            return ResponseHandler.error(message, data, code if code != 200 else 500)