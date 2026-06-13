/**
 * Query key factories for TanStack Query
 */

export const queryKeys = {
  all: ['api'] as const,
  
  auth: {
    all: ['auth'] as const,
    currentUser: () => [...queryKeys.auth.all, 'currentUser'] as const,
  },

  dashboard: {
    all: ['dashboard'] as const,
    stats: () => [...queryKeys.dashboard.all, 'stats'] as const,
    canisters: () => [...queryKeys.dashboard.all, 'canisters'] as const,
    projects: () => [...queryKeys.dashboard.all, 'projects'] as const,
    activity: () => [...queryKeys.dashboard.all, 'activity'] as const,
  },

  projects: {
    all: ['projects'] as const,
    lists: () => [...queryKeys.projects.all, 'list'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.projects.lists(), { ...filters }] as const,
    details: () => [...queryKeys.projects.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.projects.details(), id] as const,
  },

  deployments: {
    all: ['deployments'] as const,
    lists: () => [...queryKeys.deployments.all, 'list'] as const,
    list: (projectId: string) =>
      [...queryKeys.deployments.lists(), projectId] as const,
    details: () => [...queryKeys.deployments.all, 'detail'] as const,
    detail: (projectId: string, id: string) =>
      [...queryKeys.deployments.details(), projectId, id] as const,
  },

  canisters: {
    all: ['canisters'] as const,
    lists: () => [...queryKeys.canisters.all, 'list'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.canisters.lists(), { ...filters }] as const,
    details: () => [...queryKeys.canisters.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.canisters.details(), id] as const,
    metrics: (id: string) => [...queryKeys.canisters.all, 'metrics', id] as const,
    logs: (id: string) => [...queryKeys.canisters.all, 'logs', id] as const,
  },

  domains: {
    all: ['domains'] as const,
    lists: () => [...queryKeys.domains.all, 'list'] as const,
    list: (projectId?: string) =>
      projectId
        ? [...queryKeys.domains.lists(), projectId]
        : [...queryKeys.domains.lists()] as const,
    details: () => [...queryKeys.domains.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.domains.details(), id] as const,
  },

  wallet: {
    all: ['wallet'] as const,
    balance: () => [...queryKeys.wallet.all, 'balance'] as const,
    transactions: () => [...queryKeys.wallet.all, 'transactions'] as const,
  },

  analytics: {
    all: ['analytics'] as const,
    stats: (projectId?: string) =>
      projectId
        ? [...queryKeys.analytics.all, 'stats', projectId]
        : [...queryKeys.analytics.all, 'stats'] as const,
  },
} as const;
