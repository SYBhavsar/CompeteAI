'use client'

import { useState, useEffect } from 'react'
import { useAppSelector, useAppDispatch } from '@/lib/hooks'
import { fetchCompetitorsAsync } from '@/features/competitors/competitorsSlice'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'
import api from '@/services/api'
import TrendChart from '@/components/charts/TrendChart'
import SentimentChart from '@/components/charts/SentimentChart'
import QualityScoreChart from '@/components/charts/QualityScoreChart'
import toast from 'react-hot-toast'

type TimeRange = '7' | '30' | '90'

export default function AnalyticsPage() {
  const dispatch = useAppDispatch()
  const { competitors } = useAppSelector((state) => state.competitors)

  const [timeRange, setTimeRange] = useState<TimeRange>('7')
  const [selectedCompetitorId, setSelectedCompetitorId] = useState<string>('all')
  const [trendsData, setTrendsData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    dispatch(fetchCompetitorsAsync())
  }, [dispatch])

  useEffect(() => {
    fetchTrendsData()
  }, [timeRange, selectedCompetitorId])

  const fetchTrendsData = async () => {
    try {
      setLoading(true)
      const params: any = { days: timeRange }
      if (selectedCompetitorId !== 'all') {
        params.competitor_id = selectedCompetitorId
      }
      const response = await api.get('/analytics/trends', { params })
      setTrendsData(response.data)
    } catch (error) {
      console.error('Failed to fetch trends:', error)
      toast.error('Failed to fetch trends data.')
    } finally {
      setLoading(false)
    }
  }

  const handleExport = async () => {
    try {
      const params: any = { days: timeRange }
      if (selectedCompetitorId !== 'all') {
        params.competitor_id = selectedCompetitorId
      }
      const response = await api.get('/analytics/export', { params })

      const dataStr = JSON.stringify(response.data, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `analytics-${new Date().toISOString()}.json`
      link.click()
      URL.revokeObjectURL(url)
      toast.success('Analytics data exported successfully.')
    } catch (error) {
      console.error('Failed to export:', error)
      toast.error('Failed to export analytics data.')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">Competitive intelligence insights</p>
        </div>
        <Button onClick={handleExport} variant="outline">
          <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Time Range Selector */}
          <div className="flex-1">
            <label className="text-sm font-medium mb-2 block">Time Range</label>
            <div className="flex gap-2">
              <Button
                variant={timeRange === '7' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimeRange('7')}
                data-active={timeRange === '7'}
              >
                7 Days
              </Button>
              <Button
                variant={timeRange === '30' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimeRange('30')}
                data-active={timeRange === '30'}
              >
                30 Days
              </Button>
              <Button
                variant={timeRange === '90' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimeRange('90')}
                data-active={timeRange === '90'}
              >
                3 Months
              </Button>
            </div>
          </div>

          {/* Competitor Selector */}
          <div className="flex-1">
            <label className="text-sm font-medium mb-2 block">Competitor</label>
            <Select value={selectedCompetitorId} onValueChange={setSelectedCompetitorId}>
              <SelectTrigger aria-label="Competitor">
                <SelectValue placeholder="All Competitors" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Competitors</SelectItem>
                {competitors?.map((competitor) => (
                  <SelectItem key={competitor.id} value={competitor.id.toString()}>
                    {competitor.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {loading ? (
        <div className="text-center py-8">
          <p>Loading analytics...</p>
        </div>
      ) : (
        <>
          {/* Trend Chart */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Trend Analysis</h2>
            <TrendChart data={trendsData?.trend_data || []} />
          </Card>

          {/* Sentiment Distribution */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Sentiment Distribution</h2>
            <SentimentChart data={trendsData?.sentiment_data || []} />
          </Card>

          {/* Quality Score */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Quality Score Trends</h2>
            <QualityScoreChart data={trendsData?.quality_data || []} />
          </Card>
        </>
      )}
    </div>
  )
}
