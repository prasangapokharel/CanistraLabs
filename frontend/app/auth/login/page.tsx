'use client';

import { LoginForm } from '@/components/auth/login';
import { AuthLayout } from '@/components/auth/layout';

export default function LoginPage() {
  return (
    <AuthLayout title="Sign in">
      <LoginForm />
    </AuthLayout>
  );
}
