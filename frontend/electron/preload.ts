import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),

  // 窗口控制
  minimizeWindow: () => ipcRenderer.send('minimize-window'),
  maximizeWindow: () => ipcRenderer.send('maximize-window'),
  unmaximizeWindow: () => ipcRenderer.send('unmaximize-window'),
  closeWindow: () => ipcRenderer.send('close-window'),
  isWindowMaximized: () => ipcRenderer.invoke('is-window-maximized'),

  // 监听窗口状态变化
  onWindowStateChange: (callback: (state: 'maximized' | 'restored') => void) => {
    ipcRenderer.on('window-state-changed', (_event, state) => callback(state))
  },

  // 文件选择
  openFileDialog: (options?: { multiSelections?: boolean; filters?: any[] }) =>
    ipcRenderer.invoke('open-file-dialog', options),
})
