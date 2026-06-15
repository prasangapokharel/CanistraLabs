'use client';

import Link from 'next/link';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { deployAlertVariant, type DeployAlert } from '@/lib/deploy-status';
import { cn } from '@/lib/utils';

interface DeployStatusAlertProps {
  alert: DeployAlert;
  className?: string;
}

export function DeployStatusAlert({ alert, className }: DeployStatusAlertProps) {
  const isFunding = alert.kind === 'funding';

  return (
    <Alert
      variant={deployAlertVariant(alert.kind)}
      className={cn(
        isFunding && 'border-amber-500/50 bg-amber-500/5',
        alert.kind === 'success' && 'border-emerald-500/50 bg-emerald-500/5',
        className
      )}
    >
      <AlertTitle className="text-sm font-semibold">{alert.title}</AlertTitle>
      <AlertDescription className="text-sm">
        {alert.message}
        {isFunding && (
          <span className="mt-2 block">
            <Link href="/dashboard/wallet/convert" className="underline font-medium">
              Convert ICP → cycles
            </Link>
            {' · '}
            <Link href="/dashboard/wallet" className="underline">
              Wallet
            </Link>
          </span>
        )}
      </AlertDescription>
    </Alert>
  );
}
