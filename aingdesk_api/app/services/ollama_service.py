import os
import json
import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Any, AsyncGenerator
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 存储每个模型的下载速度和进度信息，键为模型全名，值为包含下载信息的对象
ModelDownloadSpeed = {}
# 模型下载断开重连标志，若模型下载速度变得很慢，可设置该标志重连下载
ReconnectModelDownload = False
ReconnectOllamaDownload = False
# 下载速度列表
ModelDownLoadSpeedList = []
# 最近10秒钟的下载速度列表
ModelDownLoadSpeedList10s = []

# 存储 Ollama 本身的下载速度和进度信息
OllamaDownloadSpeed = {
    "total": 0,
    "completed": 0,
    "speed": 0,
    "progress": 0,
    "status": 0
}

class OllamaService:
    """
    OllamaService 类，提供与 Ollama 相关的操作，如获取版本、管理模型、安装 Ollama 等
    """
    
    def __init__(self):
        self.base_url = "http://localhost:11434"
        
    def get_ollama_bin(self) -> List[str]:
        """
        获取 Ollama 可执行文件的路径
        Returns:
            List[str]: 包含 Ollama 可执行文件路径的数组
        """
        if os.name == 'nt':  # Windows
            # 获取当前用户的本地应用数据目录
            local_app_data = os.environ.get('LOCALAPPDATA')
            if local_app_data:
                # 构建 Windows 系统下 Ollama 可执行文件的完整路径
                ollama_bin = os.path.join(local_app_data, "Programs", "Ollama", "ollama.exe")
                if os.path.exists(ollama_bin):
                    return [ollama_bin, "ollama"]
            return ["ollama"]
        else:
            # 构建 Linux 或 macOS 系统下 Ollama 可执行文件的完整路径
            result = []
            bins = ['/usr/local/bin/ollama', '/usr/bin/ollama', '/sbin/ollama']
            for bin_path in bins:
                if os.path.exists(bin_path):
                    result.append(bin_path)
            result.append("ollama")
            return result

    async def version(self) -> str:
        """
        获取 Ollama 的版本信息
        Returns:
            str: 若成功获取到版本信息则返回版本号，否则返回空字符串
        """
        try:
            # 尝试从11434端口获取版本信息
            try:
                url = f"{self.base_url}/api/version"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=1)) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data and "version" in data:
                                return data["version"]
            except Exception as e:
                logger.error(f"Get ollama version error: {e}")

            # 尝试从命令行获取版本信息
            ollama_bin_list = self.get_ollama_bin()
            for bin_path in ollama_bin_list:
                try:
                    import subprocess
                    result = subprocess.run([bin_path, "--version"], capture_output=True, text=True)
                    if result.returncode == 0:
                        import re
                        version_regex = r"version is (\S+)"
                        match = re.search(version_regex, result.stdout)
                        if match:
                            return match.group(1)
                except Exception as e:
                    logger.error(f"Error getting version from {bin_path}: {e}")
                    continue
            return ""
        except Exception as error:
            logger.error(f"获取 ollama 版本时出错: {error}")
            return ""

    async def is_running(self) -> bool:
        """
        检查 Ollama 是否正在运行
        Returns:
            bool: 若 Ollama 正在运行则返回 true，否则返回 false
        """
        try:
            url = f"{self.base_url}/api/ps"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as response:
                    if response.status == 200:
                        logger.info("Ollama is running")
                        return True
        except Exception as e:
            logger.warning(f"Ollama is not running: {e}")
            return False

    async def start(self) -> bool:
        """
        启动 Ollama 服务
        Returns:
            bool: 若 Ollama 启动成功则返回 true，否则返回 false
        """
        try:
            if os.name == 'nt':  # Windows
                os.system('"ollama app"')
            elif os.name == 'posix':
                if os.path.exists('/etc/os-release'):
                    # Linux
                    os.system('systemctl start ollama')
                else:
                    # macOS
                    os.system('open /Applications/Ollama.app')
            
            await asyncio.sleep(5)
            return True
        except Exception as e:
            logger.error(f"启动 Ollama 服务时出错: {e}")
            return False

    async def generate_text_stream(self, model_id: str, messages: List[Dict[str, Any]], temperature: float = 0.7, max_tokens: int = 4096) -> AsyncGenerator[Dict[str, Any], None]:
        """
        流式文本生成 - 直接调用Ollama API
        Args:
            model_id: 模型ID，格式为"supplier_name/model"
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
        Yields:
            Dict: 包含生成文本的chunk
        """
        try:
            # 解析模型ID，提取模型名称
            model_parts = model_id.split("/")
            if len(model_parts) >= 2:
                model_name = model_parts[1]  # 获取model部分
            else:
                model_name = model_id
            
            # 构建请求数据
            request_data = {
                "model": model_name,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": temperature
                }
            }
            
            # 如果max_tokens有实际限制，添加到options
            if max_tokens and max_tokens > 0:
                request_data["options"]["num_predict"] = max_tokens
            
            url = f"{self.base_url}/api/chat"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama chat API error: {response.status} - {error_text}")
                        yield {
                            "error": f"Ollama API error: {response.status}",
                            "done": True
                        }
                        return
                    
                    # 处理流式响应
                    async for line in response.content:
                        if line:
                            line_text = line.decode('utf-8').strip()
                            if line_text:
                                try:
                                    chunk = json.loads(line_text)
                                    yield chunk
                                except json.JSONDecodeError as e:
                                    logger.error(f"Failed to parse Ollama response: {e}")
                                    continue
                                    
        except Exception as error:
            logger.error(f"Ollama generate_text_stream error: {error}")
            yield {
                "error": str(error),
                "done": True
            }

    async def get_embedding_model_list(self) -> List[Dict[str, Any]]:
        """
        获取嵌套模型列表
        Returns:
            List[Dict]: 包含模型信息的数组，若出错则返回空数组
        """
        models = await self.model_list()
        
        # 过滤出支持嵌套的模型
        result = [model for model in models if model.get("install", False) and "embedding" in model.get("capability", [])]
        
        # 构建模型信息
        result = [{
            "title": f"ollama/{model['full_name']}",
            "supplierName": "ollama",
            "model": model["full_name"],
            "size": model["size"],
            "contextLength": 512
        } for model in result]
        
        return result

    async def model_list(self) -> List[Dict[str, Any]]:
        """
        获取 Ollama 模型列表
        Returns:
            List[Dict]: 包含模型信息的数组，若出错则返回空数组
        """
        try:
            # 构建模型列表文件的完整路径 - 从resources目录读取
            model_list_file = os.path.join(os.path.dirname(__file__), "..", "..", "resources", "ollama_model.json")
            model_list_file = os.path.abspath(model_list_file)
            
            # 初始化模型源列表
            model_list_src = []
            
            # 检查模型列表文件是否存在
            if os.path.exists(model_list_file):
                try:
                    with open(model_list_file, 'r', encoding='utf-8') as f:
                        model_list_src = json.load(f)
                except Exception as e:
                    logger.error(f"读取模型列表文件出错: {e}")
            
            # 获取 Ollama 服务中的模型列表
            url = f"{self.base_url}/api/tags"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        
                        # 将models中存在，但modelListSrc中不存在的模型添加到modelListSrc中
                        for model in models:
                            is_exist = False
                            for model_src in model_list_src:
                                if model_src.get("full_name", "").lower() == model.get("name", "").lower():
                                    is_exist = True
                                    break
                            
                            if not is_exist:
                                arr = model.get("name", "").split(":")
                                if len(arr) >= 2:
                                    model_src = {
                                        "full_name": model["name"],
                                        "name": arr[0],
                                        "parameters": "",
                                        "size": self._format_size(model.get("size", 0)),
                                        "msg": "",
                                        "zh_cn_msg": "",
                                        "link": "",
                                        "pull_count": 0,
                                        "tag_count": 0,
                                        "updated": "",
                                        "updated_time": 0,
                                        "capability": []
                                    }
                                    # 从现有模型中查找同名基础模型的详细信息
                                    for modelInfo in model_list_src:
                                        if model_src.get("name", "").lower() == modelInfo.get("name", "").lower():
                                            model_src["pull_count"] = modelInfo.get("pull_count", 0)
                                            model_src["tag_count"] = modelInfo.get("tag_count", 0)
                                            model_src["updated"] = modelInfo.get("updated", "")
                                            model_src["updated_time"] = modelInfo.get("updated_time", 0)
                                            model_src["capability"] = modelInfo.get("capability", [])
                                            model_src["zh_cn_msg"] = modelInfo.get("zh_cn_msg", "")
                                            model_src["msg"] = modelInfo.get("msg", "")
                                            model_src["link"] = modelInfo.get("link", "")
                                            break
                                    model_list_src.append(model_src)
                        
                        # 处理模型信息，添加安装状态等信息
                        model_list = []
                        for model_info_src in model_list_src:
                            model_info = {
                                "full_name": model_info_src["full_name"],
                                "model": model_info_src["name"],
                                "parameters": model_info_src["parameters"],
                                "download_size": model_info_src["size"],
                                "size": 0,
                                "msg": model_info_src.get("msg", ""),
                                "title": model_info_src.get("msg", ""),
                                "link": model_info_src.get("link", ""),
                                "pull_count": model_info_src.get("pull_count", 0),
                                "tag_count": model_info_src.get("tag_count", 0),
                                "updated": model_info_src.get("updated", ""),
                                "updated_time": model_info_src.get("updated_time", 0),
                                "capability": model_info_src.get("capability", []),
                                "install": False,
                                "running": False,
                                "memory_size": 0,
                                "memory_require": 0,
                                "need_gpu": False,
                                "performance": -1
                            }
                            
                            # 检查模型是否已安装
                            for m in models:
                                if m.get("name", "").lower() == model_info_src["full_name"].lower():
                                    model_info["install"] = True
                                    model_info["size"] = m.get("size", 0)
                                    break
                            
                            model_list.append(model_info)
                        
                        return model_list
                    else:
                        logger.error(f"获取模型列表失败: {response.status}")
                        return []
        except Exception as error:
            logger.error(f"获取 Ollama 模型列表时出错: {error}")
            return []

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    def download_speed_monitoring(self, full_model: str):
        """
        下载速度监控
        Args:
            full_model (str): 模型全名，如：deepseek-r1:1.5b
        """
        global ModelDownLoadSpeedList, ModelDownLoadSpeedList10s, ReconnectModelDownload, ReconnectOllamaDownload
        
        # 获取模型下载信息
        data = None
        if full_model == 'ollama':
            data = OllamaDownloadSpeed
        else:
            data = ModelDownloadSpeed.get(full_model)
            if not data:
                return
        
        # 如果下载状态不是正在下载，则不进行检测
        if data.get("status") != 1:
            return
        
        # 如果下载速度列表长度小于60，则不进行检测
        if len(ModelDownLoadSpeedList) < 60:
            return
        
        # 获取最近1分钟的平均下载速度和最近10秒钟的平均下载速度
        average, average10s = self.get_average_speed()
        
        # 如果最近10秒钟的平均下载速度小于最近1分钟的平均下载速度的1/3，则认为下载速度很慢，重新下载
        if average10s < average / 3:
            logger.warning("检测到下载速度异常，正在尝试重新连接下载节点...")
            if full_model == 'ollama':
                self.reconnect_ollama_download()
            else:
                self.reconnect_model_download()
            
            ModelDownLoadSpeedList = []
            ModelDownLoadSpeedList10s = []

    def append_speed_to_list(self, speed: float):
        """
        添加下载速度到列表
        Args:
            speed (float): 下载速度
        """
        global ModelDownLoadSpeedList, ModelDownLoadSpeedList10s
        
        # 存储最近1分钟的下载速度
        ModelDownLoadSpeedList.append(speed)
        if len(ModelDownLoadSpeedList) > 60:
            ModelDownLoadSpeedList.pop(0)
        
        # 存储最近10秒钟的下载速度
        ModelDownLoadSpeedList10s.append(speed)
        if len(ModelDownLoadSpeedList10s) > 10:
            ModelDownLoadSpeedList10s.pop(0)

    def get_average_speed(self) -> tuple:
        """
        获取平均下载速度
        Returns:
            tuple: (最近1分钟平均速度, 最近10秒平均速度)
        """
        global ModelDownLoadSpeedList, ModelDownLoadSpeedList10s
        
        # 最近1分钟的平均下载速度
        total = sum(ModelDownLoadSpeedList)
        average = total / len(ModelDownLoadSpeedList) if ModelDownLoadSpeedList else 0
        
        # 最近10秒钟的平均下载速度
        total = sum(ModelDownLoadSpeedList10s)
        average10s = total / len(ModelDownLoadSpeedList10s) if ModelDownLoadSpeedList10s else 0
        
        return average, average10s

    async def install_model(self, model: str, parameters: str) -> bool:
        """
        安装指定模型
        Args:
            model (str): 模型名称，如：deepseek-r1
            parameters (str): 模型参数规模，如：1.5b
        Returns:
            bool: 安装成功返回 true，否则返回 false
        """
        global ReconnectModelDownload, ModelDownloadSpeed, ModelDownLoadSpeedList, ModelDownLoadSpeedList10s
        
        full_model = f"{model}:{parameters}"
        
        # 若该模型的下载信息已存在，则删除
        if full_model in ModelDownloadSpeed and not ReconnectModelDownload:
            del ModelDownloadSpeed[full_model]
        
        ReconnectModelDownload = False
        
        try:
            # 发起模型拉取请求，并开启流式响应
            url = f"{self.base_url}/api/pull"
            data = {"model": full_model, "stream": True}
            
            last_time = time.time()
            last_completed = 0
            speed = 0
            set_end = False
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status != 200:
                        logger.error(f"安装模型失败: {response.status}")
                        return False
                    
                    async for line in response.content:
                        if not line:
                            continue
                        
                        try:
                            line_str = line.decode("utf-8").strip()
                            if line_str.startswith("data: "):
                                line_str = line_str[6:]  # 移除 "data: " 前缀
                            
                            if line_str == "[DONE]":
                                break
                            
                            chunk_data = json.loads(line_str)
                            
                            if "digest" in chunk_data:
                                # 计算完成百分比
                                percent = 0
                                if chunk_data.get("completed") and chunk_data.get("total"):
                                    percent = round((chunk_data["completed"] / chunk_data["total"]) * 100)
                                
                                # 计算每秒速度
                                current_time = time.time()
                                if current_time - last_time > 0:
                                    completed = chunk_data.get("completed", 0) - last_completed
                                    speed = completed / (current_time - last_time)
                                    last_time = current_time
                                    last_completed = chunk_data.get("completed", 0)
                                    self.append_speed_to_list(speed)
                                    self.download_speed_monitoring(full_model)
                                
                                if speed < 0:
                                    speed = 0
                                
                                # 构建包含下载信息的对象
                                download_data = {
                                    "digest": chunk_data["digest"],
                                    "status": 2 if set_end else 1,
                                    "progress": percent,
                                    "speed": speed,
                                    "total": chunk_data.get("total", 0),
                                    "completed": chunk_data.get("completed", 0)
                                }
                                
                                if set_end:
                                    download_data["status"] = 2
                                    download_data["progress"] = 100
                                    download_data["speed"] = speed
                                
                                if percent == 100 and not set_end:
                                    set_end = True
                                
                                # 更新该模型的下载信息
                                ModelDownloadSpeed[full_model] = download_data
                                
                                # 检查是否断开重新下载
                                if ReconnectModelDownload:
                                    return True
                            
                            elif chunk_data.get("status") == "success":
                                ModelDownLoadSpeedList = []
                                ModelDownLoadSpeedList10s = []
                                # 模型安装成功，更新下载信息
                                download_data = {
                                    "digest": "",
                                    "status": 3,
                                    "progress": 100,
                                    "speed": 0,
                                    "total": 0,
                                    "completed": 0
                                }
                                ModelDownloadSpeed[full_model] = download_data
                                
                        except Exception as e:
                            logger.error(f"处理流式响应出错: {e}")
                            continue
            
            return True
        except Exception as error:
            logger.error(f"安装模型时出错: {error}")
            return False

    def reconnect_model_download(self):
        """重连模型下载"""
        global ReconnectModelDownload, ReconnectOllamaDownload
        ReconnectModelDownload = True
        ReconnectOllamaDownload = True

    def reconnect_ollama_download(self):
        """重连 Ollama 下载"""
        global ReconnectOllamaDownload
        ReconnectOllamaDownload = True

    def get_model_install_progress(self, model: str, parameters: str) -> Dict[str, Any]:
        """
        获取模型安装进度
        Args:
            model (str): 模型名称，如：deepseek-r1
            parameters (str): 模型参数规模，如：1.5b
        Returns:
            Dict: 包含模型下载进度和速度等信息的对象
        """
        full_model = f"{model}:{parameters}"
        data = ModelDownloadSpeed.get(full_model)
        
        if data:
            return data
        
        return {
            "digest": "",
            "status": 0,
            "progress": 0,
            "speed": 0,
            "total": 0,
            "completed": 0
        }

    async def remove_model(self, model: str, parameters: str) -> Any:
        """
        删除指定模型
        Args:
            model (str): 模型名称，如：deepseek-r1
            parameters (str): 模型参数规模，如：1.5b
        Returns:
            Any: 删除操作的结果
        """
        full_model = f"{model}:{parameters}"
        try:
            url = f"{self.base_url}/api/delete"
            data = {"model": full_model}
            
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, json=data) as response:
                    if response.status == 200:
                        return {"success": True}
                    else:
                        error_text = await response.text()
                        logger.error(f"删除模型失败: {response.status} - {error_text}")
                        return {"success": False, "error": error_text}
        except Exception as error:
            logger.error(f"删除模型时出错: {error}")
            return {"success": False, "error": str(error)}

    async def install_ollama(self) -> bool:
        """
        安装 Ollama
        Returns:
            bool: 安装成功返回 true，否则返回 false
        """
        global ReconnectOllamaDownload, OllamaDownloadSpeed
        
        ReconnectOllamaDownload = False
        
        try:
            # 根据不同操作系统确定下载 URL 和文件路径
            download_info = await self.get_ollama_download_info()
            if not download_info:
                return False
                
            download_url, download_file = download_info
            
            # 如果文件已存在，获取文件大小，准备断点续传
            download_bytes = 0
            if os.path.exists(download_file):
                download_bytes = os.path.getsize(download_file)
            
            # 发起下载请求
            headers = {
                'User-Agent': 'AingDesk/1.0.0',
                'Range': f'bytes={download_bytes}-' if download_bytes > 0 else None
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url, headers=headers) as response:
                    if response.status not in [200, 206]:
                        logger.error(f"下载 Ollama 失败: {response.status}")
                        return False
                    
                    total_size = int(response.headers.get('content-length', 0)) + download_bytes
                    downloaded = download_bytes
                    
                    with open(download_file, 'ab' if download_bytes > 0 else 'wb') as f:
                        async for chunk in response.content.iter_chunked(8192):
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # 更新下载进度
                                OllamaDownloadSpeed = {
                                    "total": total_size,
                                    "completed": downloaded,
                                    "speed": 0,  # 简化的速度计算
                                    "progress": round((downloaded / total_size) * 100) if total_size > 0 else 0,
                                    "status": 1
                                }
                                
                                # 检查是否需要重连
                                if ReconnectOllamaDownload:
                                    return True
            
            return True
        except Exception as error:
            logger.error(f"安装 Ollama 时出错: {error}")
            return False

    async def get_ollama_download_info(self) -> tuple:
        """
        获取 Ollama 下载信息
        Returns:
            tuple: (下载URL, 下载文件路径)
        """
        try:
            # 根据操作系统确定下载 URL
            if os.name == 'nt':  # Windows
                download_url = "https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.exe"
                download_file = os.path.join(os.environ.get('TEMP', '/tmp'), 'ollama-windows-amd64.exe')
            elif os.name == 'posix':
                if os.path.exists('/etc/os-release'):
                    # Linux
                    download_url = "https://github.com/ollama/ollama/releases/latest/download/ollama-linux-amd64"
                    download_file = os.path.join('/tmp', 'ollama-linux-amd64')
                else:
                    # macOS
                    download_url = "https://github.com/ollama/ollama/releases/latest/download/ollama-darwin-amd64"
                    download_file = os.path.join('/tmp', 'ollama-darwin-amd64')
            else:
                return None
            
            return download_url, download_file
        except Exception as e:
            logger.error(f"获取 Ollama 下载信息时出错: {e}")
            return None

    async def ollama_download_end(self, download_file: str) -> None:
        """
        Ollama 下载完成后的处理
        Args:
            download_file (str): 下载文件路径
        """
        try:
            installed = await self.install_ollama_after_download(download_file)
            if installed:
                logger.info("安装完成")
        except Exception as error:
            logger.error(f"安装过程中出现错误: {error}")

    async def install_ollama_after_download(self, download_file: str) -> bool:
        """
        下载完成后安装 Ollama
        Args:
            download_file (str): 下载文件路径
        Returns:
            bool: 安装成功返回 true，否则返回 false
        """
        try:
            if os.name == 'nt':  # Windows
                # Windows 下直接运行安装程序
                os.system(f'"{download_file}"')
            elif os.name == 'posix':
                # Linux/macOS 下赋予执行权限并移动到系统路径
                os.system(f"chmod +x {download_file}")
                os.system(f"sudo mv {download_file} /usr/local/bin/ollama")
            
            return True
        except Exception as e:
            logger.error(f"安装 Ollama 出错: {e}")
            return False