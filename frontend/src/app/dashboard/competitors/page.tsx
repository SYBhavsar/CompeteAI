'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAppDispatch, useAppSelector } from '@/lib/hooks'
import {
  fetchCompetitorsAsync,
  deleteCompetitorAsync,
  selectCompetitors,
  selectCompetitorsLoading,
  selectCompetitorsError,
} from '@/features/competitors/competitorsSlice'
import { PlusIcon, EyeIcon, TrashIcon } from '@heroicons/react/24/outline'
import { format } from 'date-fns'
import CompetitorModal from '@/components/competitors/CompetitorModal'
import DeleteConfirmModal from '@/components/competitors/DeleteConfirmModal'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

/**
 * Competitors list page
 * Displays all competitors in a table with actions
 */
export default function CompetitorsPage() {
  const router = useRouter()
  const dispatch = useAppDispatch()

  const competitors = useAppSelector(selectCompetitors)
  const loading = useAppSelector(selectCompetitorsLoading)
  const error = useAppSelector(selectCompetitorsError)

  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)

  /**
   * Fetch competitors on mount
   */
  useEffect(() => {
    dispatch(fetchCompetitorsAsync())
  }, [dispatch])

  /**
   * Handle view competitor details
   */
  const handleView = (id: number) => {
    router.push(`/dashboard/competitors/${id}`)
  }

  /**
   * Handle delete competitor
   */
  const handleDelete = async () => {
    if (deleteConfirmId) {
      await dispatch(deleteCompetitorAsync(deleteConfirmId))
      setDeleteConfirmId(null)
      // Refetch to update list
      dispatch(fetchCompetitorsAsync())
    }
  }

  /**
   * Show loading state
   */
  if (loading && competitors.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-text-secondary">Loading competitors...</p>
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

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Competitors</h1>
          <p className="text-sm text-text-secondary mt-1">
            Manage and monitor your competitors
          </p>
        </div>
        <Button onClick={() => setIsAddModalOpen(true)}>
          <PlusIcon className="h-5 w-5 mr-2" />
          Add Competitor
        </Button>
      </div>

      {/* Competitors Table */}
      {competitors.length === 0 ? (
        <Card className="text-center py-12">
          <CardHeader>
            <CardTitle className="text-lg">No competitors found</CardTitle>
            <CardDescription className="mt-2 text-sm text-text-secondary">
              Get started by adding your first competitor
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={() => setIsAddModalOpen(true)} className="mt-4">
              <PlusIcon className="h-5 w-5 mr-2" />
              Add Competitor
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="rounded-lg border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Domain</TableHead>
                <TableHead>Industry</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {competitors.map((competitor) => (
                <TableRow key={competitor.id} className="hover:bg-background/50">
                  <TableCell className="font-medium">
                    {competitor.name}
                  </TableCell>
                  <TableCell>{competitor.domain || '-'}</TableCell>
                  <TableCell>{competitor.industry || '-'}</TableCell>
                  <TableCell>{format(new Date(competitor.created_at), 'MMM d, yyyy')}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="icon" onClick={() => handleView(competitor.id)} aria-label="View">
                      <EyeIcon className="h-5 w-5" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => setDeleteConfirmId(competitor.id)} aria-label="Delete">
                      <TrashIcon className="h-5 w-5" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      {/* Add Competitor Modal */}
      <CompetitorModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSuccess={() => {
          setIsAddModalOpen(false)
          dispatch(fetchCompetitorsAsync())
        }}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        onConfirm={handleDelete}
        title="Delete Competitor"
        message="Are you sure you want to delete this competitor? This action cannot be undone."
      />
    </div>
  )
}
