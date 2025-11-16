import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

export default function ServerError() {
  const handleReload = () => {
    window.location.reload()
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <Card className="max-w-md w-full p-8">
        <div className="text-center space-y-6">
          <div className="flex justify-center">
            <svg
              className="h-24 w-24 text-destructive"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          <div>
            <h1 className="text-6xl font-bold text-destructive mb-2">500</h1>
            <h2 className="text-2xl font-semibold mb-2">Server Error</h2>
            <p className="text-muted-foreground">
              Something went wrong on our end. Please try again later.
            </p>
          </div>
          <div className="flex flex-col gap-2">
            <Button onClick={handleReload} className="w-full">
              Reload Page
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}
