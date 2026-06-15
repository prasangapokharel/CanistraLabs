/**
 * Deploy UI status helpers — consistent labels and alert variants.
 */
import type { DeployResult } from '@/types/api';

export type DeployAlertKind = 'funding' | 'failed' | 'deploying' | 'success' | 'info';

export interface DeployAlert {
  kind: DeployAlertKind;
  title: string;
  message: string;
}

export function deployAlertVariant(
  kind: DeployAlertKind
): 'default' | 'destructive' {
  if (kind === 'failed') return 'destructive';
  return 'default';
}

export function fundingAlertFromResult(result: DeployResult): DeployAlert {
  const message =
    result.message ??
    (result.recommended_icp
      ? `Convert about ${result.recommended_icp} ICP to cycles, then deploy again.`
      : 'Fund your wallet and convert ICP to cycles before deploying on mainnet.');

  return {
    kind: 'funding',
    title: 'Insufficient cycles — deploy not started',
    message,
  };
}

export function failedAlert(message: string): DeployAlert {
  return {
    kind: 'failed',
    title: 'Deploy unsuccessful',
    message: message || 'The deployment failed. Check wallet balance and try again.',
  };
}

export function deployingAlert(message?: string): DeployAlert {
  return {
    kind: 'deploying',
    title: 'Deploy in progress',
    message: message ?? 'Publishing your project to ICP…',
  };
}

export function successAlert(live: boolean): DeployAlert {
  return {
    kind: 'success',
    title: live ? 'Live on ICP' : 'Published',
    message: live
      ? 'Your site is deployed on the Internet Computer.'
      : 'Your project is published on the local dfx replica.',
  };
}

export function statusBadgeLabel(status: string): string {
  switch (status) {
    case 'pending_funding':
      return 'Needs funding';
    case 'failed':
      return 'Failed';
    case 'success':
    case 'deployed':
      return 'Deployed';
    case 'queued':
    case 'running':
    case 'pending':
      return 'In progress';
    case 'updated':
      return 'Updated';
    default:
      return status.replace(/_/g, ' ');
  }
}
