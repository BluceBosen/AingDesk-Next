from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class Agent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    system_prompt: str
    model_id: str
    knowledge_base_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tools: List[str] = []  # 可用工具列表
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        protected_namespaces = ()

class AgentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: str
    model_id: str
    knowledge_base_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = []

    class Config:
        protected_namespaces = ()

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    model_id: Optional[str] = None
    knowledge_base_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None

    class Config:
        protected_namespaces = ()

class AgentQuery(BaseModel):
    agent_id: str
    query: str
    chat_id: Optional[str] = None 