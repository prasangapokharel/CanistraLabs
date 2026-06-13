'use client';

import { SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Badge } from '@/components/ui/badge';
import { 
  Search, 
  Bell, 
  Settings, 
  User, 
  LogOut, 
  HelpCircle, 
  Moon, 
  Sun,
  Command,
  ChevronDown
} from 'lucide-react';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { useLogout } from '@/hooks/api/useAuth';
import { useCurrentUser } from '@/hooks/api/useAuth';

export function DashboardHeader() {
  const pathname = usePathname();
  const [searchQuery, setSearchQuery] = useState('');
  const [theme, setTheme] = useState<'light' | 'dark'>(
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark') ? 'dark' : 'light'
  );
  const notifications = 3; // Mock notification count for now
  
  const logoutMutation = useLogout();
  const { data: currentUser } = useCurrentUser();
  
  // Theme toggle functionality
  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    document.documentElement.classList.toggle('dark');
  };

  // Initialize theme on mount
  useEffect(() => {}, []);
  
  const getBreadcrumbs = () => {
    const segments = pathname.split('/').filter(Boolean);
    const breadcrumbs = [];
    
    for (let i = 0; i < segments.length; i++) {
      const segment = segments[i];
      const href = '/' + segments.slice(0, i + 1).join('/');
      const isLast = i === segments.length - 1;
      
      let title = segment.charAt(0).toUpperCase() + segment.slice(1);
      
      // Enhanced breadcrumb mapping
      const titleMap: Record<string, string> = {
        'dashboard': 'Dashboard',
        'projects': 'Projects',
        'new': 'New Project',
        'settings': 'Settings',
        'profile': 'Profile',
        'domains': 'Domains',
        'wallet': 'Wallet',
        'canisters': 'Canisters',
        'deploy': 'Deploy',
        'analytics': 'Analytics',
        'billing': 'Billing',
        'team': 'Team',
      };
      
      title = titleMap[segment] || title;
      
      // Special handling for dynamic routes
      if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment)) {
        title = `Project #${segment.slice(0, 8)}`;
      }
      
      breadcrumbs.push({
        title,
        href,
        isLast,
      });
    }
    
    return breadcrumbs;
  };
  
  const breadcrumbs = getBreadcrumbs();

  const handleLogout = () => {
    logoutMutation.mutate();
  };

  return (
    <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-2 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4">
      {/* Left section - Sidebar trigger and breadcrumbs */}
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <SidebarTrigger className="-ml-1 hover:bg-accent hover:text-accent-foreground transition-colors" />
        <Separator orientation="vertical" className="mr-2 h-4" />
        
        <Breadcrumb className="hidden md:flex">
          <BreadcrumbList>
            {breadcrumbs.map((crumb, index) => (
              <div key={crumb.href} className="flex items-center">
                {index > 0 && <BreadcrumbSeparator className="text-muted-foreground" />}
                <BreadcrumbItem>
                  {crumb.isLast ? (
                    <BreadcrumbPage className="font-semibold text-foreground">
                      {crumb.title}
                    </BreadcrumbPage>
                  ) : (
                    <BreadcrumbLink 
                      href={crumb.href}
                      className="transition-colors hover:text-foreground text-muted-foreground"
                    >
                      {crumb.title}
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
              </div>
            ))}
          </BreadcrumbList>
        </Breadcrumb>
        
        {/* Mobile breadcrumb - show only current page */}
        <div className="md:hidden">
          <h1 className="font-semibold text-foreground">
            {breadcrumbs[breadcrumbs.length - 1]?.title || 'Dashboard'}
          </h1>
        </div>
      </div>

      {/* Center section - Search (hidden on mobile) */}
      <div className="hidden lg:flex items-center max-w-sm mx-4">
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search projects, domains..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9 pr-4 h-9 bg-muted/50 border-0 focus:bg-background focus:ring-1 focus:ring-ring transition-all"
          />
          <kbd className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none inline-flex h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            <Command className="h-3 w-3" />
            K
          </kbd>
        </div>
      </div>

      {/* Right section - Actions and user menu */}
      <div className="flex items-center gap-2">
        {/* Search button for mobile */}
        <Button
          variant="ghost"
          size="sm"
          className="lg:hidden h-9 w-9 p-0"
          onClick={() => {
            // TODO: Open mobile search modal
          }}
        >
          <Search className="h-4 w-4" />
          <span className="sr-only">Search</span>
        </Button>

        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="sm"
          className="h-9 w-9 p-0"
          onClick={toggleTheme}
        >
          {theme === 'light' ? (
            <Moon className="h-4 w-4" />
          ) : (
            <Sun className="h-4 w-4" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>

        {/* Notifications */}
        <Button
          variant="ghost"
          size="sm"
          className="h-9 w-9 p-0 relative"
          render={<Link href="/dashboard/notifications" />}
        >
          <Bell className="h-4 w-4" />
          {notifications > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-1 -right-1 h-5 w-5 p-0 text-xs flex items-center justify-center"
            >
              {notifications > 99 ? '99+' : notifications}
            </Badge>
          )}
          <span className="sr-only">
            {notifications > 0 ? `${notifications} notifications` : 'Notifications'}
          </span>
        </Button>

        {/* Help */}
        <Button
          variant="ghost"
          size="sm"
          className="h-9 w-9 p-0"
          render={<Link href="/help" />}
        >
          <HelpCircle className="h-4 w-4" />
          <span className="sr-only">Help</span>
        </Button>

        <Separator orientation="vertical" className="h-6" />

        {/* User menu */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              className="h-9 px-2 flex items-center gap-2 hover:bg-accent transition-colors"
            >
              <Avatar className="h-7 w-7">
                <AvatarImage 
                  src={undefined} // Avatar URL would come from a separate field if available
                  alt={currentUser?.full_name || currentUser?.username || 'User avatar'} 
                />
                <AvatarFallback className="text-xs font-semibold bg-primary text-primary-foreground">
                  {(currentUser?.full_name || currentUser?.username)?.charAt(0)?.toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
              <div className="hidden sm:flex flex-col items-start min-w-0">
                <span className="text-sm font-medium text-foreground truncate max-w-[120px]">
                  {currentUser?.full_name || currentUser?.username || 'User'}
                </span>
                <span className="text-xs text-muted-foreground truncate max-w-[120px]">
                  {currentUser?.email || 'user@example.com'}
                </span>
              </div>
              <ChevronDown className="h-3 w-3 text-muted-foreground" />
            </Button>
          </DropdownMenuTrigger>
          
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">
                  {currentUser?.full_name || currentUser?.username || 'User'}
                </p>
                <p className="text-xs leading-none text-muted-foreground">
                  {currentUser?.email || 'user@example.com'}
                </p>
              </div>
            </DropdownMenuLabel>
            
            <DropdownMenuSeparator />
            
            <DropdownMenuItem asChild>
              <Link href="/dashboard/profile" className="cursor-pointer">
                <User className="mr-2 h-4 w-4" />
                Profile
              </Link>
            </DropdownMenuItem>
            
            <DropdownMenuItem asChild>
              <Link href="/dashboard/settings" className="cursor-pointer">
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </Link>
            </DropdownMenuItem>
            
            <DropdownMenuSeparator />
            
            <DropdownMenuItem 
              onClick={handleLogout}
              className="cursor-pointer text-destructive focus:text-destructive"
              disabled={logoutMutation.isPending}
            >
              <LogOut className="mr-2 h-4 w-4" />
              {logoutMutation.isPending ? 'Signing out...' : 'Sign out'}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
