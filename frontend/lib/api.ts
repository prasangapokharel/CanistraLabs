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
  FundingInstructions,
  Project,
  WalletIdentity,
} from '@/types/api';

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
// Deployments & hosting
// ---------------------------------------------------------------------------

export const deployApi = {
  /** Deploy project HTML/assets to a new ICP canister */
  deploy: (projectId: string | number, data?: { code_content?: string; force?: boolean }) =>
    apiClient.post<DeployResult>(
      `/api/v1/deployments/projects/${projectId}/deploy`,
      data ?? {}
    ),

  /** Re-deploy after funding (same as deploy) */
  resume: (projectId: string | number) =>
    deployApi.deploy(projectId, { force: true }),

  updateCanister: (projectId: number, data?: { code_content?: string }) =>
    apiClient.post<DeployResult>(
      `/api/v1/deployments/projects/${projectId}/update-canister`,
      data ?? {}
    ),

  deleteCanister: (projectId: number) =>
    apiClient.delete<{ message: string }>(`/api/v1/deployments/projects/${projectId}/canister`),

  getDeploymentStatus: (projectId: number, deploymentId: number) =>
    apiClient.get<DeploymentRecord>(
      `/api/v1/deployments/projects/${projectId}/deployments/${deploymentId}`
    ),

  getDeploymentHistory: async (projectId: number): Promise<DeploymentRecord[]> =>
    apiClient.get<DeploymentRecord[]>(
      `/api/v1/deployments/projects/${projectId}/deployments`
    ),

  getCanisterStatus: (canisterId: string) =>
    apiClient.get<CanisterStatus>(`/api/v1/deployments/canisters/${canisterId}/status`),

  setCanisterPower: (projectId: number, enabled: boolean) =>
    apiClient.post<{
      project_id: number;
      canister_id: string;
      enabled: boolean;
      status: string;
      canister_status: string;
    }>(`/api/v1/deployments/projects/${projectId}/canister/power`, { enabled }),
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
  start: (id: string) => canistersApi.getById(id),
  stop: (id: string) => canistersApi.getById(id),
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
  convertIcpToCycles: () =>
    apiClient.post<{ success: boolean; message?: string; cycles_balance?: number }>(
      '/api/v1/wallet/convert-icp-to-cycles'
    ),
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
  ssl_active?: boolean;
  dns_configured?: boolean;
  custom_url?: string;
  created_at?: string;
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

export type { Domain, Project, WalletIdentity, FundingInstructions, DeployResult, DeploymentRecord };
