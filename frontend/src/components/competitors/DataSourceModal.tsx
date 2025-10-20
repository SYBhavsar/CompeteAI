'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { DataSource } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

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
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{dataSource ? 'Edit Data Source' : 'Add Data Source'}</DialogTitle>
          <DialogDescription>
            {dataSource ? 'Update the details of your data source.' : 'Add a new data source to track.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="source_type" className="text-right">
                Source Type <span className="text-error">*</span>
              </Label>
              <Input id="source_type" {...register('source_type')} className="col-span-3" placeholder="e.g., website, twitter, linkedin" />
              {errors.source_type && <p className="col-span-4 text-sm text-error">{errors.source_type.message}</p>}
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="url" className="text-right">
                URL <span className="text-error">*</span>
              </Label>
              <Input id="url" {...register('url')} className="col-span-3" placeholder="https://example.com" />
              {errors.url && <p className="col-span-4 text-sm text-error">{errors.url.message}</p>}
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="is_active" className="text-right">
                Active
              </Label>
              <Checkbox id="is_active" {...register('is_active')} />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : dataSource ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
