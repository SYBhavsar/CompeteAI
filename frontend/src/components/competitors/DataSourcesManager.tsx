'use client'

import { useEffect, useState } from 'react'
import { dataSourcesService } from '@/services/dataSourcesService'
import { DataSource } from '@/types'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import DataSourceModal from './DataSourceModal'
import DeleteConfirmModal from './DeleteConfirmModal'

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
   * Fetch data sources on mount
   */
  useEffect(() => {
    fetchDataSources()
  }, [competitorId])

  /**
   * Fetch all data sources for the competitor
   */
  const fetchDataSources = async () => {
    try {
      setLoading(true)
      setError(null)
      const sources = await dataSourcesService.getByCompetitor(competitorId)
      setDataSources(sources)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch data sources')
    } finally {
      setLoading(false)
    }
  }

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
      await dataSourcesService.delete(competitorId, deleteConfirmId)
      setDeleteConfirmId(null)
      fetchDataSources()
    }
  }

  /**
   * Handle toggling data source active status
   */
  const handleToggleActive = async (dataSource: DataSource) => {
    await dataSourcesService.update(competitorId, dataSource.id, {
      is_active: !dataSource.is_active,
    })
    fetchDataSources()
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
        <button
          type="button"
          onClick={() => setIsAddModalOpen(true)}
          className="inline-flex items-center px-3 py-2 border border-transparent rounded-md text-sm font-medium text-white bg-primary hover:bg-primary/90"
        >
          <PlusIcon className="h-4 w-4 mr-2" />
          Add Data Source
        </button>
      </div>

      {/* Data Sources List */}
      {dataSources.length === 0 ? (
        <div className="text-center py-12 bg-surface border border-border rounded-lg">
          <p className="text-text-secondary text-lg">No data sources found</p>
          <p className="text-text-secondary text-sm mt-2">
            Get started by adding your first data source
          </p>
          <button
            type="button"
            onClick={() => setIsAddModalOpen(true)}
            className="mt-4 inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-primary hover:bg-primary/90"
          >
            <PlusIcon className="h-5 w-5 mr-2" />
            Add Data Source
          </button>
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-lg divide-y divide-border">
          {dataSources.map((dataSource) => (
            <div key={dataSource.id} className="p-4 hover:bg-background transition-colors">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="text-sm font-medium text-text-primary">
                      {dataSource.source_type}
                    </h4>
                    <span
                      className={`text-xs px-2 py-1 rounded ${
                        dataSource.is_active
                          ? 'bg-success/10 text-success'
                          : 'bg-error/10 text-error'
                      }`}
                    >
                      {dataSource.is_active ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                  <p className="text-sm text-text-secondary mt-1">{dataSource.url}</p>
                  {dataSource.last_scraped && (
                    <p className="text-xs text-text-secondary mt-1">
                      Last scraped: {new Date(dataSource.last_scraped).toLocaleString()}
                    </p>
                  )}
                </div>
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    type="button"
                    onClick={() => handleToggleActive(dataSource)}
                    className="text-sm text-primary hover:text-primary/90"
                    aria-label="Toggle"
                  >
                    Toggle
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditingDataSource(dataSource)}
                    className="text-primary hover:text-primary/90"
                    aria-label="Edit"
                  >
                    <PencilIcon className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeleteConfirmId(dataSource.id)}
                    className="text-error hover:text-error/90"
                    aria-label="Delete"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
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
