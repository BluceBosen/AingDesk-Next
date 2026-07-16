<template>
  <div class="mcp-list">
    <div ref="addWrapperRef" class="add-wrapper">
      <button class="btn-primary add-btn" @click.stop="toggleDropdown">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="12" y1="5" x2="12" y2="19"/>
          <line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        添加服务器
      </button>
      <div v-if="dropdownVisible" class="dropdown-menu">
        <div class="dropdown-section">新配置</div>
        <div class="dropdown-item" @click="addCustom">自定义</div>
        <template v-if="mcpStore.templateList.length">
          <div class="dropdown-section">预设模板</div>
          <div
            v-for="item in mcpStore.templateList"
            :key="item.name"
            class="dropdown-item"
            :title="item.description"
            @click="addFromTemplate(item)"
          >
            {{ item.name }}
          </div>
        </template>
      </div>
    </div>

    <div class="list-wrap">
      <div
        v-for="server in mcpStore.serverList"
        :key="server.name"
        class="server-item"
        :class="{ active: mcpStore.currentName === server.name }"
        @click="mcpStore.selectServer(server.name)"
      >
        <div class="server-left">
          <svg class="server-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="2" width="9" height="9" rx="1"/>
            <rect x="13" y="2" width="9" height="9" rx="1"/>
            <rect x="2" y="13" width="9" height="9" rx="1"/>
            <rect x="13" y="13" width="9" height="9" rx="1"/>
          </svg>
          <span class="server-name" :title="server.name">{{ server.name }}</span>
        </div>
        <span v-if="server.isActive ?? server.is_active" class="status-dot active" />
        <span v-else class="status-dot" />
      </div>
      <div v-if="!mcpStore.serverList.length" class="list-empty">暂无服务器</div>
    </div>

    <button class="btn-secondary config-btn" @click="mcpStore.openConfig">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
        <line x1="16" y1="13" x2="8" y2="13"/>
        <line x1="16" y1="17" x2="8" y2="17"/>
        <polyline points="10 9 9 9 8 9"/>
      </svg>
      编辑配置文件
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useMcpStore } from '@/stores/mcp'
import type { McpServerForm } from '@/types'

const mcpStore = useMcpStore()
const dropdownVisible = ref(false)
const addWrapperRef = ref<HTMLElement | null>(null)

const toggleDropdown = () => {
  dropdownVisible.value = !dropdownVisible.value
}

const closeDropdown = () => {
  dropdownVisible.value = false
}

const handleClickOutside = (e: MouseEvent) => {
  if (addWrapperRef.value && !addWrapperRef.value.contains(e.target as Node)) {
    closeDropdown()
  }
}

const addCustom = () => {
  mcpStore.createServer()
  closeDropdown()
}

const addFromTemplate = (template: McpServerForm) => {
  mcpStore.createServer(template)
  closeDropdown()
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped lang="scss">
.mcp-list {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  padding: 16px;
  overflow: hidden;
}

.add-wrapper {
  position: relative;
  margin-bottom: 16px;
}

.add-btn {
  width: 100%;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
  z-index: 20;
  max-height: 320px;
  overflow-y: auto;
  padding: 6px 0;
}

.dropdown-section {
  padding: 6px 12px;
  font-size: 12px;
  color: var(--text-tertiary);
}

.dropdown-item {
  padding: 8px 12px;
  font-size: 13px;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: var(--bg-hover);
  }
}

.list-wrap {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.server-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 6px;

  &:hover {
    background: var(--bg-hover);
  }

  &.active {
    background: var(--accent-color-soft, #e3e9fc);
    color: var(--accent-color);
  }
}

.server-left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.server-icon {
  flex-shrink: 0;
  color: var(--text-secondary);
}

.server-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #9ca3af;
  flex-shrink: 0;

  &.active {
    background: #22c55e;
  }
}

.list-empty {
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  padding: 30px 0;
}

.config-btn {
  width: 100%;
  margin-top: 16px;
}
</style>
