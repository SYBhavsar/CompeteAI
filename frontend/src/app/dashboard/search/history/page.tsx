'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PlayIcon, TrashIcon } from '@heroicons/react/24/outline'
import { SearchHistory } from '@/types'
import api from '@/services/api'
import toast from 'react-hot-toast'

export default function SearchHistoryPage() {
  const router = useRouter()
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([])
  const [loading, setLoading] = useState(true)

  const fetchSearchHistory = useCallback(async () => {
    try {
      setLoading(true)
      const response = await api.get('/search/history')
      setSearchHistory(response.data)
    } catch (error) {
      console.error('Failed to fetch search history:', error)
      toast.error('Failed to fetch search history.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSearchHistory()
  }, [fetchSearchHistory])

  const handleRerun = useCallback((history: SearchHistory) => {
    // Navigate to search page
    router.push('/dashboard/search')
  }, [router])

  const handleClearHistory = useCallback(async () => {
    try {
      await api.delete('/search/history')
      setSearchHistory([])
      toast.success('Search history cleared.')
    } catch (error) {
      console.error('Failed to clear search history:', error)
      toast.error('Failed to clear search history.')
    }
  }, [])

  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }, [])

  const formatTime = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleTimeString()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Search History</h1>
          <p className="text-muted-foreground">Your recent searches</p>
        </div>
        <div className="text-center py-8">
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-3xl font-bold">Search History</h1>
          <p className="text-sm text-muted-foreground">Your recent searches</p>
        </div>
        {searchHistory.length > 0 && (
          <Button variant="outline" onClick={handleClearHistory}>
            <TrashIcon className="h-4 w-4 mr-2" />
            Clear History
          </Button>
        )}
      </div>

      {searchHistory.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">No search history yet</p>
          <Button
            variant="link"
            onClick={() => router.push('/dashboard/search')}
            className="mt-4"
          >
            Go to Search
          </Button>
        </Card>
      ) : (
        <div className="space-y-4">
          {searchHistory.map((history) => (
            <Card key={history.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <p className="text-lg font-semibold">{history.query}</p>
                    <Badge variant="outline">{history.search_type}</Badge>
                  </div>
                  <div className="flex items-center gap-4 text-sm text-muted-foreground">
                    <span>{history.results_count || 0} results</span>
                    <span>
                      {formatDate(history.executed_at)} at {formatTime(history.executed_at)}
                    </span>
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleRerun(history)}
                  >
                    <PlayIcon className="h-4 w-4 mr-1" />
                    Re-run
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
