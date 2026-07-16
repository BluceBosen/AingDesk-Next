<template>
  <div class="models-page">
    <!-- 顶部 Tab -->
    <div class="page-tabs">
      <button
        class="tab-item"
        :class="{ active: store.activeTab === 'service' }"
        @click="store.activeTab = 'service'"
      >
        模型服务
      </button>
      <button
        class="tab-item"
        :class="{ active: store.activeTab === 'local' }"
        @click="store.activeTab = 'local'"
      >
        本地模型
      </button>
    </div>

    <!-- 模型服务 -->
    <div v-if="store.activeTab === 'service'" class="service-panel">
      <div class="service-layout">
        <!-- 左侧供应商列表 -->
        <div class="supplier-sidebar">
          <div class="supplier-list">
            <div
              v-for="supplier in store.supplierList"
              :key="supplier.supplierName"
              class="supplier-item"
              :class="{ active: store.currentSupplier?.supplierName === supplier.supplierName }"
              @click="store.selectSupplier(supplier)"
            >
              <div class="supplier-name">{{ supplier.supplierTitle || supplier.supplierName }}</div>
              <div class="supplier-status" :class="{ active: supplier.status === true || supplier.status === 'true' }">
                {{ supplier.status === true || supplier.status === 'true' ? '启用' : '禁用' }}
              </div>
            </div>
          </div>
          <button class="btn-primary add-supplier-btn" @click="store.addSupplierShow = true">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            添加供应商
          </button>
        </div>

        <!-- 右侧配置面板 -->
        <div class="config-main">
          <div v-if="!store.currentSupplier" class="empty-state">
            <p>请选择或添加一个模型供应商</p>
          </div>
          <template v-else>
            <!-- 配置头部 -->
            <div class="config-header">
              <div class="config-title">
                <span>{{ store.currentSupplier.supplierTitle }}</span>
                <span v-if="store.currentSupplier.home" class="help-link" @click="openHelp(store.currentSupplier.home)">获取密钥</span>
              </div>
              <div class="config-actions">
                <label class="switch-label">
                  <input
                    type="checkbox"
                    :checked="store.currentSupplier.status === true || store.currentSupplier.status === 'true'"
                    @change="onSupplierStatusChange"
                  />
                  <span class="switch-slider"></span>
                  <span class="switch-text">
                    {{ store.currentSupplier.status === true || store.currentSupplier.status === 'true' ? '启用' : '禁用' }}
                  </span>
                </label>
                <button class="icon-btn danger" title="删除供应商" @click="store.deleteSupplierShow = true">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"/>
                    <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                  </svg>
                </button>
              </div>
            </div>

            <!-- API 配置表单 -->
            <div class="config-form">
              <div class="form-group">
                <label>API 密钥</label>
                <div class="input-with-btn">
                  <input v-model="store.supplierConfig.apiKey" class="input" placeholder="请输入API密钥">
                  <button class="btn-secondary" @click="handleCheckConfig">检查</button>
                </div>
              </div>
              <div class="form-group">
                <label>API 地址</label>
                <input v-model="store.supplierConfig.baseUrl" class="input" placeholder="请输入API地址">
                <div class="form-hint">示例: {{ store.currentSupplier.baseUrlExample || 'https://api.openai.com/v1' }}</div>
              </div>
              <div class="form-actions">
                <button class="btn-primary" @click="handleSaveConfig">保存API</button>
              </div>
            </div>

            <!-- 模型列表 -->
            <div class="model-section">
              <div class="model-section-header">
                <div class="model-section-title">
                  模型
                  <span class="model-section-sub">默认从/models获取所有模型</span>
                </div>
                <div class="model-section-actions">
                  <label class="switch-label small">
                    <span>开关所有</span>
                    <input type="checkbox" :checked="store.isAllModelEnable" @change="onAllModelStatusChange">
                    <span class="switch-slider"></span>
                  </label>
                </div>
              </div>
              <button class="btn-primary add-model-btn" @click="store.openAddModel">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                添加模型
              </button>

              <div class="model-table">
                <div class="model-table-header">
                  <div class="model-col model-col-name">模型</div>
                  <div class="model-col model-col-cap">功能</div>
                  <div class="model-col model-col-status">状态</div>
                  <div class="model-col model-col-action">操作</div>
                </div>
                <div v-if="!store.supplierModels.length" class="model-empty">当前服务商下属暂无模型可用</div>
                <div
                  v-for="model in store.supplierModels"
                  :key="model.modelName"
                  class="model-table-row"
                >
                  <div class="model-col model-col-name">
                    <span class="model-title">{{ model.title }}</span>
                    <button class="icon-btn plain" title="修改模型" @click="store.openEditModel(model)">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                        <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                      </svg>
                    </button>
                  </div>
                  <div class="model-col model-col-cap">
                    <span
                      v-for="cap in model.capability"
                      :key="cap"
                      class="cap-tag"
                    >{{ formatCapability(cap) }}</span>
                  </div>
                  <div class="model-col model-col-status">
                    <label class="switch-label small">
                      <input type="checkbox" :checked="model.status" @change="store.toggleModelStatus(model)">
                      <span class="switch-slider"></span>
                    </label>
                  </div>
                  <div class="model-col model-col-action">
                    <button class="icon-btn danger" title="删除模型" @click="store.delModel(model.modelName)">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6"/>
                        <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 本地模型 -->
    <div v-else class="local-panel">
      <div class="local-config">
        <div class="local-config-label">Ollama 接口地址</div>
        <div class="local-config-input">
          <input v-model="store.ollamaUrl" class="input" placeholder="请填写ollama接入地址" />
          <button class="btn-secondary" @click="handleSaveOllamaUrl">保存</button>
        </div>
        <div v-if="!store.isInstalledManager" class="local-config-notice">当前ollama地址不可用</div>
      </div>

      <div v-if="store.localModelList.length === 0" class="local-first-tip">首次使用，请选择要安装的模型</div>

      <div class="local-toolbar">
        <div class="local-filter-group">
          <button
            v-for="opt in localModeOptions"
            :key="opt.value"
            class="local-filter-btn"
            :class="{ active: store.localModeType === opt.value }"
            @click="onLocalModeChange(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
        <div class="local-search">
          <input v-model="store.localSearch" class="input" :placeholder="'搜索模型'" @keydown.enter="store.handleLocalSearch" />
          <button class="icon-btn plain" @click="store.handleLocalSearch">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
          </button>
        </div>
      </div>

      <div class="local-table-wrap" :class="{ mask: !store.ollamaUrl }">
        <div class="local-table">
          <div class="local-table-header">
            <div class="local-col local-col-model">模型</div>
            <div class="local-col local-col-size">大小</div>
            <div class="local-col local-col-desc">简介</div>
            <div class="local-col local-col-cap">功能</div>
            <div class="local-col local-col-action">操作</div>
          </div>
          <div v-if="!store.paginatedLocalModels.length" class="local-empty">暂无模型数据</div>
          <div
            v-for="row in store.paginatedLocalModels"
            :key="row.full_name"
            class="local-table-row"
          >
            <div class="local-col local-col-model">
              <span class="local-model-link" @click="openModelLink(row.link)">{{ row.full_name }}</span>
            </div>
            <div class="local-col local-col-size">{{ row.download_size }}</div>
            <div class="local-col local-col-desc" :title="row.title">{{ row.title }}</div>
            <div class="local-col local-col-cap">
              <span v-for="cap in row.capability" :key="cap" class="cap-tag">{{ formatModelTag(cap) }}</span>
            </div>
            <div class="local-col local-col-action">
              <button
                v-if="row.install"
                class="btn-table danger"
                @click="store.delLocalModel(row.full_name)"
              >删除</button>
              <button
                v-else
                class="btn-table success"
                @click="store.installLocalModel({ model: row.model, parameters: row.parameters })"
              >安装</button>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="store.localModelTotal > store.localPagination.pageSize" class="local-pagination">
          <button
            class="page-btn"
            :disabled="store.localPagination.page === 1"
            @click="changeLocalPage(store.localPagination.page - 1)"
          >上一页</button>
          <span class="page-info">{{ store.localPagination.page }} / {{ Math.ceil(store.localModelTotal / store.localPagination.pageSize) }}</span>
          <button
            class="page-btn"
            :disabled="store.localPagination.page >= Math.ceil(store.localModelTotal / store.localPagination.pageSize)"
            @click="changeLocalPage(store.localPagination.page + 1)"
          >下一页</button>
        </div>
      </div>
    </div>

    <!-- 添加/编辑模型弹窗 -->
    <div v-if="store.addModelShow" class="modal-overlay" @click.self="store.closeAddModel">
      <div class="modal-panel">
        <div class="modal-header">
          <h3>{{ store.isEditModel ? '修改模型' : '添加模型' }}</h3>
          <button class="close-btn" @click="store.closeAddModel">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>模型ID</label>
            <input v-model="store.addModelForm.modelName" class="input" placeholder="请输入模型ID" :disabled="store.isEditModel">
          </div>
          <div class="form-group">
            <label>模型别名</label>
            <input v-model="store.addModelForm.title" class="input" placeholder="请输入模型别名">
          </div>
          <div class="form-group">
            <label>模型功能</label>
            <div class="capability-options">
              <label
                v-for="opt in store.CAPABILITY_OPTIONS"
                :key="opt.value"
                class="capability-option"
                :class="{ disabled: store.cantChooseCapability && opt.value !== 'embedding' }"
              >
                <input
                  type="checkbox"
                  :value="opt.value"
                  :checked="store.addModelForm.capability.includes(opt.value)"
                  :disabled="store.cantChooseCapability && opt.value !== 'embedding'"
                  @change="onCapabilityChange(opt.value)"
                >
                <span>{{ opt.label }}</span>
              </label>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="store.closeAddModel">取消</button>
          <button class="btn-primary" @click="handleConfirmModel">{{ store.isEditModel ? '确认' : '添加' }}</button>
        </div>
      </div>
    </div>

    <!-- 添加供应商弹窗 -->
    <div v-if="store.addSupplierShow" class="modal-overlay" @click.self="store.cancelAddSupplier">
      <div class="modal-panel">
        <div class="modal-header">
          <h3>添加模型服务商</h3>
          <button class="close-btn" @click="store.cancelAddSupplier">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>供应商名称</label>
            <input v-model="store.addSupplierForm.supplierTitle" class="input" placeholder="如：OpenAI">
          </div>
          <div class="form-group">
            <label>接口地址</label>
            <input v-model="store.addSupplierForm.baseUrl" class="input" placeholder="https://api.openai.com/v1">
            <div class="form-hint">需要兼容OpenAI格式的接口</div>
          </div>
          <div class="form-group">
            <label>密钥</label>
            <input v-model="store.addSupplierForm.apiKey" class="input" type="password" placeholder="sk-...">
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="store.cancelAddSupplier">取消</button>
          <button class="btn-primary" @click="handleConfirmSupplier">确认</button>
        </div>
      </div>
    </div>

    <!-- 删除供应商确认 -->
    <div v-if="store.deleteSupplierShow" class="modal-overlay" @click.self="store.deleteSupplierShow = false">
      <div class="modal-panel modal-sm">
        <div class="modal-header">
          <h3>删除供应商</h3>
          <button class="close-btn" @click="store.deleteSupplierShow = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p>确定要删除供应商「{{ store.currentSupplier?.supplierTitle }}」吗？该供应商下的所有模型配置也将被删除。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="store.deleteSupplierShow = false">取消</button>
          <button class="btn-primary danger" @click="store.removeSupplier">确认删除</button>
        </div>
      </div>
    </div>

    <!-- 删除模型确认 -->
    <div v-if="store.deleteModelShow" class="modal-overlay" @click.self="store.cancelDelModel">
      <div class="modal-panel modal-sm">
        <div class="modal-header">
          <h3>删除模型</h3>
          <button class="close-btn" @click="store.cancelDelModel">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p>确定要删除模型「{{ store.deleteModelName }}」吗？</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="store.cancelDelModel">取消</button>
          <button class="btn-primary danger" @click="store.confirmDelModel">确认删除</button>
        </div>
      </div>
    </div>

    <!-- 本地模型安装进度 -->
    <div v-if="store.installModelShow" class="modal-overlay" @click.self="store.closeInstallModel">
      <div class="modal-panel">
        <div class="modal-header">
          <h3>{{ store.downloadText }}</h3>
          <button class="close-btn" @click="store.closeInstallModel">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${store.modelInstallProgress.progress}%` }"></div>
            <span class="progress-text">{{ store.modelInstallProgress.progress }}%</span>
          </div>
          <div class="install-progress-info">
            <span>总大小: {{ formatBytes(store.modelInstallProgress.total, true) }}</span>
            <span>已下载: {{ formatBytes(store.modelInstallProgress.completed, true) }}</span>
            <span class="speed-wrap">
              速度: {{ formatBytes(store.modelInstallProgress.speed, true) }}/s
              <button class="icon-btn plain" title="尝试重新选择下载节点，以优化下载速度" @click="store.reconnectModelDownload">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
              </button>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 本地模型删除中 -->
    <div v-if="store.deletingLocalModel" class="modal-overlay">
      <div class="modal-panel modal-sm">
        <div class="modal-body">
          <div class="loading-wrap">
            <div class="spinner"></div>
            <p>模型删除中，请稍后</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 本地模型删除确认 -->
    <div v-if="store.deleteLocalModelShow" class="modal-overlay" @click.self="store.cancelDelLocalModel">
      <div class="modal-panel modal-sm">
        <div class="modal-header">
          <h3>删除模型</h3>
          <button class="close-btn" @click="store.cancelDelLocalModel">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p>是否确认删除这个模型</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="store.cancelDelLocalModel">取消</button>
          <button class="btn-primary danger" @click="handleConfirmDelLocalModel">确认</button>
        </div>
      </div>
    </div>

    <!-- 安装模型管理器确认 -->
    <div v-if="store.managerInstallConfirmShow" class="modal-overlay" @click.self="store.notInstallManagerNow">
      <div class="modal-panel">
        <div class="modal-header">
          <h3>提示</h3>
          <button class="close-btn" @click="store.notInstallManagerNow">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p>检测到您没有安装模型管理器，是否立即安装？</p>
          <div class="form-group">
            <label>模型管理器</label>
            <select v-model="store.managerForInstall" class="input">
              <option value="ollama">ollama</option>
            </select>
          </div>
          <div class="form-group">
            <label>模型存储位置</label>
            <button class="btn-secondary" @click="store.chooseManagerInstallPath">
              {{ store.managerInstallPath || '选择' }}
            </button>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="store.notInstallManagerNow">暂不安装</button>
          <button class="btn-primary" @click="handleInstallModelManager">立即安装</button>
        </div>
      </div>
    </div>

    <!-- 模型管理器安装进度 -->
    <div v-if="store.managerInstallProgressShow" class="modal-overlay" @click.self="store.closeManagerInstallProgress">
      <div class="modal-panel">
        <div class="modal-header">
          <h3>{{ store.managerInstallNotice }}</h3>
          <button class="close-btn" @click="store.closeManagerInstallProgress">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${store.modelManagerInstallProgress.progress}%` }"></div>
            <span class="progress-text">{{ store.modelManagerInstallProgress.progress }}%</span>
          </div>
          <div class="install-progress-info">
            <span>大小: {{ formatBytes(store.modelManagerInstallProgress.total, true) }}</span>
            <span>已下载: {{ formatBytes(store.modelManagerInstallProgress.completed, true) }}</span>
            <span class="speed-wrap">
              速度: {{ formatBytes(store.modelManagerInstallProgress.speed, true) }}
              <button class="icon-btn plain" title="尝试重新选择下载节点，以优化下载速度" @click="store.reconnectModelDownload">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"/>
                  <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                </svg>
              </button>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useModelStore } from '@/stores/model'

const store = useModelStore()

const formatCapability = (cap: string) => {
  const map: Record<string, string> = {
    llm: 'LLM',
    vision: 'Vision',
    embedding: 'Embedding',
    tools: 'Tools',
  }
  return map[cap] || cap
}

const formatModelTag = (cap: string) => {
  const map: Record<string, string> = {
    llm: 'LLM',
    vision: '视觉',
    embedding: '嵌入',
    tools: '工具',
  }
  return map[cap] || cap
}

const openHelp = (url: string) => {
  window.open(url)
}

const openModelLink = (url: string) => {
  if (!url) return
  window.open(url)
}

// 本地模型筛选选项
const localModeOptions = [
  { label: '所有', value: 'all' },
  { label: 'LLM', value: 'llm' },
  { label: '视觉', value: 'vision' },
  { label: '嵌入', value: 'embedding' },
  { label: '工具', value: 'tools' },
  { label: '已安装', value: 'installed' },
]

const onLocalModeChange = (value: string) => {
  store.localModeType = value
  store.handleLocalSearch()
}

const changeLocalPage = (page: number) => {
  store.localPagination.page = page
}

const handleSaveOllamaUrl = async () => {
  try {
    await store.setOllamaHost()
    alert('设置成功')
  } catch (e: any) {
    alert(e.message || '保存失败')
  }
}

const handleConfirmDelLocalModel = async () => {
  try {
    await store.confirmDelLocalModel()
    alert('删除成功')
  } catch (e: any) {
    alert(e.message || '删除失败')
  }
}

const handleInstallModelManager = async () => {
  try {
    await store.installModelManager()
  } catch (e: any) {
    alert(e.message || '安装失败')
  }
}

// 字节格式化
const formatBytes = (bytes: number, unit = false) => {
  if (!bytes || bytes <= 0) return unit ? '0 B' : '0'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const k = 1024
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  const size = parseFloat((bytes / Math.pow(k, i)).toFixed(2))
  return unit ? `${size} ${units[i]}` : String(size)
}

const onSupplierStatusChange = (e: Event) => {
  if (!store.currentSupplier) return
  const checked = (e.target as HTMLInputElement).checked
  store.toggleSupplierStatus(store.currentSupplier, checked)
}

const onAllModelStatusChange = (e: Event) => {
  const checked = (e.target as HTMLInputElement).checked
  store.toggleAllModelStatus(checked)
}

const onCapabilityChange = (value: string) => {
  const current = [...store.addModelForm.capability]
  if (value === 'embedding') {
    if (current.includes('embedding')) {
      store.onCapabilityChange([])
    } else {
      store.onCapabilityChange(['embedding'])
    }
    return
  }
  if (current.includes('embedding')) {
    store.onCapabilityChange([value])
    return
  }
  if (current.includes(value)) {
    store.onCapabilityChange(current.filter((c) => c !== value))
  } else {
    store.onCapabilityChange([...current, value])
  }
}

const handleSaveConfig = async () => {
  try {
    await store.saveSupplierConfig()
    alert('配置保存成功')
  } catch (e: any) {
    alert(e.message || '保存失败')
  }
}

const handleCheckConfig = async () => {
  try {
    const msg = await store.checkSupplierConfig()
    alert(msg || '配置有效')
  } catch (e: any) {
    alert(e.message || '检查失败')
  }
}

const handleConfirmSupplier = async () => {
  try {
    await store.confirmAddSupplier()
    alert('添加成功')
  } catch (e: any) {
    alert(e.message || '添加失败')
  }
}

const handleConfirmModel = async () => {
  try {
    await store.confirmAddModel()
    alert(store.isEditModel ? '修改成功' : '添加成功')
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

onMounted(() => {
  store.loadSupplierList()
})

// 切换到本地模型 Tab 时加载数据
watch(
  () => store.activeTab,
  (tab) => {
    if (tab === 'local') {
      store.loadLocalModels()
    }
  }
)
</script>

<style scoped lang="scss">
.models-page {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-tabs {
  display: flex;
  gap: 8px;
  padding: 16px 24px 0;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;
}

.tab-item {
  padding: 10px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  font-size: 14px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: all 0.2s;

  &:hover {
    color: var(--text-primary);
  }

  &.active {
    color: var(--accent-color);
    border-bottom-color: var(--accent-color);
  }
}

.service-panel {
  flex: 1;
  overflow: hidden;
  padding: 16px 24px 24px;
}

.service-layout {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 20px;
  height: 100%;
  overflow: hidden;
}

.supplier-sidebar {
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
}

.supplier-list {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.supplier-item {
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;

  &:hover {
    background: var(--bg-hover);
  }

  &.active {
    background: rgba(59, 130, 246, 0.08);
  }
}

.supplier-name {
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.supplier-status {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 999px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  flex-shrink: 0;

  &.active {
    background: #dcfce7;
    color: #166534;
  }
}

.add-supplier-btn {
  width: 100%;
  justify-content: center;
}

.config-main {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.config-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 20px;
  flex-shrink: 0;
}

.config-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
}

.help-link {
  font-size: 12px;
  color: var(--accent-color);
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

.config-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
  flex-shrink: 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;

  label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-secondary);
  }
}

.input-with-btn {
  display: flex;
  gap: 8px;

  .input {
    flex: 1;
  }
}

.form-hint {
  font-size: 12px;
  color: var(--text-tertiary);
}

.form-actions {
  display: flex;
  justify-content: flex-start;
}

.model-section {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  margin-top: 8px;
}

.model-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.model-section-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-section-sub {
  font-size: 12px;
  font-weight: normal;
  color: var(--text-tertiary);
}

.model-section-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.add-model-btn {
  margin-bottom: 12px;
}

.model-table {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.model-table-header,
.model-table-row {
  display: grid;
  grid-template-columns: 1fr 160px 80px 60px;
  align-items: center;
  padding: 10px 14px;
}

.model-table-header {
  background: var(--bg-primary);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.model-table-row {
  border-top: 1px solid var(--border-color);
  font-size: 13px;
  color: var(--text-primary);

  &:hover {
    background: var(--bg-hover);
  }
}

.model-col-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-col-cap {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.cap-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.model-empty {
  padding: 40px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  border-top: 1px solid var(--border-color);
}

.capability-options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.capability-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.local-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 16px 24px 24px;
}

.empty-state {
  text-align: center;
  color: var(--text-tertiary);
  font-size: 14px;
}

.local-config {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}

.local-config-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  flex-shrink: 0;
}

.local-config-input {
  display: flex;
  gap: 8px;
  flex: 1;
  max-width: 480px;

  .input {
    flex: 1;
  }
}

.local-config-notice {
  font-size: 12px;
  color: #ef4444;
}

.local-first-tip {
  margin-top: 16px;
  font-size: 13px;
  color: var(--text-secondary);
  flex-shrink: 0;
}

.local-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  flex-shrink: 0;
}

.local-filter-group {
  display: flex;
  gap: 8px;
}

.local-filter-btn {
  padding: 6px 14px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--accent-color);
    color: var(--accent-color);
  }

  &.active {
    border-color: var(--accent-color);
    background: rgba(59, 130, 246, 0.08);
    color: var(--accent-color);
  }
}

.local-search {
  display: flex;
  align-items: center;
  gap: 6px;

  .input {
    width: 220px;
  }
}

.local-table-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-top: 16px;
  min-height: 0;

  &.mask {
    position: relative;

    &::after {
      content: '';
      position: absolute;
      inset: 0;
      background: rgba(0, 0, 0, 0.4);
      z-index: 10;
    }
  }
}

.local-table {
  flex: 1;
  overflow-y: auto;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  min-height: 0;
}

.local-table-header,
.local-table-row {
  display: grid;
  grid-template-columns: 160px 80px 1fr 140px 80px;
  align-items: center;
  padding: 10px 14px;
  gap: 12px;
}

.local-table-header {
  background: var(--bg-primary);
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 2;
}

.local-table-row {
  font-size: 13px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);

  &:hover {
    background: var(--bg-hover);
  }

  &:last-child {
    border-bottom: none;
  }
}

.local-col {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.local-col-desc {
  color: var(--text-secondary);
}

.local-col-cap {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.local-model-link {
  color: var(--accent-color);
  cursor: pointer;

  &:hover {
    text-decoration: underline;
  }
}

.local-empty {
  padding: 40px;
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
}

.btn-table {
  padding: 5px 12px;
  border-radius: var(--radius-md);
  border: none;
  font-size: 12px;
  cursor: pointer;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.9;
  }

  &.success {
    background: #22c55e;
    color: #fff;
  }

  &.danger {
    background: #ef4444;
    color: #fff;
  }
}

.local-pagination {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
  flex-shrink: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.page-btn {
  padding: 5px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;

  &:hover:not(:disabled) {
    border-color: var(--accent-color);
    color: var(--accent-color);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

/* Progress */
.progress-bar {
  width: 100%;
  height: 24px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: var(--accent-color);
  transition: width 0.3s;
}

.progress-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: #fff;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

.install-progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  font-size: 13px;
  color: var(--text-secondary);
}

.speed-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
}

.loading-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px 0;
  color: var(--text-primary);
  font-size: 14px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border-color);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Switch */
.switch-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);

  input {
    display: none;
  }
}

.switch-slider {
  width: 40px;
  height: 22px;
  background: var(--bg-tertiary);
  border-radius: 999px;
  position: relative;
  transition: background 0.2s;
  flex-shrink: 0;

  &::after {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    background: #fff;
    border-radius: 50%;
    top: 2px;
    left: 2px;
    transition: transform 0.2s;
  }
}

.switch-label input:checked + .switch-slider {
  background: var(--accent-color);
}

.switch-label input:checked + .switch-slider::after {
  transform: translateX(18px);
}

.switch-label.small .switch-slider {
  width: 34px;
  height: 18px;

  &::after {
    width: 14px;
    height: 14px;
    top: 2px;
    left: 2px;
  }
}

.switch-label.small input:checked + .switch-slider::after {
  transform: translateX(16px);
}

.switch-text {
  font-size: 13px;
  color: var(--text-primary);
}

/* Buttons */
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: none;
  background: var(--accent-color);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.9;
  }

  &.danger {
    background: #ef4444;
  }
}

.btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;

  &:hover {
    border-color: var(--accent-color);
    color: var(--accent-color);
  }
}

.icon-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: var(--bg-hover);
    color: var(--accent-color);
  }

  &.danger:hover {
    color: #ef4444;
  }

  &.plain {
    width: 24px;
    height: 24px;
  }
}

/* Input */
.input {
  width: 100%;
  padding: 9px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  box-sizing: border-box;

  &:focus {
    border-color: var(--accent-color);
  }

  &:disabled {
    background: var(--bg-tertiary);
    color: var(--text-tertiary);
    cursor: not-allowed;
  }
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}

.modal-panel {
  width: 480px;
  max-height: 90vh;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  display: flex;
  flex-direction: column;
}

.modal-sm {
  width: 420px;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  flex-shrink: 0;

  h3 {
    font-size: 16px;
    font-weight: 600;
    color: var(--text-primary);
  }
}

.close-btn {
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    background: var(--bg-hover);
  }
}

.modal-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 12px 20px;
  border-top: 1px solid var(--border-color);
  flex-shrink: 0;
}
</style>
