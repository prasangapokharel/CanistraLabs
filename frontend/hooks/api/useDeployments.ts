'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deployApi, dfxApi } from '@/lib/api';
import type { DeploymentPayload } from '@/types/api';

interface Deployment {
  id: number | string;
  project_id?: number;
  status: string;
  created_at?: string;
  completed_at?: string;
  error?: string;
}

export function useDeployments(projectId: string) {
  return useQuery({
    queryKey: ['deployments', projectId],
    queryFn: () => deployApi.getDeploymentHistory(Number(projectId)),
    staleTime: 3 * 60 * 1000,
    enabled: !!projectId,
    retry: false,
    throwOnError: false,
  });
}

export function useDeployment(projectId: string, deploymentId: string) {
  return useQuery({
    queryKey: ['deployments', projectId, deploymentId],
    queryFn: () => deployApi.getDeploymentStatus(Number(projectId), Number(deploymentId)),
    staleTime: 60 * 1000,
    enabled: !!projectId && !!deploymentId,
  });
}

export function useCanisterStatus(canisterId: string) {
  return useQuery({
    queryKey: ['canisterStatus', canisterId],
    queryFn: () => dfxApi.getCanisterStatus(canisterId),
    staleTime: 30_000,
    enabled: !!canisterId,
  });
}

export function useDeployProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (projectId: string | number | DeploymentPayload) => {
      const id =
        typeof projectId === 'object'
          ? projectId.projectId ?? projectId.project_id
          : projectId;
      if (!id) throw new Error('projectId is required');
      const payload = typeof projectId === 'object' ? projectId : {};
      return deployApi.deploy(id, payload);
    },
    onSuccess: (_data, variables) => {
      const projectId =
        typeof variables === 'object' && variables !== null
          ? (variables as DeploymentPayload).projectId ??
            (variables as DeploymentPayload).project_id
          : variables;
      if (projectId) {
        queryClient.invalidateQueries({ queryKey: ['deployments', String(projectId)] });
      }
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useCancelDeployment(_projectId: string, _deploymentId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      throw new Error('Deployment cancellation is not supported');
    },
    onSuccess: (_data, _vars, _ctx) => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
    },
  });
}

export type { Deployment };
