import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import api from '@/services/api'
import { Alert, Notification } from '@/types'

interface AlertsState {
  alerts: Alert[]
  notifications: Notification[]
  unreadCount: number
  loading: boolean
  error: string | null
}

const initialState: AlertsState = {
  alerts: [],
  notifications: [],
  unreadCount: 0,
  loading: false,
  error: null,
}

// Async thunks
export const fetchAlertsAsync = createAsyncThunk(
  'alerts/fetchAlerts',
  async () => {
    const response = await api.get('/alerts')
    return response.data
  }
)

export const createAlertAsync = createAsyncThunk(
  'alerts/createAlert',
  async (alertData: Omit<Alert, 'id' | 'user_id' | 'created_at' | 'updated_at'>) => {
    const response = await api.post('/alerts', alertData)
    return response.data
  }
)

export const updateAlertAsync = createAsyncThunk(
  'alerts/updateAlert',
  async ({ id, data }: { id: number; data: Partial<Alert> }) => {
    const response = await api.put(`/alerts/${id}`, data)
    return response.data
  }
)

export const deleteAlertAsync = createAsyncThunk(
  'alerts/deleteAlert',
  async (id: number) => {
    await api.delete(`/alerts/${id}`)
    return id
  }
)

export const fetchNotificationsAsync = createAsyncThunk(
  'alerts/fetchNotifications',
  async () => {
    const response = await api.get('/notifications')
    return response.data
  }
)

export const markAsReadAsync = createAsyncThunk(
  'alerts/markAsRead',
  async (id: number) => {
    await api.put(`/notifications/${id}/read`)
    return id
  }
)

const alertsSlice = createSlice({
  name: 'alerts',
  initialState,
  reducers: {
    addNotification: (state, action: PayloadAction<Notification>) => {
      state.notifications.unshift(action.payload)
      if (!action.payload.is_read) {
        state.unreadCount += 1
      }
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch alerts
      .addCase(fetchAlertsAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchAlertsAsync.fulfilled, (state, action) => {
        state.loading = false
        state.alerts = action.payload
      })
      .addCase(fetchAlertsAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch alerts'
      })
      // Create alert
      .addCase(createAlertAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(createAlertAsync.fulfilled, (state, action) => {
        state.loading = false
        state.alerts.push(action.payload)
      })
      .addCase(createAlertAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to create alert'
      })
      // Update alert
      .addCase(updateAlertAsync.fulfilled, (state, action) => {
        const index = state.alerts.findIndex((a) => a.id === action.payload.id)
        if (index !== -1) {
          state.alerts[index] = action.payload
        }
      })
      // Delete alert
      .addCase(deleteAlertAsync.fulfilled, (state, action) => {
        state.alerts = state.alerts.filter((a) => a.id !== action.payload)
      })
      // Fetch notifications
      .addCase(fetchNotificationsAsync.fulfilled, (state, action) => {
        state.notifications = action.payload
        state.unreadCount = action.payload.filter((n: Notification) => !n.is_read).length
      })
      // Mark as read
      .addCase(markAsReadAsync.fulfilled, (state, action) => {
        const notification = state.notifications.find((n) => n.id === action.payload)
        if (notification && !notification.is_read) {
          notification.is_read = true
          state.unreadCount -= 1
        }
      })
  },
})

export const { addNotification, clearError } = alertsSlice.actions
export default alertsSlice.reducer
