'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Info, RefreshCw, Zap } from 'lucide-react';
import { Button, buttonVariants } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ActionConfirmDialog } from '@/components/confirm/ActionConfirmDialog';
import { walletApi } from '@/lib/api';
import { handleApiError } from '@/lib/apiClient';
import { formatFundingRequirements } from '@/lib/fundingErrors';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

export function ConvertCycles() {
  const queryClient = useQueryClient();
  const [showConvertConfirm, setShowConvertConfirm] = useState(false);

  const { data: identity, isLoading, error, refetch } = useQuery({
    queryKey: ['wallet', 'identity'],
    queryFn: () => walletApi.getIdentity(),
  });

  const refreshMutation = useMutation({
    mutationFn: () => walletApi.refreshBalance(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
      toast.success('Balances updated');
    },
    onError: (e) => toast.error(handleApiError(e)),
  });

  const convertMutation = useMutation({
    mutationFn: () => walletApi.convertIcpToCycles(),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
      if (res.success) toast.success(res.message ?? 'Converted to cycles');
      else toast.error(res.message ?? 'Conversion failed');
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
  const canConvert = Boolean(identity.auto_convert_available);
  const req = identity.requirements;
  const requirementLines = formatFundingRequirements(req);
  const deployReady = identity.deploy_ready ?? req?.deploy_ready;

  return (
    <div className="mx-auto w-full max-w-lg space-y-6">
      <div className="flex items-center gap-3">
        <Link
          href="/dashboard/wallet"
          className={cn(buttonVariants({ variant: 'ghost', size: 'sm' }), 'shrink-0')}
        >
          <ArrowLeft className="h-4 w-4" />
          Wallet
        </Link>
      </div>

      <div>
        <h1 className="text-xl font-semibold">Convert to cycles</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Convert {token} to cycles to deploy and host canisters on IC mainnet.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base flex items-center gap-2">
            <Info className="h-4 w-4 text-muted-foreground" />
            What you need for mainnet
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          {requirementLines.length > 0 ? (
            <ul className="list-disc space-y-1 pl-4">
              {requirementLines.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          ) : (
            <>
              <p>Mainnet deploy: at least <strong>600 BC</strong> cycles (creation fee + install).</p>
              <p>Recommended: <strong>2 TC</strong> (~$1–2 of ICP) for a comfortable first deploy.</p>
              <p>Convert minimum: <strong>0.002 ICP</strong> (0.001 ICP kept for ledger fees).</p>
            </>
          )}
          {req?.cycles_shortfall && req.cycles_shortfall !== '0' && !deployReady && (
            <p className="pt-1 text-foreground">
              You still need{' '}
              <strong>{req.formatted_cycles_shortfall ?? req.cycles_shortfall}</strong>
              {req.recommended_icp_to_fund ? (
                <> — convert about <strong>{req.recommended_icp_to_fund} ICP</strong></>
              ) : null}
              .
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Balances</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="rounded-lg border bg-muted/30 p-3">
              <p className="text-muted-foreground">{token}</p>
              <p className="mt-1 text-lg font-semibold tabular-nums">
                {identity.formatted_icp ?? identity.icp_balance ?? '0'}
              </p>
            </div>
            <div className="rounded-lg border bg-muted/30 p-3">
              <p className="text-muted-foreground">Cycles</p>
              <p className="mt-1 text-lg font-semibold tabular-nums">
                {identity.formatted_cycles ?? identity.cycles_balance ?? '0'}
              </p>
              {req?.formatted_cycles_required && (
                <p className="mt-1 text-xs text-muted-foreground">
                  Need {req.formatted_cycles_required} to deploy
                </p>
              )}
            </div>
          </div>

          <Button
            variant="outline"
            size="sm"
            onClick={() => refreshMutation.mutate()}
            disabled={refreshMutation.isPending}
          >
            <RefreshCw className="h-4 w-4" />
            Refresh balances
          </Button>
        </CardContent>
      </Card>

      {identity.message && (
        <Alert variant={deployReady ? 'default' : 'destructive'}>
          <AlertDescription className="text-sm">{identity.message}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardContent className="pt-6 space-y-3">
          <Button
            className="w-full"
            size="lg"
            onClick={() => setShowConvertConfirm(true)}
            disabled={convertMutation.isPending || !canConvert}
          >
            <Zap className="h-4 w-4" />
            {convertMutation.isPending ? 'Converting…' : `Convert ${token} to cycles`}
          </Button>
          <p className="text-center text-xs text-muted-foreground">
            Keeps {req?.min_icp_to_convert?.split(' ')[0] ?? '0.001'} ICP for ledger fees.
          </p>
        </CardContent>
      </Card>

      <Button variant="ghost" size="sm" onClick={() => refetch()}>
        Reload
      </Button>

      <ActionConfirmDialog
        open={showConvertConfirm}
        onOpenChange={setShowConvertConfirm}
        title={`Convert ${token} to cycles?`}
        description={`This converts available ${token} in your wallet to cycles for mainnet deploys. A small ${token} balance is kept for ledger fees.`}
        confirmLabel="Convert now"
        loading={convertMutation.isPending}
        onConfirm={() => {
          setShowConvertConfirm(false);
          convertMutation.mutate();
        }}
      />
    </div>
  );
}
