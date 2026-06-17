import os
import json
import base64
import requests
import functions_framework
from google.cloud import secretmanager
from github import Github, GithubException


def retrieve_token():
    """
    Dynamically pulls the unredacted PAT from Secret Manager memory.
    Ensures zero proximity risk on persistent local disks.
    """
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        raise ValueError("Environment variable GCP_PROJECT_ID missing.")

    secret_path = f"projects/{project_id}/secrets/EVEZ_GITHUB_TOKEN/versions/latest"
    response = client.access_secret_version(request={"name": secret_path})
    return response.payload.data.decode("UTF-8").strip()


@functions_framework.http
def route_signal(request):
    """
    Processes execution intents sent from the AI platform layer.
    """
    if request.method == "OPTIONS":
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Max-Age": "3600"
        }
        return ("", 204, headers)

    headers = {"Access-Control-Allow-Origin": "*"}

    try:
        payload = request.get_json(silent=True)
        if not payload:
            return (json.dumps({"error": "Payload missing validation structure"}), 400, headers)

        action = payload.get("action")
        target_repo = payload.get("repo")

        if not action or not target_repo:
            return (json.dumps({"error": "Parameters 'action' and 'repo' are mandatory"}), 400, headers)

        token = retrieve_token()
        git_client = Github(token)
        repo_instance = git_client.get_repo(target_repo)

        # Vector 1: Full Historical Security Scan Activation
        if action == "audit_all":
            ref = payload.get("ref", "main")
            workflows = repo_instance.get_workflows()
            target_workflow = None
            for wf in workflows:
                if "audit" in wf.name.lower() or "security" in wf.name.lower():
                    target_workflow = wf
                    break
            if not target_workflow:
                return (json.dumps({"error": "No matching active audit-all workflow schema found in repository"}), 404, headers)
            target_workflow.create_dispatch(ref=ref)
            return (json.dumps({"status": "executed", "details": f"Dispatched security workflow baseline execution on {ref}."}), 200, headers)

        # Vector 2: Telemetry Issue Creation
        elif action == "create_issue":
            title = payload.get("title", "Automated Synapse Log Entry")
            body = payload.get("body", "Payload delivered via secure cloud runtime pipeline.")
            issue = repo_instance.create_issue(title=title, body=body)
            return (json.dumps({"status": "success", "issue_id": issue.number, "url": issue.html_url}), 200, headers)

        # Vector 3: List Issues
        elif action == "list_issues":
            state = payload.get("state", "open")
            issues = list(repo_instance.get_issues(state=state))[:20]
            return (json.dumps({
                "status": "ok",
                "issues": [{"number": i.number, "title": i.title, "state": i.state, "url": i.html_url} for i in issues]
            }), 200, headers)

        # Vector 4: Trigger Named Workflow
        elif action == "trigger_workflow":
            workflow_name = payload.get("workflow")
            ref = payload.get("ref", "main")
            inputs = payload.get("inputs", {})
            if not workflow_name:
                return (json.dumps({"error": "workflow parameter required"}), 400, headers)
            workflows = list(repo_instance.get_workflows())
            target_wf = next((w for w in workflows if workflow_name.lower() in w.name.lower() or workflow_name in w.path), None)
            if not target_wf:
                return (json.dumps({"error": f"Workflow '{workflow_name}' not found"}), 404, headers)
            target_wf.create_dispatch(ref=ref, inputs=inputs)
            return (json.dumps({"status": "dispatched", "workflow": target_wf.name}), 200, headers)

        # Vector 5: List Repos
        elif action == "list_repos":
            repos_data = git_client.get_user("EvezArt").get_repos()
            return (json.dumps({
                "repos": [{"name": r.name, "private": r.private, "updated": str(r.updated_at)} for r in list(repos_data)[:30]]
            }), 200, headers)

        # Vector 6: Commit File
        elif action == "commit_file":
            path = payload.get("path")
            content = payload.get("content")
            message = payload.get("message", "Synapse commit")
            branch = payload.get("branch", "main")
            if not path or content is None:
                return (json.dumps({"error": "path and content required"}), 400, headers)
            try:
                existing = repo_instance.get_contents(path, ref=branch)
                repo_instance.update_file(path, message, content, existing.sha, branch=branch)
                result = "updated"
            except GithubException:
                repo_instance.create_file(path, message, content, branch=branch)
                result = "created"
            return (json.dumps({"status": result, "path": path}), 200, headers)

        else:
            return (json.dumps({"error": f"Requested command action '{action}' is unmapped."}), 400, headers)

    except GithubException as ge:
        return (json.dumps({"error": "GitHub API error", "detail": ge.data}), ge.status, headers)
    except Exception as error_instance:
        return (json.dumps({"error": "Execution exception encountered", "diagnostic": str(error_instance)}), 500, headers)
