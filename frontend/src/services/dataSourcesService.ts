import api from './api'
import { DataSource } from '@/types'

/**
 * Data Sources API service
 * Handles all data source-related API requests
 */

export const dataSourcesService = {
  /**
   * Fetch all data sources for a competitor
   */
  getByCompetitor: async (competitorId: number): Promise<DataSource[]> => {
    const response = await api.get<DataSource[]>(`/competitors/${competitorId}/sources`)
    return response.data
  },

  /**
   * Create a new data source for a competitor
   */
  create: async (
    competitorId: number,
    data: {
      source_type: string
      url: string
      is_active?: boolean
    }
  ): Promise<DataSource> => {
    const response = await api.post<DataSource>(`/competitors/${competitorId}/sources`, data)
    return response.data
  },

  /**
   * Update an existing data source
   */
  update: async (
    competitorId: number,
    sourceId: number,
    data: {
      source_type?: string
      url?: string
      is_active?: boolean
    }
  ): Promise<DataSource> => {
    const response = await api.put<DataSource>(
      `/competitors/${competitorId}/sources/${sourceId}`,
      data
    )
    return response.data
  },

  /**
   * Delete a data source
   */
  delete: async (competitorId: number, sourceId: number): Promise<void> => {
    await api.delete(`/competitors/${competitorId}/sources/${sourceId}`)
  },
}
