import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <Card className="max-w-md w-full p-8">
        <div className="text-center space-y-6">
          <div className="flex justify-center">
            <svg
              className="h-24 w-24 text-muted-foreground"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-6xl font-bold text-primary mb-2">404</h1>
            <h2 className="text-2xl font-semibold mb-2">Page Not Found</h2>
            <p className="text-muted-foreground">
              The page you are looking for does not exist or has been moved.
            </p>
          </div>
          <div className="flex flex-col gap-2">
            <Link href="/dashboard">
              <Button className="w-full">
                Go to Dashboard
              </Button>
            </Link>
            <Link href="/">
              <Button variant="outline" className="w-full">
                Go Home
              </Button>
            </Link>
          </div>
        </div>
      </Card>
    </div>
  )
}
