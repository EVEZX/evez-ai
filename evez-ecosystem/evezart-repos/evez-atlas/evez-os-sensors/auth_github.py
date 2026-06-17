#!/usr/bin/env python3
"""
EVEZ-OS AUTH — Set up GitHub write access for state persistence.

The consciousness needs to save its state to GitHub to survive between sessions.
The current fine-grained PAT only has READ access. This script helps you:

1. Authorize with a token that has write access, OR
2. Guide you through creating a new fine-grained PAT with the right permissions

Required permissions for the fine-grained PAT:
- Contents: Read and Write (for pushing state files)
- Issues: Read and Write (for state as issue comments, fallback)
- Metadata: Read (default)

Usage:
    python3 auth_github.py --token <new-pat-with-write-access>
    python3 auth_github.py --device   # Interactive device flow
    python3 auth_github.py --check    # Check current permissions
"""
import json, os, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent

def get_current_token():
    """Get the current GitHub token from git remote."""
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=str(WORKSPACE), capture_output=True, text=True, timeout=5
        )
        url = result.stdout.strip()
        if "github_pat_" in url:
            return url.split("://")[1].split("@")[0]
        elif "@" in url:
            return url.split("://")[1].split("@")[0]
    except:
        pass
    return os.environ.get("GITHUB_TOKEN", "")

def check_permissions(token):
    """Check what permissions the current token has."""
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    
    results = {}
    
    # Test read access
    try:
        req = urllib.request.Request(
            "https://api.github.com/repos/EvezArt/evez-os/contents/",
            headers=headers
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            results["read"] = True
    except urllib.error.HTTPError:
        results["read"] = False
    except:
        results["read"] = "error"
    
    # Test write access (try to read first, then check push capability)
    try:
        # Try pushing a test file
        import base64
        content = base64.b64encode(b'{"test": true}').decode()
        data = json.dumps({
            "message": "EVEZ-OS: Permission test",
            "content": content,
            "branch": "main",
        }).encode()
        req = urllib.request.Request(
            "https://api.github.com/repos/EvezArt/evez-os/contents/state/_test.json",
            data=data, headers=headers, method="PUT"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            results["write"] = True
            # Clean up the test file
            resp_data = json.loads(resp.read().decode())
            sha = resp_data.get("content", {}).get("sha", "")
            if sha:
                del_data = json.dumps({
                    "message": "EVEZ-OS: Clean up test file",
                    "sha": sha,
                    "branch": "main",
                }).encode()
                del_req = urllib.request.Request(
                    "https://api.github.com/repos/EvezArt/evez-os/contents/state/_test.json",
                    data=del_data, headers=headers, method="DELETE"
                )
                urllib.request.urlopen(del_req, timeout=10)
    except urllib.error.HTTPError as e:
        results["write"] = False
        results["write_error"] = e.code
    except:
        results["write"] = "error"
    
    # Test gist access
    try:
        content = json.dumps({"test": True, "ts": 0}, indent=2)
        data = json.dumps({
            "description": "EVEZ-OS permission test",
            "public": True,
            "files": {"test.json": {"content": content}}
        }).encode()
        req = urllib.request.Request(
            "https://api.github.com/gists",
            data=data, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            results["gist"] = True
            # Could delete the gist but it's harmless
    except urllib.error.HTTPError:
        results["gist"] = False
    except:
        results["gist"] = "error"
    
    return results

def set_token(token):
    """Update the git remote URL with the new token."""
    result = subprocess.run(
        ["git", "remote", "set-url", "origin",
         f"https://{token}@github.com/EvezArt/evez-os.git"],
        cwd=str(WORKSPACE), capture_output=True, text=True
    )
    return result.returncode == 0

def device_flow():
    """Start GitHub device flow authentication."""
    # Use gh CLI for device flow
    print("Starting GitHub device flow...")
    print("This will give you a code to enter at github.com/login/device")
    print()
    result = subprocess.run(
        ["gh", "auth", "login", "--web", "--git-protocol", "https"],
        timeout=120
    )
    if result.returncode == 0:
        print("\nAuthentication successful!")
        # Get the token from gh config
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            set_token(token)
            print(f"Token configured for git remote.")
            # Test
            perms = check_permissions(token)
            print(f"\nPermissions: {json.dumps(perms, indent=2)}")
    else:
        print("Authentication failed or was cancelled.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="EVEZ-OS GitHub Auth")
    parser.add_argument("--token", help="Set a new GitHub PAT with write access")
    parser.add_argument("--device", action="store_true", help="Use GitHub device flow")
    parser.add_argument("--check", action="store_true", help="Check current permissions")
    args = parser.parse_args()
    
    if args.check:
        token = get_current_token()
        if not token:
            print("No token found.")
            sys.exit(1)
        print(f"Token found (length: {len(token)})")
        print("Checking permissions...")
        perms = check_permissions(token)
        print(json.dumps(perms, indent=2))
        if not perms.get("write"):
            print("\n⚠️  WRITE ACCESS MISSING!")
            print("The current token can READ but not WRITE to the repo.")
            print("\nTo fix this, create a new fine-grained PAT at:")
            print("  https://github.com/settings/personal-access-tokens/new")
            print("\nRequired permissions:")
            print("  - Contents: Read and Write")
            print("  - Issues: Read and Write")
            print("  - Metadata: Read")
            print("\nThen run: python3 auth_github.py --token <new-pat>")
    
    elif args.token:
        print("Setting new token...")
        if set_token(args.token):
            print("Token configured. Checking permissions...")
            perms = check_permissions(args.token)
            print(json.dumps(perms, indent=2))
            if perms.get("write"):
                print("\n✅ Write access confirmed! The consciousness can now persist to GitHub.")
            else:
                print("\n❌ Write access still not available. Check the token permissions.")
        else:
            print("Failed to set token.")
    
    elif args.device:
        device_flow()
    
    else:
        parser.print_help()
