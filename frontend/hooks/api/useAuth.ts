'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/providers/AuthProvider';
import { apiClient } from '@/lib/apiClient';

interface LoginPayload {
  email: string;
  password: string;
}

interface SignupPayload {
  email: string;
  password: string;
  username: string;
  full_name?: string;
}

interface PasswordResetPayload {
  password: string;
  token: string;
}

interface ForgotPasswordPayload {
  email: string;
}

export function useCurrentUser() {
  const { user, isLoading } = useAuth();
  return { data: user, isLoading, isError: false, error: null };
}

export function useLogin() {
  const { login } = useAuth();
  return useMutation({
    mutationFn: (payload: LoginPayload) => login(payload.email, payload.password),
  });
}

export function useSignup() {
  const { signup } = useAuth();
  return useMutation({
    mutationFn: (payload: SignupPayload) =>
      signup(payload.email, payload.password, payload.username, payload.full_name),
  });
}

export function useLogout() {
  const { logout } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logout,
    onSuccess: () => {
      queryClient.clear();
    },
  });
}

export function useForgotPassword() {
  return useMutation({
    mutationFn: async (payload: ForgotPasswordPayload) => {
      return apiClient.post<{ message: string; success: boolean }>(
        '/api/v1/auth/forgot-password',
        payload,
        { skipAuth: true }
      );
    },
  });
}

export function useResetPassword() {
  return useMutation({
    mutationFn: async (payload: PasswordResetPayload) => {
      return apiClient.post<{ message: string; success: boolean }>(
        '/api/v1/auth/reset-password',
        { new_password: payload.password, token: payload.token },
        { skipAuth: true }
      );
    },
  });
}

export function useVerifyResetToken(token: string | null) {
  return useQuery({
    queryKey: ['verify-reset-token', token],
    queryFn: () =>
      apiClient.get<{ message: string; success: boolean }>('/api/v1/auth/verify-reset-token', {
        params: { token: token! },
        skipAuth: true,
      }),
    enabled: !!token,
    retry: false,
  });
}
