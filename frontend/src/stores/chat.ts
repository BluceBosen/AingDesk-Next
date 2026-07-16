import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { useGlobalStore } from '@/stores/global'
import { useSettingsStore } from '@/stores/settings'
import { toast } from 'vue3-toastify'
import { chatApi } from '@/api/chat'
import { ragApi } from '@/api/rag'
import { mcpApi } from '@/api/mcp'
import type { ChatItem, ChatMessage, RagItem, McpServer, AgentItem } from '@/types'

export const useChatStore = defineStore('chat', () => {
  // 会话列表
  const chatList = ref<ChatItem[]>([])
  const currentChatId = ref('')
  const currentChatTitle = ref('')

  // 消息
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)

  // 输入
  const inputText = ref('')

  // 工具开关
  const enableSearch = ref(false)

  // 上传附件
  const uploadedFiles = ref<{ name: string; path: string }[]>([])
  const uploadedImages = ref<string[]>([])

  // 模型
  const modelList = ref<any[]>([])
  const currentModel = ref('')
  const currentSupplier = ref('')

  // 知识库
  const knowledgeList = ref<RagItem[]>([])
  const selectedKnowledge = ref<string[]>([])

  // MCP
  const mcpList = ref<McpServer[]>([])
  const selectedMcp = ref<string[]>([])

  // 当前绑定的智能体
  const currentAgent = ref<AgentItem | null>(null)

  const canSend = computed(() => {
    return (inputText.value.trim() || uploadedFiles.value.length || uploadedImages.value.length) && !isLoading.value
  })

  const hasActiveChat = computed(() => !!currentChatId.value)

  // 加载会话列表
  const loadChatList = async () => {
    try {
      const res = await chatApi.getChatList()
      chatList.value = res || []
    } catch (e) {
      console.error('加载对话列表失败', e)
    }
  }

  // 选择会话
  const selectChat = async (contextId: string) => {
    currentChatId.value = contextId
    messages.value = []
    uploadedFiles.value = []
    uploadedImages.value = []
    try {
      const res = await chatApi.getChatHistory({ context_id: contextId })
      if (res && res.history) {
        messages.value = res.history.map((h: any) => ({
          id: h.id,
          role: h.role,
          content: h.content || '',
          thinking: h.thinking,
          images: h.images,
          files: h.files,
          search_result: h.search_result,
          tools_result: h.tools_result,
          _thinkOpen: false,
        }))
      }
      const chat = chatList.value.find(c => c.context_id === contextId)
      currentChatTitle.value = chat?.title || ''
      // 恢复模型和工具状态
      if (chat) {
        currentModel.value = chat.model || currentModel.value
        currentSupplier.value = (chat.supplier_name || chat.supplierName || currentSupplier.value).toLowerCase()
        selectedKnowledge.value = chat.rag_list || []
        enableSearch.value = !!chat.search_type
      }
    } catch (e) {
      console.error('加载历史失败', e)
    }
  }

  // 创建新会话
  const createChat = async (title = '新对话') => {
    if (!currentModel.value) return null
    try {
      const res = await chatApi.createChat({
        model: currentModel.value,
        parameters: '',
        title: title.length > 20 ? title.slice(0, 20) : title,
        supplierName: currentSupplier.value,
        agent_name: currentAgent.value?.agent_name,
      })
      if (res && res.context_id) {
        currentChatId.value = res.context_id
        messages.value = []
        uploadedFiles.value = []
        uploadedImages.value = []
        await loadChatList()
        return res.context_id
      }
    } catch (e) {
      console.error('创建对话失败', e)
    }
    return null
  }

  // 新建空对话
  const makeNewChat = () => {
    currentChatId.value = ''
    currentChatTitle.value = ''
    messages.value = []
    inputText.value = ''
    uploadedFiles.value = []
    uploadedImages.value = []
    selectedKnowledge.value = []
    selectedMcp.value = []
    currentAgent.value = null
  }

  // 删除会话
  const removeChat = async (contextId: string) => {
    try {
      await chatApi.removeChat({ context_id: contextId })
      if (currentChatId.value === contextId) {
        makeNewChat()
      }
      await loadChatList()
    } catch (e) {
      console.error('删除对话失败', e)
    }
  }

  // 修改会话标题
  const modifyChatTitle = async (contextId: string, title: string) => {
    try {
      await chatApi.modifyTitle({ context_id: contextId, title })
      if (currentChatId.value === contextId) {
        currentChatTitle.value = title
      }
      await loadChatList()
    } catch (e) {
      console.error('修改标题失败', e)
    }
  }

  // 发送消息
  const sendMessage = async () => {
    let text = inputText.value.trim()
    if (!canSend.value) return

    if (!currentModel.value) {
      toast.warning('请先选择模型')
      return
    }

    // 仅有附件时补充默认提示
    if (!text && (uploadedFiles.value.length || uploadedImages.value.length)) {
      text = '请查看附件'
    }

    // 没有当前会话则先创建
    if (!currentChatId.value) {
      const contextId = await createChat(text || '新对话')
      if (!contextId) return
    }

    // 用户消息
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      files: uploadedFiles.value.map(f => f.name),
      images: uploadedImages.value,
    }
    messages.value.push(userMsg)

    const savedFiles = [...uploadedFiles.value]
    const savedImages = [...uploadedImages.value]
    inputText.value = ''
    uploadedFiles.value = []
    uploadedImages.value = []

    isLoading.value = true

    const assistantMsg: ChatMessage = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      thinking: '',
      _thinkOpen: false,
    }
    messages.value.push(assistantMsg)
    const assistantIdx = messages.value.length - 1

    const settingsStore = useSettingsStore()

    try {
      await chatApi.sendMessage({
        context_id: currentChatId.value,
        model: currentModel.value,
        supplierName: currentSupplier.value,
        parameters: '',
        user_content: text,
        search: enableSearch.value ? '1' : undefined,
        searchProvider: enableSearch.value ? settingsStore.searchEngine : undefined,
        images: savedImages.length ? savedImages.join(',') : undefined,
        doc_files: savedFiles.length ? JSON.stringify(savedFiles.map(f => ({ path: f.path, name: f.name }))) : undefined,
        rag_list: selectedKnowledge.value.length ? selectedKnowledge.value : undefined,
        mcp_servers: selectedMcp.value.length ? selectedMcp.value : undefined,
      }, (currentText) => {
        const reactiveMsg = messages.value[assistantIdx]
        updateAssistantContent(currentText, reactiveMsg)
      })
    } catch (e) {
      console.error('发送消息失败', e)
      const reactiveMsg = messages.value[assistantIdx]
      if (reactiveMsg) reactiveMsg.content = '请求失败，请检查网络或模型配置。'
    } finally {
      isLoading.value = false
      await loadChatList()
    }
  }

  const updateAssistantContent = (rawText: string, assistantMsg: ChatMessage) => {
    // 提取 <think>...</think> 思维链
    const thinkMatch = rawText.match(/<think>([\s\S]*?)<\/think>/)
    if (thinkMatch) {
      assistantMsg.thinking = thinkMatch[1].trim()
      assistantMsg.content = rawText.replace(/<think>[\s\S]*?<\/think>/, '').trim()
    } else if (rawText.includes('<think>')) {
      assistantMsg.thinking = rawText.split('<think>')[1].trim()
      assistantMsg.content = ''
    } else {
      assistantMsg.content = rawText
      assistantMsg.thinking = ''
    }
  }

  // 停止生成
  const stopGenerate = async () => {
    if (!currentChatId.value) return
    try {
      await chatApi.stopGenerate({ context_id: currentChatId.value })
    } catch (e) {
      console.error('停止生成失败', e)
    } finally {
      isLoading.value = false
    }
  }

  // 重新生成
  const regenerate = async (msgId: string | undefined) => {
    if (!msgId) return
    const idx = messages.value.findIndex(m => m.id === msgId)
    if (idx <= 0) return
    const userMsg = messages.value[idx - 1]
    if (!userMsg || userMsg.role !== 'user') return

    messages.value.splice(idx)
    inputText.value = userMsg.content || ''
    uploadedFiles.value = (userMsg.files || []).map(f => ({ name: f, path: f }))
    uploadedImages.value = userMsg.images || []
    await sendMessage()
  }

  // 加载模型列表
  const loadModels = async () => {
    try {
      const res = await chatApi.getModelList()
      modelList.value = []
      for (const key in res) {
        if (key === 'commonModelList') continue
        const models = Array.isArray(res[key]) ? res[key] : []
        if (models.length) {
          modelList.value.push({ name: key, title: key, models })
        }
      }
    } catch (e) {
      console.error('加载模型失败', e)
    }
  }

  // 加载知识库列表
  const loadKnowledgeList = async () => {
    try {
      const res = await ragApi.getRagList()
      knowledgeList.value = res || []
    } catch (e) {
      console.error('加载知识库失败', e)
    }
  }

  // 加载 MCP 列表
  const loadMcpList = async () => {
    try {
      const res = await mcpApi.getServerList()
      mcpList.value = res || []
    } catch (e) {
      console.error('加载 MCP 失败', e)
    }
  }

  // 选择模型
  const selectModel = (model: string, supplier: string) => {
    currentModel.value = model
    currentSupplier.value = supplier.toLowerCase()
  }

  // 选择知识库
  const toggleKnowledge = (name: string) => {
    const idx = selectedKnowledge.value.indexOf(name)
    if (idx > -1) {
      selectedKnowledge.value.splice(idx, 1)
    } else {
      selectedKnowledge.value.push(name)
    }
  }

  // 选择 MCP
  const toggleMcp = (name: string) => {
    const idx = selectedMcp.value.indexOf(name)
    if (idx > -1) {
      selectedMcp.value.splice(idx, 1)
    } else {
      selectedMcp.value.push(name)
    }
  }

  // 选择文件（Electron）
  const chooseFiles = async () => {
    if (!window.electronAPI?.openFileDialog) return
    try {
      const files = await window.electronAPI.openFileDialog({ multiSelections: true })
      for (const file of files) {
        const ext = file.name.split('.').pop()?.toLowerCase() || ''
        const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        if (imageExts.includes(ext)) {
          uploadedImages.value.push(file.path)
        } else {
          uploadedFiles.value.push({ name: file.name, path: file.path })
        }
      }
    } catch (e) {
      console.error('选择文件失败', e)
    }
  }

  const removeFile = (idx: number) => {
    uploadedFiles.value.splice(idx, 1)
  }

  const removeImage = (idx: number) => {
    uploadedImages.value.splice(idx, 1)
  }

  // 绑定智能体
  const bindAgent = (agent: AgentItem) => {
    currentAgent.value = agent
    if (agent.rag_ids?.length) {
      selectedKnowledge.value = [...agent.rag_ids]
    }
    if (agent.mcp_tool?.length) {
      selectedMcp.value = [...agent.mcp_tool]
    }
  }

  return {
    chatList,
    currentChatId,
    currentChatTitle,
    messages,
    isLoading,
    inputText,
    enableSearch,
    uploadedFiles,
    uploadedImages,
    modelList,
    currentModel,
    currentSupplier,
    knowledgeList,
    selectedKnowledge,
    mcpList,
    selectedMcp,
    currentAgent,
    canSend,
    hasActiveChat,
    loadChatList,
    selectChat,
    createChat,
    makeNewChat,
    removeChat,
    modifyChatTitle,
    sendMessage,
    stopGenerate,
    regenerate,
    loadModels,
    loadKnowledgeList,
    loadMcpList,
    selectModel,
    toggleKnowledge,
    toggleMcp,
    chooseFiles,
    removeFile,
    removeImage,
    bindAgent,
  }
})
