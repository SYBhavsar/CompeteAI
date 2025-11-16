import { createSlice, PayloadAction } from '@reduxjs/toolkit'
import { Notification } from '@/types'

interface NotificationsState {
  items: Notification[]
  unreadCount: number
}

const initialState: NotificationsState = {
  items: [],
  unreadCount: 0,
}

const notificationsSlice = createSlice({
  name: 'notifications',
  initialState,
  reducers: {
    setNotifications: (state, action: PayloadAction<Notification[]>) => {
      state.items = action.payload
      state.unreadCount = action.payload.filter(n => !n.is_read).length
    },
    markAsRead: (state, action: PayloadAction<number>) => {
      const notification = state.items.find(n => n.id === action.payload)
      if (notification && !notification.is_read) {
        notification.is_read = true
        state.unreadCount = Math.max(0, state.unreadCount - 1)
      }
    },
  },
})

export const { setNotifications, markAsRead } = notificationsSlice.actions

// Selectors
export const selectNotifications = (state: { notifications: NotificationsState }) => state.notifications.items
export const selectUnreadCount = (state: { notifications: NotificationsState }) => state.notifications.unreadCount

export default notificationsSlice.reducer
