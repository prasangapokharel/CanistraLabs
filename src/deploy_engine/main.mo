import Array "mo:base/Array";
import Buffer "mo:base/Buffer";
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

/// Deploy Engine Canister
/// Handles project deployment, canister creation, and lifecycle management
/// Replaces Python CanisterFactory and DeploymentService

module DeployEngine {
  public type DeploymentId = Nat32;
  public type ProjectId = Nat32;
  public type UserId = Nat32;
  public type CanisterId = Text;
  public type Timestamp = Nat64;
  public type Result<T, E> = Result.Result<T, E>;

  public type DeploymentStatus = {
    #Queued;
    #Building;
    #Installing;
    #Running;
    #Failed;
    #Stopped;
    #Terminating;
    #Terminated;
  };

  public type DeploymentInfo = {
    id: DeploymentId;
    projectId: ProjectId;
    userId: UserId;
    canisterId: ?CanisterId;
    status: DeploymentStatus;
    version: Text;
    buildLog: ?Text;
    errorMessage: ?Text;
    createdAt: Timestamp;
    updatedAt: Timestamp;
    completedAt: ?Timestamp;
  };

  public type DeploymentRequest = {
    projectId: ProjectId;
    userId: UserId;
    sourceCode: Text;
    version: ?Text;
  };

  public type CanisterStatus = {
    #Stopped;
    #Stopping;
    #Running;
    #Installing;
  };

  public type CanisterInfo = {
    canisterId: CanisterId;
    projectId: ProjectId;
    userId: UserId;
    status: CanisterStatus;
    cycleBalance: Nat64;
    createdAt: Timestamp;
    updatedAt: Timestamp;
  };

  public type ErrorType = {
    #NotFound;
    #Unauthorized;
    #ProjectNotFound;
    #CanisterNotFound;
    #DeploymentFailed;
    #InvalidRequest;
    #InsufficientCycles;
    #InternalError;
  };

  stable var deploymentIdCounter: DeploymentId = 1;
  stable var canisterIdCounter: Nat = 1;

  let deployments = HashMap.HashMap<DeploymentId, DeploymentInfo>(20, Nat32.equal, Nat32.toNat);
  let projectDeployments = HashMap.HashMap<ProjectId, Buffer.Buffer<DeploymentId>>(20, Nat32.equal, Nat32.toNat);
  let canisters = HashMap.HashMap<CanisterId, CanisterInfo>(20, Text.equal, Text.hash);
  let projectCanisters = HashMap.HashMap<ProjectId, CanisterId>(20, Nat32.equal, Nat32.toNat);

  private func generateDeploymentId(): DeploymentId {
    let id = deploymentIdCounter;
    deploymentIdCounter += 1;
    id;
  };

  private func generateCanisterId(): CanisterId {
    let id = canisterIdCounter;
    canisterIdCounter += 1;
    // Generate a deterministic canister ID based on project
    "canister-" # Nat.toText(id);
  };

  public shared func deployProject(request: DeploymentRequest): async Result<DeploymentInfo, ErrorType> {
    if (Text.size(request.sourceCode) == 0) {
      return #err(#InvalidRequest);
    };

    let deploymentId = generateDeploymentId();
    let now = Time.now();

    let deployment: DeploymentInfo = {
      id = deploymentId;
      projectId = request.projectId;
      userId = request.userId;
      canisterId = null;
      status = #Queued;
      version = Option.getMapped<Text, Text>(request.version, func(v) { v }, "0.1.0");
      buildLog = null;
      errorMessage = null;
      createdAt = now;
      updatedAt = now;
      completedAt = null;
    };

    deployments.put(deploymentId, deployment);

    // Add to project's deployment history
    switch (projectDeployments.get(request.projectId)) {
      case (null) {
        let deploymentList = Buffer.Buffer<DeploymentId>(1);
        deploymentList.add(deploymentId);
        projectDeployments.put(request.projectId, deploymentList);
      };
      case (?deploymentList) {
        deploymentList.add(deploymentId);
      };
    };

    // Simulate deployment process
    let canisterId = generateCanisterId();
    let newCanister: CanisterInfo = {
      canisterId = canisterId;
      projectId = request.projectId;
      userId = request.userId;
      status = #Installing;
      cycleBalance = 0;
      createdAt = now;
      updatedAt = now;
    };

    canisters.put(canisterId, newCanister);
    projectCanisters.put(request.projectId, canisterId);

    let updatedDeployment = {
      deployment with
      canisterId = ?canisterId;
      status = #Installing;
      buildLog = ?"Starting deployment...";
      updatedAt = now;
    };

    deployments.put(deploymentId, updatedDeployment);

    #ok(updatedDeployment);
  };

  public shared func getDeployment(deploymentId: DeploymentId): async Result<DeploymentInfo, ErrorType> {
    switch (deployments.get(deploymentId)) {
      case (null) return #err(#NotFound);
      case (?deployment) #ok(deployment);
    };
  };

  public shared func getProjectDeployments(projectId: ProjectId): async [DeploymentInfo] {
    switch (projectDeployments.get(projectId)) {
      case (null) [];
      case (?deploymentList) {
        Array.map<DeploymentId, DeploymentInfo>(
          Buffer.toArray(deploymentList),
          func(deploymentId: DeploymentId): DeploymentInfo {
            switch (deployments.get(deploymentId)) {
              case (null) {
                {
                  id = deploymentId;
                  projectId = projectId;
                  userId = 0;
                  canisterId = null;
                  status = #Failed;
                  version = "unknown";
                  buildLog = null;
                  errorMessage = ?"Deployment record not found";
                  createdAt = 0;
                  updatedAt = 0;
                  completedAt = null;
                };
              };
              case (?deployment) deployment;
            };
          }
        );
      };
    };
  };

  public shared func updateDeploymentStatus(deploymentId: DeploymentId, status: DeploymentStatus): async Result<DeploymentInfo, ErrorType> {
    switch (deployments.get(deploymentId)) {
      case (null) return #err(#NotFound);
      case (?deployment) {
        let completedAt = if (status == #Running or status == #Failed or status == #Stopped) {
          ?Time.now();
        } else {
          deployment.completedAt;
        };

        let updatedDeployment = {
          deployment with
          status = status;
          updatedAt = Time.now();
          completedAt = completedAt;
        };

        deployments.put(deploymentId, updatedDeployment);

        #ok(updatedDeployment);
      };
    };
  };

  public shared func getCanisterInfo(canisterId: CanisterId): async Result<CanisterInfo, ErrorType> {
    switch (canisters.get(canisterId)) {
      case (null) return #err(#CanisterNotFound);
      case (?canister) #ok(canister);
    };
  };

  public shared func getProjectCanister(projectId: ProjectId): async Result<CanisterInfo, ErrorType> {
    switch (projectCanisters.get(projectId)) {
      case (null) return #err(#CanisterNotFound);
      case (?canisterId) {
        switch (canisters.get(canisterId)) {
          case (null) return #err(#CanisterNotFound);
          case (?canister) #ok(canister);
        };
      };
    };
  };

  public shared func updateCanisterStatus(canisterId: CanisterId, status: CanisterStatus): async Result<CanisterInfo, ErrorType> {
    switch (canisters.get(canisterId)) {
      case (null) return #err(#CanisterNotFound);
      case (?canister) {
        let updatedCanister = {
          canister with
          status = status;
          updatedAt = Time.now();
        };

        canisters.put(canisterId, updatedCanister);

        #ok(updatedCanister);
      };
    };
  };

  public shared func stopCanister(canisterId: CanisterId, userId: UserId): async Result<(), ErrorType> {
    switch (canisters.get(canisterId)) {
      case (null) return #err(#CanisterNotFound);
      case (?canister) {
        if (canister.userId != userId) {
          return #err(#Unauthorized);
        };

        let updatedCanister = {
          canister with
          status = #Stopping;
          updatedAt = Time.now();
        };

        canisters.put(canisterId, updatedCanister);

        #ok(());
      };
    };
  };

  public shared func startCanister(canisterId: CanisterId, userId: UserId): async Result<(), ErrorType> {
    switch (canisters.get(canisterId)) {
      case (null) return #err(#CanisterNotFound);
      case (?canister) {
        if (canister.userId != userId) {
          return #err(#Unauthorized);
        };

        let updatedCanister = {
          canister with
          status = #Running;
          updatedAt = Time.now();
        };

        canisters.put(canisterId, updatedCanister);

        #ok(());
      };
    };
  };

  public query func getDeploymentCount(): async Nat {
    deployments.size();
  };

  public query func getCanisterCount(): async Nat {
    canisters.size();
  };

  public query func getStats(): async {
    totalDeployments: Nat;
    totalCanisters: Nat;
    activeDeployments: Nat;
  } {
    var activeDeployments = 0;
    for (deployment in Iter.fromArray(Array.map<DeploymentId, DeploymentInfo>(
      Buffer.toArray(Buffer.fromArray(Array.init<DeploymentId>(0, 0))),
      func(id) { deployments.get(id) }
    ))) {
      switch (deployment) {
        case (null) {};
        case (?d) {
          if (d.status == #Building or d.status == #Installing) {
            activeDeployments += 1;
          };
        };
      };
    };

    {
      totalDeployments = deployments.size();
      totalCanisters = canisters.size();
      activeDeployments = activeDeployments;
    };
  };
};
