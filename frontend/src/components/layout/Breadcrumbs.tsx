'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { ChevronRightIcon } from '@heroicons/react/24/outline'

/**
 * Breadcrumbs component
 * Displays navigation trail based on current route
 */
export default function Breadcrumbs() {
  const pathname = usePathname()

  /**
   * Generate breadcrumb items from pathname
   */
  const generateBreadcrumbs = () => {
    // Remove leading/trailing slashes and split
    const segments = pathname?.split('/').filter(Boolean) || []

    return segments.map((segment, index) => {
      // Build path up to this segment
      const href = '/' + segments.slice(0, index + 1).join('/')

      // Capitalize segment for display
      const label = segment.charAt(0).toUpperCase() + segment.slice(1)

      return {
        label,
        href,
        isLast: index === segments.length - 1,
      }
    })
  }

  const breadcrumbs = generateBreadcrumbs()

  // Don't render if only on dashboard root
  if (breadcrumbs.length === 0) {
    return null
  }

  return (
    <nav aria-label="Breadcrumb" className="flex items-center space-x-2 text-sm">
      {breadcrumbs.map((crumb, index) => (
        <div key={crumb.href} className="flex items-center">
          {/* Separator */}
          {index > 0 && (
            <ChevronRightIcon className="h-4 w-4 text-text-secondary mx-2" />
          )}

          {/* Breadcrumb Item */}
          {crumb.isLast ? (
            <span className="text-text-primary font-medium">{crumb.label}</span>
          ) : (
            <Link
              href={crumb.href}
              className="text-text-secondary hover:text-text-primary transition-colors"
            >
              {crumb.label}
            </Link>
          )}
        </div>
      ))}
    </nav>
  )
}
