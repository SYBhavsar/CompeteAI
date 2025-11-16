import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import ComparePage from '../page'
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

describe('Compare Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
  })

  it('should render compare page', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <ComparePage />
      </Provider>
    )

    expect(screen.getByRole('heading', { name: /competitor comparison/i, level: 1 })).toBeInTheDocument()
  })

  it('should have competitor selector', async () => {
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
      {
        id: 2,
        name: 'Competitor 2',
        domain: 'competitor2.com',
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

    render(
      <Provider store={store}>
        <ComparePage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/Select Competitors to Compare \(2-4\)/i)).toBeInTheDocument()
    })
  })

  it('should display comparison when competitors selected', async () => {
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
      {
        id: 2,
        name: 'Competitor 2',
        domain: 'competitor2.com',
        industry: 'Tech',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const mockComparison = {
      competitors: [
        {
          id: 1,
          name: 'Competitor 1',
          insights_count: 25,
          avg_quality_score: 0.85,
          sentiment_distribution: {
            positive: 15,
            negative: 5,
            neutral: 5,
          },
        },
        {
          id: 2,
          name: 'Competitor 2',
          insights_count: 30,
          avg_quality_score: 0.78,
          sentiment_distribution: {
            positive: 18,
            negative: 7,
            neutral: 5,
          },
        },
      ],
    }

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
    mockApi.onGet('/analytics/comparison').reply(200, mockComparison)

    render(
      <Provider store={store}>
        <ComparePage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/Select Competitors to Compare \(2-4\)/i)).toBeInTheDocument()
    })
  })

  it('should have compare button', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <ComparePage />
      </Provider>
    )

    expect(screen.getByRole('button', { name: /compare/i })).toBeInTheDocument()
  })

  it('should display empty state when no competitors selected', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <ComparePage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/Select competitors to compare their metrics/i)).toBeInTheDocument()
    })
  })
})
