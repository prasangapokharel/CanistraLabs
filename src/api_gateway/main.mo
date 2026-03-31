import Array "mo:base/Array";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Nat32 "mo:base/Nat32";
import Nat64 "mo:base/Nat64";
import Option "mo:base/Option";
import Principal "mo:base/Principal";
import Result "mo:base/Result";
import Text "mo:base/Text";
import Time "mo:base/Time";
import Nat "mo:base/Nat";

/// API Gateway Canister
/// Main entry point for all API requests, orchestrates inter-canister calls
/// Replaces FastAPI backend layer

module APIGateway {
  public type UserId = Nat32;
  public type ProjectId = Nat32;
  public type CanisterId = Text;
  public type Timestamp = Nat64;
  public type Result<T, E> = Result.Result<T, E>;

  // Request types for user operations
  public type SignupRequest = {
    email: Text;
    password: Text;
    displayName: ?Text;
  };

  public type LoginRequest = {
    email: Text;
    password: Text;
  };

  public type RefreshTokenRequest = {
    refreshToken: Text;
  };

  // Request types for project operations
  public type CreateProjectRequest = {
    name: Text;
    description: ?Text;
    mainFile: ?Text;
    gitRepository: ?Text;
  };

  public type UpdateProjectRequest = {
    name: ?Text;
    description: ?Text;
    mainFile: ?Text;
    gitRepository: ?Text;
  };

  // Request types for deployment
  public type DeployProjectRequest = {
    projectId: ProjectId;
    sourceCode: Text;
    version: ?Text;
  };

  // Request types for domain management
  public type SetupDomainRequest = {
    projectId: ProjectId;
    domain: Text;
    canisterUrl: Text;
  };

  // Response types
  public type AuthResponse = {
    accessToken: Text;
    refreshToken: Text;
    expiresAt: Timestamp;
    userId: ?UserId;
  };

  public type ProjectResponse = {
    id: ProjectId;
    name: Text;
    description: ?Text;
    status: Text;
    url: Text;
    canisterId: ?CanisterId;
    createdAt: Timestamp;
  };

  public type ApiError = {
    code: Text;
    message: Text;
    timestamp: Timestamp;
  };

  public type ErrorType = {
    #Unauthorized;
    #NotFound;
    #BadRequest;
    #InternalError;
  };

  // Rate limiting
  stable var requestCounts = HashMap.HashMap<Principal, Nat>(100, Principal.equal, Principal.hash);
  stable var lastResetTime: Timestamp = Time.now();
  let RATE_LIMIT_PER_HOUR = 10_000;

  private func isRateLimited(principal: Principal): Bool {
    let now = Time.now();
    let hourAgo = now - (3_600 * 1_000_000_000); // 1 hour in nanoseconds

    if (now - lastResetTime > 3_600 * 1_000_000_000) {
      requestCounts.clear();
      lastResetTime := now;
    };

    let count = switch (requestCounts.get(principal)) {
      case (null) 0;
      case (?c) c;
    };

    if (count >= RATE_LIMIT_PER_HOUR) {
      return true;
    };

    requestCounts.put(principal, count + 1);
    false;
  };

  private func createErrorResponse(code: Text, message: Text): ApiError {
    {
      code = code;
      message = message;
      timestamp = Time.now();
    };
  };

  // Auth endpoints
  public shared({ caller }) func signup(request: SignupRequest): async Result<AuthResponse, ApiError> {
    if (isRateLimited(caller)) {
      return #err(createErrorResponse("RATE_LIMITED", "Too many requests"));
    };

    // Signature: Auth service would handle this
    // For now, return mock response
    #ok({
      accessToken = "mock-access-token";
      refreshToken = "mock-refresh-token";
      expiresAt = Time.now() + (24 * 3600 * 1_000_000_000);
      userId = ?1;
    });
  };

  public shared({ caller }) func login(request: LoginRequest): async Result<AuthResponse, ApiError> {
    if (isRateLimited(caller)) {
      return #err(createErrorResponse("RATE_LIMITED", "Too many requests"));
    };

    #ok({
      accessToken = "mock-access-token";
      refreshToken = "mock-refresh-token";
      expiresAt = Time.now() + (24 * 3600 * 1_000_000_000);
      userId = ?1;
    });
  };

  public shared({ caller }) func refresh(request: RefreshTokenRequest): async Result<AuthResponse, ApiError> {
    #ok({
      accessToken = "mock-new-access-token";
      refreshToken = request.refreshToken;
      expiresAt = Time.now() + (24 * 3600 * 1_000_000_000);
      userId = ?1;
    });
  };

  public shared({ caller }) func me(accessToken: Text): async Result<{ userId: UserId; email: Text }, ApiError> {
    #ok({
      userId = 1;
      email = "user@example.com";
    });
  };

  // Project endpoints
  public shared({ caller }) func createProject(accessToken: Text, request: CreateProjectRequest): async Result<ProjectResponse, ApiError> {
    if (isRateLimited(caller)) {
      return #err(createErrorResponse("RATE_LIMITED", "Too many requests"));
    };

    #ok({
      id = 1;
      name = request.name;
      description = request.description;
      status = "pending";
      url = "https://example-1.ic0.app";
      canisterId = null;
      createdAt = Time.now();
    });
  };

  public shared({ caller }) func getProjects(accessToken: Text): async Result<[ProjectResponse], ApiError> {
    #ok([
      {
        id = 1;
        name = "My First Project";
        description = null;
        status = "active";
        url = "https://example-1.ic0.app";
        canisterId = ?"canister-1";
        createdAt = Time.now() - (86_400 * 1_000_000_000);
      }
    ]);
  };

  public shared({ caller }) func getProject(accessToken: Text, projectId: ProjectId): async Result<ProjectResponse, ApiError> {
    #ok({
      id = projectId;
      name = "My Project";
      description = ?"A test project";
      status = "active";
      url = "https://example-" # Nat32.toText(projectId) # ".ic0.app";
      canisterId = ?"canister-" # Nat32.toText(projectId);
      createdAt = Time.now();
    });
  };

  public shared({ caller }) func updateProject(accessToken: Text, projectId: ProjectId, request: UpdateProjectRequest): async Result<ProjectResponse, ApiError> {
    #ok({
      id = projectId;
      name = Option.getMapped<Text, Text>(request.name, func(n) { n }, "Updated Project");
      description = request.description;
      status = "active";
      url = "https://example-" # Nat32.toText(projectId) # ".ic0.app";
      canisterId = ?"canister-" # Nat32.toText(projectId);
      createdAt = Time.now();
    });
  };

  public shared({ caller }) func deleteProject(accessToken: Text, projectId: ProjectId): async Result<{ success: Bool }, ApiError> {
    #ok({ success = true });
  };

  // Wallet endpoints
  public shared({ caller }) func getWallet(accessToken: Text): async Result<{
    cycleBalance: Nat64;
    usdBalance: Float;
    accountId: Text;
  }, ApiError> {
    #ok({
      cycleBalance = 1_000_000_000;
      usdBalance = 1.0;
      accountId = Principal.toText(caller);
    });
  };

  public shared({ caller }) func getWalletIdentity(accessToken: Text): async Result<{
    principal: Text;
    accountId: Text;
  }, ApiError> {
    #ok({
      principal = Principal.toText(caller);
      accountId = Principal.toText(caller);
    });
  };

  // Deployment endpoints
  public shared({ caller }) func deployProject(accessToken: Text, request: DeployProjectRequest): async Result<{
    deploymentId: Text;
    status: Text;
  }, ApiError> {
    #ok({
      deploymentId = "deployment-1";
      status = "building";
    });
  };

  public shared({ caller }) func getDeployments(accessToken: Text, projectId: ProjectId): async Result<[{
    id: Text;
    status: Text;
    version: Text;
    createdAt: Timestamp;
  }], ApiError> {
    #ok([
      {
        id = "deployment-1";
        status = "running";
        version = "0.1.0";
        createdAt = Time.now();
      }
    ]);
  };

  // Domain endpoints
  public shared({ caller }) func setupDomain(accessToken: Text, request: SetupDomainRequest): async Result<{
    domainId: Nat32;
    status: Text;
  }, ApiError> {
    #ok({
      domainId = 1;
      status = "pending";
    });
  };

  public shared({ caller }) func verifyDomain(accessToken: Text, domainId: Nat32): async Result<{ verified: Bool }, ApiError> {
    #ok({ verified = true });
  };

  // Metrics endpoints
  public shared({ caller }) func getMetrics(accessToken: Text, projectId: ProjectId): async Result<{
    requestCount: Nat64;
    errorCount: Nat64;
    storageUsed: Nat64;
    cyclesBurned: Nat64;
  }, ApiError> {
    #ok({
      requestCount = 10_000;
      errorCount = 50;
      storageUsed = 1_000_000;
      cyclesBurned = 500_000_000;
    });
  };

  public shared({ caller }) func getDashboardMetrics(accessToken: Text): async Result<{
    totalProjects: Nat;
    activeProjects: Nat;
    totalRequests: Nat64;
    averageUptime: Float;
  }, ApiError> {
    #ok({
      totalProjects = 10;
      activeProjects = 8;
      totalRequests = 100_000;
      averageUptime = 99.9;
    });
  };

  // Health check
  public query func health(): async {
    status: Text;
    timestamp: Timestamp;
  } {
    {
      status = "healthy";
      timestamp = Time.now();
    };
  };

  // System stats
  public query func getStats(): async {
    uptime: Nat64;
    requestCount: Nat;
    rateLimitedUsers: Nat;
  } {
    {
      uptime = Time.now();
      requestCount = requestCounts.size();
      rateLimitedUsers = 0;
    };
  };
};
