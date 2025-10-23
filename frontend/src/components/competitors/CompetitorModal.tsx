'use client'

import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useAppDispatch } from '@/lib/hooks'
import { createCompetitorAsync, updateCompetitorAsync } from '@/features/competitors/competitorsSlice'
import { Competitor } from '@/types'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import toast from 'react-hot-toast'

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
        toast.success('Competitor updated successfully')
      } else {
        // Create new competitor
        await dispatch(
          createCompetitorAsync({
            name: data.name,
            domain: data.domain || undefined,
            industry: data.industry || undefined,
          })
        ).unwrap()
        toast.success('Competitor created successfully')
      }

      onSuccess()
      reset()
    } catch (error) {
      toast.error(competitor ? 'Failed to update competitor' : 'Failed to create competitor')
      console.error('Failed to save competitor:', error)
    }
  }

  if (!isOpen) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>{competitor ? 'Edit Competitor' : 'Add Competitor'}</DialogTitle>
          <DialogDescription>
            {competitor ? 'Update the details of your competitor.' : 'Add a new competitor to track.'}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="name" className="text-right">
                Name <span className="text-error">*</span>
              </Label>
              <Input id="name" {...register('name')} className="col-span-3" placeholder="Enter competitor name" />
              {errors.name && <p className="col-span-4 text-sm text-error">{errors.name.message}</p>}
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="domain" className="text-right">
                Domain
              </Label>
              <Input id="domain" {...register('domain')} className="col-span-3" placeholder="https://example.com" />
              {errors.domain && <p className="col-span-4 text-sm text-error">{errors.domain.message}</p>}
            </div>
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="industry" className="text-right">
                Industry
              </Label>
              <Input id="industry" {...register('industry')} className="col-span-3" placeholder="e.g., Technology, Finance" />
              {errors.industry && <p className="col-span-4 text-sm text-error">{errors.industry.message}</p>}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : competitor ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
