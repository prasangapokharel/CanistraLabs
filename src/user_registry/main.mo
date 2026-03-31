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
import Blob "mo:base/Blob";
import Crypto "mo:base/Crypto";

/// User Registry Canister
/// Manages user identities, authentication tokens, and profile information
/// Replaces Python User model and auth service

module UserRegistry {
  public type UserId = Nat32;
  public type Principal = Principal;
  public type Timestamp = Nat64;
  public type Result<T, E> = Result.Result<T, E>;

  public type AuthToken = {
    accessToken: Text;
    refreshToken: Text;
    expiresAt: Timestamp;
    createdAt: Timestamp;
  };

  public type UserProfile = {
    id: UserId;
    principal: Principal;
    email: Text;
    emailVerified: Bool;
    displayName: ?Text;
    avatar: ?Text;
    createdAt: Timestamp;
    updatedAt: Timestamp;
  };

  public type UserState = {
    id: UserId;
    principal: Principal;
    email: Text;
    passwordHash: Text;
    emailVerified: Bool;
    displayName: ?Text;
    avatar: ?Text;
    createdAt: Timestamp;
    updatedAt: Timestamp;
    lastLogin: ?Timestamp;
    accountId: Text; // ICP account ID derived from principal
  };

  public type SignupRequest = {
    email: Text;
    password: Text;
    displayName: ?Text;
  };

  public type LoginRequest = {
    email: Text;
    password: Text;
  };

  public type ErrorType = {
    #NotFound;
    #UserExists;
    #InvalidEmail;
    #WeakPassword;
    #IncorrectPassword;
    #InvalidToken;
    #Unauthorized;
    #InternalError;
  };

  stable var userIdCounter: UserId = 1;
  let users = HashMap.HashMap<UserId, UserState>(10, Nat32.equal, Nat32.toNat);
  let emailIndex = HashMap.HashMap<Text, UserId>(10, Text.equal, Text.hash);
  let principalIndex = HashMap.HashMap<Principal, UserId>(10, Principal.equal, Principal.hash);
  let activeTokens = HashMap.HashMap<Text, (UserId, Timestamp)>(20, Text.equal, Text.hash);

  private func generateUserId(): UserId {
    let id = userIdCounter;
    userIdCounter += 1;
    id;
  };

  private func isValidEmail(email: Text): Bool {
    let emailPattern = #text("@");
    Text.contains(email, emailPattern);
  };

  private func isStrongPassword(password: Text): Bool {
    Text.size(password) >= 8;
  };

  private func hashPassword(password: Text): Text {
    // In production, use proper bcrypt or Argon2
    // For now, use SHA256
    let bytes = Blob.fromArray(Iter.toArray(Text.toIter(password)));
    let hash = Crypto.SHA256(bytes);
    Blob.toHex(hash);
  };

  private func verifyPassword(password: Text, hash: Text): Bool {
    hashPassword(password) == hash;
  };

  private func generateToken(): Text {
    let random = Crypto.randomBytes(32);
    Blob.toHex(random);
  };

  private func computeAccountId(principal: Principal): Text {
    // Simplified account ID computation
    // In production, use proper CRC32 checksum algorithm
    let principalText = Principal.toText(principal);
    principalText;
  };

  public shared({ caller }) func signup(request: SignupRequest): async Result<AuthToken, ErrorType> {
    if (not isValidEmail(request.email)) {
      return #err(#InvalidEmail);
    };

    if (not isStrongPassword(request.password)) {
      return #err(#WeakPassword);
    };

    switch (emailIndex.get(request.email)) {
      case (?_) return #err(#UserExists);
      case (null) {};
    };

    let userId = generateUserId();
    let now = Time.now();
    let accountId = computeAccountId(caller);
    let passwordHash = hashPassword(request.password);

    let user: UserState = {
      id = userId;
      principal = caller;
      email = request.email;
      passwordHash = passwordHash;
      emailVerified = false;
      displayName = request.displayName;
      avatar = null;
      createdAt = now;
      updatedAt = now;
      lastLogin = ?now;
      accountId = accountId;
    };

    users.put(userId, user);
    emailIndex.put(request.email, userId);
    principalIndex.put(caller, userId);

    let accessToken = generateToken();
    let refreshToken = generateToken();
    let expiresAt = now + (24 * 60 * 60 * 1_000_000_000); // 24 hours

    activeTokens.put(accessToken, (userId, expiresAt));
    activeTokens.put(refreshToken, (userId, now + (7 * 24 * 60 * 60 * 1_000_000_000))); // 7 days

    #ok({
      accessToken = accessToken;
      refreshToken = refreshToken;
      expiresAt = expiresAt;
      createdAt = now;
    });
  };

  public shared({ caller }) func login(request: LoginRequest): async Result<AuthToken, ErrorType> {
    switch (emailIndex.get(request.email)) {
      case (null) return #err(#NotFound);
      case (?userId) {
        switch (users.get(userId)) {
          case (null) return #err(#InternalError);
          case (?user) {
            if (not verifyPassword(request.password, user.passwordHash)) {
              return #err(#IncorrectPassword);
            };

            let now = Time.now();
            let updatedUser = {
              user with
              lastLogin = ?now;
            };
            users.put(userId, updatedUser);

            let accessToken = generateToken();
            let refreshToken = generateToken();
            let expiresAt = now + (24 * 60 * 60 * 1_000_000_000);

            activeTokens.put(accessToken, (userId, expiresAt));
            activeTokens.put(refreshToken, (userId, now + (7 * 24 * 60 * 60 * 1_000_000_000)));

            #ok({
              accessToken = accessToken;
              refreshToken = refreshToken;
              expiresAt = expiresAt;
              createdAt = now;
            });
          };
        };
      };
    };
  };

  public shared func verifyToken(token: Text): async Result<UserId, ErrorType> {
    let now = Time.now();
    switch (activeTokens.get(token)) {
      case (null) return #err(#InvalidToken);
      case (?(userId, expiresAt)) {
        if (now > expiresAt) {
          activeTokens.delete(token);
          return #err(#InvalidToken);
        };
        #ok(userId);
      };
    };
  };

  public shared({ caller }) func refreshToken(token: Text): async Result<AuthToken, ErrorType> {
    switch (await verifyToken(token)) {
      case (#err(e)) return #err(e);
      case (#ok(userId)) {
        switch (users.get(userId)) {
          case (null) return #err(#InternalError);
          case (?user) {
            let now = Time.now();
            let accessToken = generateToken();
            let expiresAt = now + (24 * 60 * 60 * 1_000_000_000);

            activeTokens.put(accessToken, (userId, expiresAt));

            #ok({
              accessToken = accessToken;
              refreshToken = token;
              expiresAt = expiresAt;
              createdAt = now;
            });
          };
        };
      };
    };
  };

  public shared func getProfile(userId: UserId): async Result<UserProfile, ErrorType> {
    switch (users.get(userId)) {
      case (null) return #err(#NotFound);
      case (?user) {
        #ok({
          id = user.id;
          principal = user.principal;
          email = user.email;
          emailVerified = user.emailVerified;
          displayName = user.displayName;
          avatar = user.avatar;
          createdAt = user.createdAt;
          updatedAt = user.updatedAt;
        });
      };
    };
  };

  public shared func getUserByPrincipal(principal: Principal): async Result<UserProfile, ErrorType> {
    switch (principalIndex.get(principal)) {
      case (null) return #err(#NotFound);
      case (?userId) {
        await getProfile(userId);
      };
    };
  };

  public shared({ caller }) func updateProfile(userId: UserId, displayName: ?Text, avatar: ?Text): async Result<UserProfile, ErrorType> {
    switch (users.get(userId)) {
      case (null) return #err(#NotFound);
      case (?user) {
        if (user.principal != caller) {
          return #err(#Unauthorized);
        };

        let updatedUser = {
          user with
          displayName = displayName;
          avatar = avatar;
          updatedAt = Time.now();
        };

        users.put(userId, updatedUser);

        #ok({
          id = updatedUser.id;
          principal = updatedUser.principal;
          email = updatedUser.email;
          emailVerified = updatedUser.emailVerified;
          displayName = updatedUser.displayName;
          avatar = updatedUser.avatar;
          createdAt = updatedUser.createdAt;
          updatedAt = updatedUser.updatedAt;
        });
      };
    };
  };

  public shared func getAccountId(userId: UserId): async Result<Text, ErrorType> {
    switch (users.get(userId)) {
      case (null) return #err(#NotFound);
      case (?user) #ok(user.accountId);
    };
  };

  public query func getUserCount(): async Nat {
    users.size();
  };

  public query func getStats(): async {
    totalUsers: Nat;
    activeTokens: Nat;
  } {
    {
      totalUsers = users.size();
      activeTokens = activeTokens.size();
    };
  };
};
