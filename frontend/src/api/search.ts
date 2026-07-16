import { post, get } from './request'
import type { SearchResult } from '@/types'

export const searchApi = {
  search: (query: string, searchProvider?: string): Promise<SearchResult[]> =>
    post('/search/search', { query, searchProvider }),

  getProviders: (): Promise<string[]> => get('/search/search_providers'),
}
