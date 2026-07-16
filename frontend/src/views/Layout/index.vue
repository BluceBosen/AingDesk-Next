<template>
  <div class="layout">
    <!-- Custom Title Bar -->
    <div class="title-bar">
      <div class="title-bar-drag">
        <div class="title-bar-brand">
          <div class="logo-icon-small">AI</div>
          <span class="brand-text">AiSpace</span>
        </div>
      </div>
      <div class="window-controls">
        <button class="window-btn theme-toggle-btn" @click="globalStore.toggleTheme">
          <svg v-if="!globalStore.isDark" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="5"/>
            <path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/>
          </svg>
          <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
          </svg>
        </button>
        <button class="window-btn" @click="minimizeWindow">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <rect x="1" y="5.5" width="10" height="1" fill="currentColor"/>
          </svg>
        </button>
        <button class="window-btn" @click="toggleMaximize">
          <svg v-if="!isMaximized" width="12" height="12" viewBox="0 0 12 12" fill="none">
            <rect x="1" y="1" width="10" height="10" stroke="currentColor" stroke-width="1"/>
          </svg>
          <svg v-else width="12" height="12" viewBox="0 0 12 12" fill="none">
            <rect x="2.5" y="2.5" width="7" height="7" stroke="currentColor" stroke-width="1"/>
            <path d="M3.5 2.5V1.5H9.5V7.5H8.5" stroke="currentColor" stroke-width="1"/>
          </svg>
        </button>
        <button class="window-btn close-btn" @click="closeWindow">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M2 2L10 10M10 2L2 10" stroke="currentColor" stroke-width="1.2"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Body -->
    <div class="layout-body">
      <!-- Sidebar -->
      <aside class="sidebar" :class="{ collapsed: globalStore.sidebarCollapsed }">
        <nav class="sidebar-nav">
          <router-link
            v-for="item in menuItems"
            :key="item.path"
            :to="item.path"
            class="nav-item"
            :class="{ active: route.path === item.path }"
            @click="globalStore.currentRoute = item.name"
          >
            <component :is="item.icon" class="nav-icon" />
            <span v-show="!globalStore.sidebarCollapsed" class="nav-text">{{ item.name }}</span>
            <span v-if="globalStore.sidebarCollapsed" class="nav-tooltip">{{ item.name }}</span>
          </router-link>
        </nav>

        <div class="sidebar-footer">
          <button class="nav-item toggle-btn" @click="globalStore.toggleSidebar">
            <component :is="globalStore.sidebarCollapsed ? ToggleIcon : ToggleIconExpanded" class="nav-icon" />
            <span v-show="!globalStore.sidebarCollapsed" class="nav-text">{{ globalStore.sidebarCollapsed ? '展开' : '收起' }}</span>
            <span v-if="globalStore.sidebarCollapsed" class="nav-tooltip">{{ globalStore.sidebarCollapsed ? '展开菜单' : '收起菜单' }}</span>
          </button>
          <button
            class="nav-item footer-settings-item"
            @click="settingsStore.openModal()"
          >
            <component :is="SettingsIcon" class="nav-icon" />
            <span v-show="!globalStore.sidebarCollapsed" class="nav-text">设置</span>
            <span v-if="globalStore.sidebarCollapsed" class="nav-tooltip">设置</span>
          </button>
        </div>
      </aside>

      <!-- Main Content -->
      <main class="main-content">
        <div class="page-content">
          <RouterView />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, h, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useGlobalStore } from '@/stores/global'
import { useSettingsStore } from '@/stores/settings'

const route = useRoute()
const globalStore = useGlobalStore()
const settingsStore = useSettingsStore()
const isMaximized = ref(false)

const ChatIcon = () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
  h('path', { d: 'M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z' })
])
const ModelIcon = () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
  h('rect', { x: '2', y: '3', width: '20', height: '14', rx: '2', ry: '2' }),
  h('line', { x1: '8', y1: '21', x2: '16', y2: '21' }),
  h('line', { x1: '12', y1: '17', x2: '12', y2: '21' })
])
const KnowledgeIcon = () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
  h('path', { d: 'M4 19.5A2.5 2.5 0 016.5 17H20' }),
  h('path', { d: 'M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z' })
])
const AgentIcon = () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
  h('path', { d: 'M12 2a3 3 0 013 3v1h-6V5a3 3 0 013-3z' }),
  h('path', { d: 'M19 13v-2a7 7 0 10-14 0v2' }),
  h('path', { d: 'M12 11v10' }),
  h('path', { d: 'M8 17h8' })
])
const McpIcon = () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
  h('rect', { x: '2', y: '2', width: '9', height: '9', rx: '1' }),
  h('rect', { x: '13', y: '2', width: '9', height: '9', rx: '1' }),
  h('rect', { x: '2', y: '13', width: '9', height: '9', rx: '1' }),
  h('rect', { x: '13', y: '13', width: '9', height: '9', rx: '1' })
])
const SettingsIcon = () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2 }, [
  h('circle', { cx: '12', cy: '12', r: '3' }),
  h('path', { d: 'M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-2 2 2 2 0 01-2-2v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83 0 2 2 0 010-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 01-2-2 2 2 0 012-2h.09A1.65 1.65 0 004.68 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.83 2 2 0 012.83 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 012-2 2 2 0 012 2v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 0 2 2 0 010 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 012 2 2 2 0 01-2 2h-.09a1.65 1.65 0 00-1.51 1z' })
])

const ToggleIcon = () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('rect', { x: '3', y: '3', width: '18', height: '18', rx: '2', ry: '2' }),
  h('line', { x1: '9', y1: '3', x2: '9', y2: '21' }),
  h('path', { d: 'M13 8l4 4-4 4' })
])

const ToggleIconExpanded = () => h('svg', { width: 20, height: 20, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': 2, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }, [
  h('rect', { x: '3', y: '3', width: '18', height: '18', rx: '2', ry: '2' }),
  h('line', { x1: '15', y1: '3', x2: '15', y2: '21' }),
  h('path', { d: 'M11 8l-4 4 4 4' })
])

const menuItems = [
  { path: '/chat', name: '对话', icon: ChatIcon },
  { path: '/agent', name: '智能体', icon: AgentIcon },
  { path: '/rag', name: '知识库', icon: KnowledgeIcon },
  { path: '/models', name: '模型', icon: ModelIcon },
  { path: '/mcp', name: 'MCP', icon: McpIcon },
]

const minimizeWindow = () => {
  window.electronAPI?.minimizeWindow()
}

const toggleMaximize = () => {
  if (isMaximized.value) {
    window.electronAPI?.unmaximizeWindow()
  } else {
    window.electronAPI?.maximizeWindow()
  }
}

const closeWindow = () => {
  window.electronAPI?.closeWindow()
}

onMounted(() => {
  window.electronAPI?.isWindowMaximized().then((maximized) => {
    isMaximized.value = maximized
  })
  window.electronAPI?.onWindowStateChange((state) => {
    isMaximized.value = state === 'maximized'
  })
})
</script>

<style scoped lang="scss">
.layout {
  display: flex;
  flex-direction: column;
  width: 100%;
  height: 100%;
}

/* Title Bar */
.title-bar {
  height: 52px;
  background: var(--bg-sidebar);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
  -webkit-app-region: drag;
  user-select: none;
}

.title-bar-drag {
  display: flex;
  align-items: center;
  flex: 1;
  height: 100%;
  padding-left: 16px;
}

.title-bar-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}

.logo-icon-small {
  width: 22px;
  height: 22px;
  background: var(--accent-color);
  color: white;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
}

.brand-text {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.window-controls {
  display: flex;
  align-items: center;
  height: 100%;
  -webkit-app-region: no-drag;
}

.window-btn {
  width: 46px;
  height: 100%;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  &.close-btn:hover {
    background: #e81123;
    color: white;
  }
}

/* Layout Body */
.layout-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.sidebar {
  width: 150px;
  height: 100%;
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  flex-shrink: 0;
  overflow: hidden;

  &.collapsed {
    width: 64px;
    overflow: visible;

    .nav-item {
      padding: 12px;
      justify-content: center;
    }

    .sidebar-footer {
      padding: 16px 12px;
      justify-content: center;
    }

    .sidebar-nav {
      overflow: visible;
    }
  }
}

.sidebar-nav {
  flex: 1;
  padding: 12px 9px 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s;
  white-space: nowrap;
  position: relative;

  &:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  &.active {
    background: var(--bg-active);
    color: var(--accent-color);
  }
}

.nav-icon {
  flex-shrink: 0;
}

/* Tooltip */
.nav-tooltip {
  position: absolute;
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  background: var(--bg-primary);
  color: var(--text-primary);
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 1px solid var(--border-color);
  transition: opacity 0.2s ease, transform 0.2s ease;
  z-index: 100;

  &::before {
    content: '';
    position: absolute;
    right: 100%;
    top: 50%;
    transform: translateY(-50%);
    border: 6px solid transparent;
    border-right-color: var(--bg-primary);
  }

  &::after {
    position: absolute;
    right: calc(100% - 1px);
    top: 50%;
    transform: translateY(-50%);
    border: 6px solid transparent;
    border-right-color: var(--border-color);
  }
}

.nav-item:hover .nav-tooltip,
.toggle-btn:hover .nav-tooltip {
  opacity: 1;
  transform: translateY(-50%) translateX(4px);
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 4px;
  padding: 12px;
}

.sidebar.collapsed .sidebar-footer {
  align-items: center;
}

.footer-settings-item {
  width: 100%;
  justify-content: flex-start;

  &.active {
    background: var(--bg-active);
    color: var(--accent-color);
  }
}

.sidebar.collapsed .footer-settings-item {
  justify-content: center;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-primary);
}

.page-content {
  flex: 1;
  overflow: auto;
}
</style>
