'use client';

import { AuthGuard } from '@/components/auth/guard';
import { DashboardShell } from '@/components/dashboard/DashboardSidebar';

export default function DashboardLayoutPage({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <DashboardShell>{children}</DashboardShell>
    </AuthGuard>
  );
}
