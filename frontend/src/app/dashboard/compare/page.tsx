'use client'

import { useState, useEffect, useCallback } from 'react'
import { useAppSelector, useAppDispatch } from '@/lib/hooks'
import { fetchCompetitorsAsync } from '@/features/competitors/competitorsSlice'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import TableSkeleton from '@/components/ui/TableSkeleton'
import api from '@/services/api'
import toast from 'react-hot-toast'

interface CompetitorComparison {
  id: number
  name: string
  insights_count: number
  avg_quality_score: number
  sentiment_distribution: {
    positive: number
    negative: number
    neutral: number
  }
}

interface ComparisonData {
  competitors: CompetitorComparison[]
}

export default function ComparePage() {
  const dispatch = useAppDispatch()
  const { competitors } = useAppSelector((state) => state.competitors)

  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    dispatch(fetchCompetitorsAsync())
  }, [dispatch])

  const handleToggleCompetitor = useCallback((id: number) => {
    setSelectedIds((prevIds) => {
      if (prevIds.includes(id)) {
        return prevIds.filter((cid) => cid !== id)
      } else if (prevIds.length < 4) {
        return [...prevIds, id]
      }
      return prevIds
    })
  }, [])

  const handleCompare = useCallback(async () => {
    if (selectedIds.length < 2) return

    try {
      setLoading(true)
      const response = await api.get('/analytics/comparison', {
        params: {
          competitor_ids: selectedIds.join(','),
        },
      })
      setComparisonData(response.data)
    } catch (error) {
      console.error('Failed to fetch comparison:', error)
      toast.error('Failed to fetch comparison data.')
    } finally {
      setLoading(false)
    }
  }, [selectedIds])

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-3xl font-bold">Competitor Comparison</h1>
          <p className="text-sm text-muted-foreground">Compare metrics across competitors</p>
        </div>
      </div>

      {/* Competitor Selection */}
      <Card className="p-4 sm:p-6">
        <h2 className="text-lg font-semibold mb-4">Select Competitors to Compare (2-4)</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {competitors?.map((competitor) => (
            <div
              key={competitor.id}
              onClick={() => handleToggleCompetitor(competitor.id)}
              className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                selectedIds.includes(competitor.id)
                  ? 'border-primary bg-primary/10'
                  : 'border-border hover:border-primary/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">{competitor.name}</h3>
                  <p className="text-sm text-muted-foreground">{competitor.domain}</p>
                </div>
                {selectedIds.includes(competitor.id) && (
                  <Badge variant="default">Selected</Badge>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4">
          <Button
            onClick={handleCompare}
            disabled={selectedIds.length < 2 || loading}
          >
            Compare
          </Button>
        </div>
      </Card>

      {/* Comparison Results */}
      {loading ? (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">Key Metrics</h2>
          <TableSkeleton rows={selectedIds.length} columns={6} />
        </Card>
      ) : comparisonData ? (
        <div className="space-y-6">
          {/* Metrics Table */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Key Metrics</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Competitor</th>
                    <th className="text-left py-2">Insights Count</th>
                    <th className="text-left py-2">Avg Quality Score</th>
                    <th className="text-left py-2">Positive</th>
                    <th className="text-left py-2">Negative</th>
                    <th className="text-left py-2">Neutral</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonData.competitors.map((comp) => (
                    <tr key={comp.id} className="border-b">
                      <td className="py-3 font-medium">{comp.name}</td>
                      <td className="py-3">{comp.insights_count}</td>
                      <td className="py-3">{comp.avg_quality_score.toFixed(2)}</td>
                      <td className="py-3">{comp.sentiment_distribution.positive}</td>
                      <td className="py-3">{comp.sentiment_distribution.negative}</td>
                      <td className="py-3">{comp.sentiment_distribution.neutral}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      ) : (
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">Select competitors to compare their metrics</p>
        </Card>
      )}
    </div>
  )
}
