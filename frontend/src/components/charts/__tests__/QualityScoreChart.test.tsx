import { render, screen } from '@testing-library/react'
import QualityScoreChart from '../QualityScoreChart'

describe('QualityScoreChart', () => {
  it('should render chart with data', () => {
    const mockData = [
      { name: 'Competitor 1', score: 0.85 },
      { name: 'Competitor 2', score: 0.72 },
      { name: 'Competitor 3', score: 0.90 },
    ]

    render(<QualityScoreChart data={mockData} />)

    expect(screen.getByText(/quality score trends/i)).toBeInTheDocument()
  })

  it('should render empty state when no data', () => {
    render(<QualityScoreChart data={[]} />)

    expect(screen.getByText(/no data available/i)).toBeInTheDocument()
  })
})
