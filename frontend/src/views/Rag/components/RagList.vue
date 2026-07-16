<template>
  <div class="rag-list">
    <button class="btn-primary create-btn" @click="$emit('create')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="12" y1="5" x2="12" y2="19"/>
        <line x1="5" y1="12" x2="19" y2="12"/>
      </svg>
      新建知识库
    </button>

    <div class="list-wrap">
      <div
        v-for="item in list.filter((i) => !i.isPreset)"
        :key="item.ragName"
        class="rag-item"
        :class="{ active: active === item.ragName }"
        @click="$emit('select', item.ragName)"
      >
        <div class="rag-info">
          <span class="rag-name">{{ item.ragName }}</span>
        </div>
        <div class="more-btn" @click.stop>
          <div class="more-menu" tabindex="0" @click="toggleDropdown(item.ragName)">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="5" r="2"/>
              <circle cx="12" cy="12" r="2"/>
              <circle cx="12" cy="19" r="2"/>
            </svg>
            <div class="dropdown" :class="{ visible: activeDropdown === item.ragName }">
              <div class="dropdown-item danger" @click="$emit('delete', item.ragName)">删除</div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!list.filter((i) => !i.isPreset).length" class="list-empty">
        暂无知识库
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { RagItem } from '@/types'

defineProps<{
  list: RagItem[]
  active: string | null
}>()

defineEmits<{
  (e: 'select', ragName: string): void
  (e: 'create'): void
  (e: 'edit', item: RagItem): void
  (e: 'delete', ragName: string): void
}>()

const activeDropdown = ref<string | null>(null)

const toggleDropdown = (ragName: string) => {
  activeDropdown.value = activeDropdown.value === ragName ? null : ragName
}

const closeDropdown = () => {
  activeDropdown.value = null
}

onMounted(() => {
  document.addEventListener('click', closeDropdown)
})

onUnmounted(() => {
  document.removeEventListener('click', closeDropdown)
})
</script>

<style scoped lang="scss">
.rag-list {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border-color);
  padding: 10px;
  overflow: hidden;
}

.create-btn {
  width: 100%;
  margin-bottom: 16px;
}

.list-wrap {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.rag-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
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

.rag-info {
  display: flex;
  flex-direction: column;
  min-width: 0;
  flex: 1;
}

.rag-name {
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.more-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);

  &:hover {
    background: var(--bg-hover);
  }
}

.more-menu {
  position: relative;
  outline: none;
}

.dropdown {
  display: none;
  position: absolute;
  right: 0;
  top: 24px;
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
  color: var(--text-danger, #ef4444);
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background: var(--bg-hover);
  }
}

.list-empty {
  text-align: center;
  color: var(--text-tertiary);
  font-size: 13px;
  padding: 30px 0;
}

.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
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
