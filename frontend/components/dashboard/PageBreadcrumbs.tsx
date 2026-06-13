'use client';

import { usePathname } from 'next/navigation';
import Link from 'next/link';
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';

export function PageBreadcrumbs() {
  const pathname = usePathname();

  // Parse pathname to create breadcrumb items
  const segments = pathname
    .split('/')
    .filter(Boolean)
    .map((segment) => ({
      label: segment.charAt(0).toUpperCase() + segment.slice(1).replace(/-/g, ' '),
      href: '/' + pathname.split('/').slice(0, pathname.split('/').indexOf(segment) + 1).join('/'),
    }));

  if (segments.length === 0) {
    return null;
  }

  return (
    <Breadcrumb>
      <BreadcrumbList>
        <BreadcrumbItem>
          <BreadcrumbLink asChild>
            <Link href="/dashboard">Dashboard</Link>
          </BreadcrumbLink>
        </BreadcrumbItem>
        {segments.map((segment, index) => (
          <BreadcrumbItem key={segment.href}>
            <BreadcrumbSeparator />
            {index === segments.length - 1 ? (
              <BreadcrumbPage>{segment.label}</BreadcrumbPage>
            ) : (
              <BreadcrumbLink asChild>
                <Link href={segment.href}>{segment.label}</Link>
              </BreadcrumbLink>
            )}
          </BreadcrumbItem>
        ))}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
