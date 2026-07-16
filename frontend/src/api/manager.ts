import { post } from './request'
import type {
  ModelManager,
  LocalModel,
  InstallProgress,
  DiskInfo,
} from '@/types'

export const managerApi = {
  /** 获取模型管理器信息 */
  getModelManager: (): Promise<ModelManager> =>
    post('/manager/get_model_manager'),

  /** 安装模型 */
  installModel: (data: { model: string; parameters?: string }): Promise<any> =>
    post('/manager/install_model', data),

  /** 获取模型安装进度 */
  getModelInstallProgress: (data: {
    model: string
    parameters?: string
  }): Promise<InstallProgress> => post('/manager/get_model_install_progress', data),

  /** 删除模型 */
  removeModel: (data: { model: string; parameters?: string }): Promise<any> =>
    post('/manager/remove_model', data),

  /** 安装模型管理器 */
  installModelManager: (data: {
    manager_name: string
    models_path?: string
  }): Promise<any> => post('/manager/install_model_manager', data),

  /** 获取模型管理器安装进度 */
  getModelManagerInstallProgress: (data: {
    manager_name: string
  }): Promise<InstallProgress> =>
    post('/manager/get_model_manager_install_progress', data),

  /** 获取磁盘信息 */
  getDiskList: (): Promise<DiskInfo[]> => post('/manager/get_disk_list'),

  /** 设置 Ollama 连接地址 */
  setOllamaHost: (ollama_host: string): Promise<any> =>
    post('/manager/set_ollama_host', { ollama_host }),

  /** 重新连接模型下载任务 */
  reconnectModelDownload: (): Promise<any> =>
    post('/manager/reconnect_model_download'),
}
