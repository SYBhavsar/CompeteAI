'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
import ErrorBoundary from '@/components/error/ErrorBoundary'
import useWebSocket from '@/hooks/useWebSocket'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Connect to WebSocket for real-time notifications
  useWebSocket()

  return (
    <ProtectedRoute>
      {/* Skip to main content link for keyboard navigation */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-primary focus:text-primary-foreground focus:top-4 focus:left-4 focus:rounded-md"
      >
        Skip to main content
      </a>

      <div className="flex h-screen overflow-hidden bg-background">
        {/* Sidebar */}
        <Sidebar />

        {/* Main content */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Header */}
          <Header />

          {/* Page content */}
          <main id="main-content" className="flex-1 overflow-y-auto">
            <div className="py-6 px-6">
              {/* Breadcrumb navigation */}
              <Breadcrumbs />

              <ErrorBoundary>
                {children}
              </ErrorBoundary>
            </div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
