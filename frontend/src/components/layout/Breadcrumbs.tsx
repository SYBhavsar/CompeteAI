'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'

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
    <Breadcrumb>
      <BreadcrumbList>
        {breadcrumbs.map((crumb, index) => (
          <React.Fragment key={crumb.href}>
            <BreadcrumbItem>
              {crumb.isLast ? (
                <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
              ) : (
                <BreadcrumbLink asChild>
                  <Link href={crumb.href}>{crumb.label}</Link>
                </BreadcrumbLink>
              )}
            </BreadcrumbItem>
            {index < breadcrumbs.length - 1 && <BreadcrumbSeparator />}
          </React.Fragment>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  )
}
