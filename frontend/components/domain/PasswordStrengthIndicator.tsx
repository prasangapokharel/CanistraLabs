'use client';

import { usePasswordStrength } from '@/hooks/usePasswordStrength';
import { cn } from '@/lib/utils';

interface PasswordStrengthIndicatorProps {
  password: string;
  className?: string;
}

export function PasswordStrengthIndicator({
  password,
  className,
}: PasswordStrengthIndicatorProps) {
  const { checkStrength } = usePasswordStrength();
  const evaluated = checkStrength(password);

  if (!password) {
    return null;
  }

  const filledBars = Math.max(0, Math.min(4, evaluated.score));

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex gap-1">
        {Array.from({ length: 4 }).map((_, index) => (
          <div
            key={index}
            className={cn(
              'h-1 flex-1 rounded-full transition-colors',
              index < filledBars ? evaluated.color : 'bg-muted'
            )}
          />
        ))}
      </div>
      <div className="flex items-center justify-between text-xs">
        <span className="font-medium">{evaluated.label}</span>
        {evaluated.feedback.length > 0 && (
          <span className="text-muted-foreground">{evaluated.feedback[0]}</span>
        )}
      </div>
    </div>
  );
}
