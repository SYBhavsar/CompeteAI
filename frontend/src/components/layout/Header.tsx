'use client'

import { useRouter } from 'next/navigation'
import { useAppDispatch, useAppSelector } from '@/lib/hooks'
import { logout, selectUser } from '@/features/auth/authSlice'
import { UserCircleIcon, ArrowRightOnRectangleIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import NotificationDropdown from './NotificationDropdown'
import { Input } from '@/components/ui/input'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

export default function Header() {
  const router = useRouter()
  const dispatch = useAppDispatch()
  const user = useAppSelector(selectUser)

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
            <Input
              id="search"
              name="search"
              className="pl-10 pr-3"
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
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                className="flex items-center gap-2 rounded-full p-2 text-text-secondary hover:bg-background hover:text-text-primary transition-colors"
                aria-label="User menu"
              >
                <UserCircleIcon className="h-8 w-8" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end">
              <DropdownMenuLabel>
                <p className="text-sm font-medium text-text-primary">{user?.full_name}</p>
                <p className="text-xs text-text-secondary truncate">{user?.email}</p>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <ArrowRightOnRectangleIcon className="mr-3 h-5 w-5" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  )
}
