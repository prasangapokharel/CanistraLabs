'use client';

import { useState } from 'react';
import Link from 'next/link';
import { BarChart3, ExternalLink, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { useProjects, useDeleteProject } from '@/hooks/api/useProjects';
import { handleApiError } from '@/lib/apiClient';
import { Button, buttonVariants } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { projectDeployLabel, projectIsLive, projectLiveUrl } from '@/lib/icp-url';
import { ProjectPowerToggle } from '@/components/project/ProjectPowerToggle';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

function statusLabel(project: {
  canister_id?: string | null;
  status?: string;
  url?: string | null;
  is_paused?: boolean;
}) {
  if (project.status === 'failed') return 'Failed';
  if (project.is_paused || project.status === 'paused') return 'Paused';
  if (projectIsLive(project)) return projectDeployLabel(project);
  return 'Draft';
}

function statusVariant(project: {
  canister_id?: string | null;
  status?: string;
  is_paused?: boolean;
}) {
  if (project.is_paused || project.status === 'paused') return 'secondary' as const;
  if (projectIsLive(project)) return 'default' as const;
  if (project.status === 'failed') return 'destructive' as const;
  return 'secondary' as const;
}

export default function ProjectsPage() {
  const { data: projects = [], isLoading } = useProjects();
  const deleteProject = useDeleteProject();
  const [deleteId, setDeleteId] = useState<string | null>(null);

  const handleDelete = async () => {
    if (!deleteId) return;
    try {
      await deleteProject.mutateAsync(deleteId);
      toast.success('Project deleted');
      setDeleteId(null);
    } catch (err) {
      toast.error(handleApiError(err));
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Projects</h1>
          <p className="text-sm text-muted-foreground">Open a project to edit and publish</p>
        </div>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : projects.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-sm text-muted-foreground mb-4">No projects yet</p>
            <Link href="/dashboard/projects/new" className={cn(buttonVariants())}>
              Create project
            </Link>
          </CardContent>
        </Card>
      ) : (
        <ul className="space-y-2">
          {projects.map((project) => {
            const liveUrl = projectLiveUrl(project);
            const isPaused = project.is_paused || project.status === 'paused';
            const isOn = Boolean(project.canister_id) && !isPaused;
            return (
              <li key={project.id}>
                <Card>
                  <CardContent className="py-4 flex items-center justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <Link
                        href={`/dashboard/projects/${project.id}`}
                        className="font-medium hover:underline block truncate"
                      >
                        {project.name}
                      </Link>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {project.created_at
                          ? new Date(project.created_at).toLocaleDateString()
                          : '—'}
                        {project.canister_id && (
                          <span className="ml-2 font-mono">{project.canister_id.slice(0, 12)}…</span>
                        )}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0 flex-wrap justify-end">
                      {project.canister_id && (
                        <ProjectPowerToggle
                          projectId={project.id}
                          canisterId={project.canister_id}
                          enabled={isOn}
                        />
                      )}
                      <Badge variant={statusVariant(project)}>{statusLabel(project)}</Badge>
                      <Link
                        href={`/dashboard/projects/${project.id}/metrics`}
                        className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                      >
                        <BarChart3 className="h-4 w-4" />
                        Metrics
                      </Link>
                      {liveUrl ? (
                        <a
                          href={liveUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
                        >
                          <ExternalLink className="h-4 w-4" />
                          Visit
                        </a>
                      ) : (
                        <span className="text-xs text-muted-foreground hidden sm:inline">
                          Not deployed
                        </span>
                      )}
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive"
                        onClick={() => setDeleteId(String(project.id))}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </li>
            );
          })}
        </ul>
      )}

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete project?</AlertDialogTitle>
            <AlertDialogDescription>
              This removes the project and its canister from ICP. This cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleteProject.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteProject.isPending ? 'Deleting…' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
