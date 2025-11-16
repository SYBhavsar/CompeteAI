import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { configureStore } from '@reduxjs/toolkit'
import { Provider } from 'react-redux'
import CompetitorsPage from '../page'
import authReducer from '@/features/auth/authSlice'
import competitorsReducer from '@/features/competitors/competitorsSlice'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

// Mock next/navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
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

describe('Competitors List Page', () => {
  beforeEach(() => {
    resetMockApi()
    jest.clearAllMocks()
  })

  it('should render empty state when no competitors exist', async () => {
    mockApi.onGet('/competitors').reply(200, [])

    const store = createTestStore()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    // Wait for empty state
    await waitFor(() => {
      expect(screen.getByText(/no competitors found/i)).toBeInTheDocument()
    })

    // Should show Add Competitor buttons (header + empty state)
    expect(screen.getAllByRole('button', { name: /add competitor/i }).length).toBeGreaterThan(0)
  })

  it('should render list of competitors in a table', async () => {
    const mockCompetitors = [
      {
        id: 1,
        name: 'Competitor A',
        domain: 'competitora.com',
        industry: 'Technology',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        name: 'Competitor B',
        domain: 'competitorb.com',
        industry: 'Finance',
        user_id: 1,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ]

    mockApi.onGet('/competitors').reply(200, mockCompetitors)

    const store = createTestStore()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    // Wait for competitors to load (both mobile and desktop views render)
    await waitFor(() => {
      expect(screen.getAllByText('Competitor A').length).toBeGreaterThan(0)
    })

    expect(screen.getAllByText('Competitor B').length).toBeGreaterThan(0)
    expect(screen.getAllByText('competitora.com').length).toBeGreaterThan(0)
    expect(screen.getAllByText('competitorb.com').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Technology').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Finance').length).toBeGreaterThan(0)
  })

  it('should show table headers: Name, Domain, Industry, Created, Actions', async () => {
    const mockCompetitors = [
      {
        id: 1,
        name: 'Competitor A',
        domain: 'competitora.com',
        industry: 'Technology',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    mockApi.onGet('/competitors').reply(200, mockCompetitors)

    const store = createTestStore()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText('Name')).toBeInTheDocument()
    })

    expect(screen.getByText('Domain')).toBeInTheDocument()
    expect(screen.getByText('Industry')).toBeInTheDocument()
    expect(screen.getByText(/created/i)).toBeInTheDocument()
    expect(screen.getByText('Actions')).toBeInTheDocument()
  })

  it('should navigate to competitor detail page when row is clicked', async () => {
    const mockCompetitors = [
      {
        id: 1,
        name: 'Competitor A',
        domain: 'competitora.com',
        industry: 'Technology',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    mockApi.onGet('/competitors').reply(200, mockCompetitors)

    const store = createTestStore()
    const user = userEvent.setup()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    // Wait for competitor to load (both mobile and desktop views render)
    await waitFor(() => {
      expect(screen.getAllByText('Competitor A').length).toBeGreaterThan(0)
    })

    // Click on the row to view details (get all view buttons, click the first one)
    const viewButtons = screen.getAllByRole('button', { name: /view/i })
    await user.click(viewButtons[0])

    expect(mockPush).toHaveBeenCalledWith('/dashboard/competitors/1')
  })

  it('should open Add Competitor modal when Add button is clicked', async () => {
    mockApi.onGet('/competitors').reply(200, [])

    const store = createTestStore()
    const user = userEvent.setup()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /add competitor/i }).length).toBeGreaterThan(0)
    })

    const addButtons = screen.getAllByRole('button', { name: /add competitor/i })
    await user.click(addButtons[0])

    // Should show modal with form
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/domain/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/industry/i)).toBeInTheDocument()
  })

  it('should delete competitor when delete button is clicked and confirmed', async () => {
    const mockCompetitors = [
      {
        id: 1,
        name: 'Competitor A',
        domain: 'competitora.com',
        industry: 'Technology',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]

    mockApi.onGet('/competitors').replyOnce(200, mockCompetitors)
    mockApi.onDelete('/competitors/1').reply(200)
    mockApi.onGet('/competitors').reply(200, []) // After delete

    const store = createTestStore()
    const user = userEvent.setup()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    // Wait for competitor to load (both mobile and desktop views render)
    await waitFor(() => {
      expect(screen.getAllByText('Competitor A').length).toBeGreaterThan(0)
    })

    // Click delete button (get all delete buttons, click the first one)
    const deleteButtons = screen.getAllByRole('button', { name: 'Delete' })
    await user.click(deleteButtons[0])

    // Wait for the delete confirmation modal to appear (lazy-loaded with Suspense)
    // AlertDialog uses role="alertdialog" not "dialog"
    await waitFor(() => {
      expect(screen.getByText('Delete Competitor')).toBeInTheDocument()
    })

    // Confirm deletion
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /confirm/i })).toBeInTheDocument()
    })
    const confirmButton = screen.getByRole('button', { name: /confirm/i })
    await user.click(confirmButton)

    // Competitor should be removed
    await waitFor(() => {
      expect(screen.queryByText('Competitor A')).not.toBeInTheDocument()
    })
  })

  it('should show error message when fetching competitors fails', async () => {
    mockApi.onGet('/competitors').reply(500, { detail: 'Server error' })

    const store = createTestStore()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('should filter competitors by search input and display only matching results', async () => {
    const mockCompetitors = [
      {
        id: 1,
        name: 'TechCorp',
        domain: 'techcorp.com',
        industry: 'Technology',
        user_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: 2,
        name: 'FinanceHub',
        domain: 'financehub.com',
        industry: 'Finance',
        user_id: 1,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
      {
        id: 3,
        name: 'TechStart',
        domain: 'techstart.io',
        industry: 'Technology',
        user_id: 1,
        created_at: '2024-01-03T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
      },
    ]

    mockApi.onGet('/competitors').reply(200, mockCompetitors)

    const store = createTestStore()
    const user = userEvent.setup()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    // Wait for all competitors to load (both mobile and desktop views render)
    await waitFor(() => {
      expect(screen.getAllByText('TechCorp').length).toBeGreaterThan(0)
    })

    expect(screen.getAllByText('FinanceHub').length).toBeGreaterThan(0)
    expect(screen.getAllByText('TechStart').length).toBeGreaterThan(0)

    const searchInput = screen.getByPlaceholderText(/search competitors/i)
    await user.type(searchInput, 'Tech')

    await waitFor(() => {
      expect(screen.getAllByText('TechCorp').length).toBeGreaterThan(0)
      expect(screen.getAllByText('TechStart').length).toBeGreaterThan(0)
      expect(screen.queryByText('FinanceHub')).not.toBeInTheDocument()
    })

    await user.clear(searchInput)
    await user.type(searchInput, 'Finance')

    await waitFor(() => {
      expect(screen.getAllByText('FinanceHub').length).toBeGreaterThan(0)
      expect(screen.queryByText('TechCorp')).not.toBeInTheDocument()
      expect(screen.queryByText('TechStart')).not.toBeInTheDocument()
    })
  })

  it('should handle pagination when competitors exceed page limit', async () => {
    const mockCompetitors = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      name: `Competitor ${i + 1}`,
      domain: `competitor${i + 1}.com`,
      industry: 'Technology',
      user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }))

    mockApi.onGet('/competitors').reply(200, mockCompetitors)

    const store = createTestStore()
    const user = userEvent.setup()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    // Wait for first page to load (both mobile and desktop views render)
    await waitFor(() => {
      expect(screen.getAllByText('Competitor 1').length).toBeGreaterThan(0)
    })

    expect(screen.getAllByText('Competitor 10').length).toBeGreaterThan(0)
    expect(screen.queryByText('Competitor 11')).not.toBeInTheDocument()

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    await waitFor(() => {
      expect(screen.getAllByText('Competitor 11').length).toBeGreaterThan(0)
    })

    expect(screen.getAllByText('Competitor 20').length).toBeGreaterThan(0)
    expect(screen.queryByText('Competitor 1')).not.toBeInTheDocument()

    const prevButton = screen.getByRole('button', { name: /previous/i })
    await user.click(prevButton)

    await waitFor(() => {
      expect(screen.getAllByText('Competitor 1').length).toBeGreaterThan(0)
    })
  })

  it('should combine search and pagination correctly', async () => {
    const mockCompetitors = Array.from({ length: 25 }, (_, i) => ({
      id: i + 1,
      name: i % 2 === 0 ? `TechCorp ${i + 1}` : `FinanceHub ${i + 1}`,
      domain: `company${i + 1}.com`,
      industry: i % 2 === 0 ? 'Technology' : 'Finance',
      user_id: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }))

    mockApi.onGet('/competitors').reply(200, mockCompetitors)

    const store = createTestStore()
    const user = userEvent.setup()

    render(
      <Provider store={store}>
        <CompetitorsPage />
      </Provider>
    )

    // Wait for competitors to load (both mobile and desktop views render)
    await waitFor(() => {
      expect(screen.getAllByText('TechCorp 1').length).toBeGreaterThan(0)
    })

    const searchInput = screen.getByPlaceholderText(/search competitors/i)
    await user.type(searchInput, 'Tech')

    await waitFor(() => {
      expect(screen.getAllByText('TechCorp 1').length).toBeGreaterThan(0)
      expect(screen.queryByText('FinanceHub 2')).not.toBeInTheDocument()
    })

    expect(screen.getAllByText('TechCorp 19').length).toBeGreaterThan(0)
    expect(screen.queryByText('TechCorp 21')).not.toBeInTheDocument()

    const nextButton = screen.getByRole('button', { name: /next/i })
    await user.click(nextButton)

    await waitFor(() => {
      expect(screen.getAllByText('TechCorp 21').length).toBeGreaterThan(0)
    })

    expect(screen.queryByText('TechCorp 1')).not.toBeInTheDocument()
  })
})
