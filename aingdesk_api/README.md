# AiDesk API

AiDesk API是一个FastAPI后端服务，替代了原AiDesk项目中的Electron后端。它提供了AI大模型部署和使用的所有核心功能，包括：

- 模型管理：支持OpenAI API和本地Ollama模型
- 知识库(RAG)：支持文档处理和向量搜索
- 智能体：可自定义AI助手
- 分享功能：提供在线分享服务
- 聊天功能：支持流式输出

## 安装

1. 确保已安装Python 3.11和pip

2. 克隆仓库并安装依赖：

```bash
git clone <repository_url>
cd AiDesk_api
pip install -r requirements.txt
```

3. 创建并配置`.env`文件（可选）：

```
OPENAI_API_KEY=your_api_key
OPENAI_BASE_URL=https:/.openai.com/v1
OLLAMA_BASE_URL=http://localhost:11434
```

## 运行

```bash
# 开发模式
python main.py

# 或使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 7071 --reload
```

服务将在 http://localhost:7071 上运行，API文档可在 http://localhost:7071/docs 上查看。

## API端点

- `/chat`: 聊天相关API
- `/model`: 模型管理API
- `/rag`: 知识库相关API
- `/agent`: 智能体相关API
- `/share`: 分享功能API

## 数据存储

数据存储在以下目录：

- `data/`: 所有数据存储的根目录
  - `models/`: 模型配置
  - `knowledge_bases/`: 知识库文件
  - `vector_db/`: 向量数据库
  - `agents/`: 智能体配置
  - `shares/`: 分享配置
  - `chat_history/`: 聊天历史记录

## 前端集成

本API服务与原AiDesk的前端兼容，前端项目路径：`../frontend`

要将前端连接到此API，请确保：

1. 前端API请求指向 `http://localhost:7071`
2. WebSocket连接指向 `ws://localhost:7071`

## 许可证

MIT 