'use client'

import { useState, useEffect, useCallback, useMemo, lazy, Suspense } from 'react'
import { useAppSelector, useAppDispatch } from '@/lib/hooks'
import { usePageTitle } from '@/hooks/usePageTitle'
import { fetchCompetitorsAsync } from '@/features/competitors/competitorsSlice'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { ArrowDownTrayIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import { ProcessedInsight } from '@/types'
import api from '@/services/api'

// Lazy load modal for better performance
const InsightDetailModal = lazy(() => import('@/components/insights/InsightDetailModal'))

import CardListSkeleton from '@/components/ui/CardListSkeleton'
import toast from 'react-hot-toast'

type SortOption = 'date' | 'quality_score'
type SentimentFilter = 'all' | 'positive' | 'negative' | 'neutral'

export default function InsightsPage() {
  usePageTitle('Insights')

  const dispatch = useAppDispatch()
  const { competitors } = useAppSelector((state) => state.competitors)

  const [selectedCompetitorId, setSelectedCompetitorId] = useState<string>('')
  const [sentimentFilter, setSentimentFilter] = useState<SentimentFilter>('all')
  const [sortBy, setSortBy] = useState<SortOption>('date')
  const [insights, setInsights] = useState<ProcessedInsight[]>([])
  const [loading, setLoading] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedInsight, setSelectedInsight] = useState<ProcessedInsight | null>(null)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const pageSize = 10

  useEffect(() => {
    dispatch(fetchCompetitorsAsync())
  }, [dispatch])

  useEffect(() => {
    if (competitors && competitors.length > 0 && !selectedCompetitorId) {
      setSelectedCompetitorId(competitors[0].id.toString())
    }
  }, [competitors])

  useEffect(() => {
    if (selectedCompetitorId) {
      fetchInsights()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCompetitorId])

  const fetchInsights = useCallback(async () => {
    if (!selectedCompetitorId) return

    try {
      setLoading(true)
      const response = await api.get(`/competitors/${selectedCompetitorId}/insights`)
      setInsights(response.data)
      setCurrentPage(1)
    } catch (error) {
      console.error('Failed to fetch insights:', error)
      setInsights([])
      toast.error('Failed to fetch insights.')
    } finally {
      setLoading(false)
    }
  }, [selectedCompetitorId])

  const filteredAndSortedInsights = useMemo(() => {
    return insights
      .filter((insight) => {
        if (sentimentFilter === 'all') return true
        return insight.sentiment === sentimentFilter
      })
      .sort((a, b) => {
        if (sortBy === 'date') {
          return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        } else {
          return (b.quality_score || 0) - (a.quality_score || 0)
        }
      })
  }, [insights, sentimentFilter, sortBy])

  const handleExport = useCallback(() => {
    try {
      const dataStr = JSON.stringify(filteredAndSortedInsights, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `insights-${new Date().toISOString()}.json`
      link.click()
      URL.revokeObjectURL(url)
      toast.success('Insights exported successfully.')
    } catch (error) {
      toast.error('Failed to export insights.')
    }
  }, [filteredAndSortedInsights])

  const totalPages = Math.ceil(filteredAndSortedInsights.length / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const paginatedInsights = filteredAndSortedInsights.slice(startIndex, endIndex)

  const handleNextPage = useCallback(() => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1)
    }
  }, [currentPage, totalPages])

  const handlePrevPage = useCallback(() => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1)
    }
  }, [currentPage])

  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }, [])

  const handleInsightClick = useCallback((insight: ProcessedInsight) => {
    setSelectedInsight(insight)
    setIsModalOpen(true)
  }, [])

  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false)
    setSelectedInsight(null)
  }, [])

  const getSentimentColor = useCallback((sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return 'default'
      case 'negative':
        return 'destructive'
      case 'neutral':
        return 'secondary'
      default:
        return 'secondary'
    }
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Insights</h1>
          <p className="text-muted-foreground">AI-generated competitive insights</p>
        </div>
        <Button onClick={handleExport} variant="outline">
          <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Competitor Filter */}
          <div>
            <label className="text-sm font-medium mb-2 block">Competitor</label>
            <Select value={selectedCompetitorId} onValueChange={setSelectedCompetitorId}>
              <SelectTrigger aria-label="Competitor">
                <SelectValue placeholder="Select competitor" />
              </SelectTrigger>
              <SelectContent>
                {competitors?.map((competitor) => (
                  <SelectItem key={competitor.id} value={competitor.id.toString()}>
                    {competitor.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Sentiment Filter */}
          <div>
            <label className="text-sm font-medium mb-2 block">Sentiment</label>
            <Select value={sentimentFilter} onValueChange={(v) => setSentimentFilter(v as SentimentFilter)}>
              <SelectTrigger aria-label="Sentiment">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sentiments</SelectItem>
                <SelectItem value="positive">Positive</SelectItem>
                <SelectItem value="negative">Negative</SelectItem>
                <SelectItem value="neutral">Neutral</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Sort By */}
          <div>
            <label className="text-sm font-medium mb-2 block">Sort By</label>
            <Select value={sortBy} onValueChange={(v) => setSortBy(v as SortOption)}>
              <SelectTrigger aria-label="Sort by">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="date">Date</SelectItem>
                <SelectItem value="quality_score">Quality Score</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </Card>

      {/* Insights List */}
      {loading ? (
        <CardListSkeleton count={5} />
      ) : paginatedInsights.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">No insights found</p>
        </Card>
      ) : (
        <>
          <div className="space-y-4">
            {paginatedInsights.map((insight) => (
              <Card
                key={insight.id}
                className="p-6 cursor-pointer hover:bg-accent/50 transition-colors"
                onClick={() => handleInsightClick(insight)}
              >
                <div className="space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold mb-2">{insight.summary}</h3>
                      {insight.key_points && insight.key_points.length > 0 && (
                        <ul className="list-disc list-inside text-sm text-muted-foreground mb-2">
                          {insight.key_points.map((point, idx) => (
                            <li key={idx}>{point}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <Badge variant={getSentimentColor(insight.sentiment)}>
                      {insight.sentiment}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>Quality: {insight.quality_score?.toFixed(2) || 'N/A'}</span>
                    <span>{formatDate(insight.created_at)}</span>
                  </div>
                </div>
              </Card>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  onClick={handlePrevPage}
                  disabled={currentPage === 1}
                  variant="outline"
                  size="sm"
                >
                  <ChevronLeftIcon className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <Button
                  onClick={handleNextPage}
                  disabled={currentPage === totalPages}
                  variant="outline"
                  size="sm"
                >
                  Next
                  <ChevronRightIcon className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Insight Detail Modal */}
      {isModalOpen && (
        <Suspense fallback={null}>
          <InsightDetailModal
            insight={selectedInsight}
            isOpen={isModalOpen}
            onClose={handleCloseModal}
          />
        </Suspense>
      )}
    </div>
  )
}
