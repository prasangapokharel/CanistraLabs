'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/lib/api';
import type { Project } from '@/types/api';

export interface CreateProjectPayload {
  name: string;
  description?: string;
  language?: string;
  code_content?: string;
}

export interface UpdateProjectPayload {
  id?: string | number;
  name?: string;
  description?: string;
  code_content?: string;
}

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => projectsApi.getAll(),
    staleTime: 5 * 60 * 1000,
  });
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId],
    queryFn: () => projectsApi.getById(Number(projectId)),
    staleTime: 5 * 60 * 1000,
    enabled: !!projectId,
  });
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateProjectPayload) => projectsApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export function useUpdateProject(projectId?: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UpdateProjectPayload & { id?: string | number }) => {
      const id = payload.id ?? projectId;
      if (!id) throw new Error('Project ID is required');
      return projectsApi.update(Number(id), payload);
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      const id = variables.id ?? projectId;
      if (id) {
        queryClient.invalidateQueries({ queryKey: ['projects', String(id)] });
      }
    },
  });
}

export function useDeleteProject() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (projectId: string | number) => projectsApi.delete(Number(projectId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

export type { Project };
