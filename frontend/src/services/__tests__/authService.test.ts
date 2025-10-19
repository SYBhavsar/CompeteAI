import { authService } from '../authService'
import { LoginRequest, RegisterRequest } from '@/types'
import { mockApi, resetMockApi, restoreMockApi } from '@/tests/helpers/mockApi'

describe('authService', () => {
  beforeEach(() => {
    resetMockApi()
    localStorage.clear()
  })

  afterAll(() => {
    restoreMockApi()
  })

  describe('login', () => {
    it('should login with valid credentials and return access token and user data', async () => {
      const credentials: LoginRequest = {
        email: 'test@example.com',
        password: 'password123',
      }

      const mockResponse = {
        access_token: 'mock-token-123',
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

      const response = await authService.login(credentials)

      expect(response.access_token).toBe('mock-token-123')
      expect(response.token_type).toBe('bearer')
      expect(response.user.email).toBe('test@example.com')
      expect(response.user.full_name).toBe('Test User')
    })

    it('should throw 401 error with invalid credentials', async () => {
      const credentials: LoginRequest = {
        email: 'wrong@example.com',
        password: 'wrongpassword',
      }

      mockApi.onPost('/auth/login').reply(401, { detail: 'Invalid credentials' })

      await expect(authService.login(credentials)).rejects.toThrow()
    })
  })

  describe('register', () => {
    it('should register with valid data and return token and user', async () => {
      const registerData: RegisterRequest = {
        email: 'newuser@example.com',
        password: 'password123',
        full_name: 'New User',
      }

      const mockResponse = {
        access_token: 'mock-token-new-user',
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

      const response = await authService.register(registerData)

      expect(response.access_token).toBe('mock-token-new-user')
      expect(response.user.email).toBe('newuser@example.com')
      expect(response.user.full_name).toBe('New User')
    })

    it('should throw 400 error when email already exists', async () => {
      const registerData: RegisterRequest = {
        email: 'existing@example.com',
        password: 'password123',
        full_name: 'Existing User',
      }

      mockApi.onPost('/auth/register').reply(400, { detail: 'Email already registered' })

      await expect(authService.register(registerData)).rejects.toThrow()
    })
  })

  describe('logout', () => {
    it('should clear auth token from localStorage', () => {
      const removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem')
      localStorage.setItem('auth_token', 'mock-token')

      authService.logout()

      expect(removeItemSpy).toHaveBeenCalledWith('auth_token')
      removeItemSpy.mockRestore()
    })
  })

  describe('token management', () => {
    it('should save token to localStorage', () => {
      const setItemSpy = jest.spyOn(Storage.prototype, 'setItem')

      authService.saveToken('test-token-123')

      expect(setItemSpy).toHaveBeenCalledWith('auth_token', 'test-token-123')
      setItemSpy.mockRestore()
    })

    it('should get token from localStorage', () => {
      const getItemSpy = jest.spyOn(Storage.prototype, 'getItem').mockReturnValue('stored-token')

      const token = authService.getToken()

      expect(token).toBe('stored-token')
      expect(getItemSpy).toHaveBeenCalledWith('auth_token')
      getItemSpy.mockRestore()
    })

    it('should remove token from localStorage', () => {
      const removeItemSpy = jest.spyOn(Storage.prototype, 'removeItem')

      authService.removeToken()

      expect(removeItemSpy).toHaveBeenCalledWith('auth_token')
      removeItemSpy.mockRestore()
    })
  })
})
