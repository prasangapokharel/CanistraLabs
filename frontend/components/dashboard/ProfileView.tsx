'use client';

import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useCurrentUser } from '@/hooks/api/useAuth';

export function ProfileView() {
  const { data: user, isLoading } = useCurrentUser();

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Profile</h1>
          <p className="text-sm text-muted-foreground">Your Canistra account.</p>
        </div>
        <Link href="/dashboard/settings" className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}>
          Settings
        </Link>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Email</span>
            <span className="font-medium">{user?.email ?? '—'}</span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Username</span>
            <span className="font-medium">{user?.username ?? '—'}</span>
          </div>
          {user?.full_name && (
            <div className="flex justify-between gap-4">
              <span className="text-muted-foreground">Name</span>
              <span className="font-medium">{user.full_name}</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
