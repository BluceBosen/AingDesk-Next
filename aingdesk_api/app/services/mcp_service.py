import os
import sys
import json
import asyncio
import aiohttp
import subprocess
import platform
import shutil
import zipfile
import concurrent.futures
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import tempfile

# 全局安装状态跟踪，与 AiDesk-1.2.4 的 global.bunInstall / global.uvInstall 对齐
_mcp_install_status = {
    "bun": 0,  # 0=未安装, 1=已安装, 2=安装中
    "uv": 0
}

class McpService:
    """MCP服务类，处理模型控制协议相关功能"""
    
    def __init__(self):
        self.data_dir = os.getenv("DATA_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data"))
        self.mcp_config_file = os.path.join(self.data_dir, "mcp-server.json")
        self.bin_path = os.path.join(self.data_dir, "bin")
        os.makedirs(self.bin_path, exist_ok=True)
        os.makedirs(os.path.dirname(self.mcp_config_file), exist_ok=True)
    
    def get_os_path(self) -> str:
        """获取操作系统路径标识"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            os_name = "win"
        elif system == "darwin":
            os_name = "darwin"
        elif system == "linux":
            os_name = "linux"
        else:
            os_name = "unknown"

        if "arm" in machine or "aarch64" in machine:
            arch = "arm64"
        elif "64" in machine or "amd64" in machine:
            arch = "x64"
        else:
            arch = "x86"

        return f"{os_name}-{arch}"
    
    def get_bin_path(self) -> str:
        """获取二进制文件路径"""
        return self.bin_path
    
    def get_bun_bin(self) -> str:
        """获取bun可执行文件路径"""
        extension = ".exe" if platform.system() == "Windows" else ""
        return os.path.join(self.bin_path, f"bun{extension}")
    
    def get_uv_bin(self) -> str:
        """获取uv可执行文件路径"""
        extension = ".exe" if platform.system() == "Windows" else ""
        return os.path.join(self.bin_path, f"uv{extension}")
    
    async def check_bun_exists(self) -> bool:
        """检查bun是否存在"""
        return os.path.exists(self.get_bun_bin())
    
    async def check_uv_exists(self) -> bool:
        """检查uv是否存在"""
        return os.path.exists(self.get_uv_bin())
    
    async def check_python(self) -> bool:
        """检查Python是否可用"""
        try:
            result = subprocess.run(["python", "--version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            try:
                result = subprocess.run(["python3", "--version"], capture_output=True, text=True, timeout=10)
                return result.returncode == 0
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                return False
    
    async def check_node(self) -> bool:
        """检查Node.js是否可用"""
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def check_npm(self) -> bool:
        """检查npm是否可用"""
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    async def read_mcp_config(self) -> Dict[str, Any]:
        """读取MCP配置文件"""
        try:
            if os.path.exists(self.mcp_config_file):
                with open(self.mcp_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"mcpServers": []}
        except Exception as e:
            return {"mcpServers": []}
    
    async def save_mcp_config(self, servers: List[Dict[str, Any]]) -> bool:
        """保存MCP配置文件"""
        try:
            config = {"mcpServers": servers}
            with open(self.mcp_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            return False
    
    async def get_mcp_servers(self) -> List[Dict[str, Any]]:
        """获取MCP服务器列表"""
        config = await self.read_mcp_config()
        return config.get("mcpServers", [])
    
    async def read_common_mcp_config(self) -> List[Dict[str, Any]]:
        """读取常用MCP配置"""
        # 这里返回一些预定义的常用MCP服务器配置
        return [
            {
                "name": "filesystem",
                "description": "文件系统操作工具",
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "env": {},
                "baseUrl": "",
                "is_install": False
            },
            {
                "name": "brave-search",
                "description": "Brave搜索工具",
                "type": "stdio", 
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {"BRAVE_API_KEY": "YOUR_API_KEY"},
                "baseUrl": "",
                "is_install": False
            },
            {
                "name": "github",
                "description": "GitHub操作工具",
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_TOKEN"},
                "baseUrl": "",
                "is_install": False
            }
        ]
    
    async def get_mcp_server_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定MCP服务器信息"""
        servers = await self.get_mcp_servers()
        for server in servers:
            if server.get('name') == name:
                return server
        return None
    
    async def modify_mcp_server(self, name: str, description: str, server_type: str, 
                              command: str, base_url: str, env: Dict[str, str], 
                              args: List[str], is_active: bool) -> bool:
        """修改MCP服务器"""
        try:
            servers = await self.get_mcp_servers()
            
            for server in servers:
                if server.get('name') == name:
                    server.update({
                        'description': description,
                        'type': server_type,
                        'command': command,
                        'baseUrl': base_url,
                        'env': env,
                        'args': args,
                        'isActive': is_active
                    })
                    break
            else:
                return False
            
            return await self.save_mcp_config(servers)
        except Exception as e:
            return False
    
    async def remove_mcp_server(self, name: str) -> bool:
        """删除MCP服务器"""
        try:
            servers = await self.get_mcp_servers()
            servers = [s for s in servers if s.get('name') != name]
            return await self.save_mcp_config(servers)
        except Exception as e:
            return False
    
    async def add_mcp_server(self, name: str, description: str, server_type: str,
                           command: str, base_url: str, env: Dict[str, str], 
                           args: List[str]) -> bool:
        """添加MCP服务器"""
        try:
            servers = await self.get_mcp_servers()
            
            # 检查是否已存在
            if any(s.get('name') == name for s in servers):
                return False
            
            server = {
                'name': name,
                'description': description,
                'type': server_type,
                'command': command,
                'baseUrl': base_url,
                'env': env,
                'args': args,
                'isActive': True
            }
            
            servers.append(server)
            return await self.save_mcp_config(servers)
        except Exception as e:
            return False
    
    def get_mcp_tools_save_path(self) -> str:
        """获取MCP工具保存路径 - 与Electron端保持一致"""
        tools_path = os.path.join(self.data_dir, 'mcp_tools')
        os.makedirs(tools_path, exist_ok=True)
        return tools_path

    def save_mcp_tools(self, name: str, tools: List[Dict[str, Any]]) -> bool:
        """保存MCP工具列表 - 与Electron端save_mcp_tools保持一致"""
        try:
            tools_path = self.get_mcp_tools_save_path()
            tools_file = os.path.join(tools_path, f"{name}.json")
            
            with open(tools_file, 'w', encoding='utf-8') as f:
                json.dump(tools, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            print(f"保存MCP工具文件时出错: {e}")
            return False

    async def read_mcp_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """读取MCP服务器工具列表 - 与Electron端read_mcp_tools保持一致"""
        try:
            tools_path = self.get_mcp_tools_save_path()
            tools_file = os.path.join(tools_path, f"{server_name}.json")
            
            if not os.path.exists(tools_file):
                return []
            
            with open(tools_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"读取MCP工具文件时出错: {e}")
            return []
    
    async def modify_mcp_tools(self, server_name: str, tools: Dict[str, bool]) -> bool:
        """修改MCP工具可用性"""
        try:
            servers = await self.get_mcp_servers()
            server = next((s for s in servers if s.get('name') == server_name), None)
            if not server:
                return False

            server_tools = server.get('tools', [])
            if isinstance(server_tools, list):
                for tool in server_tools:
                    tool_name = tool.get('name')
                    if tool_name in tools:
                        tool['is_active'] = tools[tool_name]

            # 同步更新工具缓存文件，使 get_mcp_server_list / get_mcp_server_info 能立即读到最新状态
            cached_tools = await self.read_mcp_tools(server_name)
            if isinstance(cached_tools, list):
                for tool in cached_tools:
                    tool_name = tool.get('name')
                    if tool_name in tools:
                        tool['is_active'] = tools[tool_name]
                self.save_mcp_tools(server_name, cached_tools)

            return await self.save_mcp_config(servers)
        except Exception as e:
            print(f"修改MCP工具可用性时出错: {e}")
            return False
    
    def _run_client_get_tools(self, server_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """在线程中运行 MCPClient，使用独立的 ProactorEventLoop 绕过主事件循环限制"""
        if sys.platform == "win32":
            loop = asyncio.ProactorEventLoop()
        else:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        from app.services.mcp_client import MCPClient
        client = MCPClient()
        try:
            return loop.run_until_complete(client.get_tools(server_config))
        finally:
            loop.run_until_complete(client.cleanup())
            loop.close()

    async def get_mcp_tools(self, server_name: str) -> List[Dict[str, Any]]:
        """获取MCP服务器工具 - 通过MCP协议真正连接服务器获取"""
        try:
            servers = await self.get_mcp_servers()
            server = next((s for s in servers if s.get('name') == server_name), None)
            if not server:
                return []

            # Windows 下 uvicorn reload 可能使用 SelectorEventLoop，不支持 asyncio 子进程。
            # 在线程中创建独立的 ProactorEventLoop 来执行 MCP 客户端。
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                tools = await loop.run_in_executor(executor, self._run_client_get_tools, server)

            # 读取本地缓存中的启用状态，避免重新获取时覆盖用户手动关闭的开关
            existing_tools = await self.read_mcp_tools(server_name)
            existing_active_map = {}
            if isinstance(existing_tools, list):
                existing_active_map = {
                    t.get('name'): t.get('is_active', True) for t in existing_tools if t.get('name')
                }

            # 转换为前端统一的 ToolInfo 格式，并保留本地启用状态
            formatted_tools = []
            for tool in tools:
                tool_name = tool.get('name', '')
                formatted_tools.append({
                    'name': tool_name,
                    'description': tool.get('description', ''),
                    'is_active': existing_active_map.get(tool_name, True),
                    'inputSchema': tool.get('inputSchema', tool.get('input_schema', {}))
                })

            # 保存到本地缓存
            if formatted_tools:
                self.save_mcp_tools(server_name, formatted_tools)

            return formatted_tools
        except Exception as e:
            print(f"获取MCP工具列表时出错: {e}")
            # 失败时回退到本地缓存
            return await self.read_mcp_tools(server_name)

    async def get_status(self) -> Dict[str, int]:
        """获取环境状态 - 与Electron端 global 状态对齐"""
        global _mcp_install_status

        if _mcp_install_status["bun"] == 2:
            # 如果状态为安装中，但实际已存在，则修正为已安装
            if await self.check_bun_exists():
                _mcp_install_status["bun"] = 1
        else:
            _mcp_install_status["bun"] = 1 if await self.check_bun_exists() else 0

        if _mcp_install_status["uv"] == 2:
            if await self.check_uv_exists():
                _mcp_install_status["uv"] = 1
        else:
            _mcp_install_status["uv"] = 1 if await self.check_uv_exists() else 0

        return {
            "node_npx": _mcp_install_status["bun"],
            "python_uv": _mcp_install_status["uv"]
        }

    async def install_npx(self) -> Dict[str, Any]:
        """安装Node.js环境（通过bun）- 与Electron端保持一致"""
        global _mcp_install_status
        try:
            if await self.check_bun_exists():
                _mcp_install_status["bun"] = 1
                return {"success": True, "message": "已安装"}

            _mcp_install_status["bun"] = 2

            os_path = self.get_os_path()
            download_url = f"https://aingdesk.bt.cn/bin/{os_path}/bun.zip"

            bun_zip_file = os.path.join(self.bin_path, "bun.zip")
            await self.download_file(download_url, bun_zip_file)
            
            # 解压缩
            with zipfile.ZipFile(bun_zip_file, 'r') as zip_ref:
                zip_ref.extractall(self.bin_path)
            
            # 删除压缩包
            os.remove(bun_zip_file)

            # Linux/Mac 设置执行权限
            bun_bin = self.get_bun_bin()
            if os.path.exists(bun_bin) and platform.system() != "Windows":
                os.chmod(bun_bin, 0o755)

            _mcp_install_status["bun"] = 1 if await self.check_bun_exists() else 0
            return {"success": True, "message": "安装成功"}
        except Exception as e:
            _mcp_install_status["bun"] = 0
            print(f"安装Bun失败: {e}")
            return {"success": False, "message": f"安装Bun失败: {str(e)}"}

    async def install_uv(self) -> Dict[str, Any]:
        """安装Python uv环境 - 与Electron端保持一致"""
        global _mcp_install_status
        try:
            if await self.check_uv_exists():
                _mcp_install_status["uv"] = 1
                return {"success": True, "message": "已安装"}

            _mcp_install_status["uv"] = 2

            os_path = self.get_os_path()
            download_url = f"https://aingdesk.bt.cn/bin/{os_path}/uv.zip"

            uv_zip_file = os.path.join(self.bin_path, "uv.zip")
            await self.download_file(download_url, uv_zip_file)
            
            # 解压缩
            with zipfile.ZipFile(uv_zip_file, 'r') as zip_ref:
                zip_ref.extractall(self.bin_path)
            
            # 删除压缩包
            os.remove(uv_zip_file)

            # Linux/Mac 设置执行权限
            uv_bin = self.get_uv_bin()
            if os.path.exists(uv_bin) and platform.system() != "Windows":
                os.chmod(uv_bin, 0o755)

            _mcp_install_status["uv"] = 1 if await self.check_uv_exists() else 0
            return {"success": True, "message": "安装成功"}
        except Exception as e:
            _mcp_install_status["uv"] = 0
            print(f"安装uv失败: {e}")
            return {"success": False, "message": f"安装uv失败: {str(e)}"}

    async def download_file(self, url: str, destination: str) -> bool:
        """下载文件 - 支持断点续传，与Electron端保持一致"""
        headers = {
            'User-Agent': 'AiDesk/1.0.0'
        }
        downloaded_bytes = 0

        if os.path.exists(destination):
            downloaded_bytes = os.path.getsize(destination)

        if downloaded_bytes > 0:
            headers['Range'] = f"bytes={downloaded_bytes}-"

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                # 416 表示文件已经下载完成
                if response.status == 416:
                    return True

                if response.status not in (200, 206):
                    err = f"下载失败，状态码: {response.status}, URL: {url}"
                    print(f"[MCP] {err}")
                    raise Exception(err)

                mode = 'ab' if downloaded_bytes > 0 and response.status == 206 else 'wb'
                with open(destination, mode) as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

        return True
    
    async def get_mcp_config_body(self) -> Optional[str]:
        """获取MCP配置文件内容"""
        try:
            config = await self.read_mcp_config()
            return json.dumps(config, ensure_ascii=False, indent=4)
        except Exception as e:
            return None
    
    async def save_mcp_config_body(self, config_body: str) -> bool:
        """保存MCP配置文件内容"""
        try:
            config = json.loads(config_body)
            if 'mcpServers' not in config:
                return False
            
            servers = config['mcpServers']
            return await self.save_mcp_config(servers)
        except Exception as e:
            return False
    
    async def get_registry_list(self) -> Dict[str, List[Dict[str, str]]]:
        """获取pypi和npm的源列表"""
        return {
            "pypi": [
                {
                    "name": "pypi",
                    "url": "https://pypi.python.org/simple",
                    "description": "Python官方源"
                },
                {
                    "name": "清华大学源",
                    "url": "https://pypi.tuna.tsinghua.edu.cn/simple",
                    "description": "清华大学源，适合中国用户"
                }
            ],
            "npm": [
                {
                    "name": "npm",
                    "url": "https://registry.npmjs.org",
                    "description": "npm官方源"
                },
                {
                    "name": "淘宝源",
                    "url": "https://registry.npmmirror.com",
                    "description": "淘宝源，适合中国用户"
                }
            ]
        }
    
    async def sync_cloud_mcp(self) -> Dict[str, Any]:
        """同步云端MCP配置"""
        try:
            # 这里应该从云端同步MCP配置
            # 暂时返回成功
            return {"success": True, "message": "同步成功"}
        except Exception as e:
            return {"success": False, "message": f"同步失败: {str(e)}"}