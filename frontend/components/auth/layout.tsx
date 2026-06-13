'use client';

import Image from 'next/image';
import { ReactNode } from 'react';

export function AuthLayout({ children, title }: { children: ReactNode; title: string }) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-background">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <Image
            src="/images/logo/icp.png"
            alt="Internet Computer"
            width={108}
            height={71}
            className="mx-auto mb-4"
            priority
          />
          <h1 className="text-xl font-semibold">{title}</h1>
          <p className="text-sm text-muted-foreground mt-1">Host websites on the Internet Computer</p>
        </div>
        {children}
      </div>
    </div>
  );
}
