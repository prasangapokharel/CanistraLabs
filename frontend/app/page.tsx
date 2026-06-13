'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/providers/AuthProvider';

export default function HomePage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isLoading) return;
    router.replace(isAuthenticated ? '/dashboard' : '/auth/login');
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-sm text-muted-foreground">Loading…</p>
    </div>
  );
}
