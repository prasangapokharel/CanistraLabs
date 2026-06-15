/** Real ICP canister URLs — never show placeholder URLs before deploy */

/** IC text canister IDs: groups of base32 chars, last segment often 3 chars (e.g. …-cai) */
const CANISTER_ID_RE = /^[a-z0-9]{3,}(-[a-z0-9]{3,})+$/i;

const LOCAL_REPLICA_PORT = 4943;

export function isCanisterId(value: string | null | undefined): boolean {
  if (!value) return false;
  const id = value.trim();
  return CANISTER_ID_RE.test(id) && id.includes('-');
}

const LOCAL_CANISTER_RE = /(?:^|-)(?:[a-z0-9]*7777|77777)(?:-|$)/i;

export function isLocalCanisterId(canisterId: string | null | undefined): boolean {
  if (!canisterId) return false;
  return LOCAL_CANISTER_RE.test(canisterId.trim());
}

export function isLocalCanisterUrl(url: string | null | undefined): boolean {
  if (!url) return false;
  const u = url.toLowerCase();
  return u.includes('127.0.0.1:4943') || u.includes('localhost:4943');
}

/** dfx-recommended local URL (asset canisters serve reliably on this host). */
export function localCanisterUrl(canisterId: string): string {
  return `http://${canisterId.trim()}.localhost:${LOCAL_REPLICA_PORT}/`;
}

export function canisterLiveUrl(canisterId: string, local = false): string {
  const id = canisterId.trim();
  if (local) {
    return localCanisterUrl(id);
  }
  return `https://${id}.icp0.io/`;
}

export function isRealLiveUrl(
  url: string | null | undefined,
  canisterId: string | null | undefined
): boolean {
  if (!url || !canisterId || !isCanisterId(canisterId)) return false;
  const normalized = url.toLowerCase();
  const id = canisterId.toLowerCase();
  return (
    normalized.includes(id) &&
    (normalized.includes('.icp0.io') ||
      normalized.includes('.raw.icp0.io') ||
      isLocalCanisterUrl(url))
  );
}

export function projectLiveUrl(project: {
  canister_id?: string | null;
  url?: string | null;
}): string | null {
  const id = project.canister_id?.trim();
  if (!id || !isCanisterId(id)) return null;

  if (isLocalCanisterUrl(project.url)) {
    return localCanisterUrl(id);
  }
  if (project.url && project.url.toLowerCase().includes(id.toLowerCase())) {
    return project.url;
  }
  if (project.url?.includes('.icp0.io')) {
    return project.url;
  }

  return canisterLiveUrl(id, false);
}

export function projectIsLive(project: {
  canister_id?: string | null;
  status?: string;
  url?: string | null;
}): boolean {
  return Boolean(project.canister_id && isCanisterId(project.canister_id));
}

export function projectDeployLabel(project: {
  canister_id?: string | null;
  url?: string | null;
  status?: string;
  is_paused?: boolean;
}): string {
  if (project.is_paused || project.status === 'paused') return 'Paused';
  if (!projectIsLive(project)) return 'Draft';
  return isLocalCanisterUrl(projectLiveUrl(project)) ? 'Live' : 'Live on ICP';
}

export function deploySucceeded(result: {
  status?: string;
  canister_id?: string | null;
  funding_required?: boolean;
  url?: string | null;
}): boolean {
  if (result.funding_required || result.status === 'pending_funding') return false;
  const okStatus =
    result.status === 'deployed' ||
    result.status === 'updated' ||
    result.status === 'success';
  return okStatus && Boolean(result.canister_id && isCanisterId(result.canister_id));
}
