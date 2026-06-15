'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { ArrowRight, RefreshCw } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button, buttonVariants } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';
import { walletApi } from '@/lib/api';
import { handleApiError } from '@/lib/apiClient';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

export function BillingView() {
  const queryClient = useQueryClient();

  const { data: identity, isLoading, error } = useQuery({
    queryKey: ['wallet', 'identity'],
    queryFn: () => walletApi.getIdentity(),
  });

  const { data: funding } = useQuery({
    queryKey: ['wallet', 'funding-instructions'],
    queryFn: () => walletApi.getFundingInstructions(),
    staleTime: 120_000,
  });

  const refreshMutation = useMutation({
    mutationFn: () => walletApi.refreshBalance(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
      toast.success('Balance refreshed');
    },
    onError: (e) => toast.error(handleApiError(e)),
  });

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (error || !identity) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{handleApiError(error)}</AlertDescription>
      </Alert>
    );
  }

  const token = identity.token_symbol ?? 'ICP';

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Billing & cycles</h1>
        <p className="text-sm text-muted-foreground">
          ICP wallet balances and cycle usage for hosting on the Internet Computer.
        </p>
      </div>

      {identity.funding_required && (
        <Alert>
          <AlertDescription>
            {identity.message ?? 'Fund your wallet before deploying to mainnet.'}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">{token} balance</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold tabular-nums">
              {identity.formatted_icp ?? identity.icp_balance ?? '0'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">Ledger balance on your identity</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Cycles wallet</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-semibold tabular-nums">
              {identity.formatted_cycles ?? identity.cycles_balance ?? '0'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">Used to create and top up canisters</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Actions</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
          >
            <RefreshCw className="h-4 w-4" />
            Refresh balance
          </Button>
          <Link
            href="/dashboard/wallet"
            className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
          >
            Wallet & deposit
          </Link>
          <Link
            href="/dashboard/wallet/convert"
            className={cn(buttonVariants({ size: 'sm' }))}
          >
            Convert {token} → cycles
            <ArrowRight className="h-4 w-4" />
          </Link>
        </CardContent>
      </Card>

      {funding?.instructions && funding.instructions.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Funding guide</CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground space-y-3">
            {funding.instructions.map((step) => (
              <div key={step.step}>
                <p className="font-medium text-foreground">{step.title}</p>
                <p className="text-xs mt-0.5">{step.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
