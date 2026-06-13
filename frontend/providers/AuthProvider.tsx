'use client';

import {
  ReactNode,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/apiClient';
import { clearTokens, getAccessToken, setTokens, type AuthTokens } from '@/lib/auth-storage';

export interface AuthUser {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  email_verified: boolean;
}

interface AuthContextValue {
  user: AuthUser | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (
    email: string,
    password: string,
    username: string,
    fullName?: string
  ) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    if (!getAccessToken()) {
      setUser(null);
      return;
    }
    try {
      const me = await apiClient.getMe();
      setUser(me);
    } catch {
      clearTokens();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    void (async () => {
      await refreshUser();
      setIsLoading(false);
    })();
  }, [refreshUser]);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens: AuthTokens = await apiClient.login(email, password);
      setTokens(tokens);
      await refreshUser();
      router.push('/dashboard');
    },
    [refreshUser, router]
  );

  const signup = useCallback(
    async (email: string, password: string, username: string, fullName?: string) => {
      const tokens: AuthTokens = await apiClient.signup(email, password, username, fullName);
      setTokens(tokens);
      await refreshUser();
      router.push('/dashboard');
    },
    [refreshUser, router]
  );

  const logout = useCallback(async () => {
    try {
      await apiClient.logout();
    } catch {
      // Clear local session even if server call fails
    } finally {
      clearTokens();
      setUser(null);
      router.push('/auth/login');
    }
  }, [router]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      login,
      signup,
      logout,
      refreshUser,
    }),
    [user, isLoading, login, signup, logout, refreshUser]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}

export function useSessionHealth() {
  const { isAuthenticated } = useAuth();
  return {
    isHealthy: isAuthenticated,
    hasRefreshToken: !!getAccessToken(),
    hasAccessToken: !!getAccessToken(),
    lastRefresh: null,
    shouldRefresh: false,
  };
}

export function useSessionWarnings() {
  return { shouldShowWarning: false };
}
