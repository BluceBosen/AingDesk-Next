import { post } from './request'
import type { McpServer, McpServerSavePayload, McpTool, McpEnvStatus } from '@/types'

export const mcpApi = {
  /** 获取已安装的 MCP 服务器列表 */
  getServerList: (): Promise<McpServer[]> => post('/mcp/get_mcp_server_list', {}),

  /** 获取常用/预设 MCP 服务器列表 */
  getCommonServerList: (): Promise<any> => post('/mcp/get_common_server_list', {}),

  /** 获取单个 MCP 服务器信息（含工具缓存） */
  getServerInfo: (name: string): Promise<McpServer> =>
    post('/mcp/get_mcp_server_info', { name }),

  /** 添加 MCP 服务器 */
  addServer: (data: McpServerSavePayload): Promise<any> =>
    post('/mcp/add_mcp_server', data),

  /** 修改 MCP 服务器 */
  modifyServer: (data: McpServerSavePayload): Promise<any> =>
    post('/mcp/modify_mcp_server', data),

  /** 删除 MCP 服务器 */
  removeServer: (name: string): Promise<any> =>
    post('/mcp/remove_mcp_server', { name }),

  /** 通过 MCP 协议真正获取服务器工具列表 */
  getTools: (name: string): Promise<McpTool[]> =>
    post('/mcp/get_mcp_tools', { name }),

  /** 修改工具启用状态 */
  modifyTools: (data: { name: string; tools: Record<string, boolean> }): Promise<any> =>
    post('/mcp/modify_mcp_tools', data),

  /** 检查 Node.js / Python 环境状态 */
  getStatus: (): Promise<McpEnvStatus> => post('/mcp/get_status', {}),

  /** 安装 Node.js 运行环境（后台任务） */
  installNpx: (): Promise<any> => post('/mcp/install_npx', {}),

  /** 安装 Python 运行环境 */
  installUv: (): Promise<any> => post('/mcp/install_uv', {}),

  /** 获取 MCP 配置文件原始 JSON */
  getConfigBody: (): Promise<{ mcp_config_body: string }> =>
    post('/mcp/get_mcp_config_body', {}),

  /** 保存 MCP 配置文件原始 JSON */
  saveConfigBody: (mcp_config_body: string): Promise<any> =>
    post('/mcp/save_mcp_config_body', { mcp_config_body }),

  /** 同步云端 MCP 预设列表 */
  syncCloudMcp: (): Promise<any> => post('/mcp/sync_cloud_mcp', {}),
}
