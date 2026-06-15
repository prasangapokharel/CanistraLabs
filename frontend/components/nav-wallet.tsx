'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Zap, Receipt } from 'lucide-react';
import {
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { HugeiconsIcon } from '@hugeicons/react';
import { Wallet01Icon } from '@hugeicons/core-free-icons';

const walletBase = '/dashboard/wallet';
const convertPath = `${walletBase}/convert`;
const billingPath = '/dashboard/billing';

export function NavWallet() {
  const pathname = usePathname();

  return (
    <SidebarGroup>
      <SidebarGroupLabel>Wallet</SidebarGroupLabel>
      <SidebarGroupContent>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Wallet"
              isActive={pathname === walletBase}
              render={<Link href={walletBase} />}
            >
              <HugeiconsIcon icon={Wallet01Icon} strokeWidth={2} />
              <span>Wallet</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Convert to cycles"
              isActive={pathname === convertPath}
              render={<Link href={convertPath} />}
            >
              <Zap className="size-4 shrink-0" />
              <span>Convert</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <SidebarMenuButton
              tooltip="Billing"
              isActive={pathname === billingPath}
              render={<Link href={billingPath} />}
            >
              <Receipt className="size-4 shrink-0" />
              <span>Billing</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarGroupContent>
    </SidebarGroup>
  );
}
