import os
import json
import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime

from app.core.config import settings
from app.models.agent import Agent, AgentCreate, AgentUpdate
from app.services.model_service import ModelService
from app.services.rag_service import RagService
from app.services.chat_service import ChatService

class AgentService:
    def __init__(self):
        self.agents_dir = os.path.join(settings.DATA_DIR, "agents")
        os.makedirs(self.agents_dir, exist_ok=True)
        
        self.agents_file = os.path.join(self.agents_dir, "agents.json")
        if not os.path.exists(self.agents_file):
            with open(self.agents_file, "w", encoding="utf-8") as f:
                json.dump([], f)
                
        self.model_service = ModelService()
        self.rag_service = RagService()
        self.chat_service = ChatService()
    
    async def list_agents(self) -> List[Agent]:
        """
        获取所有智能体列表
        """
        try:
            with open(self.agents_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            return [Agent(**agent_data) for agent_data in data]
        except Exception as e:
            print(f"Error loading agents: {e}")
            return []
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        获取特定智能体的详细信息
        """
        agents = await self.list_agents()
        for agent in agents:
            if agent.id == agent_id:
                return agent
        return None
    
    async def create_agent(self, agent_create: AgentCreate) -> Agent:
        """
        创建新的智能体
        """
        # 生成新智能体
        agent = Agent(
            id=str(uuid.uuid4()),
            name=agent_create.name,
            description=agent_create.description,
            system_prompt=agent_create.system_prompt,
            model_id=agent_create.model_id,
            knowledge_base_id=agent_create.knowledge_base_id,
            parameters=agent_create.parameters,
            tools=agent_create.tools or []
        )
        
        # 保存智能体
        await self._save_agent(agent)
        
        return agent
    
    async def update_agent(self, agent_id: str, agent_update: AgentUpdate) -> Optional[Agent]:
        """
        更新智能体信息
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            return None
            
        # 更新字段
        if agent_update.name is not None:
            agent.name = agent_update.name
        if agent_update.description is not None:
            agent.description = agent_update.description
        if agent_update.system_prompt is not None:
            agent.system_prompt = agent_update.system_prompt
        if agent_update.model_id is not None:
            agent.model_id = agent_update.model_id
        if agent_update.knowledge_base_id is not None:
            agent.knowledge_base_id = agent_update.knowledge_base_id
        if agent_update.parameters is not None:
            agent.parameters = agent_update.parameters
        if agent_update.tools is not None:
            agent.tools = agent_update.tools
            
        agent.updated_at = datetime.now()
        
        # 保存更新后的智能体
        await self._save_agent(agent)
        
        return agent
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        删除智能体
        """
        agents = await self.list_agents()
        
        filtered_agents = [agent for agent in agents if agent.id != agent_id]
        
        if len(filtered_agents) == len(agents):
            # 没有找到要删除的智能体
            return False
            
        # 保存更新后的智能体列表
        with open(self.agents_file, "w", encoding="utf-8") as f:
            json.dump([agent.dict() for agent in filtered_agents], f, ensure_ascii=False, indent=2, default=str)
            
        return True
    
    async def query_agent(
        self, 
        agent_id: str, 
        query_text: str,
        chat_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        向智能体发送查询并获取回复
        """
        agent = await self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
            
        # 准备系统提示信息
        system_prompt = agent.system_prompt
        
        # 添加工具信息
        if agent.tools:
            tool_descriptions = []
            for tool in agent.tools:
                if tool == "web_search":
                    tool_descriptions.append("- web_search: 可以使用互联网搜索获取信息")
                elif tool == "calculator":
                    tool_descriptions.append("- calculator: 可以进行数学计算")
                # 添加更多工具描述
                
            if tool_descriptions:
                system_prompt += "\n\n可用工具:\n" + "\n".join(tool_descriptions)
        
        # 构建消息
        from app.models.chat import ChatMessage
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=query_text)
        ]
        
        # 调用聊天服务获取回复
        response = await self.chat_service.send_message(
            messages=messages,
            model_id=agent.model_id,
            temperature=agent.parameters.get("temperature", 0.7) if agent.parameters else 0.7,
            knowledge_base_id=agent.knowledge_base_id,
            chat_id=chat_id
        )
        
        return {
            "response": response.message.content,
            "chat_id": response.chat_id
        }
    
    async def _save_agent(self, agent: Agent) -> None:
        """
        保存智能体到文件
        """
        agents = await self.list_agents()
        
        # 查找并替换或添加智能体
        found = False
        for i, existing_agent in enumerate(agents):
            if existing_agent.id == agent.id:
                agents[i] = agent
                found = True
                break
                
        if not found:
            agents.append(agent)
            
        # 保存更新后的智能体列表
        with open(self.agents_file, "w", encoding="utf-8") as f:
            json.dump([agent.dict() for agent in agents], f, ensure_ascii=False, indent=2, default=str) 