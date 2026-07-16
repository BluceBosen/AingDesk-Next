<template>
  <div v-if="mcpStore.deleteConfirmVisible" class="modal-overlay" @click.self="mcpStore.deleteConfirmVisible = false">
    <div class="modal-panel">
      <div class="modal-header">
        <h3>删除 MCP 服务器</h3>
        <button class="close-btn" @click="mcpStore.deleteConfirmVisible = false">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="modal-body">
        <p class="confirm-text">
          确定删除 MCP 服务器「<strong>{{ mcpStore.currentName }}</strong>」吗？删除后不可恢复。
        </p>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="mcpStore.deleteConfirmVisible = false">取消</button>
        <button class="btn-primary danger" @click="mcpStore.removeServer">删除</button>
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
  width: 400px;
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
}

.confirm-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;

  strong {
    color: var(--text-primary);
  }
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-color);
}

.btn-primary.danger {
  background: #ef4444;

  &:hover {
    background: #dc2626;
  }
}
</style>
