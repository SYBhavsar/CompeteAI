import { useEffect, useRef } from 'react'
import { useAppDispatch } from '@/lib/hooks'
import { addNotification } from '@/features/alerts/alertsSlice'
import { Notification } from '@/types'

export default function useWebSocket() {
  const dispatch = useAppDispatch()
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Get WebSocket URL from environment or default
    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
    const ws = new WebSocket(`${wsUrl}/ws/notifications`)

    ws.onopen = () => {
      console.log('WebSocket connected')
    }

    ws.onmessage = (event) => {
      try {
        const notification: Notification = JSON.parse(event.data)
        dispatch(addNotification(notification))
      } catch (error) {
        console.error('Failed to parse notification:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
    }

    wsRef.current = ws

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [dispatch])

  return wsRef.current
}
