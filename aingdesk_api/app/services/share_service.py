import os
import json
import uuid
import asyncio
import socketio
from typing import List, Dict, Optional, Any, Set
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.models.share import ShareCreate, ShareInfo, ShareQuery, ShareConnection
from app.services.agent_service import AgentService
from app.services.model_service import ModelService
from app.services.rag_service import RagService

class ShareService:
    def __init__(self):
        self.shares_dir = os.path.join(settings.DATA_DIR, "shares")
        os.makedirs(self.shares_dir, exist_ok=True)
        
        self.shares_file = os.path.join(self.shares_dir, "shares.json")
        if not os.path.exists(self.shares_file):
            with open(self.shares_file, "w", encoding="utf-8") as f:
                json.dump([], f)
                
        self.agent_service = AgentService()
        self.model_service = ModelService()
        self.rag_service = RagService()
        
        # 活跃的WebSocket连接
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def list_shares(self) -> List[ShareInfo]:
        """
        获取所有分享列表
        """
        try:
            with open(self.shares_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            shares = [ShareInfo(**share_data) for share_data in data]
            
            # 过滤掉过期的分享
            now = datetime.now()
            valid_shares = [
                share for share in shares 
                if not share.expires_at or datetime.fromisoformat(share.expires_at) > now
            ]
            
            return valid_shares
        except Exception as e:
            print(f"Error loading shares: {e}")
            return []
    
    async def get_share_info(self, share_id: str) -> Optional[ShareInfo]:
        """
        获取分享的详细信息
        """
        shares = await self.list_shares()
        for share in shares:
            if share.id == share_id:
                return share
        return None
    
    async def create_share(self, share_create: ShareCreate) -> ShareInfo:
        """
        创建新的分享
        """
        # 生成新分享ID
        share_id = str(uuid.uuid4())
        
        # 计算过期时间
        expires_at = None
        if share_create.expires_at:
            expires_at = share_create.expires_at
        
        # 生成分享URL
        # 实际项目中，应该使用配置的公共URL
        share_url = f"http://localhost:{settings.SERVER_PORT}/share/{share_id}"
        
        # 创建分享信息
        share_info = ShareInfo(
            id=share_id,
            name=share_create.name,
            description=share_create.description,
            type=share_create.type,
            resource_id=share_create.resource_id,
            share_url=share_url,
            expires_at=expires_at,
            is_public=share_create.is_public,
            is_password_protected=bool(share_create.password)
        )
        
        # 如果有密码，保存密码
        if share_create.password:
            # 实际项目中，应该对密码进行哈希处理
            password_file = os.path.join(self.shares_dir, f"{share_id}.pwd")
            with open(password_file, "w", encoding="utf-8") as f:
                f.write(share_create.password)
        
        # 保存分享信息
        await self._save_share(share_info)
        
        return share_info
    
    async def delete_share(self, share_id: str) -> bool:
        """
        删除分享
        """
        shares = await self.list_shares()
        
        filtered_shares = [share for share in shares if share.id != share_id]
        
        if len(filtered_shares) == len(shares):
            # 没有找到要删除的分享
            return False
            
        # 保存更新后的分享列表
        with open(self.shares_file, "w", encoding="utf-8") as f:
            json.dump([share.dict() for share in filtered_shares], f, ensure_ascii=False, indent=2, default=str)
            
        # 删除密码文件（如果存在）
        password_file = os.path.join(self.shares_dir, f"{share_id}.pwd")
        if os.path.exists(password_file):
            os.remove(password_file)
            
        return True
    
    async def query_share(self, query: ShareQuery) -> Dict[str, Any]:
        """
        向分享的资源发送查询并获取回复
        """
        share = await self.get_share_info(query.share_id)
        if not share:
            raise ValueError(f"Share {query.share_id} not found")
            
        # 检查密码（如果需要）
        if share.is_password_protected:
            password_file = os.path.join(self.shares_dir, f"{share.id}.pwd")
            if os.path.exists(password_file):
                with open(password_file, "r", encoding="utf-8") as f:
                    correct_password = f.read().strip()
                    
                if not query.password or query.password != correct_password:
                    raise ValueError("Incorrect password")
            
        # 根据资源类型处理查询
        if share.type == "agent":
            # 调用智能体服务
            return await self.agent_service.query_agent(
                agent_id=share.resource_id,
                query_text=query.query,
                chat_id=query.chat_id
            )
        elif share.type == "model":
            # 直接调用模型服务
            from app.models.chat import ChatMessage
            messages = [
                ChatMessage(role="user", content=query.query)
            ]
            
            # 获取模型
            model = await self.model_service.get_model(share.resource_id)
            if not model:
                raise ValueError(f"Model {share.resource_id} not found")
                
            # 调用模型
            response = await self.model_service.generate_text(
                model_id=share.resource_id,
                messages=[{"role": "user", "content": query.query}],
                temperature=0.7
            )
            
            return {
                "response": response,
                "chat_id": query.chat_id or str(uuid.uuid4())
            }
        elif share.type == "knowledge_base":
            # 搜索知识库
            results = await self.rag_service.search_knowledge_base(
                kb_id=share.resource_id,
                query=query.query,
                limit=5
            )
            
            # 格式化结果
            formatted_results = [
                {
                    "text": result.text,
                    "metadata": result.metadata,
                    "score": result.score
                }
                for result in results
            ]
            
            return {
                "results": formatted_results,
                "chat_id": query.chat_id or str(uuid.uuid4())
            }
        else:
            raise ValueError(f"Unsupported share type: {share.type}")
    
    async def register_connection(self, share_id: str, websocket: WebSocket) -> None:
        """
        注册WebSocket连接
        """
        if share_id not in self.active_connections:
            self.active_connections[share_id] = set()
            
        self.active_connections[share_id].add(websocket)
    
    async def unregister_connection(self, share_id: str, websocket: WebSocket) -> None:
        """
        注销WebSocket连接
        """
        if share_id in self.active_connections:
            self.active_connections[share_id].discard(websocket)
            
            # 如果没有连接了，删除键
            if not self.active_connections[share_id]:
                del self.active_connections[share_id]
    
    async def handle_share_message(self, share_id: str, data: Dict[str, Any], websocket: WebSocket) -> None:
        """
        处理分享消息
        """
        share = await self.get_share_info(share_id)
        if not share:
            await websocket.send_json({"error": f"Share {share_id} not found"})
            return
            
        # 检查密码（如果需要）
        if share.is_password_protected:
            password = data.get("password")
            password_file = os.path.join(self.shares_dir, f"{share.id}.pwd")
            if os.path.exists(password_file):
                with open(password_file, "r", encoding="utf-8") as f:
                    correct_password = f.read().strip()
                    
                if not password or password != correct_password:
                    await websocket.send_json({"error": "Incorrect password"})
                    return
        
        # 处理查询
        try:
            query = ShareQuery(
                share_id=share_id,
                query=data.get("query", ""),
                password=data.get("password"),
                chat_id=data.get("chat_id")
            )
            
            response = await self.query_share(query)
            
            # 发送响应
            await websocket.send_json(response)
            
            # 广播消息给所有连接的客户端（如果启用了广播）
            if data.get("broadcast", False) and share_id in self.active_connections:
                broadcast_data = {
                    "type": "broadcast",
                    "query": data.get("query", ""),
                    "response": response.get("response", ""),
                    "sender_id": data.get("sender_id", "unknown"),
                    "timestamp": datetime.now().isoformat()
                }
                
                for client in self.active_connections[share_id]:
                    if client != websocket:  # 不发送给消息源
                        try:
                            await client.send_json(broadcast_data)
                        except Exception as e:
                            print(f"Error broadcasting message: {e}")
                            
        except Exception as e:
            await websocket.send_json({"error": str(e)})
    
    async def _save_share(self, share: ShareInfo) -> None:
        """
        保存分享信息到文件
        """
        shares = await self.list_shares()
        
        # 查找并替换或添加分享
        found = False
        for i, existing_share in enumerate(shares):
            if existing_share.id == share.id:
                shares[i] = share
                found = True
                break
                
        if not found:
            shares.append(share)
            
        # 保存更新后的分享列表
        with open(self.shares_file, "w", encoding="utf-8") as f:
            json.dump([share.dict() for share in shares], f, ensure_ascii=False, indent=2, default=str) 