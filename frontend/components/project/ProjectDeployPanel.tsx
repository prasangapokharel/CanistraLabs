'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Copy, RefreshCw } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { Button, buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { analyticsApi } from '@/lib/api';
import { useDeployments } from '@/hooks/api/useDeployments';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

function statusVariant(status: string): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (status === 'success' || status === 'deployed') return 'default';
  if (status === 'failed') return 'destructive';
  if (status === 'pending_funding') return 'outline';
  return 'secondary';
}

function formatWhen(iso?: string | null) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

interface ProjectDeployPanelProps {
  projectId: string;
  canisterId?: string | null;
}

export function ProjectDeployPanel({ projectId, canisterId }: ProjectDeployPanelProps) {
  const {
    data: deployments,
    isLoading: historyLoading,
    refetch: refetchHistory,
  } = useDeployments(projectId);

  const {
    data: metricsRes,
    isLoading: metricsLoading,
    refetch: refetchMetrics,
  } = useQuery({
    queryKey: ['project-metrics', projectId],
    queryFn: () => analyticsApi.getMetrics(Number(projectId)),
    enabled: !!canisterId,
    refetchInterval: 60_000,
  });

  const metrics = metricsRes?.metrics as
    | {
        cycles_formatted?: string;
        idle_cycles_burned_per_day_formatted?: string;
        status?: string;
      }
    | undefined;

  const copyCanister = async () => {
    if (!canisterId) return;
    await navigator.clipboard.writeText(canisterId);
    toast.success('Canister ID copied');
  };

  const refreshAll = () => {
    void refetchHistory();
    void refetchMetrics();
  };

  const recent = (deployments ?? []).slice(0, 5);

  return (
    <Card className="shrink-0">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">Hosting</CardTitle>
        <div className="flex items-center gap-1">
          <Link
            href={`/dashboard/projects/${projectId}/metrics`}
            className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), 'h-7 text-xs')}
          >
            All metrics
          </Link>
          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={refreshAll}>
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {canisterId ? (
          <div className="grid gap-2 sm:grid-cols-2">
            <div>
              <p className="text-xs text-muted-foreground">Canister</p>
              <div className="mt-0.5 flex items-center gap-1">
                <code className="truncate text-xs" title={canisterId}>
                  {canisterId}
                </code>
                <Button variant="ghost" size="icon" className="h-6 w-6 shrink-0" onClick={copyCanister}>
                  <Copy className="h-3 w-3" />
                </Button>
              </div>
            </div>
            <div className="flex gap-4 sm:justify-end">
              <div>
                <p className="text-xs text-muted-foreground">Cycles left</p>
                <p className="font-medium tabular-nums">
                  {metricsLoading ? '…' : (metrics?.cycles_formatted ?? '—')}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Idle / day</p>
                <p className="font-medium tabular-nums">
                  {metricsLoading ? '…' : (metrics?.idle_cycles_burned_per_day_formatted ?? '—')}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Status</p>
                <p className="font-medium capitalize">{metricsLoading ? '…' : (metrics?.status ?? '—')}</p>
              </div>
            </div>
          </div>
        ) : (
          <p className="text-xs text-muted-foreground">Not deployed yet — publish to create a canister.</p>
        )}

        <div>
          <p className="mb-1.5 text-xs font-medium text-muted-foreground">Deploy history</p>
          {historyLoading ? (
            <p className="text-xs text-muted-foreground">Loading…</p>
          ) : recent.length === 0 ? (
            <p className="text-xs text-muted-foreground">No deploys yet.</p>
          ) : (
            <ul className="space-y-1">
              {recent.map((d) => (
                <li
                  key={d.id}
                  className="flex items-center justify-between gap-2 rounded-md border bg-muted/20 px-2 py-1.5"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-xs">{d.message ?? d.status}</p>
                    <p className="text-[10px] text-muted-foreground">
                      {formatWhen(d.completed_at ?? d.created_at)}
                    </p>
                  </div>
                  <Badge variant={statusVariant(d.status)} className="shrink-0 text-[10px]">
                    {d.status}
                  </Badge>
                </li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
