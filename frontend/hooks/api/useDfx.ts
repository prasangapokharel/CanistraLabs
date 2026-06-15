'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { dfxApi } from '@/lib/api';
import { queryKeys } from '@/lib/query-keys';

export function useDfxCommands() {
  return useQuery({
    queryKey: queryKeys.dfx.commands(),
    queryFn: () => dfxApi.getCommands(),
    staleTime: 60 * 60 * 1000,
  });
}

export function useDfxPing(network = 'ic') {
  return useQuery({
    queryKey: queryKeys.dfx.ping(network),
    queryFn: () => dfxApi.ping(network),
    staleTime: 30_000,
  });
}

export function useDfxCanisterStatus(canisterId: string) {
  return useQuery({
    queryKey: queryKeys.dfx.canisterStatus(canisterId),
    queryFn: () => dfxApi.getCanisterStatus(canisterId),
    staleTime: 30_000,
    enabled: !!canisterId,
  });
}

export function useDfxCanisterUrl(canisterId: string) {
  return useQuery({
    queryKey: queryKeys.dfx.canisterUrl(canisterId),
    queryFn: () => dfxApi.getCanisterUrl(canisterId),
    staleTime: 60_000,
    enabled: !!canisterId,
  });
}

export function useDfxConvertCycles() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (amount?: string) => dfxApi.convertCycles(amount ? { amount } : undefined),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.wallet.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dfx.all });
    },
  });
}

export function useDfxProjectPower(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (enabled: boolean) => dfxApi.setProjectPower(projectId, enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dfx.all });
    },
  });
}
