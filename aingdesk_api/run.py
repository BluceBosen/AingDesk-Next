import os
import subprocess
import sys
import time
import argparse
from threading import Thread

def run_api_server():
    """运行API服务器"""
    print("启动 AiDesk API 服务器...")
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # 使用Python执行main.py
    subprocess.run([sys.executable, "main.py"])
    
def run_frontend():
    """运行前端服务"""
    print("启动 AiDesk 前端服务...")
    
    # 前端目录路径，假设前端在相对于当前目录的上一层的frontend目录
    frontend_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend"))
    
    if not os.path.exists(frontend_dir):
        print(f"错误: 前端目录 {frontend_dir} 不存在")
        return
    
    os.chdir(frontend_dir)
    
    # 运行前端开发服务器
    # 注: 在生产环境中，你可能需要构建前端并使用静态文件服务
    try:
        subprocess.run(["npm", "run", "dev"], check=True)
    except subprocess.CalledProcessError:
        print("启动前端服务失败。请确保已安装前端依赖。")
    except FileNotFoundError:
        print("找不到npm命令。请确保已安装Node.js。")
        
def main():
    """主函数，启动所有服务"""
    parser = argparse.ArgumentParser(description='运行AiDesk API服务')
    parser.add_argument('--api-only', action='store_true', help='仅启动API服务，不启动前端')
    args = parser.parse_args()
    
    if args.api_only:
        # 仅运行API服务
        run_api_server()
    else:
        # 在单独的线程中启动API服务器
        api_thread = Thread(target=run_api_server)
        api_thread.daemon = True
        api_thread.start()
        
        # 等待API服务器启动
        print("等待API服务器启动...")
        time.sleep(3)
        
        # 启动前端服务
        run_frontend()
        
        # 如果前端服务退出，主线程将等待API服务器线程
        api_thread.join()
    
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0) 