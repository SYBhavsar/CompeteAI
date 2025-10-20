import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import Header from '../Header'

const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}))

const createTestStore = () => {
  return configureStore({
    reducer: {
      auth: authReducer,
    },
    preloadedState: {
      auth: {
        user: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test User',
          is_active: true,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
        token: 'test-token',
        isAuthenticated: true,
        loading: false,
        error: null,
      },
    },
  })
}

describe('Header Component', () => {
  beforeEach(() => {
    mockPush.mockClear()
  })

  it('should toggle user menu when clicking user icon', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    render(
      <Provider store={store}>
        <Header />
      </Provider>
    )

    // User menu should not be visible initially
    expect(screen.queryByText('Sign out')).not.toBeInTheDocument()

    // Click user icon to open menu
    const userMenuButton = screen.getByLabelText('User menu')
    await user.click(userMenuButton)

    // User menu should be visible
    expect(screen.getByText('Sign out')).toBeInTheDocument()
    expect(screen.getByText('test@example.com')).toBeInTheDocument()
  })

  it('should logout user and redirect to /login when clicking Sign out', async () => {
    const user = userEvent.setup()
    const store = createTestStore()
    const removeTokenSpy = jest.spyOn(Storage.prototype, 'removeItem')

    render(
      <Provider store={store}>
        <Header />
      </Provider>
    )

    // Open user menu
    const userMenuButton = screen.getByLabelText('User menu')
    await user.click(userMenuButton)

    // Click Sign out
    const signOutButton = screen.getByText('Sign out')
    await user.click(signOutButton)

    // Wait for logout action
    await waitFor(() => {
      // Verify token removed from localStorage
      expect(removeTokenSpy).toHaveBeenCalledWith('auth_token')

      // Verify redirect to login
      expect(mockPush).toHaveBeenCalledWith('/login')

      // Verify user is logged out in Redux
      const state = store.getState()
      expect(state.auth.isAuthenticated).toBe(false)
      expect(state.auth.user).toBeNull()
    })

    removeTokenSpy.mockRestore()
  })

  it('should render a search bar', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <Header />
      </Provider>
    )

    const searchInput = screen.getByPlaceholderText(/search.../i)
    expect(searchInput).toBeInTheDocument()
  })
})
