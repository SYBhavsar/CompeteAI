import alertsReducer, {
  fetchAlertsAsync,
  createAlertAsync,
  updateAlertAsync,
  deleteAlertAsync,
  fetchNotificationsAsync,
  markAsReadAsync,
  addNotification,
} from '../alertsSlice'
import { configureStore } from '@reduxjs/toolkit'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

describe('alertsSlice', () => {
  beforeEach(() => {
    resetMockApi()
  })

  it('should return initial state', () => {
    const state = alertsReducer(undefined, { type: 'unknown' })
    expect(state).toEqual({
      alerts: [],
      notifications: [],
      unreadCount: 0,
      loading: false,
      error: null,
    })
  })

  it('should handle fetchAlertsAsync', async () => {
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

    mockApi.onGet('/alerts').reply(200, mockAlerts)

    const store = configureStore({
      reducer: { alerts: alertsReducer },
    })

    await store.dispatch(fetchAlertsAsync())

    const state = store.getState().alerts
    expect(state.alerts).toEqual(mockAlerts)
    expect(state.loading).toBe(false)
  })

  it('should handle createAlertAsync', async () => {
    const newAlert = {
      competitor_id: 1,
      alert_type: 'new_content' as const,
      conditions: {},
      is_active: true,
    }

    const createdAlert = {
      id: 2,
      user_id: 1,
      ...newAlert,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    mockApi.onPost('/alerts').reply(200, createdAlert)

    const store = configureStore({
      reducer: { alerts: alertsReducer },
    })

    await store.dispatch(createAlertAsync(newAlert))

    const state = store.getState().alerts
    expect(state.alerts).toHaveLength(1)
    expect(state.alerts[0]).toEqual(createdAlert)
  })

  it('should handle updateAlertAsync', async () => {
    const initialState = {
      alerts: [
        {
          id: 1,
          user_id: 1,
          competitor_id: 1,
          alert_type: 'sentiment_change' as const,
          conditions: {},
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
      notifications: [],
      unreadCount: 0,
      loading: false,
      error: null,
    }

    const updatedAlert = {
      ...initialState.alerts[0],
      is_active: false,
    }

    mockApi.onPut('/alerts/1').reply(200, updatedAlert)

    const store = configureStore({
      reducer: { alerts: alertsReducer },
      preloadedState: { alerts: initialState },
    })

    await store.dispatch(updateAlertAsync({ id: 1, data: { is_active: false } }))

    const state = store.getState().alerts
    expect(state.alerts[0].is_active).toBe(false)
  })

  it('should handle deleteAlertAsync', async () => {
    const initialState = {
      alerts: [
        {
          id: 1,
          user_id: 1,
          competitor_id: 1,
          alert_type: 'sentiment_change' as const,
          conditions: {},
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
      notifications: [],
      unreadCount: 0,
      loading: false,
      error: null,
    }

    mockApi.onDelete('/alerts/1').reply(200)

    const store = configureStore({
      reducer: { alerts: alertsReducer },
      preloadedState: { alerts: initialState },
    })

    await store.dispatch(deleteAlertAsync(1))

    const state = store.getState().alerts
    expect(state.alerts).toHaveLength(0)
  })

  it('should handle fetchNotificationsAsync', async () => {
    const mockNotifications = [
      {
        id: 1,
        user_id: 1,
        alert_id: 1,
        message: 'Test notification',
        is_read: false,
        created_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        user_id: 1,
        alert_id: 1,
        message: 'Test notification 2',
        is_read: true,
        created_at: '2024-01-01T00:00:00Z',
      },
    ]

    mockApi.onGet('/notifications').reply(200, mockNotifications)

    const store = configureStore({
      reducer: { alerts: alertsReducer },
    })

    await store.dispatch(fetchNotificationsAsync())

    const state = store.getState().alerts
    expect(state.notifications).toEqual(mockNotifications)
    expect(state.unreadCount).toBe(1)
  })

  it('should handle markAsReadAsync', async () => {
    const initialState = {
      alerts: [],
      notifications: [
        {
          id: 1,
          user_id: 1,
          alert_id: 1,
          message: 'Test notification',
          is_read: false,
          created_at: '2024-01-01T00:00:00Z',
        },
      ],
      unreadCount: 1,
      loading: false,
      error: null,
    }

    mockApi.onPut('/notifications/1/read').reply(200)

    const store = configureStore({
      reducer: { alerts: alertsReducer },
      preloadedState: { alerts: initialState },
    })

    await store.dispatch(markAsReadAsync(1))

    const state = store.getState().alerts
    expect(state.notifications[0].is_read).toBe(true)
    expect(state.unreadCount).toBe(0)
  })

  it('should handle addNotification action', () => {
    const notification = {
      id: 1,
      user_id: 1,
      alert_id: 1,
      message: 'New notification',
      is_read: false,
      created_at: '2024-01-01T00:00:00Z',
    }

    const state = alertsReducer(undefined, addNotification(notification))

    expect(state.notifications).toHaveLength(1)
    expect(state.notifications[0]).toEqual(notification)
    expect(state.unreadCount).toBe(1)
  })
})
