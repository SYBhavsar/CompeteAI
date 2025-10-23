import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import AnalyticsPage from '../page'
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

describe('Analytics Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
  })

  it('should render analytics page', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onGet('/analytics/trends').reply(200, { data: [] })

    render(
      <Provider store={store}>
        <AnalyticsPage />
      </Provider>
    )

    expect(screen.getByRole('heading', { name: /analytics/i, level: 1 })).toBeInTheDocument()
  })

  it('should display time range selector', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onGet('/analytics/trends').reply(200, { data: [] })

    render(
      <Provider store={store}>
        <AnalyticsPage />
      </Provider>
    )

    expect(screen.getByRole('button', { name: /7 days/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /30 days/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /3 months/i })).toBeInTheDocument()
  })

  it('should display competitor selector', async () => {
    const store = createTestStore()

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

    mockApi.onGet('/competitors').reply(200, mockCompetitors)
    mockApi.onGet('/analytics/trends').reply(200, { data: [] })

    render(
      <Provider store={store}>
        <AnalyticsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('combobox', { name: /competitor/i })).toBeInTheDocument()
    })
  })

  it('should fetch trends data on mount', async () => {
    const store = createTestStore()

    const mockTrends = {
      data: [
        { date: '2024-01-01', value: 10 },
        { date: '2024-01-02', value: 15 },
      ],
    }

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onGet('/analytics/trends').reply(200, mockTrends)

    render(
      <Provider store={store}>
        <AnalyticsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /trend analysis/i })).toBeInTheDocument()
    })
  })

  it('should have export button', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onGet('/analytics/trends').reply(200, { data: [] })

    render(
      <Provider store={store}>
        <AnalyticsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
    })
  })

  it('should change time range when clicked', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onGet('/analytics/trends').reply(200, { data: [] })

    render(
      <Provider store={store}>
        <AnalyticsPage />
      </Provider>
    )

    const thirtyDaysButton = screen.getByRole('button', { name: /30 days/i })
    await user.click(thirtyDaysButton)

    // Should be active now
    expect(thirtyDaysButton).toHaveAttribute('data-active', 'true')
  })

  it('should display sentiment chart section', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onGet('/analytics/trends').reply(200, { data: [] })

    render(
      <Provider store={store}>
        <AnalyticsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /sentiment distribution/i })).toBeInTheDocument()
    })
  })

  it('should display quality score chart section', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onGet('/analytics/trends').reply(200, { data: [] })

    render(
      <Provider store={store}>
        <AnalyticsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /quality score trends/i })).toBeInTheDocument()
    })
  })
})
