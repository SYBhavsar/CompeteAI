import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import RegisterPage from '../page'
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

describe('Register Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
    mockPush.mockClear()
  })

  it('should successfully register user and redirect to dashboard', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    const mockResponse = {
      access_token: 'new-user-token',
      token_type: 'bearer',
      user: {
        id: 2,
        email: 'newuser@example.com',
        full_name: 'New User',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    }

    mockApi.onPost('/auth/register').reply(200, mockResponse)

    render(
      <Provider store={store}>
        <RegisterPage />
      </Provider>
    )

    // Fill in form
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const termsCheckbox = screen.getByLabelText(/i agree to the/i)
    const submitButton = screen.getByRole('button', { name: /sign up|register/i })

    await user.type(nameInput, 'New User')
    await user.type(emailInput, 'newuser@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'password123')
    await user.click(termsCheckbox)
    await user.click(submitButton)

    // Wait for redirect
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    // Verify user is NOT authenticated in Redux yet (they need to login)
    const state = store.getState()
    expect(state.auth.isAuthenticated).toBe(false)
  })

  it('should display error when passwords do not match', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    render(
      <Provider store={store}>
        <RegisterPage />
      </Provider>
    )

    // Fill in form with mismatched passwords
    const nameInput = screen.getByLabelText(/full name/i)
    const emailInput = screen.getByLabelText(/email/i)
    const passwordInput = screen.getByLabelText(/^password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)
    const submitButton = screen.getByRole('button', { name: /sign up|register/i })

    await user.type(nameInput, 'Test User')
    await user.type(emailInput, 'test@example.com')
    await user.type(passwordInput, 'password123')
    await user.type(confirmPasswordInput, 'different')
    await user.click(submitButton)

    // Wait for validation error
    await waitFor(() => {
      expect(screen.getByText(/passwords must match/i)).toBeInTheDocument()
    })

    // Verify user is NOT authenticated
    const state = store.getState()
    expect(state.auth.isAuthenticated).toBe(false)
    expect(mockPush).not.toHaveBeenCalled()
  })

  it('should render a "Terms & Conditions" checkbox and prevent submission if unchecked', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    render(
      <Provider store={store}>
        <RegisterPage />
      </Provider>
    )

    const termsCheckbox = screen.getByLabelText(/i agree to the/i)
    expect(termsCheckbox).toBeInTheDocument()
    expect(termsCheckbox).not.toBeChecked()

    // Fill out the form but don't check the box
    await user.type(screen.getByLabelText(/full name/i), 'Test User')
    await user.type(screen.getByLabelText(/email/i), 'test@example.com')
    await user.type(screen.getByLabelText(/^password$/i), 'password123')
    await user.type(screen.getByLabelText(/confirm password/i), 'password123')

    // Try to submit
    const submitButton = screen.getByRole('button', { name: /sign up|register/i })
    await user.click(submitButton)

    // Expect validation error
    await waitFor(() => {
      expect(screen.getByText(/you must accept the terms and conditions/i)).toBeInTheDocument()
    })

    expect(mockApi.history.post.length).toBe(0)
    expect(mockPush).not.toHaveBeenCalled()
  })
})
