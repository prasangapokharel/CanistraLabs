/**
 * Normalize dfx API CLI-shaped responses into frontend types.
 */
import type { CanisterStatus, DeployResult } from '@/types/api';

export interface DfxCommandResult {
  success?: boolean;
  output?: string;
  error?: string;
  [key: string]: unknown;
}

export interface DfxWrappedResponse<T = DfxCommandResult> {
  command?: string;
  result?: T;
  project_id?: number;
  deployment_id?: number;
  canister_id?: string;
  success?: boolean;
  timestamp?: string;
}

export function normalizeCanisterStatus(
  wrapped: DfxWrappedResponse
): CanisterStatus {
  const r = wrapped.result ?? {};
  const parsed =
    r.status && typeof r.status === 'object' && !Array.isArray(r.status)
      ? (r.status as Record<string, unknown>)
      : {};
  const statusText =
    typeof r.status === 'string'
      ? r.status
      : String(parsed.status ?? 'unknown');

  return {
    status: statusText,
    canister_id: String(r.canisterId ?? wrapped.canister_id ?? ''),
    cycles_balance: Number(parsed.cycles ?? r.cycles ?? 0),
    memory_size: Number(parsed.memorySize ?? r.memory_size ?? 0),
  };
}

export function normalizePowerResult(wrapped: DfxWrappedResponse) {
  const r = (wrapped.result ?? wrapped) as Record<string, unknown>;
  return {
    project_id: Number(r.project_id),
    canister_id: String(r.canister_id ?? ''),
    enabled: Boolean(r.enabled),
    status: String(r.status ?? ''),
    canister_status: String(r.canister_status ?? ''),
  };
}

export function normalizeDfxDeploy(
  wrapped: DfxWrappedResponse | DeployResult
): DeployResult {
  const flat = wrapped as Record<string, unknown>;
  const nested = (flat.result ?? {}) as Record<string, unknown>;
  // Merge wrapper + nested result (old API wrapped in `result`, new API is flat)
  const r = { ...flat, ...nested };
  const funding = Boolean(r.funding_required) || r.status === 'pending_funding';
  return {
    deployment_id: Number(r.deployment_id ?? 0),
    project_id: Number(r.project_id ?? 0),
    canister_id: (r.canister_id as string) ?? null,
    url: (r.url as string) ?? null,
    status: funding
      ? 'pending_funding'
      : String(r.status ?? (r.async ? 'queued' : 'deployed')),
    message: (r.message as string) ?? (flat.command as string),
    principal_id: r.principal_id as string | undefined,
    cycles_balance: r.cycles_balance as string | undefined,
    funding_required: funding,
    can_retry: funding || Boolean(r.can_retry),
    async: Boolean(r.async),
    error_code: r.error_code as string | undefined,
    cycles_required: r.cycles_required as number | undefined,
    cycles_shortfall: r.cycles_shortfall as number | undefined,
    recommended_icp: r.recommended_icp as string | undefined,
    action: r.action as string | undefined,
  };
}

export function normalizeConvertResult(wrapped: DfxWrappedResponse) {
  const r = wrapped.result ?? {};
  const newBal = r.newBalance as Record<string, unknown> | undefined;
  return {
    success: Boolean(r.success),
    message: (r.output as string) ?? (r.error as string),
    cycles_balance: newBal?.balanceCycles as number | undefined,
  };
}

export function unwrapDfxUrl(wrapped: DfxWrappedResponse): string | null {
  const r = wrapped.result ?? {};
  return (r.url as string) ?? null;
}
