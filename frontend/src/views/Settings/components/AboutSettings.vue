<template>
  <div class="settings-tab-content">
    <div class="settings-section">
      <h3 class="settings-section-title">软件版本</h3>
      <div class="setting-card">
        <div class="about-row">
          <div class="app-logo">AI</div>
          <div class="app-info">
            <div class="app-name">AiSpace</div>
            <div class="app-version">版本 {{ version }}</div>
          </div>
        </div>
        <div class="about-desc">
          基于 aingdesk_api 的 AiSpace 前端项目。
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { settingsApi } from '@/api/settings'

const version = ref('1.0.0')

onMounted(async () => {
  try {
    const res = await settingsApi.getVersion()
    version.value = res.version || '1.0.0'
  } catch (e) {
    version.value = '1.0.0'
  }
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
  padding: 24px;
}

.about-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.app-logo {
  width: 48px;
  height: 48px;
  background: var(--accent-color);
  color: white;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
}

.app-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.app-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}

.app-version {
  font-size: 13px;
  color: var(--text-tertiary);
}

.about-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}
</style>
