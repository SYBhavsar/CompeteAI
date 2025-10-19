import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import LoginPage from '../page'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

// Mock next/navigation
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
  })
}

describe('Login Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
    mockPush.mockClear()
  })

  it('should successfully login user and redirect to dashboard', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    const mockResponse = {
      access_token: 'test-token',
      token_type: 'bearer',
      user: {
        id: 1,
        email: 'test@example.com',
        full_name: 'Test User',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    }

    mockApi.onPost('/auth/login').reply(200, mockResponse)

    render(
      <Provider store={store}>
        <LoginPage />
      </Provider>
    )

    // Fill in form
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in|log in/i })

    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.click(submitButton)

    // Wait for redirect
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard')
    })

    // Verify user is authenticated in Redux
    const state = store.getState()
    expect(state.auth.isAuthenticated).toBe(true)
    expect(state.auth.user?.email).toBe('test@example.com')
  })

  it('should display error message on login failure', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    mockApi.onPost('/auth/login').reply(401, { detail: 'Invalid credentials' })

    render(
      <Provider store={store}>
        <LoginPage />
      </Provider>
    )

    // Fill in form with wrong credentials
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/password/i)
    const submitButton = screen.getByRole('button', { name: /sign in|log in/i })

    await user.type(emailInput, 'wrong@example.com')
    await user.type(passwordInput, 'wrongpassword')
    await user.click(submitButton)

    // Wait for error message to appear
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument()
    })

    // Verify user is NOT authenticated
    const state = store.getState()
    expect(state.auth.isAuthenticated).toBe(false)
    expect(mockPush).not.toHaveBeenCalled()
  })
})
