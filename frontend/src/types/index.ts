export interface ApiResponse<T = any> {
  status: number
  code: number
  msg: string
  error_msg: string
  message: T
}

export interface ChatItem {
  context_id: string
  title: string
  model: string
  supplier_name?: string
  supplierName?: string
  agent_name?: string
  create_time?: string
  update_time?: string
  rag_list?: string[]
  search_type?: string
}

export interface ChatMessage {
  id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  thinking?: string
  images?: string[]
  files?: string[]
  search_result?: SearchResult[]
  tools_result?: any[]
  created_at?: string
  _thinkOpen?: boolean
}

export interface Supplier {
  supplierName: string
  name?: string
  supplierTitle: string
  title?: string
  status: boolean | string
  baseUrl?: string
  apiKey?: string
  baseUrlExample?: string
  help?: string
  home?: string
  sort?: number
}

export interface SupplierConfig {
  supplierName: string
  supplierTitle: string
  baseUrl: string
  apiKey: string
  baseUrlExample?: string
  status?: boolean
}

export interface SupplierModel {
  modelName: string
  model?: string
  title: string
  status: boolean
  capability: string[]
}

export interface ModelItem {
  model: string
  modelName?: string
  title?: string
  supplier_name?: string
  supplierName?: string
  status?: boolean | string
  capability?: any
}

export interface RagItem {
  ragName: string
  ragDesc: string
  embeddingModel?: string
  supplierName?: string
  docCount?: number
  ragCreateTime?: number
  isPreset?: boolean
}

export interface RagDoc {
  docId: string
  docName: string
  docSize: number
  docStatus: 'pending' | 'processing' | 'completed' | 'failed'
  is_parsed: number
  docCreateTime: number
}

export interface EmbeddingModelItem {
  title: string
  model: string
  supplierName: string
  supplier_name?: string
  [key: string]: any
}

export interface AgentItem {
  agent_name: string
  agent_title: string
  description?: string
  prompt: string
  icon?: string
  agent_type?: string
  is_system?: boolean
  is_collect?: boolean
  rag_ids?: string[]
  mcp_tool?: string[]
}

export interface McpServer {
  name: string
  description: string
  type: 'stdio' | 'sse'
  command: string
  baseUrl?: string
  env?: Record<string, string>
  args?: string[]
  isActive?: boolean
  is_active?: boolean
  tools?: McpTool[]
}

export interface McpServerForm {
  name: string
  description: string
  type: 'stdio' | 'sse'
  command: string
  baseUrl: string
  env: string
  args: string
  isActive: boolean
}

export interface McpServerSavePayload {
  name: string
  description: string
  type: 'stdio' | 'sse'
  command: string
  baseUrl?: string
  env?: Record<string, string>
  args?: string[]
  is_active?: boolean
}

export interface McpTool {
  name: string
  description: string
  is_active: boolean
  inputSchema?: any
}

export interface McpEnvStatus {
  node_npx: number
  python_uv: number
}

export interface SearchResult {
  title: string
  url: string
  content: string
}

// Electron API 类型声明
export interface ElectronAPI {
  getAppVersion: () => Promise<string>
  minimizeWindow: () => void
  maximizeWindow: () => void
  unmaximizeWindow: () => void
  closeWindow: () => void
  isWindowMaximized: () => Promise<boolean>
  onWindowStateChange: (callback: (state: 'maximized' | 'restored') => void) => void
  openFileDialog: (options?: { multiSelections?: boolean; filters?: any[] }) => Promise<Array<{ name: string; path: string }>>
}

/** 本地模型信息 */
export interface LocalModel {
  full_name: string
  model: string
  parameters: string
  download_size: string
  size: number
  msg: string
  title: string
  link: string
  pull_count: number
  tag_count: number
  updated: string
  updated_time: number
  capability: string[]
  install: boolean
  running: boolean
  memory_size: number
  memory_require: number
  need_gpu: boolean
  performance: number
}

/** 模型管理器信息 */
export interface ModelManager {
  manager_name: string
  version: string
  models: LocalModel[]
  status: boolean
  ollama_host: string
}

/** 安装进度 */
export interface InstallProgress {
  status: number
  digest: string
  total: number
  completed: number
  progress: number
  speed: number
  message?: string
}

/** 磁盘信息 */
export interface DiskInfo {
  mountpoint: string
  total: number
  used: number
  free: number
  progress: number
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI
  }
}
