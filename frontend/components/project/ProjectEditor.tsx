'use client';

import { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  FileCode,
  FilePlus,
  FolderOpen,
  Save,
  Upload,
  ExternalLink,
  Trash2,
  Rocket,
} from 'lucide-react';
import { Button, buttonVariants } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ProjectCodeEditor } from '@/components/project/ProjectCodeEditor';
import { ProjectDeployPanel } from '@/components/project/ProjectDeployPanel';
import DomainManager from '@/components/dashboard/DomainManager';
import {
  listFileNames,
  parseProjectFiles,
  serializeProjectFiles,
} from '@/lib/project-files';
import { deployApi, projectsApi, walletApi } from '@/lib/api';
import { useDeployments } from '@/hooks/api/useDeployments';
import { handleApiError } from '@/lib/apiClient';
import { formatDeployError } from '@/lib/fundingErrors';
import type { Project } from '@/types/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import {
  deploySucceeded,
  isLocalCanisterId,
  isLocalCanisterUrl,
  projectDeployLabel,
  projectIsLive,
  projectLiveUrl,
} from '@/lib/icp-url';
import { DeployStatusAlert } from '@/components/project/DeployStatusAlert';
import {
  deployingAlert,
  failedAlert,
  fundingAlertFromResult,
  type DeployAlert,
} from '@/lib/deploy-status';
import type { DeployResult } from '@/types/api';

interface ProjectEditorProps {
  project: Project;
}

export function ProjectEditor({ project }: ProjectEditorProps) {
  const queryClient = useQueryClient();
  const [files, setFiles] = useState<Record<string, string>>({});
  const [activeFile, setActiveFile] = useState('index.html');
  const [newFileName, setNewFileName] = useState('');
  const [deployAlert, setDeployAlert] = useState<DeployAlert | null>(null);
  const [dirty, setDirty] = useState(false);
  const [pollingDeploymentId, setPollingDeploymentId] = useState<number | null>(null);

  const { refetch: refetchDeployments } = useDeployments(String(project.id));

  const { data: polledDeployment } = useQuery({
    queryKey: ['deployments', String(project.id), pollingDeploymentId],
    queryFn: () =>
      deployApi.getDeploymentStatus(Number(project.id), pollingDeploymentId as number),
    enabled: pollingDeploymentId != null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (!status) return 2000;
      if (['success', 'failed', 'pending_funding', 'deployed', 'updated'].includes(status))
        return false;
      return 2000;
    },
  });

  // Stop polling after 5 minutes (e.g. Celery worker offline)
  useEffect(() => {
    if (pollingDeploymentId == null) return;
    const timer = window.setTimeout(() => {
      setPollingDeploymentId(null);
      setDeployAlert(
        failedAlert(
          'Deploy timed out. Convert ICP to cycles or ensure the backend worker is running, then try again.'
        )
      );
      toast.error('Deploy timed out', {
        description: 'The deployment did not finish in time.',
      });
    }, 5 * 60 * 1000);
    return () => window.clearTimeout(timer);
  }, [pollingDeploymentId]);

  const { data: wallet } = useQuery({
    queryKey: ['wallet', 'identity'],
    queryFn: () => walletApi.getIdentity(),
    staleTime: 30_000,
  });

  const deployNetwork = wallet?.deploy_network ?? 'local';
  const isLocalDeploy = deployNetwork === 'local';
  const isLocalCanister = Boolean(project.canister_id && isLocalCanisterId(project.canister_id));
  const deployReady = wallet?.deploy_ready ?? isLocalDeploy;
  const needsFunding = !project.canister_id && !deployReady && !isLocalDeploy;

  const fundingMessage =
    wallet?.message ??
    (wallet?.requirements?.formatted_cycles_shortfall
      ? `Need ${wallet.requirements.formatted_cycles_shortfall} more cycles for mainnet deploy.`
      : 'Fund wallet and convert ICP to cycles before deploying.');

  useEffect(() => {
    setFiles(parseProjectFiles(project.code_content ?? null));
    setDirty(false);
  }, [project.code_content, project.id]);

  useEffect(() => {
    if (pollingDeploymentId == null || !polledDeployment) return;
    const status = polledDeployment.status;

    if (status === 'pending_funding') {
      setPollingDeploymentId(null);
      const alert = fundingAlertFromResult({
        status: 'pending_funding',
        funding_required: true,
        message: polledDeployment.message,
      } as DeployResult);
      setDeployAlert(alert);
      toast.warning(alert.title, { description: alert.message });
      void refetchDeployments();
      return;
    }

    if (status === 'failed') {
      setPollingDeploymentId(null);
      const alert = failedAlert(polledDeployment.message ?? 'Deploy failed');
      setDeployAlert(alert);
      toast.error(alert.title, { description: alert.message });
      void refetchDeployments();
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      return;
    }

    if (status === 'success' || status === 'deployed') {
      setPollingDeploymentId(null);
      setDeployAlert(null);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', String(project.id)] });
      queryClient.invalidateQueries({ queryKey: ['project-metrics', String(project.id)] });
      queryClient.invalidateQueries({ queryKey: ['wallet', 'identity'] });
      void refetchDeployments();
      const url = polledDeployment.url;
      toast.success(isLocalCanisterUrl(url) ? 'Published' : 'Live on ICP', {
        action: url
          ? { label: 'Visit site', onClick: () => window.open(url, '_blank', 'noopener,noreferrer') }
          : undefined,
      });
    }
  }, [polledDeployment, pollingDeploymentId, project.id, queryClient, refetchDeployments]);

  const saveOnlyMutation = useMutation({
    mutationFn: async () => {
      const serialized = serializeProjectFiles(files);
      return projectsApi.update(Number(project.id), { code_content: serialized });
    },
    onSuccess: () => {
      setDirty(false);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', String(project.id)] });
      toast.success('Project saved');
    },
    onError: (err) => toast.error(handleApiError(err)),
  });

  const publishMutation = useMutation({
    mutationFn: async () => {
      const serialized = serializeProjectFiles(files);
      await projectsApi.update(Number(project.id), { code_content: serialized });
      toast.success('Project saved');

      const fresh = await projectsApi.getById(Number(project.id));
      const canisterId = fresh.canister_id ?? project.canister_id;

      setDeployAlert(deployingAlert('Deploying to ICP…'));

      if (canisterId) {
        return deployApi.updateCanister(Number(project.id), { code_content: serialized });
      }
      return deployApi.deploy(Number(project.id), { code_content: serialized });
    },
    onSuccess: (result: DeployResult) => {
      setDirty(false);
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      queryClient.invalidateQueries({ queryKey: ['projects', String(project.id)] });
      queryClient.invalidateQueries({ queryKey: ['wallet', 'identity'] });

      if (result.async || result.status === 'queued') {
        setPollingDeploymentId(result.deployment_id);
        setDeployAlert(deployingAlert('Deploy queued — processing in background…'));
        toast.message('Deploy started', { description: 'This may take a minute.' });
        void refetchDeployments();
        return;
      }

      if (result.funding_required || result.status === 'pending_funding') {
        const alert = fundingAlertFromResult(result);
        setDeployAlert(alert);
        toast.warning(alert.title, { description: alert.message });
        void refetchDeployments();
        return;
      }

      if (deploySucceeded(result)) {
        setDeployAlert(null);
        void refetchDeployments();
        queryClient.invalidateQueries({ queryKey: ['project-metrics', String(project.id)] });
        const url =
          result.url ??
          (result.canister_id
            ? projectLiveUrl({ canister_id: result.canister_id, url: result.url })
            : null);
        const local = isLocalCanisterUrl(url);
        toast.success(local ? 'Published' : 'Live on ICP', {
          description: 'Project saved and deployed.',
          action: url
            ? {
                label: 'Visit site',
                onClick: () => window.open(url, '_blank', 'noopener,noreferrer'),
              }
            : undefined,
        });
        return;
      }

      if (result.status === 'updated') {
        setDeployAlert(null);
        toast.success('Published', {
          description: 'Project saved and canister updated.',
        });
        void refetchDeployments();
        return;
      }

      if (result.status === 'failed') {
        const alert = failedAlert(result.message ?? 'Deploy failed');
        setDeployAlert(alert);
        toast.error(alert.title, { description: alert.message });
        return;
      }

      const alert = failedAlert(
        result.message ?? `Unexpected deploy status: ${result.status ?? 'unknown'}`
      );
      setDeployAlert(alert);
      toast.error(alert.title, { description: alert.message });
    },
    onError: (err) => {
      const msg = formatDeployError(err);
      const alert = failedAlert(msg);
      setDeployAlert(alert);
      toast.error(alert.title, { description: alert.message });
    },
  });

  const updateFile = useCallback((name: string, content: string) => {
    setFiles((prev) => ({ ...prev, [name]: content }));
    setDirty(true);
  }, []);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 's') {
        e.preventDefault();
        if (publishMutation.isPending || saveOnlyMutation.isPending) return;
        saveOnlyMutation.mutate();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [publishMutation.isPending, saveOnlyMutation]);

  const addFile = () => {
    const name = newFileName.trim();
    if (!name || files[name]) return;
    setFiles((prev) => ({ ...prev, [name]: '' }));
    setActiveFile(name);
    setNewFileName('');
    setDirty(true);
  };

  const removeFile = (name: string) => {
    if (name === 'index.html') return;
    setFiles((prev) => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
    if (activeFile === name) setActiveFile('index.html');
    setDirty(true);
  };

  const onUploadFolder = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList?.length) return;
    const next: Record<string, string> = { ...files };
    for (const file of Array.from(fileList)) {
      const path = file.webkitRelativePath
        ? file.webkitRelativePath.split('/').slice(1).join('/') || file.name
        : file.name;
      if (/\.(html|css|js|json|txt|svg|ico|webp|png|jpg|jpeg|gif|woff2?|ttf)$/i.test(path)) {
        next[path] = await file.text();
      }
    }
    setFiles(next);
    if (next['index.html']) setActiveFile('index.html');
    setDirty(true);
    toast.success('Files loaded');
    e.target.value = '';
  };

  const fileNames = listFileNames(files);
  const isLive = projectIsLive(project);
  const liveUrl = projectLiveUrl(project);
  const deployLabel = projectDeployLabel(project);
  const isBusy =
    saveOnlyMutation.isPending ||
    publishMutation.isPending ||
    pollingDeploymentId != null;

  // One banner max: errors/funding only (live state is in the badge + Visit button)
  const showDraftHint =
    !isLive && !deployAlert && !project.canister_id && !needsFunding;
  const showWalletHint = needsFunding && !deployAlert;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3">
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-3">
        <div className="min-w-0 flex flex-wrap items-center gap-2">
          <h1 className="truncate text-lg font-semibold">{project.name}</h1>
          <Badge
            variant={
              isLive ? 'default' : project.status === 'failed' ? 'destructive' : 'secondary'
            }
          >
            {project.status === 'failed' ? 'Failed' : deployLabel}
          </Badge>
          {dirty && (
            <Badge variant="outline" className="text-xs">
              Unsaved
            </Badge>
          )}
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {liveUrl && (
            <a
              href={liveUrl}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(buttonVariants({ variant: 'outline', size: 'sm' }))}
              title={liveUrl}
            >
              <ExternalLink className="h-4 w-4" />
              Visit site
            </a>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={() => saveOnlyMutation.mutate()}
            disabled={isBusy}
          >
            <Save className="h-4 w-4" />
            Save
          </Button>
          <Button size="sm" onClick={() => publishMutation.mutate()} disabled={isBusy}>
            <Rocket className="h-4 w-4" />
            {isBusy ? 'Publishing…' : isLive ? 'Publish' : needsFunding ? 'Deploy (needs cycles)' : 'Deploy'}
          </Button>
        </div>
      </div>

      <ProjectDeployPanel projectId={String(project.id)} canisterId={project.canister_id} />

      {project.canister_id && (
        <div className="shrink-0 max-h-[40vh] overflow-y-auto rounded-lg border p-3">
          <DomainManager projectId={Number(project.id)} />
        </div>
      )}

      {isLocalCanister && !isLocalDeploy && (
        <Alert className="shrink-0 border-amber-500/50 bg-amber-500/5">
          <AlertDescription className="text-sm">
            This project uses a <strong>local dev canister</strong> (not IC mainnet). Publishing
            updates it on your machine — the backend auto-starts <code className="text-xs">dfx</code>.
            For mainnet, delete this project and deploy again after funding cycles.
          </AlertDescription>
        </Alert>
      )}

      {deployAlert && <DeployStatusAlert alert={deployAlert} className="shrink-0" />}

      {showWalletHint && (
        <DeployStatusAlert
          className="shrink-0"
          alert={{
            kind: 'funding',
            title: 'Insufficient cycles for mainnet deploy',
            message: fundingMessage,
          }}
        />
      )}

      {showDraftHint && (
        <Alert className="shrink-0">
          <AlertDescription className="text-sm">
            {isLocalDeploy ? (
              <>
                Click <strong>Deploy</strong> to publish on your local dfx replica (backend
                auto-starts <code className="text-xs">dfx start</code>).
              </>
            ) : (
              <>
                Fund your{' '}
                <Link href="/dashboard/wallet" className="underline">
                  wallet
                </Link>{' '}
                then click <strong>Deploy</strong>.
              </>
            )}
          </AlertDescription>
        </Alert>
      )}

      <div className="flex min-h-0 flex-1 overflow-hidden rounded-lg border bg-card">
        <aside className="flex w-52 shrink-0 flex-col border-r bg-muted/20 md:w-56">
          <div className="shrink-0 border-b p-3">
            <p className="mb-2 flex items-center gap-1 text-xs font-medium text-muted-foreground">
              <FolderOpen className="h-3.5 w-3.5" />
              Files
            </p>
            <label className="block">
              <input
                type="file"
                multiple
                // @ts-expect-error webkitdirectory is non-standard but widely supported
                webkitdirectory=""
                className="hidden"
                onChange={onUploadFolder}
              />
              <Button variant="outline" size="sm" className="w-full" type="button" render={<span />}>
                <Upload className="h-3.5 w-3.5" />
                Upload folder
              </Button>
            </label>
          </div>

          <ul className="min-h-0 flex-1 space-y-0.5 overflow-y-auto p-2">
            {fileNames.map((name) => (
              <li key={name} className="group flex items-center gap-0.5">
                <button
                  type="button"
                  onClick={() => setActiveFile(name)}
                  className={cn(
                    'flex min-w-0 flex-1 items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm',
                    activeFile === name ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
                  )}
                >
                  <FileCode className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate">{name}</span>
                </button>
                {name !== 'index.html' && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 shrink-0 opacity-60 hover:opacity-100"
                    onClick={() => removeFile(name)}
                    aria-label={`Delete ${name}`}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                )}
              </li>
            ))}
          </ul>

          <div className="flex shrink-0 gap-1 border-t p-2">
            <Input
              placeholder="new-file.css"
              value={newFileName}
              onChange={(e) => setNewFileName(e.target.value)}
              className="h-8 text-xs"
              onKeyDown={(e) => e.key === 'Enter' && addFile()}
            />
            <Button variant="outline" size="icon" className="h-8 w-8 shrink-0" onClick={addFile}>
              <FilePlus className="h-4 w-4" />
            </Button>
          </div>
        </aside>

        <div className="flex min-h-0 min-w-0 flex-1 flex-col">
          <div className="flex shrink-0 items-center justify-between border-b px-3 py-2 font-mono text-xs text-muted-foreground">
            <span>{activeFile}</span>
            <span className="hidden sm:inline">Ctrl+S to save</span>
          </div>
          <div className="relative min-h-0 flex-1">
            <ProjectCodeEditor
              key={activeFile}
              filename={activeFile}
              value={files[activeFile] ?? ''}
              onChange={(value) => updateFile(activeFile, value)}
            />
          </div>
        </div>
      </div>
    </div>
  );
}
