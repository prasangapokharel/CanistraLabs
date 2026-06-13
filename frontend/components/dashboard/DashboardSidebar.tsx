'use client';

import { usePathname } from 'next/navigation';
import { AppSidebar } from '@/components/app-sidebar';
import { SiteHeader } from '@/components/site-header';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { cn } from '@/lib/utils';

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isEditor = Boolean(pathname?.match(/^\/dashboard\/projects\/[^/]+$/));

  return (
    <SidebarProvider
      style={
        {
          '--sidebar-width': 'calc(var(--spacing) * 72)',
          '--header-height': 'calc(var(--spacing) * 12)',
        } as React.CSSProperties
      }
    >
      <AppSidebar variant="inset" />
      <SidebarInset>
        <SiteHeader />
        <div className="flex flex-1 flex-col min-h-0">
          <div
            className={cn(
              'flex flex-1 flex-col',
              isEditor ? 'min-h-0 overflow-hidden p-4' : 'gap-4 p-4 md:p-6 mx-auto w-full max-w-4xl'
            )}
          >
            {children}
          </div>
        </div>
      </SidebarInset>
    </SidebarProvider>
  );
}

/** @deprecated Use AppSidebar via DashboardShell */
export { AppSidebar as DashboardSidebar } from '@/components/app-sidebar';
