'use client';

import Link from 'next/link';
import { useICPWallet } from '@/lib/wallet/ICPWalletContext';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Wallet, Copy, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';

export function WalletManager() {
  const { wallet, isInitialized, isConnected, refresh, fundWallet } = useICPWallet();

  const handleCopy = (value?: string) => {
    if (!value) return;
    void navigator.clipboard.writeText(value);
    toast.success('Copied to clipboard');
  };

  if (!isInitialized) {
    return <div className="h-8 w-24 animate-pulse rounded bg-muted" />;
  }

  if (!isConnected || !wallet) {
    return (
      <Button variant="outline" size="sm" render={<Link href="/dashboard/wallet" />}>
        <Wallet className="mr-2 h-4 w-4" />
        Wallet
      </Button>
    );
  }

  const principal = wallet.principal_id ?? '';
  const truncated =
    principal.length > 16
      ? `${principal.slice(0, 8)}...${principal.slice(-6)}`
      : principal;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Wallet className="h-4 w-4" />
          <span>{wallet.formatted_cycles ?? '0 cycles'}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-72">
        <DropdownMenuLabel>ICP Platform Wallet</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <div className="px-2 py-2 text-xs">
          <div className="mb-1 font-semibold">Principal</div>
          <div className="flex items-center gap-2 rounded bg-muted p-2">
            <code className="flex-1 break-all">{truncated}</code>
            <button type="button" onClick={() => handleCopy(principal)}>
              <Copy className="h-3 w-3" />
            </button>
          </div>
        </div>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => void refresh()} className="cursor-pointer">
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh balance
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => void fundWallet()} className="cursor-pointer">
          Sync funding status
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/dashboard/wallet">Open wallet dashboard</Link>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
