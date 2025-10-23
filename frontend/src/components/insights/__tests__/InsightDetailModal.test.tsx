import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import InsightDetailModal from '../InsightDetailModal'
import { ProcessedInsight } from '@/types'

const mockInsight: ProcessedInsight = {
  id: 1,
  raw_content_id: 1,
  summary: 'Test insight summary',
  key_points: ['Point 1', 'Point 2', 'Point 3'],
  sentiment: 'positive',
  insights: 'This is the detailed insight text that provides more context.',
  quality_score: 0.85,
  created_at: '2024-01-15T10:30:00Z',
  updated_at: '2024-01-15T10:30:00Z',
}

describe('InsightDetailModal', () => {
  it('should not render when closed', () => {
    render(<InsightDetailModal insight={mockInsight} isOpen={false} onClose={() => {}} />)

    expect(screen.queryByText('Insight Details')).not.toBeInTheDocument()
  })

  it('should render insight details when open', () => {
    render(<InsightDetailModal insight={mockInsight} isOpen={true} onClose={() => {}} />)

    expect(screen.getByText('Insight Details')).toBeInTheDocument()
    expect(screen.getByText('Test insight summary')).toBeInTheDocument()
    expect(screen.getByText(/This is the detailed insight text/i)).toBeInTheDocument()
  })

  it('should display key points', () => {
    render(<InsightDetailModal insight={mockInsight} isOpen={true} onClose={() => {}} />)

    expect(screen.getByText('Point 1')).toBeInTheDocument()
    expect(screen.getByText('Point 2')).toBeInTheDocument()
    expect(screen.getByText('Point 3')).toBeInTheDocument()
  })

  it('should display sentiment', () => {
    render(<InsightDetailModal insight={mockInsight} isOpen={true} onClose={() => {}} />)

    expect(screen.getByText(/positive/i)).toBeInTheDocument()
  })

  it('should display quality score', () => {
    render(<InsightDetailModal insight={mockInsight} isOpen={true} onClose={() => {}} />)

    expect(screen.getByText(/0.85/i)).toBeInTheDocument()
  })

  it('should call onClose when close button clicked', async () => {
    const user = userEvent.setup()
    const onClose = jest.fn()

    render(<InsightDetailModal insight={mockInsight} isOpen={true} onClose={onClose} />)

    const closeButtons = screen.getAllByRole('button', { name: 'Close' })
    await user.click(closeButtons[0])

    expect(onClose).toHaveBeenCalled()
  })
})
