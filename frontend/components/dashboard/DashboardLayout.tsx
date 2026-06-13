'use client';

import { ReactNode } from 'react';
import { SidebarProvider, SidebarInset } from '@/components/ui/sidebar';
import { DashboardSidebar } from './DashboardSidebar';
import { PageBreadcrumbs } from '@/components/dashboard/PageBreadcrumbs';

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <SidebarProvider>
      <DashboardSidebar />
      <SidebarInset>
        <main className="flex-1 space-y-6 p-6">
          <PageBreadcrumbs />
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
