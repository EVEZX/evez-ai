#!/usr/bin/env python3
"""
X/Twitter OAuth2 Authentication Server
Runs locally, exposed via Cloudflare tunnel.
Steven logs in on his phone → callback hits our server → tokens saved to xurl.
"""
import http.server
import json
import os
import sys
import urllib.parse
import urllib.request
import hashlib
import base64
import secrets
import webbrowser
from pathlib import Path

PORT = 9997
REDIRECT_URI = None  # Set after tunnel is up
STATE = secrets.token_urlsafe(16)
CODE_VERIFIER = secrets.token_urlsafe(32)

# X OAuth2 endpoints
AUTHORIZE_URL = "https://twitter.com/i/oauth2/authorize"
TOKEN_URL = "https://api.twitter.com/2/oauth2/token"

# These will be set from command line args
CLIENT_ID = None
CLIENT_SECRET = None

class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        if parsed.path == "/":
            # Root - show auth link
            auth_url = (
                f"{AUTHORIZE_URL}?response_type=code"
                f"&client_id={CLIENT_ID}"
                f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
                f"&scope=tweet.read%20tweet.write%20users.read%20offline.access"
                f"&state={STATE}"
                f"&code_challenge={CODE_VERIFIER}"
                f"&code_challenge_method=plain"
            )
            html = f"""<!DOCTYPE html>
<html><head><title>EVEZ X Auth</title>
<style>
body {{ background: #0a0a0f; color: #e0e0e0; font-family: monospace; text-align: center; padding: 50px; }}
a {{ color: #ff0040; font-size: 1.5em; display: inline-block; padding: 20px 40px; border: 2px solid #ff0040; border-radius: 8px; text-decoration: none; margin: 20px; }}
a:hover {{ background: #ff0040; color: #fff; }}
h1 {{ color: #ff0040; }}
</style></head><body>
<h1>⚡ EVEZ X Auth</h1>
<p>Click below to authorize EVEZ to post on your X account</p>
<a href="{auth_url}">Authorize @EVEZ666</a>
<p style="color:#666; font-size: 0.8em;">Scopes: tweet.read, tweet.write, users.read, offline.access</p>
</body></html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(html.encode())
            
        elif parsed.path == "/callback":
            # OAuth callback
            if "error" in params:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h1>Error</h1><p>{params['error']}</p>".encode())
                return
            
            code = params.get("code", [None])[0]
            received_state = params.get("state", [None])[0]
            
            if not code:
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"<h1>No code received</h1>")
                return
            
            # Exchange code for token
            token_data = urllib.parse.urlencode({
                "code": code,
                "grant_type": "authorization_code",
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "code_verifier": CODE_VERIFIER,
            }).encode()
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
            }
            
            if CLIENT_SECRET:
                import base64
                basic = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
                headers["Authorization"] = f"Basic {basic}"
            
            req = urllib.request.Request(TOKEN_URL, data=token_data, headers=headers)
            
            try:
                resp = urllib.request.urlopen(req, timeout=30)
                tokens = json.loads(resp.read())
                
                # Configure xurl with the tokens
                self.configure_xurl(tokens)
                
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(b"""<!DOCTYPE html>
<html><head><title>EVEZ X Auth - Success!</title>
<style>body{background:#0a0a0f;color:#0f0;font-family:monospace;text-align:center;padding:50px}h1{font-size:3em}</style></head>
<body><h1>✅ Authorized!</h1><p>EVEZ can now post to X.</p><p>You can close this tab.</p></body></html>""")
                
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(f"<h1>Token exchange failed</h1><p>{e}</p>".encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def configure_xurl(self, tokens):
        """Save tokens to xurl config"""
        # Save access token for xurl
        config_dir = Path.home() / ".xurl"
        config_dir.mkdir(exist_ok=True)
        
        config = {
            "access_token": tokens.get("access_token", ""),
            "refresh_token": tokens.get("refresh_token", ""),
            "token_type": tokens.get("token_type", "bearer"),
            "expires_in": tokens.get("expires_in", 0),
        }
        
        with open(config_dir / "oauth2_tokens.json", "w") as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Tokens saved to {config_dir}/oauth2_tokens.json")
        print(f"✅ Access token: {tokens.get('access_token', '')[:20]}...")
    
    def log_message(self, format, *args):
        print(f"[X-Auth] {args[0]}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 x-auth-server.py <client_id> <client_secret> [redirect_uri]")
        print("\nGet your client_id and client_secret from:")
        print("  https://developer.x.com → Apps → your app → Keys and tokens → OAuth 2.0")
        sys.exit(1)
    
    CLIENT_ID = sys.argv[1]
    CLIENT_SECRET = sys.argv[2]
    REDIRECT_URI = sys.argv[3] if len(sys.argv) > 3 else f"http://localhost:{PORT}/callback"
    
    print("=" * 60)
    print("  🐦 EVEZ X Authentication Server")
    print("=" * 60)
    print(f"  Client ID: {CLIENT_ID[:10]}...")
    print(f"  Redirect URI: {REDIRECT_URI}")
    print(f"  Listening on port {PORT}")
    print(f"  State: {STATE}")
    print(f"\n  Open this URL on your phone to authorize:")
    print(f"  {REDIRECT_URI.rsplit('/', 1)[0]}/")
    print("=" * 60)
    
    server = http.server.HTTPServer(("0.0.0.0", PORT), OAuthHandler)
    server.serve_forever()
