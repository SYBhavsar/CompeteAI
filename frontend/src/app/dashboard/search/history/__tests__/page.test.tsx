import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import SearchHistoryPage from '../page'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

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
      ...initialState,
    },
  })
}

describe('Search History Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
    mockPush.mockClear()
  })

  it('should render search history page', async () => {
    const store = createTestStore()

    mockApi.onGet('/search/history').reply(200, [])

    render(
      <Provider store={store}>
        <SearchHistoryPage />
      </Provider>
    )

    expect(screen.getByText(/search history/i)).toBeInTheDocument()
  })

  it('should display list of search history', async () => {
    const store = createTestStore()

    const mockHistory = [
      {
        id: 1,
        user_id: 1,
        search_type: 'semantic',
        query: 'test query 1',
        filters: null,
        results_count: 10,
        executed_at: '2024-01-15T10:30:00Z',
      },
      {
        id: 2,
        user_id: 1,
        search_type: 'traditional',
        query: 'test query 2',
        filters: null,
        results_count: 5,
        executed_at: '2024-01-14T09:20:00Z',
      },
    ]

    mockApi.onGet('/search/history').reply(200, mockHistory)

    render(
      <Provider store={store}>
        <SearchHistoryPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText('test query 1')).toBeInTheDocument()
    })

    expect(screen.getByText('test query 2')).toBeInTheDocument()
    expect(screen.getByText(/10 results/i)).toBeInTheDocument()
    expect(screen.getByText(/5 results/i)).toBeInTheDocument()
  })

  it('should have re-run button for each history item', async () => {
    const store = createTestStore()

    const mockHistory = [
      {
        id: 1,
        user_id: 1,
        search_type: 'semantic',
        query: 'test query 1',
        filters: null,
        results_count: 10,
        executed_at: '2024-01-15T10:30:00Z',
      },
    ]

    mockApi.onGet('/search/history').reply(200, mockHistory)

    render(
      <Provider store={store}>
        <SearchHistoryPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /re-run/i })).toBeInTheDocument()
    })
  })

  it('should navigate to search page when re-run clicked', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    const mockHistory = [
      {
        id: 1,
        user_id: 1,
        search_type: 'semantic',
        query: 'test query 1',
        filters: null,
        results_count: 10,
        executed_at: '2024-01-15T10:30:00Z',
      },
    ]

    mockApi.onGet('/search/history').reply(200, mockHistory)

    render(
      <Provider store={store}>
        <SearchHistoryPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /re-run/i })).toBeInTheDocument()
    })

    const rerunButton = screen.getByRole('button', { name: /re-run/i })
    await user.click(rerunButton)

    expect(mockPush).toHaveBeenCalledWith('/dashboard/search')
  })

  it('should have clear history button', async () => {
    const store = createTestStore()

    const mockHistory = [
      {
        id: 1,
        user_id: 1,
        search_type: 'semantic',
        query: 'test query 1',
        filters: null,
        results_count: 10,
        executed_at: '2024-01-15T10:30:00Z',
      },
    ]

    mockApi.onGet('/search/history').reply(200, mockHistory)

    render(
      <Provider store={store}>
        <SearchHistoryPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /clear history/i })).toBeInTheDocument()
    })
  })

  it('should clear all history', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    const mockHistory = [
      {
        id: 1,
        user_id: 1,
        search_type: 'semantic',
        query: 'test query 1',
        filters: null,
        results_count: 10,
        executed_at: '2024-01-15T10:30:00Z',
      },
    ]

    mockApi.onGet('/search/history').reply(200, mockHistory)
    mockApi.onDelete('/search/history').reply(200)

    render(
      <Provider store={store}>
        <SearchHistoryPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText('test query 1')).toBeInTheDocument()
    })

    const clearButton = screen.getByRole('button', { name: /clear history/i })
    await user.click(clearButton)

    await waitFor(() => {
      expect(screen.getByText(/no search history/i)).toBeInTheDocument()
    })
  })

  it('should display empty state when no history', async () => {
    const store = createTestStore()

    mockApi.onGet('/search/history').reply(200, [])

    render(
      <Provider store={store}>
        <SearchHistoryPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/no search history/i)).toBeInTheDocument()
    })
  })

  it('should display searches in chronological order', async () => {
    const store = createTestStore()

    const mockHistory = [
      {
        id: 1,
        user_id: 1,
        search_type: 'semantic',
        query: 'newest query',
        filters: null,
        results_count: 10,
        executed_at: '2024-01-15T10:30:00Z',
      },
      {
        id: 2,
        user_id: 1,
        search_type: 'traditional',
        query: 'older query',
        filters: null,
        results_count: 5,
        executed_at: '2024-01-14T09:20:00Z',
      },
    ]

    mockApi.onGet('/search/history').reply(200, mockHistory)

    render(
      <Provider store={store}>
        <SearchHistoryPage />
      </Provider>
    )

    await waitFor(() => {
      const queries = screen.getAllByText(/query/)
      expect(queries[0]).toHaveTextContent('newest query')
      expect(queries[1]).toHaveTextContent('older query')
    })
  })
})
