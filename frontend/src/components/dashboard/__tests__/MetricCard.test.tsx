import { render, screen } from '@testing-library/react'
import MetricCard from '../MetricCard'
import { ChartBarIcon } from '@heroicons/react/24/outline'

describe('MetricCard Component - Integration Tests', () => {
  it('should render metric card with all basic props', () => {
    render(
      <MetricCard
        icon={<ChartBarIcon className="h-6 w-6" data-testid="chart-icon" />}
        title="Total Competitors"
        value={25}
      />
    )

    expect(screen.getByTestId('chart-icon')).toBeInTheDocument()
    expect(screen.getByText('Total Competitors')).toBeInTheDocument()
    expect(screen.getByText('25')).toBeInTheDocument()
  })

  it('should display positive trend indicator when provided', () => {
    render(
      <MetricCard
        icon={<ChartBarIcon className="h-6 w-6" />}
        title="Total Insights"
        value={150}
        trend={{ value: 15, isPositive: true }}
      />
    )

    expect(screen.getByText('Total Insights')).toBeInTheDocument()
    expect(screen.getByText('150')).toBeInTheDocument()
    expect(screen.getByText('+15%')).toBeInTheDocument()

    // Check for upward arrow icon
    const trendContainer = screen.getByText('+15%').closest('div')
    expect(trendContainer).toHaveClass('text-success')
  })

  it('should display negative trend indicator', () => {
    render(
      <MetricCard
        icon={<ChartBarIcon className="h-6 w-6" />}
        title="Active Alerts"
        value={5}
        trend={{ value: 8, isPositive: false }}
      />
    )

    expect(screen.getByText('Active Alerts')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('-8%')).toBeInTheDocument()

    // Check for downward arrow and error color
    const trendContainer = screen.getByText('-8%').closest('div')
    expect(trendContainer).toHaveClass('text-error')
  })

  it('should show loading skeleton state', () => {
    render(
      <MetricCard
        icon={<ChartBarIcon className="h-6 w-6" />}
        title="Total Competitors"
        value={25}
        loading={true}
      />
    )

    // When loading, actual content should not be visible
    expect(screen.queryByText('Total Competitors')).not.toBeInTheDocument()
    expect(screen.queryByText('25')).not.toBeInTheDocument()

    // Skeleton should be present
    const skeletons = document.querySelectorAll('.animate-pulse')
    expect(skeletons.length).toBeGreaterThan(0)
  })

  it('should handle optional trend (no trend indicator)', () => {
    render(
      <MetricCard
        icon={<ChartBarIcon className="h-6 w-6" />}
        title="Search History"
        value={42}
      />
    )

    expect(screen.getByText('Search History')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()

    // No trend indicator should be present
    expect(screen.queryByText(/%/)).not.toBeInTheDocument()
  })

  it('should apply custom className', () => {
    const { container } = render(
      <MetricCard
        icon={<ChartBarIcon className="h-6 w-6" />}
        title="Custom Card"
        value={100}
        className="custom-class"
      />
    )

    const card = container.firstChild
    expect(card).toHaveClass('custom-class')
  })

  it('should render string values correctly', () => {
    render(
      <MetricCard
        icon={<ChartBarIcon className="h-6 w-6" />}
        title="Status"
        value="Active"
      />
    )

    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })
})
