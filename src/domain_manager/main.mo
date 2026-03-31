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

/// Domain Manager Canister
/// Manages custom domains, DNS configuration, and SSL certificates
/// Replaces Python domainManagement service

module DomainManager {
  public type DomainId = Nat32;
  public type ProjectId = Nat32;
  public type UserId = Nat32;
  public type Timestamp = Nat64;
  public type Result<T, E> = Result.Result<T, E>;

  public type DomainStatus = {
    #Pending;
    #Active;
    #Verified;
    #Failed;
    #Expired;
  };

  public type DomainInfo = {
    id: DomainId;
    projectId: ProjectId;
    userId: UserId;
    domain: Text;
    status: DomainStatus;
    canisterUrl: ?Text;
    verificationRecord: ?Text;
    verifiedAt: ?Timestamp;
    createdAt: Timestamp;
    updatedAt: Timestamp;
  };

  public type DNSRecord = {
    recordType: Text; // "CNAME", "A", "TXT", etc.
    name: Text;
    value: Text;
    ttl: Nat32;
  };

  public type SetupDomainRequest = {
    projectId: ProjectId;
    userId: UserId;
    domain: Text;
    canisterUrl: Text;
  };

  public type VerifyDomainRequest = {
    projectId: ProjectId;
    userId: UserId;
    domainId: DomainId;
    verificationRecord: Text;
  };

  public type ErrorType = {
    #NotFound;
    #Unauthorized;
    #InvalidDomain;
    #DomainExists;
    #VerificationFailed;
    #ProjectNotFound;
    #InternalError;
  };

  stable var domainIdCounter: DomainId = 1;

  let domains = HashMap.HashMap<DomainId, DomainInfo>(20, Nat32.equal, Nat32.toNat);
  let projectDomains = HashMap.HashMap<ProjectId, Buffer.Buffer<DomainId>>(20, Nat32.equal, Nat32.toNat);
  let domainIndex = HashMap.HashMap<Text, DomainId>(20, Text.equal, Text.hash);

  private func generateDomainId(): DomainId {
    let id = domainIdCounter;
    domainIdCounter += 1;
    id;
  };

  private func isValidDomain(domain: Text): Bool {
    // Basic domain validation
    let parts = Iter.toArray(Text.split(domain, #char('.')));
    if (parts.size() < 2) return false;
    if (Text.size(parts[parts.size() - 1]) < 2) return false; // TLD too short
    for (part in Iter.fromArray(parts)) {
      if (Text.size(part) == 0) return false;
    };
    true;
  };

  private func generateVerificationRecord(domain: Text, projectId: ProjectId): Text {
    // Generate a unique verification record
    "ic-verify=" # domain # "-" # Nat32.toText(projectId);
  };

  private func generateDNSRecords(domain: Text, canisterUrl: Text): [DNSRecord] {
    [
      {
        recordType = "CNAME";
        name = domain;
        value = canisterUrl;
        ttl = 3600;
      }
    ];
  };

  public shared func setupDomain(request: SetupDomainRequest): async Result<DomainInfo, ErrorType> {
    if (not isValidDomain(request.domain)) {
      return #err(#InvalidDomain);
    };

    switch (domainIndex.get(request.domain)) {
      case (?_) return #err(#DomainExists);
      case (null) {};
    };

    let domainId = generateDomainId();
    let now = Time.now();
    let verificationRecord = generateVerificationRecord(request.domain, request.projectId);

    let domain: DomainInfo = {
      id = domainId;
      projectId = request.projectId;
      userId = request.userId;
      domain = request.domain;
      status = #Pending;
      canisterUrl = ?request.canisterUrl;
      verificationRecord = ?verificationRecord;
      verifiedAt = null;
      createdAt = now;
      updatedAt = now;
    };

    domains.put(domainId, domain);
    domainIndex.put(request.domain, domainId);

    // Add to project's domain list
    switch (projectDomains.get(request.projectId)) {
      case (null) {
        let domainList = Buffer.Buffer<DomainId>(1);
        domainList.add(domainId);
        projectDomains.put(request.projectId, domainList);
      };
      case (?domainList) {
        domainList.add(domainId);
      };
    };

    #ok(domain);
  };

  public shared func getDomain(domainId: DomainId): async Result<DomainInfo, ErrorType> {
    switch (domains.get(domainId)) {
      case (null) return #err(#NotFound);
      case (?domain) #ok(domain);
    };
  };

  public shared func getDomainByName(domainName: Text): async Result<DomainInfo, ErrorType> {
    switch (domainIndex.get(domainName)) {
      case (null) return #err(#NotFound);
      case (?domainId) {
        switch (domains.get(domainId)) {
          case (null) return #err(#NotFound);
          case (?domain) #ok(domain);
        };
      };
    };
  };

  public shared func getProjectDomains(projectId: ProjectId): async [DomainInfo] {
    switch (projectDomains.get(projectId)) {
      case (null) [];
      case (?domainList) {
        Array.map<DomainId, DomainInfo>(
          Buffer.toArray(domainList),
          func(domainId: DomainId): DomainInfo {
            switch (domains.get(domainId)) {
              case (null) {
                {
                  id = domainId;
                  projectId = projectId;
                  userId = 0;
                  domain = "unknown";
                  status = #Failed;
                  canisterUrl = null;
                  verificationRecord = null;
                  verifiedAt = null;
                  createdAt = 0;
                  updatedAt = 0;
                };
              };
              case (?domain) domain;
            };
          }
        );
      };
    };
  };

  public shared func verifyDomain(domainId: DomainId, userId: UserId, verificationRecord: Text): async Result<DomainInfo, ErrorType> {
    switch (domains.get(domainId)) {
      case (null) return #err(#NotFound);
      case (?domain) {
        if (domain.userId != userId) {
          return #err(#Unauthorized);
        };

        // In production, would actually check DNS records
        let expectedRecord = switch (domain.verificationRecord) {
          case (null) "";
          case (?record) record;
        };

        if (verificationRecord != expectedRecord) {
          return #err(#VerificationFailed);
        };

        let now = Time.now();
        let updatedDomain = {
          domain with
          status = #Verified;
          verifiedAt = ?now;
          updatedAt = now;
        };

        domains.put(domainId, updatedDomain);

        #ok(updatedDomain);
      };
    };
  };

  public shared func getDNSRecords(domainId: DomainId): async Result<[DNSRecord], ErrorType> {
    switch (domains.get(domainId)) {
      case (null) return #err(#NotFound);
      case (?domain) {
        let canisterUrl = switch (domain.canisterUrl) {
          case (null) "";
          case (?url) url;
        };

        let records = generateDNSRecords(domain.domain, canisterUrl);
        #ok(records);
      };
    };
  };

  public shared func deleteDomain(domainId: DomainId, userId: UserId): async Result<(), ErrorType> {
    switch (domains.get(domainId)) {
      case (null) return #err(#NotFound);
      case (?domain) {
        if (domain.userId != userId) {
          return #err(#Unauthorized);
        };

        domains.delete(domainId);
        domainIndex.delete(domain.domain);

        // Remove from project's domain list
        switch (projectDomains.get(domain.projectId)) {
          case (null) {};
          case (?domainList) {
            let filtered = Buffer.Buffer<DomainId>(1);
            for (id in Iter.fromArray(Buffer.toArray(domainList))) {
              if (id != domainId) {
                filtered.add(id);
              };
            };
            if (filtered.size() > 0) {
              projectDomains.put(domain.projectId, filtered);
            } else {
              projectDomains.delete(domain.projectId);
            };
          };
        };

        #ok(());
      };
    };
  };

  public shared func updateDomainCanisterUrl(domainId: DomainId, userId: UserId, newCanisterUrl: Text): async Result<DomainInfo, ErrorType> {
    switch (domains.get(domainId)) {
      case (null) return #err(#NotFound);
      case (?domain) {
        if (domain.userId != userId) {
          return #err(#Unauthorized);
        };

        let updatedDomain = {
          domain with
          canisterUrl = ?newCanisterUrl;
          updatedAt = Time.now();
        };

        domains.put(domainId, updatedDomain);

        #ok(updatedDomain);
      };
    };
  };

  public query func getDomainCount(): async Nat {
    domains.size();
  };

  public query func getStats(): async {
    totalDomains: Nat;
    verifiedDomains: Nat;
    pendingDomains: Nat;
  } {
    var verifiedDomains = 0;
    var pendingDomains = 0;

    for (domain in Iter.map<(DomainId, DomainInfo), DomainInfo>(
      domains.entries(),
      func((_, d)) { d }
    )) {
      if (domain.status == #Verified) {
        verifiedDomains += 1;
      };
      if (domain.status == #Pending) {
        pendingDomains += 1;
      };
    };

    {
      totalDomains = domains.size();
      verifiedDomains = verifiedDomains;
      pendingDomains = pendingDomains;
    };
  };
};
