'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useAppSelector } from '@/lib/hooks'
import { selectNotifications, selectUnreadCount } from '@/features/notifications/notificationsSlice'
import { BellIcon } from '@heroicons/react/24/outline'
import { formatDistanceToNow } from 'date-fns'
import clsx from 'clsx'

export default function NotificationDropdown() {
  const [isOpen, setIsOpen] = useState(false)
  const notifications = useAppSelector(selectNotifications)
  const unreadCount = useAppSelector(selectUnreadCount)

  // Show only last 5 notifications in dropdown
  const recentNotifications = notifications.slice(0, 5)

  return (
    <div className="relative">
      {/* Bell Icon Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="relative rounded-full p-2 text-text-secondary hover:bg-background hover:text-text-primary transition-colors"
        aria-label="View notifications"
      >
        <BellIcon className="h-6 w-6" />

        {/* Unread Badge */}
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold leading-none text-white bg-error rounded-full">
            {unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <>
          {/* Backdrop to close dropdown */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown Menu */}
          <div className="absolute right-0 z-20 mt-2 w-80 origin-top-right rounded-md bg-surface border border-border shadow-lg">
            <div className="py-2">
              {/* Header */}
              <div className="px-4 py-2 border-b border-border">
                <h3 className="text-sm font-semibold text-text-primary">Notifications</h3>
              </div>

              {/* Notifications List */}
              {recentNotifications.length === 0 ? (
                <div className="px-4 py-8 text-center">
                  <p className="text-sm text-text-secondary">No notifications</p>
                </div>
              ) : (
                <div className="max-h-96 overflow-y-auto">
                  {recentNotifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={clsx(
                        'px-4 py-3 hover:bg-background transition-colors border-b border-border last:border-b-0',
                        !notification.is_read && 'bg-primary/5'
                      )}
                    >
                      <p className="text-sm text-text-primary">{notification.message}</p>
                      <p className="text-xs text-text-secondary mt-1">
                        {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
                      </p>
                    </div>
                  ))}
                </div>
              )}

              {/* View All Link */}
              <div className="px-4 py-2 border-t border-border">
                <Link
                  href="/dashboard/notifications"
                  className="text-sm text-primary hover:text-primary/90 font-medium"
                  onClick={() => setIsOpen(false)}
                >
                  View all notifications
                </Link>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
