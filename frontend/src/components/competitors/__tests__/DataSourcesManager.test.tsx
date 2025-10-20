import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DataSourcesManager from '../DataSourcesManager'
import { mockApi, resetMockApi } from '@/tests/helpers/mockApi'

describe('DataSourcesManager Component', () => {
  const competitorId = 1

  beforeEach(() => {
    resetMockApi()
    jest.clearAllMocks()
  })

  it('should display list of data sources', async () => {
    const mockDataSources = [
      {
        id: 1,
        competitor_id: 1,
        source_type: 'website',
        url: 'https://competitor.com/blog',
        is_active: true,
        last_scraped: '2024-01-15T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      {
        id: 2,
        competitor_id: 1,
        source_type: 'twitter',
        url: 'https://twitter.com/competitor',
        is_active: false,
        last_scraped: null,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ]

    mockApi.onGet('/competitors/1/sources').reply(200, mockDataSources)

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getByText('website')).toBeInTheDocument()
    })

    expect(screen.getByText('https://competitor.com/blog')).toBeInTheDocument()
    expect(screen.getByText('twitter')).toBeInTheDocument()
    expect(screen.getByText('https://twitter.com/competitor')).toBeInTheDocument()
  })

  it('should show active/inactive status for each data source', async () => {
    const mockDataSources = [
      {
        id: 1,
        competitor_id: 1,
        source_type: 'website',
        url: 'https://competitor.com/blog',
        is_active: true,
        last_scraped: '2024-01-15T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
      {
        id: 2,
        competitor_id: 1,
        source_type: 'twitter',
        url: 'https://twitter.com/competitor',
        is_active: false,
        last_scraped: null,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ]

    mockApi.onGet('/competitors/1/sources').reply(200, mockDataSources)

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    expect(screen.getByText('Inactive')).toBeInTheDocument()
  })

  it('should display empty state when no data sources exist', async () => {
    mockApi.onGet('/competitors/1/sources').reply(200, [])

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getByText(/no data sources/i)).toBeInTheDocument()
    })

    expect(screen.getAllByRole('button', { name: /add data source/i }).length).toBeGreaterThan(0)
  })

  it('should open Add Data Source modal when Add button is clicked', async () => {
    mockApi.onGet('/competitors/1/sources').reply(200, [])

    const user = userEvent.setup()

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /add data source/i }).length).toBeGreaterThan(0)
    })

    const addButtons = screen.getAllByRole('button', { name: /add data source/i })
    await user.click(addButtons[0])

    // Should show modal with form
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    expect(screen.getByLabelText(/source type/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/url/i)).toBeInTheDocument()
  })

  it('should create new data source when form is submitted', async () => {
    mockApi.onGet('/competitors/1/sources').replyOnce(200, [])
    mockApi.onPost('/competitors/1/sources').reply(200, {
      id: 1,
      competitor_id: 1,
      source_type: 'website',
      url: 'https://newsite.com',
      is_active: true,
      last_scraped: null,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    })
    mockApi.onGet('/competitors/1/sources').reply(200, [
      {
        id: 1,
        competitor_id: 1,
        source_type: 'website',
        url: 'https://newsite.com',
        is_active: true,
        last_scraped: null,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ])

    const user = userEvent.setup()

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /add data source/i }).length).toBeGreaterThan(0)
    })

    // Open modal
    const addButtons = screen.getAllByRole('button', { name: /add data source/i })
    await user.click(addButtons[0])

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // Fill form
    const sourceTypeInput = screen.getByLabelText(/source type/i)
    const urlInput = screen.getByLabelText(/url/i)

    await user.type(sourceTypeInput, 'website')
    await user.type(urlInput, 'https://newsite.com')

    // Submit
    const submitButton = screen.getByRole('button', { name: /create/i })
    await user.click(submitButton)

    // Should close modal and show new data source
    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    })

    await waitFor(() => {
      expect(screen.getByText('https://newsite.com')).toBeInTheDocument()
    })
  })

  it('should validate required fields when creating data source', async () => {
    mockApi.onGet('/competitors/1/sources').reply(200, [])

    const user = userEvent.setup()

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getAllByRole('button', { name: /add data source/i }).length).toBeGreaterThan(0)
    })

    // Open modal
    const addButtons = screen.getAllByRole('button', { name: /add data source/i })
    await user.click(addButtons[0])

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    // Try to submit without filling form
    const submitButton = screen.getByRole('button', { name: /create/i })
    await user.click(submitButton)

    // Should show validation errors
    await waitFor(() => {
      expect(screen.getByText(/source type is required/i)).toBeInTheDocument()
    })

    expect(screen.getByText(/url is required/i)).toBeInTheDocument()
  })

  it('should open Edit Data Source modal when edit button is clicked', async () => {
    const mockDataSources = [
      {
        id: 1,
        competitor_id: 1,
        source_type: 'website',
        url: 'https://competitor.com/blog',
        is_active: true,
        last_scraped: '2024-01-15T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
    ]

    mockApi.onGet('/competitors/1/sources').reply(200, mockDataSources)

    const user = userEvent.setup()

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getByText('website')).toBeInTheDocument()
    })

    // Click edit button
    const editButton = screen.getByRole('button', { name: /edit/i })
    await user.click(editButton)

    // Should show modal with pre-filled form
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })

    expect(screen.getByDisplayValue('website')).toBeInTheDocument()
    expect(screen.getByDisplayValue('https://competitor.com/blog')).toBeInTheDocument()
  })

  it('should delete data source when delete button is clicked and confirmed', async () => {
    const mockDataSources = [
      {
        id: 1,
        competitor_id: 1,
        source_type: 'website',
        url: 'https://competitor.com/blog',
        is_active: true,
        last_scraped: '2024-01-15T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
    ]

    mockApi.onGet('/competitors/1/sources').replyOnce(200, mockDataSources)
    mockApi.onDelete('/competitors/1/sources/1').reply(200)
    mockApi.onGet('/competitors/1/sources').reply(200, [])

    const user = userEvent.setup()

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getByText('website')).toBeInTheDocument()
    })

    // Click delete button
    const deleteButton = screen.getByRole('button', { name: /delete/i })
    await user.click(deleteButton)

    // Confirm deletion
    const confirmButton = screen.getByRole('button', { name: /confirm/i })
    await user.click(confirmButton)

    // Data source should be removed
    await waitFor(() => {
      expect(screen.queryByText('website')).not.toBeInTheDocument()
    })

    expect(screen.getByText(/no data sources/i)).toBeInTheDocument()
  })

  it('should toggle data source active status', async () => {
    const mockDataSources = [
      {
        id: 1,
        competitor_id: 1,
        source_type: 'website',
        url: 'https://competitor.com/blog',
        is_active: true,
        last_scraped: '2024-01-15T10:00:00Z',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:00:00Z',
      },
    ]

    mockApi.onGet('/competitors/1/sources').replyOnce(200, mockDataSources)
    mockApi.onPut('/competitors/1/sources/1').reply(200, {
      ...mockDataSources[0],
      is_active: false,
    })
    mockApi.onGet('/competitors/1/sources').reply(200, [
      {
        ...mockDataSources[0],
        is_active: false,
      },
    ])

    const user = userEvent.setup()

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument()
    })

    // Click toggle button
    const toggleButton = screen.getByRole('button', { name: /toggle/i })
    await user.click(toggleButton)

    // Status should change to Inactive
    await waitFor(() => {
      expect(screen.getByText('Inactive')).toBeInTheDocument()
    })

    expect(screen.queryByText('Active')).not.toBeInTheDocument()
  })

  it('should show error message when fetching data sources fails', async () => {
    mockApi.onGet('/competitors/1/sources').reply(500, { detail: 'Server error' })

    render(<DataSourcesManager competitorId={competitorId} />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })
})
