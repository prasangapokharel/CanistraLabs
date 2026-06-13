'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function CanisterDetailRedirect() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string | undefined;

  useEffect(() => {
    router.replace(id ? `/dashboard/projects/${id}` : '/dashboard/projects');
  }, [id, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-sm text-muted-foreground">Redirecting…</p>
    </div>
  );
}
