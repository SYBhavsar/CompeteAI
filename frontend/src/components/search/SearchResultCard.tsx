'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { SearchResult } from '@/types'

interface SearchResultCardProps {
  result: SearchResult
  searchType?: 'semantic' | 'traditional'
}

export default function SearchResultCard({ result, searchType }: SearchResultCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const shouldShowExpand = result.content.length > 200

  const getSentimentVariant = (sentiment: string) => {
    switch (sentiment.toLowerCase()) {
      case 'positive':
        return 'default'
      case 'negative':
        return 'destructive'
      case 'neutral':
        return 'secondary'
      default:
        return 'secondary'
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  const displayContent = shouldShowExpand && !isExpanded
    ? result.content.slice(0, 200) + '...'
    : result.content

  return (
    <Card className="p-4">
      <div className="space-y-2">
        <div className="flex items-start justify-between gap-4">
          <p className="flex-1">{displayContent}</p>
          <Badge variant={getSentimentVariant(result.sentiment)}>
            {result.sentiment}
          </Badge>
        </div>

        {shouldShowExpand && (
          <Button
            variant="link"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-0 h-auto"
          >
            {isExpanded ? 'Show less' : 'Read more'}
          </Button>
        )}

        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <span>Source: {result.source}</span>
          <span>Score: {result.quality_score}</span>
          {searchType === 'semantic' && result.relevance_score && (
            <span>Relevance: {result.relevance_score}</span>
          )}
          <span>{formatDate(result.created_at)}</span>
        </div>
      </div>
    </Card>
  )
}
