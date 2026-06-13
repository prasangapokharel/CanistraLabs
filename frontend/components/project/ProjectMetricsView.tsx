'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, ExternalLink, RefreshCw } from 'lucide-react';
import { analyticsApi } from '@/lib/api';
import { useProject } from '@/hooks/api/useProjects';
import { handleApiError } from '@/lib/apiClient';
import { projectLiveUrl } from '@/lib/icp-url';
import { Button, buttonVariants } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import type { ProjectMetrics } from '@/types/api';

function MetricCell({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-lg border bg-muted/20 p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 text-lg font-semibold tabular-nums">{value}</p>
      {hint && <p className="mt-1 text-[10px] text-muted-foreground">{hint}</p>}
    </div>
  );
}

export function ProjectMetricsView() {
  const params = useParams();
  const projectId = params?.id as string;
  const { data: project, isLoading: projectLoading, error: projectError } = useProject(projectId);

  const {
    data,
    isLoading: metricsLoading,
    error: metricsError,
    refetch,
    isFetching,
  } = useQuery({
    queryKey: ['project-metrics', projectId],
    queryFn: () => analyticsApi.getMetrics(Number(projectId)),
    enabled: !!projectId,
    refetchInterval: 30_000,
  });

  if (projectLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (projectError || !project) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{projectError ? handleApiError(projectError) : 'Project not found'}</AlertDescription>
      </Alert>
    );
  }

  const liveUrl = projectLiveUrl(project);
  const m = (data?.metrics ?? {}) as ProjectMetrics;
  const loading = metricsLoading && !data;
  const isRunning = String(m.status ?? '').toLowerCase() === 'running';

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <Link href="/dashboard/projects" className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }))}>
          <ArrowLeft className="h-4 w-4" />
          Projects
        </Link>
        <Link
          href={`/dashboard/projects/${project.id}`}
          className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
        >
          Editor
        </Link>
        {liveUrl && (
          <a
            href={liveUrl}
            target="_blank"
            rel="noopener noreferrer"
            className={cn(buttonVariants({ variant: 'default', size: 'sm' }))}
          >
            <ExternalLink className="h-4 w-4" />
            Visit site
          </a>
        )}
        <Button variant="outline" size="sm" className="ml-auto" onClick={() => refetch()} disabled={isFetching}>
          <RefreshCw className={cn('h-4 w-4', isFetching && 'animate-spin')} />
          Refresh
        </Button>
      </div>

      <div>
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-xl font-semibold">{project.name}</h1>
          <Badge variant={isRunning ? 'default' : 'secondary'}>{m.status ?? (project.canister_id ? 'Unknown' : 'Draft')}</Badge>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          ICP canister metrics from <code className="text-xs">dfx canister status</code> — real on-chain data only.
        </p>
      </div>

      {metricsError && (
        <Alert variant="destructive">
          <AlertDescription>{handleApiError(metricsError)}</AlertDescription>
        </Alert>
      )}

      {!project.canister_id ? (
        <Alert>
          <AlertDescription>
            Not deployed yet.{' '}
            <Link href={`/dashboard/projects/${project.id}`} className="underline">
              Publish
            </Link>{' '}
            to see ICP metrics.
          </AlertDescription>
        </Alert>
      ) : (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCell
              label="Cycles balance (current)"
              value={loading ? '…' : (m.cycles_formatted ?? '—')}
              hint="Remaining on canister"
            />
            <MetricCell
              label="Idle burn / day"
              value={loading ? '…' : (m.idle_cycles_burned_per_day_formatted ?? '—')}
              hint="ICP estimated idle cost"
            />
            <MetricCell
              label="Memory (on-chain)"
              value={loading ? '…' : (m.memory_formatted ?? '—')}
              hint="Canister memory size"
            />
            <MetricCell
              label="Query calls (total)"
              value={loading ? '…' : (m.number_of_queries?.toLocaleString() ?? '0')}
              hint="ICP-reported count"
            />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <MetricCell
              label="Incoming data (queries)"
              value={loading ? '…' : (m.query_request_payload_formatted ?? '—')}
              hint="Total query request payload"
            />
            <MetricCell
              label="Outgoing data (queries)"
              value={loading ? '…' : (m.query_response_payload_formatted ?? '—')}
              hint="Total query response payload"
            />
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">All ICP fields</CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <p className="text-sm text-muted-foreground">Loading…</p>
              ) : (
                <dl className="space-y-2 text-sm">
                  {(m.fields ?? []).map((row) => (
                    <div key={row.label} className="flex justify-between gap-4 border-b border-border/50 pb-2 last:border-0">
                      <dt className="text-muted-foreground shrink-0">{row.label}</dt>
                      <dd className="font-mono text-xs text-right break-all">{row.value}</dd>
                    </div>
                  ))}
                </dl>
              )}
            </CardContent>
          </Card>

          <p className="text-xs text-muted-foreground">
            Canister: <span className="font-mono">{project.canister_id}</span>
            {m.checked_at && (
              <span className="ml-2">· {m.source ?? 'dfx'} · {new Date(m.checked_at).toLocaleTimeString()}</span>
            )}
          </p>
        </>
      )}
    </div>
  );
}
