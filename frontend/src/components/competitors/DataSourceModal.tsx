'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { DataSource } from '@/types'

/**
 * Form validation schema
 */
const dataSourceSchema = z.object({
  source_type: z.string().min(1, 'Source type is required').max(50, 'Source type is too long'),
  url: z.string().min(1, 'URL is required').url('Invalid URL'),
  is_active: z.boolean().optional(),
})

type DataSourceFormData = z.infer<typeof dataSourceSchema>

interface DataSourceModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: DataSourceFormData) => Promise<void>
  dataSource?: DataSource
}

/**
 * Modal for adding or editing a data source
 */
export default function DataSourceModal({
  isOpen,
  onClose,
  onSubmit,
  dataSource,
}: DataSourceModalProps) {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<DataSourceFormData>({
    resolver: zodResolver(dataSourceSchema),
    defaultValues: {
      source_type: dataSource?.source_type || '',
      url: dataSource?.url || '',
      is_active: dataSource?.is_active ?? true,
    },
  })

  /**
   * Reset form when modal opens/closes or data source changes
   */
  useEffect(() => {
    if (isOpen) {
      reset({
        source_type: dataSource?.source_type || '',
        url: dataSource?.url || '',
        is_active: dataSource?.is_active ?? true,
      })
    }
  }, [isOpen, dataSource, reset])

  /**
   * Handle form submission
   */
  const handleFormSubmit = async (data: DataSourceFormData) => {
    try {
      await onSubmit(data)
      reset()
    } catch (error) {
      console.error('Failed to save data source:', error)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="flex min-h-full items-center justify-center p-4">
        <div
          className="relative bg-surface rounded-lg shadow-xl max-w-md w-full p-6"
          role="dialog"
          aria-modal="true"
        >
          {/* Close button */}
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 text-text-secondary hover:text-text-primary"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>

          {/* Header */}
          <h2 className="text-xl font-bold text-text-primary mb-4">
            {dataSource ? 'Edit Data Source' : 'Add Data Source'}
          </h2>

          {/* Form */}
          <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
            {/* Source Type */}
            <div>
              <label htmlFor="source_type" className="block text-sm font-medium text-text-primary mb-1">
                Source Type <span className="text-error">*</span>
              </label>
              <input
                id="source_type"
                type="text"
                {...register('source_type')}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="e.g., website, twitter, linkedin"
              />
              {errors.source_type && (
                <p className="mt-1 text-sm text-error">{errors.source_type.message}</p>
              )}
            </div>

            {/* URL */}
            <div>
              <label htmlFor="url" className="block text-sm font-medium text-text-primary mb-1">
                URL <span className="text-error">*</span>
              </label>
              <input
                id="url"
                type="text"
                {...register('url')}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="https://example.com"
              />
              {errors.url && (
                <p className="mt-1 text-sm text-error">{errors.url.message}</p>
              )}
            </div>

            {/* Active Status */}
            <div className="flex items-center">
              <input
                id="is_active"
                type="checkbox"
                {...register('is_active')}
                className="h-4 w-4 text-primary focus:ring-primary border-border rounded"
              />
              <label htmlFor="is_active" className="ml-2 block text-sm text-text-primary">
                Active
              </label>
            </div>

            {/* Actions */}
            <div className="flex justify-end space-x-3 mt-6">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-text-primary bg-background border border-border rounded-md hover:bg-surface focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-white bg-primary rounded-md hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSubmitting ? 'Saving...' : dataSource ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
