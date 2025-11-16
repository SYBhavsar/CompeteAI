import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import InsightsPage from '../page'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      competitors: competitorsReducer,
    },
    preloadedState: {
      auth: {
        user: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        token: 'test-token',
        isAuthenticated: true,
        loading: false,
        error: null,
      },
      competitors: {
        competitors: [],
        selectedCompetitor: null,
        dataSources: [],
        insights: [],
        loading: false,
        error: null,
      },
      ...initialState,
    },
  })
}

describe('Insights Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
  })

  it('should render insights page', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onGet(/\/competitors\/\d+\/insights/).reply(200, [])

    render(
      <Provider store={store}>
        <InsightsPage />
      </Provider>
    )

    expect(screen.getByRole('heading', { name: /insights/i, level: 1 })).toBeInTheDocument()
  })

  it('should display list of insights', async () => {
    const mockCompetitors = [
      {
        id: 1,
        name: 'Competitor 1',
        domain: 'competitor1.com',
        industry: 'Tech',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const mockInsights = [
      {
        id: 1,
        raw_content_id: 1,
        summary: 'Test insight summary 1',
        key_points: ['Point 1', 'Point 2'],
        sentiment: 'positive',
        insights: 'Detailed insights',
        quality_score: 0.85,
        created_at: '2024-01-15T10:30:00Z',
        updated_at: '2024-01-15T10:30:00Z',
      },
      {
        id: 2,
        raw_content_id: 2,
        summary: 'Test insight summary 2',
        key_points: ['Point A', 'Point B'],
        sentiment: 'negative',
        insights: 'More insights',
        quality_score: 0.72,
        created_at: '2024-01-14T09:20:00Z',
        updated_at: '2024-01-14T09:20:00Z',
      },
    ]

    const store = createTestStore({
      competitors: {
        competitors: mockCompetitors,
        selectedCompetitor: null,
        dataSources: [],
        insights: [],
        loading: false,
        error: null,
      },
    })

    mockApi.onGet('/competitors').reply(200, mockCompetitors)
    mockApi.onGet('/competitors/1/insights').reply(200, mockInsights)

    const { container } = render(
      <Provider store={store}>
        <InsightsPage />
      </Provider>
    )

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByText(/loading insights/i)).not.toBeInTheDocument()
    }, { timeout: 3000 })

    // Debug: log what's on screen
    // screen.debug()

    await waitFor(() => {
      expect(screen.getByText(/test insight summary 1/i)).toBeInTheDocument()
    }, { timeout: 3000 })

    expect(screen.getByText(/test insight summary 2/i)).toBeInTheDocument()
  })

  it('should have competitor filter', async () => {
    const mockCompetitors = [
      {
        id: 1,
        name: 'Competitor 1',
        domain: 'competitor1.com',
        industry: 'Tech',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const store = createTestStore({
      competitors: {
        competitors: mockCompetitors,
        selectedCompetitor: null,
        dataSources: [],
        insights: [],
        loading: false,
        error: null,
      },
    })

    mockApi.onGet('/competitors').reply(200, mockCompetitors)
    mockApi.onGet('/competitors/1/insights').reply(200, [])

    render(
      <Provider store={store}>
        <InsightsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /competitor/i })).toBeInTheDocument()
    })
  })

  it('should have sentiment filter', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <InsightsPage />
      </Provider>
    )

    expect(screen.getByRole('combobox', { name: /sentiment/i })).toBeInTheDocument()
  })

  it('should have sort options', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <InsightsPage />
      </Provider>
    )

    expect(screen.getByRole('combobox', { name: /sort by/i })).toBeInTheDocument()
  })

  it('should have export button', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <InsightsPage />
      </Provider>
    )

    expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
  })

  it('should display pagination', async () => {
    const mockCompetitors = [
      {
        id: 1,
        name: 'Competitor 1',
        domain: 'competitor1.com',
        industry: 'Tech',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const mockInsights = Array.from({ length: 15 }, (_, i) => ({
      id: i + 1,
      raw_content_id: i + 1,
      summary: `Test insight summary ${i + 1}`,
      key_points: ['Point 1'],
      sentiment: 'positive',
      insights: 'Insights',
      quality_score: 0.8,
      created_at: '2024-01-15T10:30:00Z',
      updated_at: '2024-01-15T10:30:00Z',
    }))

    const store = createTestStore({
      competitors: {
        competitors: mockCompetitors,
        selectedCompetitor: null,
        dataSources: [],
        insights: [],
        loading: false,
        error: null,
      },
    })

    mockApi.onGet('/competitors').reply(200, mockCompetitors)
    mockApi.onGet('/competitors/1/insights').reply(200, mockInsights)

    render(
      <Provider store={store}>
        <InsightsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/page 1 of 2/i)).toBeInTheDocument()
    }, { timeout: 3000 })
  })

  it('should display empty state when no insights', async () => {
    const mockCompetitors = [
      {
        id: 1,
        name: 'Competitor 1',
        domain: 'competitor1.com',
        industry: 'Tech',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const store = createTestStore({
      competitors: {
        competitors: mockCompetitors,
        selectedCompetitor: null,
        dataSources: [],
        insights: [],
        loading: false,
        error: null,
      },
    })

    mockApi.onGet('/competitors').reply(200, mockCompetitors)
    mockApi.onGet('/competitors/1/insights').reply(200, [])

    render(
      <Provider store={store}>
        <InsightsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/no insights found/i)).toBeInTheDocument()
    })
  })
})
