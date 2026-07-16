import { get, post } from './request'
import type { AgentItem } from '@/types'

export const agentApi = {
  getAgentList: (agent_type?: string, agent_title?: string): Promise<AgentItem[]> =>
    post('/agent/get_agent_list', { agent_type, agent_title }),

  getSystemAgentList: (agent_title?: string): Promise<AgentItem[]> =>
    post('/agent/get_system_agent_list', { agent_title }),

  getCollectAgentList: (agent_title?: string): Promise<AgentItem[]> =>
    post('/agent/get_collect_agent_list', { agent_title }),

  createAgent: (data: {
    agent_type?: string
    agent_name?: string
    agent_title: string
    description?: string
    prompt: string
    icon?: string
    rag_ids?: string[]
    mcp_tool?: string[]
  }): Promise<any> => post('/agent/create_agent', data),

  modifyAgent: (data: {
    agent_type?: string
    agent_name: string
    agent_title: string
    description?: string
    prompt: string
    icon?: string
    is_collect?: boolean
    rag_ids?: string[]
    mcp_tool?: string[]
  }): Promise<any> => post('/agent/modify_agent', data),

  collectAgent: (agent_name: string, is_collect: boolean): Promise<any> =>
    post('/agent/collect_agent', { agent_name, is_collect }),

  removeAgent: (agent_name: string): Promise<any> =>
    post('/agent/remove_agent', { agent_name }),

  getAgentInfo: (agent_name: string): Promise<AgentItem> =>
    post('/agent/get_agent_info', { agent_name }),

  getAgentTypes: (): Promise<string[]> =>
    get('/agent/agent_type_list'),
}
