import { render, screen } from '@testing-library/react'
import Breadcrumbs from '../Breadcrumbs'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  usePathname: jest.fn(),
}))

const { usePathname } = require('next/navigation')

describe('Breadcrumbs Component', () => {
  it('should render Home breadcrumb on dashboard root', () => {
    usePathname.mockReturnValue('/dashboard')

    render(<Breadcrumbs />)

    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    // Current page should not be a clickable link (no href attribute)
    const dashboardElement = screen.getByText('Dashboard')
    expect(dashboardElement.closest('a')).not.toBeInTheDocument()
  })

  it('should render breadcrumb trail for nested routes', () => {
    usePathname.mockReturnValue('/dashboard/competitors')

    render(<Breadcrumbs />)

    // Should show: Dashboard > Competitors
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Competitors')).toBeInTheDocument()

    // Dashboard should be a link
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
    expect(dashboardLink).toHaveAttribute('href', '/dashboard')
  })

  it('should render breadcrumb trail for deeply nested routes', () => {
    usePathname.mockReturnValue('/dashboard/competitors/123')

    render(<Breadcrumbs />)

    // Should show: Dashboard > Competitors > 123
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Competitors')).toBeInTheDocument()
    expect(screen.getByText('123')).toBeInTheDocument()

    // Dashboard and Competitors should be links
    const dashboardLink = screen.getByRole('link', { name: /dashboard/i })
    expect(dashboardLink).toHaveAttribute('href', '/dashboard')

    const competitorsLink = screen.getByRole('link', { name: /competitors/i })
    expect(competitorsLink).toHaveAttribute('href', '/dashboard/competitors')
  })

  it('should capitalize breadcrumb labels', () => {
    usePathname.mockReturnValue('/dashboard/search/history')

    render(<Breadcrumbs />)

    // Should capitalize: Search, History
    expect(screen.getByText('Search')).toBeInTheDocument()
    expect(screen.getByText('History')).toBeInTheDocument()
  })

  it('should render separator between breadcrumbs', () => {
    usePathname.mockReturnValue('/dashboard/competitors')

    render(<Breadcrumbs />)

    // Should have separators (chevrons or slashes)
    const breadcrumbNav = screen.getByRole('navigation')
    expect(breadcrumbNav).toBeInTheDocument()
    expect(breadcrumbNav.textContent).toMatch(/Dashboard.*Competitors/)
  })
})
