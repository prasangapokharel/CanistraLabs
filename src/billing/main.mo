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

/// Billing Canister
/// Manages user wallets, cycle balances, funding, and billing operations
/// Replaces Python Wallet service

module Billing {
  public type UserId = Nat32;
  public type CanisterId = Text;
  public type Timestamp = Nat64;
  public type Cycles = Nat64;
  public type Result<T, E> = Result.Result<T, E>;

  public type WalletInfo = {
    userId: UserId;
    principal: Principal;
    accountId: Text;
    cycleBalance: Cycles;
    usdBalance: Float;
    createdAt: Timestamp;
    updatedAt: Timestamp;
  };

  public type TransactionType = {
    #Deposit;
    #Withdrawal;
    #Burn;
    #Transfer;
    #Refund;
  };

  public type Transaction = {
    id: Text;
    userId: UserId;
    transactionType: TransactionType;
    amount: Cycles;
    description: ?Text;
    canisterId: ?CanisterId;
    timestamp: Timestamp;
    status: TransactionStatus;
  };

  public type TransactionStatus = {
    #Pending;
    #Completed;
    #Failed;
    #Cancelled;
  };

  public type FundingRequest = {
    userId: UserId;
    amount: Cycles;
    source: FundingSource;
  };

  public type FundingSource = {
    #ICP: {
      amount: Nat64; // in e8s (smallest ICP unit)
      accountId: Text;
    };
    #TestnetCycles: {
      amount: Cycles;
      faucetId: Text;
    };
    #Credit: {
      amount: Cycles;
      promoCode: ?Text;
    };
  };

  public type ErrorType = {
    #NotFound;
    #Unauthorized;
    #InsufficientBalance;
    #InvalidAmount;
    #TransactionFailed;
    #CanisterNotFound;
    #InternalError;
  };

  stable var transactionIdCounter: Nat = 1;

  let wallets = HashMap.HashMap<UserId, WalletInfo>(20, Nat32.equal, Nat32.toNat);
  let principals = HashMap.HashMap<Principal, UserId>(20, Principal.equal, Principal.hash);
  let transactions = HashMap.HashMap<Text, Transaction>(50, Text.equal, Text.hash);
  let userTransactions = HashMap.HashMap<UserId, [Text]>(20, Nat32.equal, Nat32.toNat);
  let canisterBudgets = HashMap.HashMap<CanisterId, Cycles>(20, Text.equal, Text.hash);

  private func generateTransactionId(): Text {
    let id = transactionIdCounter;
    transactionIdCounter += 1;
    "tx-" # Nat.toText(id);
  };

  private func convertICPToCycles(icpAmount: Nat64): Cycles {
    // 1 ICP = 1 trillion cycles (10^12)
    // 1 e8 (ICP's smallest unit) = 10^4 cycles
    icpAmount * 10_000;
  };

  private func convertCyclesToUSD(cycles: Cycles): Float {
    // Approximate: 1 trillion cycles ≈ $1 USD
    let cyclesAsFloat = Float.fromInt(Int.fromNat64(cycles));
    cyclesAsFloat / 1_000_000_000_000.0;
  };

  public shared func initializeWallet(userId: UserId, principal: Principal, accountId: Text): async Result<WalletInfo, ErrorType> {
    switch (wallets.get(userId)) {
      case (?_) return #err(#InternalError); // Wallet already exists
      case (null) {
        let now = Time.now();
        let wallet: WalletInfo = {
          userId = userId;
          principal = principal;
          accountId = accountId;
          cycleBalance = 0;
          usdBalance = 0.0;
          createdAt = now;
          updatedAt = now;
        };

        wallets.put(userId, wallet);
        principals.put(principal, userId);

        #ok(wallet);
      };
    };
  };

  public shared func getWallet(userId: UserId): async Result<WalletInfo, ErrorType> {
    switch (wallets.get(userId)) {
      case (null) return #err(#NotFound);
      case (?wallet) #ok(wallet);
    };
  };

  public shared func getWalletByPrincipal(principal: Principal): async Result<WalletInfo, ErrorType> {
    switch (principals.get(principal)) {
      case (null) return #err(#NotFound);
      case (?userId) {
        switch (wallets.get(userId)) {
          case (null) return #err(#NotFound);
          case (?wallet) #ok(wallet);
        };
      };
    };
  };

  public shared func fundWallet(request: FundingRequest): async Result<Transaction, ErrorType> {
    switch (wallets.get(request.userId)) {
      case (null) return #err(#NotFound);
      case (?wallet) {
        let transactionId = generateTransactionId();
        let now = Time.now();

        let (cycles, description) = switch (request.source) {
          case (#ICP({ amount; accountId })) {
            (convertICPToCycles(amount), ?"Funded with ICP from account " # accountId);
          };
          case (#TestnetCycles({ amount; faucetId })) {
            (amount, ?"Funded from testnet cycles faucet");
          };
          case (#Credit({ amount; promoCode })) {
            let promoDesc = switch (promoCode) {
              case (null) "Credit applied";
              case (?code) "Promo code " # code # " applied";
            };
            (amount, ?promoDesc);
          };
        };

        let transaction: Transaction = {
          id = transactionId;
          userId = request.userId;
          transactionType = #Deposit;
          amount = cycles;
          description = description;
          canisterId = null;
          timestamp = now;
          status = #Completed;
        };

        transactions.put(transactionId, transaction);

        let updatedWallet = {
          wallet with
          cycleBalance = wallet.cycleBalance + cycles;
          usdBalance = convertCyclesToUSD(wallet.cycleBalance + cycles);
          updatedAt = now;
        };

        wallets.put(request.userId, updatedWallet);

        #ok(transaction);
      };
    };
  };

  public shared func burnCycles(userId: UserId, canisterId: CanisterId, amount: Cycles): async Result<Transaction, ErrorType> {
    if (amount == 0) {
      return #err(#InvalidAmount);
    };

    switch (wallets.get(userId)) {
      case (null) return #err(#NotFound);
      case (?wallet) {
        if (wallet.cycleBalance < amount) {
          return #err(#InsufficientBalance);
        };

        let transactionId = generateTransactionId();
        let now = Time.now();

        let transaction: Transaction = {
          id = transactionId;
          userId = userId;
          transactionType = #Burn;
          amount = amount;
          description = ?"Cycles burned for canister operation";
          canisterId = ?canisterId;
          timestamp = now;
          status = #Completed;
        };

        transactions.put(transactionId, transaction);

        let updatedWallet = {
          wallet with
          cycleBalance = wallet.cycleBalance - amount;
          usdBalance = convertCyclesToUSD(wallet.cycleBalance - amount);
          updatedAt = now;
        };

        wallets.put(userId, updatedWallet);

        #ok(transaction);
      };
    };
  };

  public shared func allocateCyclesToCanister(userId: UserId, canisterId: CanisterId, cycles: Cycles): async Result<(), ErrorType> {
    if (cycles == 0) {
      return #err(#InvalidAmount);
    };

    switch (wallets.get(userId)) {
      case (null) return #err(#NotFound);
      case (?wallet) {
        if (wallet.cycleBalance < cycles) {
          return #err(#InsufficientBalance);
        };

        canisterBudgets.put(canisterId, cycles);

        let transactionId = generateTransactionId();
        let now = Time.now();

        let transaction: Transaction = {
          id = transactionId;
          userId = userId;
          transactionType = #Transfer;
          amount = cycles;
          description = ?"Cycles allocated to canister";
          canisterId = ?canisterId;
          timestamp = now;
          status = #Completed;
        };

        transactions.put(transactionId, transaction);

        let updatedWallet = {
          wallet with
          cycleBalance = wallet.cycleBalance - cycles;
          usdBalance = convertCyclesToUSD(wallet.cycleBalance - cycles);
          updatedAt = now;
        };

        wallets.put(userId, updatedWallet);

        #ok(());
      };
    };
  };

  public shared func getCanisterBudget(canisterId: CanisterId): async ?Cycles {
    canisterBudgets.get(canisterId);
  };

  public shared func getTransactionHistory(userId: UserId, limit: Nat): async [Transaction] {
    let txIds = switch (userTransactions.get(userId)) {
      case (null) [];
      case (?ids) ids;
    };

    let txArray = Array.tabulate<Transaction>(
      Nat.min(limit, txIds.size()),
      func(i: Nat): Transaction {
        switch (transactions.get(txIds[i])) {
          case (null) {
            {
              id = "unknown";
              userId = userId;
              transactionType = #Deposit;
              amount = 0;
              description = null;
              canisterId = null;
              timestamp = 0;
              status = #Failed;
            };
          };
          case (?tx) tx;
        };
      }
    );

    txArray;
  };

  public query func getStats(): async {
    totalWallets: Nat;
    totalTransactions: Nat;
    totalCycles: Nat64;
  } {
    var totalCycles: Nat64 = 0;
    for (wallet in Iter.map<(UserId, WalletInfo), WalletInfo>(
      wallets.entries(),
      func((_, w)) { w }
    )) {
      totalCycles += wallet.cycleBalance;
    };

    {
      totalWallets = wallets.size();
      totalTransactions = transactions.size();
      totalCycles = totalCycles;
    };
  };

  public query func getCycleRate(): async { ratePerCycle: Float } {
    {
      ratePerCycle = 0.0000000010; // $1e-9 per cycle
    };
  };
};
