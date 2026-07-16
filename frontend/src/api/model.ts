import { post } from './request'
import type { Supplier, SupplierConfig, SupplierModel } from '@/types'

export const modelApi = {
  getSupplierList: (): Promise<Supplier[]> => post('/model/get_supplier_list'),

  getSupplierConfig: (supplierName: string): Promise<SupplierConfig> =>
    post('/model/get_supplier_config', { supplierName }),

  getModelsList: (supplierName: string): Promise<SupplierModel[]> =>
    post('/model/get_models_list', { supplierName }),

  addSupplier: (data: {
    supplierName: string
    supplierTitle: string
    baseUrl?: string
    apiKey?: string
  }): Promise<any> => post('/model/add_supplier', data),

  removeSupplier: (supplierName: string): Promise<any> =>
    post('/model/remove_supplier', { supplierName }),

  setSupplierConfig: (data: {
    supplierName: string
    baseUrl?: string
    apiKey?: string
  }): Promise<any> => post('/model/set_supplier_config', data),

  checkSupplierConfig: (data: {
    supplierName: string
    baseUrl?: string
    apiKey?: string
  }): Promise<any> => post('/model/check_supplier_config', data),

  setSupplierStatus: (data: { supplierName: string; status: string }): Promise<any> =>
    post('/model/set_supplier_status', data),

  addModels: (data: {
    supplierName: string
    modelName: string
    title: string
    capability?: any
  }): Promise<any> => post('/model/add_models', data),

  removeModels: (data: { supplierName: string; modelName: string }): Promise<any> =>
    post('/model/remove_models', data),

  modifyModel: (data: {
    supplierName: string
    modelName: string
    title: string
    capability?: any
  }): Promise<any> => post('/model/modify_model', data),

  setModelStatus: (data: { supplierName: string; modelName: string; status: string }): Promise<any> =>
    post('/model/set_model_status', data),

  getOnlineModels: (supplierName: string): Promise<any> =>
    post('/model/get_online_models', { supplierName }),

  syncTemplates: (): Promise<any> => post('/model/sync_templates'),
}
