import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import SavedSearchesPage from '../page'
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

describe('Saved Searches Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
    mockPush.mockClear()
  })

  it('should render saved searches page', async () => {
    const store = createTestStore()

    mockApi.onGet('/search/saved').reply(200, [])

    render(
      <Provider store={store}>
        <SavedSearchesPage />
      </Provider>
    )

    expect(screen.getByText(/saved searches/i)).toBeInTheDocument()
  })

  it('should display list of saved searches', async () => {
    const store = createTestStore()

    const mockSavedSearches = [
      {
        id: 1,
        user_id: 1,
        name: 'My Search 1',
        search_type: 'semantic',
        query: 'test query',
        filters: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        user_id: 1,
        name: 'My Search 2',
        search_type: 'traditional',
        query: 'another query',
        filters: null,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ]

    mockApi.onGet('/search/saved').reply(200, mockSavedSearches)

    render(
      <Provider store={store}>
        <SavedSearchesPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText('My Search 1')).toBeInTheDocument()
    })

    expect(screen.getByText('My Search 2')).toBeInTheDocument()
    expect(screen.getByText('test query')).toBeInTheDocument()
    expect(screen.getByText('another query')).toBeInTheDocument()
  })

  it('should have execute button for each saved search', async () => {
    const store = createTestStore()

    const mockSavedSearches = [
      {
        id: 1,
        user_id: 1,
        name: 'My Search 1',
        search_type: 'semantic',
        query: 'test query',
        filters: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    mockApi.onGet('/search/saved').reply(200, mockSavedSearches)

    render(
      <Provider store={store}>
        <SavedSearchesPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /execute/i })).toBeInTheDocument()
    })
  })

  it('should navigate to search page when execute clicked', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    const mockSavedSearches = [
      {
        id: 1,
        user_id: 1,
        name: 'My Search 1',
        search_type: 'semantic',
        query: 'test query',
        filters: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    mockApi.onGet('/search/saved').reply(200, mockSavedSearches)

    render(
      <Provider store={store}>
        <SavedSearchesPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /execute/i })).toBeInTheDocument()
    })

    const executeButton = screen.getByRole('button', { name: /execute/i })
    await user.click(executeButton)

    expect(mockPush).toHaveBeenCalledWith('/dashboard/search')
  })

  it('should have delete button for each saved search', async () => {
    const store = createTestStore()

    const mockSavedSearches = [
      {
        id: 1,
        user_id: 1,
        name: 'My Search 1',
        search_type: 'semantic',
        query: 'test query',
        filters: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    mockApi.onGet('/search/saved').reply(200, mockSavedSearches)

    render(
      <Provider store={store}>
        <SavedSearchesPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })
  })

  it('should delete saved search', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    const mockSavedSearches = [
      {
        id: 1,
        user_id: 1,
        name: 'My Search 1',
        search_type: 'semantic',
        query: 'test query',
        filters: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    mockApi.onGet('/search/saved').reply(200, mockSavedSearches)
    mockApi.onDelete('/search/saved/1').reply(200)

    render(
      <Provider store={store}>
        <SavedSearchesPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText('My Search 1')).toBeInTheDocument()
    })

    const deleteButton = screen.getByRole('button', { name: /delete/i })
    await user.click(deleteButton)

    await waitFor(() => {
      expect(screen.queryByText('My Search 1')).not.toBeInTheDocument()
    })
  })

  it('should display empty state when no saved searches', async () => {
    const store = createTestStore()

    mockApi.onGet('/search/saved').reply(200, [])

    render(
      <Provider store={store}>
        <SavedSearchesPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/no saved searches/i)).toBeInTheDocument()
    })
  })
})
