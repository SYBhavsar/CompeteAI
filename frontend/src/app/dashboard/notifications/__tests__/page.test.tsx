import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import alertsReducer from '@/features/alerts/alertsSlice'
import NotificationsPage from '../page'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

const createTestStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      alerts: alertsReducer,
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
      ...initialState,
    },
  })
}

describe('Notifications Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
  })

  it('should render notifications page', async () => {
    const store = createTestStore()

    mockApi.onGet('/notifications').reply(200, [])

    render(
      <Provider store={store}>
        <NotificationsPage />
      </Provider>
    )

    expect(screen.getByRole('heading', { name: /notifications/i, level: 1 })).toBeInTheDocument()
  })

  it('should display list of notifications', async () => {
    const mockNotifications = [
      {
        id: 1,
        user_id: 1,
        alert_id: 1,
        message: 'New content detected from Competitor 1',
        is_read: false,
        created_at: '2024-01-15T10:30:00Z',
      },
      {
        id: 2,
        user_id: 1,
        alert_id: 2,
        message: 'Sentiment change detected',
        is_read: true,
        created_at: '2024-01-14T09:20:00Z',
      },
    ]

    const store = createTestStore()

    mockApi.onGet('/notifications').reply(200, mockNotifications)

    render(
      <Provider store={store}>
        <NotificationsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/new content detected/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/sentiment change detected/i)).toBeInTheDocument()
  })

  it('should display unread count', async () => {
    const mockNotifications = [
      {
        id: 1,
        user_id: 1,
        alert_id: 1,
        message: 'Test notification 1',
        is_read: false,
        created_at: '2024-01-15T10:30:00Z',
      },
      {
        id: 2,
        user_id: 1,
        alert_id: 2,
        message: 'Test notification 2',
        is_read: false,
        created_at: '2024-01-14T09:20:00Z',
      },
      {
        id: 3,
        user_id: 1,
        alert_id: 3,
        message: 'Test notification 3',
        is_read: true,
        created_at: '2024-01-13T08:10:00Z',
      },
    ]

    const store = createTestStore()

    mockApi.onGet('/notifications').reply(200, mockNotifications)

    render(
      <Provider store={store}>
        <NotificationsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/2/, { selector: 'span' })).toBeInTheDocument()
    })
  })

  it('should have filter buttons', async () => {
    const store = createTestStore()

    mockApi.onGet('/notifications').reply(200, [])

    render(
      <Provider store={store}>
        <NotificationsPage />
      </Provider>
    )

    expect(screen.getByRole('button', { name: /all/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /unread/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^read$/i })).toBeInTheDocument()
  })

  it('should mark notification as read', async () => {
    const user = userEvent.setup()

    const mockNotifications = [
      {
        id: 1,
        user_id: 1,
        alert_id: 1,
        message: 'Test notification',
        is_read: false,
        created_at: '2024-01-15T10:30:00Z',
      },
    ]

    const store = createTestStore()

    mockApi.onGet('/notifications').reply(200, mockNotifications)
    mockApi.onPut('/notifications/1/read').reply(200)

    render(
      <Provider store={store}>
        <NotificationsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/test notification/i)).toBeInTheDocument()
    })

    const markReadButtons = screen.getAllByRole('button')
    const markReadButton = markReadButtons.find((btn) => btn.getAttribute('aria-label')?.includes('Mark as read'))

    if (markReadButton) {
      await user.click(markReadButton)
    }
  })

  it('should display empty state when no notifications', async () => {
    const store = createTestStore()

    mockApi.onGet('/notifications').reply(200, [])

    render(
      <Provider store={store}>
        <NotificationsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/no notifications/i)).toBeInTheDocument()
    })
  })

  it('should filter notifications by unread', async () => {
    const user = userEvent.setup()

    const mockNotifications = [
      {
        id: 1,
        user_id: 1,
        alert_id: 1,
        message: 'This is unread',
        is_read: false,
        created_at: '2024-01-15T10:30:00Z',
      },
      {
        id: 2,
        user_id: 1,
        alert_id: 2,
        message: 'This is already read',
        is_read: true,
        created_at: '2024-01-14T09:20:00Z',
      },
    ]

    const store = createTestStore()

    mockApi.onGet('/notifications').reply(200, mockNotifications)

    render(
      <Provider store={store}>
        <NotificationsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/this is unread/i)).toBeInTheDocument()
    })

    const unreadButton = screen.getByRole('button', { name: /unread/i })
    await user.click(unreadButton)

    // After clicking unread filter, read notification should not be visible
    expect(screen.queryByText(/this is already read/i)).not.toBeInTheDocument()
  })
})
