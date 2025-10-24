import { useEffect } from 'react'

/**
 * Custom hook to set page title for accessibility and SEO
 * @param title - The page title to set
 */
export function usePageTitle(title: string) {
  useEffect(() => {
    const previousTitle = document.title
    document.title = `${title} | AI Competitive Intelligence`

    // Cleanup: restore previous title on unmount
    return () => {
      document.title = previousTitle
    }
  }, [title])
}
