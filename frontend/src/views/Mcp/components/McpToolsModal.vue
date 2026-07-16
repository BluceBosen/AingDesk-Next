<template>
  <div v-if="mcpStore.toolsModalVisible" class="modal-overlay" @click.self="mcpStore.toolsModalVisible = false">
    <div class="modal-panel">
      <div class="modal-header">
        <h3>管理工具启用状态 - {{ mcpStore.currentName }}</h3>
        <button class="close-btn" @click="mcpStore.toolsModalVisible = false">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="modal-body">
        <div v-if="mcpStore.toolsLoading" class="loading-state">
          <span class="spinner"></span>
          <span>正在获取MCP工具列表...</span>
        </div>
        <div v-else-if="!mcpStore.toolsList.length" class="empty-state">
          <div class="empty-icon">🛠️</div>
          <div class="empty-title">未获取到MCP工具</div>
          <div class="empty-desc">请检查服务器配置是否正确，或服务器是否可正常启动</div>
        </div>
        <div v-else class="tool-list">
          <div v-for="tool in mcpStore.toolsList" :key="tool.name" class="tool-item">
            <div class="tool-info">
              <div class="tool-name">{{ tool.name }}</div>
              <div class="tool-desc">{{ tool.description || '暂无描述' }}</div>
            </div>
            <label class="active-switch" :title="tool.is_active ? '已启用' : '已禁用'">
              <input
                type="checkbox"
                :checked="tool.is_active"
                @change="mcpStore.toggleTool(tool.name, !tool.is_active)"
              />
              <span class="switch-slider"></span>
            </label>
          </div>
        </div>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="mcpStore.toolsModalVisible = false">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMcpStore } from '@/stores/mcp'

const mcpStore = useMcpStore()
</script>

<style scoped lang="scss">
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
  width: 520px;
  max-width: 90vw;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);

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
  flex: 1;
  overflow-y: auto;
  min-height: 0;
}

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 40px 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border-color);
  border-top-color: var(--accent-color);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
  color: var(--text-secondary);

  .empty-icon {
    font-size: 40px;
    margin-bottom: 12px;
  }

  .empty-title {
    font-size: 15px;
    font-weight: 500;
    margin-bottom: 4px;
    color: var(--text-primary);
  }

  .empty-desc {
    font-size: 13px;
    color: var(--text-tertiary);
    text-align: center;
    padding: 0 20px;
  }
}

.tool-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tool-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
}

.tool-info {
  min-width: 0;
  flex: 1;
}

.tool-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 2px;
}

.tool-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.active-switch {
  position: relative;
  width: 44px;
  height: 24px;
  cursor: pointer;
  flex-shrink: 0;

  input {
    opacity: 0;
    width: 0;
    height: 0;
  }
}

.switch-slider {
  position: absolute;
  inset: 0;
  background: var(--border-color);
  border-radius: 24px;
  transition: 0.2s;

  &::before {
    content: '';
    position: absolute;
    width: 18px;
    height: 18px;
    left: 3px;
    top: 3px;
    background: white;
    border-radius: 50%;
    transition: 0.2s;
  }
}

.active-switch input:checked + .switch-slider {
  background: #22c55e;
}

.active-switch input:checked + .switch-slider::before {
  transform: translateX(20px);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-color);
}
</style>
