import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { authService } from '@/services/authService'
import { User, LoginRequest, RegisterRequest, AuthResponse } from '@/types'

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  loading: boolean
  error: string | null
}

const initialState: AuthState = {
  user: null,
  token: null,
  isAuthenticated: false,
  loading: false,
  error: null,
}

/**
 * Login user with email and password
 * Persists token to localStorage on success
 */
export const loginAsync = createAsyncThunk<AuthResponse, LoginRequest>(
  'auth/loginAsync',
  async (credentials, { rejectWithValue }) => {
    try {
      const response = await authService.login(credentials)
      authService.saveToken(response.access_token)
      return response
    } catch (error) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      return rejectWithValue(axiosError.response?.data?.detail || 'Login failed')
    }
  }
)

/**
 * Register new user account
 * Auto-authenticates user on success
 */
export const registerAsync = createAsyncThunk<AuthResponse, RegisterRequest>(
  'auth/registerAsync',
  async (data, { rejectWithValue }) => {
    try {
      const response = await authService.register(data)
      return response
    } catch (error) {
      const axiosError = error as { response?: { data?: { detail?: string } } }
      return rejectWithValue(axiosError.response?.data?.detail || 'Registration failed')
    }
  }
)

/**
 * Restore authentication state from localStorage on app load
 * Note: Backend doesn't have /auth/me endpoint, so we just check if token exists
 * User will need to login again if token is invalid
 */
export const restoreAuth = createAsyncThunk<{ token: string } | null>(
  'auth/restoreAuth',
  async () => {
    const token = authService.getToken()
    if (!token) {
      return null
    }
    return { token }
  }
)

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    logout: (state) => {
      state.user = null
      state.token = null
      state.isAuthenticated = false
      state.error = null
      authService.removeToken()
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    // Login
    builder
      .addCase(loginAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(loginAsync.fulfilled, (state, action: PayloadAction<AuthResponse>) => {
        state.loading = false
        state.isAuthenticated = true
        state.user = action.payload.user
        state.token = action.payload.access_token
        state.error = null
      })
      .addCase(loginAsync.rejected, (state, action) => {
        state.loading = false
        state.isAuthenticated = false
        state.user = null
        state.token = null
        state.error = action.payload as string
      })

    // Register
    builder
      .addCase(registerAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(registerAsync.fulfilled, (state) => {
        state.loading = false
        state.error = null
      })
      .addCase(registerAsync.rejected, (state, action) => {
        state.loading = false
        state.isAuthenticated = false
        state.error = action.payload as string
      })

    // Restore Auth
    builder
      .addCase(restoreAuth.pending, (state) => {
        state.loading = true
      })
      .addCase(restoreAuth.fulfilled, (state, action) => {
        if (action.payload) {
          state.loading = false
          state.token = action.payload.token
          // Note: User will be authenticated but user data unknown until they interact
          // This is a limitation since backend doesn't have /auth/me endpoint
          state.isAuthenticated = true
        } else {
          state.loading = false
        }
      })
      .addCase(restoreAuth.rejected, (state) => {
        state.loading = false
        state.isAuthenticated = false
        state.user = null
        state.token = null
      })
  },
})

export const { logout, clearError } = authSlice.actions

// Selectors
export const selectAuth = (state: { auth: AuthState }) => state.auth
export const selectUser = (state: { auth: AuthState }) => state.auth.user
export const selectIsAuthenticated = (state: { auth: AuthState }) => state.auth.isAuthenticated
export const selectAuthLoading = (state: { auth: AuthState }) => state.auth.loading
export const selectAuthError = (state: { auth: AuthState }) => state.auth.error

export default authSlice.reducer
