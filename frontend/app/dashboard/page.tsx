'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button, buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { dashboardApi, walletApi } from '@/lib/api';
import { useProjects } from '@/hooks/api/useProjects';
import { projectIsLive, projectLiveUrl } from '@/lib/icp-url';

export default function DashboardPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: dashboardApi.getStats,
  });

  const { data: projects = [], isLoading: projectsLoading } = useProjects();

  const { data: wallet } = useQuery({
    queryKey: ['wallet', 'identity'],
    queryFn: () => walletApi.getIdentity(),
    staleTime: 30_000,
  });

  const deployed = projects.filter((p) => projectIsLive(p)).length;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-lg font-semibold">Overview</h2>
        <p className="text-sm text-muted-foreground">Your projects on the Internet Computer</p>
      </div>

      {wallet?.funding_required && (
        <Alert>
          <AlertDescription>
            Wallet needs funding before deploy.{' '}
            <Link href="/dashboard/wallet" className="underline font-medium">
              View wallet & balance
            </Link>
            {' — '}
            {wallet.token_symbol ?? 'ICP'}:{' '}
            {wallet.formatted_icp ?? '0'} · Cycles: {wallet.formatted_cycles ?? '0'}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Projects</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{projectsLoading ? '—' : projects.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Live on ICP</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">{projectsLoading ? '—' : deployed}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Cycles</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold">
              {statsLoading ? '—' : `${((stats?.totalCycles ?? 0) / 1e12).toFixed(1)}T`}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-base">Recent projects</CardTitle>
          <Button variant="outline" size="sm" render={<Link href="/dashboard/projects" />}>
            View all
          </Button>
        </CardHeader>
        <CardContent>
          {projectsLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : projects.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No projects yet. Use <strong>New project</strong> in the sidebar.
            </p>
          ) : (
            <ul className="flex flex-col gap-2">
              {projects.slice(0, 5).map((project) => {
                const liveUrl = projectLiveUrl(project);
                return (
                  <li
                    key={project.id}
                    className="flex items-center justify-between gap-3 rounded-md border px-3 py-2"
                  >
                    <Link
                      href={`/dashboard/projects/${project.id}`}
                      className="font-medium hover:underline truncate"
                    >
                      {project.name}
                    </Link>
                    <div className="flex items-center gap-2 shrink-0">
                      <Badge variant={projectIsLive(project) ? 'default' : 'secondary'}>
                        {projectIsLive(project) ? 'Live' : 'Draft'}
                      </Badge>
                      {liveUrl && (
                        <Link
                          href={liveUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                        >
                          Open
                        </Link>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
