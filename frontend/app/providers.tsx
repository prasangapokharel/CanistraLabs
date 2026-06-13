'use client';

import { ReactNode } from 'react';
import { QueryProvider } from '@/lib/queryProvider';
import { ThemeProvider } from '@/components/shared/theme-provider';
import { Toaster } from '@/components/ui/sonner';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ConditionalLayout } from '@/components/shared/ConditionalLayout';
import { AuthProvider } from '@/providers/AuthProvider';
import { ICPWalletProvider } from '@/lib/wallet/ICPWalletContext';

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem disableTransitionOnChange>
      <TooltipProvider>
        <QueryProvider>
          <AuthProvider>
            <ICPWalletProvider>
              <ConditionalLayout>{children}</ConditionalLayout>
            </ICPWalletProvider>
            <Toaster />
          </AuthProvider>
        </QueryProvider>
      </TooltipProvider>
    </ThemeProvider>
  );
}
