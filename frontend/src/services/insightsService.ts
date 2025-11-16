import api from './api'
import { ProcessedInsight } from '@/types'

/**
 * Insights API service
 * Handles all insights-related API requests
 */

export const insightsService = {
  /**
   * Fetch all insights for a competitor
   */
  getByCompetitor: async (competitorId: number): Promise<ProcessedInsight[]> => {
    const response = await api.get<ProcessedInsight[]>(`/competitors/${competitorId}/insights`)
    return response.data
  },

  /**
   * Fetch a specific insight by ID
   */
  getById: async (insightId: number): Promise<ProcessedInsight> => {
    const response = await api.get<ProcessedInsight>(`/insights/${insightId}`)
    return response.data
  },
}
