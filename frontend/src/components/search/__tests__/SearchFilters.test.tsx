import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchFilters from '../SearchFilters'
import { Competitor } from '@/types'

const mockCompetitors: Competitor[] = [
  {
    id: 1,
    name: 'Competitor 1',
    domain: 'competitor1.com',
    industry: 'Tech',
    user_id: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    name: 'Competitor 2',
    domain: 'competitor2.com',
    industry: 'Finance',
    user_id: 1,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
]

describe('SearchFilters Component', () => {
  const mockOnFilterChange = jest.fn()

  beforeEach(() => {
    mockOnFilterChange.mockClear()
  })

  it('should render all filter options', () => {
    render(
      <SearchFilters
        competitors={mockCompetitors}
        onFilterChange={mockOnFilterChange}
      />
    )

    expect(screen.getByLabelText(/date range/i)).toBeInTheDocument()
    expect(screen.getByRole('combobox', { name: /competitor/i })).toBeInTheDocument()
    expect(screen.getByRole('radiogroup', { name: /sentiment/i })).toBeInTheDocument()
  })

  it('should update date range filter', async () => {
    const user = userEvent.setup()

    render(
      <SearchFilters
        competitors={mockCompetitors}
        onFilterChange={mockOnFilterChange}
      />
    )

    const dateInput = screen.getByLabelText(/date range/i)
    await user.type(dateInput, '2024-01-01')

    expect(mockOnFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({
        dateFrom: '2024-01-01',
      })
    )
  })

  it('should render competitor select dropdown', () => {
    render(
      <SearchFilters
        competitors={mockCompetitors}
        onFilterChange={mockOnFilterChange}
      />
    )

    expect(screen.getByRole('combobox', { name: /competitor/i })).toBeInTheDocument()
  })

  it('should select sentiment filter', async () => {
    const user = userEvent.setup()

    render(
      <SearchFilters
        competitors={mockCompetitors}
        onFilterChange={mockOnFilterChange}
      />
    )

    const positiveRadio = screen.getByRole('radio', { name: /positive/i })
    await user.click(positiveRadio)

    expect(mockOnFilterChange).toHaveBeenCalledWith(
      expect.objectContaining({
        sentiment: 'positive',
      })
    )
  })

  it('should clear all filters', async () => {
    const user = userEvent.setup()

    render(
      <SearchFilters
        competitors={mockCompetitors}
        onFilterChange={mockOnFilterChange}
      />
    )

    const clearButton = screen.getByRole('button', { name: /clear filters/i })
    await user.click(clearButton)

    expect(mockOnFilterChange).toHaveBeenCalledWith({
      dateFrom: null,
      dateTo: null,
      competitorIds: [],
      sentiment: null,
    })
  })

  it('should render with empty competitors list', () => {
    render(
      <SearchFilters
        competitors={[]}
        onFilterChange={mockOnFilterChange}
      />
    )

    expect(screen.getByRole('combobox', { name: /competitor/i })).toBeInTheDocument()
  })
})
