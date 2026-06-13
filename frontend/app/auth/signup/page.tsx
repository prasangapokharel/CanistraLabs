'use client';

import { SignupForm } from '@/components/auth/register';
import { AuthLayout } from '@/components/auth/layout';

export default function SignupPage() {
  return (
    <AuthLayout title="Create account">
      <SignupForm />
    </AuthLayout>
  );
}
