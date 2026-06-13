import React, { useState, useEffect } from 'react';
import QRCode from 'qrcode';
import Image from 'next/image';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { 
  Loader2, 
  Wallet, 
  ExternalLink, 
  RefreshCw, 
  AlertCircle, 
  CheckCircle2, 
  Zap,
  Copy,
  QrCode,
  ArrowRight,
  TrendingUp
} from 'lucide-react';
import { walletApi } from '@/lib/api';
import type { FundingInstructions, WalletIdentity } from '@/types/api';
import { logger } from '@/lib/logger';

export function WalletManager() {
  const queryClient = useQueryClient();
  const [showQrCode, setShowQrCode] = useState(false);
  const [copiedAddress, setCopiedAddress] = useState(false);

  // Fetch wallet identity with enhanced funding detection
  const {
    data: identity,
    isLoading: identityLoading,
    error: identityError,
  } = useQuery({
    queryKey: ['wallet', 'identity'],
    queryFn: () => walletApi.getIdentity(),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });

  // Fetch detailed funding instructions
  const { data: fundingInstructions } = useQuery({
    queryKey: ['wallet', 'funding-instructions'],
    queryFn: () => walletApi.getFundingInstructions(),
    enabled: !!identity,
  });

  // Refresh balance mutation with enhanced detection
  const refreshBalanceMutation = useMutation({
    mutationFn: () => walletApi.refreshBalance(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });

  // Auto-convert ICP to cycles mutation
  const convertIcpMutation = useMutation({
    mutationFn: () => walletApi.convertIcpToCycles(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });

  // QR code generation
  const [qrCodeDataUrl, setQrCodeDataUrl] = useState<string>('');

  const generateQRCode = async (principalId: string) => {
    try {
      const qrDataUrl = await QRCode.toDataURL(principalId, {
        width: 256,
        margin: 2,
        color: {
          dark: '#000000',
          light: '#FFFFFF',
        },
      });
      setQrCodeDataUrl(qrDataUrl);
    } catch (error) {
      logger.error('Error generating QR code', { error, principalId }, 'WalletManager');
    }
  };

  // Generate QR code when account ID is available
  useEffect(() => {
    if (identity?.account_id) {
      queueMicrotask(() => { void generateQRCode(identity.account_id); });
    }
  }, [identity?.account_id]);

  // Recreate identity mutation
  const recreateIdentityMutation = useMutation({
    mutationFn: () => walletApi.recreateIdentity(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['wallet'] });
    },
  });

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedAddress(true);
      setTimeout(() => setCopiedAddress(false), 2000);
    } catch {
      logger.error('Failed to copy to clipboard', { text, type }, 'WalletManager');
    }
  };

  // Derive status from identity properties
  const getStatusFromIdentity = (identity: { funding_required?: boolean; auto_convert_available?: boolean } | null | undefined) => {
    if (!identity) return 'error';
    if (!identity.funding_required) return 'active';
    if (identity.auto_convert_available) return 'active';
    return 'active';
  };

  const getStatusBadgeVariant = (status: string, fundingRequired: boolean): 'default' | 'secondary' | 'destructive' | 'outline' => {
    if (status === 'active' && !fundingRequired) return 'default';
    if (status === 'active' && fundingRequired) return 'secondary';
    if (status === 'pending') return 'outline';
    return 'destructive';
  };

  const getStatusText = (status: string, fundingRequired: boolean, autoConvertAvailable: boolean) => {
    if (status === 'active' && !fundingRequired) return 'Ready';
    if (status === 'active' && autoConvertAvailable) return 'Convert Available';
    if (status === 'active' && fundingRequired) return 'Needs Funding';
    if (status === 'pending') return 'Pending';
    return 'Error';
  };

  if (identityLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
        <span className="ml-2">Loading wallet information...</span>
      </div>
    );
  }

  if (identityError) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load wallet information. Please try again or contact support.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Enhanced Wallet Status Card */}
      <Card>
        <CardHeader className="flex flex-row items-center space-y-0 pb-2">
          <div className="flex items-center space-x-3">
            <Image
              src="/images/partner/icp.png"
              alt="Internet Computer Protocol"
              width={24}
              height={24}
              className="rounded"
            />
            <Wallet className="h-5 w-5" />
            <CardTitle>ICP Wallet</CardTitle>
          </div>
           <div className="ml-auto">
             <Badge 
               variant={getStatusBadgeVariant(
                 getStatusFromIdentity(identity), 
                 identity?.funding_required || true
               )}
             >
               {getStatusText(
                 getStatusFromIdentity(identity), 
                 identity?.funding_required || true,
                 identity?.auto_convert_available || false
               )}
             </Badge>
           </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {identity && (
            <>
              {/* Account ID for funding with copy and QR */}
              <div>
                <label className="text-sm font-medium text-muted-foreground">ICP Funding Address (Account ID)</label>
                <div className="flex items-center space-x-2">
                  <div className="font-mono text-sm bg-muted/50 p-2 rounded border flex-grow">
                    {identity.account_id}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(identity.account_id, 'Account ID')}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Dialog open={showQrCode} onOpenChange={setShowQrCode}>
                    <DialogTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <QrCode className="h-4 w-4" />
                      </Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>ICP Funding Address QR Code</DialogTitle>
                        <DialogDescription>
                          Scan this QR code to get your Account ID for ICP funding
                        </DialogDescription>
                      </DialogHeader>
                       <div className="flex items-center justify-center p-6">
                          {qrCodeDataUrl ? (
                            <Image 
                              src={qrCodeDataUrl} 
                              alt={`QR code for Account ID ${identity.account_id}`}
                              width={256}
                              height={256}
                              className="border rounded-lg"
                            />
                          ) : (
                           <div className="w-64 h-64 bg-muted border-2 border-dashed border-border flex items-center justify-center">
                             <div className="text-center text-muted-foreground">
                               <QrCode className="h-12 w-12 mx-auto mb-2" />
                               <p className="text-sm">Generating QR code...</p>
                             </div>
                           </div>
                         )}
                       </div>
                    </DialogContent>
                  </Dialog>
                </div>
                {copiedAddress && (
                  <p className="text-sm text-primary mt-1">Account ID copied!</p>
                )}
              </div>

              {/* Enhanced Balance Display */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-muted-foreground">ICP Balance</label>
                  <div className="flex items-center space-x-2">
                     <span className="text-lg font-semibold">
                       {identity.formatted_icp}
                     </span>
                      {identity.auto_convert_available && (
                        <Badge variant="secondary">
                          Detected
                        </Badge>
                      )}
                  </div>
                </div>
                <div>
                   <label className="text-sm font-medium text-muted-foreground">Cycles Balance</label>
                   <div className="flex items-center space-x-2">
                     <span className="text-lg font-semibold">
                       {identity.formatted_cycles}
                     </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => refreshBalanceMutation.mutate()}
                      disabled={refreshBalanceMutation.isPending}
                    >
                      <RefreshCw className={`h-4 w-4 ${refreshBalanceMutation.isPending ? 'animate-spin' : ''}`} />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Auto-Convert Available Alert */}
               {identity.auto_convert_available && (
                 <Alert>
                   <Zap className="h-4 w-4" />
                   <AlertDescription className="flex items-center justify-between">
                     <span>
                       <strong>ICP Detected!</strong> You have {identity.formatted_icp} available to convert to cycles.
                     </span>
                    <Button
                      size="sm"
                      onClick={() => convertIcpMutation.mutate()}
                      disabled={convertIcpMutation.isPending}
                      className="ml-4"
                    >
                      {convertIcpMutation.isPending ? (
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      ) : (
                        <ArrowRight className="h-4 w-4 mr-2" />
                      )}
                      Convert Now
                    </Button>
                  </AlertDescription>
                </Alert>
              )}

              {/* Standard Funding Required Alert */}
              {identity.funding_required && !identity.auto_convert_available && (
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Your wallet needs funding to deploy projects. Minimum 0.1 ICP (~$1.00) required.
                  </AlertDescription>
                </Alert>
              )}

              {/* Status Message */}
              <div className="text-sm text-muted-foreground bg-muted/50 p-3 rounded">
                <strong>Important:</strong> Send ICP tokens to your <strong>Account ID</strong> (not Principal ID) to fund deployments.
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Enhanced Funding Instructions */}
      {identity?.funding_required && fundingInstructions && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Quick Funding Guide</span>
            </CardTitle>
            <CardDescription>
              Follow these steps to fund your wallet automatically
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {fundingInstructions.instructions.map((step) => (
               <div key={step.step} className="flex space-x-4">
                  <div className="flex-shrink-0">
                    <div className="flex items-center justify-center w-8 h-8 bg-muted text-muted-foreground dark:bg-muted dark:text-muted-foreground rounded-full text-sm font-medium">
                      {step.step}
                    </div>
                  </div>
                <div className="flex-grow">
                  <h3 className="font-semibold">{step.title}</h3>
                  <p className="text-muted-foreground text-sm">{step.description}</p>
                  
                  {/* Exchange options */}
                  {step.options && (
                    <div className="mt-2 grid grid-cols-3 gap-2">
                      {step.options.map((option) => (
                        <Button
                          key={option.name}
                          variant="outline"
                          size="sm"
                          onClick={() => window.open(option.url, '_blank')}
                        >
                          <ExternalLink className="h-4 w-4 mr-2" />
                          {option.name}
                        </Button>
                      ))}
                    </div>
                  )}

                   {/* Account ID data for funding */}
                   {identity?.account_id && (
                     <div className="mt-2">
                       <span className="text-xs text-muted-foreground">Send ICP to this Account ID:</span>
                       <div className="font-mono text-xs bg-muted p-2 rounded border border-input mt-1 flex items-center justify-between">
                         <span>{identity.account_id}</span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(identity.account_id, 'Account ID')}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                       <p className="text-xs text-muted-foreground mt-1">
                         ⚠️ Use Account ID (above), not Principal ID for ICP transfers
                       </p>
                    </div>
                  )}

                   {/* Minimum amount */}
                   {step.step === 1 && (
                     <p className="text-sm font-medium mt-1">
                       Minimum: 0.1 ICP
                     </p>
                   )}
                </div>
              </div>
            ))}

            <Separator />

            {/* Quick Actions */}
            <div>
              <h3 className="font-semibold mb-3">Quick Actions</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => window.open('https://nns.ic0.app', '_blank')}
                >
                  <ExternalLink className="h-4 w-4 mr-2" />
                  Open NNS Dapp
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => refreshBalanceMutation.mutate()}
                  disabled={refreshBalanceMutation.isPending}
                >
                  <RefreshCw className={`h-4 w-4 mr-2 ${refreshBalanceMutation.isPending ? 'animate-spin' : ''}`} />
                  Check for Deposits
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

       {/* Ready Status */}
       {identity && !identity.funding_required && (
         <Card>
           <CardContent className="pt-6">
             <div className="text-center">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">
                 Wallet Ready for Deployments!
               </h3>
               <p className="text-muted-foreground mb-4">
                 Your wallet is funded and ready. You can now deploy projects to the Internet Computer.
               </p>
                <div className="p-4 rounded-lg">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Available Cycles:</span>
                      <p className="font-semibold">{identity.formatted_cycles}</p>
                    </div>
                    <div>
                      <span className="text-muted-foreground">ICP Balance:</span>
                      <p className="font-semibold">{identity.formatted_icp}</p>
                    </div>
                  </div>
                </div>
             </div>
           </CardContent>
         </Card>
       )}

      {/* Advanced Options */}
      <Card>
        <CardHeader>
          <CardTitle>Advanced Options</CardTitle>
          <CardDescription>
            Advanced wallet management options (use with caution)
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            variant="destructive"
            onClick={() => {
              if (confirm('This will create a new identity and orphan existing canisters. Continue?')) {
                recreateIdentityMutation.mutate();
              }
            }}
            disabled={recreateIdentityMutation.isPending}
          >
            {recreateIdentityMutation.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              'Recreate Identity'
            )}
          </Button>
          
          <div className="text-xs text-muted-foreground">
            <p><strong>Warning:</strong> Recreating your identity will generate a new Principal ID and orphan any existing canisters.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
