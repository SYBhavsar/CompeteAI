'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAppDispatch, useAppSelector } from '@/lib/hooks'
import { logout, selectUser } from '@/features/auth/authSlice'
import { BellIcon, UserCircleIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'

export default function Header() {
  const router = useRouter()
  const dispatch = useAppDispatch()
  const user = useAppSelector(selectUser)
  const [showUserMenu, setShowUserMenu] = useState(false)

  /**
   * Handle user logout
   */
  const handleLogout = () => {
    dispatch(logout())
    router.push('/login')
  }

  return (
    <div className="flex h-16 flex-shrink-0 border-b border-border bg-surface">
      <div className="flex flex-1 justify-between px-6">
        {/* Left side - could add breadcrumbs or search */}
        <div className="flex flex-1 items-center">
          <h2 className="text-lg font-semibold text-text-primary">
            Welcome back, {user?.full_name}
          </h2>
        </div>

        {/* Right side - notifications and user menu */}
        <div className="flex items-center gap-4">
          {/* Notifications */}
          <button
            type="button"
            className="rounded-full p-2 text-text-secondary hover:bg-background hover:text-text-primary transition-colors"
            aria-label="View notifications"
          >
            <BellIcon className="h-6 w-6" />
          </button>

          {/* User menu */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 rounded-full p-2 text-text-secondary hover:bg-background hover:text-text-primary transition-colors"
              aria-label="User menu"
            >
              <UserCircleIcon className="h-8 w-8" />
            </button>

            {/* Dropdown menu */}
            {showUserMenu && (
              <>
                {/* Backdrop to close menu */}
                <div
                  className="fixed inset-0 z-10"
                  onClick={() => setShowUserMenu(false)}
                />

                {/* Menu */}
                <div className="absolute right-0 z-20 mt-2 w-56 origin-top-right rounded-md bg-surface border border-border shadow-lg">
                  <div className="py-1">
                    {/* User info */}
                    <div className="px-4 py-3 border-b border-border">
                      <p className="text-sm font-medium text-text-primary">{user?.full_name}</p>
                      <p className="text-xs text-text-secondary truncate">{user?.email}</p>
                    </div>

                    {/* Menu items */}
                    <button
                      onClick={handleLogout}
                      className="flex w-full items-center px-4 py-2 text-sm text-text-secondary hover:bg-background hover:text-text-primary transition-colors"
                    >
                      <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5" />
                      Sign out
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
