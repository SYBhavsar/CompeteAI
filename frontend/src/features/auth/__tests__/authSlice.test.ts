import { configureStore } from '@reduxjs/toolkit'
import authReducer, { loginAsync, registerAsync, logout, restoreAuth } from '../authSlice'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'
import { authService } from '@/services/authService'

// Helper to create a fresh store for each test
const createTestStore = () => {
  return configureStore({
    reducer: {
      auth: authReducer,
    },
  })
}

describe('authSlice - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
    localStorage.clear()
    jest.clearAllMocks()
  })

  it('should have correct initial state', () => {
    const store = createTestStore()
    const state = store.getState().auth

    expect(state).toEqual({
      user: null,
      token: null,
      isAuthenticated: false,
      loading: false,
      error: null,
    })
  })

  it('should handle full login flow: set loading, save user/token, persist to localStorage', async () => {
    const store = createTestStore()
    const saveTokenSpy = jest.spyOn(authService, 'saveToken')

    const mockResponse = {
      access_token: 'test-token-123',
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

    // Dispatch login action
    await store.dispatch(loginAsync({ email: 'test@example.com', password: 'password123' }))

    const state = store.getState().auth

    // Verify state updated correctly
    expect(state.isAuthenticated).toBe(true)
    expect(state.user?.email).toBe('test@example.com')
    expect(state.token).toBe('test-token-123')
    expect(state.loading).toBe(false)
    expect(state.error).toBeNull()

    // Verify token saved to localStorage
    expect(saveTokenSpy).toHaveBeenCalledWith('test-token-123')

    saveTokenSpy.mockRestore()
  })

  it('should handle login failure: set error, clear user/token, stay unauthenticated', async () => {
    const store = createTestStore()

    mockApi.onPost('/auth/login').reply(401, { detail: 'Invalid credentials' })

    await store.dispatch(loginAsync({ email: 'wrong@example.com', password: 'wrong' }))

    const state = store.getState().auth

    expect(state.isAuthenticated).toBe(false)
    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.loading).toBe(false)
    expect(state.error).toBeTruthy()
  })

  it('should handle register flow: create user, save token, authenticate', async () => {
    const store = createTestStore()
    const saveTokenSpy = jest.spyOn(authService, 'saveToken')

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

    await store.dispatch(
      registerAsync({
        email: 'newuser@example.com',
        password: 'password123',
        full_name: 'New User',
      })
    )

    const state = store.getState().auth

    expect(state.isAuthenticated).toBe(true)
    expect(state.user?.email).toBe('newuser@example.com')
    expect(state.token).toBe('new-user-token')
    expect(saveTokenSpy).toHaveBeenCalledWith('new-user-token')

    saveTokenSpy.mockRestore()
  })

  it('should handle logout: clear all auth state and remove token from localStorage', () => {
    const store = createTestStore()
    const removeTokenSpy = jest.spyOn(authService, 'removeToken')

    // First login to set state
    store.dispatch({
      type: 'auth/loginAsync/fulfilled',
      payload: {
        access_token: 'token',
        token_type: 'bearer',
        user: {
          id: 1,
          email: 'test@example.com',
          full_name: 'Test',
          is_active: true,
          created_at: '2024-01-01',
          updated_at: '2024-01-01',
        },
      },
    })

    // Then logout
    store.dispatch(logout())

    const state = store.getState().auth

    expect(state.user).toBeNull()
    expect(state.token).toBeNull()
    expect(state.isAuthenticated).toBe(false)
    expect(removeTokenSpy).toHaveBeenCalled()

    removeTokenSpy.mockRestore()
  })

  it('should restore auth from localStorage on app load if token exists', async () => {
    const store = createTestStore()
    const getTokenSpy = jest.spyOn(authService, 'getToken').mockReturnValue('stored-token')

    await store.dispatch(restoreAuth())

    const state = store.getState().auth

    expect(state.isAuthenticated).toBe(true)
    expect(state.token).toBe('stored-token')

    getTokenSpy.mockRestore()
  })
})
