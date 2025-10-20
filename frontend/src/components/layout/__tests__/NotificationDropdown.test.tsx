import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import NotificationDropdown from '../NotificationDropdown'

// Mock notification reducer (we'll create this)
const mockNotifications = [
  { id: 1, message: 'New competitor added', is_read: false, created_at: '2024-01-01T10:00:00Z' },
  { id: 2, message: 'Search completed', is_read: true, created_at: '2024-01-01T09:00:00Z' },
  { id: 3, message: 'Alert triggered', is_read: false, created_at: '2024-01-01T08:00:00Z' },
]

const createTestStore = (notifications = mockNotifications, unreadCount = 2) => {
  return configureStore({
    reducer: {
      notifications: (state = { items: notifications, unreadCount }) => state,
    },
  })
}

describe('NotificationDropdown Component', () => {
  it('should toggle dropdown when clicking bell icon', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    render(
      <Provider store={store}>
        <NotificationDropdown />
      </Provider>
    )

    // Dropdown should not be visible initially
    expect(screen.queryByText('New competitor added')).not.toBeInTheDocument()

    // Click bell icon
    const bellButton = screen.getByLabelText(/notifications/i)
    await user.click(bellButton)

    // Dropdown should be visible
    expect(screen.getByText('New competitor added')).toBeInTheDocument()
  })

  it('should display unread count badge when there are unread notifications', () => {
    const store = createTestStore(mockNotifications, 2)

    render(
      <Provider store={store}>
        <NotificationDropdown />
      </Provider>
    )

    // Badge should show count
    expect(screen.getByText('2')).toBeInTheDocument()
  })

  it('should not display badge when no unread notifications', () => {
    const store = createTestStore(mockNotifications, 0)

    render(
      <Provider store={store}>
        <NotificationDropdown />
      </Provider>
    )

    // No badge should be displayed
    const badge = screen.queryByText('0')
    expect(badge).not.toBeInTheDocument()
  })

  it('should display list of notifications when dropdown is open', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    render(
      <Provider store={store}>
        <NotificationDropdown />
      </Provider>
    )

    // Open dropdown
    const bellButton = screen.getByLabelText(/notifications/i)
    await user.click(bellButton)

    // Should display all notifications
    expect(screen.getByText('New competitor added')).toBeInTheDocument()
    expect(screen.getByText('Search completed')).toBeInTheDocument()
    expect(screen.getByText('Alert triggered')).toBeInTheDocument()
  })

  it('should have "View all" link in dropdown', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    render(
      <Provider store={store}>
        <NotificationDropdown />
      </Provider>
    )

    // Open dropdown
    const bellButton = screen.getByLabelText(/notifications/i)
    await user.click(bellButton)

    // Should have "View all" link
    const viewAllLink = screen.getByText(/view all/i)
    expect(viewAllLink).toBeInTheDocument()
    expect(viewAllLink).toHaveAttribute('href', '/dashboard/notifications')
  })

  it('should show empty state when no notifications', async () => {
    const user = userEvent.setup()
    const store = createTestStore([], 0)

    render(
      <Provider store={store}>
        <NotificationDropdown />
      </Provider>
    )

    // Open dropdown
    const bellButton = screen.getByLabelText(/notifications/i)
    await user.click(bellButton)

    // Should show empty message
    expect(screen.getByText(/no notifications/i)).toBeInTheDocument()
  })
})
