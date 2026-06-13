'use client';

import Link from 'next/link';
import { Suspense } from 'react';
import { ResetPasswordForm } from '@/components/auth/reset-password';
import { AuthLayout } from '@/components/auth/layout';

export default function ResetPasswordPage() {
  return (
    <AuthLayout title="Set new password">
      <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
        <ResetPasswordForm />
      </Suspense>
      <p className="text-center text-sm text-muted-foreground mt-4">
        <Link href="/auth/login" className="underline">
          Back to sign in
        </Link>
      </p>
    </AuthLayout>
  );
}
