'use client';

import { useState } from 'react';
import { useDeployProject, useCanisterStatus } from '@/hooks/api/useDeployments';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import {
  Rocket,
  CheckCircle,
  AlertCircle,
  ExternalLink,
  Copy,
  RefreshCw,
  Loader2,
} from 'lucide-react';
import { handleApiError } from '@/lib/apiClient';
import { Project } from '@/types/api';

interface DeploymentStatusProps {
  project: Project;
  onDeploymentComplete?: () => void;
}

export function DeploymentStatus({ project, onDeploymentComplete }: DeploymentStatusProps) {
  const [deploymentProgress, setDeploymentProgress] = useState(0);
  const [deploymentStage, setDeploymentStage] = useState('');
  const [deploymentUrl, setDeploymentUrl] = useState<string | null>(null);
  const [canisterId, setCanisterId] = useState<string | null>(null);
  
  const deployProjectMutation = useDeployProject();
  const { data: canisterStatus } = useCanisterStatus(
    canisterId || ''
  );

  const isDeploying = deployProjectMutation.isPending || project.status === 'deploying';
  const isDeployed = project.status === 'deployed';

  const handleDeploy = async () => {
    try {
      setDeploymentProgress(10);
      setDeploymentStage('Initializing deployment...');
      
      const result = await deployProjectMutation.mutateAsync(String(project.id));
      
      setDeploymentProgress(30);
      setDeploymentStage('Processing project files...');
      
      // Simulate realistic deployment progress
      setTimeout(() => {
        setDeploymentProgress(50);
        setDeploymentStage('Creating canister...');
      }, 1000);
      
      setTimeout(() => {
        setDeploymentProgress(70);
        setDeploymentStage('Uploading to Internet Computer...');
      }, 2000);
      
      setTimeout(() => {
        setDeploymentProgress(85);
        setDeploymentStage('Configuring canister...');
      }, 3500);
      
      setTimeout(() => {
        setDeploymentProgress(100);
        setDeploymentStage('Deployment complete!');
        
        // If the deployment was successful, set the URL
        if (result && typeof result === 'object' && 'project_id' in result) {
          setCanisterId(project.canister_id || `canister-${project.id}`);
          setDeploymentUrl(project.url || `https://${project.id}.icp0.io`);
        }
        
        onDeploymentComplete?.();
      }, 5000);
      
    } catch (error) {
      console.error('Deploy failed:', handleApiError(error));
      setDeploymentProgress(0);
      setDeploymentStage('Deployment failed');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const getStatusIcon = () => {
    if (isDeploying) {
      return <Loader2 className="h-4 w-4 animate-spin" />;
    }
    if (isDeployed) {
      return <CheckCircle className="h-4 w-4 text-green-600" />;
    }
    if (deployProjectMutation.error) {
      return <AlertCircle className="h-4 w-4 text-red-600" />;
    }
    return <Rocket className="h-4 w-4" />;
  };

  const getStatusText = () => {
    if (isDeploying && deploymentStage) {
      return deploymentStage;
    }
    if (isDeploying) {
      return 'Deploying...';
    }
    if (isDeployed) {
      return 'Deployed successfully';
    }
    if (deployProjectMutation.error) {
      return 'Deployment failed';
    }
    return 'Ready to deploy';
  };

  const getStatusColor = () => {
    if (isDeploying) {
      return 'bg-blue-100 text-blue-800 border-blue-200';
    }
    if (isDeployed) {
      return 'bg-green-100 text-green-800 border-green-200';
    }
    if (deployProjectMutation.error) {
      return 'bg-red-100 text-red-800 border-red-200';
    }
    return 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          {getStatusIcon()}
          Deployment Status
        </CardTitle>
        <CardDescription>
          Deploy your project to the Internet Computer
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center gap-2">
          <Badge className={getStatusColor()}>
            {getStatusText()}
          </Badge>
        </div>

        {isDeploying && (
          <div className="space-y-2">
            <Progress value={deploymentProgress} className="h-2" />
            <p className="text-sm text-muted-foreground">
              {deploymentProgress}% complete
            </p>
          </div>
        )}

        {deployProjectMutation.error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-800">
              {handleApiError(deployProjectMutation.error)}
            </p>
          </div>
        )}

        {(project.url || deploymentUrl) && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Live URL:</p>
            <div className="flex items-center gap-2 p-2 border rounded-lg bg-muted">
              <span className="text-sm font-mono flex-1 truncate">
                {project.url || deploymentUrl}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(project.url || deploymentUrl!)}
              >
                <Copy className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                asChild
              >
                <a
                  href={project.url || deploymentUrl || ''}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  <ExternalLink className="h-3 w-3" />
                </a>
              </Button>
            </div>
          </div>
        )}

        {project.canister_id && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Canister ID:</p>
            <div className="flex items-center gap-2 p-2 border rounded-lg bg-muted">
              <span className="text-sm font-mono flex-1">
                {project.canister_id}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => copyToClipboard(project.canister_id!)}
              >
                <Copy className="h-3 w-3" />
              </Button>
            </div>
          </div>
        )}

        {canisterStatus && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Canister Status:</p>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Status:</span>
                <span className="ml-1 font-medium">{canisterStatus.status}</span>
              </div>
              {canisterStatus.cycles_balance && (
                <div>
                  <span className="text-muted-foreground">Cycles:</span>
                  <span className="ml-1 font-medium">{canisterStatus.cycles_balance}</span>
                </div>
              )}
            </div>
          </div>
        )}

        <div className="flex gap-2">
          {!isDeployed && !isDeploying && (
            <Button
              onClick={handleDeploy}
              disabled={deployProjectMutation.isPending}
              className="flex-1"
            >
              {deployProjectMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Rocket className="mr-2 h-4 w-4" />
              )}
              Deploy to IC
            </Button>
          )}
          
          {isDeployed && (
            <Button
              onClick={handleDeploy}
              variant="outline"
              disabled={deployProjectMutation.isPending}
            >
              {deployProjectMutation.isPending ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="mr-2 h-4 w-4" />
              )}
              Redeploy
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}