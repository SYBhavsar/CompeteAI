import api from './api'
import { Competitor } from '@/types'

/**
 * Competitors API service
 * Handles all competitor-related API requests
 */

export const competitorsService = {
  /**
   * Fetch all competitors for the authenticated user
   */
  getAll: async (): Promise<Competitor[]> => {
    const response = await api.get<Competitor[]>('/competitors')
    return response.data
  },

  /**
   * Fetch a single competitor by ID
   */
  getById: async (id: number): Promise<Competitor> => {
    const response = await api.get<Competitor>(`/competitors/${id}`)
    return response.data
  },

  /**
   * Create a new competitor
   */
  create: async (data: {
    name: string
    domain?: string
    industry?: string
  }): Promise<Competitor> => {
    const response = await api.post<Competitor>('/competitors', data)
    return response.data
  },

  /**
   * Update an existing competitor
   */
  update: async (
    id: number,
    data: {
      name?: string
      domain?: string
      industry?: string
    }
  ): Promise<Competitor> => {
    const response = await api.put<Competitor>(`/competitors/${id}`, data)
    return response.data
  },

  /**
   * Delete a competitor
   */
  delete: async (id: number): Promise<void> => {
    await api.delete(`/competitors/${id}`)
  },
}
