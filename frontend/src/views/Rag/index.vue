<template>
  <div class="rag-page">
    <RagList
      :list="ragStore.ragList"
      :active="ragStore.activeRagName"
      @select="selectRag"
      @create="openCreateModal"
      @edit="openEditModal"
      @delete="confirmDeleteRag"
    />
    <RagDetail
      v-if="ragStore.activeRag"
      :rag="ragStore.activeRag"
      :docs="ragStore.docList"
      :active-doc-id="ragStore.activeDocId"
      :content="ragStore.docContent"
      :loading-docs="ragStore.loadingDocs"
      :loading-content="ragStore.loadingDocContent"
      :parsing="ragStore.parsingRags.has(ragStore.activeRagName || '')"
      @upload="openUploadModal"
      @edit="openEditModal(ragStore.activeRag!)"
      @select-doc="selectDoc"
      @delete-doc="confirmDeleteDoc"
    />
    <div v-else class="empty-detail">
      <div class="empty-icon">📚</div>
      <div class="empty-title">暂无知识库</div>
      <div class="empty-desc">创建知识库并上传文档，让 AI 基于私有内容回答</div>
      <button class="btn-primary mt-16" @click="openCreateModal">创建知识库</button>
    </div>

    <CreateRagModal
      v-model:visible="ragStore.createModalVisible"
      :edit-mode="ragStore.editMode"
      :form="ragStore.createForm"
      :models="ragStore.embeddingModels"
      @submit="submitCreateOrEdit"
    />

    <UploadDocModal
      v-model:visible="ragStore.uploadModalVisible"
      :rag-name="ragStore.activeRagName || ''"
      :chunk-form="ragStore.chunkForm"
      @submit="submitUpload"
    />

    <DeleteConfirm
      v-model:visible="ragStore.deleteRagConfirmVisible"
      title="删除知识库"
      :content="`确定删除知识库「${ragStore.pendingDeleteRagName}」吗？删除后不可恢复。`"
      @confirm="deleteRag"
    />

    <DeleteConfirm
      v-model:visible="ragStore.deleteDocConfirmVisible"
      title="删除文档"
      :content="`确定删除文档「${ragStore.pendingDeleteDoc?.docName}」吗？`"
      @confirm="deleteDoc"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useRagStore } from '@/stores/rag'
import { ragApi } from '@/api/rag'
import type { RagItem, RagDoc } from '@/types'
import RagList from './components/RagList.vue'
import RagDetail from './components/RagDetail.vue'
import CreateRagModal from './components/CreateRagModal.vue'
import UploadDocModal from './components/UploadDocModal.vue'
import DeleteConfirm from './components/DeleteConfirm.vue'

const ragStore = useRagStore()
const { activeRagName } = storeToRefs(ragStore)

let parseTimer: number | null = null

const message = (text: string, type: 'success' | 'error' = 'success') => {
  // 简单使用 console + alert 兜底，后续可接入全局 message 组件
  if (type === 'error') {
    console.error(text)
    window.alert(text)
  } else {
    console.log(text)
  }
}

/** 初始化 */
const init = async () => {
  try {
    await checkRagStatus()
    await loadEmbeddingModels()
    await loadRagList(true)
  } catch (e) {
    console.error(e)
  }
}

/** 检查知识库服务状态 */
const checkRagStatus = async () => {
  try {
    const res = await ragApi.getStatus()
    console.log('rag_status response:', res)
    // 只要接口正常返回（status=0），即认为知识库服务就绪
    ragStore.ragServiceReady = true
  } catch (e: any) {
    console.error('rag_status error:', e)
    ragStore.ragServiceReady = false
  }
}

/** 加载嵌入模型列表 */
const loadEmbeddingModels = async () => {
  try {
    const res = await ragApi.getEmbeddingModels()
    const list: any[] = []
    if (res && typeof res === 'object') {
      Object.values(res).forEach((group: any) => {
        if (Array.isArray(group)) {
          group.forEach((item: any) => {
            list.push({
              ...item,
              supplierName: item.supplierName || item.supplier_name || 'ollama',
            })
          })
        }
      })
    }
    ragStore.embeddingModels = list
    // 默认选中 bge-m3 或第一个
    if (!ragStore.createForm.embeddingModel && list.length) {
      const bge = list.find((m) => m.model?.includes('bge-m3'))
      const target = bge || list[0]
      ragStore.createForm.embeddingModel = target.model
      ragStore.createForm.supplierName = target.supplierName
    }
  } catch (e) {
    console.error('加载嵌入模型失败', e)
  }
}

/** 加载知识库列表 */
const loadRagList = async (autoSelect = false) => {
  try {
    const res = await ragApi.getRagList()
    const list = (res || []).sort((a: RagItem, b: RagItem) => (b.ragCreateTime || 0) - (a.ragCreateTime || 0))
    ragStore.ragList = list
    if (autoSelect && list.length && !ragStore.activeRagName) {
      const first = list.find((item) => !item.isPreset) || list[0]
      if (first) await selectRag(first.ragName)
    }
  } catch (e) {
    console.error('加载知识库列表失败', e)
  }
}

/** 选择知识库 */
const selectRag = async (ragName: string) => {
  ragStore.activeRagName = ragName
  await loadDocList()
  // 默认加载第一个文档内容
  const firstDoc = ragStore.docList[0]
  if (firstDoc) {
    await selectDoc(firstDoc)
  } else {
    ragStore.activeDocId = null
    ragStore.docContent = ''
  }
}

/** 加载文档列表 */
const loadDocList = async () => {
  const ragName = ragStore.activeRagName
  if (!ragName) return
  ragStore.loadingDocs = true
  try {
    const res = await ragApi.getDocList(ragName)
    ragStore.docList = res || []
  } catch (e) {
    console.error('加载文档列表失败', e)
  } finally {
    ragStore.loadingDocs = false
  }
}

/** 选择文档 */
const selectDoc = async (doc: RagDoc) => {
  ragStore.activeDocId = doc.docId
  ragStore.loadingDocContent = true
  try {
    const res = await ragApi.getDocContent(ragStore.activeRagName || '', doc.docName)
    ragStore.docContent = typeof res === 'string' ? res : ''
  } catch (e) {
    console.error('加载文档内容失败', e)
    ragStore.docContent = ''
  } finally {
    ragStore.loadingDocContent = false
  }
}

/** 打开创建弹窗 */
const openCreateModal = async () => {
  await checkRagStatus()
  await loadEmbeddingModels()
  if (!ragStore.ragServiceReady) {
    message('知识库服务未就绪，请先安装本地嵌入模型或配置第三方模型', 'error')
    return
  }
  ragStore.editMode = false
  ragStore.createForm = {
    ragName: '',
    ragDesc: '',
    embeddingModel: '',
    supplierName: '',
    maxRecall: 5,
  }
  // 默认模型
  if (ragStore.embeddingModels.length) {
    const bge = ragStore.embeddingModels.find((m) => m.model?.includes('bge-m3'))
    const target = bge || ragStore.embeddingModels[0]
    ragStore.createForm.embeddingModel = target.model
    ragStore.createForm.supplierName = target.supplierName
  }
  ragStore.createModalVisible = true
}

/** 打开编辑弹窗 */
const openEditModal = (item?: RagItem) => {
  const target = item || ragStore.activeRag
  if (!target) return
  ragStore.editMode = true
  ragStore.createForm = {
    ragName: target.ragName,
    ragDesc: target.ragDesc,
    embeddingModel: target.embeddingModel || '',
    supplierName: target.supplierName || '',
    maxRecall: 5,
  }
  ragStore.createModalVisible = true
}

/** 提交创建/编辑 */
const submitCreateOrEdit = async (form: typeof ragStore.createForm) => {
  if (!form.ragName.trim()) {
    message('请输入知识库名称', 'error')
    return
  }
  if (!form.ragDesc.trim()) {
    message('请输入知识库描述', 'error')
    return
  }
  if (!form.embeddingModel) {
    message('请选择嵌入模型', 'error')
    return
  }
  try {
    if (ragStore.editMode) {
      await ragApi.modifyRag({
        ragName: form.ragName,
        ragDesc: form.ragDesc,
        maxRecall: form.maxRecall,
      })
      message('修改成功')
    } else {
      await ragApi.createRag({
        ragName: form.ragName,
        ragDesc: form.ragDesc,
        embeddingModel: form.embeddingModel,
        supplierName: form.supplierName,
        maxRecall: form.maxRecall,
      })
      message('创建成功')
      ragStore.activeRagName = form.ragName
    }
    ragStore.createModalVisible = false
    await loadRagList()
    if (!ragStore.editMode) {
      await selectRag(form.ragName)
    }
  } catch (e: any) {
    message(e.message || '操作失败', 'error')
  }
}

/** 删除知识库确认 */
const confirmDeleteRag = (ragName: string) => {
  ragStore.pendingDeleteRagName = ragName
  ragStore.deleteRagConfirmVisible = true
}

/** 删除知识库 */
const deleteRag = async () => {
  try {
    await ragApi.removeRag(ragStore.pendingDeleteRagName)
    message('删除成功')
    if (ragStore.activeRagName === ragStore.pendingDeleteRagName) {
      ragStore.activeRagName = null
      ragStore.docList = []
      ragStore.docContent = ''
    }
    ragStore.deleteRagConfirmVisible = false
    await loadRagList(true)
  } catch (e: any) {
    message(e.message || '删除失败', 'error')
  }
}

/** 打开上传弹窗 */
const openUploadModal = () => {
  ragStore.chunkForm = {
    chunkSize: 1000,
    overlapSize: 200,
    separators: ['\n\n', '\n', ' '],
    customSeparators: false,
  }
  ragStore.uploadModalVisible = true
}

/** 提交上传 */
const submitUpload = async (payload: { file: File; overSameFile: number | null; chunkForm: typeof ragStore.chunkForm }) => {
  const ragName = ragStore.activeRagName
  if (!ragName) return
  ragStore.uploading = true
  try {
    await ragApi.uploadDoc({
      ragName,
      file: payload.file,
      separators: payload.chunkForm.customSeparators ? payload.chunkForm.separators : ['\n\n', '\n', ' '],
      chunkSize: payload.chunkForm.chunkSize,
      overlapSize: payload.chunkForm.overlapSize,
      overSameFile: payload.overSameFile,
    })
    message('上传成功')
    ragStore.uploadModalVisible = false
    ragStore.parsingRags.add(ragName)
    await loadDocList()
    startParsePolling()
  } catch (e: any) {
    message(e.message || '上传失败', 'error')
  } finally {
    ragStore.uploading = false
  }
}

/** 文档解析轮询 */
const startParsePolling = () => {
  if (parseTimer) return
  parseTimer = window.setInterval(async () => {
    if (!ragStore.parsingRags.size) {
      stopParsePolling()
      return
    }
    await loadDocList()
    const ragName = ragStore.activeRagName
    if (ragName && ragStore.parsingRags.has(ragName)) {
      const allParsed = ragStore.docList.every((doc) => doc.is_parsed === 1 || doc.is_parsed === 3 || doc.is_parsed === -1)
      if (allParsed) {
        ragStore.parsingRags.delete(ragName)
      }
    }
  }, 3000)
}

const stopParsePolling = () => {
  if (parseTimer) {
    clearInterval(parseTimer)
    parseTimer = null
  }
}

/** 删除文档确认 */
const confirmDeleteDoc = (doc: RagDoc) => {
  ragStore.pendingDeleteDoc = doc
  ragStore.deleteDocConfirmVisible = true
}

/** 删除文档 */
const deleteDoc = async () => {
  const doc = ragStore.pendingDeleteDoc
  if (!doc || !ragStore.activeRagName) return
  try {
    await ragApi.removeDoc(ragStore.activeRagName, [doc.docId])
    message('删除成功')
    if (ragStore.activeDocId === doc.docId) {
      ragStore.activeDocId = null
      ragStore.docContent = ''
    }
    ragStore.deleteDocConfirmVisible = false
    await loadDocList()
  } catch (e: any) {
    message(e.message || '删除失败', 'error')
  }
}

watch(activeRagName, () => {
  if (ragStore.activeRagName && ragStore.parsingRags.has(ragStore.activeRagName)) {
    startParsePolling()
  }
})

onMounted(init)
onUnmounted(stopParsePolling)
</script>

<style scoped lang="scss">
.rag-page {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.empty-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }

  .empty-title {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 6px;
    color: var(--text-primary);
  }

  .empty-desc {
    font-size: 14px;
    color: var(--text-tertiary);
    margin-bottom: 16px;
  }
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: none;
  background: var(--accent-color);
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.9;
  }
}

.mt-16 {
  margin-top: 16px;
}
</style>
