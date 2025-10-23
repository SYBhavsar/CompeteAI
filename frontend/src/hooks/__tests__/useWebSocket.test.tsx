import { renderHook, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import alertsReducer from '@/features/alerts/alertsSlice'
import useWebSocket from '../useWebSocket'

const createTestStore = () => {
  return configureStore({
    reducer: {
      alerts: alertsReducer,
    },
    preloadedState: {
      alerts: {
        alerts: [],
        notifications: [],
        unreadCount: 0,
        loading: false,
        error: null,
      },
    },
  })
}

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = []
  url: string
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  onclose: (() => void) | null = null
  readyState: number = 0

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
    // Simulate connection
    setTimeout(() => {
      this.readyState = 1
      this.onopen?.()
    }, 0)
  }

  send(data: string) {}

  close() {
    this.readyState = 3
    this.onclose?.()
  }

  static clear() {
    MockWebSocket.instances = []
  }
}

global.WebSocket = MockWebSocket as any

describe('useWebSocket', () => {
  beforeEach(() => {
    MockWebSocket.clear()
  })

  it('should connect to WebSocket', async () => {
    const store = createTestStore()
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    )

    const { result } = renderHook(() => useWebSocket(), { wrapper })

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1)
    })
  })

  it('should use correct WebSocket URL', async () => {
    const store = createTestStore()
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    )

    renderHook(() => useWebSocket(), { wrapper })

    await waitFor(() => {
      expect(MockWebSocket.instances[0].url).toContain('ws://')
    })
  })

  it('should handle incoming notifications', async () => {
    const store = createTestStore()
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    )

    renderHook(() => useWebSocket(), { wrapper })

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1)
    })

    const mockNotification = {
      id: 1,
      user_id: 1,
      alert_id: 1,
      message: 'Test notification',
      is_read: false,
      created_at: new Date().toISOString(),
    }

    // Simulate receiving message
    MockWebSocket.instances[0].onmessage?.({
      data: JSON.stringify(mockNotification),
    })

    await waitFor(() => {
      const state = store.getState().alerts
      expect(state.notifications.length).toBe(1)
      expect(state.notifications[0].message).toBe('Test notification')
    })
  })

  it('should cleanup on unmount', async () => {
    const store = createTestStore()
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <Provider store={store}>{children}</Provider>
    )

    const { unmount } = renderHook(() => useWebSocket(), { wrapper })

    await waitFor(() => {
      expect(MockWebSocket.instances.length).toBe(1)
    })

    unmount()

    await waitFor(() => {
      expect(MockWebSocket.instances[0].readyState).toBe(3)
    })
  })
})
