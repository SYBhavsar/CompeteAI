'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useAppDispatch, useAppSelector } from '@/lib/hooks'
import {
  fetchCompetitorByIdAsync,
  deleteCompetitorAsync,
  selectSelectedCompetitor,
  selectCompetitorsLoading,
  selectCompetitorsError,
} from '@/features/competitors/competitorsSlice'
import { dataSourcesService } from '@/services/dataSourcesService'
import { insightsService } from '@/services/insightsService'
import { PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import { format } from 'date-fns'
import CompetitorModal from '@/components/competitors/CompetitorModal'
import DeleteConfirmModal from '@/components/competitors/DeleteConfirmModal'
import DataSourcesManager from '@/components/competitors/DataSourcesManager'
import { DataSource, ProcessedInsight } from '@/types'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs'
import toast from 'react-hot-toast'

type TabType = 'overview' | 'data-sources' | 'insights' | 'scraped-data'

/**
 * Competitor detail page
 * Shows detailed information about a single competitor
 */
export default function CompetitorDetailPage() {
  const router = useRouter()
  const params = useParams()
  const dispatch = useAppDispatch()

  const competitorId = Number(params.id)
  const competitor = useAppSelector(selectSelectedCompetitor)
  const loading = useAppSelector(selectCompetitorsLoading)
  const error = useAppSelector(selectCompetitorsError)

  const [activeTab, setActiveTab] = useState<TabType>('overview')
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false)

  const [dataSources, setDataSources] = useState<DataSource[]>([])
  const [insights, setInsights] = useState<ProcessedInsight[]>([])
  const [insightsLoading, setInsightsLoading] = useState(false)

  /**
   * Fetch competitor details on mount
   */
  useEffect(() => {
    if (competitorId) {
      dispatch(fetchCompetitorByIdAsync(competitorId))
    }
  }, [dispatch, competitorId])

  /**
   * Fetch data sources and insights
   */
  useEffect(() => {
    if (competitorId) {
      // Fetch data sources
      dataSourcesService
        .getByCompetitor(competitorId)
        .then((sources) => {
          setDataSources(sources)
        })
        .catch((err) => {
          console.error('Failed to fetch data sources:', err)
          toast.error('Failed to fetch data sources.')
        })

      // Fetch insights
      setInsightsLoading(true)
      insightsService
        .getByCompetitor(competitorId)
        .then((data) => {
          setInsights(data)
        })
        .catch((err) => {
          console.error('Failed to fetch insights:', err)
          toast.error('Failed to fetch insights.')
        })
        .finally(() => {
          setInsightsLoading(false)
        })
    }
  }, [competitorId])

  /**
   * Handle delete competitor
   */
  const handleDelete = async () => {
    if (competitorId) {
      try {
        await dispatch(deleteCompetitorAsync(competitorId)).unwrap()
        setIsDeleteModalOpen(false)
        toast.success('Competitor deleted successfully.')
        router.push('/dashboard/competitors')
      } catch (error) {
        toast.error('Failed to delete competitor.')
      }
    }
  }

  /**
   * Get last scraped date from data sources
   */
  const getLastScrapedDate = () => {
    if (dataSources.length === 0) return null

    const scrapedDates = dataSources
      .filter((ds) => ds.last_scraped)
      .map((ds) => new Date(ds.last_scraped!))

    if (scrapedDates.length === 0) return null

    return new Date(Math.max(...scrapedDates.map((d) => d.getTime())))
  }

  /**
   * Show loading state
   */
  if (loading && !competitor) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-text-secondary">Loading competitor details...</p>
      </div>
    )
  }

  /**
   * Show error state
   */
  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-error">Error: {error}</p>
      </div>
    )
  }

  if (!competitor) {
    return null
  }

  const lastScraped = getLastScrapedDate()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">{competitor.name}</h1>
          {competitor.domain && (
            <a
              href={competitor.domain}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary hover:underline mt-1 inline-block"
            >
              {competitor.domain}
            </a>
          )}
          {competitor.industry && (
            <p className="text-sm text-text-secondary mt-1">{competitor.industry}</p>
          )}
        </div>
        <div className="flex space-x-2">
          <Button variant="outline" onClick={() => setIsEditModalOpen(true)}>
            <PencilIcon className="h-4 w-4 mr-2" />
            Edit
          </Button>
          <Button variant="destructive" onClick={() => setIsDeleteModalOpen(true)}>
            <TrashIcon className="h-4 w-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Data Sources</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{dataSources.length}</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Last Scraped</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-semibold">
              {lastScraped ? format(lastScraped, 'MMM d, yyyy') : 'Never'}
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm font-medium">Insights</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{insights.length}</div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as TabType)}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="data-sources">Data Sources</TabsTrigger>
          <TabsTrigger value="insights">AI Insights</TabsTrigger>
          <TabsTrigger value="scraped-data">Scraped Data</TabsTrigger>
        </TabsList>
        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="space-y-3">
                <div>
                  <dt className="text-sm font-medium text-text-secondary">Name</dt>
                  <dd className="mt-1 text-sm text-text-primary">{competitor.name}</dd>
                </div>
                {competitor.domain && (
                  <div>
                    <dt className="text-sm font-medium text-text-secondary">Domain</dt>
                    <dd className="mt-1 text-sm text-text-primary">{competitor.domain}</dd>
                  </div>
                )}
                {competitor.industry && (
                  <div>
                    <dt className="text-sm font-medium text-text-secondary">Industry</dt>
                    <dd className="mt-1 text-sm text-text-primary">{competitor.industry}</dd>
                  </div>
                )}
                <div>
                  <dt className="text-sm font-medium text-text-secondary">Created</dt>
                  <dd className="mt-1 text-sm text-text-primary">
                    {format(new Date(competitor.created_at), 'MMMM d, yyyy')}
                  </dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="data-sources">
          <DataSourcesManager competitorId={competitorId} />
        </TabsContent>
        <TabsContent value="insights">
          <Card>
            <CardHeader>
              <CardTitle>AI Insights</CardTitle>
            </CardHeader>
            <CardContent>
              {insightsLoading ? (
                <p className="text-text-secondary">Loading insights...</p>
              ) : insights.length === 0 ? (
                <p className="text-text-secondary">No insights available yet.</p>
              ) : (
                <div className="space-y-4">
                  {insights.map((insight) => (
                    <div key={insight.id} className="p-4 bg-background rounded">
                      <p className="text-sm text-text-primary">{insight.summary}</p>
                      <p className="text-xs text-text-secondary mt-2">
                        Sentiment: <span className="font-medium">{insight.sentiment}</span>
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="scraped-data">
          <Card>
            <CardHeader>
              <CardTitle>Scraped Data</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-text-secondary">Scraped data will be displayed here.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Modal */}
      <CompetitorModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSuccess={() => {
          setIsEditModalOpen(false)
          dispatch(fetchCompetitorByIdAsync(competitorId))
        }}
        competitor={competitor}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDelete}
        title="Delete Competitor"
        message="Are you sure you want to delete this competitor? This action cannot be undone and will delete all associated data sources and insights."
      />
    </div>
  )
}
