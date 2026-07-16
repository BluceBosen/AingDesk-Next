import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useGlobalStore = defineStore('global', () => {
  const theme = ref<'light' | 'dark'>('light')
  const sidebarCollapsed = ref(false)
  const currentRoute = ref('Chat')
  const apiBaseUrl = ref(import.meta.env.VITE_API_BASE_URL || 'http://localhost:7071')

  const isDark = computed(() => theme.value === 'dark')

  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setTheme = (val: 'light' | 'dark') => {
    theme.value = val
    document.documentElement.setAttribute('data-theme', val)
  }

  return {
    theme,
    sidebarCollapsed,
    currentRoute,
    apiBaseUrl,
    isDark,
    toggleTheme,
    toggleSidebar,
    setTheme,
  }
})
