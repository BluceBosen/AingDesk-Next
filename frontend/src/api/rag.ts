import request, { post, get } from './request'
import type { RagItem, RagDoc } from '@/types'

export const ragApi = {
  /** 检查知识库服务状态 */
  getStatus: (): Promise<any> => get('/rag/rag_status'),

  /** 获取嵌入模型列表 */
  getEmbeddingModels: (): Promise<any> => get('/rag/get_embedding_models'),

  /** 创建知识库 */
  createRag: (data: {
    ragName: string
    ragDesc: string
    embeddingModel?: string
    supplierName?: string
    searchStrategy?: number
    maxRecall?: number
    recallAccuracy?: number
    resultReordering?: number
    rerankModel?: string
    queryRewrite?: number
    vectorWeight?: number
    keywordWeight?: number
    savePath?: string
  }): Promise<any> => post('/rag/create_rag', data),

  /** 获取知识库列表 */
  getRagList: (): Promise<RagItem[]> => get('/rag/get_rag_list'),

  /** 删除知识库 */
  removeRag: (ragName: string): Promise<any> => post('/rag/remove_rag', { ragName }),

  /** 修改知识库 */
  modifyRag: (data: {
    ragName: string
    ragDesc: string
    searchStrategy?: number
    maxRecall?: number
    recallAccuracy?: number
    resultReordering?: number
    rerankModel?: string
    queryRewrite?: number
    vectorWeight?: number
    keywordWeight?: number
  }): Promise<any> => post('/rag/modify_rag', data),

  /**
   * 上传文档（multipart/form-data 直接上传文件）
   * @param data.ragName 知识库名称
   * @param data.file 文件对象
   * @param data.separators 分隔符数组
   * @param data.chunkSize 分块大小
   * @param data.overlapSize 重叠大小
   * @param data.overSameFile 同文件处理：null=覆盖 1=不覆盖 2=重命名
   */
  uploadDoc: (data: {
    ragName: string
    file: File
    separators?: string[]
    chunkSize?: number
    overlapSize?: number
    overSameFile?: number | null
  }): Promise<any> => {
    const formData = new FormData()
    formData.append('ragName', data.ragName)
    formData.append('file', data.file)
    if (data.separators) {
      formData.append('separators', JSON.stringify(data.separators))
    }
    if (data.chunkSize !== undefined) {
      formData.append('chunkSize', String(data.chunkSize))
    }
    if (data.overlapSize !== undefined) {
      formData.append('overlapSize', String(data.overlapSize))
    }
    if (data.overSameFile !== undefined && data.overSameFile !== null) {
      formData.append('overSameFile', String(data.overSameFile))
    }
    return request.post('/rag/upload_doc', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    })
  },

  /** 获取知识库文档列表 */
  getDocList: (ragName: string): Promise<RagDoc[]> => post('/rag/get_rag_doc_list', { ragName }),

  /** 获取文档内容 */
  getDocContent: (ragName: string, docName: string): Promise<string> =>
    post('/rag/get_doc_content', { ragName, docName }),

  /** 删除知识库文档 */
  removeDoc: (ragName: string, docIdList: string[]): Promise<any> =>
    post('/rag/remove_doc', { ragName, docIdList: JSON.stringify(docIdList) }),

  /** 重新索引文档 */
  reindexDoc: (ragName: string, docId: string): Promise<any> =>
    post('/rag/reindex_document', { ragName, docId }),

  /** 测试文档分片 */
  testChunk: (data: {
    filename: string
    chunkSize: number
    overlapSize: number
    separators: string[]
  }): Promise<any> => post('/rag/test_chunk', data),

  /** 优化知识库 */
  optimizeTable: (ragName: string): Promise<any> => post('/rag/optimize_table', { ragName }),
}
