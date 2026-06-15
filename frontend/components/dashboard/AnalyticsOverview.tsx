'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { BarChart3 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { analyticsApi, dashboardApi } from '@/lib/api';
import { useProjects } from '@/hooks/api/useProjects';
import { projectIsLive } from '@/lib/icp-url';

function ProjectMetricCard({ projectId, name }: { projectId: number; name: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['project-metrics', projectId],
    queryFn: () => analyticsApi.getMetrics(projectId),
    staleTime: 60_000,
  });

  const m = (data?.metrics ?? {}) as Record<string, unknown>;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium">{name}</CardTitle>
        <Link
          href={`/dashboard/projects/${projectId}/metrics`}
          className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), 'h-7')}
        >
          <BarChart3 className="h-3.5 w-3.5" />
          Details
        </Link>
      </CardHeader>
      <CardContent className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <p className="text-xs text-muted-foreground">Cycles</p>
          <p className="font-medium tabular-nums">
            {isLoading ? '…' : String(m.cycles_formatted ?? '—')}
          </p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Status</p>
          <Badge variant="secondary" className="mt-0.5">
            {isLoading ? '…' : String(m.status ?? 'unknown')}
          </Badge>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Memory</p>
          <p className="font-medium">{isLoading ? '…' : String(m.memory_formatted ?? '—')}</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Queries</p>
          <p className="font-medium tabular-nums">
            {isLoading ? '…' : Number(m.number_of_queries ?? 0).toLocaleString()}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

export function AnalyticsOverview() {
  const { data: projects = [], isLoading } = useProjects();
  const live = projects.filter((p) => projectIsLive(p));

  const { data: stats } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardApi.getStats,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Analytics</h1>
        <p className="text-sm text-muted-foreground">
          On-chain canister metrics from ICP — no synthetic traffic data.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Live projects</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{isLoading ? '—' : live.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Total cycles</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">
              {stats ? `${((stats.totalCycles ?? 0) / 1e12).toFixed(1)}T` : '—'}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Deployments (month)</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{stats?.deploymentsThisMonth ?? '—'}</p>
          </CardContent>
        </Card>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : live.length === 0 ? (
        <Card>
          <CardContent className="py-10 text-center text-sm text-muted-foreground">
            Deploy a project to see canister analytics.
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {live.map((p) => (
            <ProjectMetricCard key={p.id} projectId={Number(p.id)} name={p.name} />
          ))}
        </div>
      )}
    </div>
  );
}
