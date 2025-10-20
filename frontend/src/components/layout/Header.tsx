'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAppDispatch, useAppSelector } from '@/lib/hooks'
import { logout, selectUser } from '@/features/auth/authSlice'
import { UserCircleIcon, ArrowRightOnRectangleIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'
import NotificationDropdown from './NotificationDropdown'

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
        {/* Left side - Search Bar */}
        <div className="flex flex-1 items-center">
          <div className="relative w-full max-w-xs">
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              <MagnifyingGlassIcon className="h-5 w-5 text-text-secondary" aria-hidden="true" />
            </div>
            <input
              id="search"
              name="search"
              className="block w-full bg-background border border-border rounded-md py-2 pl-10 pr-3 text-sm placeholder-text-secondary focus:ring-primary focus:border-primary"
              placeholder="Search..."
              type="search"
            />
          </div>
        </div>

        {/* Right side - notifications and user menu */}
        <div className="flex items-center gap-4">
          {/* Notifications */}
          <NotificationDropdown />

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
