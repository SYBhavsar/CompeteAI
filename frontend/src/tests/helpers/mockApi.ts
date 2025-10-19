import MockAdapter from 'axios-mock-adapter'
import api from '@/services/api'

// Create a mock instance for the API client
export const mockApi = new MockAdapter(api, { delayResponse: 0 })

// Helper to reset mocks between tests
export const resetMockApi = () => {
  mockApi.reset()
}

// Helper to restore original axios instance
export const restoreMockApi = () => {
  mockApi.restore()
}
