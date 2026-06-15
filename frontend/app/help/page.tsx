'use client';

import Link from 'next/link';
import { Header } from '@/components/landing/Header';
import { Footer } from '@/components/landing/Footer';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button, buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';

const guides = [
  {
    title: 'Create a project',
    body: 'Sign up, open Dashboard → New project, add HTML/CSS/JS, and click Deploy.',
    href: '/auth/signup',
  },
  {
    title: 'Fund your wallet',
    body: 'Send ICP to your Account ID (not Principal), refresh balance, then convert to cycles.',
    href: '/dashboard/wallet',
  },
  {
    title: 'Custom domains',
    body: 'After deploy, open Domains, pick a project, add DNS records, verify, and register with ICP.',
    href: '/dashboard/domains',
  },
  {
    title: 'Canister metrics',
    body: 'View real on-chain cycles, memory, and query stats per project under Metrics.',
    href: '/dashboard/analytics',
  },
];

export default function HelpPage() {
  return (
    <div className="bg-landing-bg min-h-screen">
      <Header />
      <main className="pt-24 px-6 md:px-12 pb-16">
        <div className="max-w-3xl mx-auto space-y-8">
          <div className="text-center">
            <h1 className="font-heading font-bold text-3xl md:text-4xl text-white mb-3">
              Help & documentation
            </h1>
            <p className="text-white/70">
              Quick guides for hosting static sites on the Internet Computer with Canistra.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            {guides.map((g) => (
              <Card key={g.title} className="bg-white/5 border-white/10 text-white">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base">{g.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-white/70">{g.body}</p>
                  <Link href={g.href} className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}>
                    Learn more
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="bg-white/5 border-white/10 text-white">
            <CardHeader>
              <CardTitle className="text-base">Need more?</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap gap-3">
              <Link href="/about" className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}>
                About Canistra
              </Link>
              <Link href="/privacy" className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}>
                Privacy
              </Link>
              <Button variant="outline" size="sm" render={<a href="https://internetcomputer.org/docs" target="_blank" rel="noopener noreferrer" />}>
                ICP official docs
              </Button>
            </CardContent>
          </Card>
        </div>
      </main>
      <Footer />
    </div>
  );
}
