import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import CompetitorDetailPage from '../page'
import authReducer from '@/features/auth/authSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

// Mock next/navigation
const mockPush = jest.fn()
const mockParams = { id: '1' }

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useParams: () => mockParams,
}))

// Helper to create test store
const createTestStore = () => {
  return configureStore({
    reducer: {
      auth: authReducer,
      competitors: competitorsReducer,
    },
  })
}

describe('Competitor Detail Page', () => {
  beforeEach(() => {
    resetMockApi()
    jest.clearAllMocks()
  })

  it('should fetch and display competitor details', async () => {
    const mockCompetitor = {
      id: 1,
      name: 'Competitor A',
      domain: 'https://competitora.com',
      industry: 'Technology',
      user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    mockApi.onGet('/competitors/1').reply(200, mockCompetitor)

    const store = createTestStore()

    render(
      <Provider store={store}>
        <CompetitorDetailPage />
      </Provider>
    )

    // Should show loading initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    // Wait for competitor details to load
    await waitFor(() => {
      expect(screen.getAllByText('Competitor A').length).toBeGreaterThan(0)
    })
 
    expect(screen.getAllByText('https://competitora.com').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Technology').length).toBeGreaterThan(0)
  })

  it('should display stats cards: data sources count, last scraped, insights count', async () => {
    const mockCompetitor = {
      id: 1,
      name: 'Competitor A',
      domain: 'https://competitora.com',
      industry: 'Technology',
      user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    const mockDataSources = [
      {
        id: 1,
        competitor_id: 1,
        source_type: 'website',
        url: 'https://competitora.com/blog',
        is_active: true,
        last_scraped: '2024-01-15T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      {
        id: 2,
        competitor_id: 1,
        source_type: 'twitter',
        url: 'https://twitter.com/competitora',
        is_active: true,
        last_scraped: '2024-01-14T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-14T10:00:00Z',
      },
    ]

    mockApi.onGet('/competitors/1').reply(200, mockCompetitor)
    mockApi.onGet('/competitors/1/sources').reply(200, mockDataSources)
    mockApi.onGet('/competitors/1/insights').reply(200, []) // Empty insights for now

    const store = createTestStore()

    render(
      <Provider store={store}>
        <CompetitorDetailPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getAllByText(/data sources/i).length).toBeGreaterThan(0)
    })

    // Should show 2 data sources
    expect(screen.getByText('2')).toBeInTheDocument()

    // Should show last scraped date
    expect(screen.getByText(/last scraped/i)).toBeInTheDocument()
  })

  it('should render tabs: Overview, Data Sources, Insights, Scraped Data', async () => {
    const mockCompetitor = {
      id: 1,
      name: 'Competitor A',
      domain: 'https://competitora.com',
      industry: 'Technology',
      user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    mockApi.onGet('/competitors/1').reply(200, mockCompetitor)
    mockApi.onGet('/competitors/1/sources').reply(200, [])
    mockApi.onGet('/competitors/1/insights').reply(200, [])

    const store = createTestStore()

    render(
      <Provider store={store}>
        <CompetitorDetailPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument()
    })

    expect(screen.getByRole('tab', { name: /data sources/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /insights/i })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /scraped data/i })).toBeInTheDocument()
  })

  it('should switch tabs when clicked', async () => {
    const mockCompetitor = {
      id: 1,
      name: 'Competitor A',
      domain: 'https://competitora.com',
      industry: 'Technology',
      user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    mockApi.onGet('/competitors/1').reply(200, mockCompetitor)
    mockApi.onGet('/competitors/1/sources').reply(200, [])
    mockApi.onGet('/competitors/1/insights').reply(200, [])

    const store = createTestStore()
    const user = userEvent.setup()

    render(
      <Provider store={store}>
        <CompetitorDetailPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('tab', { name: /overview/i })).toBeInTheDocument()
    })

    // Click on Data Sources tab
    const dataSourcesTab = screen.getByRole('tab', { name: /data sources/i })
    await user.click(dataSourcesTab)

    // Should show data sources content (Add Data Source button appears)
    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /add data source/i }).length).toBeGreaterThan(0)
    })
  })

  it('should show Edit and Delete actions in header', async () => {
    const mockCompetitor = {
      id: 1,
      name: 'Competitor A',
      domain: 'https://competitora.com',
      industry: 'Technology',
      user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    mockApi.onGet('/competitors/1').reply(200, mockCompetitor)
    mockApi.onGet('/competitors/1/sources').reply(200, [])
    mockApi.onGet('/competitors/1/insights').reply(200, [])

    const store = createTestStore()

    render(
      <Provider store={store}>
        <CompetitorDetailPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument()
    })

    expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
  })

  it('should open edit modal when Edit button is clicked', async () => {
    const mockCompetitor = {
      id: 1,
      name: 'Competitor A',
      domain: 'https://competitora.com',
      industry: 'Technology',
      user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    mockApi.onGet('/competitors/1').reply(200, mockCompetitor)
    mockApi.onGet('/competitors/1/sources').reply(200, [])
    mockApi.onGet('/competitors/1/insights').reply(200, [])

    const store = createTestStore()
    const user = userEvent.setup()

    render(
      <Provider store={store}>
        <CompetitorDetailPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /edit/i })).toBeInTheDocument()
    })

    const editButton = screen.getByRole('button', { name: /edit/i })
    await user.click(editButton)

    // Should show edit modal
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByDisplayValue('Competitor A')).toBeInTheDocument()
    })
  })

  it('should redirect to competitors list after deleting competitor', async () => {
    const mockCompetitor = {
      id: 1,
      name: 'Competitor A',
      domain: 'https://competitora.com',
      industry: 'Technology',
      user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }

    mockApi.onGet('/competitors/1').reply(200, mockCompetitor)
    mockApi.onGet('/competitors/1/sources').reply(200, [])
    mockApi.onGet('/competitors/1/insights').reply(200, [])
    mockApi.onDelete('/competitors/1').reply(200)

    const store = createTestStore()
    const user = userEvent.setup()

    render(
      <Provider store={store}>
        <CompetitorDetailPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument()
    })

    const deleteButton = screen.getByRole('button', { name: /delete/i })
    await user.click(deleteButton)

    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /confirm/i })
    await user.click(confirmButton)

    // Should redirect to competitors list
    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('/dashboard/competitors')
    })
  })

  it('should show error message when fetching competitor fails', async () => {
    mockApi.onGet('/competitors/1').reply(404, { detail: 'Competitor not found' })

    const store = createTestStore()

    render(
      <Provider store={store}>
        <CompetitorDetailPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })
})
