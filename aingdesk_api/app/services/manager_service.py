import os
import json
import asyncio
import aiohttp
import subprocess
import platform
import shutil
import time
import re
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# 可选导入psutil，如果不存在则提供备用方案
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class ManagerService:
    """模型管理器服务类，主要处理Ollama相关功能"""
    
    def __init__(self):
        self.ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.install_progress = {}
        self.model_install_progress = {}
        self.ollama_executable_path = self._get_ollama_executable_path()
    
    def _get_ollama_executable_path(self) -> str:
        """获取Ollama可执行文件路径"""
        try:
            system = platform.system().lower()
            if system == "windows":
                # Windows下查找ollama.exe
                possible_paths = [
                    os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Ollama", "ollama.exe"),
                    os.path.join(os.environ.get("PROGRAMFILES", ""), "Ollama", "ollama.exe"),
                    "ollama.exe"  # 如果在PATH中
                ]
            elif system == "darwin":  # macOS
                possible_paths = [
                    "/Applications/Ollama.app/Contents/Resources/ollama",
                    "/usr/local/bin/ollama",
                    "ollama"
                ]
            else:  # Linux
                possible_paths = [
                    "/usr/local/bin/ollama",
                    "/usr/bin/ollama",
                    "ollama"
                ]
            
            for path in possible_paths:
                if shutil.which(path) or os.path.exists(path):
                    return path
            
            return "ollama"  # 默认返回ollama命令
        except Exception as e:
            return "ollama"
    
    async def get_ollama_version(self) -> str:
        """获取Ollama版本信息"""
        try:
            # 首先尝试通过HTTP API获取版本信息
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_host}/api/version", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        version = data.get("version", "")
                        if version:
                            return version
        except Exception as e:
            pass
        
        # 如果HTTP方式失败，尝试通过命令行获取版本信息
        try:
            # 执行命令获取 Ollama 版本信息
            result = subprocess.run([self.ollama_executable_path, "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            if result.returncode == 0:
                # 使用正则表达式匹配版本信息
                version_regex = r"version is (\S+)"
                match = re.search(version_regex, result.stdout)
                if match:
                    return match.group(1)
                
                # 尝试其他格式
                version_regex = r"(\d+\.\d+\.\d+)"
                match = re.search(version_regex, result.stdout)
                if match:
                    return match.group(1)
        except Exception as e:
            pass
        
        return ""
    
    async def is_ollama_running(self) -> bool:
        """检查Ollama服务是否运行"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.ollama_host}/api/version", timeout=3) as response:
                    return response.status == 200
        except:
            return False
    
    async def install_model(self, model: str, parameters: str = "") -> Dict[str, Any]:
        """安装模型"""
        try:
            self.model_install_progress[model] = {
                "status": "downloading",
                "progress": 0,
                "message": "开始下载模型...",
                "completed": 0,
                "total": 0
            }
            
            async with aiohttp.ClientSession() as session:
                payload = {"name": model}
                if parameters:
                    payload["options"] = json.loads(parameters) if isinstance(parameters, str) else parameters
                
                async with session.post(
                    f"{self.ollama_host}/api/pull",
                    json=payload,
                    timeout=None
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                try:
                                    progress_data = json.loads(line.decode('utf-8'))
                                    self.model_install_progress[model].update({
                                        "status": progress_data.get("status", "downloading"),
                                        "progress": progress_data.get("completed", 0),
                                        "total": progress_data.get("total", 0),
                                        "message": progress_data.get("status", "下载中...")
                                    })
                                    
                                    if progress_data.get("status") == "success":
                                        self.model_install_progress[model]["status"] = "completed"
                                        self.model_install_progress[model]["message"] = "安装完成"
                                        break
                                except json.JSONDecodeError:
                                    continue
                        
                        return {"success": True, "message": "模型安装完成"}
                    else:
                        self.model_install_progress[model]["status"] = "failed"
                        self.model_install_progress[model]["message"] = "安装失败"
                        return {"success": False, "message": "模型安装失败"}
                        
        except Exception as e:
            self.model_install_progress[model] = {
                "status": "failed",
                "message": f"安装失败: {str(e)}"
            }
            return {"success": False, "message": str(e)}
    
    async def get_model_install_progress(self, model: str, parameters: str = "") -> Dict[str, Any]:
        """获取模型安装进度"""
        return self.model_install_progress.get(model, {
            "status": "not_started",
            "progress": 0,
            "message": "未开始安装",
            "completed": 0,
            "total": 0
        })
    
    async def remove_model(self, model: str, parameters: str = "") -> Dict[str, Any]:
        """删除模型"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"name": model}
                async with session.delete(f"{self.ollama_host}/api/delete", json=payload) as response:
                    if response.status == 200:
                        return {"success": True, "message": "模型删除成功"}
                    else:
                        return {"success": False, "message": "模型删除失败"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def install_ollama(self) -> Dict[str, Any]:
        """安装Ollama"""
        try:
            self.install_progress["ollama"] = {
                "status": "downloading",
                "progress": 0,
                "message": "开始下载Ollama安装程序..."
            }
            
            system = platform.system().lower()
            architecture = platform.machine().lower()
            
            # 根据系统选择下载URL
            if system == "windows":
                if "64" in architecture:
                    download_url = "https://ollama.com/download/OllamaSetup.exe"
                    installer_name = "OllamaSetup.exe"
                else:
                    raise Exception("不支持32位Windows系统")
            elif system == "darwin":  # macOS
                download_url = "https://ollama.com/download/Ollama-darwin.zip"
                installer_name = "Ollama-darwin.zip"
            elif system == "linux":
                download_url = "https://ollama.com/download/install.sh"
                installer_name = "install.sh"
            else:
                raise Exception(f"不支持的操作系统: {system}")
            
            # 下载安装程序
            download_path = await self._download_ollama_installer(download_url, installer_name)
            if not download_path:
                raise Exception("下载Ollama安装程序失败")
            
            # 执行安装
            self.install_progress["ollama"].update({
                "status": "installing",
                "progress": 70,
                "message": "正在安装Ollama..."
            })
            
            success = await self._execute_ollama_installation(download_path, system)
            if not success:
                raise Exception("执行Ollama安装失败")
            
            self.install_progress["ollama"].update({
                "status": "completed",
                "progress": 100,
                "message": "Ollama安装完成"
            })
            
            # 更新可执行文件路径
            self.ollama_executable_path = self._get_ollama_executable_path()
            
            return {"success": True, "message": "Ollama安装成功"}
            
        except Exception as e:
            self.install_progress["ollama"] = {
                "status": "failed",
                "progress": 0,
                "message": f"安装失败: {str(e)}"
            }
            return {"success": False, "message": str(e)}
    
    async def get_ollama_install_progress(self) -> Dict[str, Any]:
        """获取Ollama安装进度"""
        return self.install_progress.get("ollama", {
            "status": "not_started",
            "progress": 0,
            "message": "未开始安装"
        })
    
    async def set_ollama_model_save_path(self, save_path: str) -> Dict[str, Any]:
        """设置Ollama模型保存路径"""
        try:
            if not os.path.exists(save_path):
                os.makedirs(save_path, exist_ok=True)
            
            # 设置环境变量
            os.environ["OLLAMA_MODELS"] = save_path
            
            # 在Windows上，也可以通过注册表设置
            if platform.system() == "Windows":
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE)
                    winreg.SetValueEx(key, "OLLAMA_MODELS", 0, winreg.REG_SZ, save_path)
                    winreg.CloseKey(key)
                except ImportError:
                    pass
            
            return {"success": True, "message": "模型保存路径设置成功", "path": save_path}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def reconnect_model_download(self) -> Dict[str, Any]:
        """重新连接模型下载任务"""
        try:
            # 这里应该实现重新连接下载的逻辑
            # 对于Ollama，通常是重新发起pull请求
            return {"success": True, "message": "重新连接下载任务成功"}
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def _download_ollama_installer(self, download_url: str, installer_name: str) -> Optional[str]:
        """下载Ollama安装程序"""
        try:
            # 创建临时下载目录
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads", "ollama_installer")
            os.makedirs(download_dir, exist_ok=True)
            
            download_path = os.path.join(download_dir, installer_name)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        with open(download_path, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                # 更新下载进度
                                if total_size > 0:
                                    progress = int((downloaded / total_size) * 60)  # 下载占60%进度
                                    self.install_progress["ollama"]["progress"] = progress
                                    self.install_progress["ollama"]["message"] = f"下载中... {progress}%"
                        
                        return download_path
                    else:
                        return None
        except Exception as e:
            return None
    
    async def _execute_ollama_installation(self, installer_path: str, system: str) -> bool:
        """执行Ollama安装"""
        try:
            if system == "windows":
                # Windows下静默安装
                process = await asyncio.create_subprocess_exec(
                    installer_path, "/S",  # 静默安装参数
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                return process.returncode == 0
                
            elif system == "darwin":  # macOS
                # macOS下解压并安装
                extract_dir = os.path.dirname(installer_path)
                process = await asyncio.create_subprocess_exec(
                    "unzip", "-o", installer_path, "-d", extract_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                if process.returncode == 0:
                    # 移动到Applications目录
                    app_path = os.path.join(extract_dir, "Ollama.app")
                    if os.path.exists(app_path):
                        shutil.move(app_path, "/Applications/Ollama.app")
                        return True
                return False
                
            elif system == "linux":
                # Linux下执行安装脚本
                process = await asyncio.create_subprocess_exec(
                    "bash", installer_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                return process.returncode == 0
                
            return False
        except Exception as e:
            return False
    
    def get_ollama_executable_path(self) -> str:
        """获取Ollama可执行文件路径（公开方法）"""
        return self.ollama_executable_path
    
    async def get_ollama_host(self) -> str:
        """获取Ollama主机地址"""
        return self.ollama_host
    
    async def set_ollama_host(self, host: str) -> bool:
        """设置Ollama主机地址"""
        try:
            # 验证新的主机地址是否可用
            old_host = self.ollama_host
            self.ollama_host = host
            
            # 测试连接
            if await self.is_ollama_running():
                # 保存到环境变量
                os.environ["OLLAMA_HOST"] = host
                return True
            else:
                # 恢复原地址
                self.ollama_host = old_host
                return False
        except Exception as e:
            return False
    
    def check_nvidia_smi_exists(self) -> bool:
        """检查nvidia-smi命令是否存在"""
        try:
            result = subprocess.run(["nvidia-smi", "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU信息"""
        gpu_info = {
            "gpu_model": "",
            "gpu_type": "",
            "is_cuda": False,
            "gpu_memory": 0,
            "gpu_free_memory_size": 0
        }
        
        try:
            if self.check_nvidia_smi_exists():
                # 使用nvidia-smi获取GPU信息
                result = subprocess.run([
                    "nvidia-smi", 
                    "--query-gpu=name,memory.total,memory.free",
                    "--format=csv,noheader,nounits"
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if lines:
                        gpu_data = lines[0].split(',')
                        if len(gpu_data) >= 3:
                            gpu_info["gpu_model"] = gpu_data[0].strip()
                            gpu_info["gpu_type"] = "Nvidia"
                            gpu_info["is_cuda"] = True
                            gpu_info["gpu_memory"] = int(gpu_data[1].strip())
                            gpu_info["gpu_free_memory_size"] = int(gpu_data[2].strip())
        except Exception as e:
            print(f"获取GPU信息时出错: {e}")
        
        return gpu_info

    def get_configuration_info(self) -> Dict[str, Any]:
        """获取电脑配置信息
        
        获取当前电脑的详细硬件配置信息，包括CPU、内存、GPU、操作系统等
        """
        config_info = {
            "cpu_model": "",
            "cpu_cores": 0,
            "cpu_clock": "",
            "memory_size": 0,
            "free_memory_size": 0,
            "gpu_model": "",
            "gpu_type": "",
            "is_cuda": False,
            "gpu_memory": 0,
            "gpu_free_memory_size": 0,
            "os_type": "",
            "os_name": "",
            "os_version": "",
            "recommend": ""
        }
        
        try:
            # 获取CPU信息
            try:
                import cpuinfo
                cpu_data = cpuinfo.get_cpu_info()
                config_info["cpu_model"] = cpu_data.get('brand_raw', 'Unknown')
                if PSUTIL_AVAILABLE:
                    config_info["cpu_cores"] = psutil.cpu_count()
                else:
                    config_info["cpu_cores"] = os.cpu_count() or 1
                config_info["cpu_clock"] = f"{cpu_data.get('hz_advertised_friendly', 'Unknown')}"
            except Exception:
                config_info["cpu_model"] = platform.processor() or "Unknown"
                if PSUTIL_AVAILABLE:
                    config_info["cpu_cores"] = psutil.cpu_count()
                else:
                    config_info["cpu_cores"] = os.cpu_count() or 1
            
            # 获取内存信息
            if PSUTIL_AVAILABLE:
                memory = psutil.virtual_memory()
                config_info["memory_size"] = memory.total
                config_info["free_memory_size"] = memory.available
            else:
                config_info["memory_size"] = 8 * 1024 * 1024 * 1024
                config_info["free_memory_size"] = 4 * 1024 * 1024 * 1024
            
            # 获取操作系统信息
            config_info["os_type"] = platform.system()
            config_info["os_name"] = platform.platform()
            config_info["os_version"] = platform.version()
            
            # 获取GPU信息
            gpu_info = self.get_gpu_info()
            config_info["gpu_model"] = gpu_info["gpu_model"]
            config_info["gpu_type"] = gpu_info["gpu_type"]
            config_info["is_cuda"] = gpu_info["is_cuda"]
            config_info["gpu_memory"] = gpu_info["gpu_memory"]
            config_info["gpu_free_memory_size"] = gpu_info["gpu_free_memory_size"]
            
            # 模型选择建议
            if (config_info["cpu_cores"] >= 8 and 
                config_info["memory_size"] >= 15 * 1024 * 1024 * 1024 and
                config_info["is_cuda"] and 
                config_info["gpu_memory"] >= 15 * 1024):
                config_info["recommend"] = "根据您的硬件配置，可以流畅运行大部分中大规模的模型，如：32b、27b、24b、14b、7b 等"
            elif (config_info["cpu_cores"] >= 16 and 
                  config_info["memory_size"] >= 31 * 1024 * 1024 * 1024):
                config_info["recommend"] = "您的硬件配置适合选择中等规模的模型，如: 7b、14b、16b 等"
            else:
                config_info["recommend"] = "由于硬件资源有限，建议选择轻量级的模型，如: 1b、2b 等"
                
        except Exception as e:
            # 异常时保持默认值
            print(f"获取配置信息时出错: {e}")
        
        return config_info