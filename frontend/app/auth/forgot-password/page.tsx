'use client';

import Link from 'next/link';
import { ForgotPasswordForm } from '@/components/auth/forgot-password';
import { AuthLayout } from '@/components/auth/layout';

export default function ForgotPasswordPage() {
  return (
    <AuthLayout title="Reset password">
      <ForgotPasswordForm />
      <p className="text-center text-sm text-muted-foreground mt-4">
        <Link href="/auth/login" className="underline">
          Back to sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
