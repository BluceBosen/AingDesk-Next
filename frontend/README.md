# AingDesk Frontend

AingDesk 桌面端前端项目，基于 Electron + Vue 3 + TypeScript + Vite 构建，对接 [aingdesk_api](https://github.com/aingdesk/AingDesk) 后端服务。

---

## 技术栈

- **Electron** — 跨平台桌面应用框架
- **Vue 3** — 渐进式前端框架（Composition API）
- **TypeScript** — 类型安全的 JavaScript 超集
- **Vite** — 下一代前端构建工具
- **Vue Router** — 官方路由管理
- **Pinia** — 轻量级状态管理
- **Tailwind CSS** — 原子化 CSS 框架
- **Axios** — HTTP 客户端
- **MarkdownIt + Highlight.js** — Markdown 渲染与代码高亮

---

## 项目结构

```
frontend/
├── electron/                # Electron 主进程与预加载脚本
│   ├── main.ts              # 主进程入口（窗口创建、生命周期）
│   └── preload.ts           # 预加载脚本（安全桥接）
├── src/
│   ├── api/                 # HTTP API 接口封装
│   │   ├── request.ts       # Axios 实例与拦截器、流式请求封装
│   │   ├── chat.ts          # 对话相关接口
│   │   ├── model.ts         # 模型管理接口
│   │   ├── rag.ts           # 知识库接口
│   │   ├── agent.ts         # 智能体接口
│   │   ├── mcp.ts           # MCP 服务器接口
│   │   ├── search.ts        # 搜索接口
│   │   ├── share.ts         # 分享接口
│   │   └── index.ts         # 通用接口（设置、上传等）
│   ├── assets/styles/       # 全局样式
│   │   ├── index.scss       # 主题变量、滚动条、动画等
│   │   └── tailwind.css     # Tailwind 入口
│   ├── components/          # 公共 Vue 组件
│   ├── composables/         # 组合式函数
│   ├── router/
│   │   └── index.ts         # 路由配置
│   ├── stores/
│   │   └── global.ts        # Pinia 全局状态（主题、侧边栏、API 地址）
│   ├── types/
│   │   └── index.ts         # TypeScript 类型定义
│   ├── views/               # 页面视图
│   │   ├── Layout/          # 全局布局（侧边栏 + 主内容区）
│   │   ├── Chat/            # 对话页（流式输出、Markdown、代码高亮）
│   │   ├── Models/          # 模型管理
│   │   ├── Knowledge/       # 知识库
│   │   ├── Agent/           # 智能体
│   │   ├── Mcp/             # MCP 配置
│   │   ├── Share/           # 分享管理
│   │   └── Settings/        # 系统设置
│   ├── App.vue              # 根组件
│   └── main.ts              # Vue 应用入口
├── index.html               # HTML 模板
├── package.json             # 项目依赖与脚本
├── vite.config.ts           # Vite + Electron 插件配置
├── tailwind.config.js       # Tailwind 配置
├── postcss.config.js        # PostCSS 配置
├── tsconfig.json            # TypeScript 配置
└── tsconfig.node.json       # Node 端 TS 配置
```

---

## 快速开始

### 1. 安装依赖

```bash
npm install
```

> Electron 体积较大，首次安装可能需要一些时间。

### 2. 启动开发环境

```bash
npm run dev
```

该命令会同时启动：
- **Vite 开发服务器**：`http://localhost:5173`
- **Electron 桌面窗口**：自动加载上述开发服务器地址

前端代码修改后会热更新，Electron 主进程代码修改后会自动重启。

### 3. 构建生产包

```bash
npm run build
```

构建产物：
- 前端资源：`dist/`
- Electron 主进程：`dist-electron/`
- 安装包：`release/`（由 `electron-builder` 生成）

---

## 后端对接

本项目作为纯前端，通过 **HTTP** 直接对接 `aingdesk_api` 后端服务。

- 默认后端地址：`http://localhost:7071`
- 可在「设置」页面中修改后端 API 地址
- 确保后端服务已启动且 CORS 配置允许跨域访问

开发模式下，Vite 代理了 `/api` 前缀的请求到后端：
```ts
// vite.config.ts
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:7071',
      changeOrigin: true,
    },
  },
}
```

---

## 功能页面

| 页面 | 路径 | 说明 |
|------|------|------|
| 对话 | `/chat` | 核心页面，支持多会话、流式 SSE 输出、Markdown 渲染、代码高亮、思考过程折叠、联网搜索、模型切换 |
| 模型 | `/models` | 第三方模型供应商管理（新增/编辑/删除/启用），Ollama 本地模型展示 |
| 知识库 | `/knowledge` | 知识库列表与基础管理 |
| 智能体 | `/agent` | 智能体列表与基础管理 |
| MCP | `/mcp` | MCP 服务器配置（启用/禁用/增删改） |
| 分享 | `/share` | 分享链接管理与复制 |
| 设置 | `/settings` | 主题切换（浅色/深色）、后端 API 地址配置 |

---

## 主题与样式

- 支持 **浅色 / 深色 / 跟随系统** 三种模式
- 基于 CSS 变量实现主题切换，过渡动画平滑
- 全局圆角卡片风格，阴影柔和
- 主题色：`#4f46e5`（靛蓝）

---

## 开发注意事项

1. **Electron 主进程** 代码位于 `electron/` 目录，使用 Node.js API，与前端代码隔离。
2. **预加载脚本** `electron/preload.ts` 是前后端安全通信的唯一桥梁。
3. **流式对话** 使用 `fetch` + `ReadableStream` 实现 SSE 效果，相关封装在 `src/api/request.ts` 的 `streamPost` 中。
4. **类型安全**：所有 API 接口与数据结构均已定义 TypeScript 类型，位于 `src/types/index.ts`。

---

## 协议

本项目为 AingDesk 的前端重构实现，仅供学习与研究使用。
