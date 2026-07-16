import { post, get } from './request'

export interface DataSavePathResponse {
  currentPath: string
  oldPath: string
  isMove: boolean
  isMoveSuccess: boolean
  isClearOldPath: boolean
  dataSize: number
  copyStatus: {
    status: number
    speed: number
    total: number
    current: number
    percent: number
    startTime: number
    endTime: number
    fileTotal: number
    fileCurrent: number
    message: string
    error: string
  }
}

export const settingsApi = {
  /** 获取数据保存路径 */
  getDataSavePath: (): Promise<DataSavePathResponse> => get('/index/get_data_save_path'),

  /** 设置数据保存路径 */
  setDataSavePath: (newPath: string): Promise<any> =>
    post('/index/set_data_save_path', { newPath }),

  /** 选择文件夹（web 端使用浏览器目录选择器后回传路径） */
  selectFolder: (): Promise<{ folder: string }> => get('/os/select_folder'),

  /** 获取版本信息 */
  getVersion: (): Promise<{ version: string }> => get('/index/get_version'),
}
