import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { RagItem, RagDoc, EmbeddingModelItem } from '@/types'

export const useRagStore = defineStore('rag', () => {
  // 知识库列表
  const ragList = ref<RagItem[]>([])
  // 当前激活知识库名称
  const activeRagName = ref<string | null>(null)
  // 当前激活知识库详情
  const activeRag = computed(() => ragList.value.find((item) => item.ragName === activeRagName.value) || null)
  // 当前知识库文档列表
  const docList = ref<RagDoc[]>([])
  // 当前激活文档
  const activeDocId = ref<string | null>(null)
  // 当前文档内容
  const docContent = ref<string>('')
  // 是否正在加载文档列表
  const loadingDocs = ref(false)
  // 是否正在加载文档内容
  const loadingDocContent = ref(false)
  // 是否正在上传
  const uploading = ref(false)
  // 文档解析中状态集合（用于轮询）
  const parsingRags = ref<Set<string>>(new Set())
  // 嵌入模型列表
  const embeddingModels = ref<EmbeddingModelItem[]>([])
  // 是否已安装 bge（知识库服务状态）
  const ragServiceReady = ref(false)
  // 弹窗显隐
  const createModalVisible = ref(false)
  const uploadModalVisible = ref(false)
  const editMode = ref(false)
  const deleteRagConfirmVisible = ref(false)
  const deleteDocConfirmVisible = ref(false)
  const installEmbeddingModalVisible = ref(false)
  // 等待删除/编辑的对象
  const pendingDeleteRagName = ref<string>('')
  const pendingDeleteDoc = ref<RagDoc | null>(null)
  // 创建/编辑表单
  const createForm = ref({
    ragName: '',
    ragDesc: '',
    embeddingModel: '',
    supplierName: '',
    maxRecall: 5,
  })
  // 分片配置表单
  const chunkForm = ref({
    chunkSize: 1000,
    overlapSize: 200,
    separators: ['\n\n', '\n', ' '],
    customSeparators: false,
  })

  return {
    ragList,
    activeRagName,
    activeRag,
    docList,
    activeDocId,
    docContent,
    loadingDocs,
    loadingDocContent,
    uploading,
    parsingRags,
    embeddingModels,
    ragServiceReady,
    createModalVisible,
    uploadModalVisible,
    editMode,
    deleteRagConfirmVisible,
    deleteDocConfirmVisible,
    installEmbeddingModalVisible,
    pendingDeleteRagName,
    pendingDeleteDoc,
    createForm,
    chunkForm,
  }
})
