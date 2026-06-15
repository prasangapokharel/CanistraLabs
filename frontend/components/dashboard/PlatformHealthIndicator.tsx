'use client';

import { useQuery } from '@tanstack/react-query';
import { healthApi } from '@/lib/api';
import { cn } from '@/lib/utils';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

export function PlatformHealthIndicator({ className }: { className?: string }) {
  const { data, isError, isLoading } = useQuery({
    queryKey: ['platform', 'health'],
    queryFn: () => healthApi.get(),
    refetchInterval: 30_000,
    staleTime: 15_000,
    retry: 1,
  });

  const backendOk = !isError && data?.status === 'healthy';
  const dfxOk = Boolean(data?.dfx_local_replica);
  const deployNetwork = data?.deploy_network ?? '—';

  const dotClass = isLoading
    ? 'bg-muted-foreground/40 animate-pulse'
    : !backendOk
      ? 'bg-red-500'
      : dfxOk
        ? 'bg-green-500'
        : deployNetwork === 'ic'
          ? 'bg-amber-500'
          : 'bg-red-500';

  const label = isLoading
    ? 'Checking platform status…'
    : !backendOk
      ? 'Backend unreachable'
      : dfxOk
        ? `dfx local replica running · deploy: ${deployNetwork}`
        : deployNetwork === 'ic'
          ? `Backend healthy · dfx local off (mainnet deploy)`
          : `Backend healthy · dfx local replica offline`;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger
          className={cn(
            'inline-flex items-center gap-2 rounded-full border px-2.5 py-1 text-xs text-muted-foreground',
            className
          )}
        >
          <span className={cn('size-2 shrink-0 rounded-full', dotClass)} aria-hidden />
          <span className="hidden sm:inline">
            {isLoading ? 'Status…' : backendOk ? (dfxOk ? 'dfx live' : 'dfx off') : 'offline'}
          </span>
        </TooltipTrigger>
        <TooltipContent side="bottom" className="max-w-xs text-xs">
          {label}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
