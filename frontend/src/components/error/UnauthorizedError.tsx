import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function UnauthorizedError() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <Card className="max-w-md w-full p-8">
        <div className="text-center space-y-6">
          <div className="flex justify-center">
            <svg
              className="h-24 w-24 text-yellow-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-6xl font-bold text-yellow-500 mb-2">401</h1>
            <h2 className="text-2xl font-semibold mb-2">Unauthorized</h2>
            <p className="text-muted-foreground">
              You do not have permission to access this resource. Please log in to continue.
            </p>
          </div>
          <div className="flex flex-col gap-2">
            <Link href="/login">
              <Button className="w-full">
                Go to Login
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
