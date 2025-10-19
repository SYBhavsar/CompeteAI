import api from './api'
import { LoginRequest, RegisterRequest, AuthResponse, User } from '@/types'

const TOKEN_KEY = 'auth_token'

export const authService = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/login', credentials)
    return response.data
  },

  /**
   * Register a new user
   */
  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await api.post<AuthResponse>('/auth/register', data)
    return response.data
  },

  /**
   * Logout user and clear token
   */
  logout(): void {
    this.removeToken()
  },

  /**
   * Save auth token to localStorage
   */
  saveToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  },

  /**
   * Get auth token from localStorage
   */
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },

  /**
   * Remove auth token from localStorage
   */
  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY)
  },
}
