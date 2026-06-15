'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { domainsApi, type DomainRecord } from '@/lib/api';
import { 
  Globe, 
  ExternalLink, 
  Copy, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertCircle,
  Shield,
  Server,
  Settings
} from 'lucide-react';

interface DNSRecord {
  type: string;
  host: string;
  value: string;
  description: string;
}

interface DomainSetupData {
  domain_id: number;
  domain: string;
  canister_id: string;
  dns_config: {
    records: DNSRecord[];
    alternative_records: DNSRecord[];
  };
  ic_domains_content: string;
}

export default function DomainManager({ projectId }: { projectId: number }) {
  const [setupLoading, setSetupLoading] = useState(false);
  const [newDomain, setNewDomain] = useState('');
  const [newSubdomain, setNewSubdomain] = useState('');
  const [setupData, setSetupData] = useState<DomainSetupData | null>(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const { data: domains = [], isLoading, refetch } = useQuery({
    queryKey: ['project-domains', projectId],
    queryFn: async () => {
      const data = await domainsApi.getForProject(projectId);

      if (!data.success) {
        throw new Error('Failed to load domains');
      }

      return data.domains ?? [];
    },
  });

  const setupCustomDomain = async () => {
    if (!newDomain.trim()) {
      setError('Please enter a domain name');
      return;
    }

    try {
      setSetupLoading(true);
      setError('');
      
      const result = await domainsApi.setup(
        projectId,
        newDomain.trim(),
        newSubdomain.trim() || undefined
      );

      if (result.success) {
        setSetupData(result.data as DomainSetupData);
        setSuccess(`Domain ${(result.data as DomainSetupData).domain} setup initiated successfully!`);
        setNewDomain('');
        setNewSubdomain('');
        void refetch();
      } else {
        setError('Failed to setup domain');
      }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (_) {
      setError('Failed to setup domain');
    } finally {
      setSetupLoading(false);
    }
  };

  const verifyDNS = async (domainId: number) => {
    try {
      const result = await domainsApi.verify(domainId);

      if (result.success) {
        setSuccess('DNS verification completed!');
        void refetch();
      } else {
        setError('DNS verification failed');
      }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (_) {
      setError('Failed to verify DNS');
    }
  };

  const registerDomain = async (domainId: number) => {
    try {
      const result = await domainsApi.register(domainId);

      if (result.success) {
        setSuccess('Domain registration submitted to ICP boundary nodes!');
        void refetch();
      } else {
        setError('Domain registration failed');
      }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (_) {
      setError('Failed to register domain');
    }
  };

  const checkRegistrationStatus = async (domainId: number) => {
    try {
      const result = await domainsApi.checkRegistration(domainId);

      if (result.success) {
        setSuccess('Registration status updated!');
        void refetch();
      } else {
        setError('Failed to check registration status');
      }
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (_) {
      setError('Failed to check registration status');
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setSuccess('Copied to clipboard!');
  };

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const getStatusBadge = (status: string, _sslActive?: boolean) => {
    switch (status) {
      case 'active':
        return <Badge variant="outline" className="border-green-200 bg-green-50 text-green-800 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400"><CheckCircle className="w-3 h-3 mr-1" />Active</Badge>;
      case 'dns_configured':
        return <Badge variant="outline" className="border-blue-200 bg-blue-50 text-blue-800 dark:bg-blue-900/20 dark:border-blue-800 dark:text-blue-400"><Server className="w-3 h-3 mr-1" />DNS Ready</Badge>;
      case 'registering':
        return <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-800 dark:bg-amber-900/20 dark:border-amber-800 dark:text-amber-400"><Clock className="w-3 h-3 mr-1" />Registering</Badge>;
      case 'pending':
        return <Badge variant="outline" className="border-muted text-muted-foreground"><AlertCircle className="w-3 h-3 mr-1" />Pending</Badge>;
      case 'failed':
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Failed</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Custom Domains</h2>
          <p className="text-muted-foreground">Connect your custom domain to your ICP canister</p>
        </div>
      </div>

      {/* Alerts */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

       {success && (
         <Alert className="border-green-200 bg-green-50 dark:bg-green-950/20 dark:border-green-900">
           <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />
           <AlertDescription className="text-green-800 dark:text-green-300">{success}</AlertDescription>
         </Alert>
       )}

      {/* Add New Domain */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Globe className="w-5 h-5 mr-2" />
            Add Custom Domain
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Subdomain (optional)</label>
              <Input
                placeholder="www, app, api"
                value={newSubdomain}
                onChange={(e) => setNewSubdomain(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Domain Name</label>
              <Input
                placeholder="yourdomain.com"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button 
                onClick={setupCustomDomain}
                disabled={setupLoading || !newDomain.trim()}
                className="w-full"
              >
                {setupLoading ? 'Setting up...' : 'Setup Domain'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* DNS Setup Instructions */}
      {setupData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="w-5 h-5 mr-2" />
              DNS Configuration for {setupData.domain}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="dns" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="dns">DNS Records</TabsTrigger>
                <TabsTrigger value="file">Canister File</TabsTrigger>
              </TabsList>
              
              <TabsContent value="dns" className="space-y-4">
                <Alert>
                  <Server className="h-4 w-4" />
                  <AlertDescription>
                    Add these DNS records at your domain registrar (Namecheap, GoDaddy, Cloudflare, etc.)
                  </AlertDescription>
                </Alert>
                
                <div className="space-y-3">
                  {setupData.dns_config.records.map((record, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-gray-50">
                      <div className="grid grid-cols-1 md:grid-cols-4 gap-2 items-center">
                        <div>
                          <strong>Type:</strong> {record.type}
                        </div>
                         <div className="md:col-span-2">
                           <div><strong>Host/Name:</strong></div>
                           <div className="flex items-center space-x-2">
                             <code className="bg-muted px-2 py-1 rounded text-sm font-mono">{record.host}</code>
                             <Button
                               size="sm"
                               variant="outline"
                               onClick={() => copyToClipboard(record.host)}
                             >
                               <Copy className="w-3 h-3" />
                             </Button>
                           </div>
                         </div>
                         <div>
                           <div><strong>Value/Target:</strong></div>
                           <div className="flex items-center space-x-2">
                             <code className="bg-muted px-2 py-1 rounded text-sm font-mono">{record.value}</code>
                             <Button
                               size="sm"
                               variant="outline"
                               onClick={() => copyToClipboard(record.value)}
                             >
                               <Copy className="w-3 h-3" />
                             </Button>
                           </div>
                         </div>
                       </div>
                       <p className="text-sm text-muted-foreground mt-2">{record.description}</p>
                    </div>
                  ))}
                </div>
              </TabsContent>
              
              <TabsContent value="file" className="space-y-4">
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>
                    Add this file to your project and redeploy to enable custom domain support
                  </AlertDescription>
                </Alert>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      File: <code>.well-known/ic-domains</code>
                    </label>
                    <div className="bg-gray-100 p-3 rounded border">
                      <div className="flex items-center justify-between">
                        <code className="text-sm">{setupData.ic_domains_content}</code>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => copyToClipboard(setupData.ic_domains_content)}
                        >
                          <Copy className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-2">
                      File: <code>.ic-assets.json5</code>
                    </label>
                    <div className="bg-gray-100 p-3 rounded border">
                      <pre className="text-sm whitespace-pre-wrap">
{`[
  {
    "match": ".well-known",
    "ignore": false
  }
]`}
                      </pre>
                      <Button
                        size="sm"
                        variant="outline"
                        className="mt-2"
                        onClick={() => copyToClipboard(`[{"match": ".well-known","ignore": false}]`)}
                      >
                        <Copy className="w-3 h-3 mr-1" />
                        Copy Config
                      </Button>
                    </div>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Existing Domains */}
      <Card>
        <CardHeader>
          <CardTitle>Your Custom Domains</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading domains...</p>
            </div>
          ) : domains.length === 0 ? (
            <div className="text-center py-8">
              <Globe className="w-12 h-12 mx-auto text-gray-400 mb-4" />
              <p className="text-gray-600">No custom domains configured yet</p>
            </div>
          ) : (
            <div className="space-y-4">
              {domains.map((domain) => (
                <div key={domain.domain_id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-3">
                      <h3 className="font-medium text-lg">{domain.domain}</h3>
                      {getStatusBadge(domain.status, domain.ssl_active)}
                       {domain.ssl_active && (
                         <Badge className="bg-green-100 text-green-800 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800">
                           <Shield className="w-3 h-3 mr-1" />
                           SSL Active
                         </Badge>
                       )}
                    </div>
                    
                    <div className="flex space-x-2">
                      {domain.status === 'pending' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => verifyDNS(domain.domain_id)}
                        >
                          Verify DNS
                        </Button>
                      )}
                      
                      {domain.status === 'dns_configured' && (
                        <Button
                          size="sm"
                          onClick={() => registerDomain(domain.domain_id)}
                        >
                          Register with ICP
                        </Button>
                      )}
                      
                      {domain.status === 'registering' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => checkRegistrationStatus(domain.domain_id)}
                        >
                          Check Status
                        </Button>
                      )}
                      
                      {domain.custom_url && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => window.open(domain.custom_url, '_blank')}
                        >
                          <ExternalLink className="w-3 h-3 mr-1" />
                          Visit
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <div className="text-sm text-gray-600 space-y-1">
                    <div className="flex items-center justify-between">
                      <span>Canister URL:</span>
                      <div className="flex items-center space-x-2">
                        <code className="bg-gray-100 px-2 py-1 rounded text-xs">{domain.canister_url ?? domain.canister_id ?? '—'}</code>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => copyToClipboard(domain.canister_url ?? domain.canister_id ?? '')}
                        >
                          <Copy className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                    
                    {domain.custom_url && (
                      <div className="flex items-center justify-between">
                        <span>Custom URL:</span>
                        <div className="flex items-center space-x-2">
                          <code className="bg-green-100 px-2 py-1 rounded text-xs text-green-800">{domain.custom_url}</code>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => copyToClipboard(domain.custom_url || '')}
                          >
                            <Copy className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                    )}
                    
                    <div className="flex items-center justify-between">
                      <span>Created:</span>
                      <span>{domain.created_at ? new Date(domain.created_at).toLocaleDateString() : '—'}</span>
                    </div>
                    
                    {domain.activated_at && (
                      <div className="flex items-center justify-between">
                        <span>Activated:</span>
                        <span>{new Date(domain.activated_at).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
