import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { mcpApi } from '@/api/mcp'
import { toast } from 'vue3-toastify'
import type { McpServer, McpServerForm, McpTool, McpEnvStatus } from '@/types'

const emptyForm = (): McpServerForm => ({
  name: '',
  description: '',
  type: 'stdio',
  command: 'npx',
  baseUrl: '',
  env: '',
  args: '',
  isActive: true,
})

const formatArgs = (val?: string[]): string => {
  if (!Array.isArray(val)) return ''
  return val.join('\n')
}

const parseArgs = (val: string): string[] => {
  if (!val.trim()) return []
  return val.split('\n').map((s) => s.trim()).filter(Boolean)
}

const formatEnv = (val?: Record<string, string>): string => {
  if (!val || typeof val !== 'object') return ''
  return Object.entries(val)
    .map(([k, v]) => `${k}=${v}`)
    .join('\n')
}

const parseEnv = (val: string): Record<string, string> => {
  if (!val.trim()) return {}
  return val.split('\n').reduce((acc: Record<string, string>, line) => {
    const trimmed = line.trim()
    if (!trimmed) return acc
    const idx = trimmed.indexOf('=')
    if (idx === -1) {
      acc[trimmed] = ''
    } else {
      acc[trimmed.slice(0, idx)] = trimmed.slice(idx + 1)
    }
    return acc
  }, {})
}

const serverToForm = (server: McpServer): McpServerForm => ({
  name: server.name || '',
  description: server.description || '',
  type: server.type || 'stdio',
  command: server.command || '',
  baseUrl: server.baseUrl || '',
  env: formatEnv(server.env),
  args: formatArgs(server.args),
  isActive: server.isActive ?? server.is_active ?? true,
})

export const useMcpStore = defineStore('mcp', () => {
  // state
  const serverList = ref<McpServer[]>([])
  const templateList = ref<McpServerForm[]>([])
  const currentName = ref<string>('')
  const form = ref<McpServerForm>(emptyForm())
  const editMode = ref(false)
  const formVisible = ref(false)
  const commandType = ref<'npx' | 'custom'>('npx')
  const envStatus = ref<McpEnvStatus>({ node_npx: 0, python_uv: 0 })
  const envInstalling = ref(false)
  const envInstallType = ref<'npx' | 'uv' | ''>('')
  const configModalVisible = ref(false)
  const configContent = ref('')
  const toolsModalVisible = ref(false)
  const toolsLoading = ref(false)
  const toolsList = ref<McpTool[]>([])
  const deleteConfirmVisible = ref(false)
  const cloudSynced = ref(false)

  // getters
  const currentServer = computed(() =>
    serverList.value.find((s) => s.name === currentName.value) || null
  )

  // actions
  const loadServerList = async () => {
    try {
      const res = await mcpApi.getServerList()
      serverList.value = Array.isArray(res) ? res : []
    } catch (e: any) {
      toast.error(e.message || '加载 MCP 服务器列表失败')
    }
  }

  const loadTemplateList = async () => {
    try {
      const res = await mcpApi.getCommonServerList()
      const mcpServers = res?.mcpServers || res || {}
      const list: McpServerForm[] = []
      Object.keys(mcpServers).forEach((key) => {
        const item = mcpServers[key]
        list.push({
          name: item.name || key,
          description: item.description || '',
          type: item.type || 'stdio',
          command: item.command || 'npx',
          baseUrl: item.baseUrl || '',
          env: formatEnv(item.env),
          args: formatArgs(item.args),
          isActive: item.isActive ?? item.is_active ?? true,
        })
      })
      templateList.value = list
      // 若预设为空且未同步过云端，尝试同步
      if (list.length === 0 && !cloudSynced.value) {
        await syncCloudMcp()
      }
    } catch (e: any) {
      toast.error(e.message || '加载 MCP 预设模板失败')
    }
  }

  const syncCloudMcp = async () => {
    try {
      await mcpApi.syncCloudMcp()
      cloudSynced.value = true
      await loadTemplateList()
    } catch (e: any) {
      toast.error(e.message || '同步云端 MCP 预设失败')
    }
  }

  const selectServer = (name: string) => {
    currentName.value = name
    const server = serverList.value.find((s) => s.name === name)
    if (server) {
      form.value = serverToForm(server)
      editMode.value = true
    } else {
      form.value = emptyForm()
      editMode.value = false
    }
    formVisible.value = true
    commandType.value = form.value.command === 'npx' ? 'npx' : 'custom'
  }

  const createServer = (template?: McpServerForm) => {
    editMode.value = false
    currentName.value = ''
    if (template) {
      form.value = { ...template, name: `${template.name}` }
    } else {
      form.value = emptyForm()
    }
    formVisible.value = true
    commandType.value = form.value.command === 'npx' ? 'npx' : 'custom'
  }

  const resetForm = () => {
    form.value = emptyForm()
    editMode.value = false
    formVisible.value = false
    currentName.value = ''
    commandType.value = 'npx'
  }

  const buildPayload = (data: McpServerForm): any => {
    const payload: any = {
      name: data.name.trim(),
      description: data.description.trim(),
      type: data.type,
      command: data.type === 'sse' ? '' : data.command.trim(),
      baseUrl: data.type === 'sse' ? data.baseUrl.trim() : '',
      env: parseEnv(data.env),
      args: parseArgs(data.args),
    }
    if (editMode.value) {
      payload.is_active = data.isActive
    }
    return payload
  }

  const saveServer = async () => {
    const data = form.value
    if (!data.name.trim()) {
      toast.warning('请输入 MCP 服务器名称')
      return false
    }
    if (data.type === 'sse' && !data.baseUrl.trim()) {
      toast.warning('请输入服务器 URL 地址')
      return false
    }
    if (data.type === 'stdio' && commandType.value === 'custom' && !data.command.trim()) {
      toast.warning('请输入可执行命令')
      return false
    }

    const payload = buildPayload(data)
    try {
      if (editMode.value) {
        await mcpApi.modifyServer(payload)
        toast.success('保存成功')
      } else {
        await mcpApi.addServer(payload)
        toast.success('添加成功')
        // 添加成功后进入编辑模式
        await loadServerList()
        selectServer(data.name.trim())
        return true
      }
      await loadServerList()
      return true
    } catch (e: any) {
      toast.error(e.message || '保存失败')
      return false
    }
  }

  const toggleServerActive = async (active: boolean) => {
    if (!currentServer.value) return
    const oldActive = form.value.isActive
    form.value.isActive = active
    const payload = buildPayload(form.value)
    payload.is_active = active
    try {
      await mcpApi.modifyServer(payload)
      toast.success('状态更新成功')
      await loadServerList()
    } catch (e: any) {
      form.value.isActive = oldActive
      toast.error(e.message || '状态更新失败')
    }
  }

  const confirmDeleteServer = (name: string) => {
    currentName.value = name
    deleteConfirmVisible.value = true
  }

  const removeServer = async () => {
    const name = currentName.value
    if (!name) return
    try {
      await mcpApi.removeServer(name)
      toast.success('删除成功')
      deleteConfirmVisible.value = false
      if (form.value.name === name) {
        resetForm()
      }
      await loadServerList()
    } catch (e: any) {
      toast.error(e.message || '删除失败')
    }
  }

  const checkEnv = async () => {
    try {
      const res = await mcpApi.getStatus()
      envStatus.value = res
    } catch (e: any) {
      toast.error(e.message || '检查环境状态失败')
    }
  }

  const installEnv = async (type: 'npx' | 'uv') => {
    envInstalling.value = true
    envInstallType.value = type
    const startTime = Date.now()
    const timeout = 300000 // 最长轮询 5 分钟
    try {
      if (type === 'npx') {
        await mcpApi.installNpx()
        toast.info('Node.js 环境安装中，请稍候...')
      } else {
        await mcpApi.installUv()
      }

      // 轮询状态
      const timer = setInterval(async () => {
        await checkEnv()
        const elapsed = Date.now() - startTime
        const installed =
          (type === 'npx' && envStatus.value.node_npx === 1) ||
          (type === 'uv' && envStatus.value.python_uv === 1)
        if (installed || elapsed > timeout) {
          clearInterval(timer)
          envInstalling.value = false
          envInstallType.value = ''
          if (installed) {
            toast.success(type === 'npx' ? 'Node.js 环境安装成功' : 'Python 环境安装成功')
          } else if (elapsed > timeout) {
            toast.error('环境安装超时，请检查网络或稍后重试')
          }
        }
      }, 2000)
    } catch (e: any) {
      envInstalling.value = false
      envInstallType.value = ''
      toast.error(e.message || '环境安装失败')
    }
  }

  const openConfig = async () => {
    try {
      const res = await mcpApi.getConfigBody()
      configContent.value = res.mcp_config_body
      configModalVisible.value = true
    } catch (e: any) {
      toast.error(e.message || '获取配置文件失败')
    }
  }

  const saveConfig = async () => {
    try {
      await mcpApi.saveConfigBody(configContent.value)
      toast.success('配置文件保存成功')
      configModalVisible.value = false
      await loadServerList()
    } catch (e: any) {
      toast.error(e.message || '配置文件保存失败')
    }
  }

  const openTools = async (name: string) => {
    currentName.value = name
    toolsModalVisible.value = true
    toolsLoading.value = true
    toolsList.value = []
    try {
      const res = await mcpApi.getTools(name)
      toolsList.value = Array.isArray(res) ? res : []
    } catch (e: any) {
      toast.error(e.message || '获取工具列表失败')
    } finally {
      toolsLoading.value = false
    }
  }

  const toggleTool = async (toolName: string, active: boolean) => {
    const name = currentName.value
    if (!name) return
    try {
      await mcpApi.modifyTools({ name, tools: { [toolName]: active } })
      toast.success('工具状态更新成功')
      const tool = toolsList.value.find((t) => t.name === toolName)
      if (tool) tool.is_active = active
      await loadServerList()
    } catch (e: any) {
      toast.error(e.message || '工具状态更新失败')
    }
  }

  const onChangeCommandType = (type: 'npx' | 'custom') => {
    commandType.value = type
    if (type === 'npx') {
      form.value.command = 'npx'
    } else {
      form.value.command = ''
    }
  }

  return {
    serverList,
    templateList,
    currentName,
    form,
    editMode,
    formVisible,
    commandType,
    envStatus,
    envInstalling,
    envInstallType,
    configModalVisible,
    configContent,
    toolsModalVisible,
    toolsLoading,
    toolsList,
    deleteConfirmVisible,
    currentServer,
    loadServerList,
    loadTemplateList,
    syncCloudMcp,
    selectServer,
    createServer,
    resetForm,
    saveServer,
    toggleServerActive,
    confirmDeleteServer,
    removeServer,
    checkEnv,
    installEnv,
    openConfig,
    saveConfig,
    openTools,
    toggleTool,
    onChangeCommandType,
  }
})
