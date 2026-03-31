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
import Int "mo:base/Int";

/// Project Manager Canister
/// Manages user projects, project metadata, and project lifecycle
/// Replaces Python Project model and projects service

module ProjectManager {
  public type ProjectId = Nat32;
  public type UserId = Nat32;
  public type CanisterId = Text;
  public type Timestamp = Nat64;
  public type Result<T, E> = Result.Result<T, E>;

  public type ProjectStatus = {
    #Pending;
    #Active;
    #Paused;
    #Archived;
    #Failed;
  };

  public type ProjectMetadata = {
    id: ProjectId;
    userId: UserId;
    name: Text;
    description: ?Text;
    status: ProjectStatus;
    canisterId: ?CanisterId;
    url: Text;
    mainFile: ?Text;
    gitRepository: ?Text;
    createdAt: Timestamp;
    updatedAt: Timestamp;
    deployedAt: ?Timestamp;
  };

  public type CreateProjectRequest = {
    userId: UserId;
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
    status: ?ProjectStatus;
  };

  public type ErrorType = {
    #NotFound;
    #Unauthorized;
    #ProjectExists;
    #InvalidName;
    #InvalidRequest;
    #CanisterNotReady;
    #InternalError;
  };

  stable var projectIdCounter: ProjectId = 1;
  let projects = HashMap.HashMap<ProjectId, ProjectMetadata>(20, Nat32.equal, Nat32.toNat);
  let userProjects = HashMap.HashMap<UserId, Buffer.Buffer<ProjectId>>(10, Nat32.equal, Nat32.toNat);
  let projectNameIndex = HashMap.HashMap<(UserId, Text), ProjectId>(20, func(a, b) {
    a.0 == b.0 and a.1 == b.1;
  }, func((userId, name)) {
    Nat32.toNat(userId) + Text.hash(name);
  });

  private func generateProjectId(): ProjectId {
    let id = projectIdCounter;
    projectIdCounter += 1;
    id;
  };

  private func generateProjectUrl(projectId: ProjectId): Text {
    let projectIdText = Nat32.toText(projectId);
    "https://" # Principal.toText(Principal.fromActor(ProjectManager)) # "-" # projectIdText # ".ic0.app";
  };

  private func isValidProjectName(name: Text): Bool {
    let size = Text.size(name);
    size >= 3 and size <= 100 and not Text.contains(name, #text(""));
  };

  public shared func createProject(request: CreateProjectRequest): async Result<ProjectMetadata, ErrorType> {
    if (not isValidProjectName(request.name)) {
      return #err(#InvalidName);
    };

    let nameKey = (request.userId, request.name);
    switch (projectNameIndex.get(nameKey)) {
      case (?_) return #err(#ProjectExists);
      case (null) {};
    };

    let projectId = generateProjectId();
    let now = Time.now();
    let projectUrl = generateProjectUrl(projectId);

    let project: ProjectMetadata = {
      id = projectId;
      userId = request.userId;
      name = request.name;
      description = request.description;
      status = #Pending;
      canisterId = null;
      url = projectUrl;
      mainFile = request.mainFile;
      gitRepository = request.gitRepository;
      createdAt = now;
      updatedAt = now;
      deployedAt = null;
    };

    projects.put(projectId, project);
    projectNameIndex.put(nameKey, projectId);

    // Add to user's project list
    switch (userProjects.get(request.userId)) {
      case (null) {
        let projectList = Buffer.Buffer<ProjectId>(1);
        projectList.add(projectId);
        userProjects.put(request.userId, projectList);
      };
      case (?projectList) {
        projectList.add(projectId);
      };
    };

    #ok(project);
  };

  public shared func getProject(projectId: ProjectId): async Result<ProjectMetadata, ErrorType> {
    switch (projects.get(projectId)) {
      case (null) return #err(#NotFound);
      case (?project) #ok(project);
    };
  };

  public shared func getUserProjects(userId: UserId): async [ProjectMetadata] {
    switch (userProjects.get(userId)) {
      case (null) [];
      case (?projectList) {
        Array.map<ProjectId, ProjectMetadata>(
          Buffer.toArray(projectList),
          func(projectId: ProjectId): ProjectMetadata {
            switch (projects.get(projectId)) {
              case (null) {
                // This shouldn't happen, but return a default
                {
                  id = projectId;
                  userId = userId;
                  name = "Unknown";
                  description = null;
                  status = #Failed;
                  canisterId = null;
                  url = "";
                  mainFile = null;
                  gitRepository = null;
                  createdAt = 0;
                  updatedAt = 0;
                  deployedAt = null;
                };
              };
              case (?project) project;
            };
          }
        );
      };
    };
  };

  public shared func updateProject(projectId: ProjectId, userId: UserId, request: UpdateProjectRequest): async Result<ProjectMetadata, ErrorType> {
    switch (projects.get(projectId)) {
      case (null) return #err(#NotFound);
      case (?project) {
        if (project.userId != userId) {
          return #err(#Unauthorized);
        };

        let updatedProject = {
          project with
          name = Option.getMapped<Text, Text>(request.name, func(n) { n }, project.name);
          description = Option.or(request.description, project.description);
          mainFile = Option.or(request.mainFile, project.mainFile);
          gitRepository = Option.or(request.gitRepository, project.gitRepository);
          status = Option.getMapped<ProjectStatus, ProjectStatus>(request.status, func(s) { s }, project.status);
          updatedAt = Time.now();
        };

        projects.put(projectId, updatedProject);

        #ok(updatedProject);
      };
    };
  };

  public shared func deleteProject(projectId: ProjectId, userId: UserId): async Result<(), ErrorType> {
    switch (projects.get(projectId)) {
      case (null) return #err(#NotFound);
      case (?project) {
        if (project.userId != userId) {
          return #err(#Unauthorized);
        };

        projects.delete(projectId);

        // Remove from user's project list
        switch (userProjects.get(userId)) {
          case (null) {};
          case (?projectList) {
            let filtered = Buffer.Buffer<ProjectId>(1);
            for (id in Iter.fromArray(Buffer.toArray(projectList))) {
              if (id != projectId) {
                filtered.add(id);
              };
            };
            if (filtered.size() > 0) {
              userProjects.put(userId, filtered);
            } else {
              userProjects.delete(userId);
            };
          };
        };

        // Remove from name index
        projectNameIndex.delete((userId, project.name));

        #ok(());
      };
    };
  };

  public shared func setCanisterId(projectId: ProjectId, userId: UserId, canisterId: CanisterId): async Result<ProjectMetadata, ErrorType> {
    switch (projects.get(projectId)) {
      case (null) return #err(#NotFound);
      case (?project) {
        if (project.userId != userId) {
          return #err(#Unauthorized);
        };

        let updatedProject = {
          project with
          canisterId = ?canisterId;
          status = #Active;
          deployedAt = ?Time.now();
          updatedAt = Time.now();
        };

        projects.put(projectId, updatedProject);

        #ok(updatedProject);
      };
    };
  };

  public shared func pauseProject(projectId: ProjectId, userId: UserId): async Result<ProjectMetadata, ErrorType> {
    switch (projects.get(projectId)) {
      case (null) return #err(#NotFound);
      case (?project) {
        if (project.userId != userId) {
          return #err(#Unauthorized);
        };

        let updatedProject = {
          project with
          status = #Paused;
          updatedAt = Time.now();
        };

        projects.put(projectId, updatedProject);

        #ok(updatedProject);
      };
    };
  };

  public shared func resumeProject(projectId: ProjectId, userId: UserId): async Result<ProjectMetadata, ErrorType> {
    switch (projects.get(projectId)) {
      case (null) return #err(#NotFound);
      case (?project) {
        if (project.userId != userId) {
          return #err(#Unauthorized);
        };

        let updatedProject = {
          project with
          status = #Active;
          updatedAt = Time.now();
        };

        projects.put(projectId, updatedProject);

        #ok(updatedProject);
      };
    };
  };

  public query func getProjectCount(): async Nat {
    projects.size();
  };

  public query func getStats(): async {
    totalProjects: Nat;
    totalUsers: Nat;
  } {
    {
      totalProjects = projects.size();
      totalUsers = userProjects.size();
    };
  };
};
