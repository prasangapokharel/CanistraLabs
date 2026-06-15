'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { dashboardApi } from '@/lib/api';

const ATTENTION_STATUSES = new Set(['pending_funding', 'failed', 'error']);

function attentionCount(activities: { status?: string }[]): number {
  return activities.filter((a) => a.status && ATTENTION_STATUSES.has(a.status)).length;
}

export function HeaderNotifications() {
  const { data: activities = [] } = useQuery({
    queryKey: ['dashboard', 'activity'],
    queryFn: () => dashboardApi.getActivity(),
    staleTime: 30_000,
    refetchInterval: 60_000,
  });

  const count = attentionCount(activities);
  const total = activities.length;

  return (
    <Button
      variant="ghost"
      size="icon"
      className="relative size-9"
      render={<Link href="/dashboard/notifications" />}
      title={count > 0 ? `${count} items need attention` : 'Activity'}
    >
      <Bell className="size-4" />
      {count > 0 ? (
        <Badge
          variant="destructive"
          className="absolute -right-0.5 -top-0.5 flex size-5 items-center justify-center p-0 text-[10px]"
        >
          {count > 99 ? '99+' : count}
        </Badge>
      ) : total > 0 ? (
        <span className="absolute right-1 top-1 size-2 rounded-full bg-primary" aria-hidden />
      ) : null}
      <span className="sr-only">
        {count > 0 ? `${count} notifications need attention` : 'View activity'}
      </span>
    </Button>
  );
}
