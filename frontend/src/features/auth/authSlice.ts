import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { authService } from '@/services/authService'
import { User, LoginRequest, RegisterRequest, AuthResponse } from '@/types'
import api from '@/services/api'

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

/**
 * Update user profile
 */
export const updateUserAsync = createAsyncThunk<User, Partial<User>>(
  'auth/updateUser',
  async (data) => {
    const response = await api.put('/users/me', data)
    return response.data
  }
)

/**
 * Update user password
 */
export const updatePasswordAsync = createAsyncThunk<void, { current_password: string; new_password: string }>(
  'auth/updatePassword',
  async (data) => {
    await api.put('/users/me/password', data)
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

    // Update User
    builder
      .addCase(updateUserAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(updateUserAsync.fulfilled, (state, action: PayloadAction<User>) => {
        state.loading = false
        state.user = action.payload
      })
      .addCase(updateUserAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to update profile'
      })

    // Update Password
    builder
      .addCase(updatePasswordAsync.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(updatePasswordAsync.fulfilled, (state) => {
        state.loading = false
      })
      .addCase(updatePasswordAsync.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to change password'
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
