<template>
  <div class="settings-tab-content">
    <div class="settings-section">
      <h3 class="settings-section-title">外观</h3>
      <div class="setting-card">
        <div class="setting-card-row">
          <div class="setting-label">
            <div class="setting-name">主题模式</div>
            <div class="setting-desc">切换浅色或深色主题</div>
          </div>
          <div class="theme-toggle">
            <button
              class="theme-option"
              :class="{ active: globalStore.theme === 'light' }"
              @click="globalStore.setTheme('light')"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="5"/>
                <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
              </svg>
              浅色
            </button>
            <button
              class="theme-option"
              :class="{ active: globalStore.theme === 'dark' }"
              @click="globalStore.setTheme('dark')"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
              </svg>
              深色
            </button>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-section">
      <h3 class="settings-section-title">联网搜索</h3>
      <div class="setting-card">
        <div class="setting-card-row">
          <div class="setting-label">
            <div class="setting-name">默认搜索引擎</div>
            <div class="setting-desc">开启联网搜索时使用的搜索引擎</div>
          </div>
          <div class="custom-select" ref="selectRef">
            <div
              class="custom-select-trigger"
              :class="{ open: selectOpen }"
              @click="selectOpen = !selectOpen"
            >
              <span>{{ currentEngineLabel }}</span>
              <svg class="custom-select-arrow" :class="{ rotate: selectOpen }" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </div>
            <div v-if="selectOpen" class="custom-select-dropdown">
              <div
                v-for="engine in searchEngines"
                :key="engine.value"
                class="custom-select-option"
                :class="{ selected: settingsStore.searchEngine === engine.value }"
                @click="handleSelect(engine.value)"
              >
                {{ engine.label }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="settings-section">
      <h3 class="settings-section-title">数据设置</h3>
      <div class="setting-card">
        <div class="setting-card-row vertical">
          <div class="setting-label">
            <div class="setting-name">数据存储位置</div>
            <div class="setting-desc">更改后将自动迁移数据到新目录</div>
          </div>
          <div class="path-input-row">
            <input
              v-model="settingsStore.dataSavePath"
              class="input path-input"
              placeholder="数据保存路径"
              readonly
            >
            <input
              ref="dirInputRef"
              type="file"
              webkitdirectory
              directory
              class="hidden-input"
              @change="handleDirSelect"
            >
            <button class="btn-secondary" :disabled="settingsStore.dataPathLoading" @click="triggerDirSelect">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/>
              </svg>
              更改
            </button>
          </div>
        </div>

        <div v-if="settingsStore.dataPathChanging" class="migration-panel">
          <div class="migration-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <path d="M12 6v6l4 2"/>
            </svg>
            <span>数据迁移中...</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${settingsStore.dataPathChangeStatus.percent}%` }" />
          </div>
          <div class="migration-info">
            <span>{{ settingsStore.dataPathChangeStatus.message }}</span>
            <span v-if="settingsStore.dataPathChangeStatus.percent > 0">
              {{ settingsStore.dataPathChangeStatus.percent.toFixed(1) }}%
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { toast } from 'vue3-toastify'
import { useGlobalStore } from '@/stores/global'
import { useSettingsStore, type SearchEngine } from '@/stores/settings'
import { settingsApi } from '@/api/settings'

const globalStore = useGlobalStore()
const settingsStore = useSettingsStore()
const dirInputRef = ref<HTMLInputElement | null>(null)
const selectRef = ref<HTMLElement | null>(null)
const selectOpen = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null

const searchEngines: { label: string; value: SearchEngine }[] = [
  { label: '百度', value: 'baidu' },
  { label: '搜狗', value: 'sogou' },
  { label: '360搜索', value: '360' },
]

const currentEngineLabel = computed(() => {
  return searchEngines.find(e => e.value === settingsStore.searchEngine)?.label || '百度'
})

const handleSelect = (value: SearchEngine) => {
  settingsStore.setSearchEngine(value)
  selectOpen.value = false
}

const handleClickOutside = (e: MouseEvent) => {
  if (selectRef.value && !selectRef.value.contains(e.target as Node)) {
    selectOpen.value = false
  }
}

const loadDataSavePath = async () => {
  try {
    settingsStore.dataPathLoading = true
    const res = await settingsApi.getDataSavePath()
    settingsStore.dataSavePath = res.currentPath || ''
    settingsStore.dataPathChangeStatus = res.copyStatus
  } catch (e: any) {
    toast.error(e.message || '获取数据保存路径失败')
  } finally {
    settingsStore.dataPathLoading = false
  }
}

const triggerDirSelect = () => {
  dirInputRef.value?.click()
}

const handleDirSelect = async (e: Event) => {
  const target = e.target as HTMLInputElement
  const files = target.files
  if (!files || files.length === 0) return

  const firstFile = files[0]
  const pathParts = firstFile.webkitRelativePath.split('/')
  const selectedDir = pathParts.length > 1 ? pathParts[0] : firstFile.name

  const userPath = window.prompt('请填写目标目录的完整绝对路径（需为空目录）：', selectedDir)
  if (!userPath) {
    target.value = ''
    return
  }

  try {
    settingsStore.dataPathChanging = true
    const res = await settingsApi.setDataSavePath(userPath)
    if (res.code === 200) {
      toast.success('已开始迁移数据')
      startPolling()
    } else {
      toast.error(res.msg || '设置失败')
      settingsStore.dataPathChanging = false
    }
  } catch (err: any) {
    toast.error(err.message || '设置数据保存路径失败')
    settingsStore.dataPathChanging = false
  } finally {
    target.value = ''
  }
}

const startPolling = () => {
  stopPolling()
  pollTimer = setInterval(async () => {
    try {
      const res = await settingsApi.getDataSavePath()
      settingsStore.dataSavePath = res.currentPath
      settingsStore.dataPathChangeStatus = res.copyStatus
      const status = res.copyStatus.status
      if (status === 2 || status === -1) {
        stopPolling()
        settingsStore.dataPathChanging = false
        if (status === 2) toast.success('数据迁移成功')
        if (status === -1) toast.error(res.copyStatus.error || '数据迁移失败')
      }
    } catch (e) {
      stopPolling()
      settingsStore.dataPathChanging = false
    }
  }, 1500)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(() => {
  loadDataSavePath()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  stopPolling()
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped lang="scss">
.settings-tab-content {
  padding: 0 24px 24px;
  overflow-y: auto;
  flex: 1;
}

.settings-section {
  margin-bottom: 28px;

  &:last-child {
    margin-bottom: 0;
  }
}

.settings-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-tertiary);
  text-transform: uppercase;
  margin-bottom: 12px;
  letter-spacing: 0.5px;
}

.setting-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
}

.setting-card-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  gap: 16px;

  &.vertical {
    flex-direction: column;
    align-items: stretch;
  }
}

.setting-label {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.setting-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.setting-desc {
  font-size: 13px;
  color: var(--text-tertiary);
}

.theme-toggle {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.theme-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;

  &.active {
    border-color: var(--accent-color);
    background: var(--bg-active);
    color: var(--accent-color);
  }

  &:hover:not(.active) {
    border-color: var(--text-tertiary);
  }
}

.custom-select {
  position: relative;
  min-width: 120px;
  flex-shrink: 0;
}

.custom-select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 14px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
  transition: border-color 0.2s;
  user-select: none;

  &:hover,
  &.open {
    border-color: var(--accent-color);
  }
}

.custom-select-arrow {
  flex-shrink: 0;
  transition: transform 0.2s;

  &.rotate {
    transform: rotate(180deg);
  }
}

.custom-select-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 100;
  overflow: hidden;
}

.custom-select-option {
  padding: 8px 14px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid var(--border-color);

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: var(--bg-secondary);
  }

  &.selected {
    color: var(--accent-color);
    font-weight: 500;
    background: var(--bg-active);
  }
}

.path-input-row {
  display: flex;
  gap: 10px;
  align-items: center;
}

.path-input {
  flex: 1;
}

.input {
  width: 100%;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;

  &:focus {
    border-color: var(--accent-color);
  }

  &::placeholder {
    color: var(--text-tertiary);
  }

  &:read-only {
    opacity: 0.8;
  }
}

.hidden-input {
  display: none;
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-primary);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    border-color: var(--accent-color);
    color: var(--accent-color);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.migration-panel {
  padding: 16px 20px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-primary);
}

.migration-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 10px;
}

.progress-bar {
  height: 6px;
  background: var(--bg-secondary);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: var(--accent-color);
  transition: width 0.3s ease;
}

.migration-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: var(--text-tertiary);
}
</style>
