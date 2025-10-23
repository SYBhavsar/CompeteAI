import { render, screen } from '@testing-library/react'
import TrendChart from '../TrendChart'

describe('TrendChart', () => {
  it('should render chart with data', () => {
    const mockData = [
      { date: '2024-01-01', value: 10 },
      { date: '2024-01-02', value: 15 },
      { date: '2024-01-03', value: 12 },
    ]

    render(<TrendChart data={mockData} />)

    expect(screen.getByText(/trend analysis/i)).toBeInTheDocument()
  })

  it('should render empty state when no data', () => {
    render(<TrendChart data={[]} />)

    expect(screen.getByText(/no data available/i)).toBeInTheDocument()
  })
})
