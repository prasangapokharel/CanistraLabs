'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import QRCode from 'qrcode';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowRight, Copy, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button, buttonVariants } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { walletApi } from '@/lib/api';
import { handleApiError } from '@/lib/apiClient';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

export function MinimalWallet() {
  const queryClient = useQueryClient();
  const [qrUrl, setQrUrl] = useState('');
  const [copied, setCopied] = useState(false);

  const { data: identity, isLoading, error } = useQuery({
    queryKey: ['wallet', 'identity'],
    queryFn: () => walletApi.getIdentity(),
    refetchInterval: 60_000,
  });

  const refreshMutation = useMutation({
    mutationFn: () => walletApi.refreshBalance(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
      toast.success('Balance updated');
    },
    onError: (e) => toast.error(handleApiError(e)),
  });

  useEffect(() => {
    if (identity?.account_id) {
      void QRCode.toDataURL(identity.account_id, { width: 200, margin: 1 }).then(setQrUrl);
    }
  }, [identity?.account_id]);

  const copyAddress = async () => {
    if (!identity?.account_id) return;
    await navigator.clipboard.writeText(identity.account_id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading wallet…</p>;
  }

  if (error || !identity) {
    return (
      <Alert variant="destructive">
        <AlertDescription>Could not load wallet. {handleApiError(error)}</AlertDescription>
      </Alert>
    );
  }

  const tokenLabel = identity.token_symbol ?? 'ICP';

  return (
    <div className="mx-auto w-full max-w-lg space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Wallet</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Your ICP identity — deposit address and balances.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Balances</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">{tokenLabel}</span>
            <span className="font-medium tabular-nums">
              {identity.formatted_icp ?? identity.icp_balance ?? '0'}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Cycles</span>
            <span className="font-medium tabular-nums">
              {identity.formatted_cycles ?? identity.cycles_balance ?? '0'}
            </span>
          </div>
          <div className="flex flex-wrap gap-2 pt-1">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refreshMutation.mutate()}
              disabled={refreshMutation.isPending}
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Link
              href="/dashboard/wallet/convert"
              className={cn(buttonVariants({ variant: 'default', size: 'sm' }))}
            >
              Convert to cycles
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Deposit address</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <code className="flex-1 break-all rounded bg-muted p-3 text-xs">
              {identity.account_id}
            </code>
            <Button variant="outline" size="icon" onClick={copyAddress}>
              <Copy className="h-4 w-4" />
            </Button>
          </div>
          {copied && <p className="text-xs text-muted-foreground">Copied</p>}
          {qrUrl && (
            <div className="flex justify-center">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={qrUrl} alt="Deposit QR" className="h-[180px] w-[180px] rounded border" />
            </div>
          )}
          <p className="text-xs text-muted-foreground">
            Send ICP to this Account ID from an exchange or wallet — not your Principal ID.
            After deposit, click <strong>Refresh</strong> to update your balance.
          </p>
        </CardContent>
      </Card>

      {identity.funding_required && (
        <Alert>
          <AlertDescription className="text-sm">
            {identity.message ?? 'Fund your wallet before deploying to mainnet.'}
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
