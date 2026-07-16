<template>
  <div class="app-container" :data-theme="theme">
    <RouterView />
    <SettingsModal />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useGlobalStore } from './stores/global'
import SettingsModal from '@/views/Settings/SettingsModal.vue'

const globalStore = useGlobalStore()
const theme = computed(() => globalStore.theme)
</script>

<style scoped lang="scss">
.app-container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: var(--bg-primary);
  color: var(--text-primary);
}
</style>
