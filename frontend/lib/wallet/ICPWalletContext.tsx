'use client';

import { ReactNode, createContext, useCallback, useContext, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { walletApi } from '@/lib/api';
import type { WalletIdentity } from '@/types/api';
import { getAccessToken } from '@/lib/auth-storage';

interface WalletContextValue {
  wallet: WalletIdentity | null;
  isInitialized: boolean;
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  fundWallet: () => Promise<void>;
  requestTestnetCycles: () => Promise<boolean>;
  refresh: () => Promise<void>;
}

const WalletContext = createContext<WalletContextValue | null>(null);

export function ICPWalletProvider({ children }: { children: ReactNode }) {
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['wallet', 'identity'],
    queryFn: () => walletApi.getIdentity() as Promise<WalletIdentity>,
    enabled: !!getAccessToken(),
    retry: false,
    staleTime: 30_000,
  });

  const refresh = useCallback(async () => {
    await refetch();
  }, [refetch]);

  const value = useMemo<WalletContextValue>(
    () => ({
      wallet: data ?? null,
      isInitialized: !isLoading,
      isConnected: !!data?.principal_id,
      connect: refresh,
      disconnect: () => {},
      fundWallet: async () => {
        await walletApi.refreshBalance();
        await refetch();
      },
      requestTestnetCycles: async () => {
        await walletApi.convertIcpToCycles();
        await refetch();
        return true;
      },
      refresh,
    }),
    [data, isLoading, refresh, refetch]
  );

  return <WalletContext.Provider value={value}>{children}</WalletContext.Provider>;
}

export function useICPWallet(): WalletContextValue {
  const ctx = useContext(WalletContext);
  if (!ctx) {
    throw new Error('useICPWallet must be used within ICPWalletProvider');
  }
  return ctx;
}
