'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ExternalLink, BarChart3 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { dashboardApi } from '@/lib/api';

export function CanistersView() {
  const { data: canisters = [], isLoading } = useQuery({
    queryKey: ['dashboard', 'canisters'],
    queryFn: () => dashboardApi.getCanisters(),
    staleTime: 30_000,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Canisters</h1>
        <p className="text-sm text-muted-foreground">
          Live ICP canisters backing your projects.
        </p>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : canisters.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-sm text-muted-foreground mb-4">No deployed canisters yet</p>
            <Link href="/dashboard/projects/new" className={cn(buttonVariants())}>
              Create project
            </Link>
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-2">
          {canisters.map((c) => (
            <li key={c.id}>
              <Card>
                <CardContent className="py-4 flex flex-wrap items-center justify-between gap-3">
                  <div className="min-w-0">
                    <Link
                      href={`/dashboard/projects/${c.id}`}
                      className="font-medium hover:underline"
                    >
                      {c.name}
                    </Link>
                    <p className="text-xs text-muted-foreground font-mono mt-0.5 truncate">
                      {c.canister_id}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge variant={c.is_healthy ? 'default' : 'secondary'}>
                      {c.is_healthy ? 'Healthy' : 'Check'}
                    </Badge>
                    <span className="text-xs text-muted-foreground tabular-nums">
                      {(c.cycles_balance / 1e12).toFixed(2)}T cycles
                    </span>
                    <Link
                      href={`/dashboard/projects/${c.id}/metrics`}
                      className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                    >
                      <BarChart3 className="h-4 w-4" />
                      Metrics
                    </Link>
                    {c.url && (
                      <a
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                      >
                        <ExternalLink className="h-4 w-4" />
                        Open
                      </a>
                    )}
                  </div>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
