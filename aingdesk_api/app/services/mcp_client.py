import os
import json
import asyncio
import uuid
import aiohttp
from typing import Dict, Any, List, Optional


class MCPClient:
    """
    轻量级 MCP 客户端，用于通过 stdio 或 sse 连接 MCP 服务器并获取工具列表。
    与 AingDesk electron/service/mcp_client.ts 的 getTools 行为对齐。
    """

    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self.transports: Dict[str, Any] = {}
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _build_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params or {}
        }

    async def _create_stdio_transport(self, command: str, args: List[str], env: Dict[str, str]) -> asyncio.subprocess.Process:
        """创建 stdio 传输：启动子进程并返回 Process 对象"""
        merged_env = os.environ.copy()
        if env:
            merged_env.update({k: str(v) for k, v in env.items()})

        # Python 编译的 MCP 服务在重定向到管道时默认会启用块缓冲，
        # 导致 asyncio stdout.readline() 长时间挂起。强制无缓冲输出。
        merged_env.setdefault("PYTHONUNBUFFERED", "1")

        # 处理 npx 命令：与 Electron 端保持一致，使用 bun 执行 npx
        if command == "npx":
            from app.services.mcp_service import McpService
            mcp_service = McpService()
            bun_bin = mcp_service.get_bun_bin()
            if os.path.exists(bun_bin):
                command = bun_bin
                args = ["x", "--bun"] + args
                merged_env.setdefault("NPM_CONFIG_REGISTRY", "https://registry.npmmirror.com")

        return await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=merged_env
        )

    async def _send_stdio_request(self, process: asyncio.subprocess.Process, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """通过 stdio 发送 JSON-RPC 请求并读取响应"""
        raw_request = json.dumps(request) + "\n"
        process.stdin.write(raw_request.encode('utf-8'))
        await process.stdin.drain()

        # 读取响应行
        while True:
            try:
                line = await asyncio.wait_for(process.stdout.readline(), timeout=30.0)
            except asyncio.TimeoutError:
                raise Exception("读取 MCP 响应超时")

            if not line:
                raise Exception("MCP 服务器已关闭输出")

            text = line.decode('utf-8', errors='replace').strip()
            try:
                response = json.loads(text)
                # 跳过通知类消息
                if "id" in response:
                    return response
            except json.JSONDecodeError:
                continue

    async def _create_sse_transport(self, base_url: str) -> Dict[str, Any]:
        """创建 SSE 传输：初始化 session 并返回 endpoint"""
        session = aiohttp.ClientSession()
        # MCP SSE 通常通过 GET /sse 建立事件流，然后 POST 到返回的 endpoint
        sse_url = base_url.rstrip('/') + "/sse"
        response = await session.get(sse_url)
        if response.status != 200:
            await session.close()
            raise Exception(f"无法连接 SSE MCP 服务器: {response.status}")

        # 读取第一个 endpoint 事件
        endpoint = None
        async for line in response.content:
            text = line.decode('utf-8').strip()
            if text.startswith("event: endpoint"):
                continue
            if text.startswith("data:"):
                endpoint = text[5:].strip()
                break

        if not endpoint:
            await session.close()
            raise Exception("SSE MCP 服务器未返回 endpoint")

        # 处理相对路径
        if endpoint.startswith("http"):
            post_url = endpoint
        else:
            post_url = base_url.rstrip('/') + endpoint

        return {"session": session, "post_url": post_url, "response": response}

    async def _send_sse_request(self, transport: Dict[str, Any], request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """通过 SSE 发送 JSON-RPC 请求并读取响应"""
        session: aiohttp.ClientSession = transport["session"]
        post_url = transport["post_url"]

        headers = {"Content-Type": "application/json"}
        async with session.post(post_url, data=json.dumps(request), headers=headers) as response:
            if response.status != 200 and response.status != 202:
                raise Exception(f"SSE 请求失败: {response.status}")

            # 202 表示 Accepted，需要从 SSE 响应流中读取结果
            if response.status == 202:
                sse_response = transport["response"]
                async for line in sse_response.content:
                    text = line.decode('utf-8').strip()
                    if text.startswith("data:"):
                        try:
                            data = json.loads(text[5:].strip())
                            if data.get("id") == request.get("id"):
                                return data
                        except json.JSONDecodeError:
                            continue
                raise Exception("SSE 未收到对应响应")

            return await response.json()

    async def connect_to_server(self, server_config: Dict[str, Any]) -> str:
        """连接到 MCP 服务器，返回 session_id"""
        server_name = server_config.get('name', str(uuid.uuid4()))
        server_type = server_config.get('type', 'stdio')
        command = server_config.get('command', '')
        args = server_config.get('args', []) or []
        env = server_config.get('env', {}) or {}
        base_url = server_config.get('baseUrl', '') or server_config.get('base_url', '')

        if server_type == 'stdio':
            if not command:
                raise Exception("stdio 类型 MCP 服务器缺少 command")
            process = await self._create_stdio_transport(command, args, env)
            self.transports[server_name] = process

            # 发送 initialize 请求
            init_request = self._build_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "aingdesk-mcp-client", "version": "1.0.0"}
            })
            init_response = await self._send_stdio_request(process, init_request)
            if not init_response or "error" in init_response:
                raise Exception(f"MCP initialize 失败: {init_response}")

            # 发送 initialized 通知
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            process.stdin.write(json.dumps(initialized_notification).encode('utf-8') + b"\n")
            await process.stdin.drain()

        elif server_type == 'sse':
            if not base_url:
                raise Exception("sse 类型 MCP 服务器缺少 baseUrl")
            transport = await self._create_sse_transport(base_url)
            self.transports[server_name] = transport

            # SSE 类型也需要 initialize（部分实现要求）
            init_request = self._build_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "aingdesk-mcp-client", "version": "1.0.0"}
            })
            init_response = await self._send_sse_request(transport, init_request)
            if not init_response or "error" in init_response:
                raise Exception(f"MCP SSE initialize 失败: {init_response}")
        else:
            raise Exception(f"不支持的 MCP 服务器类型: {server_type}")

        self.sessions[server_name] = server_config
        return server_name

    async def get_tools(self, server_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取指定 MCP 服务器的工具列表"""
        server_name = await self.connect_to_server(server_config)
        transport = self.transports.get(server_name)
        if not transport:
            raise Exception("MCP 传输未建立")

        list_tools_request = self._build_request("tools/list")

        server_type = server_config.get('type', 'stdio')
        if server_type == 'stdio':
            response = await self._send_stdio_request(transport, list_tools_request)
        else:
            response = await self._send_sse_request(transport, list_tools_request)

        if not response:
            raise Exception("未收到 tools/list 响应")

        if "error" in response:
            raise Exception(f"tools/list 失败: {response['error']}")

        result = response.get("result", {})
        return result.get("tools", [])

    async def cleanup(self):
        """清理所有连接"""
        for server_name, transport in self.transports.items():
            try:
                server_type = self.sessions.get(server_name, {}).get('type', 'stdio')
                if server_type == 'stdio':
                    process: asyncio.subprocess.Process = transport
                    if process.returncode is None:
                        process.terminate()
                        try:
                            await asyncio.wait_for(process.wait(), timeout=5.0)
                        except asyncio.TimeoutError:
                            process.kill()
                            await process.wait()
                else:
                    session: aiohttp.ClientSession = transport.get("session")
                    if session:
                        await session.close()
            except Exception as e:
                print(f"清理 MCP 连接时出错: {e}")

        self.sessions.clear()
        self.transports.clear()
