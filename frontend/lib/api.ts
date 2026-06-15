/**
 * API modules — single source of truth aligned with backend /api/v1 routes.
 * All feature pages must import from here, not call fetch directly.
 */
import { apiClient } from './apiClient';
import { projectLiveUrl } from './icp-url';
import type {
  Activity,
  Canister,
  CanisterLog,
  CanisterMetric,
  CanisterStatus,
  DeployResult,
  DeploymentRecord,
  Domain,
  DfxCommandCatalog,
  DfxConvertBody,
  DfxCyclesTopUpBody,
  DfxDepositCyclesBody,
  FundingInstructions,
  Project,
  WalletIdentity,
} from '@/types/api';
import {
  normalizeCanisterStatus,
  normalizeConvertResult,
  normalizeDfxDeploy,
  normalizePowerResult,
  unwrapDfxUrl,
  type DfxWrappedResponse,
} from '@/lib/dfx/normalize';

// ---------------------------------------------------------------------------
// Response normalizers
// ---------------------------------------------------------------------------

function normalizeProject(p: Project): Project {
  const paused = p.status === 'paused';
  const hasCanister = Boolean(p.canister_id);
  const display = paused ? 'paused' : hasCanister ? 'deployed' : p.status === 'failed' ? 'failed' : 'draft';
  const url = paused ? null : projectLiveUrl(p);
  return { ...p, display_status: display, status: display, url: url ?? null, is_paused: paused };
}

function normalizeProjects(projects: Project[]): Project[] {
  return projects.map(normalizeProject);
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export interface DashboardStats {
  totalCanisters: number;
  activeProjects: number;
  totalCycles: number;
  deploymentsThisMonth?: number;
  uptime?: number;
  averageResponseTime?: number;
}

export interface DashboardCanister {
  id: number;
  name: string;
  canister_id: string;
  status: string;
  url: string;
  cycles_balance: number;
  requests_today: number;
  storage_used_bytes: number;
  is_healthy: boolean;
  created_at: string;
  updated_at: string;
}

export const dashboardApi = {
  getStats: () =>
    apiClient.get<DashboardStats>('/api/v1/dashboard/stats'),

  getCanisters: async (): Promise<DashboardCanister[]> => {
    const res = await apiClient.get<{ success: boolean; data: DashboardCanister[] }>(
      '/api/v1/dashboard/canisters'
    );
    return res.data ?? [];
  },

  getProjects: async () => normalizeProjects(await projectsApi.getAll()),

  getActivity: async (): Promise<Activity[]> => {
    const res = await apiClient.get<{ success: boolean; data: Activity[] }>(
      '/api/v1/dashboard/activities'
    );
    return res.data ?? [];
  },

  getOverview: () =>
    apiClient.get<Record<string, unknown>>('/api/v1/dashboard/overview'),
};

// ---------------------------------------------------------------------------
// Projects
// ---------------------------------------------------------------------------

export const projectsApi = {
  getAll: async () => normalizeProjects(await apiClient.get<Project[]>('/api/v1/projects')),
  getById: async (id: number) => normalizeProject(await apiClient.get<Project>(`/api/v1/projects/${id}`)),
  create: (data: unknown) =>
    apiClient.post<Project>('/api/v1/projects', data).then(normalizeProject),
  update: (id: number, data: unknown) =>
    apiClient.patch<Project>(`/api/v1/projects/${id}`, data).then(normalizeProject),
  delete: (id: number) => apiClient.delete<void>(`/api/v1/projects/${id}`),
};

// ---------------------------------------------------------------------------
// DFX commands — /api/v1/dfx (maps to official dfx CLI)
// ---------------------------------------------------------------------------

export const dfxApi = {
  getCommands: () => apiClient.get<DfxCommandCatalog>('/api/v1/dfx/commands'),

  getVersion: () =>
    apiClient.get<{ command: string; success: boolean; version: string }>('/api/v1/dfx/version'),

  ping: (network = 'ic') =>
    apiClient.get<DfxWrappedResponse>(`/api/v1/dfx/ping`, { params: { network } }),

  getIdentityPrincipal: () =>
    apiClient.get<DfxWrappedResponse>('/api/v1/dfx/identity/principal'),

  getLedgerBalance: () =>
    apiClient.get<DfxWrappedResponse>('/api/v1/dfx/ledger/balance'),

  getCyclesBalance: () =>
    apiClient.get<DfxWrappedResponse>('/api/v1/dfx/cycles/balance'),

  convertCycles: (body?: DfxConvertBody) =>
    apiClient
      .post<DfxWrappedResponse>('/api/v1/dfx/cycles/convert', body ?? {})
      .then(normalizeConvertResult),

  topUpCycles: (body: DfxCyclesTopUpBody) =>
    apiClient.post<DfxWrappedResponse>('/api/v1/dfx/cycles/top-up', body),

  getCanisterStatus: (canisterId: string) =>
    apiClient
      .get<DfxWrappedResponse>(`/api/v1/dfx/canister/${canisterId}/status`)
      .then(normalizeCanisterStatus),

  getCanisterInfo: (canisterId: string) =>
    apiClient.get<DfxWrappedResponse>(`/api/v1/dfx/canister/${canisterId}/info`),

  getCanisterUrl: (canisterId: string) =>
    apiClient
      .get<DfxWrappedResponse>(`/api/v1/dfx/canister/${canisterId}/url`)
      .then(unwrapDfxUrl),

  startCanister: (canisterId: string) =>
    apiClient.post<DfxWrappedResponse>(`/api/v1/dfx/canister/${canisterId}/start`, {}),

  stopCanister: (canisterId: string) =>
    apiClient.post<DfxWrappedResponse>(`/api/v1/dfx/canister/${canisterId}/stop`, {}),

  deleteCanister: (canisterId: string) =>
    apiClient.delete<DfxWrappedResponse>(`/api/v1/dfx/canister/${canisterId}`),

  depositCycles: (canisterId: string, body: DfxDepositCyclesBody) =>
    apiClient.post<DfxWrappedResponse>(
      `/api/v1/dfx/canister/${canisterId}/deposit-cycles`,
      body
    ),

  /** Official asset deploy path (async Celery or sync) */
  deployProject: (projectId: number, data?: { code_content?: string }) =>
    apiClient
      .post<DeployResult>(`/api/v1/dfx/projects/${projectId}/deploy`, data ?? {})
      .then(normalizeDfxDeploy),

  updateProject: (projectId: number, data?: { code_content?: string }) =>
    apiClient
      .post<DeployResult>(`/api/v1/dfx/projects/${projectId}/update-canister`, data ?? {})
      .then(normalizeDfxDeploy),

  getDeploymentStatus: (projectId: number, deploymentId: number) =>
    apiClient.get<DeploymentRecord>(
      `/api/v1/dfx/projects/${projectId}/deployments/${deploymentId}`
    ),

  listDeployments: (projectId: number) =>
    apiClient.get<DeploymentRecord[]>(`/api/v1/dfx/projects/${projectId}/deployments`),

  setProjectPower: (projectId: number, enabled: boolean) =>
    apiClient
      .post<DfxWrappedResponse>(`/api/v1/dfx/projects/${projectId}/power`, { enabled })
      .then(normalizePowerResult),

  deleteProjectCanister: (projectId: number) =>
    apiClient.delete<{ command: string; project_id: number; canister_id?: string; success: boolean }>(
      `/api/v1/dfx/projects/${projectId}/canister`
    ),
};

// ---------------------------------------------------------------------------
// Deployments & hosting
// ---------------------------------------------------------------------------

export const deployApi = {
  /** Deploy project HTML/assets to ICP (official dfx path via /api/v1/dfx) */
  deploy: (projectId: string | number, data?: { code_content?: string; force?: boolean }) =>
    apiClient
      .post<DeployResult>(`/api/v1/dfx/projects/${projectId}/deploy`, data ?? {})
      .then(normalizeDfxDeploy),

  resume: (projectId: string | number) =>
    deployApi.deploy(projectId, { force: true }),

  updateCanister: (projectId: number, data?: { code_content?: string }) =>
    apiClient
      .post<DeployResult>(`/api/v1/dfx/projects/${projectId}/update-canister`, data ?? {})
      .then((res) => normalizeDfxDeploy(res)),

  deleteCanister: (projectId: number) => dfxApi.deleteProjectCanister(projectId),

  getDeploymentStatus: (projectId: number, deploymentId: number) =>
    apiClient.get<DeploymentRecord>(
      `/api/v1/dfx/projects/${projectId}/deployments/${deploymentId}`
    ),

  getDeploymentHistory: async (projectId: number): Promise<DeploymentRecord[]> =>
    apiClient.get<DeploymentRecord[]>(
      `/api/v1/dfx/projects/${projectId}/deployments`
    ),

  getCanisterStatus: (canisterId: string) => dfxApi.getCanisterStatus(canisterId),

  setCanisterPower: (projectId: number, enabled: boolean) =>
    dfxApi.setProjectPower(projectId, enabled),
};

// ---------------------------------------------------------------------------
// Canisters (dashboard view)
// ---------------------------------------------------------------------------

export const canistersApi = {
  getAll: async (): Promise<Canister[]> => {
    const items = await dashboardApi.getCanisters();
    return items.map((c) => ({
      id: String(c.id),
      name: c.name,
      projectId: String(c.id),
      status: c.is_healthy ? 'running' : 'error',
      cycles: c.cycles_balance,
      maxCycles: 0,
      memory: c.storage_used_bytes,
      subnet: 'application',
      principal: c.canister_id,
      createdAt: c.created_at,
      updatedAt: c.updated_at,
      lastDeployed: c.updated_at,
      url: c.url,
    }));
  },
  getList: () => canistersApi.getAll(),
  getById: (id: string) => projectsApi.getById(Number(id)) as unknown as Promise<Canister>,
  getDetail: (id: string) => canistersApi.getById(id),
  getMetrics: async (id: string): Promise<CanisterMetric[]> => {
    const res = await apiClient.get<{ metrics?: { cycles?: { balance: number } } }>(
      `/api/v1/projects/${id}/metrics`
    );
    return [
      {
        timestamp: new Date().toISOString(),
        cycles: res.metrics?.cycles?.balance ?? 0,
        memoryUsage: 0,
        requests: 0,
      },
    ];
  },
  getLogs: async (_id: string): Promise<CanisterLog[]> => [],
  start: async (id: string) => {
    const project = await projectsApi.getById(Number(id));
    if (!project.canister_id) throw new Error('No canister deployed');
    await dfxApi.startCanister(project.canister_id);
    return canistersApi.getById(id);
  },
  stop: async (id: string) => {
    const project = await projectsApi.getById(Number(id));
    if (!project.canister_id) throw new Error('No canister deployed');
    await dfxApi.stopCanister(project.canister_id);
    return canistersApi.getById(id);
  },
  redeploy: (id: string) => deployApi.deploy(id, {}),
  delete: (id: string) => deployApi.deleteCanister(Number(id)),
  updateSettings: (id: string, _data: { name: string; cycles?: number }) =>
    canistersApi.getById(id),
};

// ---------------------------------------------------------------------------
// Wallet — fund Account ID → convert ICP → cycles
// ---------------------------------------------------------------------------

export const walletApi = {
  getIdentity: () => apiClient.get<WalletIdentity>('/api/v1/wallet/identity'),
  refreshBalance: () => apiClient.post<WalletIdentity>('/api/v1/wallet/refresh-balance'),
  convertIcpToCycles: () => dfxApi.convertCycles(),
  getFundingInstructions: () =>
    apiClient.get<FundingInstructions>('/api/v1/wallet/funding-instructions'),
  getNetworkStatus: () => apiClient.get<Record<string, unknown>>('/api/v1/wallet/network-status'),
  recreateIdentity: () => apiClient.post<WalletIdentity>('/api/v1/wallet/recreate-identity'),
};

// ---------------------------------------------------------------------------
// Custom domains
// ---------------------------------------------------------------------------

export interface DomainRecord {
  domain_id: number;
  domain: string;
  status: string;
  canister_id?: string;
  canister_url?: string;
  ssl_active?: boolean;
  dns_configured?: boolean;
  custom_url?: string;
  created_at?: string;
  activated_at?: string;
}

export const domainsApi = {
  getAll: async (projectId?: string): Promise<DomainRecord[]> => {
    if (projectId) {
      const res = await domainsApi.getForProject(Number(projectId));
      return (res.domains ?? []) as DomainRecord[];
    }
    const res = await apiClient.get<{ success: boolean; domains: DomainRecord[] }>(
      '/api/v1/domains/user/domains'
    );
    return res.domains ?? [];
  },
  getForProject: (projectId: number) =>
    apiClient.get<{ success: boolean; domains: DomainRecord[] }>(
      `/api/v1/domains/projects/${projectId}/domains`
    ),
  setup: (projectId: number, domain_name: string, subdomain?: string) =>
    apiClient.post<{ success: boolean; data: unknown }>(
      `/api/v1/domains/projects/${projectId}/setup`,
      { domain_name, subdomain }
    ),
  verify: (domainId: number) =>
    apiClient.post<{ success: boolean }>(`/api/v1/domains/domains/${domainId}/verify-dns`, {}),
  register: (domainId: number) =>
    apiClient.post<{ success: boolean }>(`/api/v1/domains/domains/${domainId}/register`, {}),
  checkRegistration: (domainId: number) =>
    apiClient.post<{ success: boolean }>(
      `/api/v1/domains/domains/${domainId}/check-registration`,
      {}
    ),
  delete: (domainId: number) =>
    apiClient.delete<{ success: boolean }>(`/api/v1/domains/domains/${domainId}`),
  getDnsInstructions: (canisterId: string, domain: string) =>
    apiClient.get<Record<string, unknown>>(
      `/api/v1/domains/dns-instructions/${canisterId}`,
      { params: { domain } }
    ),
};

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export const analyticsApi = {
  getMetrics: (projectId: number) =>
    apiClient.get<Record<string, unknown>>(`/api/v1/projects/${projectId}/metrics`),
  getLiveMetrics: (projectId: number) =>
    apiClient.get<Record<string, unknown>>(`/api/v1/projects/${projectId}/metrics/live`),
};

export type {
  Domain,
  Project,
  WalletIdentity,
  FundingInstructions,
  DeployResult,
  DeploymentRecord,
  DfxCommandCatalog,
};
