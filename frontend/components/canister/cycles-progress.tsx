import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface CyclesProgressProps {
  cycles: number
  maxCycles: number
  className?: string
}

export function CyclesProgress({ cycles, maxCycles, className }: CyclesProgressProps) {
  const percentage = Math.min((cycles / maxCycles) * 100, 100)
  const isLow = percentage < 20
  
  const formatCycles = (value: number) => {
    if (value >= 1e12) return `${(value / 1e12).toFixed(1)}T`
    if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`
    return value.toString()
  }

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex justify-between text-sm">
        <span className={cn('font-medium', isLow && 'text-destructive')}>
          {formatCycles(cycles)} cycles
        </span>
        <span className="text-muted-foreground">
          of {formatCycles(maxCycles)}
        </span>
      </div>
      <Progress 
        value={percentage} 
        className={cn(
          'h-2',
          isLow && '[&>div]:bg-destructive'
        )}
      />
      {isLow && (
        <p className="text-xs text-destructive">
          Low cycles - consider topping up
        </p>
      )}
    </div>
  )
}