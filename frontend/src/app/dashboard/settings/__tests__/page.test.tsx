import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import SettingsPage from '../page'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

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
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        token: 'test-token',
        isAuthenticated: true,
        loading: false,
        error: null,
      },
    },
  })
}

describe('Settings Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
  })

  it('should render settings page', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <SettingsPage />
      </Provider>
    )

    expect(screen.getByRole('heading', { name: /settings/i, level: 1 })).toBeInTheDocument()
  })

  it('should have profile tab', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <SettingsPage />
      </Provider>
    )

    expect(screen.getByRole('tab', { name: /profile/i })).toBeInTheDocument()
  })

  it('should have security tab', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <SettingsPage />
      </Provider>
    )

    expect(screen.getByRole('tab', { name: /security/i })).toBeInTheDocument()
  })

  it('should have preferences tab', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <SettingsPage />
      </Provider>
    )

    expect(screen.getByRole('tab', { name: /preferences/i })).toBeInTheDocument()
  })

  it('should display profile content by default', () => {
    const store = createTestStore()

    render(
      <Provider store={store}>
        <SettingsPage />
      </Provider>
    )

    expect(screen.getByDisplayValue(/test@example.com/i)).toBeInTheDocument()
    expect(screen.getByDisplayValue(/test user/i)).toBeInTheDocument()
  })

  it('should switch to security tab', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    render(
      <Provider store={store}>
        <SettingsPage />
      </Provider>
    )

    const securityTab = screen.getByRole('tab', { name: /security/i })
    await user.click(securityTab)

    await waitFor(() => {
      expect(screen.getByLabelText(/current password/i)).toBeInTheDocument()
    })
  })

  it('should update profile', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    mockApi.onPut('/users/me').reply(200, {
      id: 1,
      email: 'test@example.com',
      full_name: 'Updated Name',
      is_active: true,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })

    render(
      <Provider store={store}>
        <SettingsPage />
      </Provider>
    )

    const nameInput = screen.getByLabelText(/full name/i)
    await user.clear(nameInput)
    await user.type(nameInput, 'Updated Name')

    const saveButton = screen.getByRole('button', { name: /save/i })
    await user.click(saveButton)

    await waitFor(() => {
      expect(mockApi.history.put.length).toBe(1)
    })
  })

  it('should change password', async () => {
    const user = userEvent.setup()
    const store = createTestStore()

    mockApi.onPut('/users/me/password').reply(200)

    render(
      <Provider store={store}>
        <SettingsPage />
      </Provider>
    )

    const securityTab = screen.getByRole('tab', { name: /security/i })
    await user.click(securityTab)

    await waitFor(() => {
      expect(screen.getByLabelText(/current password/i)).toBeInTheDocument()
    })

    const currentPasswordInput = screen.getByLabelText(/current password/i)
    const newPasswordInput = screen.getByLabelText(/^new password$/i)
    const confirmPasswordInput = screen.getByLabelText(/confirm password/i)

    await user.type(currentPasswordInput, 'oldpassword')
    await user.type(newPasswordInput, 'newpassword123')
    await user.type(confirmPasswordInput, 'newpassword123')

    const changePasswordButton = screen.getByRole('button', { name: /change password/i })
    await user.click(changePasswordButton)

    await waitFor(() => {
      expect(mockApi.history.put.length).toBe(1)
    })
  })
})
