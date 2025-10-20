import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import Sidebar from '../Sidebar'

// Mock next navigation
jest.mock('next/navigation', () => ({
  usePathname: () => '/dashboard',
}))

describe('Mobile Sidebar - Integration Tests', () => {
  it('should show hamburger menu button on mobile viewport', () => {
    render(<Sidebar />)

    // Hamburger button should be visible
    const hamburgerButton = screen.getByLabelText(/toggle menu/i)
    expect(hamburgerButton).toBeInTheDocument()
    expect(hamburgerButton.parentElement).toHaveClass('lg:hidden')
  })

  it('should toggle sidebar when clicking hamburger button', async () => {
    const user = userEvent.setup()

    render(<Sidebar />)

    // Sidebar should be hidden initially on mobile (translate-x-full)
    const sidebar = screen.getByRole('navigation')
    expect(sidebar).toHaveClass('-translate-x-full')

    // Click hamburger to open
    const hamburgerButton = screen.getByLabelText(/toggle menu/i)
    await user.click(hamburgerButton)

    // Sidebar should be visible (translate-x-0)
    await waitFor(() => {
      expect(sidebar).toHaveClass('translate-x-0')
    })
  })

  it('should close sidebar when clicking backdrop overlay', async () => {
    const user = userEvent.setup()

    render(<Sidebar />)

    // Open sidebar
    const hamburgerButton = screen.getByLabelText(/toggle menu/i)
    await user.click(hamburgerButton)

    // Wait for sidebar to open
    await waitFor(() => {
      expect(screen.getByRole('navigation')).toHaveClass('translate-x-0')
    })

    // Click backdrop
    const backdrop = screen.getByTestId('sidebar-backdrop')
    await user.click(backdrop)

    // Sidebar should close
    await waitFor(() => {
      expect(screen.getByRole('navigation')).toHaveClass('-translate-x-full')
    })
  })

  it('should close sidebar when clicking a navigation link on mobile', async () => {
    const user = userEvent.setup()

    render(<Sidebar />)

    // Open sidebar
    const hamburgerButton = screen.getByLabelText(/toggle menu/i)
    await user.click(hamburgerButton)

    // Wait for sidebar to open
    await waitFor(() => {
      expect(screen.getByRole('navigation')).toHaveClass('translate-x-0')
    })

    // Click a navigation link
    const competitorsLink = screen.getByText(/competitors/i)
    await user.click(competitorsLink)

    // Sidebar should close after navigation
    await waitFor(() => {
      expect(screen.getByRole('navigation')).toHaveClass('-translate-x-full')
    })
  })

  it('should always show sidebar on desktop viewport', () => {
    // Set desktop viewport
    global.innerWidth = 1280
    global.dispatchEvent(new Event('resize'))

    render(<Sidebar />)

    // Hamburger button exists but hidden on desktop with lg:hidden class
    const hamburgerButton = screen.getByLabelText(/toggle menu/i)
    expect(hamburgerButton).toBeInTheDocument()
    expect(hamburgerButton.parentElement).toHaveClass('lg:hidden')

    // Sidebar should be visible (has translate-x-0 on desktop)
    const sidebar = screen.getByRole('navigation')
    expect(sidebar).toBeInTheDocument()
    expect(sidebar).toHaveClass('lg:translate-x-0')
  })
})
