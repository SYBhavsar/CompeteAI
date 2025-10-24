'use client'

import { useEffect, useState, useMemo, useCallback, lazy, Suspense } from 'react'
import { useRouter } from 'next/navigation'
import { useAppDispatch, useAppSelector } from '@/lib/hooks'
import { usePageTitle } from '@/hooks/usePageTitle'
import {
  fetchCompetitorsAsync,
  deleteCompetitorAsync,
  selectCompetitors,
  selectCompetitorsLoading,
  selectCompetitorsError,
} from '@/features/competitors/competitorsSlice'
import { PlusIcon, EyeIcon, TrashIcon } from '@heroicons/react/24/outline'
import { format } from 'date-fns'

// Lazy load modal components for better performance
const CompetitorModal = lazy(() => import('@/components/competitors/CompetitorModal'))
const DeleteConfirmModal = lazy(() => import('@/components/competitors/DeleteConfirmModal'))
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
import TableSkeleton from '@/components/ui/TableSkeleton'
import toast from 'react-hot-toast'

const ITEMS_PER_PAGE = 10

/**
 * Competitors list page
 * Displays all competitors in a table with actions
 */
export default function CompetitorsPage() {
  usePageTitle('Competitors')

  const router = useRouter()
  const dispatch = useAppDispatch()

  const competitors = useAppSelector(selectCompetitors)
  const loading = useAppSelector(selectCompetitorsLoading)
  const error = useAppSelector(selectCompetitorsError)

  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  useEffect(() => {
    dispatch(fetchCompetitorsAsync())
  }, [dispatch])

  const filteredCompetitors = useMemo(() => {
    if (!searchQuery.trim()) return competitors

    const query = searchQuery.toLowerCase()
    return competitors.filter(
      (competitor) =>
        competitor.name.toLowerCase().includes(query) ||
        competitor.domain?.toLowerCase().includes(query) ||
        competitor.industry?.toLowerCase().includes(query)
    )
  }, [competitors, searchQuery])

  const paginatedCompetitors = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE
    const endIndex = startIndex + ITEMS_PER_PAGE
    return filteredCompetitors.slice(startIndex, endIndex)
  }, [filteredCompetitors, currentPage])

  const totalPages = Math.ceil(filteredCompetitors.length / ITEMS_PER_PAGE)

  useEffect(() => {
    setCurrentPage(1)
  }, [searchQuery])

  /**
   * Handle view competitor details
   */
  const handleView = useCallback((id: number) => {
    router.push(`/dashboard/competitors/${id}`)
  }, [router])

  /**
   * Handle delete competitor
   */
  const handleDelete = useCallback(async () => {
    if (deleteConfirmId) {
      try {
        await dispatch(deleteCompetitorAsync(deleteConfirmId)).unwrap()
        toast.success('Competitor deleted successfully')
        setDeleteConfirmId(null)
        // Refetch to update list
        dispatch(fetchCompetitorsAsync())
      } catch (error) {
        toast.error('Failed to delete competitor')
      }
    }
  }, [deleteConfirmId, dispatch])

  /**
   * Show loading state
   */
  if (loading && competitors.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Competitors</h1>
            <p className="text-sm text-text-secondary mt-1">
              Manage and monitor your competitors
            </p>
          </div>
        </div>
        <TableSkeleton rows={5} columns={5} />
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

      {competitors.length > 0 && (
        <div className="flex items-center gap-4">
          <Input
            type="text"
            placeholder="Search competitors..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="max-w-sm"
            aria-label="Search competitors"
          />
        </div>
      )}

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
      ) : filteredCompetitors.length === 0 ? (
        <Card className="text-center py-12">
          <CardHeader>
            <CardTitle className="text-lg">No results found</CardTitle>
            <CardDescription className="mt-2 text-sm text-text-secondary">
              Try adjusting your search query
            </CardDescription>
          </CardHeader>
        </Card>
      ) : (
        <>
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
                {paginatedCompetitors.map((competitor) => (
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

          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-text-secondary">
                Showing {(currentPage - 1) * ITEMS_PER_PAGE + 1} to{' '}
                {Math.min(currentPage * ITEMS_PER_PAGE, filteredCompetitors.length)} of{' '}
                {filteredCompetitors.length} results
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Add Competitor Modal */}
      {isAddModalOpen && (
        <Suspense fallback={null}>
          <CompetitorModal
            isOpen={isAddModalOpen}
            onClose={() => setIsAddModalOpen(false)}
            onSuccess={() => {
              setIsAddModalOpen(false)
              dispatch(fetchCompetitorsAsync())
            }}
          />
        </Suspense>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmId !== null && (
        <Suspense fallback={null}>
          <DeleteConfirmModal
            isOpen={deleteConfirmId !== null}
            onClose={() => setDeleteConfirmId(null)}
            onConfirm={handleDelete}
            title="Delete Competitor"
            message="Are you sure you want to delete this competitor? This action cannot be undone."
          />
        </Suspense>
      )}
    </div>
  )
}
