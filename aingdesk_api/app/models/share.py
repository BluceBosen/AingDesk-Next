from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ShareCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str  # "agent", "model", "knowledge_base"
    resource_id: str  # agent_id, model_id, 或 knowledge_base_id
    expires_at: Optional[datetime] = None
    is_public: bool = True
    password: Optional[str] = None

class ShareInfo(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    type: str
    resource_id: str
    share_url: str
    expires_at: Optional[datetime] = None
    is_public: bool = True
    is_password_protected: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ShareQuery(BaseModel):
    share_id: str
    query: str
    password: Optional[str] = None
    chat_id: Optional[str] = None

class ShareConnection(BaseModel):
    share_id: str
    client_id: str
    connected_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        } 