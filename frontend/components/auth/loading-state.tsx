import { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface LoadingStateProps {
  isLoading: boolean
  children: ReactNode
  loadingComponent?: ReactNode
  className?: string
}

export function LoadingState({ 
  isLoading, 
  children, 
  loadingComponent, 
  className 
}: LoadingStateProps) {
  if (isLoading) {
    return (
      <div className={cn("animate-in fade-in-0 duration-300", className)}>
        {loadingComponent || (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={cn("animate-in fade-in-0 slide-in-from-bottom-4 duration-300", className)}>
      {children}
    </div>
  )
}