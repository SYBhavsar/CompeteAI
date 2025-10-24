'use client'

import { useState, useEffect, useCallback, lazy, Suspense } from 'react'
import { useAppSelector, useAppDispatch } from '@/lib/hooks'
import { usePageTitle } from '@/hooks/usePageTitle'
import { fetchAlertsAsync, updateAlertAsync, deleteAlertAsync } from '@/features/alerts/alertsSlice'
import { fetchCompetitorsAsync } from '@/features/competitors/competitorsSlice'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { TrashIcon, PencilIcon } from '@heroicons/react/24/outline'

// Lazy load modal components for better performance
const CreateAlertModal = lazy(() => import('@/components/alerts/CreateAlertModal'))
const EditAlertModal = lazy(() => import('@/components/alerts/EditAlertModal'))

import CardListSkeleton from '@/components/ui/CardListSkeleton'
import { Alert } from '@/types'
import toast from 'react-hot-toast'

export default function AlertsPage() {
  usePageTitle('Alerts')

  const dispatch = useAppDispatch()
  const { alerts, loading } = useAppSelector((state) => state.alerts)
  const { competitors } = useAppSelector((state) => state.competitors)

  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null)

  useEffect(() => {
    dispatch(fetchAlertsAsync())
    dispatch(fetchCompetitorsAsync())
  }, [dispatch])

  const handleToggleStatus = useCallback(async (id: number, currentStatus: boolean) => {
    try {
      await dispatch(updateAlertAsync({ id, data: { is_active: !currentStatus } })).unwrap()
      toast.success(currentStatus ? 'Alert deactivated' : 'Alert activated')
    } catch (error) {
      toast.error('Failed to update alert')
    }
  }, [dispatch])

  const handleEdit = useCallback((alert: Alert) => {
    setSelectedAlert(alert)
    setIsEditModalOpen(true)
  }, [])

  const handleDelete = useCallback(async (id: number) => {
    if (confirm('Are you sure you want to delete this alert?')) {
      try {
        await dispatch(deleteAlertAsync(id)).unwrap()
        toast.success('Alert deleted successfully')
      } catch (error) {
        toast.error('Failed to delete alert')
      }
    }
  }, [dispatch])

  const getCompetitorName = (competitorId: number | null) => {
    if (!competitorId) return 'All Competitors'
    const competitor = competitors?.find((c) => c.id === competitorId)
    return competitor?.name || 'Unknown'
  }

  const formatAlertType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Alerts</h1>
          <p className="text-muted-foreground">Manage your monitoring alerts</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          Create Alert
        </Button>
      </div>

      {loading ? (
        <CardListSkeleton count={3} />
      ) : alerts.length === 0 ? (
        <Card className="p-8 text-center">
          <p className="text-muted-foreground">No alerts configured</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <Card key={alert.id} className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold">
                      {formatAlertType(alert.alert_type)}
                    </h3>
                    <Badge variant={alert.is_active ? 'default' : 'secondary'}>
                      {alert.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-2">
                    Competitor: {getCompetitorName(alert.competitor_id)}
                  </p>
                  {alert.conditions && Object.keys(alert.conditions).length > 0 && (
                    <div className="text-sm text-muted-foreground">
                      Conditions: {JSON.stringify(alert.conditions)}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleToggleStatus(alert.id, alert.is_active)}
                    aria-label={`Toggle alert ${alert.id}`}
                  >
                    {alert.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(alert)}
                    aria-label={`Edit alert ${alert.id}`}
                  >
                    <PencilIcon className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleDelete(alert.id)}
                    aria-label={`Delete alert ${alert.id}`}
                  >
                    <TrashIcon className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Create Alert Modal */}
      {isCreateModalOpen && (
        <Suspense fallback={null}>
          <CreateAlertModal isOpen={isCreateModalOpen} onClose={() => setIsCreateModalOpen(false)} />
        </Suspense>
      )}

      {/* Edit Alert Modal */}
      {isEditModalOpen && (
        <Suspense fallback={null}>
          <EditAlertModal
            alert={selectedAlert}
            isOpen={isEditModalOpen}
            onClose={() => {
              setIsEditModalOpen(false)
              setSelectedAlert(null)
            }}
          />
        </Suspense>
      )}
    </div>
  )
}
