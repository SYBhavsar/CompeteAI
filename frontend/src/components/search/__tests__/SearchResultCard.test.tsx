import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import SearchResultCard from '../SearchResultCard'

const mockResult = {
  id: 1,
  content: 'This is a test insight about competitor activities',
  summary: 'Test summary',
  key_points: ['Point 1', 'Point 2'],
  sentiment: 'positive' as const,
  quality_score: 0.85,
  source: 'competitor1.com',
  created_at: '2024-01-15T10:30:00Z',
  relevance_score: 0.92,
}

describe('SearchResultCard Component', () => {
  it('should render result content', () => {
    render(<SearchResultCard result={mockResult} />)

    expect(screen.getByText(/test insight about competitor activities/i)).toBeInTheDocument()
  })

  it('should display sentiment badge with correct color', () => {
    render(<SearchResultCard result={mockResult} />)

    const sentimentBadge = screen.getByText('positive')
    expect(sentimentBadge).toBeInTheDocument()
  })

  it('should display quality score', () => {
    render(<SearchResultCard result={mockResult} />)

    expect(screen.getByText(/0\.85/)).toBeInTheDocument()
  })

  it('should display source information', () => {
    render(<SearchResultCard result={mockResult} />)

    expect(screen.getByText(/competitor1\.com/)).toBeInTheDocument()
  })

  it('should display formatted date', () => {
    render(<SearchResultCard result={mockResult} />)

    expect(screen.getByText(/1\/15\/2024/)).toBeInTheDocument()
  })

  it('should display relevance score for semantic search', () => {
    render(<SearchResultCard result={mockResult} searchType="semantic" />)

    expect(screen.getByText(/relevance.*0\.92/i)).toBeInTheDocument()
  })

  it('should not display relevance score for traditional search', () => {
    render(<SearchResultCard result={mockResult} searchType="traditional" />)

    expect(screen.queryByText(/relevance/i)).not.toBeInTheDocument()
  })

  it('should handle negative sentiment', () => {
    const negativeResult = { ...mockResult, sentiment: 'negative' }
    render(<SearchResultCard result={negativeResult} />)

    const sentimentBadge = screen.getByText('negative')
    expect(sentimentBadge).toBeInTheDocument()
  })

  it('should handle neutral sentiment', () => {
    const neutralResult = { ...mockResult, sentiment: 'neutral' }
    render(<SearchResultCard result={neutralResult} />)

    const sentimentBadge = screen.getByText('neutral')
    expect(sentimentBadge).toBeInTheDocument()
  })

  it('should expand content on click', async () => {
    const longContent = 'This is a very long insight content. '.repeat(10)
    const longResult = { ...mockResult, content: longContent }
    const user = userEvent.setup()

    render(<SearchResultCard result={longResult} />)

    const expandButton = screen.getByRole('button', { name: /read more/i })
    await user.click(expandButton)

    expect(screen.getByRole('button', { name: /show less/i })).toBeInTheDocument()
  })
})
