'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { Globe, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { domainsApi } from '@/lib/api';
import { useProjects } from '@/hooks/api/useProjects';
import { projectIsLive } from '@/lib/icp-url';
import DomainManager from '@/components/dashboard/DomainManager';

export function UserDomainsView() {
  const { data: projects = [], isLoading: projectsLoading } = useProjects();
  const deployed = projects.filter((p) => projectIsLive(p));

  const [selectedProjectId, setSelectedProjectId] = useState<string>('');

  const { data: domains = [], isLoading: domainsLoading } = useQuery({
    queryKey: ['user-domains'],
    queryFn: () => domainsApi.getAll(),
    staleTime: 30_000,
  });

  const activeProjectId = selectedProjectId || String(deployed[0]?.id ?? '');
  const activeProject = deployed.find((p) => String(p.id) === activeProjectId);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Custom domains</h1>
        <p className="text-sm text-muted-foreground">
          Point your own domain at an ICP canister via boundary-node registration.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Your domains</CardTitle>
        </CardHeader>
        <CardContent>
          {domainsLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : domains.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No custom domains yet. Select a deployed project below to add one.
            </p>
          ) : (
            <ul className="space-y-2">
              {domains.map((d) => (
                <li
                  key={d.domain_id}
                  className="flex items-center justify-between gap-3 rounded-md border px-3 py-2"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <Globe className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="font-medium truncate">{d.domain}</span>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <Badge variant={d.ssl_active ? 'default' : 'secondary'}>{d.status}</Badge>
                    {d.custom_url && (
                      <a
                        href={d.custom_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-base">Add domain to project</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {projectsLoading ? (
            <p className="text-sm text-muted-foreground">Loading projects…</p>
          ) : deployed.length === 0 ? (
            <Alert>
              <AlertDescription>
                Deploy a project first.{' '}
                <Link href="/dashboard/projects" className="underline">
                  Go to projects
                </Link>
              </AlertDescription>
            </Alert>
          ) : (
            <>
              <Select
                value={activeProjectId}
                onValueChange={(v) => setSelectedProjectId(v ?? '')}
              >
                <SelectTrigger className="w-full max-w-sm">
                  <SelectValue placeholder="Select project" />
                </SelectTrigger>
                <SelectContent>
                  {deployed.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      {p.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {activeProject && (
                <DomainManager projectId={Number(activeProject.id)} />
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
