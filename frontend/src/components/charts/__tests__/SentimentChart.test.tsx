import { render, screen } from '@testing-library/react'
import SentimentChart from '../SentimentChart'

describe('SentimentChart', () => {
  it('should render chart with data', () => {
    const mockData = [
      { name: 'Positive', value: 45 },
      { name: 'Negative', value: 30 },
      { name: 'Neutral', value: 25 },
    ]

    render(<SentimentChart data={mockData} />)

    expect(screen.getByText(/sentiment distribution/i)).toBeInTheDocument()
  })

  it('should render empty state when no data', () => {
    render(<SentimentChart data={[]} />)

    expect(screen.getByText(/no data available/i)).toBeInTheDocument()
  })
})
