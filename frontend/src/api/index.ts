import { post, get } from './request'

export const indexApi = {
  getVersion: (): Promise<string> => post('/index/get_version'),

  getLanguages: (): Promise<any> => post('/index/get_languages'),

  setLanguage: (language: string): Promise<any> =>
    post('/index/set_language', { language }),

  writeLogs: (logs: string): Promise<any> => post('/index/write_logs', { logs }),
}
