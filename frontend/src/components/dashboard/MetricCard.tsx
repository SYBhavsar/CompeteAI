import { memo } from 'react'
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export interface MetricTrend {
  value: number
  isPositive: boolean
}

export interface MetricCardProps {
  icon: React.ReactNode
  title: string
  value: string | number
  trend?: MetricTrend
  loading?: boolean
  className?: string
}

/**
 * Displays a key metric with icon, title, value, and optional trend indicator.
 * Used on dashboard pages to show important statistics.
 * Memoized to prevent unnecessary re-renders.
 */
const MetricCard = memo(function MetricCard({
  icon,
  title,
  value,
  trend,
  loading = false,
  className,
}: MetricCardProps) {
  if (loading) {
    return (
      <Card className={cn('', className)} role="status" aria-label="Loading metric">
        <CardContent className="p-6">
          <div className="flex items-center space-x-4">
            <Skeleton className="h-12 w-12 rounded-lg" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-8 w-16" />
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className={cn('', className)} role="article" aria-label={`${title} metric`}>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-primary/10 rounded-lg text-primary" aria-hidden="true">
              {icon}
            </div>
            <div>
              <p className="text-sm font-medium text-text-secondary">{title}</p>
              <p className="text-2xl font-bold text-text-primary mt-1">{value}</p>
              {trend && (
                <div
                  className={cn(
                    'flex items-center mt-2 text-sm font-medium',
                    trend.isPositive ? 'text-success' : 'text-error'
                  )}
                  role="status"
                  aria-label={`Trend: ${trend.isPositive ? 'up' : 'down'} ${trend.value} percent`}
                >
                  {trend.isPositive ? (
                    <ArrowUpIcon className="h-4 w-4 mr-1" aria-hidden="true" />
                  ) : (
                    <ArrowDownIcon className="h-4 w-4 mr-1" aria-hidden="true" />
                  )}
                  <span>
                    {trend.isPositive ? '+' : '-'}
                    {trend.value}%
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
})

export default MetricCard

