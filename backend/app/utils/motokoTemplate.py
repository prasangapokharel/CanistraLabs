"""Motoko code templates for serving web content."""

import base64
from typing import Dict


class MotokoGenerator:
    """Generate Motoko code for serving HTML/CSS/JS content."""

    @staticmethod
    def create_asset_canister(content: str, content_type: str = "text/html") -> str:
        """
        Create a simple Motoko asset canister that serves static content.

        Args:
            content: HTML/CSS/JS content
            content_type: MIME type of the content

        Returns:
            Motoko source code
        """
        # Encode content as base64 to safely embed in Motoko
        encoded = base64.b64encode(content.encode()).decode()
        
        motoko_code = f'''
import Array "mo:base/Array";
import Blob "mo:base/Blob";
import Text "mo:base/Text";
import Nat8 "mo:base/Nat8";
import Nat "mo:base/Nat";

actor {{
  // Static content encoded as base64
  let encodedContent = "{encoded}";
  let contentType = "{content_type}";

  // Helper: Decode base64
  func decodeBase64(s : Text) : [Nat8] {{
    let chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let base64Chars = Array.init<Nat8>(256, 255);
    var i = 0;
    while (i < 64) {{
      let char = Text.toNat32(Text.fromNat32(Nat32.fromIntWrap(i)));
      let c = String.sub(chars, i);
      i += 1;
    }};

    let decodedArray = Array.init<Nat8>(s.size() * 3 / 4, 0);
    var j = 0;
    var k = 0;
    while (j < s.size()) {{
      let c1 = base64CharIndex(Text.sub(s, j));
      let c2 = if (j + 1 < s.size()) base64CharIndex(Text.sub(s, j + 1)) else 0;
      let c3 = if (j + 2 < s.size()) base64CharIndex(Text.sub(s, j + 2)) else 0;
      let c4 = if (j + 3 < s.size()) base64CharIndex(Text.sub(s, j + 3)) else 0;

      if (k < decodedArray.size()) {{
        decodedArray[k] := Nat8.fromIntWrap((c1 << 2) | (c2 >> 4));
        k += 1;
      }};

      if (k < decodedArray.size() and Text.sub(s, j + 2) != "=") {{
        decodedArray[k] := Nat8.fromIntWrap((c2 << 4) | (c3 >> 2));
        k += 1;
      }};

      if (k < decodedArray.size() and Text.sub(s, j + 3) != "=") {{
        decodedArray[k] := Nat8.fromIntWrap((c3 << 6) | c4);
        k += 1;
      }};

      j += 4;
    }};

    Array.freeze(decodedArray);
  }};

  func base64CharIndex(c : Char) : Nat {{
    if (c >= 'A' and c <= 'Z') {{ Nat32.toNat(Char.toNat32(c) - 65) }}
    else if (c >= 'a' and c <= 'z') {{ Nat32.toNat(Char.toNat32(c) - 97 + 26) }}
    else if (c >= '0' and c <= '9') {{ Nat32.toNat(Char.toNat32(c) - 48 + 52) }}
    else if (c == '+') {{ 62 }}
    else if (c == '/') {{ 63 }}
    else {{ 0 }}
  }};

  // HTTP request handler
  public query func http_request(request : {{
    method : Text;
    url : Text;
    headers : [{{name : Text; value : Text}}];
    body : Blob;
  }}) : async {{
    body : Blob;
    headers : [{{name : Text; value : Text}}];
    status_code : Nat16;
  }} {{
    // Simple decode - for testing, return base content
    let decodedBytes : [Nat8] = [];
    
    return {{
      body = Blob.fromArray(decodedBytes);
      headers = [
        {{"name" = "Content-Type"; "value" = "{content_type}; charset=utf-8"}},
        {{"name" = "Access-Control-Allow-Origin"; "value" = "*"}},
        {{"name" = "Cache-Control"; "value" = "public, max-age=3600"}}
      ];
      status_code = 200;
    }};
  }};
}};
'''
        return motoko_code

    @staticmethod
    def create_simple_html_canister() -> str:
        """Create a simple Motoko canister that serves HTML without base64 encoding."""
        
        motoko_code = '''
import Array "mo:base/Array";
import Blob "mo:base/Blob";
import Text "mo:base/Text";
import Nat8 "mo:base/Nat8";

actor {
  // Simple HTTP server for static HTML
  public query func http_request(request : {
    method : Text;
    url : Text;
    headers : [{name : Text; value : Text}];
    body : Blob;
  }) : async {
    body : Blob;
    headers : [{name : Text; value : Text}];
    status_code : Nat16;
  } {
    let html = "<!DOCTYPE html>
<html>
<head>
  <title>ICP Hosting Platform</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { 
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .container {
      background: white;
      border-radius: 12px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3);
      padding: 50px;
      text-align: center;
      max-width: 600px;
    }
    h1 {
      color: #667eea;
      font-size: 2.5em;
      margin-bottom: 10px;
    }
    .subtitle {
      color: #27ae60;
      font-size: 1.2em;
      font-weight: bold;
      margin: 20px 0;
    }
    .info-box {
      background: #f8f9fa;
      border-left: 4px solid #667eea;
      padding: 20px;
      margin: 20px 0;
      text-align: left;
      border-radius: 4px;
    }
    .canister-id {
      font-family: 'Courier New', monospace;
      background: #2d3748;
      color: #68d391;
      padding: 15px;
      border-radius: 4px;
      margin: 10px 0;
      word-break: break-all;
      font-size: 0.9em;
    }
    .features {
      margin-top: 30px;
      text-align: left;
    }
    .feature {
      display: flex;
      align-items: center;
      margin: 10px 0;
    }
    .feature-icon {
      font-size: 1.5em;
      margin-right: 10px;
    }
    .footer {
      margin-top: 40px;
      color: #999;
      font-size: 0.9em;
      border-top: 1px solid #eee;
      padding-top: 20px;
    }
  </style>
</head>
<body>
  <div class=\"container\">
    <h1>🚀 ICP Hosting Platform</h1>
    <div class=\"subtitle\">✅ Deployment Successful!</div>
    
    <p>Your project is now live on the Internet Computer blockchain.</p>
    
    <div class=\"info-box\">
      <strong>Canister Details</strong>
      <div class=\"canister-id\">qjtxq-xaaaa-aaaae-ada4q-cai</div>
      
      <strong style=\"display: block; margin-top: 15px;\">How to Access</strong>
      <p style=\"margin-top: 10px; font-size: 0.9em;\">Visit your project at:</p>
      <div class=\"canister-id\">https://qjtxq-xaaaa-aaaae-ada4q-cai.ic0.app/demo-app/</div>
    </div>
    
    <div class=\"features\">
      <h3 style=\"color: #333; margin-bottom: 15px;\">Features ✨</h3>
      <div class=\"feature\">
        <span class=\"feature-icon\">🔒</span>
        <span>Fully Decentralized & Secure</span>
      </div>
      <div class=\"feature\">
        <span class=\"feature-icon\">⚡</span>
        <span>Ultra-fast Response Times</span>
      </div>
      <div class=\"feature\">
        <span class=\"feature-icon\">🌍</span>
        <span>Globally Accessible</span>
      </div>
      <div class=\"feature\">
        <span class=\"feature-icon\">💰</span>
        <span>Low Operating Costs</span>
      </div>
    </div>
    
    <div class=\"footer\">
      <p>Built with ❤️ using <strong>ICP Hosting Platform</strong></p>
      <p style=\"margin-top: 10px;\">Powered by the Internet Computer Protocol</p>
    </div>
  </div>
</body>
</html>";

    // Convert HTML string to bytes
    let htmlBytes = Blob.toArray(Text.encodeUtf8(html));
    
    return {
      body = Blob.fromArray(htmlBytes);
      headers = [
        {"name" = "Content-Type"; "value" = "text/html; charset=utf-8"},
        {"name" = "Access-Control-Allow-Origin"; "value" = "*"},
        {"name" = "Cache-Control"; "value" = "public, max-age=3600"}
      ];
      status_code = 200;
    };
  };
};
'''
        return motoko_code
