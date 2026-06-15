import type { FundingRequirements } from '@/types/api';
import { ApiError } from '@/lib/apiClient';

export function formatFundingRequirements(req?: FundingRequirements): string[] {
  if (!req) return [];
  const lines: string[] = [];
  if (req.deploy_network === 'ic') {
    lines.push(
      `Mainnet deploy needs at least ${req.formatted_cycles_required ?? req.cycles_required} cycles.`
    );
    lines.push(
      `Recommended: ${req.formatted_cycles_recommended ?? req.cycles_recommended} (~$1–2 of ICP).`
    );
    lines.push(`Convert minimum: ${req.min_icp_to_convert ?? '0.002 ICP'} (keeps a small fee reserve).`);
  } else {
    lines.push(`Local deploy needs at least ${req.formatted_cycles_required ?? '20M cycles'}.`);
  }
  return lines;
}

/** Turn API deploy/wallet errors into a readable multi-line message. */
export function formatDeployError(error: unknown): string {
  if (error instanceof ApiError) {
    const data = error.data;
    if (data && typeof data === 'object' && data !== null) {
      const payload = data as { detail?: unknown; message?: string };
      const detail = payload.detail ?? payload.message;
      if (detail && typeof detail === 'object' && detail !== null) {
        const d = detail as {
          message?: string;
          action?: string;
          recommended_icp?: string;
          formatted_cycles_shortfall?: string;
        };
        if (d.message) {
          const parts = [d.message];
          if (d.formatted_cycles_shortfall && d.formatted_cycles_shortfall !== '0 cycles') {
            parts.push(`Shortfall: ${d.formatted_cycles_shortfall}.`);
          }
          if (d.recommended_icp) {
            parts.push(`Convert about ${d.recommended_icp} ICP to cycles.`);
          }
          if (d.action) parts.push(d.action);
          return parts.filter(Boolean).join(' ');
        }
      }
      if (typeof detail === 'string' && detail.length > 0) {
        return detail;
      }
    }
    if (error.message && !error.message.startsWith('API Error:')) {
      return error.message;
    }
  }
  if (error instanceof Error) return error.message;
  return 'Request failed';
}
