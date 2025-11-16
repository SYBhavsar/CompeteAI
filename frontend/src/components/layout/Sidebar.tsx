'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  HomeIcon,
  UsersIcon,
  MagnifyingGlassIcon,
  ChartBarIcon,
  LightBulbIcon,
  ArrowsRightLeftIcon,
  BellIcon,
  Cog6ToothIcon,
  Bars3Icon,
} from '@heroicons/react/24/outline'
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  SheetDescription
} from '@/components/ui/sheet'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Competitors', href: '/dashboard/competitors', icon: UsersIcon },
  { name: 'Search', href: '/dashboard/search', icon: MagnifyingGlassIcon },
  { name: 'Analytics', href: '/dashboard/analytics', icon: ChartBarIcon },
  { name: 'Insights', href: '/dashboard/insights', icon: LightBulbIcon },
  { name: 'Compare', href: '/dashboard/compare', icon: ArrowsRightLeftIcon },
  { name: 'Alerts', href: '/dashboard/alerts', icon: BellIcon },
  { name: 'Settings', href: '/dashboard/settings', icon: Cog6ToothIcon },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [isOpen, setIsOpen] = useState(false)

  const SidebarContent = () => (
    <div className="flex w-64 flex-col">
      <div className="flex min-h-0 flex-1 flex-col bg-surface border-r border-border">
        {/* Logo */}
        <div className="flex h-16 flex-shrink-0 items-center px-6 border-b border-border">
          <h1 className="text-xl font-bold text-primary">CompeteAI</h1>
        </div>

        {/* Navigation Links */}
        <div className="flex-1 space-y-1 px-3 py-4">
          {navigation.map((item) => {
            const isActive = pathname === item.href || pathname?.startsWith(item.href + '/')
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setIsOpen(false)}
                className={clsx(
                  'group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-text-secondary hover:bg-background hover:text-text-primary'
                )}
              >
                <item.icon
                  className={clsx(
                    'mr-3 h-5 w-5 flex-shrink-0',
                    isActive ? 'text-primary' : 'text-text-secondary group-hover:text-text-primary'
                  )}
                />
                {item.name}
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Mobile Sidebar (Sheet) */}
      <div className="lg:hidden fixed top-4 left-4 z-50" data-testid="mobile-sidebar">
        <Sheet open={isOpen} onOpenChange={setIsOpen}>
          <SheetTrigger asChild>
            <button
              type="button"
              className="rounded-md p-2 text-text-primary bg-surface border border-border hover:bg-background"
              aria-label="Toggle menu"
            >
              <Bars3Icon className="h-6 w-6" />
            </button>
          </SheetTrigger>
          <SheetContent side="left" className="w-64 p-0">
            <SheetHeader>
              <SheetTitle className="sr-only">Mobile Menu</SheetTitle>
              <SheetDescription className="sr-only">Main navigation menu for the application.</SheetDescription>
            </SheetHeader>
            <div role="navigation">
              <SidebarContent />
            </div>
          </SheetContent>
        </Sheet>
      </div>

      {/* Desktop Sidebar */}
      <nav className="hidden lg:flex lg:flex-shrink-0 lg:translate-x-0" role="navigation">
        <SidebarContent />
      </nav>
    </>
  )
}
