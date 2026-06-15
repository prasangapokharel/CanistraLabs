'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import { useCurrentUser, useLogout } from '@/hooks/api/useAuth';
import { walletApi } from '@/lib/api';

export function SettingsView() {
  const { data: user, isLoading } = useCurrentUser();
  const logoutMutation = useLogout();

  const { data: network } = useQuery({
    queryKey: ['wallet', 'network-status'],
    queryFn: () => walletApi.getNetworkStatus(),
    staleTime: 60_000,
  });

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Account and deployment preferences.</p>
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

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">ICP network</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">Deploy network</span>
            <span className="font-medium">
              {String((network as Record<string, unknown>)?.deploy_network ?? 'local')}
            </span>
          </div>
          <div className="flex justify-between gap-4">
            <span className="text-muted-foreground">dfx available</span>
            <span className="font-medium">
              {(network as Record<string, unknown>)?.dfx_available ? 'Yes' : 'No'}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Wallet identity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Your dfx identity is created on signup. Manage balances and conversion in Wallet.
          </p>
          <Button variant="outline" size="sm" render={<Link href="/dashboard/wallet" />}>
            Open wallet
          </Button>
        </CardContent>
      </Card>

      <Separator />

      <Button
        variant="destructive"
        size="sm"
        onClick={() => logoutMutation.mutate()}
        disabled={logoutMutation.isPending}
      >
        {logoutMutation.isPending ? 'Signing out…' : 'Sign out'}
      </Button>
    </div>
  );
}
