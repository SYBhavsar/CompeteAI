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
        <button
          type="button"
          onClick={() => setIsAddModalOpen(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Add Competitor
        </button>
      </div>

      {/* Competitors Table */}
      {competitors.length === 0 ? (
        <div className="text-center py-12 bg-surface border border-border rounded-lg">
          <p className="text-text-secondary text-lg">No competitors found</p>
          <p className="text-text-secondary text-sm mt-2">
            Get started by adding your first competitor
          </p>
          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Competitor
          </button>
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-border">
            <thead className="bg-background">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Domain
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Industry
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-text-secondary uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {competitors.map((competitor) => (
                <tr key={competitor.id} className="hover:bg-background transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-text-primary">
                      {competitor.name}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-text-secondary">
                      {competitor.domain || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-text-secondary">
                      {competitor.industry || '-'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-text-secondary">
                      {format(new Date(competitor.created_at), 'MMM d, yyyy')}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                    <button
                      type="button"
                      onClick={() => handleView(competitor.id)}
                      className="text-primary hover:text-primary/90 inline-flex items-center"
                      aria-label="View"
                    >
                      <EyeIcon className="h-5 w-5 mr-1" />
                      View
                    </button>
                    <button
                      type="button"
                      onClick={() => setDeleteConfirmId(competitor.id)}
                      className="text-error hover:text-error/90 inline-flex items-center ml-4"
                      aria-label="Delete"
                    >
                      <TrashIcon className="h-5 w-5 mr-1" />
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
