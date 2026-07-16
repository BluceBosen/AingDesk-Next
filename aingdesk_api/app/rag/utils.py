import os
import uuid
import hashlib
import time
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

class PubUtils:
    """
    公共工具类，模拟electron项目中的pub类功能
    """
    
    @staticmethod
    def uuid() -> str:
        """
        生成UUID
        """
        return str(uuid.uuid4())
    
    @staticmethod
    def md5(text: str) -> str:
        """
        生成MD5哈希
        """
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    @staticmethod
    def time() -> int:
        """
        获取当前时间戳
        """
        return int(time.time())
    
    @staticmethod
    def get_data_path() -> str:
        """
        获取数据路径
        """
        from app.core.config import get_data_path
        return get_data_path()
    
    @staticmethod
    def get_rag_path() -> str:
        """
        获取知识库路径
        """
        return os.path.join(PubUtils.get_data_path(), "rag")
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """
        检查文件是否存在
        """
        return os.path.exists(file_path)
    
    @staticmethod
    def mkdir(dir_path: str) -> None:
        """
        创建目录
        """
        os.makedirs(dir_path, exist_ok=True)
    
    @staticmethod
    def copy_file(src: str, dst: str) -> bool:
        """
        复制文件
        """
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            return True
        except Exception as e:
            print(f"复制文件失败: {e}")
            return False
    
    @staticmethod
    def read_file(file_path: str) -> str:
        """
        读取文件内容
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return ""
    
    @staticmethod
    def write_file(file_path: str, content: str) -> bool:
        """
        写入文件内容
        """
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"写入文件失败: {e}")
            return False
    
    @staticmethod
    def cut_for_search(text: str) -> List[str]:
        """
        分词（搜索）- 改进的中文分词
        """
        import re
        # 移除标点符号
        text = re.sub(r'[^\u4e00-\u9fff\w\s]', '', text)
        
        # 提取中文词汇（2-4个字符）
        chinese_words = re.findall(r'[\u4e00-\u9fff]{2,4}', text)
        
        # 提取英文词汇
        english_words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        
        # 提取数字和字母组合
        mixed_words = re.findall(r'\b[\w]+\b', text.lower())
        
        # 合并所有词汇并去重
        all_words = list(set(chinese_words + english_words + mixed_words))
        
        # 过滤长度小于2的词，但保留单个中文字符
        filtered_words = []
        for word in all_words:
            if len(word) >= 2:
                filtered_words.append(word)
            elif len(word) == 1 and re.match(r'[\u4e00-\u9fff]', word):
                # 单个中文字符也保留
                filtered_words.append(word)
        
        return filtered_words
    
    @staticmethod
    def return_success(message: str, data: Any = None) -> Dict[str, Any]:
        """
        返回成功响应
        """
        result = {
            "success": True,
            "message": message
        }
        if data is not None:
            result["data"] = data
        return result
    
    @staticmethod
    def return_error(message: str, error: Any = None) -> Dict[str, Any]:
        """
        返回错误响应
        """
        result = {
            "success": False,
            "message": message
        }
        if error is not None:
            result["error"] = str(error)
        return result
    
    @staticmethod
    def get_current_datetime() -> str:
        """
        获取当前日期时间字符串
        """
        now = datetime.now()
        weekdays = ['星期一', '星期二', '星期三', '星期四', '星期五', '星期六', '星期日']
        weekday = weekdays[now.weekday()]
        ampm = '上午' if now.hour < 12 else '下午'
        return f"{now.strftime('%Y-%m-%d %H:%M:%S')} -- {ampm} {weekday}"
    
    @staticmethod
    def get_user_location() -> str:
        """
        获取用户位置（模拟）
        """
        return "中国"
    
    @staticmethod
    def read_dir(dir_path: str) -> List[str]:
        """
        读取目录内容列表
        """
        try:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                return os.listdir(dir_path)
            return []
        except Exception as e:
            print(f"读取目录失败: {e}")
            return []
    
    @staticmethod
    def is_directory(path: str) -> bool:
        """
        检查路径是否为目录
        """
        try:
            return os.path.exists(path) and os.path.isdir(path)
        except Exception as e:
            print(f"检查目录失败: {e}")
            return False
    
    @staticmethod
    def remove_dir(dir_path: str) -> bool:
        """
        删除目录及其所有内容
        """
        try:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
                return True
            return False
        except Exception as e:
            print(f"删除目录失败: {e}")
            return False
    
    @staticmethod
    def remove_file(file_path: str) -> bool:
        """
        删除文件
        """
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False

