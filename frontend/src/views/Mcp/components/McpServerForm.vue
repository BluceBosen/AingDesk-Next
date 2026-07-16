<template>
  <div class="server-form">
    <div class="form-header">
      <div class="header-left">
        <h3 class="server-title">{{ mcpStore.form.name || '新服务器' }}</h3>
        <button
          v-if="mcpStore.editMode"
          class="icon-btn danger"
          title="删除服务器"
          @click="mcpStore.confirmDeleteServer(mcpStore.form.name)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/>
          </svg>
        </button>
      </div>
      <div class="header-right">
        <button
          v-if="mcpStore.editMode"
          class="icon-btn"
          title="管理工具"
          @click="mcpStore.openTools(mcpStore.form.name)"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/>
          </svg>
        </button>
        <label v-if="mcpStore.editMode" class="active-switch" title="是否启用">
          <input
            type="checkbox"
            :checked="mcpStore.form.isActive"
            @change="mcpStore.toggleServerActive(($event.target as HTMLInputElement).checked)"
          />
          <span class="switch-slider"></span>
        </label>
      </div>
    </div>

    <div class="form-body">
      <div class="form-group">
        <label>名称</label>
        <input
          v-model="mcpStore.form.name"
          class="input"
          placeholder="如：filesystem"
          :disabled="mcpStore.editMode"
        />
      </div>

      <div class="form-group">
        <label>描述</label>
        <input
          v-model="mcpStore.form.description"
          class="input"
          placeholder="文件系统访问"
        />
      </div>

      <div class="form-group inline">
        <label>类型</label>
        <div class="radio-group">
          <label class="radio-label">
            <input v-model="mcpStore.form.type" type="radio" value="stdio" />
            <span>Stdio</span>
          </label>
          <label class="radio-label">
            <input v-model="mcpStore.form.type" type="radio" value="sse" />
            <span>SSE</span>
          </label>
        </div>
      </div>

      <template v-if="mcpStore.form.type === 'sse'">
        <div class="form-group">
          <label>服务器地址</label>
          <input
            v-model="mcpStore.form.baseUrl"
            class="input"
            placeholder="http://localhost:3000/sse"
          />
        </div>
      </template>

      <template v-else>
        <div class="form-group inline">
          <label>程序类型</label>
          <div class="radio-group">
            <label class="radio-label">
              <input
                v-model="mcpStore.commandType"
                type="radio"
                value="npx"
                @change="mcpStore.onChangeCommandType('npx')"
              />
              <span>NPX</span>
            </label>
            <label class="radio-label">
              <input
                v-model="mcpStore.commandType"
                type="radio"
                value="custom"
                @change="mcpStore.onChangeCommandType('custom')"
              />
              <span>自定义</span>
            </label>
          </div>
        </div>

        <div v-if="mcpStore.commandType === 'npx' && mcpStore.envStatus.node_npx === 0" class="env-tip">
          当前未安装 Node.js 运行环境，
          <button class="link-btn" :disabled="mcpStore.envInstalling" @click="mcpStore.installEnv('npx')">
            立即安装
          </button>
        </div>

        <div v-if="mcpStore.commandType === 'custom'" class="form-group">
          <label>命令</label>
          <input
            v-model="mcpStore.form.command"
            class="input"
            placeholder="可执行命令全路径"
          />
        </div>

        <div class="form-group">
          <label>参数</label>
          <textarea
            v-model="mcpStore.form.args"
            class="textarea"
            rows="4"
            placeholder="填写多个参数一行一个，如：\n-y\n@modelcontextprotocol/server-filesystem"
          />
        </div>
      </template>

      <div class="form-group">
        <label>环境变量</label>
        <textarea
          v-model="mcpStore.form.env"
          class="textarea"
          rows="4"
          placeholder="填写多个环境变量一行一个，如：\nBRAVE_API_KEY=xxx\nGITHUB_TOKEN=xxx"
        />
      </div>
    </div>

    <div class="form-footer">
      <button class="btn-secondary" @click="mcpStore.resetForm">取消</button>
      <button class="btn-primary" @click="mcpStore.saveServer">
        {{ mcpStore.editMode ? '保存' : '添加' }}
      </button>
    </div>

    <!-- 环境安装进度提示 -->
    <div v-if="mcpStore.envInstalling" class="install-modal">
      <div class="install-panel">
        <span class="spinner"></span>
        <span class="install-text">
          正在安装 {{ mcpStore.envInstallType === 'npx' ? 'Node.js' : 'Python' }} 运行环境，请稍候...
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useMcpStore } from '@/stores/mcp'

const mcpStore = useMcpStore()
</script>

<style scoped lang="scss">
.server-form {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 24px;
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.server-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
  background: var(--bg-primary);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  &.danger:hover {
    color: #ef4444;
    border-color: #ef4444;
  }
}

.active-switch {
  position: relative;
  width: 44px;
  height: 24px;
  cursor: pointer;

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

.form-body {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
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

  &.inline {
    flex-direction: row;
    align-items: center;
    gap: 16px;

    label {
      margin-bottom: 0;
    }
  }
}

.radio-group {
  display: flex;
  gap: 16px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--text-primary);
  cursor: pointer;

  input {
    cursor: pointer;
  }
}

.env-tip {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.link-btn {
  background: transparent;
  border: none;
  color: var(--accent-color);
  font-size: 13px;
  cursor: pointer;
  padding: 0;

  &:hover {
    text-decoration: underline;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
  margin-top: 20px;
}

.install-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
}

.install-panel {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 28px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  color: var(--text-primary);
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
</style>
