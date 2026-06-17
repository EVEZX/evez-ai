# EvezArt Synapse Engine

**Neural bridge between AI intent and GitHub execution**, running as a stateless Google Cloud Run Function. The GitHub PAT lives exclusively in Secret Manager — never on disk.

## Architecture

```
[AI / Chat]  ──JSON──►  [Cloud Run Function]  ──runtime fetch──►  [Secret Manager]
                              │                                          EVEZ_GITHUB_TOKEN
                              └──authenticated──►  [GitHub API / EvezArt repos]
```

## Quick Deploy

```bash
chmod +x deploy.sh
./deploy.sh YOUR_GCP_PROJECT_ID us-central1
```

## Available Actions

| Action | Required | Description |
|--------|---------|-------------|
| `audit_all` | `repo`, `ref` | Triggers audit/security workflow |
| `create_issue` | `repo`, `title`, `body` | Opens a GitHub issue |
| `list_issues` | `repo` | Lists issues |
| `trigger_workflow` | `repo`, `workflow`, `ref` | Dispatches any named workflow |
| `list_repos` | — | Lists EvezArt repos |
| `commit_file` | `repo`, `path`, `content` | Commits a file |

## Example Payloads

```json
{"action": "audit_all", "repo": "EvezArt/evez-os", "ref": "main"}
```

```json
{"action": "create_issue", "repo": "EvezArt/evez-os", "title": "Synapse Trace", "body": "Pipeline verified."}
```

```json
{"action": "commit_file", "repo": "EvezArt/evez-os", "path": "runtime/status.json", "content": "{\"status\": \"operational\"}", "message": "Update status"}
```
