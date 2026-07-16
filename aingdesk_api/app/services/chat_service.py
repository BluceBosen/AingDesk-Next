import os
import json
import uuid
import time
from typing import List, Dict, Optional, AsyncGenerator, Any
from datetime import datetime
import shutil
import logging

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.models.chat import ChatMessage, ChatResponse, ChatHistory
from app.services.model_service import ModelService
from app.services.rag_service import RagService

class ChatService:
    def __init__(self):
        self.model_service = ModelService()
        self.rag_service = RagService()
        
        self.context_root_dir = os.path.join(settings.DATA_DIR, "context")
        os.makedirs(self.context_root_dir, exist_ok=True)

    def _get_context_path(self, context_id: str) -> str:
        return os.path.join(self.context_root_dir, context_id)

    def _get_config_file_path(self, context_id: str) -> str:
        return os.path.join(self._get_context_path(context_id), "config.json")

    def _get_history_file_path(self, context_id: str) -> str:
        return os.path.join(self._get_context_path(context_id), "history.json")

    def _file_exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)

    def _read_json_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        if not self._file_exists(file_path):
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading JSON file {file_path}: {e}")
            return None

    def _write_json_file(self, file_path: str, data: Dict[str, Any]) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def _readdir(self, dir_path: str) -> List[str]:
        if not self._file_exists(dir_path):
            return []
        return [d for d in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, d))]

    def _uuid(self) -> str:
        return str(uuid.uuid4())

    def _time(self) -> int:
        return int(datetime.now().timestamp())

    def _parse_datetime_safely(self, dt_value: Any) -> datetime:
        """
        Safely parses a datetime value from various formats, defaulting to now() if parsing fails.
        """
        if isinstance(dt_value, datetime):
            return dt_value
        if isinstance(dt_value, int):
            try:
                return datetime.fromtimestamp(dt_value)
            except (TypeError, ValueError):
                pass
        if isinstance(dt_value, str):
            if dt_value == '':
                return datetime.now() # Handle empty string explicitly
            try:
                # Try ISO format first (preferred for Pydantic)
                return datetime.fromisoformat(dt_value)
            except ValueError:
                pass
            try:
                # Try common formats if ISO fails
                return datetime.strptime(dt_value, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                pass
            try:
                return datetime.strptime(dt_value, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
        return datetime.now() # Fallback if all attempts fail

    async def send_message(
        self, 
        messages: List[ChatMessage], 
        model_id: str, 
        temperature: float = 0.7,
        stream: bool = False,
        knowledge_base_id: Optional[str] = None,
        chat_id: Optional[str] = None
    ) -> ChatResponse:
        """
        发送消息并获取回复
        """
        # 如果没有提供chat_id，创建一个新的
        if not chat_id:
            chat_id = self._uuid()
            
        # 获取模型
        model = await self.model_service.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
            
        # 如果有知识库ID，处理RAG
        context = None
        if knowledge_base_id:
            # 获取最后一条用户消息
            last_user_msg = next((m for m in reversed(messages) if m.role == "user"), None)
            if last_user_msg:
                # 搜索知识库
                search_results = await self.rag_service.search_knowledge_base(
                    knowledge_base_id, 
                    last_user_msg.content, 
                    limit=5
                )
                if search_results:
                    # 构建上下文
                    context = "\n\n".join([f"文档内容: {r.text}" for r in search_results])
        
        # 处理消息，添加知识库上下文
        processed_messages = messages.copy()
        if context:
            # 找到系统消息或创建一个新的
            sys_msg_idx = next((i for i, m in enumerate(processed_messages) if m.role == "system"), None)
            if sys_msg_idx is not None:
                # 在系统消息中添加上下文
                processed_messages[sys_msg_idx].content += f"\n\n以下是相关的知识库信息，请在回答时参考这些信息：\n{context}"
            else:
                # 创建系统消息
                sys_msg = ChatMessage(
                    role="system",
                    content=f"请在回答时参考以下知识库中的相关信息：\n{context}"
                )
                processed_messages.insert(0, sys_msg)
                
        # 调用模型服务获取回复
        response_text = await self.model_service.generate_text(
            model_id=model_id,
            messages=[{"role": m.role, "content": m.content} for m in processed_messages],
            temperature=temperature
        )
        
        # 创建回复消息
        response_message = ChatMessage(
            role="assistant",
            content=response_text,
            created_at=self._parse_datetime_safely(datetime.now().isoformat()) # Ensure datetime object
        )
        
        # 保存聊天历史
        await self._save_chat_history(chat_id, processed_messages + [response_message], model_id, knowledge_base_id)
        
        return ChatResponse(
            message=response_message,
            chat_id=chat_id
        )
    
    async def chat(
        self,
        context_id: str,
        supplier_name: str,
        model: str,
        parameters: Optional[str] = None,  # 与Electron端保持一致，使用string类型
        user_content: str = "",
        rag_results: Optional[List[Dict[str, Any]]] = None,
        search_results: Optional[List[Dict[str, Any]]] = None,
        search: Optional[str] = None,
        search_provider: Optional[str] = "baidu",
        rag_list: Optional[List[str]] = None,
        regenerate_id: Optional[str] = None,
        images: Optional[str] = None,
        doc_files: Optional[str] = None,
        compare_id: Optional[str] = None,
        mcp_servers: Optional[List[str]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        与Electron端ToChatService.chat方法保持一致的核心聊天方法
        处理完整的对话逻辑，包括RAG、搜索、图片、文档等
        """
        start_time = time.time()
        
        try:
            # 读取并同步 config.json 中的配置
            config_file = self._get_config_file_path(context_id)
            config_data = self._read_json_file(config_file) or {}
            
            config_supplier_name = config_data.get("supplierName", "")
            if supplier_name is None:
                supplier_name = config_supplier_name
            elif supplier_name != config_supplier_name:
                config_data["supplierName"] = supplier_name
                self._write_json_file(config_file, config_data)
            
            config_model = config_data.get("model", "")
            if model is None:
                model = config_model
            elif model != config_model:
                config_data["model"] = model
                self._write_json_file(config_file, config_data)
            
            # 1. 参数解析与处理
            model_info = await self._get_model_info(supplier_name, model)
            if not model_info:
                yield {"error": f"模型信息获取失败: {supplier_name}/{model}"}
                return
            
            # 获取模型上下文长度
            context_length = self._get_context_length(model_info)
            is_vision_model = self._check_is_vision_model(model_info)
            
            # 判断是否为Ollama模型
            is_ollama = supplier_name.lower() == "ollama"
            
            # 2. 参数解析 - 与Electron端保持一致
            images_list = images.split(',') if images else []
            doc_files_list = json.loads(doc_files) if doc_files else []
            rag_list_parsed = rag_list if rag_list else []
            
            # rag_list 不为空时持久化到 config.json
            if rag_list_parsed:
                config_data["rag_list"] = rag_list_parsed
                self._write_json_file(config_file, config_data)
            
            # 2. 获取历史记录和构建消息
            messages = await self._build_messages(
                context_id, user_content, regenerate_id, images_list, doc_files_list,
                is_vision_model, compare_id, search, search_results
            )
            
            # 3. 处理RAG和搜索工具
            current_search_type = search or ""
            current_search_query = ""
            current_search_result: List[Dict[str, Any]] = []
            
            if rag_list_parsed and len(rag_list_parsed) > 0:
                rag_context = await self._handle_rag(messages, rag_list_parsed, user_content)
                if rag_context:
                    # 添加RAG上下文到系统消息
                    self._add_rag_context_to_messages(messages, rag_context)
                    # 记录RAG检索信息，用于保存到历史记录
                    current_search_type = f"[RAG]:{rag_list_parsed}"
                    current_search_query = user_content
                    # 复用已有的 rag_results 作为检索结果；若前端未传则保留空列表
                    current_search_result = rag_results or []
            
            if search:
                search_context = await self._handle_search(messages, search, search_provider or "baidu")
                if search_context:
                    # 添加搜索上下文到系统消息
                    self._add_search_context_to_messages(messages, search_context)
                    current_search_type = search
                    current_search_query = user_content
                    current_search_result = search_results or []
            
            # 4. 处理MCP服务器
            if mcp_servers and len(mcp_servers) > 0:
                mcp_context = await self._handle_mcp_servers(messages, mcp_servers, user_content)
                if mcp_context:
                    self._add_mcp_context_to_messages(messages, mcp_context)
            
            # 5. 处理已存在的RAG和搜索结果
            if rag_results and len(rag_results) > 0:
                self._add_existing_rag_results_to_messages(messages, rag_results)
            
            if search_results and len(search_results) > 0:
                self._add_existing_search_results_to_messages(messages, search_results)
            
            # 6. 格式化消息并计算上下文长度
            formatted_messages = self._format_messages(messages)
            context_used = self._calculate_context_length(formatted_messages)
            
            # 7. 构建请求选项
            request_options = self._build_request_options(
                parameters, model_info, context_length, context_used
            )
            
            # 8. 初始化响应变量
            full_response = ""
            thinking_content = ""
            is_thinking = False
            
            # 9. 处理停止生成逻辑
            stop_event = self._get_stop_event(context_id)
            
            # 10. 调用模型生成响应
            async for chunk in self._generate_response(
                supplier_name, model, formatted_messages, request_options, stop_event
            ):
                if "error" in chunk:
                    yield chunk
                    return
                
                # 处理思考过程标记
                if self._is_thinking_marker(chunk.get("text", "")):
                    is_thinking = not is_thinking
                    continue
                
                if is_thinking:
                    thinking_content += chunk.get("text", "")
                    continue
                
                # 处理非Ollama模型的思维链内容（与Electron端保持一致）
                if not is_ollama and isinstance(chunk, dict):
                    # 检查是否有思维链内容（reasoning_content）
                    reasoning_content = chunk.get("choices", [{}])[0].get("delta", {}).get("reasoning_content", "")
                    if reasoning_content:
                        if not is_thinking:
                            is_thinking = True
                            # 添加思维链开始标记
                            if "<think>" not in reasoning_content:
                                yield "\n<think>\n"
                                thinking_content += "\n<think>\n"
                        yield reasoning_content
                        thinking_content += reasoning_content
                        # 检查思维链结束
                        if "</think>" in reasoning_content:
                            is_thinking = False
                        continue
                    
                    # 处理正常内容
                    if is_thinking:
                        is_thinking = False
                        if "</think>" not in thinking_content:
                            yield "\n</think>\n"
                    
                    normal_content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if normal_content:
                        full_response += normal_content
                        yield normal_content
                else:
                    # Ollama模型或简单文本格式
                    chunk_text = chunk.get("text", "")
                    if chunk_text:
                        full_response += chunk_text
                        yield chunk_text
            
            # 11. 生成统计信息
            end_time = time.time()
            response_info = self._get_response_info(
                supplier_name, model, start_time, end_time, full_response, context_used
            )
            
            # 12. 保存聊天历史
            await self._save_chat_result(
                context_id, messages, full_response, model, supplier_name, parameters,
                compare_id, current_search_type, current_search_query, current_search_result,
                response_info, images_list, doc_files_list, thinking_content
            )
            
        except Exception as e:
            logger.error(f"Chat method error: {e}")
            yield {"error": str(e)}

    async def send_message_stream(
        self,
        messages: List[ChatMessage],
        model_id: str,
        temperature: float = 0.7,
        knowledge_base_id: Optional[str] = None,
        chat_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式发送消息并获取回复 - 兼容旧接口
        """
        # 如果没有提供chat_id，创建一个新的
        if not chat_id:
            chat_id = self._uuid()
            
        # 获取模型
        model = await self.model_service.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
            
        # 处理RAG逻辑，与send_message相同
        context = None
        if knowledge_base_id:
            last_user_msg = next((m for m in reversed(messages) if m.role == "user"), None)
            if last_user_msg:
                search_results = await self.rag_service.search_knowledge_base(
                    knowledge_base_id,
                    last_user_msg.content,
                    limit=5
                )
                if search_results:
                    context = "\n\n".join([f"文档内容: {r.text}" for r in search_results])
        
        # 处理消息
        processed_messages = messages.copy()
        if context:
            sys_msg_idx = next((i for i, m in enumerate(processed_messages) if m.role == "system"), None)
            if sys_msg_idx is not None:
                processed_messages[sys_msg_idx].content += f"\n\n以下是相关的知识库信息，请在回答时参考这些信息：\n{context}"
            else:
                sys_msg = ChatMessage(
                    role="system",
                    content=f"请在回答时参考以下知识库中的相关信息：\n{context}"
                )
                processed_messages.insert(0, sys_msg)
        
        # 用于构建完整响应
        full_response = ""
        
        # 调用模型服务进行流式生成
        async for chunk in self.model_service.generate_text_stream(
            model_id=model_id,
            messages=[{"role": m.role, "content": m.content} for m in processed_messages],
            temperature=temperature
        ):
            # 检查是否有错误
            if isinstance(chunk, dict) and chunk.get("error"):
                yield {
                    "error": chunk["error"],
                    "chat_id": chat_id
                }
                return
            
            # 提取文本内容
            if isinstance(chunk, dict):
                chunk_text = chunk.get("message", {}).get("content", "")
            else:
                chunk_text = str(chunk)
            
            # 更新完整响应
            full_response += chunk_text
            
            # 返回当前块
            yield {
                "text": chunk_text,
                "full_text": full_response,
                "chat_id": chat_id
            }
        
        # 创建并保存完整响应
        response_message = ChatMessage(
            role="assistant",
            content=full_response,
            created_at=self._parse_datetime_safely(datetime.now().isoformat()) # Ensure datetime object
        )
        
        # 保存聊天历史
        await self._save_chat_history(chat_id, processed_messages + [response_message], model_id, knowledge_base_id)
        
    async def get_history(self, chat_id: str) -> List[ChatMessage]:
        """
        获取聊天历史
        """
        # This method is now redundant and will be replaced by get_chat_history
        # The logic was moved to get_chat_history for consistency
        chat_history_obj = await self.get_chat_history(chat_id)
        return chat_history_obj.messages if chat_history_obj else []
    
    async def clear_history(self, chat_id: str) -> bool:
        """
        清除聊天历史（删除整个对话目录）。
        """
        context_dir = self._get_context_path(chat_id)
        if self._file_exists(context_dir):
            try:
                shutil.rmtree(context_dir)
                return True
            except Exception as e:
                print(f"Error deleting chat directory: {e}")
                return False
        return True
    
    async def list_histories(self) -> List[ChatHistory]:
        """
        获取所有聊天历史的列表
        """
        histories = []
        context_dirs = self._readdir(self.context_root_dir)
        
        for context_id in context_dirs:
            config_file = self._get_config_file_path(context_id)
            if self._file_exists(config_file):
                try:
                    config_data = self._read_json_file(config_file)
                    if config_data:
                        # 从config_data构建ChatHistory对象，这里需要填充messages
                        history_file = self._get_history_file_path(context_id)
                        history_messages_data = self._read_json_file(history_file)
                        
                        messages = []
                        if history_messages_data:
                            for msg_data in history_messages_data:
                                # Sanitize and parse datetime fields using the helper
                                msg_data["created_at"] = self._parse_datetime_safely(msg_data.get("created_at", datetime.now()))
                                
                                try:
                                    messages.append(ChatMessage(**msg_data))
                                except Exception as e:
                                    print(f"Warning: Could not load chat message in list_histories (ID: {msg_data.get('id', 'N/A')}) due to validation error: {e}. Skipping this message.")
                                    continue

                        # Sanitize and parse datetime fields for ChatHistory
                        config_data["created_at"] = self._parse_datetime_safely(config_data.get("created_at", datetime.now()))
                        config_data["updated_at"] = self._parse_datetime_safely(config_data.get("updated_at", datetime.now()))

                        history = ChatHistory(
                            id=context_id,
                            title=config_data.get("title", "未知对话"),
                            model_id=config_data.get("model_id", ""),
                            knowledge_base_id=config_data.get("knowledge_base_id"),
                            messages=messages,
                            created_at=config_data["created_at"],
                            updated_at=config_data["updated_at"]
                        )
                        histories.append(history)
                except Exception as e:
                    print(f"Error loading chat history for context_id {context_id}: {e}")
                    continue
        
        # 按更新时间排序
        histories.sort(key=lambda x: x.updated_at, reverse=True)
        return histories
        
    async def get_chat_history(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定对话的完整信息，包括标题、模型、消息等。
        """
        context_dir = self._get_context_path(chat_id)
        config_file = self._get_config_file_path(chat_id)
        history_file = self._get_history_file_path(chat_id)

        if not self._file_exists(config_file):
            return None
            
        try:
            config_data = self._read_json_file(config_file)
            history_messages_data = self._read_json_file(history_file)
            
            messages = []
            if history_messages_data:
                for msg_data in history_messages_data:
                    # Sanitize and parse datetime fields using the helper
                    msg_data["created_at"] = self._parse_datetime_safely(msg_data.get("created_at", datetime.now()))

                    try:
                        messages.append(ChatMessage(**msg_data))
                    except Exception as e:
                        print(f"Warning: Could not load chat message in get_chat_history (ID: {msg_data.get('id', 'N/A')}) due to validation error: {e}. Skipping this message.")
                        continue
            
            if config_data:
                # Sanitize and parse datetime fields for config_data
                config_data["created_at"] = self._parse_datetime_safely(config_data.get("created_at", datetime.now()))
                config_data["updated_at"] = self._parse_datetime_safely(config_data.get("updated_at", datetime.now()))

                chat_info = {
                    "context_id": chat_id,
                    "model": config_data.get("model_id"),
                    "parameters": config_data.get("parameters"),
                    "title": config_data.get("title"),
                    "supplierName": config_data.get("supplier_name"),
                    "agent_name": config_data.get("agent_name"),
                    "create_time": int(config_data["created_at"].timestamp()),
                    "update_time": int(config_data["updated_at"].timestamp()),
                    "contextPath": context_dir,
                    "search_type": "",
                    "rag_list": [],
                    "history": [msg.model_dump(mode='json') for msg in messages]
                }

                # Now, for each message in history, convert created_at to Unix timestamp
                for msg in chat_info["history"]:
                    if "created_at" in msg and isinstance(msg["created_at"], str):
                        try:
                            # Parse the ISO string back to datetime, then to timestamp
                            dt_obj = datetime.fromisoformat(msg["created_at"])
                            msg["created_at"] = int(dt_obj.timestamp())
                        except ValueError:
                            # Fallback if parsing fails, should not happen with _parse_datetime_safely
                            msg["created_at"] = int(datetime.now().timestamp())

                return chat_info
            else:
                return None
        except Exception as e:
            print(f"Error loading full chat history for {chat_id}: {e}")
            return None

    def _merge_history(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并同一个compare_id的历史记录 - 与Electron端mergeHistory保持一致
        """
        merged_history = []
        for history in chat_history:
            compare_id = history.get("compare_id")
            if compare_id is None:
                merged_history.append(history)
                continue

            # 相同compare_id只保留一条user记录
            if history.get("role") == "user":
                index = next((i for i, item in enumerate(merged_history) 
                            if item.get("compare_id") == compare_id and item.get("role") == "user"), -1)
                if index > -1:
                    # 更新现有记录
                    merged_history[index].update(history)
                    continue

            # 合并assistant记录
            if history.get("role") == "assistant":
                index = next((i for i, item in enumerate(merged_history) 
                            if item.get("compare_id") == compare_id and item.get("role") == "assistant"), -1)
                if index > -1:
                    # 合并content和其他字段到数组
                    for key in ["content", "stat", "reasoning"]:
                        if key in history:
                            if not isinstance(merged_history[index].get(key), list):
                                merged_history[index][key] = [merged_history[index].get(key, "")]
                            merged_history[index][key].append(history[key])
                    continue

            merged_history.append(history)
        return merged_history

    def _check_history(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        检查聊天历史记录，确保顺序正确 - 与Electron端checkHistory保持一致
        """
        new_chat_history = []
        user_number = 0
        assistant_number = 0
        
        for history in chat_history:
            role = history.get("role")
            if role == "user":
                if user_number == 0:
                    new_chat_history.append(history)
                    user_number += 1
                    assistant_number = 0  # 重置assistant_number
                else:
                    # 如果已经有一个user了，就不再添加了
                    continue
            elif role == "assistant":
                if assistant_number == 0:
                    new_chat_history.append(history)
                    assistant_number += 1
                    user_number = 0  # 重置user_number
                else:
                    # 如果已经有一个assistant了，就不再添加了
                    continue
        return new_chat_history

    def _format_history(self, chat_history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化聊天历史记录，将同一对话的历史记录合并 - 与Electron端formatHistory保持一致
        """
        merged_history = self._merge_history(chat_history)
        new_chat_history = self._check_history(merged_history)
        return new_chat_history

    async def get_last_chat_history(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """
        获取指定对话的最后一条历史记录 - 与Electron端实现保持一致
        """
        # 读取对话的历史记录
        history_list = self._format_history(self._read_json_file(self._get_history_file_path(chat_id)) or [])
        # 返回最后一条历史记录对象，如果不存在则返回空对象 - 与Electron端保持一致
        return history_list[-1] if history_list else {}

    async def _save_chat_history(
        self, 
        chat_id: str, 
        messages: List[ChatMessage], 
        model_id: str,
        knowledge_base_id: Optional[str] = None
    ) -> None:
        context_path = self._get_context_path(chat_id)
        os.makedirs(context_path, exist_ok=True)

        history_file = self._get_history_file_path(chat_id)
        config_file = self._get_config_file_path(chat_id)

        # Load existing history messages
        existing_messages_data = self._read_json_file(history_file)
        existing_messages: List[ChatMessage] = []
        if existing_messages_data:
            for msg_data in existing_messages_data:
                # Sanitize and parse datetime fields using the helper
                msg_data["created_at"] = self._parse_datetime_safely(msg_data.get("created_at", datetime.now()))
                
                try:
                    existing_messages.append(ChatMessage(**msg_data))
                except Exception as e:
                    print(f"Warning: Could not load existing chat message (ID: {msg_data.get('id', 'N/A')}) due to validation error: {e}. Skipping this message.")
                    continue

        # Combine existing and new messages
        all_messages: List[ChatMessage] = existing_messages + messages

        # Prepare data for saving (ensure datetimes are ISO formatted strings)
        messages_to_save = [msg.model_dump(mode='json') for msg in all_messages]

        # Load existing config if it exists, to preserve other fields like title
        existing_config = self._read_json_file(config_file)
        chat_title = existing_config.get("title", "New Chat") if existing_config else "New Chat"

        # Update config
        config_data = {
            "id": chat_id,
            "title": chat_title,
            "model_id": model_id,
            "knowledge_base_id": knowledge_base_id,
            "created_at": self._parse_datetime_safely(existing_config.get("created_at", datetime.now())).isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self._write_json_file(config_file, config_data)

        # Save history
        self._write_json_file(history_file, messages_to_save)
    
    async def create_chat(
        self, 
        model: str,
        title: str,
        parameters: Optional[str] = None,
        supplier_name: Optional[str] = None,
        agent_name: str = ""
    ) -> Dict[str, Any]:
        """
        创建一个新的聊天会话 - 与Electron端实现保持一致
        """

        # 生成对话的唯一标识符
        context_id = self._uuid()
        
        # 限制标题长度不超过18个字符（与Electron端保持一致）
        if len(title) > 18:
            title = title[:18]
        
        # 构建对话配置对象（与Electron端保持一致）
        context_config = {
            "supplierName": supplier_name or "ollama",
            "model": model,
            "title": title,
            "parameters": parameters or "",
            "contextPath": self._get_context_path(context_id),
            "context_id": context_id,
            "agent_name": agent_name or "",
            "create_time": self._time()
        }
        
        # 保存对话配置信息到文件
        self._write_json_file(self._get_config_file_path(context_id), context_config)
        
        # 创建空的历史记录文件（与Electron端保持一致）
        self._write_json_file(self._get_history_file_path(context_id), [])
        
        # 直接返回context_config对象（与Electron端保持一致）
        return context_config

    async def get_chat_list(self) -> List[Dict[str, Any]]:
        """
        获取对话列表 - 与Electron端实现保持一致
        """
        from app.core.config import get_data_path
        
        chat_list = []
        context_dirs = self._readdir(self.context_root_dir)
        rag_path = os.path.join(get_data_path(), "rag")
        
        for context_id in context_dirs:
            config_file = self._get_config_file_path(context_id)
            if self._file_exists(config_file):
                config_data = self._read_json_file(config_file)
                if config_data:
                    # 处理创建时间 - 与Electron端保持一致
                    create_time = config_data.get("create_time")
                    if create_time is None:
                        # 如果配置中没有创建时间，尝试从文件创建时间获取
                        try:
                            stat_info = os.stat(config_file)
                            create_time = int(stat_info.st_ctime)
                        except Exception:
                            create_time = 0
                    
                    # 处理供应商名称 - 默认为ollama
                    supplier_name = config_data.get("supplierName", "ollama")
                    if supplier_name is None:
                        supplier_name = "ollama"
                    
                    # 处理知识库列表 - 与Electron端保持一致
                    rag_list = []
                    if config_data.get("rag_list"):
                        for rag_name in config_data.get("rag_list"):
                            rag_dir = os.path.join(rag_path, rag_name)
                            rag_config_file = os.path.join(rag_dir, "config.json")
                            if self._file_exists(rag_config_file):
                                rag_list.append(rag_name)
                    
                    # 处理智能体信息 - 与Electron端保持一致
                    agent_info = None
                    if config_data.get("agent_name"):
                        # 这里需要调用agent服务获取智能体信息
                        # 暂时使用简化实现，后续可以集成完整的agent服务
                        agent_info = {"name": config_data.get("agent_name")}
                    
                    # 构建与Electron端一致的返回结构
                    chat_item = {
                        "context_id": context_id,
                        "contextPath": self._get_context_path(context_id),
                        "title": config_data.get("title", "未知对话"),
                        "model": config_data.get("model", config_data.get("model_id", "未知模型")),
                        "supplierName": supplier_name,
                        "agent_name": config_data.get("agent_name", ""),
                        "agent_info": agent_info,
                        "rag_list": rag_list,
                        "parameters": config_data.get("parameters", ""),
                        "create_time": create_time,
                        "search_type": config_data.get("search_type", ""),
                    }
                    
                    chat_list.append(chat_item)
        
        # 按创建时间降序排序 - 与Electron端保持一致
        chat_list.sort(key=lambda x: x.get("create_time", 0), reverse=True)
        
        return chat_list

    async def delete_chat(self, chat_id: str) -> bool:
        """
        删除指定对话及其所有历史记录
        """
        context_dir = self._get_context_path(chat_id)
        if self._file_exists(context_dir):
            try:
                shutil.rmtree(context_dir)
                return True
            except Exception as e:
                print(f"Error deleting chat directory {context_dir}: {e}")
                return False
        return True

    async def update_chat_title(self, chat_id: str, new_title: str) -> bool:
        """
        更新指定对话的标题
        """
        config_file = self._get_config_file_path(chat_id)
        if not self._file_exists(config_file):
            return False
            
        try:
            config_data = self._read_json_file(config_file)
            if config_data:
                config_data["title"] = new_title
                self._write_json_file(config_file, config_data)
                print(f"Updated chat title for {chat_id}: {new_title}")
                return True
            return False
        except Exception as e:
            print(f"Error updating chat title for {chat_id}: {e}")
            return False

    async def delete_chat_history(self, chat_id: str, message_id: str) -> bool:
        """
        删除指定对话中的某条消息 - 与Electron端实现保持一致。
        """
        history_file = self._get_history_file_path(chat_id)
        if not self._file_exists(history_file):
            return False
            
        try:
            history_messages_data = self._read_json_file(history_file)
            if history_messages_data is None:
                return False

            # 过滤掉要删除的历史记录 - 与Electron端实现保持一致
            updated_messages_data = [msg for msg in history_messages_data if msg.get("id") != message_id]
            
            # 保存更新后的历史记录到文件 - 与Electron端实现保持一致
            self._write_json_file(history_file, updated_messages_data)
            return True
        except Exception as e:
            print(f"Error deleting chat history message {message_id} from {chat_id}: {e}")
            return False

    async def stop_generate(self, chat_id: str) -> bool:
        """
        停止指定对话的生成响应。此方法为占位符，实际停止逻辑需根据模型服务实现。
        """
        print(f"Stopping generation for chat_id: {chat_id} (placeholder)")
        # 实际停止逻辑需要在此处添加，例如向正在运行的模型生成任务发送中断信号。
        # 这可能涉及使用一个共享状态（如Redis或内存中的字典）来标记某个chat_id的生成应停止。
        return True

    # === 以下是为chat方法实现的辅助方法 ===
    
    async def _get_model_info(self, supplier_name: str, model: str) -> Optional[Dict[str, Any]]:
        """获取模型信息 - 与Electron端逻辑保持一致"""
        try:
            # 尝试获取模型信息
            model_info = await self.model_service.get_model(f"{supplier_name}/{model}")
            if model_info:
                return model_info
            
            # 如果找不到，尝试只使用模型名查询（兼容Ollama格式）
            model_info = await self.model_service.get_model(model)
            if model_info:
                return model_info
                
            # 如果还是找不到，返回默认模型信息（与Electron端保持一致）
            logger.warning(f"模型信息未找到，使用默认信息: {supplier_name}/{model}")
            return {
                "title": f"{supplier_name}/{model}",
                "supplierName": supplier_name,
                "model": model,
                "size": 0,
                "contextLength": self._get_default_context_length(model),
                "capability": ["llm"]
            }
            
        except Exception as e:
            logger.error(f"获取模型信息失败: {supplier_name}/{model}, error: {e}")
            # 即使出错也返回默认信息，确保流程继续
            return {
                "title": f"{supplier_name}/{model}",
                "supplierName": supplier_name,
                "model": model,
                "size": 0,
                "contextLength": self._get_default_context_length(model),
                "capability": ["llm"]
            }
    
    def _get_default_context_length(self, model: str) -> int:
        """获取模型默认上下文长度 - 与Electron端getModelContextLength保持一致"""
        model_context_obj = {
            "qwq": 32768,
            "qwen2.5": 32768,
            "qwen": 32768,
            "deepseek": 32768,
            "phi": 16384,
            "gemma2": 8192,
            "smollm": 8192,
            "llama": 32768,
            "glm": 32768,
            "qvq": 32768,
        }
        
        model_str_lower = model.lower()
        for key, value in model_context_obj.items():
            if model_str_lower in key:
                return value
        return 32768  # 默认返回32768，与Electron端一致

    def _get_context_length(self, model_info: Dict[str, Any]) -> int:
        """获取模型上下文长度"""
        return model_info.get("contextLength", 4096)  # 默认4K
    
    def _check_is_vision_model(self, model_info: Dict[str, Any]) -> bool:
        """检查是否为视觉模型"""
        model_name = model_info.get("model", "").lower()
        vision_keywords = ["vision", "claude", "gpt-4", "gemini", "llava"]
        return any(keyword in model_name for keyword in vision_keywords)
    
    async def _build_messages(self, context_id: str, user_content: str, regenerate_id: Optional[str], 
                             images: Optional[List[str]], doc_files: Optional[List[Dict[str, Any]]], 
                             is_vision_model: bool, compare_id: Optional[str] = None,
                             search: Optional[str] = None,
                             search_results: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """构建消息列表"""
        messages = []
        
        # 获取历史消息
        history = await self.get_chat_history(context_id)
        if history and history.get("history"):
            messages.extend(history["history"])
        
        # 如果存在regenerate_id，移除该消息之后的历史
        if regenerate_id and messages:
            for i, msg in enumerate(messages):
                if msg.get("id") == regenerate_id:
                    messages = messages[:i]
                    break
        
        # 构建用户消息（字段与Java端createUserMessage保持一致）
        user_message = {
            "id": self._uuid(),
            "role": "user",
            "content": user_content,
            "create_time": self._time(),
            "created_at": datetime.now().isoformat(),
            "compare_id": compare_id or "",
            "reasoning": "",
            "stat": {},
            "images": images if images else [],
            "doc_files": doc_files if doc_files else [],
            "tool_calls": "",
            "tokens": 0,
            "search_result": search_results if search_results else [],
            "search_type": search if search else "",
            "search_query": "",
            "tools_result": []
        }
        
        # 处理图片
        if images and is_vision_model:
            user_message["images"] = images
        
        # 处理文档文件
        if doc_files:
            doc_content = await self._handle_documents(doc_files)
            if doc_content:
                user_message["content"] += f"\n\n文档内容:\n{doc_content}"
        
        messages.append(user_message)
        return messages
    
    async def _handle_documents(self, doc_files: List[Dict[str, Any]]) -> str:
        """处理文档文件，支持直接传入 content 或本地文件 path"""
        doc_content = []
        text_extensions = {".txt", ".md", ".markdown", ".log", ".html", ".htm", ".csv", ".json", ".xml"}
        for doc in doc_files:
            if doc.get("content"):
                doc_content.append(doc["content"])
                continue
            file_path = doc.get("path")
            if file_path and os.path.exists(file_path):
                ext = os.path.splitext(file_path)[1].lower()
                if ext in text_extensions:
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            doc_content.append(f.read())
                    except Exception as e:
                        logger.error(f"读取文档失败: {file_path}, 错误: {e}")
                else:
                    doc_content.append(f"[附件: {os.path.basename(file_path)}]")
        return "\n\n".join(doc_content) if doc_content else ""
    
    async def _handle_rag(self, messages: List[Dict[str, Any]], rag_list: List[str], user_content: str) -> Optional[str]:
        """处理RAG查询"""
        try:
            rag_context = []
            for rag_name in rag_list:
                results = await self.rag_service.search_knowledge_base(rag_name, user_content, limit=3)
                if results:
                    for result in results:
                        rag_context.append(f"知识库 {rag_name}: {result.text}")
            return "\n\n".join(rag_context) if rag_context else None
        except Exception as e:
            logger.error(f"RAG处理失败: {e}")
            return None
    
    def _add_rag_context_to_messages(self, messages: List[Dict[str, Any]], rag_context: str):
        """添加RAG上下文到系统消息"""
        system_msg = next((m for m in messages if m.get("role") == "system"), None)
        if system_msg:
            system_msg["content"] += f"\n\n以下是相关的知识库信息：\n{rag_context}"
        else:
            messages.insert(0, {
                "role": "system",
                "content": f"以下是相关的知识库信息，请在回答时参考：\n{rag_context}",
                "id": self._uuid(),
                "created_at": datetime.now().isoformat()
            })
    
    async def _handle_search(self, messages: List[Dict[str, Any]], search_query: str, search_provider: str = "baidu") -> Optional[str]:
        """处理搜索查询"""
        try:
            from app.services.search_service import SearchService
            search_service = SearchService()
            results = await search_service.search(search_query, search_provider)
            if not results:
                return None
            # 格式化搜索结果为文本上下文
            lines = []
            for idx, item in enumerate(results[:5], 1):
                title = item.get('title', '')
                snippet = item.get('snippet', '') or item.get('content', '')
                url = item.get('url', '')
                lines.append(f"[{idx}] {title}\n{snippet}\n来源：{url}")
            return "\n\n".join(lines)
        except Exception as e:
            logger.error(f"搜索处理失败: {e}")
            return None
    
    def _add_search_context_to_messages(self, messages: List[Dict[str, Any]], search_context: str):
        """添加搜索上下文到系统消息"""
        system_msg = next((m for m in messages if m.get("role") == "system"), None)
        if system_msg:
            system_msg["content"] += f"\n\n以下是相关的搜索结果：\n{search_context}"
        else:
            messages.insert(0, {
                "role": "system",
                "content": f"以下是相关的搜索结果，请在回答时参考：\n{search_context}",
                "id": self._uuid(),
                "created_at": datetime.now().isoformat()
            })
    
    async def _handle_mcp_servers(self, messages: List[Dict[str, Any]], mcp_servers: List[str], user_content: str) -> Optional[str]:
        """处理MCP服务器查询"""
        # MCP服务器功能待实现
        logger.info(f"MCP服务器功能待实现，服务器列表: {mcp_servers}")
        return None
    
    def _add_mcp_context_to_messages(self, messages: List[Dict[str, Any]], mcp_context: str):
        """添加MCP上下文到系统消息"""
        system_msg = next((m for m in messages if m.get("role") == "system"), None)
        if system_msg:
            system_msg["content"] += f"\n\n以下是MCP服务器返回的信息：\n{mcp_context}"
        else:
            messages.insert(0, {
                "role": "system",
                "content": f"以下是MCP服务器返回的信息，请在回答时参考：\n{mcp_context}",
                "id": self._uuid(),
                "created_at": datetime.now().isoformat()
            })
    
    def _add_existing_rag_results_to_messages(self, messages: List[Dict[str, Any]], rag_results: List[Dict[str, Any]]):
        """添加已存在的RAG结果到消息"""
        rag_context = []
        for result in rag_results:
            if result.get("content"):
                rag_context.append(result["content"])
        
        if rag_context:
            self._add_rag_context_to_messages(messages, "\n\n".join(rag_context))
    
    def _add_existing_search_results_to_messages(self, messages: List[Dict[str, Any]], search_results: List[Dict[str, Any]]):
        """添加已存在的搜索结果到消息"""
        search_context = []
        for result in search_results:
            if result.get("content"):
                search_context.append(result["content"])
        
        if search_context:
            self._add_search_context_to_messages(messages, "\n\n".join(search_context))
    
    def _format_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """格式化消息，确保系统消息在最前面且user/assistant交替"""
        if not messages:
            return []
        
        formatted = []
        system_messages = [m for m in messages if m.get("role") == "system"]
        other_messages = [m for m in messages if m.get("role") != "system"]
        
        # 添加系统消息
        formatted.extend(system_messages)
        
        # 确保user和assistant消息交替
        last_role = "system"
        for msg in other_messages:
            current_role = msg.get("role")
            if current_role == "user" and last_role == "user":
                # 跳过连续的user消息
                continue
            if current_role == "assistant" and last_role == "assistant":
                # 跳过连续的assistant消息
                continue
            formatted.append(msg)
            last_role = current_role
        
        return formatted
    
    def _calculate_context_length(self, messages: List[Dict[str, Any]]) -> int:
        """计算消息总长度（估算）"""
        total_length = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_length += len(content)
            # 如果有图片，估算图片描述长度
            if msg.get("images"):
                total_length += len(msg["images"]) * 100  # 粗略估算
        return total_length
    
    def _build_request_options(self, parameters: Optional[str], model_info: Dict[str, Any], 
                              context_length: int, context_used: int) -> Dict[str, Any]:
        """构建请求选项"""
        options = {
            "temperature": 0.7,
            "max_tokens": min(2048, context_length - context_used),
            "stream": True
        }
        
        if parameters:
            try:
                # 尝试解析JSON字符串参数
                import json
                param_dict = json.loads(parameters)
                if isinstance(param_dict, dict):
                    # 合并用户提供的参数
                    if "temperature" in param_dict:
                        options["temperature"] = param_dict["temperature"]
                    if "max_tokens" in param_dict:
                        options["max_tokens"] = param_dict["max_tokens"]
                    if "top_p" in param_dict:
                        options["top_p"] = param_dict["top_p"]
            except (json.JSONDecodeError, ValueError):
                # 如果不是有效的JSON，尝试作为简单字符串处理
                # 例如，可能包含temperature=0.7,max_tokens=1000这样的格式
                import re
                temp_match = re.search(r'temperature[=:]([\d.]+)', parameters)
                if temp_match:
                    options["temperature"] = float(temp_match.group(1))
                
                max_tokens_match = re.search(r'max_tokens[=:](\d+)', parameters)
                if max_tokens_match:
                    options["max_tokens"] = int(max_tokens_match.group(1))
                
                top_p_match = re.search(r'top_p[=:]([\d.]+)', parameters)
                if top_p_match:
                    options["top_p"] = float(top_p_match.group(1))
        
        # Ollama特定参数处理
        model_name = model_info.get("model", "").lower()
        if "ollama" in model_name:
            if "qwen" in model_name:
                options["stop"] = ["<|im_end|>", "<|im_start|>"]
        
        return options
    
    def _get_stop_event(self, context_id: str) -> Any:
        """获取停止事件（占位符）"""
        # 这里需要实现停止机制，暂时返回None
        return None
    
    async def _generate_response(self, supplier_name: str, model: str, messages: List[Dict[str, Any]], 
                                options: Dict[str, Any], stop_event: Any) -> AsyncGenerator[Dict[str, Any], None]:
        """生成模型响应"""
        try:
            # 调用模型服务
            model_id = f"{supplier_name}/{model}"
            
            # 转换消息格式
            formatted_messages = []
            for msg in messages:
                formatted_msg = {
                    "role": msg.get("role"),
                    "content": msg.get("content", "")
                }
                if msg.get("images"):
                    formatted_msg["images"] = msg["images"]
                formatted_messages.append(formatted_msg)
            
            # 调用模型服务进行流式生成
            async for chunk in self.model_service.generate_text_stream(
                model_id=model_id,
                messages=formatted_messages,
                temperature=options.get("temperature", 0.7),
                max_tokens=options.get("max_tokens", 2048)
            ):
                if stop_event and stop_event.is_set():
                    break
                
                # 检查是否有错误
                if isinstance(chunk, dict) and chunk.get("error"):
                    yield {"error": chunk["error"]}
                    return
                
                # 提取文本内容
                if isinstance(chunk, dict):
                    chunk_text = chunk.get("message", {}).get("content", "")
                else:
                    chunk_text = str(chunk)
                
                yield {"text": chunk_text}
                
        except Exception as e:
            logger.error(f"模型响应生成失败: {e}")
            yield {"error": str(e)}
    
    def _is_thinking_marker(self, text: str) -> bool:
        """检查是否为思考过程标记"""
        thinking_markers = ["<think>", "</think>", "【思考中】", "[思考中]"]
        return any(marker in text for marker in thinking_markers)
    
    def _get_response_info(self, supplier_name: str, model: str, start_time: float, end_time: float, 
                          response_text: str, context_used: int) -> Dict[str, Any]:
        """生成响应统计信息，保持与Java端 createDefaultStat 字段一致"""
        generation_time = end_time - start_time
        
        # 估算token数（粗略计算）
        char_count = len(response_text)
        token_count = char_count // 4  # 粗略估算：4字符≈1token
        prompt_tokens = context_used // 4
        
        return {
            "model": model,
            "created_at": datetime.now().isoformat(),
            "total_duration": int(generation_time * 1e9),  # 纳秒
            "load_duration": 0,
            "prompt_eval_count": prompt_tokens,
            "prompt_eval_duration": 0,
            "eval_count": token_count,
            "eval_duration": int(generation_time * 1e9)
        }
    
    async def _save_chat_result(self, context_id: str, messages: List[Dict[str, Any]], response_text: str,
                               model: str, supplier_name: str, parameters: Optional[str],
                               compare_id: Optional[str], search_type: str, search_query: str,
                               search_result: List[Dict[str, Any]], response_info: Dict[str, Any],
                               images: Optional[List[str]], doc_files: Optional[List[Dict[str, Any]]],
                               reasoning: str = ""):
        """保存聊天结果到历史记录（字段与Java端 createAIResponseTemplate 保持一致）"""
        try:
            # 构建助手消息
            assistant_message = {
                "id": self._uuid(),
                "role": "assistant",
                "content": response_text,
                "create_time": self._time(),
                "created_at": datetime.now().isoformat(),
                "compare_id": compare_id or "",
                "reasoning": reasoning or "",
                "stat": response_info if response_info else self._get_response_info(
                    supplier_name, model, time.time(), time.time(), response_text, 0
                ),
                "images": images if images else [],
                "doc_files": doc_files if doc_files else [],
                "tool_calls": "",
                "tokens": 0,
                "search_result": search_result if search_result else [],
                "search_type": search_type or "",
                "search_query": search_query or "",
                "tools_result": []
            }
            
            # 添加到消息列表
            messages.append(assistant_message)
            
            # 保存到文件
            history_file = self._get_history_file_path(context_id)
            self._write_json_file(history_file, messages)
            
            # 更新配置文件的更新时间
            config_file = self._get_config_file_path(context_id)
            config_data = self._read_json_file(config_file)
            if config_data:
                config_data["updated_at"] = datetime.now().isoformat()
                self._write_json_file(config_file, config_data)
                
        except Exception as e:
            logger.error(f"保存聊天历史失败: {e}")