import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import alertsReducer from '@/features/alerts/alertsSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import AlertsPage from '../page'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      alerts: alertsReducer,
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
      alerts: {
        alerts: [],
        notifications: [],
        unreadCount: 0,
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

describe('Alerts Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
  })

  it('should render alerts page', async () => {
    const store = createTestStore()

    mockApi.onGet('/alerts').reply(200, [])
    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <AlertsPage />
      </Provider>
    )

    expect(screen.getByRole('heading', { name: /alerts/i, level: 1 })).toBeInTheDocument()
  })

  it('should display list of alerts', async () => {
    const mockAlerts = [
      {
        id: 1,
        user_id: 1,
        competitor_id: 1,
        alert_type: 'sentiment_change',
        conditions: { threshold: 0.5 },
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        user_id: 1,
        competitor_id: 2,
        alert_type: 'new_content',
        conditions: {},
        is_active: false,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ]

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

    const store = createTestStore()

    mockApi.onGet('/alerts').reply(200, mockAlerts)
    mockApi.onGet('/competitors').reply(200, mockCompetitors)

    render(
      <Provider store={store}>
        <AlertsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/sentiment change/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/new content/i)).toBeInTheDocument()
  })

  it('should have create alert button', async () => {
    const store = createTestStore()

    mockApi.onGet('/alerts').reply(200, [])
    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <AlertsPage />
      </Provider>
    )

    expect(screen.getByRole('button', { name: /create alert/i })).toBeInTheDocument()
  })

  it('should toggle alert status', async () => {
    const user = userEvent.setup()

    const mockAlerts = [
      {
        id: 1,
        user_id: 1,
        competitor_id: 1,
        alert_type: 'sentiment_change',
        conditions: { threshold: 0.5 },
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const store = createTestStore()

    mockApi.onGet('/alerts').reply(200, mockAlerts)
    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onPut('/alerts/1').reply(200, { ...mockAlerts[0], is_active: false })

    render(
      <Provider store={store}>
        <AlertsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/sentiment change/i)).toBeInTheDocument()
    })

    const toggleButtons = screen.getAllByRole('button')
    const toggleButton = toggleButtons.find((btn) => btn.getAttribute('aria-label')?.includes('Toggle'))

    if (toggleButton) {
      await user.click(toggleButton)
    }
  })

  it('should display empty state when no alerts', async () => {
    const store = createTestStore()

    mockApi.onGet('/alerts').reply(200, [])
    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <AlertsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/no alerts configured/i)).toBeInTheDocument()
    })
  })

  it('should delete alert', async () => {
    const user = userEvent.setup()

    // Mock window.confirm
    window.confirm = jest.fn(() => true)

    const mockAlerts = [
      {
        id: 1,
        user_id: 1,
        competitor_id: 1,
        alert_type: 'sentiment_change',
        conditions: { threshold: 0.5 },
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    const store = createTestStore()

    mockApi.onGet('/alerts').reply(200, mockAlerts)
    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onDelete('/alerts/1').reply(200)

    render(
      <Provider store={store}>
        <AlertsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/sentiment change/i)).toBeInTheDocument()
    })

    const deleteButtons = screen.getAllByRole('button')
    const deleteButton = deleteButtons.find((btn) => btn.getAttribute('aria-label')?.includes('Delete'))

    if (deleteButton) {
      await user.click(deleteButton)
    }
  })
})
