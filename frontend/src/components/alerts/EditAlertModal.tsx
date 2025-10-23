import { useState, useEffect } from 'react'
import { useAppSelector, useAppDispatch } from '@/lib/hooks'
import { updateAlertAsync } from '@/features/alerts/alertsSlice'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Alert } from '@/types'

interface EditAlertModalProps {
  alert: Alert | null
  isOpen: boolean
  onClose: () => void
}

type AlertType = 'sentiment_change' | 'new_content' | 'keyword_match'

export default function EditAlertModal({ alert, isOpen, onClose }: EditAlertModalProps) {
  const dispatch = useAppDispatch()
  const { competitors } = useAppSelector((state) => state.competitors)

  const [alertType, setAlertType] = useState<AlertType>('new_content')
  const [competitorId, setCompetitorId] = useState<string>('all')
  const [isActive, setIsActive] = useState(true)
  const [threshold, setThreshold] = useState('0.5')
  const [keywords, setKeywords] = useState('')

  useEffect(() => {
    if (alert) {
      setAlertType(alert.alert_type)
      setCompetitorId(alert.competitor_id ? alert.competitor_id.toString() : 'all')
      setIsActive(alert.is_active)

      if (alert.alert_type === 'sentiment_change' && alert.conditions) {
        setThreshold(alert.conditions.threshold?.toString() || '0.5')
      }

      if (alert.alert_type === 'keyword_match' && alert.conditions) {
        const keywordArray = alert.conditions.keywords as string[]
        setKeywords(keywordArray?.join(', ') || '')
      }
    }
  }, [alert])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!alert) return

    const conditions: Record<string, unknown> = {}

    if (alertType === 'sentiment_change') {
      conditions.threshold = parseFloat(threshold)
    } else if (alertType === 'keyword_match') {
      conditions.keywords = keywords.split(',').map((k) => k.trim())
    }

    await dispatch(
      updateAlertAsync({
        id: alert.id,
        data: {
          competitor_id: competitorId !== 'all' ? parseInt(competitorId) : null,
          alert_type: alertType,
          conditions,
          is_active: isActive,
        },
      })
    )

    onClose()
  }

  if (!alert) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Edit Alert</DialogTitle>
          <DialogDescription>
            Update alert configuration
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Alert Type */}
          <div>
            <Label htmlFor="alert-type">Alert Type</Label>
            <Select value={alertType} onValueChange={(v) => setAlertType(v as AlertType)}>
              <SelectTrigger id="alert-type">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="sentiment_change">Sentiment Change</SelectItem>
                <SelectItem value="new_content">New Content</SelectItem>
                <SelectItem value="keyword_match">Keyword Match</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Competitor */}
          <div>
            <Label htmlFor="competitor">Competitor</Label>
            <Select value={competitorId} onValueChange={setCompetitorId}>
              <SelectTrigger id="competitor">
                <SelectValue placeholder="All Competitors" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Competitors</SelectItem>
                {competitors?.map((competitor) => (
                  <SelectItem key={competitor.id} value={competitor.id.toString()}>
                    {competitor.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Conditions based on alert type */}
          {alertType === 'sentiment_change' && (
            <div>
              <Label htmlFor="threshold">Sentiment Threshold</Label>
              <Input
                id="threshold"
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
              />
            </div>
          )}

          {alertType === 'keyword_match' && (
            <div>
              <Label htmlFor="keywords">Keywords (comma-separated)</Label>
              <Input
                id="keywords"
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="keyword1, keyword2, keyword3"
              />
            </div>
          )}

          {/* Active Toggle */}
          <div className="flex items-center gap-2">
            <input
              id="is-active"
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4"
            />
            <Label htmlFor="is-active">Active</Label>
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit">Update</Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
