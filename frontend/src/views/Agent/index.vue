<template>
  <div class="agent-page">
    <div class="section-header">
      <h2 class="section-title">智能体</h2>
      <button class="btn-primary" @click="openCreate">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        创建智能体
      </button>
    </div>

    <!-- 分类 + 搜索 -->
    <div class="filter-bar">
      <div class="category-list">
        <button
          v-for="cat in categories"
          :key="cat"
          class="category-btn"
          :class="{ active: activeCategory === cat }"
          @click="changeCategory(cat)"
        >
          {{ cat }}
        </button>
      </div>
      <div class="search-box">
        <input
          v-model="searchKeyword"
          class="search-input"
          placeholder="搜索智能体名称"
          @keydown.enter="handleSearch"
        />
        <button class="search-btn" @click="handleSearch">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
        </button>
      </div>
    </div>

    <div class="agent-grid">
      <div
        v-for="agent in agents"
        :key="agent.agent_name"
        class="agent-card"
        :class="{ 'system-card': agent.is_system }"
      >
        <div class="agent-card-main">
          <div class="agent-icon">{{ agent.icon || 'A' }}</div>
          <div class="agent-info">
            <div class="agent-title-row">
              <h3 class="agent-name" :title="agent.agent_title">{{ agent.agent_title }}</h3>
              <button
                class="collect-btn"
                :class="{ collected: agent.is_collect }"
                @click.stop="toggleCollect(agent)"
                :title="agent.is_collect ? '取消收藏' : '收藏'"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
              </button>
            </div>
            <p v-if="agent.description" class="agent-desc" :title="agent.description">{{ agent.description }}</p>
            <p class="agent-prompt" :title="agent.prompt">{{ agent.prompt }}</p>
          </div>
        </div>
        <div class="agent-footer">
          <div class="agent-tags">
            <span v-if="agent.agent_type" class="tag">{{ agent.agent_type }}</span>
            <span v-if="agent.is_system" class="tag system">系统</span>
          </div>
          <div class="agent-actions">
            <button class="action-text" @click="useAgent(agent)">使用</button>
            <button class="action-text" @click="openEdit(agent)">编辑</button>
            <button class="action-text danger" @click="confirmDelete(agent)">删除</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!agents.length" class="empty-state">
      <div class="empty-icon">🤖</div>
      <div class="empty-title">暂无智能体</div>
      <div class="empty-desc">{{ emptyHint }}</div>
    </div>

    <!-- Create / Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-panel modal-lg">
        <div class="modal-header">
          <h3>{{ isEdit ? '编辑智能体' : '创建智能体' }}</h3>
          <button class="close-btn" @click="closeModal">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <div class="avatar-section">
            <div class="avatar-preview" @click="showEmojiPicker = !showEmojiPicker">
              {{ formData.icon || '😀' }}
            </div>
            <button class="btn-secondary btn-sm" @click="showEmojiPicker = !showEmojiPicker">
              {{ showEmojiPicker ? '收起' : '选择头像' }}
            </button>
            <div v-if="showEmojiPicker" class="emoji-picker-wrap">
              <EmojiPicker :native="true" @select="onSelectEmoji" />
            </div>
          </div>
          <div class="form-group">
            <label>标题 <span class="required">*</span></label>
            <input v-model="formData.agent_title" class="input" placeholder="如：代码助手">
          </div>
          <div class="form-group">
            <label>类别</label>
            <select v-model="formData.agent_type" class="input select-input">
              <option value="">请选择类别</option>
              <option v-for="type in agentTypeOptions" :key="type" :value="type">{{ type }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>描述</label>
            <input v-model="formData.description" class="input" placeholder="简短描述该智能体的用途">
          </div>
          <div class="form-group">
            <label>提示词 <span class="required">*</span></label>
            <textarea v-model="formData.prompt" class="textarea" rows="5" placeholder="设定该智能体的角色和能力..." />
          </div>

          <div class="form-group">
            <label>知识库</label>
            <div class="multi-select" v-if="ragList.length">
              <div class="multi-select-trigger" @click="showRagDropdown = !showRagDropdown">
                <div class="multi-select-tags" v-if="formData.rag_ids.length">
                  <span v-for="id in formData.rag_ids" :key="id" class="multi-select-tag">
                    {{ id }}
                    <button class="tag-remove" @click.stop="removeRag(id)">×</button>
                  </span>
                </div>
                <span v-else class="multi-select-placeholder">请选择知识库</span>
                <svg class="multi-select-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotated: showRagDropdown }">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
              <div v-if="showRagDropdown" class="multi-select-dropdown">
                <label v-for="rag in ragList" :key="rag.ragName" class="multi-select-option">
                  <input type="checkbox" :value="rag.ragName" v-model="formData.rag_ids" />
                  <span>{{ rag.ragName }}</span>
                </label>
              </div>
            </div>
            <p v-else class="hint-text">暂无知识库，请先到知识库页面创建</p>
          </div>
          <div class="form-group">
            <label>MCP 工具</label>
            <div class="multi-select" v-if="mcpList.length">
              <div class="multi-select-trigger" @click="showMcpDropdown = !showMcpDropdown">
                <div class="multi-select-tags" v-if="formData.mcp_tool.length">
                  <span v-for="name in formData.mcp_tool" :key="name" class="multi-select-tag">
                    {{ name }}
                    <button class="tag-remove" @click.stop="removeMcp(name)">×</button>
                  </span>
                </div>
                <span v-else class="multi-select-placeholder">请选择 MCP 工具</span>
                <svg class="multi-select-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" :class="{ rotated: showMcpDropdown }">
                  <polyline points="6 9 12 15 18 9"/>
                </svg>
              </div>
              <div v-if="showMcpDropdown" class="multi-select-dropdown">
                <label v-for="mcp in mcpList" :key="mcp.name" class="multi-select-option">
                  <input type="checkbox" :value="mcp.name" v-model="formData.mcp_tool" />
                  <span>{{ mcp.name }}</span>
                </label>
              </div>
            </div>
            <p v-else class="hint-text">暂无 MCP 工具，请先到 MCP 页面添加</p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="closeModal">取消</button>
          <button class="btn-primary" @click="saveAgent">{{ isEdit ? '保存' : '创建' }}</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirm Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal-panel modal-sm">
        <div class="modal-header">
          <h3>确认删除</h3>
          <button class="close-btn" @click="showDeleteModal = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"/>
              <line x1="6" y1="6" x2="18" y2="18"/>
            </svg>
          </button>
        </div>
        <div class="modal-body">
          <p>是否确认删除智能体 <strong>{{ agentToDelete?.agent_title }}</strong>？删除后无法恢复。</p>
        </div>
        <div class="modal-footer">
          <button class="btn-secondary" @click="showDeleteModal = false">取消</button>
          <button class="btn-danger" @click="doDelete">确认删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { toast } from 'vue3-toastify'
import EmojiPicker from 'vue3-emoji-picker'
import 'vue3-emoji-picker/css'
import { agentApi } from '@/api/agent'
import { ragApi } from '@/api/rag'
import { mcpApi } from '@/api/mcp'
import type { AgentItem, RagItem, McpServer } from '@/types'

const router = useRouter()

const agents = ref<AgentItem[]>([])
const categories = ref<string[]>(['全部助手'])
const activeCategory = ref('全部助手')
const searchKeyword = ref('')
const showModal = ref(false)
const isEdit = ref(false)
const showEmojiPicker = ref(false)
const showDeleteModal = ref(false)
const showRagDropdown = ref(false)
const showMcpDropdown = ref(false)
const agentToDelete = ref<AgentItem | null>(null)

const ragList = ref<RagItem[]>([])
const mcpList = ref<McpServer[]>([])

const emptyHint = computed(() => {
  if (searchKeyword.value.trim()) return '没有找到相关智能体'
  return '创建智能体，预设角色和提示词，让 AI 更专业'
})

const agentTypeOptions = computed(() => {
  const fixed = ['全部助手','精选推荐',  '我的收藏']
  return categories.value.filter(c => !fixed.includes(c))
})

const formData = ref({
  agent_name: '',
  agent_title: '',
  agent_type: '',
  description: '',
  prompt: '',
  icon: '',
  rag_ids: [] as string[],
  mcp_tool: [] as string[],
})

const loadCategories = async () => {
  try {
    const res = await agentApi.getAgentTypes()
    const list = Array.isArray(res) ? res : []
    const fixed = ['全部助手','精选推荐',  '我的收藏']
    const others = list.filter((c: string) => !fixed.includes(c))
    categories.value = [...fixed, ...others]
  } catch (e) {
    console.error(e)
  }
}

const loadRagList = async () => {
  try {
    const res = await ragApi.getRagList()
    ragList.value = res || []
  } catch (e) {
    console.error(e)
  }
}

const loadMcpList = async () => {
  try {
    const res = await mcpApi.getServerList()
    mcpList.value = res || []
  } catch (e) {
    console.error(e)
  }
}

const loadAgents = async () => {
  try {
    const keyword = searchKeyword.value.trim()
    const cat = activeCategory.value

    let res: AgentItem[] = []

    if (cat === '我的收藏') {
      res = await agentApi.getCollectAgentList(keyword || undefined)
    } else if (cat === '精选推荐') {
      res = await agentApi.getSystemAgentList(keyword || undefined)
    } else if (cat === '全部助手') {
      res = await agentApi.getAgentList(undefined, keyword || undefined)
    } else {
      res = await agentApi.getAgentList(cat, keyword || undefined)
    }

    agents.value = res || []
  } catch (e) {
    console.error(e)
  }
}

const changeCategory = (cat: string) => {
  activeCategory.value = cat
  loadAgents()
}

const handleSearch = () => {
  loadAgents()
}

const openCreate = () => {
  isEdit.value = false
  formData.value = { agent_name: '', agent_title: '', agent_type: '', description: '', prompt: '', icon: '', rag_ids: [], mcp_tool: [] }
  showEmojiPicker.value = false
  showModal.value = true
  loadRagList()
  loadMcpList()
}

const openEdit = (agent: AgentItem) => {
  isEdit.value = true
  formData.value = {
    agent_name: agent.agent_name,
    agent_title: agent.agent_title || '',
    agent_type: agent.agent_type || '',
    description: agent.description || '',
    prompt: agent.prompt || '',
    icon: agent.icon || '',
    rag_ids: agent.rag_ids || [],
    mcp_tool: agent.mcp_tool || [],
  }
  showEmojiPicker.value = false
  showModal.value = true
  loadRagList()
  loadMcpList()
}

const closeModal = () => {
  showModal.value = false
  showEmojiPicker.value = false
  showRagDropdown.value = false
  showMcpDropdown.value = false
}

const onSelectEmoji = (emoji: any) => {
  formData.value.icon = emoji.i
  showEmojiPicker.value = false
}

const removeRag = (id: string) => {
  formData.value.rag_ids = formData.value.rag_ids.filter(r => r !== id)
}

const removeMcp = (name: string) => {
  formData.value.mcp_tool = formData.value.mcp_tool.filter(n => n !== name)
}

const saveAgent = async () => {
  const title = formData.value.agent_title.trim()
  const prompt = formData.value.prompt.trim()
  if (!title) {
    toast.warning('请输入智能体标题')
    return
  }
  if (!prompt) {
    toast.warning('请输入智能体提示词')
    return
  }
  try {
    if (isEdit.value) {
      await agentApi.modifyAgent({
        agent_name: formData.value.agent_name,
        agent_title: title,
        agent_type: formData.value.agent_type || undefined,
        description: formData.value.description.trim(),
        prompt,
        icon: formData.value.icon || undefined,
        rag_ids: formData.value.rag_ids.length ? formData.value.rag_ids : undefined,
        mcp_tool: formData.value.mcp_tool.length ? formData.value.mcp_tool : undefined,
      })
    } else {
      await agentApi.createAgent({
        agent_title: title,
        agent_type: formData.value.agent_type || undefined,
        description: formData.value.description.trim(),
        prompt,
        icon: formData.value.icon || undefined,
        rag_ids: formData.value.rag_ids.length ? formData.value.rag_ids : undefined,
        mcp_tool: formData.value.mcp_tool.length ? formData.value.mcp_tool : undefined,
      })
    }
    closeModal()
    await loadAgents()
  } catch (e) {
    console.error(e)
    toast.error(isEdit.value ? '保存失败' : '创建失败')
  }
}

const toggleCollect = async (agent: AgentItem) => {
  try {
    await agentApi.collectAgent(agent.agent_name, !agent.is_collect)
    agent.is_collect = !agent.is_collect
  } catch (e) {
    console.error(e)
  }
}

const confirmDelete = (agent: AgentItem) => {
  agentToDelete.value = agent
  showDeleteModal.value = true
}

const doDelete = async () => {
  if (!agentToDelete.value) return
  try {
    await agentApi.removeAgent(agentToDelete.value.agent_name)
    showDeleteModal.value = false
    agentToDelete.value = null
    await loadAgents()
  } catch (e) {
    console.error(e)
  }
}

const useAgent = (agent: AgentItem) => {
  router.push({ path: '/chat', query: { agent_name: agent.agent_name } })
}

onMounted(() => {
  loadCategories().then(() => {
    activeCategory.value = '全部助手'
    loadAgents()
  })
})
</script>

<style scoped lang="scss">
.agent-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

/* 分类 + 搜索 */
.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.category-list {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.category-btn {
  padding: 7px 16px;
  border-radius: 20px;
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--accent-color);
    color: var(--accent-color);
  }

  &.active {
    background: var(--accent-color);
    color: #fff;
    border-color: var(--accent-color);
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
  }
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  overflow: hidden;
  width: 260px;
  transition: border-color 0.2s;

  &:focus-within {
    border-color: var(--accent-color);
  }
}

.search-input {
  flex: 1;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 13px;
  outline: none;

  &::placeholder {
    color: var(--text-tertiary);
  }
}

.search-btn {
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover {
    color: var(--accent-color);
  }
}

/* 卡片网格 */
.agent-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.agent-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 20px;
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-active) 100%);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;

  &:hover {
    transform: translateY(-2px);
    border-color: var(--accent-color);
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.12);
  }

  &.system-card {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(139, 92, 246, 0.06) 100%);
    border-color: rgba(59, 130, 246, 0.2);

    &:hover {
      border-color: rgba(59, 130, 246, 0.4);
      box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
    }
  }
}

.agent-card-main {
  display: flex;
  gap: 14px;
}

.agent-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-color), #8b5cf6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
}

.agent-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.agent-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.agent-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.collect-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  color: var(--text-tertiary);
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: color 0.2s;

  &:hover {
    color: #f59e0b;
  }

  &.collected {
    color: #f59e0b;
  }
}

.agent-desc {
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-prompt {
  font-size: 13px;
  color: var(--text-tertiary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.agent-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color);
}

.agent-tags {
  display: flex;
  gap: 6px;
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  background: var(--bg-active);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);

  &.system {
    background: rgba(59, 130, 246, 0.1);
    color: var(--accent-color);
    border-color: rgba(59, 130, 246, 0.2);
  }
}

.agent-actions {
  display: flex;
  gap: 14px;
}

.action-text {
  font-size: 13px;
  color: var(--accent-color);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  font-weight: 500;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.8;
    text-decoration: underline;
  }

  &.danger {
    color: #ef4444;
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
}

.empty-icon {
  font-size: 56px;
  margin-bottom: 20px;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.empty-desc {
  font-size: 14px;
  color: var(--text-tertiary);
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  backdrop-filter: blur(2px);
}

.modal-panel {
  width: 520px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
}

.modal-lg {
  width: 580px;
}

.modal-sm {
  width: 400px;
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
  flex: 1;
  min-height: 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-color);
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

    .required {
      color: #ef4444;
    }
  }
}

.input,
.textarea,
.select-input {
  padding: 9px 12px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;

  &:focus {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
  }

  &::placeholder {
    color: var(--text-tertiary);
  }
}

.select-input {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%236b7280' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  padding-right: 30px;
}

.textarea {
  resize: vertical;
  min-height: 90px;
}

.emoji-picker-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.emoji-preview {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-color), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #fff;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  position: relative;
}

.avatar-preview {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--accent-color), #8b5cf6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
  cursor: pointer;
  transition: transform 0.2s;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.25);
}

.avatar-preview:hover {
  transform: scale(1.05);
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.emoji-picker-wrap {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 8px;
  z-index: 10;
}

/* 高级配置 */
.advanced-section {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.advanced-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg-secondary);
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;

  &:hover {
    background: var(--bg-hover);
  }
}

.advanced-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.advanced-arrow {
  transition: transform 0.25s ease;
  color: var(--text-secondary);

  &.rotated {
    transform: rotate(180deg);
  }
}

.advanced-content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.checkbox-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  cursor: pointer;
  font-size: 13px;
  color: var(--text-primary);
  transition: all 0.2s;

  input[type="checkbox"] {
    width: 14px;
    height: 14px;
    accent-color: var(--accent-color);
    cursor: pointer;
  }

  &:hover {
    border-color: var(--accent-color);
  }

  &:has(input:checked) {
    border-color: var(--accent-color);
    background: rgba(59, 130, 246, 0.08);
  }
}

.hint-text {
  font-size: 13px;
  color: var(--text-tertiary);
  margin: 0;
}

/* 多选下拉 */
.multi-select {
  position: relative;
}

.multi-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
  cursor: pointer;
  min-height: 38px;
  transition: border-color 0.2s;

  &:hover {
    border-color: var(--accent-color);
  }
}

.multi-select-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  flex: 1;
}

.multi-select-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  background: rgba(59, 130, 246, 0.1);
  color: var(--accent-color);
  border: 1px solid rgba(59, 130, 246, 0.2);
}

.tag-remove {
  background: none;
  border: none;
  color: var(--accent-color);
  cursor: pointer;
  font-size: 14px;
  padding: 0;
  line-height: 1;
  opacity: 0.7;

  &:hover {
    opacity: 1;
  }
}

.multi-select-placeholder {
  font-size: 13px;
  color: var(--text-tertiary);
}

.multi-select-arrow {
  flex-shrink: 0;
  transition: transform 0.2s ease;
  color: var(--text-tertiary);

  &.rotated {
    transform: rotate(180deg);
  }
}

.multi-select-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 4px;
  max-height: 180px;
  overflow-y: auto;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: 10;
}

.multi-select-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s;

  input[type="checkbox"] {
    width: 14px;
    height: 14px;
    accent-color: var(--accent-color);
    cursor: pointer;
  }

  &:hover {
    background: var(--bg-hover);
  }
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: none;
  background: var(--accent-color);
  color: #fff;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.9;
  }
}

.btn-secondary {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;

  &:hover {
    background: var(--bg-hover);
  }
}

.btn-danger {
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: none;
  background: #ef4444;
  color: #fff;
  font-size: 14px;
  cursor: pointer;

  &:hover {
    opacity: 0.9;
  }
}
</style>
