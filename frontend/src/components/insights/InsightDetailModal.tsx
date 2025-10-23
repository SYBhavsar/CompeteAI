import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ProcessedInsight } from '@/types'

interface InsightDetailModalProps {
  insight: ProcessedInsight | null
  isOpen: boolean
  onClose: () => void
}

export default function InsightDetailModal({ insight, isOpen, onClose }: InsightDetailModalProps) {
  if (!insight) return null

  const getSentimentColor = (sentiment: string) => {
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
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Insight Details</DialogTitle>
          <DialogDescription className="sr-only">
            Detailed view of the selected insight
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Summary */}
          <div>
            <h3 className="text-lg font-semibold mb-2">{insight.summary}</h3>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span>Created: {formatDate(insight.created_at)}</span>
              <Badge variant={getSentimentColor(insight.sentiment)}>
                {insight.sentiment}
              </Badge>
              <span>Quality: {insight.quality_score?.toFixed(2) || 'N/A'}</span>
            </div>
          </div>

          {/* Detailed Insights */}
          <div>
            <h4 className="text-sm font-semibold mb-2">Details</h4>
            <p className="text-sm text-muted-foreground">{insight.insights}</p>
          </div>

          {/* Key Points */}
          {insight.key_points && insight.key_points.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2">Key Points</h4>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
                {insight.key_points.map((point, idx) => (
                  <li key={idx}>{point}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button onClick={onClose} variant="outline">
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
