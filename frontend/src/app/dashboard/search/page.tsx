'use client'

import { useState, useEffect } from 'react'
import { useAppSelector, useAppDispatch } from '@/lib/hooks'
import { fetchCompetitorsAsync } from '@/features/competitors/competitorsSlice'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import SearchFilters from '@/components/search/SearchFilters'
import SearchResultCard from '@/components/search/SearchResultCard'
import { SearchResult, SearchFilters as SearchFiltersType } from '@/types'
import api from '@/services/api'

type SearchType = 'semantic' | 'traditional'

export default function SearchPage() {
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

  useEffect(() => {
    dispatch(fetchCompetitorsAsync())
  }, [dispatch])

  const handleSearch = async () => {
    if (!query.trim()) return

    setLoading(true)
    setSearched(true)

    try {
      const endpoint = searchType === 'semantic' ? '/search/semantic' : '/search/traditional'
      const method = searchType === 'semantic' ? 'post' : 'get'

      const response = method === 'post'
        ? await api.post(endpoint, { query })
        : await api.get(endpoint, { params: { query } })

      setResults(response.data.results || [])
    } catch (error) {
      console.error('Search failed:', error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Search Insights</h1>
        <p className="text-muted-foreground">Search through competitive intelligence data</p>
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
        <div className="space-y-4">
          {results.map((result) => (
            <SearchResultCard key={result.id} result={result} searchType={searchType} />
          ))}
        </div>
      )}
    </div>
  )
}
