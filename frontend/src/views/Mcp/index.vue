<template>
  <div class="mcp-page">
    <McpServerList />
    <div class="mcp-detail">
      <McpServerForm v-if="mcpStore.formVisible" />
      <div v-else class="empty-detail">
        <div class="empty-icon">🔌</div>
        <div class="empty-title">暂无选中的 MCP 服务器</div>
        <div class="empty-desc">从左侧添加服务器或选择已有服务器进行配置</div>
      </div>
    </div>

    <McpConfigModal />
    <McpToolsModal />
    <McpConfirmModal />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useMcpStore } from '@/stores/mcp'
import McpServerList from './components/McpServerList.vue'
import McpServerForm from './components/McpServerForm.vue'
import McpConfigModal from './components/McpConfigModal.vue'
import McpToolsModal from './components/McpToolsModal.vue'
import McpConfirmModal from './components/McpConfirmModal.vue'

const mcpStore = useMcpStore()

onMounted(() => {
  mcpStore.checkEnv()
  mcpStore.loadServerList()
  mcpStore.loadTemplateList()
})
</script>

<style scoped lang="scss">
.mcp-page {
  display: flex;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

.mcp-detail {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--bg-primary);
}

.empty-detail {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }

  .empty-title {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 6px;
    color: var(--text-primary);
  }

  .empty-desc {
    font-size: 14px;
    color: var(--text-tertiary);
  }
}
</style>
