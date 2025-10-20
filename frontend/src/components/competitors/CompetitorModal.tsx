'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAppDispatch } from '@/lib/hooks'
import { createCompetitorAsync, updateCompetitorAsync } from '@/features/competitors/competitorsSlice'
import { XMarkIcon } from '@heroicons/react/24/outline'
import { Competitor } from '@/types'

/**
 * Form validation schema
 */
const competitorSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100, 'Name is too long'),
  domain: z.string().url('Invalid URL').optional().or(z.literal('')),
  industry: z.string().max(100, 'Industry name is too long').optional().or(z.literal('')),
})

type CompetitorFormData = z.infer<typeof competitorSchema>

interface CompetitorModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
  competitor?: Competitor
}

/**
 * Modal for adding or editing a competitor
 */
export default function CompetitorModal({
  isOpen,
  onClose,
  onSuccess,
  competitor,
}: CompetitorModalProps) {
  const dispatch = useAppDispatch()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<CompetitorFormData>({
    resolver: zodResolver(competitorSchema),
    defaultValues: {
      name: competitor?.name || '',
      domain: competitor?.domain || '',
      industry: competitor?.industry || '',
    },
  })

  /**
   * Reset form when modal opens/closes or competitor changes
   */
  useEffect(() => {
    if (isOpen) {
      reset({
        name: competitor?.name || '',
        domain: competitor?.domain || '',
        industry: competitor?.industry || '',
      })
    }
  }, [isOpen, competitor, reset])

  /**
   * Handle form submission
   */
  const onSubmit = async (data: CompetitorFormData) => {
    try {
      if (competitor) {
        // Update existing competitor
        await dispatch(
          updateCompetitorAsync({
            id: competitor.id,
            data: {
              name: data.name,
              domain: data.domain || undefined,
              industry: data.industry || undefined,
            },
          })
        ).unwrap()
      } else {
        // Create new competitor
        await dispatch(
          createCompetitorAsync({
            name: data.name,
            domain: data.domain || undefined,
            industry: data.industry || undefined,
          })
        ).unwrap()
      }

      onSuccess()
      reset()
    } catch (error) {
      // Error is handled by Redux slice
      console.error('Failed to save competitor:', error)
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
            {competitor ? 'Edit Competitor' : 'Add Competitor'}
          </h2>

          {/* Form */}
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            {/* Name */}
            <div>
              <label htmlFor="name" className="block text-sm font-medium text-text-primary mb-1">
                Name <span className="text-error">*</span>
              </label>
              <input
                id="name"
                type="text"
                {...register('name')}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="Enter competitor name"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-error">{errors.name.message}</p>
              )}
            </div>

            {/* Domain */}
            <div>
              <label htmlFor="domain" className="block text-sm font-medium text-text-primary mb-1">
                Domain
              </label>
              <input
                id="domain"
                type="text"
                {...register('domain')}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="https://example.com"
              />
              {errors.domain && (
                <p className="mt-1 text-sm text-error">{errors.domain.message}</p>
              )}
            </div>

            {/* Industry */}
            <div>
              <label htmlFor="industry" className="block text-sm font-medium text-text-primary mb-1">
                Industry
              </label>
              <input
                id="industry"
                type="text"
                {...register('industry')}
                className="w-full px-3 py-2 border border-border rounded-md bg-background text-text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
                placeholder="e.g., Technology, Finance"
              />
              {errors.industry && (
                <p className="mt-1 text-sm text-error">{errors.industry.message}</p>
              )}
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
                {isSubmitting ? 'Saving...' : competitor ? 'Update' : 'Create'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  )
}
