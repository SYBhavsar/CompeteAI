'use client'

import ProtectedRoute from '@/components/auth/ProtectedRoute'
import Sidebar from '@/components/layout/Sidebar'
import Header from '@/components/layout/Header'
import Breadcrumbs from '@/components/layout/Breadcrumbs'
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
      <div className="flex h-screen overflow-hidden bg-background">
        {/* Sidebar */}
        <Sidebar />

        {/* Main content */}
        <div className="flex flex-1 flex-col overflow-hidden">
          {/* Header */}
          <Header />

          {/* Page content */}
          <main className="flex-1 overflow-y-auto">
            <div className="py-6 px-6">
              {/* Breadcrumb navigation */}
              <Breadcrumbs />

              {children}
            </div>
          </main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
