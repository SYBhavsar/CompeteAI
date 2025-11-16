'use client'

import { useEffect, useState, useCallback } from 'react'
import { dataSourcesService } from '@/services/dataSourcesService'
import { DataSource } from '@/types'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import DataSourceModal from './DataSourceModal'
import DeleteConfirmModal from './DeleteConfirmModal'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import toast from 'react-hot-toast'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

interface DataSourcesManagerProps {
  competitorId: number
}

/**
 * Data Sources Manager component
 * Manages data sources for a competitor
 */
export default function DataSourcesManager({ competitorId }: DataSourcesManagerProps) {
  const [dataSources, setDataSources] = useState<DataSource[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [editingDataSource, setEditingDataSource] = useState<DataSource | null>(null)
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null)

  /**
   * Fetch all data sources for the competitor
   */
  const fetchDataSources = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const sources = await dataSourcesService.getByCompetitor(competitorId)
      setDataSources(sources)
    } catch (err) {
      const error = err as { response?: { data?: { detail?: string } } }
      setError(error.response?.data?.detail || 'Failed to fetch data sources')
    } finally {
      setLoading(false)
    }
  }, [competitorId])

  /**
   * Fetch data sources on mount
   */
  useEffect(() => {
    fetchDataSources()
  }, [fetchDataSources])

  /**
   * Handle creating a new data source
   */
  const handleCreate = async (data: { source_type: string; url: string; is_active?: boolean }) => {
    await dataSourcesService.create(competitorId, data)
    setIsAddModalOpen(false)
    fetchDataSources()
  }

  /**
   * Handle updating an existing data source
   */
  const handleUpdate = async (data: { source_type: string; url: string; is_active?: boolean }) => {
    if (editingDataSource) {
      await dataSourcesService.update(competitorId, editingDataSource.id, data)
      setEditingDataSource(null)
      fetchDataSources()
    }
  }

  /**
   * Handle deleting a data source
   */
  const handleDelete = async () => {
    if (deleteConfirmId) {
      try {
        await dataSourcesService.delete(competitorId, deleteConfirmId)
        toast.success('Data source deleted successfully')
        setDeleteConfirmId(null)
        fetchDataSources()
      } catch (error) {
        toast.error('Failed to delete data source')
      }
    }
  }

  /**
   * Handle toggling data source active status
   */
  const handleToggleActive = async (dataSource: DataSource) => {
    try {
      await dataSourcesService.update(competitorId, dataSource.id, {
        is_active: !dataSource.is_active,
      })
      toast.success(`Data source ${dataSource.is_active ? 'deactivated' : 'activated'}`)
      fetchDataSources()
    } catch (error) {
      toast.error('Failed to toggle data source status')
    }
  }

  /**
   * Show loading state
   */
  if (loading && dataSources.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-text-secondary">Loading data sources...</p>
      </div>
    )
  }

  /**
   * Show error state
   */
  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-error">Error: {error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-text-primary">Data Sources</h3>
        <Button onClick={() => setIsAddModalOpen(true)}>
          <PlusIcon className="h-4 w-4 mr-2" />
          Add Data Source
        </Button>
      </div>

      {/* Data Sources Table */}
      {dataSources.length === 0 ? (
        <div className="text-center py-12 bg-surface border border-border rounded-lg">
          <p className="text-text-secondary text-lg">No data sources found</p>
          <p className="text-text-secondary text-sm mt-2">
            Get started by adding your first data source
          </p>
          <Button onClick={() => setIsAddModalOpen(true)} className="mt-4">
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Data Source
          </Button>
        </div>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Source Type</TableHead>
              <TableHead>URL</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Last Scraped</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {dataSources.map((dataSource) => (
              <TableRow key={dataSource.id}>
                <TableCell className="font-medium">{dataSource.source_type}</TableCell>
                <TableCell>{dataSource.url}</TableCell>
                <TableCell>
                  <Badge variant={dataSource.is_active ? 'default' : 'destructive'}>
                    {dataSource.is_active ? 'Active' : 'Inactive'}
                  </Badge>
                </TableCell>
                <TableCell>{dataSource.last_scraped ? new Date(dataSource.last_scraped).toLocaleString() : 'Never'}</TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleToggleActive(dataSource)}
                    aria-label="Toggle"
                  >
                    Toggle
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setEditingDataSource(dataSource)} aria-label="Edit">
                    <PencilIcon className="h-4 w-4" />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={() => setDeleteConfirmId(dataSource.id)} aria-label="Delete">
                    <TrashIcon className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      {/* Add Data Source Modal */}
      <DataSourceModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        onSubmit={handleCreate}
      />

      {/* Edit Data Source Modal */}
      <DataSourceModal
        isOpen={editingDataSource !== null}
        onClose={() => setEditingDataSource(null)}
        onSubmit={handleUpdate}
        dataSource={editingDataSource || undefined}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmModal
        isOpen={deleteConfirmId !== null}
        onClose={() => setDeleteConfirmId(null)}
        onConfirm={handleDelete}
        title="Delete Data Source"
        message="Are you sure you want to delete this data source? This action cannot be undone."
      />
    </div>
  )
}
