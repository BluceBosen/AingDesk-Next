import axios from 'axios'
import { post } from './request'
import type { ChatItem } from '@/types'

export const chatApi = {
  getChatList: (): Promise<ChatItem[]> => post('/chat/get_chat_list'),

  createChat: (data: {
    model: string
    parameters?: string
    title: string
    supplierName?: string
    agent_name?: string
  }): Promise<any> => post('/chat/create_chat', data),

  getChatHistory: (data: { context_id: string }): Promise<any> =>
    post('/chat/get_chat_info', data),

  sendMessage: (data: {
    context_id: string
    model: string
    supplierName?: string
    parameters?: string
    user_content: string
    search?: string
    searchProvider?: string
    images?: string
    doc_files?: string
    rag_list?: string[]
    regenerate_id?: string
    mcp_servers?: string[]
  }, onProgress?: (text: string) => void): Promise<void> => {
    return axios.post(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:7071'}/chat/chat`, data, {
      responseType: 'text',
      onDownloadProgress: (progressEvent: any) => {
        const xhr = progressEvent.event?.currentTarget
        const text = xhr?.responseText || ''
        onProgress?.(text)
      },
    })
  },

  stopGenerate: (data: { context_id: string }): Promise<any> =>
    post('/chat/stop_generate', data),

  modifyTitle: (data: { context_id: string; title: string }): Promise<any> =>
    post('/chat/modify_chat_title', data),

  removeChat: (data: { context_id: string }): Promise<any> =>
    post('/chat/remove_chat', data),

  getModelList: (): Promise<any> => post('/chat/get_model_list'),
}
