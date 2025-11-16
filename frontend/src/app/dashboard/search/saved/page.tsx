'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { PlayIcon, TrashIcon } from '@heroicons/react/24/outline'
import { SavedSearch } from '@/types'
import api from '@/services/api'
import toast from 'react-hot-toast'

export default function SavedSearchesPage() {
  const router = useRouter()
  const [savedSearches, setSavedSearches] = useState<SavedSearch[]>([])
  const [loading, setLoading] = useState(true)

  const fetchSavedSearches = useCallback(async () => {
    try {
      setLoading(true)
      const response = await api.get('/search/saved')
      setSavedSearches(response.data)
    } catch (error) {
      console.error('Failed to fetch saved searches:', error)
      toast.error('Failed to fetch saved searches.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchSavedSearches()
  }, [fetchSavedSearches])

  const handleExecute = useCallback((search: SavedSearch) => {
    // Navigate to search page with query params
    router.push('/dashboard/search')
  }, [router])

  const handleDelete = useCallback(async (id: number) => {
    try {
      await api.delete(`/search/saved/${id}`)
      setSavedSearches((prev) => prev.filter((s) => s.id !== id))
      toast.success('Saved search deleted.')
    } catch (error) {
      console.error('Failed to delete saved search:', error)
      toast.error('Failed to delete saved search.')
    }
  }, [])

  const formatDate = useCallback((dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }, [])

  if (loading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Saved Searches</h1>
          <p className="text-muted-foreground">Your saved search queries</p>
        </div>
        <div className="text-center py-8">
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      <div>
        <h1 className="text-xl sm:text-3xl font-bold">Saved Searches</h1>
        <p className="text-sm text-muted-foreground">Your saved search queries</p>
      </div>

      {savedSearches.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">No saved searches yet</p>
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
          {savedSearches.map((search) => (
            <Card key={search.id} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="text-lg font-semibold">{search.name}</h3>
                    <Badge variant="outline">{search.search_type}</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">{search.query}</p>
                  <p className="text-xs text-muted-foreground">
                    Created: {formatDate(search.created_at)}
                  </p>
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleExecute(search)}
                  >
                    <PlayIcon className="h-4 w-4 mr-1" />
                    Execute
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(search.id)}
                  >
                    <TrashIcon className="h-4 w-4 mr-1" />
                    Delete
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
