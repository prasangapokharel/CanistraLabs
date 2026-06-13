export const queryKeys = {
  dashboard: {
    stats: ['dashboard', 'stats'] as const,
    canisters: ['dashboard', 'canisters'] as const,
    activities: ['dashboard', 'activities'] as const,
  },
  canisters: {
    all: ['canisters'] as const,
    list: (filters?: unknown) => ['canisters', 'list', filters] as const,
    detail: (id: string) => ['canisters', 'detail', id] as const,
    metrics: (id: string) => ['canisters', 'metrics', id] as const,
    logs: (id: string) => ['canisters', 'logs', id] as const,
  },
}
