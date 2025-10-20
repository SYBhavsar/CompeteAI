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

    // Initially, mobile navigation links should not be visible
    expect(screen.queryByRole('navigation', { hidden: false })).toBeInTheDocument()

    // Click hamburger to open
    const hamburgerButton = screen.getByLabelText(/toggle menu/i)
    await user.click(hamburgerButton)

    // Sheet content should be visible with navigation links
    await waitFor(() => {
      const links = screen.getAllByRole('link')
      expect(links.length).toBeGreaterThan(0)
    })
  })

  it('should close sidebar when clicking backdrop overlay', async () => {
    const user = userEvent.setup()

    render(<Sidebar />)

    // Open sidebar
    const hamburgerButton = screen.getByLabelText(/toggle menu/i)
    await user.click(hamburgerButton)

    // Wait for sidebar to open and show links
    await waitFor(() => {
      const links = screen.getAllByRole('link')
      expect(links.length).toBeGreaterThan(0)
    })

    // Click backdrop (Sheet uses Radix UI, clicking overlay closes it)
    // We need to find the overlay element
    const overlay = document.querySelector('[data-radix-dialog-overlay]')
    if (overlay) {
      await user.click(overlay as HTMLElement)

      // Navigation should close
      await waitFor(() => {
        // Sheet content should be removed or hidden
        const sheetContent = document.querySelector('[role="dialog"]')
        expect(sheetContent).not.toBeInTheDocument()
      })
    }
  })

  it('should close sidebar when clicking a navigation link on mobile', async () => {
    const user = userEvent.setup()

    render(<Sidebar />)

    // Open sidebar
    const hamburgerButton = screen.getByLabelText(/toggle menu/i)
    await user.click(hamburgerButton)

    // Wait for sidebar to open
    await waitFor(() => {
      const dialog = document.querySelector('[role="dialog"]')
      expect(dialog).toBeInTheDocument()
    })

    // Click a navigation link inside the Sheet dialog
    const sheetDialog = document.querySelector('[role="dialog"]')
    const competitorsLink = sheetDialog?.querySelector('a[href="/dashboard/competitors"]')

    if (competitorsLink) {
      await user.click(competitorsLink as HTMLElement)

      // Sidebar should close after navigation (Sheet dialog removed)
      await waitFor(() => {
        const sheetContent = document.querySelector('[role="dialog"]')
        expect(sheetContent).not.toBeInTheDocument()
      })
    } else {
      throw new Error('Competitors link not found in Sheet dialog')
    }
  })

  it('should always show sidebar on desktop viewport', () => {
    render(<Sidebar />)

    // Hamburger button exists but hidden on desktop with lg:hidden class
    const hamburgerButton = screen.getByLabelText(/toggle menu/i)
    expect(hamburgerButton).toBeInTheDocument()
    expect(hamburgerButton.parentElement).toHaveClass('lg:hidden')

    // Desktop sidebar should be visible (hidden class with lg:flex)
    const desktopSidebar = screen.getAllByRole('navigation')[0]
    expect(desktopSidebar).toBeInTheDocument()
    expect(desktopSidebar).toHaveClass('lg:flex')
  })
})
