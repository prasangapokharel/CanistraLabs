'use client';

import { walletApi } from '@/lib/api';

export function useWalletOperations() {
  return {
    fundWalletWithPromoCode: async (_opts: { promoCode: string }) => {
      await walletApi.refreshBalance();
    },
    allocateCyclesToCanister: async (_opts: { canisterId: string; cycles: number }) => {
      throw new Error('Direct cycle allocation is managed by the platform wallet');
    },
    refreshWalletBalance: () => walletApi.refreshBalance(),
    getTransactionHistory: async (_limit: number) => ({ transactions: [] as unknown[] }),
    convertICPToCycles: () => walletApi.convertIcpToCycles(),
  };
}
