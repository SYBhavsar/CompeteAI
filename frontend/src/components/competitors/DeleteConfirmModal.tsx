'use client'

import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface DeleteConfirmModalProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: () => void
  title: string
  message: string
}

/**
 * Reusable confirmation modal for delete actions
 */
export default function DeleteConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
}: DeleteConfirmModalProps) {
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

          {/* Icon and content */}
          <div className="flex items-start space-x-4">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="h-6 w-6 text-error" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-medium text-text-primary mb-2">{title}</h3>
              <p className="text-sm text-text-secondary">{message}</p>
            </div>
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
              type="button"
              onClick={onConfirm}
              className="px-4 py-2 text-sm font-medium text-white bg-error rounded-md hover:bg-error/90 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-error"
            >
              Confirm
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
