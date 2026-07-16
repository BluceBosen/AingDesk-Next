<template>
  <div class="rag-detail">
    <!-- 顶部：知识库标题 + 操作按钮 -->
    <div class="detail-header">
      <div class="header-title">
        <span class="rag-title" :title="rag.ragName">{{ rag.ragName }}</span>
      </div>
      <div class="header-actions">
        <button class="btn-secondary edit-btn" @click="$emit('edit')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
            <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
          </svg>
          编辑
        </button>
        <button class="btn-primary upload-btn" @click="$emit('upload')">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
          上传文件
        </button>
      </div>
    </div>

    <!-- 下方：左边文件列表，右边文档内容 -->
    <div class="detail-body">
      <!-- 左侧：知识库文件列表 -->
      <div class="doc-panel">
        <div class="files-info">
          <span class="text-secondary">{{ docs.length }} 个文件</span>
          <span v-if="parsing" class="parsing-tip">
            <svg class="spin" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M21 12a9 9 0 11-6.219-8.56"/>
            </svg>
            文档嵌入中...
          </span>
        </div>

        <div class="doc-list-wrap">
          <div v-if="loadingDocs" class="loading-mask">加载中...</div>
          <ul v-else class="doc-list">
            <li
              v-for="doc in docs"
              :key="doc.docId"
              class="doc-item"
              :class="{ active: activeDocId === doc.docId }"
              @click="$emit('select-doc', doc)"
            >
              <div class="doc-item-main">
                <svg v-if="doc.is_parsed === 0 || doc.is_parsed === 2" class="spin doc-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 12a9 9 0 11-6.219-8.56"/>
                </svg>
                <svg v-else-if="doc.is_parsed === -1" class="doc-icon text-danger" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="15" y1="9" x2="9" y2="15"/>
                  <line x1="9" y1="9" x2="15" y2="15"/>
                </svg>
                <svg v-else class="doc-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
                <span class="doc-name" :title="doc.docName">{{ doc.docName }}</span>
              </div>
              <div class="doc-actions" @click.stop>
                <div class="more-menu" tabindex="0" @click="toggleDocDropdown(doc.docId)">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="5" r="2"/>
                    <circle cx="12" cy="12" r="2"/>
                    <circle cx="12" cy="19" r="2"/>
                  </svg>
                  <div class="dropdown" :class="{ visible: activeDocDropdown === doc.docId }">
                    <div class="dropdown-item danger" @click="$emit('delete-doc', doc)">删除</div>
                  </div>
                </div>
              </div>
            </li>
          </ul>
          <div v-if="!docs.length && !loadingDocs" class="list-empty">
            暂无文档，点击上传
          </div>
        </div>
      </div>

      <!-- 右侧：文档内容预览 -->
      <div class="content-panel">
        <div v-if="loadingContent" class="loading-mask">加载文档内容...</div>
        <div v-else-if="content" class="markdown-body" v-html="renderedContent" />
        <div v-else class="empty-content">
          <div class="empty-icon">📝</div>
          <div class="empty-title">选择文档查看内容</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import type { RagItem, RagDoc } from '@/types'

const props = defineProps<{
  rag: RagItem
  docs: RagDoc[]
  activeDocId: string | null
  content: string
  loadingDocs: boolean
  loadingContent: boolean
  parsing: boolean
}>()

defineEmits<{
  (e: 'upload'): void
  (e: 'edit'): void
  (e: 'select-doc', doc: RagDoc): void
  (e: 'delete-doc', doc: RagDoc): void
}>()

const activeDocDropdown = ref<string | null>(null)

const toggleDocDropdown = (docId: string) => {
  activeDocDropdown.value = activeDocDropdown.value === docId ? null : docId
}

const closeDocDropdown = () => {
  activeDocDropdown.value = null
}

onMounted(() => {
  document.addEventListener('click', closeDocDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDocDropdown)
})

// 简单 markdown 渲染：换行和代码块
const renderedContent = computed(() => {
  let html = props.content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // 代码块
  html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  // 段落
  html = html.split('\n\n').map((p) => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('')
  return html
})
</script>

<style scoped lang="scss">
.rag-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100%;
  overflow: hidden;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px;
  border-bottom: 1px solid var(--border-color);
  gap: 8px;
  flex-shrink: 0;
}

.header-title {
  min-width: 0;
  flex: 1;
}

.rag-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.detail-body {
  flex: 1;
  display: flex;
  min-height: 0;
  overflow: hidden;
}

.doc-panel {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-color);
  background: var(--bg-primary);
}

.edit-btn {
  font-size: 12px;
}

.upload-btn {
  padding: 6px 10px;
  font-size: 12px;
}

.files-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  font-size: 12px;
  color: var(--text-secondary);
}

.parsing-tip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--warning-color, #f59e0b);
}

.doc-list-wrap {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  position: relative;
}

.doc-list {
  list-style: none;
  padding: 0 8px 8px;
  margin: 0;
}

.doc-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 8px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;

  &:hover {
    background: var(--bg-hover);
  }

  &.active {
    background: var(--accent-color-soft, #e3e9fc);
    color: var(--accent-color);
  }
}

.doc-item-main {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.doc-icon {
  flex-shrink: 0;
  color: var(--text-tertiary);
}

.text-danger {
  color: var(--danger-color, #ef4444);
}

.doc-name {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
}

.doc-actions {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.more-menu {
  position: relative;
  outline: none;
}

.dropdown {
  display: none;
  position: absolute;
  right: 0;
  top: 22px;
  min-width: 100px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: 10;
  padding: 4px 0;

  &.visible {
    display: block;
  }
}

.dropdown-item {
  padding: 8px 14px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background: var(--bg-hover);
  }

  &.danger {
    color: var(--danger-color, #ef4444);
  }
}

.list-empty {
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  padding: 40px 20px;
}

.loading-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 13px;
  background: var(--bg-primary);
}

.content-panel {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  padding: 20px;
  background: var(--bg-primary);
}

.markdown-body {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);

  p {
    margin-bottom: 12px;
  }

  pre {
    background: var(--bg-secondary);
    padding: 12px;
    border-radius: var(--radius-md);
    overflow-x: auto;
    margin-bottom: 12px;
  }

  code {
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    font-size: 13px;
  }
}

.empty-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);

  .empty-icon {
    font-size: 40px;
    margin-bottom: 12px;
  }

  .empty-title {
    font-size: 14px;
  }
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
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
</style>
