'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAppSelector, useAppDispatch } from '@/lib/hooks'
import { fetchCompetitorsAsync } from '@/features/competitors/competitorsSlice'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { MagnifyingGlassIcon, BookmarkIcon, ArrowDownTrayIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline'
import SearchFilters from '@/components/search/SearchFilters'
import SearchResultCard from '@/components/search/SearchResultCard'
import { SearchResult, SearchFilters as SearchFiltersType } from '@/types'
import api from '@/services/api'

type SearchType = 'semantic' | 'traditional'

export default function SearchPage() {
  const router = useRouter()
  const dispatch = useAppDispatch()
  const { competitors } = useAppSelector((state) => state.competitors)

  const [searchType, setSearchType] = useState<SearchType>('semantic')
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState<SearchFiltersType>({
    dateFrom: null,
    dateTo: null,
    competitorIds: [],
    sentiment: null,
  })
  const [results, setResults] = useState<SearchResult[]>([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalResults, setTotalResults] = useState(0)
  const pageSize = 10

  useEffect(() => {
    dispatch(fetchCompetitorsAsync())
  }, [dispatch])

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    setSearched(true)
    setCurrentPage(1)

    try {
      const endpoint = searchType === 'semantic' ? '/search/semantic' : '/search/traditional'
      const method = searchType === 'semantic' ? 'post' : 'get'

      const response = method === 'post'
        ? await api.post(endpoint, { query })
        : await api.get(endpoint, { params: { query } })

      setResults(response.data.results || [])
      setTotalResults(response.data.total || 0)
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
      setTotalResults(0)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSearch = () => {
    // TODO: Implement save search modal
    console.log('Save search')
  }

  const handleExport = () => {
    const dataStr = JSON.stringify(paginatedResults, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `search-results-${new Date().toISOString()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const totalPages = Math.ceil(totalResults / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const paginatedResults = results.slice(startIndex, endIndex)

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1)
    }
  }

  const handlePrevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Search Insights</h1>
          <p className="text-muted-foreground">Search through competitive intelligence data</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleSaveSearch} variant="outline">
            <BookmarkIcon className="h-5 w-5 mr-2" />
            Save Search
          </Button>
        </div>
      </div>

      {/* Sub-navigation */}
      <div className="flex gap-2">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/dashboard/search/saved')}
        >
          Saved Searches
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push('/dashboard/search/history')}
        >
          Search History
        </Button>
      </div>

      <Card className="p-6">
        <div className="space-y-4">
          {/* Search Type Toggle */}
          <div className="flex gap-2">
            <Button
              variant={searchType === 'semantic' ? 'default' : 'outline'}
              onClick={() => setSearchType('semantic')}
              data-active={searchType === 'semantic'}
            >
              Semantic
            </Button>
            <Button
              variant={searchType === 'traditional' ? 'default' : 'outline'}
              onClick={() => setSearchType('traditional')}
              data-active={searchType === 'traditional'}
            >
              Traditional
            </Button>
          </div>

          {/* Search Input */}
          <div className="flex gap-2">
            <Input
              placeholder="Search insights..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch} disabled={loading}>
              <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
              Search
            </Button>
          </div>

          {/* Filters Panel */}
          <SearchFilters competitors={competitors} onFilterChange={setFilters} />
        </div>
      </Card>

      {/* Results */}
      {loading && (
        <div className="text-center py-8">
          <p>Loading results...</p>
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="text-center py-8">
          <p className="text-muted-foreground">No results found</p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Showing {totalResults} results
            </p>
            <Button onClick={handleExport} variant="outline" size="sm">
              <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>

          <div className="space-y-4">
            {paginatedResults.map((result) => (
              <SearchResultCard key={result.id} result={result} searchType={searchType} />
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
    </div>
  )
}
