'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { dashboardApi } from '@/lib/api';
import type { Activity } from '@/types/api';

function formatWhen(iso?: string) {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function NotificationsView() {
  const { data: activities = [], isLoading } = useQuery({
    queryKey: ['dashboard', 'activity'],
    queryFn: () => dashboardApi.getActivity(),
    staleTime: 30_000,
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Activity</h1>
        <p className="text-sm text-muted-foreground">
          Recent deploys and project events on your account.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Recent activity</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : activities.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No activity yet. Deploy a project to see events here.
            </p>
          ) : (
            <ul className="space-y-2">
              {activities.map((a: Activity, i: number) => (
                <li
                  key={a.id ?? i}
                  className="flex items-start justify-between gap-3 rounded-md border px-3 py-2"
                >
                  <div className="min-w-0">
                    <p className="text-sm font-medium">{a.title ?? a.type ?? 'Event'}</p>
                    {a.description && (
                      <p className="text-xs text-muted-foreground mt-0.5">{a.description}</p>
                    )}
                    <p className="text-[10px] text-muted-foreground mt-1">
                      {formatWhen(a.timestamp)}
                    </p>
                  </div>
                  {a.status && (
                    <Badge variant="secondary" className="shrink-0">
                      {a.status}
                    </Badge>
                  )}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground">
        View per-project deploy history in the{' '}
        <Link href="/dashboard/projects" className="underline">
          project editor
        </Link>
        .
      </p>
    </div>
  );
}
