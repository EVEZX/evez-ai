#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${OPENCLAW_STATE_DIR:=$HOME/.openclaw}"
: "${OPENCLAW_WORKSPACE_DIR:=$OPENCLAW_STATE_DIR/workspace}"
ENV_FILE="$OPENCLAW_STATE_DIR/openclaw.env"
INCLUDE_PRIVATE=false
if [[ "${1:-}" == "--include-private" ]]; then
  INCLUDE_PRIVATE=true
elif [[ "${1:-}" == "--public-only" || -z "${1:-}" ]]; then
  INCLUDE_PRIVATE=false
else
  echo "Usage: $0 [--public-only|--include-private]" >&2
  exit 2
fi
if [[ -f "$ENV_FILE" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a
fi
mkdir -p "$OPENCLAW_WORKSPACE_DIR/ecosystem" "$OPENCLAW_WORKSPACE_DIR/private"
chmod 700 "$OPENCLAW_WORKSPACE_DIR/private" 2>/dev/null || true
python3 - "$OPENCLAW_WORKSPACE_DIR" "$INCLUDE_PRIVATE" <<'PY'
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

workspace=pathlib.Path(sys.argv[1])
include_private=sys.argv[2].lower()=="true"
token=(os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()
owner="EvezArt"
now=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
headers={"Accept":"application/vnd.github+json","User-Agent":"evez-openclaw-ecosystem-sync"}
if token:
    headers["Authorization"]="Bearer "+token

def gh(path, authed=False):
    url="https://api.github.com"+path
    req=urllib.request.Request(url, headers=headers if (token or not authed) else {k:v for k,v in headers.items() if k!="Authorization"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())

def paged(path):
    out=[]; page=1
    while True:
        sep='&' if '?' in path else '?'
        data=gh(f"{path}{sep}per_page=100&page={page}")
        if not data:
            break
        out.extend(data)
        if len(data)<100:
            break
        page+=1
    return out

def slim_repo(r):
    return {
        "name": r.get("name"),
        "full_name": r.get("full_name"),
        "visibility": r.get("visibility", "private" if r.get("private") else "public"),
        "private": bool(r.get("private")),
        "description": r.get("description") or "",
        "html_url": r.get("html_url"),
        "updated_at": r.get("updated_at"),
        "pushed_at": r.get("pushed_at"),
        "default_branch": r.get("default_branch"),
        "language": r.get("language"),
        "stargazers_count": r.get("stargazers_count",0),
        "forks_count": r.get("forks_count",0),
        "archived": bool(r.get("archived")),
    }

profile=gh(f"/users/{owner}")
public_repos=[slim_repo(r) for r in paged(f"/users/{owner}/repos?type=owner&sort=updated&direction=desc")]
public_repos=sorted(public_repos, key=lambda r: r.get("updated_at") or "", reverse=True)
(ecosystem:=workspace/"ecosystem").mkdir(parents=True, exist_ok=True)
public_payload={
    "generated_at": now,
    "owner": owner,
    "source": "GitHub public API",
    "profile": {
        "login": profile.get("login"),
        "name": profile.get("name"),
        "bio": profile.get("bio"),
        "blog": profile.get("blog"),
        "location": profile.get("location"),
        "html_url": profile.get("html_url"),
        "public_repos": profile.get("public_repos"),
        "created_at": profile.get("created_at"),
        "updated_at": profile.get("updated_at"),
    },
    "accounts": {
        "github": "EvezArt",
        "x_twitter": "@EVEZ666",
        "youtube": "@lordevez",
        "slack_primary_channel": "#all-evez-x",
    },
    "repos": public_repos,
}
(ecosystem/"github-public-repos.json").write_text(json.dumps(public_payload, indent=2)+"\n")

core_names=[
    "evez-openclaw-deploy","openclaw-fork","evezart-openclaw","evez-openclaw-apk","clawbreak","clawbreak-ai","evezstation","nexus","evez-vcl","evez-vcl-core","evez-agentnet","agentvault","evez-os","evez-platform","evez-engine","evez-atlas","evez-autonomous-ledger","evez-skills","disclosure.tools"
]
repo_by_name={r["name"]:r for r in public_repos}
core=[repo_by_name[n] for n in core_names if n in repo_by_name]
# Add active repos not already in core to keep the agent oriented.
for r in public_repos[:25]:
    if r not in core:
        core.append(r)
lines=[
    "# EVEZ Ecosystem Bootstrap",
    "",
    f"Generated: {now}",
    "",
    "## Steven Crawford-Maggard / EvezArt",
    f"- GitHub: EvezArt — {profile.get('public_repos')} public repos",
    "- X/Twitter: @EVEZ666",
    "- YouTube: @lordevez",
    "- Main Slack channel: #all-evez-x",
    "",
    "## Mission",
    "Build open-source AI infrastructure that can deploy, recover, and extend itself: OpenClaw, ClawBreak, EVEZ Station, EVEZ VCL, AgentNet, AgentVault, SDKs, bots, and visual cognition surfaces.",
    "",
    "## Key Repos for OpenClaw Context",
]
for r in core:
    lines.append(f"- `{r['full_name']}` — {r['description'] or 'No description'} (updated {r.get('updated_at')})")
lines += [
    "",
    "## How OpenClaw should use this",
    "- Treat this workspace as the local EVEZ memory seed.",
    "- Prefer real upstream OpenClaw Gateway/Control UI/docs over custom substitute dashboards.",
    "- Use Groq first when configured; keep OpenRouter as a fallback if credits are available.",
    "- Use Lobster for typed workflows and approval-gated automations.",
    "- Keep secret tokens out of git; local private inventory belongs under `workspace/private/` only.",
    "",
]
(workspace/"EVEZ_IDENTITY.md").write_text("\n".join(lines))
(ecosystem/"github-public-repos.md").write_text("\n".join(lines))

if include_private:
    if not token:
        raise SystemExit("--include-private requires GITHUB_TOKEN or GH_TOKEN in environment/openclaw.env")
    all_repos=[slim_repo(r) for r in paged("/user/repos?visibility=all&affiliation=owner&sort=updated&direction=desc")]
    visible=[r for r in all_repos if (r.get("full_name") or "").lower().startswith(owner.lower()+"/")]
    private_payload={
        "generated_at": now,
        "owner": owner,
        "source": "GitHub authenticated API",
        "note": "Local-only inventory. Do not commit this file.",
        "visible_repo_count": len(visible),
        "private_repo_count": sum(1 for r in visible if r.get("private")),
        "repos": visible,
    }
    priv=workspace/"private"
    priv.mkdir(parents=True, exist_ok=True)
    (priv/"github-visible-repos-private.json").write_text(json.dumps(private_payload, indent=2)+"\n")
    os.chmod(priv/"github-visible-repos-private.json", 0o600)
print(json.dumps({"ok": True, "public_repos": len(public_repos), "private_index_written": bool(include_private and token)}, indent=2))
PY
