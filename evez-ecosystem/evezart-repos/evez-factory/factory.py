#!/usr/bin/env python3
"""
EVEZ Factory — Self-Manufacturing Automation Pipeline
Generates, audits, and ships new projects using AI (Groq via Composio).
Zero human intervention. The factory builds products.
"""
import asyncio, json, os, time, logging
from typing import Dict, Optional
from pydantic import BaseModel
import httpx
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("evez-factory")

# ── Config ──────────────────────────────────────────────
class FactoryConfig(BaseModel):
    composio_api_key: str = os.getenv("COMPOSIO_API_KEY", "ck_nGR0xHdPC0mRYoxmoHUo")
    groq_account_id: str = "groqcloud_cheney-larry"
    github_account_id: str = "github_walter-empusa"
    slack_account_id: str = "slack_range-wheel"
    cognition_url: str = "http://127.0.0.1:8081"
    maes_url: str = "http://127.0.0.1:8082"
    github_owner: str = "EvezArt"

class ProjectSpec(BaseModel):
    name: str
    description: str
    type: str = "api"  # api, agent, tool, dashboard
    private: bool = False

# ── Composio Helper ─────────────────────────────────────
COMPOSIO_BASE = "https://backend.composio.dev"

async def composio_exec(tool_slug: str, arguments: dict, account_id: str, api_key: str) -> dict:
    """Execute a Composio tool via the v1 REST API (MCP-compatible)"""
    # Use the MCP streamable-http endpoint
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{COMPOSIO_BASE}/api/v1/tools/execute",
            headers={
                "x-consumer-api-key": api_key,
                "Content-Type": "application/json"
            },
            json={
                "toolSlug": tool_slug,
                "arguments": arguments,
                "accountId": account_id
            }
        )
        try:
            data = r.json()
        except:
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
        
        if "error" in data:
            return {"error": str(data["error"])[:300]}
        return data.get("data", data)

# ── Phase 1: Generate ──────────────────────────────────
async def generate_project_code(spec: ProjectSpec, config: FactoryConfig) -> Dict[str, str]:
    """Use Groq to generate all project files"""
    log.info(f"🧠 Generating code for {spec.name} ({spec.type})...")
    
    prompt = f"""Generate a complete, production-ready {spec.type} project called "{spec.name}".
Description: {spec.description}

Return a JSON object with these exact keys:
- "main.py": The main application file (FastAPI if type=api, CLI if type=tool, etc.)
- "tests/test_main.py": Comprehensive pytest tests
- "config.yaml": Configuration file
- "README.md": Full documentation with usage examples
- "requirements.txt": Python dependencies
- "Dockerfile": Container config

Rules:
- Use FastAPI + uvicorn for APIs
- Use httpx for async HTTP
- Use pydantic for models
- Include error handling and logging
- No placeholders — every function must be complete and working
- Type: {spec.type}
"""

    result = await composio_exec(
        "GROQCLOUD_GROQ_CREATE_CHAT_COMPLETION",
        {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": "You are an expert Python developer. Output ONLY valid JSON with the exact keys requested. No markdown fences."},
                {"role": "user", "content": prompt}
            ],
            "max_completion_tokens": 16000,
            "temperature": 0.2
        },
        config.groq_account_id,
        config.composio_api_key
    )
    
    # Extract the generated content
    if "error" in result:
        log.error(f"Groq generation failed: {result['error']}")
        return {}
    
    choices = result.get("choices", [])
    if not choices:
        log.error("No choices in Groq response")
        return {}
    
    content = choices[0].get("message", {}).get("content", "")
    
    # Parse JSON from the response (handle markdown fences)
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1] if "\n" in content else content[3:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()
    
    try:
        files = json.loads(content)
        log.info(f"✅ Generated {len(files)} files")
        return files
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse generated JSON: {e}")
        # Try to extract JSON from the content
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                files = json.loads(content[start:end])
                log.info(f"✅ Extracted {len(files)} files from response")
                return files
            except:
                pass
        log.error(f"Raw content preview: {content[:300]}")
        return {}

# ── Phase 2: Audit ─────────────────────────────────────
async def audit_generated_code(files: Dict[str, str], spec: ProjectSpec, config: FactoryConfig) -> Dict:
    """Run cognition forensics on all generated code"""
    log.info(f"🔍 Auditing {len(files)} files through Cognition API...")
    audit_results = {}
    
    for path, content in files.items():
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    f"{config.cognition_url}/analyze",
                    json={"output": content[:2000], "agent_id": f"factory-{spec.name}"},
                    headers={"Content-Type": "application/json"}
                )
                result = r.json()
                verdict = result.get("verdict", "UNKNOWN")
                risk = result.get("risk_score", -1)
                audit_results[path] = {"verdict": verdict, "risk_score": risk}
                icon = {"CLEAN": "✅", "SUSPICIOUS": "⚠️", "HIGH_RISK": "🔴", "CRITICAL": "🚨"}.get(verdict, "❓")
                log.info(f"  {icon} {path}: {verdict} (risk={risk})")
        except Exception as e:
            audit_results[path] = {"verdict": "ERROR", "risk_score": -1, "error": str(e)}
            log.warning(f"  ❌ {path}: audit failed - {e}")
    
    # Check if any file is critical
    max_risk = max((r.get("risk_score", 0) for r in audit_results.values()), default=0)
    if max_risk >= 80:
        log.warning(f"🚨 HIGH RISK detected (max={max_risk}). Code needs review before shipping.")
    
    return audit_results

# ── Phase 3: Ship ──────────────────────────────────────
async def ship_to_github(files: Dict[str, str], spec: ProjectSpec, config: FactoryConfig) -> Dict:
    """Create GitHub repo and push generated code"""
    log.info(f"📦 Shipping {spec.name} to GitHub...")
    
    # Step 1: Create the repository
    create_result = await composio_exec(
        "GITHUB_CREATE_A_REPOSITORY_FOR_THE_AUTHENTICATED_USER",
        {
            "name": spec.name,
            "description": spec.description,
            "private": spec.private,
            "auto_init": True,
            "gitignore_template": "Python",
            "has_issues": True,
            "has_wiki": True
        },
        config.github_account_id,
        config.composio_api_key
    )
    
    if "error" in create_result:
        log.error(f"GitHub repo creation failed: {create_result['error']}")
        return {"status": "failed", "error": create_result["error"]}
    
    repo_url = create_result.get("html_url", f"https://github.com/{config.github_owner}/{spec.name}")
    log.info(f"✅ Repo created: {repo_url}")
    
    # Step 2: Commit all generated files
    upserts = []
    for path, content in files.items():
        upserts.append({"path": path, "content": content, "encoding": "utf-8"})
    
    commit_result = await composio_exec(
        "GITHUB_COMMIT_MULTIPLE_FILES",
        {
            "owner": config.github_owner,
            "repo": spec.name,
            "branch": "main",
            "message": f"🤖 Auto-generated by EVEZ Factory\n\nProject: {spec.name}\nType: {spec.type}\nDescription: {spec.description}",
            "upserts": upserts
        },
        config.github_account_id,
        config.composio_api_key
    )
    
    if "error" in commit_result:
        log.error(f"GitHub commit failed: {commit_result['error']}")
        return {"status": "partial", "repo_url": repo_url, "commit_error": commit_result["error"]}
    
    commit_sha = commit_result.get("sha", "unknown")
    log.info(f"✅ Code pushed: {commit_sha}")
    
    return {"status": "shipped", "repo_url": repo_url, "commit_sha": commit_sha}

# ── Phase 4: Report ────────────────────────────────────
async def report_to_slack(spec: ProjectSpec, audit: Dict, ship: Dict, config: FactoryConfig):
    """Post results to Slack"""
    audit_summary = "\n".join(
        f"  • {path}: {r['verdict']} (risk={r['risk_score']})"
        for path, r in audit.items()
    )
    
    status_emoji = "✅" if ship.get("status") == "shipped" else "⚠️"
    
    message = f"""{status_emoji} **EVEZ Factory: {spec.name}**

**Type:** {spec.type} | **Description:** {spec.description}

**Cognition Audit:**
{audit_summary}

**GitHub:** {ship.get('repo_url', 'N/A')}
**Status:** {ship.get('status', 'unknown')}

— *EVEZ Factory (Steven AI)*"""
    
    await composio_exec(
        "SLACK_SEND_MESSAGE",
        {"channel": "general", "markdown_text": message},
        config.slack_account_id,
        config.composio_api_key
    )
    log.info("📡 Reported to Slack")

# ── Phase 5: Log ───────────────────────────────────────
async def log_to_maes(spec: ProjectSpec, audit: Dict, ship: Dict, config: FactoryConfig):
    """Log factory event to MAES"""
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            # Tick the factory agent in MAES
            await client.post(
                f"{config.maes_url}/agents/evez-deploy/tick",
                json={
                    "action": "FACTORY_BUILD",
                    "confidence": 1.0 if ship.get("status") == "shipped" else 0.5,
                    "data": json.dumps({"project": spec.name, "type": spec.type, "status": ship.get("status")})
                },
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        log.warning(f"MAES log failed: {e}")

# ── Main Pipeline ──────────────────────────────────────
async def run_factory(spec: ProjectSpec, config: Optional[FactoryConfig] = None) -> Dict:
    """Run the full factory pipeline: Generate → Audit → Ship → Report"""
    config = config or FactoryConfig()
    start = time.time()
    
    log.info(f"🏭 FACTORY START: {spec.name} ({spec.type})")
    log.info(f"   Description: {spec.description}")
    
    # Phase 1: Generate
    files = await generate_project_code(spec, config)
    if not files:
        return {"status": "failed", "phase": "generate", "error": "No code generated"}
    
    # Phase 2: Audit
    audit = await audit_generated_code(files, spec, config)
    
    # Phase 3: Ship
    ship = await ship_to_github(files, spec, config)
    
    # Phase 4: Report
    await report_to_slack(spec, audit, ship, config)
    
    # Phase 5: Log
    await log_to_maes(spec, audit, ship, config)
    
    elapsed = round(time.time() - start, 1)
    log.info(f"🏭 FACTORY COMPLETE: {spec.name} in {elapsed}s — {ship.get('status', 'unknown')}")
    
    return {
        "status": ship.get("status", "unknown"),
        "project": spec.name,
        "files_generated": len(files),
        "audit_results": audit,
        "github": ship,
        "elapsed_seconds": elapsed
    }

# ── API Server Mode ────────────────────────────────────
def create_api():
    from fastapi import FastAPI, BackgroundTasks
    api = FastAPI(title="EVEZ Factory API", version="1.0.0")
    config = FactoryConfig()
    
    @api.get("/health")
    def health():
        return {"status": "ok", "service": "evez-factory", "ts": int(time.time())}
    
    @api.post("/build")
    async def build(spec: ProjectSpec, background_tasks: BackgroundTasks):
        background_tasks.add_task(run_factory, spec, config)
        return {"status": "queued", "project": spec.name, "type": spec.type}
    
    @api.post("/build/sync")
    async def build_sync(spec: ProjectSpec):
        result = await run_factory(spec, config)
        return result
    
    return api

if __name__ == "__main__":
    import sys
    if "--serve" in sys.argv:
        import uvicorn
        port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else 8891
        uvicorn.run(create_api(), host="127.0.0.1", port=port)
    elif len(sys.argv) >= 3:
        # CLI mode: python factory.py <name> <type> [description]
        spec = ProjectSpec(
            name=sys.argv[1],
            type=sys.argv[2],
            description=sys.argv[3] if len(sys.argv) > 3 else f"Auto-generated {sys.argv[2]} project"
        )
        asyncio.run(run_factory(spec))
    else:
        print("Usage: factory.py <name> <type> [description]")
        print("       factory.py --serve [--port 8891]")
        print("Types: api, agent, tool, dashboard")
