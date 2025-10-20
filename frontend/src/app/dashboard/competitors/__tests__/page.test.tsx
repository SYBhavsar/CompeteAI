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

    // Should show loading initially
    expect(screen.getByText(/loading/i)).toBeInTheDocument()

    // Wait for empty state
    await waitFor(() => {
      expect(screen.getByText(/no competitors/i)).toBeInTheDocument()
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

    // Wait for competitors to load
    await waitFor(() => {
      expect(screen.getByText('Competitor A')).toBeInTheDocument()
    })

    expect(screen.getByText('Competitor B')).toBeInTheDocument()
    expect(screen.getByText('competitora.com')).toBeInTheDocument()
    expect(screen.getByText('competitorb.com')).toBeInTheDocument()
    expect(screen.getByText('Technology')).toBeInTheDocument()
    expect(screen.getByText('Finance')).toBeInTheDocument()
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

    // Wait for competitor to load
    await waitFor(() => {
      expect(screen.getByText('Competitor A')).toBeInTheDocument()
    })

    // Click on the row to view details
    const viewButton = screen.getByRole('button', { name: /view/i })
    await user.click(viewButton)

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

    // Wait for competitor to load
    await waitFor(() => {
      expect(screen.getByText('Competitor A')).toBeInTheDocument()
    })

    // Click delete button
    const deleteButton = screen.getByRole('button', { name: /delete/i })
    await user.click(deleteButton)

    // Confirm deletion
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
})
