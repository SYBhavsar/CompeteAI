import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import DashboardPage from '../page'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

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
      ...initialState,
    },
  })
}

describe('Dashboard Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
    mockPush.mockClear()
  })

  it('should display welcome message with user name', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    )

    expect(screen.getByText(/welcome back, test user/i)).toBeInTheDocument()
  })

  it('should display all metric cards with loading state initially', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText('Total Competitors')).toBeInTheDocument()
    })

    expect(screen.getByText('Total Insights')).toBeInTheDocument()
    expect(screen.getByText('Recent Alerts')).toBeInTheDocument()
    expect(screen.getByText('Searches')).toBeInTheDocument()
  })

  it('should fetch and display competitor count', async () => {
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

    mockApi.onGet('/competitors').reply(200, mockCompetitors)

    render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    )

    await waitFor(() => {
      const competitorMetric = screen.getByText('Total Competitors').closest('[role="article"]')
      expect(competitorMetric).toHaveTextContent('2')
    })
  })

  it('should display quick action buttons', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /add competitor/i })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /new search/i })).toBeInTheDocument()
  })

  it('should navigate to competitors page when Add Competitor clicked', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    )

    const addButton = screen.getByRole('button', { name: /add competitor/i })
    await user.click(addButton)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard/competitors')
    })
  })

  it('should navigate to search page when New Search clicked', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    )

    const searchButton = screen.getByRole('button', { name: /new search/i })
    await user.click(searchButton)

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard/search')
    })
  })

  it('should display recent activity section', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    )

    await waitFor(() => {
      const activitySections = screen.getAllByText(/recent activity/i)
      expect(activitySections.length).toBeGreaterThan(0)
    })
  })

  it('should handle API error gracefully', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(500, { detail: 'Server error' })

    render(
      <Provider store={store}>
        <DashboardPage />
      </Provider>
    )

    await waitFor(() => {
      const metricCards = screen.getAllByText('0')
      expect(metricCards.length).toBeGreaterThan(0)
    })
  })
})
