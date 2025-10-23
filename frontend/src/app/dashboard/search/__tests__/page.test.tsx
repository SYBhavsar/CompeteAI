import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Provider } from 'react-redux'
import { configureStore } from '@reduxjs/toolkit'
import authReducer from '@/features/auth/authSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import SearchPage from '../page'
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
      competitors: competitorsReducer,
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
      competitors: {
        competitors: [],
        selectedCompetitor: null,
        dataSources: [],
        insights: [],
        loading: false,
        error: null,
      },
      ...initialState,
    },
  })
}

describe('Search Page - Integration Tests', () => {
  beforeEach(() => {
    resetMockApi()
    mockPush.mockClear()
  })

  it('should render search page with search input', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <SearchPage />
      </Provider>
    )

    expect(screen.getByPlaceholderText(/search insights/i)).toBeInTheDocument()
  })

  it('should toggle between semantic and traditional search', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <SearchPage />
      </Provider>
    )

    const semanticButton = screen.getByRole('button', { name: /semantic/i })
    const traditionalButton = screen.getByRole('button', { name: /traditional/i })

    expect(semanticButton).toHaveAttribute('data-active', 'true')
    expect(traditionalButton).toHaveAttribute('data-active', 'false')

    await user.click(traditionalButton)

    expect(semanticButton).toHaveAttribute('data-active', 'false')
    expect(traditionalButton).toHaveAttribute('data-active', 'true')
  })

  it('should display advanced filters panel', async () => {
    const store = createTestStore()

    mockApi.onGet('/competitors').reply(200, [])

    render(
      <Provider store={store}>
        <SearchPage />
      </Provider>
    )

    expect(screen.getByRole('heading', { name: /filters/i })).toBeInTheDocument()
    expect(screen.getByLabelText(/date range/i)).toBeInTheDocument()
  })

  it('should perform search and display results', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    const mockResults = [
      {
        id: 1,
        content: 'Test insight content',
        sentiment: 'positive',
        quality_score: 0.85,
        source: 'competitor1.com',
        created_at: '2024-01-01T00:00:00Z',
      },
    ]

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onPost('/search/semantic').reply(200, { results: mockResults, total: 1 })

    render(
      <Provider store={store}>
        <SearchPage />
      </Provider>
    )

    const searchInput = screen.getByPlaceholderText(/search insights/i)
    await user.type(searchInput, 'test query')

    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText('Test insight content')).toBeInTheDocument()
    })
  })

  it('should display empty state when no results', async () => {
    const store = createTestStore()
    const user = userEvent.setup()

    mockApi.onGet('/competitors').reply(200, [])
    mockApi.onPost('/search/semantic').reply(200, { results: [], total: 0 })

    render(
      <Provider store={store}>
        <SearchPage />
      </Provider>
    )

    const searchInput = screen.getByPlaceholderText(/search insights/i)
    await user.type(searchInput, 'nonexistent query')

    const searchButton = screen.getByRole('button', { name: /search/i })
    await user.click(searchButton)

    await waitFor(() => {
      expect(screen.getByText(/no results found/i)).toBeInTheDocument()
    })
  })
})
