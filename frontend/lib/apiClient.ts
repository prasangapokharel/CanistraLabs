/**
 * Low-level HTTP client — prefer lib/api.ts for feature calls.
 */
import {
  clearTokens,
  getAuthHeaders,
  getRefreshToken,
  setTokens,
  type AuthTokens,
} from './auth-storage';
import type { FundingInstructions, WalletIdentity } from '@/types/api';

const API_BASE =
  typeof window !== 'undefined'
    ? process.env.NEXT_PUBLIC_API_URL || ''
    : process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiRequestInit extends RequestInit {
  params?: Record<string, string | number | boolean>;
  skipAuth?: boolean;
}

export class ApiError extends Error {
  constructor(
    public statusCode: number,
    public data?: unknown,
    message?: string
  ) {
    super(message || `API Error: ${statusCode}`);
    this.name = 'ApiError';
  }
}

function buildUrl(path: string, params?: ApiRequestInit['params']): string {
  const base = API_BASE || (typeof window !== 'undefined' ? window.location.origin : '');
  const url = new URL(path.startsWith('http') ? path : `${base}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, String(value));
    });
  }
  return url.toString();
}

async function refreshAccessToken(): Promise<boolean> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return false;
  try {
    const response = await fetch(buildUrl('/api/v1/auth/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!response.ok) {
      clearTokens();
      return false;
    }
    setTokens((await response.json()) as AuthTokens);
    return true;
  } catch {
    clearTokens();
    return false;
  }
}

async function request<T>(url: string, init: ApiRequestInit = {}): Promise<T> {
  const { params, skipAuth, headers, ...rest } = init;
  const finalUrl = buildUrl(url, params);
  const authHeaders = skipAuth ? {} : getAuthHeaders();

  let response = await fetch(finalUrl, {
    ...rest,
    redirect: 'manual',
    headers: { 'Content-Type': 'application/json', ...authHeaders, ...headers },
  });

  // Never follow redirects — they drop Authorization on cross-origin hops (3000 → 8000)
  if (response.status >= 300 && response.status < 400) {
    const location = response.headers.get('Location');
    if (location) {
      const redirectUrl = location.startsWith('http')
        ? location
        : new URL(location, finalUrl).toString();
      response = await fetch(redirectUrl, {
        ...rest,
        redirect: 'manual',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders(), ...headers },
      });
    }
  }

  if (response.status === 401 && !skipAuth) {
    if (await refreshAccessToken()) {
      response = await fetch(finalUrl, {
        ...rest,
        redirect: 'manual',
        headers: { 'Content-Type': 'application/json', ...getAuthHeaders(), ...headers },
      });
    }
  }

  if (!response.ok) {
    let data: unknown;
    try {
      data = await response.json();
    } catch {
      data = response.statusText;
    }
    const detail =
      typeof data === 'object' && data !== null && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : undefined;
    throw new ApiError(response.status, data, detail);
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const apiClient = {
  get: <T>(url: string, init?: ApiRequestInit) => request<T>(url, { ...init, method: 'GET' }),
  post: <T>(url: string, body?: unknown, init?: ApiRequestInit) =>
    request<T>(url, {
      ...init,
      method: 'POST',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  put: <T>(url: string, body?: unknown, init?: ApiRequestInit) =>
    request<T>(url, {
      ...init,
      method: 'PUT',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  patch: <T>(url: string, body?: unknown, init?: ApiRequestInit) =>
    request<T>(url, {
      ...init,
      method: 'PATCH',
      body: body !== undefined ? JSON.stringify(body) : undefined,
    }),
  delete: <T>(url: string, init?: ApiRequestInit) => request<T>(url, { ...init, method: 'DELETE' }),
  request,

  // Auth
  login: (email: string, password: string) =>
    request<AuthTokens>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      skipAuth: true,
    }),
  signup: (email: string, password: string, username: string, full_name?: string) =>
    request<AuthTokens>('/api/v1/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, username, full_name }),
      skipAuth: true,
    }),
  logout: () => request<{ message: string; success: boolean }>('/api/v1/auth/logout', { method: 'POST' }),
  getMe: () =>
    request<{
      id: number;
      email: string;
      username: string;
      full_name?: string;
      email_verified: boolean;
    }>('/api/v1/auth/me'),

  // Wallet shortcuts (prefer walletApi from lib/api.ts)
  getWalletIdentity: () => request<WalletIdentity>('/api/v1/wallet/identity'),
  getWalletStatus: () => request<FundingInstructions>('/api/v1/wallet/funding-instructions'),
  refreshWalletBalance: () => request<WalletIdentity>('/api/v1/wallet/refresh-balance', { method: 'POST' }),
  convertIcpToCycles: () =>
    request<{ success: boolean; message?: string }>('/api/v1/wallet/convert-icp-to-cycles', {
      method: 'POST',
    }),
  recreateIdentity: () => request<WalletIdentity>('/api/v1/wallet/recreate-identity', { method: 'POST' }),

  // Domain shortcuts (prefer domainsApi)
  getProjectDomains: (projectId: number) =>
    request<{ success: boolean; domains: unknown[] }>(
      `/api/v1/domains/projects/${projectId}/domains`
    ),
  setupDomain: (projectId: number, domain_name: string, subdomain?: string) =>
    apiClient.post<{ success: boolean; data: unknown }>(
      `/api/v1/domains/projects/${projectId}/setup`,
      { domain_name, subdomain }
    ),
  verifyDomainDns: (domainId: number) =>
    apiClient.post<{ success: boolean }>(`/api/v1/domains/domains/${domainId}/verify-dns`, {}),
  registerDomain: (domainId: number) =>
    apiClient.post<{ success: boolean }>(`/api/v1/domains/domains/${domainId}/register`, {}),
  checkDomainRegistration: (domainId: number) =>
    apiClient.post<{ success: boolean }>(
      `/api/v1/domains/domains/${domainId}/check-registration`,
      {}
    ),
};

export function handleApiError(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.message && error.message !== `API Error: ${error.statusCode}`) {
      return error.message;
    }
    if (typeof error.data === 'object' && error.data !== null && 'detail' in error.data) {
      const detail = (error.data as { detail: unknown }).detail;
      if (detail && typeof detail === 'object' && detail !== null && 'message' in detail) {
        return String((detail as { message: unknown }).message);
      }
      return String(detail);
    }
    return `Request failed (${error.statusCode})`;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred';
}
