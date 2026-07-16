import os
import secrets
from typing import Dict, List, Optional, Union

from pydantic import AnyHttpUrl, validator

# 尝试从pydantic_settings导入BaseSettings，如果不存在则从pydantic导入
try:
    from pydantic_settings import BaseSettings
except ImportError:
    try:
        # 对于旧版本pydantic
        from pydantic import BaseSettings
    except ImportError:
        # 简单的后备方案
        print("Warning: Neither pydantic_settings nor pydantic.BaseSettings available. Using fallback.")
        class BaseSettings:
            class Config:
                pass


class Settings(BaseSettings):
    PROJECT_NAME: str = "AiDesk API"
    API_V1_STR: str = ""
    SECRET_KEY: str = secrets.token_urlsafe(32)
    
    # 定义一个基础应用数据目录（动态获取当前用户目录）
    BASE_APP_DATA_DIR: str = os.path.join(os.path.expanduser("~"), "AppData", "Roaming", "AiDesk")

    # 服务端口
    SERVER_PORT: int = 7071
    
    # 跨域配置
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # 数据存储路径
    DATA_DIR: str = os.path.join(BASE_APP_DATA_DIR, "data")
    UPLOADS_DIR: str = os.path.join(BASE_APP_DATA_DIR, "uploads")
    LOGS_DIR: str = os.path.join(BASE_APP_DATA_DIR, "logs")
    
    # 向量数据库配置
    VECTOR_DB_PATH: str = os.path.join(DATA_DIR, "vector_db")
    
    # 分享配置
    SHARE_ID_PREFIX: str = "none"
    
    # OpenAI 配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = "https://api.openai.com/v1"
    
    # Ollama 配置
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    class Config:
        case_sensitive = True
        env_file = ".env"


# 创建全局设置实例
settings = Settings()

# 确保目录存在
os.makedirs(settings.DATA_DIR, exist_ok=True)
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
os.makedirs(settings.LOGS_DIR, exist_ok=True)
os.makedirs(settings.VECTOR_DB_PATH, exist_ok=True)

def get_data_path() -> str:
    """
    获取数据路径
    """
    return settings.DATA_DIR