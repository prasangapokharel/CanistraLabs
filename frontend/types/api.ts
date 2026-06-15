/**
 * Shared API types for the frontend — aligned with backend schemas.
 */

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export type SortDirection = 'asc' | 'desc';

export type CanisterStatusType = 'running' | 'stopped' | 'error' | 'deploying' | 'failed';

export interface CanisterMetric {
  timestamp: string;
  cycles: number;
  memoryUsage: number;
  requests: number;
}

export interface Canister {
  id: string;
  name: string;
  projectId: string;
  status: CanisterStatusType;
  cycles: number;
  maxCycles: number;
  memory: number;
  subnet: string;
  principal: string;
  createdAt: string;
  updatedAt: string;
  lastDeployed: string;
  version?: string;
  lastDeployment?: string;
}

export interface CanisterListItem extends Canister {
  version?: string;
  lastDeployment?: string;
}

export interface CanisterLog {
  id: string;
  canisterId: string;
  level: 'info' | 'warn' | 'error' | 'debug';
  message: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export interface Project {
  id: number | string;
  name: string;
  description?: string;
  status: 'active' | 'inactive' | 'deploying' | 'pending' | string;
  display_status?: string;
  is_paused?: boolean;
  code_content?: string | null;
  canister_id?: string | null;
  url?: string | null;
  principal_id?: string | null;
  canisters?: Canister[];
  created_at?: string;
  updated_at?: string;
  deployed_at?: string | null;
  createdAt?: string;
  updatedAt?: string;
}

export interface Domain {
  id: string | number;
  name?: string;
  domain_name?: string;
  projectId?: string | number;
  project_id?: number;
  status: 'pending' | 'verified' | 'failed' | string;
  expiresAt?: string;
  createdAt?: string;
  updatedAt?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Activity {
  id: string;
  type?: 'deployment' | 'domain_update' | 'canister_update' | 'project_update';
  title?: string;
  description: string;
  projectId?: string | number;
  project_id?: number;
  canisterId?: string;
  timestamp: string;
  status?: string;
}

export interface CanisterStatus {
  status: string;
  canister_id?: string;
  cycles_balance?: number;
  memory_size?: number;
}

export interface ProjectMetrics {
  source?: string;
  status?: string;
  cycles_balance?: number;
  cycles_formatted?: string;
  idle_cycles_burned_per_day?: number;
  idle_cycles_burned_per_day_formatted?: string;
  memory_bytes?: number;
  memory_formatted?: string;
  freezing_threshold_seconds?: number;
  freezing_threshold_formatted?: string;
  reserved_cycles?: number;
  reserved_cycles_formatted?: string;
  number_of_queries?: number;
  instructions_spent_in_queries?: number;
  query_request_payload_bytes?: number;
  query_request_payload_formatted?: string;
  query_response_payload_bytes?: number;
  query_response_payload_formatted?: string;
  module_hash?: string | null;
  fields?: Array<{ label: string; value: string }>;
  checked_at?: string;
  error?: string;
}

export interface DeploymentPayload {
  code_content?: string;
  force?: boolean;
  projectId?: string | number;
  project_id?: number;
}

export interface FundingInstructions {
  principal_id?: string;
  account_id?: string;
  funding_address?: string;
  current_status?: {
    funded?: boolean;
    balance?: string;
    cycles_balance?: string;
    auto_convert_available?: boolean;
    has_pending_icp?: boolean;
  };
  instructions?: Array<{
    step: number;
    title: string;
    description: string;
    data?: Record<string, unknown>;
    options?: Array<{ name: string; url: string }>;
  }>;
  quick_links?: Record<string, string>;
}

export interface FundingRequirements {
  deploy_network?: string;
  cycles_balance?: string;
  cycles_required?: string;
  cycles_recommended?: string;
  cycles_shortfall?: string;
  formatted_cycles_required?: string;
  formatted_cycles_recommended?: string;
  formatted_cycles_shortfall?: string;
  deploy_ready?: boolean;
  min_icp_to_convert?: string;
  min_icp_to_convert_e8s?: string;
  recommended_icp_to_fund?: string;
}

export interface DeployResult {
  deployment_id: number;
  project_id: number;
  canister_id?: string | null;
  url?: string | null;
  status: string;
  message?: string;
  principal_id?: string;
  cycles_balance?: string;
  funding_required?: boolean;
  can_retry?: boolean;
  async?: boolean;
  error_code?: string;
  cycles_required?: number;
  cycles_shortfall?: number;
  recommended_icp?: string;
  action?: string;
}

export interface DeploymentRecord {
  id: number;
  deployment_id: number;
  status: string;
  message?: string;
  canister_id?: string | null;
  url?: string | null;
  created_at?: string;
  started_at?: string;
  completed_at?: string;
}

export interface WalletIdentity {
  identity_name?: string;
  principal_id?: string;
  account_id?: string;
  cycles_balance?: number;
  icp_balance?: number;
  formatted_icp?: string;
  formatted_cycles?: string;
  funding_required?: boolean;
  auto_convert_available?: boolean;
  has_pending_icp?: boolean;
  status?: string;
  message?: string;
  funding_address?: string;
  token_symbol?: string;
  network?: string;
  deploy_network?: string;
  use_testicp?: boolean;
  deploy_ready?: boolean;
  requirements?: FundingRequirements;
  created_at?: string;
}

export interface DfxCommandCatalogEntry {
  dfx: string;
  method: string;
  api: string | null;
  implemented: boolean;
  category: string;
  notes?: string;
}

export interface DfxCommandCatalog {
  total: number;
  implemented: number;
  pending: number;
  commands: DfxCommandCatalogEntry[];
  dfx_version?: string;
  timestamp?: string;
}

export interface DfxConvertBody {
  amount?: string;
}

export interface DfxCyclesTopUpBody {
  canister_id: string;
  amount: string;
}

export interface DfxDepositCyclesBody {
  amount: string;
}
