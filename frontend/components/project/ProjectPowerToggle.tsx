'use client';

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { deployApi } from '@/lib/api';
import { formatDeployError } from '@/lib/fundingErrors';
import { toast } from 'sonner';

interface ProjectPowerToggleProps {
  projectId: string | number;
  canisterId?: string | null;
  enabled: boolean;
  disabled?: boolean;
}

export function ProjectPowerToggle({
  projectId,
  canisterId,
  enabled,
  disabled,
}: ProjectPowerToggleProps) {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (next: boolean) => deployApi.setCanisterPower(Number(projectId), next),
    onSuccess: (_data, next) => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      toast.success(next ? 'Canister started' : 'Canister stopped', {
        description: next ? 'Site is live again.' : 'Site offline — lower idle compute use.',
      });
    },
    onError: (err) => toast.error(formatDeployError(err)),
  });

  if (!canisterId) return null;

  return (
    <div className="flex items-center gap-2">
      <Switch
        id={`power-${projectId}`}
        checked={enabled}
        disabled={disabled || mutation.isPending}
        onCheckedChange={(checked) => mutation.mutate(checked)}
      />
      <Label htmlFor={`power-${projectId}`} className="text-xs text-muted-foreground cursor-pointer">
        {mutation.isPending ? '…' : enabled ? 'On' : 'Off'}
      </Label>
    </div>
  );
}
