from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Model(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    type: str  # "api" 或 "local"
    provider: str  # "openai", "ollama", "anthropic", "custom" 等
    model_name: str  # 实际模型名称，如 "gpt-4", "llama2", 等
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    local_path: Optional[str] = None
    status: str = "active"  # "active", "downloading", "error"
    error_message: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        protected_namespaces = ()

class ModelCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    provider: str
    model_name: str
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    local_path: Optional[str] = None

    class Config:
        protected_namespaces = ()

class ModelUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    api_key: Optional[str] = None
    api_base_url: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    local_path: Optional[str] = None
    status: Optional[str] = None

    class Config:
        protected_namespaces = () 