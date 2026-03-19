import Debug "mo:base/Debug";

actor {
  public func greet(name : Text) : async Text {
    Debug.print("Hello from Motoko!");
    return "Hello, " # name # "!";
  };
}