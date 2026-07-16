import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { modelApi } from '@/api/model'
import { managerApi } from '@/api/manager'
import type { Supplier, SupplierConfig, SupplierModel, LocalModel, ModelManager, InstallProgress } from '@/types'

const CAPABILITY_OPTIONS = [
  { label: 'LLM', value: 'llm' },
  { label: 'Vision', value: 'vision' },
  { label: 'Embedding', value: 'embedding' },
  { label: 'Tools', value: 'tools' },
]

const _useModelStore = defineStore('model', () => {
  // 当前 Tab：'service' | 'local'
  const activeTab = ref('service')

  // 供应商列表
  const supplierList = ref<Supplier[]>([])
  // 当前选中的供应商
  const currentSupplier = ref<Supplier | null>(null)
  // 当前供应商配置（编辑中）
  const supplierConfig = ref<SupplierConfig>({
    supplierName: '',
    supplierTitle: '',
    baseUrl: '',
    apiKey: '',
  })
  // 当前供应商下的模型列表
  const supplierModels = ref<SupplierModel[]>([])

  // 加载状态
  const loading = ref(false)

  // ==================== 本地模型相关状态 ====================
  // 模型管理器信息
  const modelManager = ref<ModelManager | null>(null)
  // 本地模型列表（原始）
  const localModelList = ref<LocalModel[]>([])
  // 过滤后的本地模型列表
  const filteredLocalModels = ref<LocalModel[]>([])
  // Ollama 接口地址
  const ollamaUrl = ref('')
  // 是否已安装模型管理器
  const isInstalledManager = ref(false)
  // 本地模型搜索关键字
  const localSearch = ref('')
  // 本地模型筛选类型
  const localModeType = ref('all')
  // 本地模型分页
  const localPagination = ref({ page: 1, pageSize: 10 })

  // 安装模型相关
  const installModelShow = ref(false)
  const installModelInfo = ref<{ model: string; parameters: string }>({
    model: '',
    parameters: '',
  })
  const modelInstallProgress = ref<InstallProgress>({
    status: 0,
    digest: '',
    total: 0,
    completed: 0,
    progress: 0,
    speed: 0,
  })
  const downloadText = ref('正在连接，请稍候...')

  // 删除模型相关
  const deleteLocalModelShow = ref(false)
  const deleteLocalModelName = ref('')
  const deletingLocalModel = ref(false)

  // 安装模型管理器相关
  const managerInstallConfirmShow = ref(false)
  const managerForInstall = ref('ollama')
  const managerInstallPath = ref('')
  const managerInstallProgressShow = ref(false)
  const managerInstallNotice = ref('')
  const modelManagerInstallProgress = ref<InstallProgress>({
    status: 0,
    digest: '',
    total: 0,
    completed: 0,
    progress: 0,
    speed: 0,
  })

  // 本地模型安装定时器
  let modelInstallTimer: ReturnType<typeof setInterval> | null = null
  let managerInstallTimer: ReturnType<typeof setInterval> | null = null

  // 本地模型分页后列表
  const paginatedLocalModels = computed(() => {
    const start = (localPagination.value.page - 1) * localPagination.value.pageSize
    return filteredLocalModels.value.slice(start, start + localPagination.value.pageSize)
  })

  const localModelTotal = computed(() => filteredLocalModels.value.length)

  // 添加供应商弹窗
  const addSupplierShow = ref(false)
  const addSupplierForm = ref({
    supplierTitle: '',
    baseUrl: '',
    apiKey: '',
  })

  // 添加/编辑模型弹窗
  const addModelShow = ref(false)
  const isEditModel = ref(false)
  const addModelForm = ref<{
    modelName: string
    title: string
    capability: string[]
  }>({
    modelName: '',
    title: '',
    capability: [],
  })

  // 删除确认
  const deleteSupplierShow = ref(false)
  const deleteModelShow = ref(false)
  const deleteModelName = ref('')

  // 是否全部启用
  const isAllModelEnable = computed(() => {
    if (!supplierModels.value.length) return false
    return supplierModels.value.every((m) => m.status === true)
  })

  const cantChooseCapability = computed(() => {
    return addModelForm.value.capability.includes('embedding')
  })

  // 生成随机 supplierName
  const generateSupplierName = () => {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789'
    let result = 'sp_'
    for (let i = 0; i < 10; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length))
    }
    return result
  }

  // 加载供应商列表
  const loadSupplierList = async () => {
    try {
      loading.value = true
      const res = await modelApi.getSupplierList()
      supplierList.value = (res || []).map((item: any) => ({
        ...item,
        supplierName: item.supplierName || item.name,
        supplierTitle: item.supplierTitle || item.title,
      }))
      if (supplierList.value.length && !currentSupplier.value) {
        await selectSupplier(supplierList.value[0])
      }
    } catch (e) {
      console.error('加载供应商列表失败', e)
    } finally {
      loading.value = false
    }
  }

  // 选中供应商
  const selectSupplier = async (supplier: Supplier) => {
    currentSupplier.value = supplier
    try {
      const config = await modelApi.getSupplierConfig(supplier.supplierName)
      supplierConfig.value = {
        supplierName: supplier.supplierName,
        supplierTitle: supplier.supplierTitle,
        baseUrl: config?.baseUrl || supplier.baseUrl || '',
        apiKey: config?.apiKey || '',
      }
      await loadSupplierModels(supplier.supplierName)
    } catch (e) {
      console.error('加载供应商配置失败', e)
    }
  }

  // 加载模型列表
  const loadSupplierModels = async (supplierName: string) => {
    try {
      const res = await modelApi.getModelsList(supplierName)
      supplierModels.value = (res || [])
        .filter((item: any) => item.title || item.modelName || item.model)
        .map((item: any) => {
          let capability: string[] = []
          if (Array.isArray(item.capability)) {
            capability = item.capability
          } else if (typeof item.capability === 'string') {
            try {
              const parsed = JSON.parse(item.capability)
              capability = Array.isArray(parsed) ? parsed : [item.capability]
            } catch {
              capability = item.capability ? [item.capability] : []
            }
          }
          return {
            modelName: item.modelName || item.model,
            title: item.title || item.modelName || item.model,
            status: item.status !== false,
            capability,
          }
        })
    } catch (e) {
      console.error('加载模型列表失败', e)
      supplierModels.value = []
    }
  }

  // 保存供应商配置
  const saveSupplierConfig = async () => {
    if (!currentSupplier.value) return
    if (!supplierConfig.value.baseUrl || !supplierConfig.value.apiKey) {
      throw new Error('请填写完整配置信息')
    }
    await modelApi.setSupplierConfig({
      supplierName: currentSupplier.value.supplierName,
      baseUrl: supplierConfig.value.baseUrl,
      apiKey: supplierConfig.value.apiKey,
    })
    currentSupplier.value.status = true
  }

  // 检查配置
  const checkSupplierConfig = async () => {
    if (!currentSupplier.value) return ''
    if (!supplierConfig.value.apiKey || !supplierConfig.value.baseUrl) {
      throw new Error('缺少API密钥或API地址')
    }
    const msg = await modelApi.checkSupplierConfig({
      supplierName: currentSupplier.value.supplierName,
      baseUrl: supplierConfig.value.baseUrl,
      apiKey: supplierConfig.value.apiKey,
    })
    return msg
  }

  // 切换供应商状态
  const toggleSupplierStatus = async (supplier: Supplier, status: boolean) => {
    await modelApi.setSupplierStatus({
      supplierName: supplier.supplierName,
      status: String(status),
    })
    supplier.status = status
  }

  // 删除供应商
  const removeSupplier = async () => {
    if (!currentSupplier.value) return
    await modelApi.removeSupplier(currentSupplier.value.supplierName)
    deleteSupplierShow.value = false
    currentSupplier.value = null
    await loadSupplierList()
  }

  // 确认添加供应商
  const confirmAddSupplier = async () => {
    if (!addSupplierForm.value.supplierTitle) {
      throw new Error('请输入供应商名称')
    }
    if (!addSupplierForm.value.baseUrl) {
      throw new Error('请输入API地址')
    }
    await modelApi.addSupplier({
      supplierName: generateSupplierName(),
      supplierTitle: addSupplierForm.value.supplierTitle,
      baseUrl: addSupplierForm.value.baseUrl,
      apiKey: addSupplierForm.value.apiKey,
    })
    addSupplierShow.value = false
    addSupplierForm.value = { supplierTitle: '', baseUrl: '', apiKey: '' }
    await loadSupplierList()
  }

  // 取消添加供应商
  const cancelAddSupplier = () => {
    addSupplierShow.value = false
    addSupplierForm.value = { supplierTitle: '', baseUrl: '', apiKey: '' }
  }

  // 打开添加模型弹窗
  const openAddModel = () => {
    isEditModel.value = false
    addModelForm.value = { modelName: '', title: '', capability: [] }
    addModelShow.value = true
  }

  // 打开编辑模型弹窗
  const openEditModel = (model: SupplierModel) => {
    isEditModel.value = true
    addModelForm.value = {
      modelName: model.modelName,
      title: model.title,
      capability: [...model.capability],
    }
    addModelShow.value = true
  }

  // 确认添加/编辑模型
  const confirmAddModel = async () => {
    if (!currentSupplier.value) return
    if (!addModelForm.value.modelName) {
      throw new Error('请输入模型ID')
    }
    if (!addModelForm.value.title) {
      throw new Error('请输入模型别名')
    }
    if (!addModelForm.value.capability.length) {
      throw new Error('请选择模型功能')
    }
    if (isEditModel.value) {
      await modelApi.modifyModel({
        supplierName: currentSupplier.value.supplierName,
        modelName: addModelForm.value.modelName,
        title: addModelForm.value.title,
        capability: JSON.stringify(addModelForm.value.capability),
      })
    } else {
      await modelApi.addModels({
        supplierName: currentSupplier.value.supplierName,
        modelName: addModelForm.value.modelName,
        title: addModelForm.value.title,
        capability: JSON.stringify(addModelForm.value.capability),
      })
    }
    addModelShow.value = false
    addModelForm.value = { modelName: '', title: '', capability: [] }
    await loadSupplierModels(currentSupplier.value.supplierName)
  }

  // 关闭添加模型弹窗
  const closeAddModel = () => {
    addModelShow.value = false
    isEditModel.value = false
    addModelForm.value = { modelName: '', title: '', capability: [] }
  }

  // 切换单个模型状态
  const toggleModelStatus = async (model: SupplierModel) => {
    if (!currentSupplier.value) return
    const newStatus = !model.status
    await modelApi.setModelStatus({
      supplierName: currentSupplier.value.supplierName,
      modelName: model.modelName,
      status: String(newStatus),
    })
    model.status = newStatus
  }

  // 批量切换模型状态
  const toggleAllModelStatus = async (status: boolean) => {
    if (!currentSupplier.value || !supplierModels.value.length) return
    const modelNames = supplierModels.value.map((m) => m.modelName).join(',')
    await modelApi.setModelStatus({
      supplierName: currentSupplier.value.supplierName,
      modelName: modelNames,
      status: String(status),
    })
    supplierModels.value.forEach((m) => (m.status = status))
  }

  // 删除模型
  const delModel = (modelName: string) => {
    deleteModelName.value = modelName
    deleteModelShow.value = true
  }

  const confirmDelModel = async () => {
    if (!currentSupplier.value || !deleteModelName.value) return
    await modelApi.removeModels({
      supplierName: currentSupplier.value.supplierName,
      modelName: deleteModelName.value,
    })
    deleteModelShow.value = false
    deleteModelName.value = ''
    await loadSupplierModels(currentSupplier.value.supplierName)
  }

  const cancelDelModel = () => {
    deleteModelShow.value = false
    deleteModelName.value = ''
  }

  // 能力选择变化（embedding 独占）
  const onCapabilityChange = (val: string[]) => {
    if (val.includes('embedding')) {
      addModelForm.value.capability = ['embedding']
    } else {
      addModelForm.value.capability = val
    }
  }

  // ==================== 本地模型相关方法 ====================

  // 获取本地模型管理器信息
  const loadLocalModels = async () => {
    try {
      loading.value = true
      const res = (await managerApi.getModelManager()) as ModelManager
      modelManager.value = res
      isInstalledManager.value = !!res.status
      ollamaUrl.value = res.ollama_host || ''
      localModelList.value = res.models || []

      // 如果未安装管理器，弹出安装确认
      if (!res.status) {
        managerInstallConfirmShow.value = true
      }

      handleLocalSearch()
    } catch (e) {
      console.error('加载本地模型失败', e)
      localModelList.value = []
      filteredLocalModels.value = []
    } finally {
      loading.value = false
    }
  }

  // 本地模型搜索/筛选
  const handleLocalSearch = () => {
    const keyword = localSearch.value.trim().toLowerCase()
    filteredLocalModels.value = localModelList.value.filter((item) => {
      const matchKeyword = item.full_name.toLowerCase().includes(keyword)
      if (!matchKeyword) return false
      if (localModeType.value === 'all') return true
      if (localModeType.value === 'installed') return item.install
      return item.capability.includes(localModeType.value)
    })
    localPagination.value.page = 1
  }

  // 设置 Ollama 地址
  const setOllamaHost = async () => {
    if (!ollamaUrl.value) throw new Error('请输入 Ollama 接口地址')
    await managerApi.setOllamaHost(ollamaUrl.value)
    await loadLocalModels()
  }

  // 安装模型
  const installLocalModel = async (modelInfo: { model: string; parameters: string }) => {
    installModelInfo.value = modelInfo
    installModelShow.value = true
    downloadText.value = '正在连接，请稍候...'
    modelInstallProgress.value = {
      status: 0,
      digest: '',
      total: 0,
      completed: 0,
      progress: 0,
      speed: 0,
    }

    // 开始安装
    await managerApi.installModel({
      model: modelInfo.model,
      parameters: modelInfo.parameters,
    })

    // 轮询进度
    if (modelInstallTimer) clearInterval(modelInstallTimer)
    modelInstallTimer = setInterval(async () => {
      try {
        const progress = await managerApi.getModelInstallProgress({
          model: installModelInfo.value.model,
          parameters: installModelInfo.value.parameters,
        })
        modelInstallProgress.value = progress
        const fullName = `${installModelInfo.value.model}:${installModelInfo.value.parameters}`

        if (progress.status === 0) {
          downloadText.value = `等待下载:${fullName}，请稍候...`
        } else if (progress.status === 1) {
          downloadText.value = `正在下载:${fullName}，请稍候...`
        } else if (progress.status === 2) {
          downloadText.value = `正在安装:${fullName}，请稍候...`
        } else if (progress.status === 3) {
          downloadText.value = '安装完成'
          closeInstallModel()
          await loadLocalModels()
          localModeType.value = 'installed'
          handleLocalSearch()
        } else if (progress.status === -1) {
          downloadText.value = '安装失败'
          if (modelInstallTimer) {
            clearInterval(modelInstallTimer)
            modelInstallTimer = null
          }
        }
      } catch (e) {
        console.error('获取安装进度失败', e)
      }
    }, 1000)
  }

  // 关闭安装模型弹窗
  const closeInstallModel = () => {
    if (modelInstallTimer) {
      clearInterval(modelInstallTimer)
      modelInstallTimer = null
    }
    installModelShow.value = false
  }

  // 重新连接下载
  const reconnectModelDownload = async () => {
    await managerApi.reconnectModelDownload()
  }

  // 删除本地模型询问
  const delLocalModel = (fullName: string) => {
    deleteLocalModelName.value = fullName
    deleteLocalModelShow.value = true
  }

  // 确认删除本地模型
  const confirmDelLocalModel = async () => {
    if (!deleteLocalModelName.value) return
    deletingLocalModel.value = true
    try {
      const [model, parameters = ''] = deleteLocalModelName.value.split(':')
      await managerApi.removeModel({ model, parameters })
      deleteLocalModelShow.value = false
      await loadLocalModels()
    } catch (e: any) {
      throw new Error(e.message || '删除失败')
    } finally {
      deletingLocalModel.value = false
      deleteLocalModelName.value = ''
    }
  }

  // 取消删除本地模型
  const cancelDelLocalModel = () => {
    deleteLocalModelShow.value = false
    deleteLocalModelName.value = ''
  }

  // 选择模型管理器安装路径（使用 Electron 文件对话框）
  const chooseManagerInstallPath = async () => {
    if (!window.electronAPI?.openFileDialog) return
    const files = await window.electronAPI.openFileDialog({ multiSelections: false })
    if (files && files.length) {
      managerInstallPath.value = files[0].path
    }
  }

  // 安装模型管理器
  const installModelManager = async () => {
    if (!managerForInstall.value) throw new Error('请选择模型管理器')
    if (!managerInstallPath.value) throw new Error('请选择模型管理器安装路径')

    managerInstallProgressShow.value = true
    managerInstallConfirmShow.value = false
    managerInstallNotice.value = '正在下载'
    modelManagerInstallProgress.value = {
      status: 0,
      digest: '',
      total: 0,
      completed: 0,
      progress: 0,
      speed: 0,
    }

    await managerApi.installModelManager({
      manager_name: managerForInstall.value,
      models_path: managerInstallPath.value,
    })

    // 轮询管理器安装进度
    if (managerInstallTimer) clearInterval(managerInstallTimer)
    managerInstallTimer = setInterval(async () => {
      try {
        const progress = await managerApi.getModelManagerInstallProgress({
          manager_name: managerForInstall.value,
        })
        modelManagerInstallProgress.value = progress

        if (progress.status === 0) managerInstallNotice.value = '正在选择下载节点，请稍后'
        if (progress.status === 1) managerInstallNotice.value = '正在下载模型管理器，请稍后'
        if (progress.status === 2) managerInstallNotice.value = '正在安装模型管理器，可能要几分钟时间，请耐心等待'
        if (progress.status === 3) {
          managerInstallNotice.value = '安装成功'
          closeManagerInstallProgress()
          isInstalledManager.value = true
          await loadLocalModels()
        }
        if (progress.status === -1) {
          managerInstallNotice.value = '模型管理器安装失败'
          if (managerInstallTimer) {
            clearInterval(managerInstallTimer)
            managerInstallTimer = null
          }
        }
      } catch (e) {
        console.error('获取管理器安装进度失败', e)
      }
    }, 1000)
  }

  // 关闭模型管理器安装进度
  const closeManagerInstallProgress = () => {
    if (managerInstallTimer) {
      clearInterval(managerInstallTimer)
      managerInstallTimer = null
    }
    managerInstallProgressShow.value = false
  }

  // 暂不安装模型管理器
  const notInstallManagerNow = () => {
    managerInstallConfirmShow.value = false
  }

  return {
    activeTab,
    supplierList,
    currentSupplier,
    supplierConfig,
    supplierModels,
    loading,
    addSupplierShow,
    addSupplierForm,
    addModelShow,
    isEditModel,
    addModelForm,
    deleteSupplierShow,
    deleteModelShow,
    deleteModelName,
    isAllModelEnable,
    cantChooseCapability,
    CAPABILITY_OPTIONS,
    loadSupplierList,
    selectSupplier,
    loadSupplierModels,
    saveSupplierConfig,
    checkSupplierConfig,
    toggleSupplierStatus,
    removeSupplier,
    confirmAddSupplier,
    cancelAddSupplier,
    openAddModel,
    openEditModel,
    confirmAddModel,
    closeAddModel,
    toggleModelStatus,
    toggleAllModelStatus,
    delModel,
    confirmDelModel,
    cancelDelModel,
    onCapabilityChange,
    // 本地模型
    modelManager,
    localModelList,
    filteredLocalModels,
    paginatedLocalModels,
    localModelTotal,
    ollamaUrl,
    isInstalledManager,
    localSearch,
    localModeType,
    localPagination,
    installModelShow,
    installModelInfo,
    modelInstallProgress,
    downloadText,
    deleteLocalModelShow,
    deleteLocalModelName,
    deletingLocalModel,
    managerInstallConfirmShow,
    managerForInstall,
    managerInstallPath,
    managerInstallProgressShow,
    managerInstallNotice,
    modelManagerInstallProgress,
    loadLocalModels,
    handleLocalSearch,
    setOllamaHost,
    installLocalModel,
    closeInstallModel,
    reconnectModelDownload,
    delLocalModel,
    confirmDelLocalModel,
    cancelDelLocalModel,
    chooseManagerInstallPath,
    installModelManager,
    closeManagerInstallProgress,
    notInstallManagerNow,
  }
})

export { _useModelStore as useModelStore }
