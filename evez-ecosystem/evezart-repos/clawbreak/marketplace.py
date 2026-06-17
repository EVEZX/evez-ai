"""ClawBreak Agent Marketplace — list, deploy, rate, and inspect AI agents."""
import json
import time
import uuid
from pathlib import Path
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
MARKETPLACE_FILE = DATA_DIR / "marketplace.json"

SEED_AGENTS = [
    {
        "id": "agent-research",
        "name": "Research Agent",
        "description": "Deep web research — searches, summarizes, and synthesizes information from multiple sources into structured reports.",
        "system_prompt": "You are a research specialist. Search thoroughly, cite sources, and produce structured findings with key insights highlighted.",
        "tools_allowed": ["search", "shell", "file"],
        "price_monthly": 0,
        "category": "research",
        "author": "EVEZ-OS",
        "ratings": [],
        "deploys": 0,
    },
    {
        "id": "agent-code",
        "name": "Code Agent",
        "description": "Full-stack coding assistant — writes, reviews, debugs, and ships code across any language or framework.",
        "system_prompt": "You are an expert software engineer. Write production-quality code, explain your reasoning, and always test your solutions.",
        "tools_allowed": ["shell", "file", "memory"],
        "price_monthly": 0,
        "category": "development",
        "author": "EVEZ-OS",
        "ratings": [],
        "deploys": 0,
    },
    {
        "id": "agent-writing",
        "name": "Writing Agent",
        "description": "Professional writing — drafts, edits, and polishes content from emails to essays to marketing copy.",
        "system_prompt": "You are a professional writer and editor. Adapt your tone to the audience, be concise, and make every word count.",
        "tools_allowed": ["file", "search"],
        "price_monthly": 9.99,
        "category": "content",
        "author": "EVEZ-OS",
        "ratings": [],
        "deploys": 0,
    },
    {
        "id": "agent-analysis",
        "name": "Analysis Agent",
        "description": "Data analysis — crunches numbers, builds visualizations, and extracts actionable insights from datasets.",
        "system_prompt": "You are a data analyst. Use quantitative reasoning, show your work, and present findings with clear visualizations.",
        "tools_allowed": ["shell", "file", "memory"],
        "price_monthly": 9.99,
        "category": "analytics",
        "author": "EVEZ-OS",
        "ratings": [],
        "deploys": 0,
    },
    {
        "id": "agent-creative",
        "name": "Creative Agent",
        "description": "Creative brainstorming — generates ideas, stories, names, taglines, and creative concepts on demand.",
        "system_prompt": "You are a creative powerhouse. Think divergently, combine unexpected ideas, and produce original content that stands out.",
        "tools_allowed": ["file", "search"],
        "price_monthly": 4.99,
        "category": "creative",
        "author": "EVEZ-OS",
        "ratings": [],
        "deploys": 0,
    },
]


def _load_marketplace() -> list:
    if MARKETPLACE_FILE.exists():
        try:
            return json.loads(MARKETPLACE_FILE.read_text())
        except (json.JSONDecodeError, ValueError):
            pass
    # Seed on first load
    agents = SEED_AGENTS
    _save_marketplace(agents)
    return agents


def _save_marketplace(agents: list):
    MARKETPLACE_FILE.write_text(json.dumps(agents, indent=2))


def _find_agent(agents: list, agent_id: str) -> tuple:
    for i, a in enumerate(agents):
        if a["id"] == agent_id:
            return i, a
    return -1, None


router = APIRouter(prefix="/marketplace", tags=["marketplace"])


@router.get("")
async def list_agents(category: str = None):
    """List all marketplace agents, optionally filtered by category."""
    agents = _load_marketplace()
    if category:
        agents = [a for a in agents if a.get("category") == category]
    # Summary view (no system_prompt)
    out = []
    for a in agents:
        out.append({
            "id": a["id"],
            "name": a["name"],
            "description": a["description"],
            "category": a.get("category", "general"),
            "price_monthly": a.get("price_monthly", 0),
            "author": a.get("author", "unknown"),
            "deploys": a.get("deploys", 0),
            "avg_rating": _avg_rating(a),
            "rating_count": len(a.get("ratings", [])),
        })
    return {"agents": out, "total": len(out)}


@router.get("/agent/{agent_id}")
async def agent_details(agent_id: str):
    """Full agent details including usage stats and ratings."""
    agents = _load_marketplace()
    _, agent = _find_agent(agents, agent_id)
    if not agent:
        return JSONResponse({"error": f"Agent '{agent_id}' not found"}, status_code=404)
    return {
        **agent,
        "avg_rating": _avg_rating(agent),
        "rating_count": len(agent.get("ratings", [])),
    }


@router.post("/deploy")
async def deploy_agent(request: Request):
    """Deploy an agent — creates a runtime config and increments deploy count."""
    body = await request.json()
    agent_id = body.get("agent_id")
    if not agent_id:
        return JSONResponse({"error": "agent_id is required"}, status_code=400)

    agents = _load_marketplace()
    idx, agent = _find_agent(agents, agent_id)
    if agent is None:
        return JSONResponse({"error": f"Agent '{agent_id}' not found"}, status_code=404)

    # Create deployment config
    deploy_id = f"deploy-{uuid.uuid4().hex[:8]}"
    config = {
        "deploy_id": deploy_id,
        "agent_id": agent_id,
        "agent_name": agent["name"],
        "system_prompt": agent["system_prompt"],
        "tools_allowed": agent.get("tools_allowed", []),
        "created_at": time.time(),
        "status": "running",
    }

    # Increment deploy count
    agents[idx]["deploys"] = agents[idx].get("deploys", 0) + 1
    _save_marketplace(agents)

    return {"status": "deployed", "config": config}


@router.post("/agent/{agent_id}/rate")
async def rate_agent(agent_id: str, request: Request):
    """Rate an agent 1-5 stars."""
    body = await request.json()
    stars = body.get("stars")
    review = body.get("review", "")

    if stars is None or not (1 <= stars <= 5):
        return JSONResponse({"error": "stars must be 1-5"}, status_code=400)

    agents = _load_marketplace()
    idx, agent = _find_agent(agents, agent_id)
    if agent is None:
        return JSONResponse({"error": f"Agent '{agent_id}' not found"}, status_code=404)

    rating = {"stars": stars, "review": review, "timestamp": time.time()}
    if "ratings" not in agents[idx]:
        agents[idx]["ratings"] = []
    agents[idx]["ratings"].append(rating)
    _save_marketplace(agents)

    return {
        "status": "rated",
        "agent_id": agent_id,
        "avg_rating": _avg_rating(agents[idx]),
        "rating_count": len(agents[idx]["ratings"]),
    }


def _avg_rating(agent: dict) -> float:
    ratings = agent.get("ratings", [])
    if not ratings:
        return 0.0
    return round(sum(r["stars"] for r in ratings) / len(ratings), 2)
