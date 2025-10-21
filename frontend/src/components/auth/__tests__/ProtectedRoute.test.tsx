import { render, screen, waitFor } from '@testing-library/react'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import ProtectedRoute from '../ProtectedRoute'
import {  resetMockApi } from '@/tests/helpers/mockApi'

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
    },
    preloadedState: {
      auth: {
        user: null,
        token: null,
        isAuthenticated: false,
        loading: false,
        error: null,
        ...initialState,
      },
    },
  })
}

describe('ProtectedRoute Component', () => {
  beforeEach(() => {
    resetMockApi()
    mockPush.mockClear()
    jest.clearAllMocks()
  })

  it('should redirect to /login when user is not authenticated', async () => {
    const store = createTestStore()

    // Mock no token in localStorage
    const getTokenSpy = jest.spyOn(Storage.prototype, 'getItem').mockReturnValue(null)

    render(
      <Provider store={store}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </Provider>
    )

    // Wait for auth check to complete and redirect
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    }, { timeout: 3000 })

    // Should not render children
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()

    getTokenSpy.mockRestore()
  })

  it('should show loading spinner while checking authentication', () => {
    const store = createTestStore({ loading: true })

    render(
      <Provider store={store}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </Provider>
    )

    expect(screen.getByText('Loading...')).toBeInTheDocument()
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument()
  })

  it('should render children when user is authenticated', async () => {
    const store = createTestStore({
      isAuthenticated: true,
      user: {
        id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      },
      token: 'valid-token',
    })

    const getTokenSpy = jest.spyOn(Storage.prototype, 'getItem').mockReturnValue('valid-token')

    render(
      <Provider store={store}>
        <ProtectedRoute>
          <div>Protected Content</div>
        </ProtectedRoute>
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText('Protected Content')).toBeInTheDocument()
    })

    expect(mockPush).not.toHaveBeenCalled()

    getTokenSpy.mockRestore()
  })
})
