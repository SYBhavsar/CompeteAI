'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Competitor, SearchFilters } from '@/types'

interface SearchFiltersProps {
  competitors: Competitor[]
  onFilterChange: (filters: SearchFilters) => void
}

export default function SearchFilters({ competitors, onFilterChange }: SearchFiltersProps) {
  const [filters, setFilters] = useState<SearchFilters>({
    dateFrom: null,
    dateTo: null,
    competitorIds: [],
    sentiment: null,
  })

  const handleDateChange = (field: 'dateFrom' | 'dateTo', value: string) => {
    const newFilters = { ...filters, [field]: value || null }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleCompetitorChange = (competitorId: string) => {
    const id = parseInt(competitorId)
    const newFilters = {
      ...filters,
      competitorIds: filters.competitorIds.includes(id)
        ? filters.competitorIds.filter((cid) => cid !== id)
        : [...filters.competitorIds, id],
    }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleSentimentChange = (sentiment: string) => {
    const newFilters = { ...filters, sentiment }
    setFilters(newFilters)
    onFilterChange(newFilters)
  }

  const handleClearFilters = () => {
    const clearedFilters = {
      dateFrom: null,
      dateTo: null,
      competitorIds: [],
      sentiment: null,
    }
    setFilters(clearedFilters)
    onFilterChange(clearedFilters)
  }

  return (
    <div className="border-t pt-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold">Filters</h3>
        <Button variant="ghost" size="sm" onClick={handleClearFilters}>
          Clear Filters
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Date Range */}
        <div>
          <Label htmlFor="date-range">Date Range</Label>
          <Input
            type="date"
            id="date-range"
            value={filters.dateFrom || ''}
            onChange={(e) => handleDateChange('dateFrom', e.target.value)}
          />
        </div>

        {/* Competitor Select */}
        <div>
          <Label>Competitor</Label>
          <Select onValueChange={handleCompetitorChange}>
            <SelectTrigger aria-label="Competitor">
              <SelectValue placeholder="Select competitor" />
            </SelectTrigger>
            <SelectContent>
              {competitors?.length > 0 ? (
                competitors.map((competitor) => (
                  <SelectItem key={competitor.id} value={competitor.id.toString()}>
                    {competitor.name}
                  </SelectItem>
                ))
              ) : (
                <div className="p-2 text-sm text-muted-foreground">No competitors available</div>
              )}
            </SelectContent>
          </Select>
        </div>

        {/* Sentiment Filter */}
        <div>
          <Label>Sentiment</Label>
          <div className="flex gap-2 mt-2" role="radiogroup" aria-label="Sentiment">
            <label className="flex items-center gap-1">
              <input
                type="radio"
                name="sentiment"
                value="positive"
                checked={filters.sentiment === 'positive'}
                onChange={(e) => handleSentimentChange(e.target.value)}
                aria-label="Positive"
              />
              Positive
            </label>
            <label className="flex items-center gap-1">
              <input
                type="radio"
                name="sentiment"
                value="negative"
                checked={filters.sentiment === 'negative'}
                onChange={(e) => handleSentimentChange(e.target.value)}
                aria-label="Negative"
              />
              Negative
            </label>
            <label className="flex items-center gap-1">
              <input
                type="radio"
                name="sentiment"
                value="neutral"
                checked={filters.sentiment === 'neutral'}
                onChange={(e) => handleSentimentChange(e.target.value)}
                aria-label="Neutral"
              />
              Neutral
            </label>
          </div>
        </div>
      </div>
    </div>
  )
}
