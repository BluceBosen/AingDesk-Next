import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export type SearchEngine = 'baidu' | 'sogou' | '360'

const SEARCH_ENGINE_KEY = 'aingspace_search_engine'

export const useSettingsStore = defineStore('settings', () => {
  // 弹窗显示状态
  const showModal = ref(false)
  const currentTab = ref('general')

  // 搜索引擎偏好，默认百度，与 xly-agent-space-electron 保持一致
  const searchEngine = ref<SearchEngine>((localStorage.getItem(SEARCH_ENGINE_KEY) as SearchEngine) || 'baidu')

  // 数据保存路径
  const dataSavePath = ref('')
  const dataPathLoading = ref(false)
  const dataPathChanging = ref(false)
  const dataPathChangeStatus = ref({
    status: 0, // 0:未开始,1:正在复制,2:复制完成,-1:复制失败
    speed: 0,
    total: 0,
    current: 0,
    percent: 0,
    startTime: 0,
    endTime: 0,
    fileTotal: 0,
    fileCurrent: 0,
    message: '',
    error: '',
  })

  const isSearchEngine = computed(() => (engine: SearchEngine) => searchEngine.value === engine)

  const setSearchEngine = (engine: SearchEngine) => {
    searchEngine.value = engine
    localStorage.setItem(SEARCH_ENGINE_KEY, engine)
  }

  const openModal = (tab = 'general') => {
    currentTab.value = tab
    showModal.value = true
  }

  const closeModal = () => {
    showModal.value = false
  }

  return {
    showModal,
    currentTab,
    searchEngine,
    dataSavePath,
    dataPathLoading,
    dataPathChanging,
    dataPathChangeStatus,
    isSearchEngine,
    setSearchEngine,
    openModal,
    closeModal,
  }
})
