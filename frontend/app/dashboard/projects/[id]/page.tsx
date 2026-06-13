'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ProjectEditor } from '@/components/project/ProjectEditor';
import { useProject } from '@/hooks/api/useProjects';
import { handleApiError } from '@/lib/apiClient';

export default function ProjectPage() {
  const params = useParams();
  const projectId = params?.id as string;
  const { data: project, isLoading, error } = useProject(projectId);

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading project…</p>;
  }

  if (error || !project) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error ? handleApiError(error) : 'Project not found'}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <Button
        variant="ghost"
        size="sm"
        className="w-fit shrink-0"
        render={<Link href="/dashboard/projects" />}
      >
        <ArrowLeft className="h-4 w-4" />
        All projects
      </Button>
      <ProjectEditor project={project} />
    </div>
  );
}
