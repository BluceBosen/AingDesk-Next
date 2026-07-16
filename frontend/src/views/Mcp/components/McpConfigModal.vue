<template>
  <div v-if="mcpStore.configModalVisible" class="modal-overlay" @click.self="mcpStore.configModalVisible = false">
    <div class="modal-panel">
      <div class="modal-header">
        <h3>编辑 MCP 配置文件</h3>
        <button class="close-btn" @click="mcpStore.configModalVisible = false">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="modal-body">
        <textarea
          v-model="mcpStore.configContent"
          class="textarea"
          rows="18"
          placeholder="{}"
        />
        <p class="form-tip">编辑 MCP 服务器配置的 JSON。保存前请确保格式正确。</p>
      </div>
      <div class="modal-footer">
        <button class="btn-secondary" @click="mcpStore.configModalVisible = false">取消</button>
        <button class="btn-primary" @click="mcpStore.saveConfig">确认</button>
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
  width: 640px;
  max-width: 90vw;
  max-height: 90vh;
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
  display: flex;
  flex-direction: column;
  gap: 10px;
  flex: 1;
  min-height: 0;
}

.textarea {
  width: 100%;
  padding: 12px;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 13px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  line-height: 1.5;
  resize: none;
  flex: 1;
  min-height: 300px;
  outline: none;

  &:focus {
    border-color: var(--accent-color);
  }
}

.form-tip {
  font-size: 12px;
  color: var(--text-tertiary);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid var(--border-color);
}
</style>
