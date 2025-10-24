'use client'

import { useEffect, useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useAppDispatch, useAppSelector } from '@/lib/hooks'
import { fetchCompetitorsAsync, selectCompetitors } from '@/features/competitors/competitorsSlice'
import { selectUser } from '@/features/auth/authSlice'
import { usePageTitle } from '@/hooks/usePageTitle'
import MetricCard from '@/components/dashboard/MetricCard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { PlusIcon,UserGroupIcon,LightBulbIcon,BellAlertIcon,MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function DashboardPage() {
  usePageTitle('Dashboard')

  const router = useRouter()
  const dispatch = useAppDispatch()
  const user = useAppSelector(selectUser)
  const competitors = useAppSelector(selectCompetitors)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        await dispatch(fetchCompetitorsAsync()).unwrap()
      } catch (error) {
        toast.error('Failed to fetch dashboard data.')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [dispatch])

  const handleAddCompetitor = useCallback(() => {
    router.push('/dashboard/competitors')
  }, [router])

  const handleNewSearch = useCallback(() => {
    router.push('/dashboard/search')
  }, [router])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-text-primary">
          Welcome back, {user?.full_name}
        </h1>
        <p className="text-text-secondary mt-2">
          Here's what's happening with your competitive intelligence
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          icon={<UserGroupIcon className="h-6 w-6" />}
          title="Total Competitors"
          value={loading ? 0 : competitors.length}
          loading={loading}
        />
        <MetricCard
          icon={<LightBulbIcon className="h-6 w-6" />}
          title="Total Insights"
          value={0}
          loading={loading}
        />
        <MetricCard
          icon={<BellAlertIcon className="h-6 w-6" />}
          title="Recent Alerts"
          value={0}
          loading={loading}
        />
        <MetricCard
          icon={<MagnifyingGlassIcon className="h-6 w-6" />}
          title="Searches"
          value={0}
          loading={loading}
        />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <Button onClick={handleAddCompetitor} className="w-full justify-start">
              <PlusIcon className="h-5 w-5 mr-2" />
              Add Competitor
            </Button>
            <Button onClick={handleNewSearch} variant="outline" className="w-full justify-start">
              <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
              New Search
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-text-secondary text-sm">No recent activity</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
