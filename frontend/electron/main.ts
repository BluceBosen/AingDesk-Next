import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
let isQuitting = false

const createWindow = () => {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 900,
    minHeight: 600,
    title: 'AiSpace',
    frame: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: false,
    },
  })

  if (process.env.VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(process.env.VITE_DEV_SERVER_URL)
  } else {
    mainWindow.loadFile(path.join(__dirname, '../index.html'))
  }

  // 监听窗口最大化状态变化，通知渲染进程
  mainWindow.on('maximize', () => {
    mainWindow.webContents.send('window-state-changed', 'maximized')
  })
  mainWindow.on('unmaximize', () => {
    mainWindow.webContents.send('window-state-changed', 'restored')
  })
}

app.whenReady().then(() => {
  createWindow()
})

app.on('activate', () => {
  if (isQuitting) return
  if (BrowserWindow.getAllWindows().length === 0) createWindow()
})

app.on('window-all-closed', () => {
  isQuitting = true
  if (process.platform !== 'darwin') app.quit()
})

ipcMain.handle('get-app-version', () => {
  return app.getVersion()
})

// 窗口控制 IPC
ipcMain.on('minimize-window', () => {
  const win = BrowserWindow.getFocusedWindow()
  if (win) win.minimize()
})

ipcMain.on('maximize-window', () => {
  const win = BrowserWindow.getFocusedWindow()
  if (win) win.maximize()
})

ipcMain.on('unmaximize-window', () => {
  const win = BrowserWindow.getFocusedWindow()
  if (win) win.unmaximize()
})

ipcMain.on('close-window', () => {
  const win = BrowserWindow.getFocusedWindow()
  if (win) win.close()
})

ipcMain.handle('is-window-maximized', () => {
  const win = BrowserWindow.getFocusedWindow()
  return win ? win.isMaximized() : false
})

ipcMain.handle('open-file-dialog', async (_event, options?: { multiSelections?: boolean; filters?: any[] }) => {
  const win = BrowserWindow.getFocusedWindow()
  if (!win) return []
  const result = await dialog.showOpenDialog(win, {
    properties: ['openFile', options?.multiSelections ? 'multiSelections' : ''].filter(Boolean) as any,
    filters: options?.filters || [
      { name: '文档和图片', extensions: ['docx', 'doc', 'xlsx', 'xls', 'csv', 'pptx', 'ppt', 'pdf', 'html', 'htm', 'md', 'markdown', 'txt', 'log', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'] },
      { name: '所有文件', extensions: ['*'] },
    ],
  })
  if (result.canceled) return []
  return result.filePaths.map(filePath => ({ name: path.basename(filePath), path: filePath }))
})
