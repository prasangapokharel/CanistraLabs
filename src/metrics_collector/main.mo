import Array "mo:base/Array";
import HashMap "mo:base/HashMap";
import Iter "mo:base/Iter";
import Nat32 "mo:base/Nat32";
import Nat64 "mo:base/Nat64";
import Option "mo:base/Option";
import Result "mo:base/Result";
import Text "mo:base/Text";
import Time "mo:base/Time";
import Nat "mo:base/Nat";

/// Metrics Collector Canister
/// Collects and aggregates metrics for projects and canisters
/// Replaces Python metrics service

module MetricsCollector {
  public type ProjectId = Nat32;
  public type CanisterId = Text;
  public type Timestamp = Nat64;
  public type Result<T, E> = Result.Result<T, E>;

  public type MetricPoint = {
    timestamp: Timestamp;
    value: Nat64;
  };

  public type ProjectMetrics = {
    projectId: ProjectId;
    canisterId: ?CanisterId;
    requestCount: Nat64;
    errorCount: Nat64;
    averageResponseTime: Nat64; // milliseconds
    p95ResponseTime: Nat64;
    p99ResponseTime: Nat64;
    storageUsed: Nat64; // bytes
    cyclesBurned: Nat64;
    uptime: Float; // percentage
    lastUpdated: Timestamp;
  };

  public type ProjectActivity = {
    id: Text;
    projectId: ProjectId;
    activityType: ActivityType;
    description: Text;
    timestamp: Timestamp;
  };

  public type ActivityType = {
    #Deployment;
    #Update;
    #Scale;
    #Failure;
    #Recovery;
    #Custom;
  };

  public type DashboardMetrics = {
    totalProjects: Nat;
    activeProjects: Nat;
    totalRequests: Nat64;
    totalErrors: Nat64;
    totalCyclesBurned: Nat64;
    averageUptime: Float;
    recentActivity: [ProjectActivity];
  };

  public type ErrorType = {
    #NotFound;
    #InvalidData;
    #InternalError;
  };

  stable var activityIdCounter: Nat = 1;

  let projectMetrics = HashMap.HashMap<ProjectId, ProjectMetrics>(20, Nat32.equal, Nat32.toNat);
  let projectActivities = HashMap.HashMap<ProjectId, [ProjectActivity]>(20, Nat32.equal, Nat32.toNat);
  let requestCounts = HashMap.HashMap<(ProjectId, Nat64), Nat64>(50, func(a, b) {
    a.0 == b.0 and a.1 == b.1;
  }, func((projectId, period)) {
    Nat32.toNat(projectId) + Nat64.toNat(period);
  });
  let errorCounts = HashMap.HashMap<(ProjectId, Nat64), Nat64>(50, func(a, b) {
    a.0 == b.0 and a.1 == b.1;
  }, func((projectId, period)) {
    Nat32.toNat(projectId) + Nat64.toNat(period);
  });
  let responseTimeSamples = HashMap.HashMap<ProjectId, [Nat64]>(20, Nat32.equal, Nat32.toNat);

  private func generateActivityId(): Text {
    let id = activityIdCounter;
    activityIdCounter += 1;
    "activity-" # Nat.toText(id);
  };

  private func calculatePercentile(values: [Nat64], percentile: Nat64): Nat64 {
    if (values.size() == 0) return 0;
    if (values.size() == 1) return values[0];

    // Simple percentile calculation (not production-grade)
    let index = (Nat64.toNat(percentile) * values.size()) / 100;
    if (index >= values.size()) {
      values[values.size() - 1];
    } else {
      values[index];
    };
  };

  private func calculateAverage(values: [Nat64]): Nat64 {
    if (values.size() == 0) return 0;
    var sum: Nat64 = 0;
    for (value in Iter.fromArray(values)) {
      sum += value;
    };
    sum / Nat64.fromNat(values.size());
  };

  public shared func recordRequest(projectId: ProjectId, responseTime: Nat64, isError: Bool): async Result<(), ErrorType> {
    let now = Time.now();
    let hour = now / (3_600_000_000_000); // hour in nanoseconds

    let requestKey = (projectId, hour);
    let currentCount = switch (requestCounts.get(requestKey)) {
      case (null) 0;
      case (?count) count;
    };
    requestCounts.put(requestKey, currentCount + 1);

    if (isError) {
      let errorKey = (projectId, hour);
      let currentErrors = switch (errorCounts.get(errorKey)) {
        case (null) 0;
        case (?count) count;
      };
      errorCounts.put(errorKey, currentErrors + 1);
    };

    // Record response time sample
    let samples = switch (responseTimeSamples.get(projectId)) {
      case (null) [responseTime];
      case (?existing) {
        let buffer = Array.init<Nat64>(existing.size() + 1, responseTime);
        for (i in Iter.range(0, existing.size() - 1)) {
          buffer[i] := existing[i];
        };
        Array.freeze(buffer);
      };
    };

    responseTimeSamples.put(projectId, samples);

    #ok(());
  };

  public shared func recordCyclesBurned(projectId: ProjectId, cycles: Nat64): async Result<(), ErrorType> {
    switch (projectMetrics.get(projectId)) {
      case (null) return #err(#NotFound);
      case (?metrics) {
        let updatedMetrics = {
          metrics with
          cyclesBurned = metrics.cyclesBurned + cycles;
          lastUpdated = Time.now();
        };
        projectMetrics.put(projectId, updatedMetrics);
        #ok(());
      };
    };
  };

  public shared func recordStorageUsed(projectId: ProjectId, bytes: Nat64): async Result<(), ErrorType> {
    switch (projectMetrics.get(projectId)) {
      case (null) return #err(#NotFound);
      case (?metrics) {
        let updatedMetrics = {
          metrics with
          storageUsed = bytes;
          lastUpdated = Time.now();
        };
        projectMetrics.put(projectId, updatedMetrics);
        #ok(());
      };
    };
  };

  public shared func initializeProjectMetrics(projectId: ProjectId, canisterId: ?CanisterId): async Result<ProjectMetrics, ErrorType> {
    let metrics: ProjectMetrics = {
      projectId = projectId;
      canisterId = canisterId;
      requestCount = 0;
      errorCount = 0;
      averageResponseTime = 0;
      p95ResponseTime = 0;
      p99ResponseTime = 0;
      storageUsed = 0;
      cyclesBurned = 0;
      uptime = 100.0;
      lastUpdated = Time.now();
    };

    projectMetrics.put(projectId, metrics);
    #ok(metrics);
  };

  public shared func getProjectMetrics(projectId: ProjectId): async Result<ProjectMetrics, ErrorType> {
    switch (projectMetrics.get(projectId)) {
      case (null) return #err(#NotFound);
      case (?metrics) {
        // Calculate current stats
        let samples = switch (responseTimeSamples.get(projectId)) {
          case (null) [];
          case (?s) s;
        };

        let avg = calculateAverage(samples);
        let p95 = calculatePercentile(samples, 95);
        let p99 = calculatePercentile(samples, 99);

        let updatedMetrics = {
          metrics with
          averageResponseTime = avg;
          p95ResponseTime = p95;
          p99ResponseTime = p99;
        };

        #ok(updatedMetrics);
      };
    };
  };

  public shared func recordActivity(projectId: ProjectId, activityType: ActivityType, description: Text): async Result<ProjectActivity, ErrorType> {
    let activity: ProjectActivity = {
      id = generateActivityId();
      projectId = projectId;
      activityType = activityType;
      description = description;
      timestamp = Time.now();
    };

    let activities = switch (projectActivities.get(projectId)) {
      case (null) [activity];
      case (?existing) {
        let buffer = Array.init<ProjectActivity>(existing.size() + 1, activity);
        for (i in Iter.range(0, existing.size() - 1)) {
          buffer[i] := existing[i];
        };
        Array.freeze(buffer);
      };
    };

    projectActivities.put(projectId, activities);
    #ok(activity);
  };

  public shared func getProjectActivities(projectId: ProjectId, limit: Nat): async [ProjectActivity] {
    switch (projectActivities.get(projectId)) {
      case (null) [];
      case (?activities) {
        let count = Nat.min(limit, activities.size());
        Array.tabulate<ProjectActivity>(
          count,
          func(i: Nat): ProjectActivity {
            activities[activities.size() - 1 - i];
          }
        );
      };
    };
  };

  public shared func getDashboardMetrics(): async DashboardMetrics {
    var totalProjects = projectMetrics.size();
    var activeProjects = 0;
    var totalRequests: Nat64 = 0;
    var totalErrors: Nat64 = 0;
    var totalCyclesBurned: Nat64 = 0;
    var totalUptime: Float = 0.0;
    var recentActivityList: [ProjectActivity] = [];

    for (metrics in Iter.map<(ProjectId, ProjectMetrics), ProjectMetrics>(
      projectMetrics.entries(),
      func((_, m)) { m }
    )) {
      if (metrics.uptime > 90.0) {
        activeProjects += 1;
      };
      totalRequests += metrics.requestCount;
      totalErrors += metrics.errorCount;
      totalCyclesBurned += metrics.cyclesBurned;
      totalUptime += metrics.uptime;
    };

    let averageUptime = if (totalProjects > 0) {
      totalUptime / Float.fromInt(totalProjects);
    } else {
      100.0;
    };

    // Get recent activities
    for (activities in Iter.map<(ProjectId, [ProjectActivity]), [ProjectActivity]>(
      projectActivities.entries(),
      func((_, a)) { a }
    )) {
      if (activities.size() > 0) {
        recentActivityList := Array.append(recentActivityList, activities);
      };
    };

    {
      totalProjects = totalProjects;
      activeProjects = activeProjects;
      totalRequests = totalRequests;
      totalErrors = totalErrors;
      totalCyclesBurned = totalCyclesBurned;
      averageUptime = averageUptime;
      recentActivity = recentActivityList;
    };
  };

  public query func getMetricsCount(): async Nat {
    projectMetrics.size();
  };

  public query func getStats(): async {
    trackedProjects: Nat;
    totalActivities: Nat;
  } {
    var totalActivities = 0;
    for (activities in Iter.map<(ProjectId, [ProjectActivity]), [ProjectActivity]>(
      projectActivities.entries(),
      func((_, a)) { a }
    )) {
      totalActivities += activities.size();
    };

    {
      trackedProjects = projectMetrics.size();
      totalActivities = totalActivities;
    };
  };
};
