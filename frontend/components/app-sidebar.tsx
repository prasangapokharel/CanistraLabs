'use client';

import Image from 'next/image';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { NavMain } from '@/components/nav-main';
import { NavWallet } from '@/components/nav-wallet';
import { NavUser } from '@/components/nav-user';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { HugeiconsIcon } from '@hugeicons/react';
import {
  DashboardSquare01Icon,
  Folder01Icon,
  Globe02Icon,
  ChartHistogramIcon,
} from '@hugeicons/core-free-icons';
import { Server } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { walletApi } from '@/lib/api';

const navMain = [
  {
    title: 'Dashboard',
    url: '/dashboard',
    icon: <HugeiconsIcon icon={DashboardSquare01Icon} strokeWidth={2} />,
  },
  {
    title: 'Projects',
    url: '/dashboard/projects',
    icon: <HugeiconsIcon icon={Folder01Icon} strokeWidth={2} />,
  },
  {
    title: 'Canisters',
    url: '/dashboard/canisters',
    icon: <Server className="size-4 shrink-0" />,
  },
  {
    title: 'Domains',
    url: '/dashboard/domains',
    icon: <HugeiconsIcon icon={Globe02Icon} strokeWidth={2} />,
  },
  {
    title: 'Analytics',
    url: '/dashboard/analytics',
    icon: <HugeiconsIcon icon={ChartHistogramIcon} strokeWidth={2} />,
  },
];

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { user } = useAuth();

  const { data: wallet } = useQuery({
    queryKey: ['wallet', 'identity'],
    queryFn: () => walletApi.getIdentity(),
    staleTime: 30_000,
  });

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" render={<Link href="/dashboard" />}>
              <Image
                src="/images/logo/icp.svg"
                alt="Internet Computer"
                width={36}
                height={18}
                className="h-7 w-auto max-w-[2.25rem] shrink-0 object-contain"
              />
              <div className="flex flex-col gap-0.5 leading-none">
                <span className="font-semibold">Canistra</span>
                <span className="text-xs text-muted-foreground">ICP Hosting</span>
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        <NavMain items={navMain} />
        <NavWallet />

        {wallet && (
          <SidebarGroup className="mt-auto">
            <SidebarGroupContent>
              <div className="rounded-lg border bg-background/60 px-3 py-2 text-xs space-y-1">
                <p className="text-muted-foreground">
                  {wallet.token_symbol ?? 'ICP'}:{' '}
                  {wallet.formatted_icp ?? wallet.icp_balance ?? '0'}
                </p>
                <p className="text-muted-foreground">
                  Cycles: {wallet.formatted_cycles ?? wallet.cycles_balance ?? '0'}
                </p>
              </div>
            </SidebarGroupContent>
          </SidebarGroup>
        )}
      </SidebarContent>

      <SidebarFooter>
        <NavUser
          user={{
            name: user?.email?.split('@')[0] ?? 'User',
            email: user?.email ?? '',
            avatar: '',
          }}
        />
      </SidebarFooter>
    </Sidebar>
  );
}
