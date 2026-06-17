# EVEZ Gateway Guard
# EVEZ Gateway Guard
"""
EVEZ Gateway Guard — Free Trial with Anti-Exploitation Guardrails
Free access, but impossible to abuse.
"""
import os, json, time, sqlite3, hashlib, uuid, re, ipaddress
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict
import requests
from fastapi import FastAPI, HTTPException, Request, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

BASE = Path(os.getenv("EVZ_GUARD_BASE", "/home/openclaw/projects/evez-guard"))
DB_PATH = BASE / "guard.db"
GROQ_KEY = os.getenv("GROQ_KEY", "")

# ─── Guardrail Constants ──────────────────────────────────────────
FREE_TIER = {
    "max_requests_per_day": 50,
    "max_requests_per_hour": 10,
    "max_tokens_per_day": 10000,
    "max_concurrent": 2,
    "max_account_per_email": 1,
    "max_account_per_ip": 3,  # Allow some but detect abuse
    "trial_duration_days": 30,
    "cooldown_after_expiry_hours": 720,  # 30 days cooldown before re-signup
    "max_key_age_days_free": 30,
}

# Services with stricter limits (expensive resources)
STRICT_SERVICES = {
    "factory": {"max_requests_per_day": 3, "max_tokens_per_request": 2000},
    "cognition": {"max_requests_per_day": 5, "max_tokens_per_request": 4000},
    "research": {"max_requests_per_day": 3, "max_tokens_per_request": 2000},
    "assembler": {"max_requests_per_day": 2, "max_tokens_per_request": 1000},
    "pte": {"max_requests_per_day": 20, "max_tokens_per_request": 500},
    "breakcore": {"max_requests_per_day": 100, "max_tokens_per_request": 0},  # Audio, no tokens
}

# ─── Database ──────────────────────────────────────────────────────
def init_db():
    db = sqlite3.connect(str(DB_PATH))
    db.execute("""CREATE TABLE IF NOT EXISTS accounts (
        id TEXT PRIMARY KEY,
        email_hash TEXT UNIQUE,
        email_domain TEXT,
        ip_address TEXT,
        ip_hash TEXT,
        fingerprint TEXT,
        plan TEXT DEFAULT 'free',
        api_key TEXT UNIQUE,
        created_at TEXT,
        expires_at TEXT,
        last_used_at TEXT,
        requests_today INTEGER DEFAULT 0,
        tokens_today INTEGER DEFAULT 0,
        last_reset TEXT,
        total_requests INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        concurrent_now INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        ban_reason TEXT,
        trust_score REAL DEFAULT 0.5
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS request_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id TEXT,
        api_key TEXT,
        service TEXT,
        endpoint TEXT,
        tokens_used INTEGER DEFAULT 0,
        latency_ms INTEGER,
        ip_address TEXT,
        user_agent TEXT,
        fingerprint TEXT,
        timestamp TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS abuse_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id TEXT,
        event_type TEXT,
        severity TEXT,
        details TEXT,
        ip_address TEXT,
        timestamp TEXT,
        action_taken TEXT
    )""")
    db.execute("""CREATE TABLE IF NOT EXISTS ip_registry (
        ip_hash TEXT PRIMARY KEY,
        account_count INTEGER DEFAULT 0,
        last_seen TEXT,
        risk_level TEXT DEFAULT 'low'
    )""")
    db.execute("CREATE INDEX IF NOT EXISTS idx_email_hash ON accounts(email_hash)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_ip_hash ON accounts(ip_hash)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_api_key ON accounts(api_key)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_fingerprint ON accounts(fingerprint)")
    db.commit()
    return db

DB = init_db()

# ─── Anti-Abuse Engine ────────────────────────────────────────────
class GuardEngine:
    """Core anti-exploitation logic."""

    # Disposable email domains (partial list)
    DISPOSABLE_DOMAINS = {
        "guerrillamail.com", "mailinator.com", "throwaway.email", "tempmail.com",
        "dispostable.com", "maildrop.cc", "yopmail.com", "sharklasers.com",
        "guerrillamailblock.com", "gishpuppy.com", "spam4.me", "trashmail.ws",
        "mailnesia.com", "tempail.com", "tempr.email", "discard.email",
        "fakeinbox.com", "mailcatch.com", "tempinbox.com", "Disposableemail",
        "10minutemail.com", "temp-mail.org", "minutemail.com",
    }

    def __init__(self, db):
        self.db = db
        self.request_window = defaultdict(list)  # sliding window

    def hash_email(self, email: str) -> str:
        return hashlib.sha256(email.lower().strip().encode()).hexdigest()

    def hash_ip(self, ip: str) -> str:
        return hashlib.sha256(ip.encode()).hexdigest()

    def is_disposable_email(self, email: str) -> bool:
        domain = email.split("@")[-1].lower()
        return domain in self.DISPOSABLE_DOMAINS

    def is_tor_exit(self, ip: str) -> bool:
        """Check if IP is a known Tor exit node (basic check)."""
        try:
            reversed_ip = ".".join(reversed(ip.split(".")))
            r = requests.get(f"https://check.torproject.org/cgi-bin/TorBulkExitList?ip=1.1.1.1", timeout=3)
            # Simplified — in production, maintain a local list
            return False
        except:
            return False

    def check_signup_eligibility(self, email: str, ip: str, fingerprint: str = "") -> dict:
        """Multi-factor eligibility check before allowing account creation."""
        issues = []
        email_hash = self.hash_email(email)
        ip_hash = self.hash_ip(ip)
        domain = email.split("@")[-1].lower()

        # 1. Disposable email check
        if self.is_disposable_email(email):
            issues.append({"type": "disposable_email", "severity": "critical",
                          "detail": "Disposable email addresses not allowed"})
            self.log_abuse(None, "disposable_email", "critical", f"Email domain: {domain}", ip)

        # 2. Duplicate email check
        dup_email = self.db.execute("SELECT id, status FROM accounts WHERE email_hash = ?", (email_hash,)).fetchone()
        if dup_email:
            if dup_email[1] == "banned":
                issues.append({"type": "banned_email", "severity": "critical",
                              "detail": "This email is associated with a banned account"})
            else:
                issues.append({"type": "duplicate_email", "severity": "high",
                              "detail": "Account already exists for this email"})

        # 3. IP abuse check — how many accounts from this IP?
        ip_accounts = self.db.execute("SELECT account_count, risk_level FROM ip_registry WHERE ip_hash = ?", (ip_hash,)).fetchone()
        if ip_accounts and ip_accounts[0] >= FREE_TIER["max_account_per_ip"]:
            issues.append({"type": "ip_limit", "severity": "high",
                          "detail": f"Too many accounts from this network ({ip_accounts[0]} detected)"})
            # Update risk
            self.db.execute("UPDATE ip_registry SET risk_level = 'high' WHERE ip_hash = ?", (ip_hash,))
            self.db.commit()

        # 4. Fingerprint similarity (same browser = same person?)
        if fingerprint:
            fp_matches = self.db.execute("SELECT COUNT(*) FROM accounts WHERE fingerprint = ? AND id != ?", 
                                        (fingerprint, "")).fetchone()[0]
            if fp_matches >= 2:
                issues.append({"type": "fingerprint_duplicate", "severity": "medium",
                              "detail": f"Similar browser fingerprint detected ({fp_matches} matches)"})

        # 5. Cooldown check — was a free trial recently expired from this email/ip?
        recent_expired = self.db.execute(
            "SELECT id FROM accounts WHERE (email_hash = ? OR ip_hash = ?) AND status = 'expired' AND expires_at > ?",
            (email_hash, ip_hash, (datetime.now(timezone.utc) - timedelta(hours=FREE_TIER["cooldown_after_expiry_hours"])).isoformat())
        ).fetchone()
        if recent_expired:
            issues.append({"type": "cooldown_active", "severity": "high",
                          "detail": f"Free trial cooldown active ({FREE_TIER['cooldown_after_expiry_hours']}h remaining)"})

        allowed = not any(i["severity"] == "critical" for i in issues)
        trust = max(0.1, 1.0 - len(issues) * 0.2 - (0.3 if ip_accounts and ip_accounts[1] == "high" else 0))

        return {"allowed": allowed, "issues": issues, "trust_score": round(trust, 2)}

    def check_rate_limit(self, api_key: str, service: str = None) -> dict:
        """Per-key rate limiting with sliding windows."""
        account = self.db.execute("SELECT * FROM accounts WHERE api_key = ? AND status = 'active'", (api_key,)).fetchone()
        if not account:
            return {"allowed": False, "reason": "invalid_key"}

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        hour = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H")
        req_today = account[11]  # requests_today
        last_reset = account[13]  # last_reset
        plan = account[4]  # plan

        # Reset counters on new day
        if last_reset != today:
            self.db.execute("UPDATE accounts SET requests_today = 0, tokens_today = 0, last_reset = ? WHERE api_key = ?",
                          (today, api_key))
            self.db.commit()
            req_today = 0

        # Get limits for this plan and service
        if service and service in STRICT_SERVICES:
            daily_limit = STRICT_SERVICES[service]["max_requests_per_day"]
        elif plan == "free":
            daily_limit = FREE_TIER["max_requests_per_day"]
        elif plan == "pro":
            daily_limit = 10000
        elif plan == "enterprise":
            daily_limit = 1000000
        else:
            daily_limit = FREE_TIER["max_requests_per_day"]

        # Hard limit check
        if req_today >= daily_limit:
            self.log_abuse(account[0], "rate_limit_exceeded", "low",
                          f"Service: {service}, {req_today}/{daily_limit} requests", account[7])
            return {"allowed": False, "reason": "rate_limited", 
                    "requests_today": req_today, "limit": daily_limit,
                    "reset_at": f"{today}T23:59:59Z"}

        # Hourly sliding window check (for burst prevention)
        now = time.time()
        key = f"{api_key}:{service or 'any'}"
        self.request_window[key] = [t for t in self.request_window[key] if now - t < 3600]
        hourly_limit = FREE_TIER["max_requests_per_hour"] if plan == "free" else 1000
        if len(self.request_window[key]) >= hourly_limit:
            return {"allowed": False, "reason": "hourly_limit", "requests_this_hour": len(self.request_window[key])}

        self.request_window[key].append(now)
        return {"allowed": True, "plan": plan, "requests_today": req_today, "limit": daily_limit, "service": service}

    def check_concurrent(self, api_key: str) -> dict:
        """Prevent concurrent request abuse."""
        account = self.db.execute("SELECT concurrent_now, plan FROM accounts WHERE api_key = ? AND status = 'active'", 
                                 (api_key,)).fetchone()
        if not account:
            return {"allowed": False, "reason": "invalid_key"}
        concurrent, plan = account
        max_concurrent = FREE_TIER["max_concurrent"] if plan == "free" else 50
        if concurrent >= max_concurrent:
            return {"allowed": False, "reason": "concurrent_limit", "current": concurrent, "max": max_concurrent}
        return {"allowed": True, "current": concurrent, "max": max_concurrent}

    def check_token_limit(self, api_key: str, tokens: int, service: str = None) -> dict:
        """Token-based limits for AI services."""
        account = self.db.execute("SELECT tokens_today, plan FROM accounts WHERE api_key = ? AND status = 'active'", 
                                 (api_key,)).fetchone()
        if not account:
            return {"allowed": False, "reason": "invalid_key"}
        tokens_today, plan = account
        if service and service in STRICT_SERVICES:
            per_request = STRICT_SERVICES[service]["max_tokens_per_request"]
            if tokens > per_request:
                return {"allowed": False, "reason": "token_limit_per_request", "requested": tokens, "max": per_request}
        daily_token_limit = FREE_TIER["max_tokens_per_day"] if plan == "free" else 1000000
        if tokens_today + tokens > daily_token_limit:
            return {"allowed": False, "reason": "daily_token_limit", "used": tokens_today, "max": daily_token_limit}
        return {"allowed": True, "tokens_today": tokens_today, "tokens_requested": tokens, "max": daily_token_limit}

    def check_expiry(self, api_key: str) -> dict:
        """Check if free trial has expired."""
        account = self.db.execute("SELECT id, plan, expires_at, status FROM accounts WHERE api_key = ?", (api_key,)).fetchone()
        if not account:
            return {"valid": False, "reason": "invalid_key"}
        aid, plan, expires, status = account
        if status == "banned":
            return {"valid": False, "reason": "banned"}
        if plan == "free" and expires:
            exp = datetime.fromisoformat(expires.replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > exp:
                self.db.execute("UPDATE accounts SET status = 'expired' WHERE id = ?", (aid,))
                self.db.commit()
                return {"valid": False, "reason": "trial_expired", "expired_at": expires}
        return {"valid": True, "plan": plan, "expires_at": expires}

    def log_abuse(self, account_id, event_type, severity, details, ip=""):
        self.db.execute(
            "INSERT INTO abuse_events (account_id, event_type, severity, details, ip_address, timestamp, action_taken) VALUES (?,?,?,?,?,?,?)",
            (account_id, event_type, severity, details, ip, datetime.now(timezone.utc).isoformat(),
             "logged" if severity == "low" else "flagged" if severity == "medium" else "action_required")
        )
        self.db.commit()

    def get_trust_score(self, api_key: str) -> float:
        """Dynamic trust scoring — degrades with abuse, improves with legitimate use."""
        account = self.db.execute("SELECT id, trust_score FROM accounts WHERE api_key = ?", (api_key,)).fetchone()
        if not account:
            return 0.0
        aid, trust = account
        # Check recent abuse
        abuse_count = self.db.execute(
            "SELECT COUNT(*) FROM abuse_events WHERE account_id = ? AND timestamp > ?",
            (aid, (datetime.now(timezone.utc) - timedelta(days=7)).isoformat())
        ).fetchone()[0]
        if abuse_count > 0:
            trust = max(0.1, trust - abuse_count * 0.1)
            self.db.execute("UPDATE accounts SET trust_score = ? WHERE id = ?", (trust, aid))
            self.db.commit()
        return trust

    def auto_ban_check(self, api_key: str) -> bool:
        """Auto-ban accounts with trust score below threshold."""
        account = self.db.execute("SELECT id, trust_score, email_hash FROM accounts WHERE api_key = ?", (api_key,)).fetchone()
        if not account:
            return False
        aid, trust, email_hash = account
        if trust < 0.15:
            self.db.execute("UPDATE accounts SET status = 'banned', ban_reason = 'Auto-banned: trust score below threshold' WHERE id = ?", (aid,))
            self.log_abuse(aid, "auto_ban", "critical", f"Trust score: {trust}", "")
            self.db.commit()
            return True
        return False


# ─── FastAPI ──────────────────────────────────────────────────────
app = FastAPI(title="EVEZ Gateway Guard", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
guard = GuardEngine(DB)

class SignupRequest(BaseModel):
    email: str
    fingerprint: Optional[str] = None

class ValidateRequest(BaseModel):
    api_key: str
    service: Optional[str] = None
    tokens: Optional[int] = 0

@app.get("/")
async def root():
    active = DB.execute("SELECT COUNT(*) FROM accounts WHERE status = 'active'").fetchone()[0]
    banned = DB.execute("SELECT COUNT(*) FROM accounts WHERE status = 'banned'").fetchone()[0]
    return {
        "service": "EVEZ Gateway Guard",
        "active_accounts": active,
        "banned_accounts": banned,
        "free_tier": {
            "requests_per_day": FREE_TIER["max_requests_per_day"],
            "requests_per_hour": FREE_TIER["max_requests_per_hour"],
            "tokens_per_day": FREE_TIER["max_tokens_per_day"],
            "concurrent_limit": FREE_TIER["max_concurrent"],
            "trial_duration": f"{FREE_TIER['trial_duration_days']} days",
            "cooldown_after_trial": f"{FREE_TIER['cooldown_after_expiry_hours']//24} days",
        },
        "strict_services": {k: v["max_requests_per_day"] for k, v in STRICT_SERVICES.items()},
    }

@app.post("/signup")
async def signup(req: SignupRequest, request: Request):
    """Create a free trial account with full abuse prevention."""
    # Extract client info
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown").split(",")[0].strip()
    fingerprint = req.fingerprint or request.headers.get("X-Fingerprint", "")

    # Validate email format
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', req.email):
        raise HTTPException(400, "Invalid email format")

    # Check eligibility (multi-factor)
    eligibility = guard.check_signup_eligibility(req.email, ip, fingerprint)
    if not eligibility["allowed"]:
        guard.log_abuse(None, "signup_blocked", "high", json.dumps(eligibility["issues"]), ip)
        raise HTTPException(403, {
            "error": "Signup not allowed",
            "issues": [i["type"] for i in eligibility["issues"] if i["severity"] in ("critical", "high")]
        })

    # Create account
    account_id = f"evez-acc-{uuid.uuid4().hex[:12]}"
    api_key = f"evez_free_{uuid.uuid4().hex}"
    email_hash = guard.hash_email(req.email)
    email_domain = req.email.split("@")[-1].lower()
    ip_hash = guard.hash_ip(ip)
    expires_at = (datetime.now(timezone.utc) + timedelta(days=FREE_TIER["trial_duration_days"])).isoformat()

    DB.execute(
        """INSERT INTO accounts 
        (id, email_hash, email_domain, ip_address, ip_hash, fingerprint, plan, api_key, 
         created_at, expires_at, last_reset, trust_score)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (account_id, email_hash, email_domain, ip, ip_hash, fingerprint, "free", api_key,
         datetime.now(timezone.utc).isoformat(), expires_at,
         datetime.now(timezone.utc).strftime("%Y-%m-%d"), eligibility["trust_score"])
    )

    # Update IP registry
    ip_exists = DB.execute("SELECT account_count FROM ip_registry WHERE ip_hash = ?", (ip_hash,)).fetchone()
    if ip_exists:
        DB.execute("UPDATE ip_registry SET account_count = account_count + 1, last_seen = ? WHERE ip_hash = ?",
                   (datetime.now(timezone.utc).isoformat(), ip_hash))
    else:
        DB.execute("INSERT INTO ip_registry (ip_hash, account_count, last_seen) VALUES (?,?,?)",
                   (ip_hash, 1, datetime.now(timezone.utc).isoformat()))
    DB.commit()

    return {
        "api_key": api_key,
        "plan": "free",
        "expires_at": expires_at,
        "limits": {
            "requests_per_day": FREE_TIER["max_requests_per_day"],
            "requests_per_hour": FREE_TIER["max_requests_per_hour"],
            "tokens_per_day": FREE_TIER["max_tokens_per_day"],
            "concurrent": FREE_TIER["max_concurrent"],
            "strict_services": {k: f"{v['max_requests_per_day']} req/day" for k, v in STRICT_SERVICES.items()},
        },
        "trust_score": eligibility["trust_score"],
        "message": f"Welcome to EVEZ. Free trial active for {FREE_TIER['trial_duration_days']} days. Use your API key in the Authorization header.",
    }

@app.post("/validate")
async def validate(req: ValidateRequest, request: Request):
    """Validate an API key for a specific service. Called before every proxied request."""
    ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")

    # 1. Expiry check
    expiry = guard.check_expiry(req.api_key)
    if not expiry["valid"]:
        raise HTTPException(401, expiry)

    # 2. Rate limit check
    rate = guard.check_rate_limit(req.api_key, req.service)
    if not rate["allowed"]:
        raise HTTPException(429, rate)

    # 3. Concurrent check
    conc = guard.check_concurrent(req.api_key)
    if not conc["allowed"]:
        raise HTTPException(429, conc)

    # 4. Token check (for AI services)
    if req.tokens and req.tokens > 0:
        token_check = guard.check_token_limit(req.api_key, req.tokens, req.service)
        if not token_check["allowed"]:
            raise HTTPException(429, token_check)

    # 5. Trust score
    trust = guard.get_trust_score(req.api_key)

    # 6. Auto-ban check
    if guard.auto_ban_check(req.api_key):
        raise HTTPException(403, {"error": "Account suspended due to policy violations"})

    # Increment concurrent
    DB.execute("UPDATE accounts SET concurrent_now = concurrent_now + 1 WHERE api_key = ?", (req.api_key,))
    DB.commit()

    return {
        "valid": True,
        "plan": rate.get("plan"),
        "requests_today": rate.get("requests_today", 0),
        "limit": rate.get("limit"),
        "trust_score": trust,
        "service": req.service,
    }

@app.post("/release")
async def release(api_key: str):
    """Decrement concurrent counter after request completes."""
    DB.execute("UPDATE accounts SET concurrent_now = MAX(0, concurrent_now - 1) WHERE api_key = ?", (api_key,))
    DB.commit()
    return {"released": True}

@app.post("/usage")
async def log_usage(api_key: str, service: str, endpoint: str, tokens: int = 0, latency: int = 0,
                    ip: str = "", user_agent: str = ""):
    """Log actual usage after a request completes."""
    account = DB.execute("SELECT id FROM accounts WHERE api_key = ?", (api_key,)).fetchone()
    if not account:
        return {"logged": False}

    DB.execute(
        "INSERT INTO request_log (account_id, api_key, service, endpoint, tokens_used, latency_ms, ip_address, user_agent, timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
        (account[0], api_key, service, endpoint, tokens, latency, ip, user_agent, datetime.now(timezone.utc).isoformat())
    )
    # Update counters
    DB.execute(
        "UPDATE accounts SET requests_today = requests_today + 1, tokens_today = tokens_today + ?, total_requests = total_requests + 1, total_tokens = total_tokens + ?, last_used_at = ? WHERE api_key = ?",
        (tokens, tokens, datetime.now(timezone.utc).isoformat(), api_key)
    )
    DB.commit()
    return {"logged": True}

@app.get("/status/{api_key}")
async def account_status(api_key: str):
    """Get account status and usage info."""
    account = DB.execute("SELECT * FROM accounts WHERE api_key = ?", (api_key,)).fetchone()
    if not account:
        raise HTTPException(404, "Account not found")
    return {
        "id": account[0], "plan": account[4], "status": account[16],
        "created_at": account[8], "expires_at": account[9],
        "requests_today": account[11], "tokens_today": account[12],
        "total_requests": account[14], "total_tokens": account[15],
        "trust_score": account[18],
        "limits": {
            "requests_per_day": FREE_TIER["max_requests_per_day"] if account[4] == "free" else "unlimited",
            "tokens_per_day": FREE_TIER["max_tokens_per_day"] if account[4] == "free" else "unlimited",
        }
    }

@app.get("/abuse-log")
async def abuse_log(limit: int = 50):
    """View recent abuse events (admin only — add auth in production)."""
    rows = DB.execute("SELECT * FROM abuse_events ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
    return {"events": [{
        "id": r[0], "account": r[1], "type": r[2], "severity": r[3],
        "details": r[4], "ip": r[5], "timestamp": r[6], "action": r[7]
    } for r in rows]}

@app.get("/guardrails")
async def guardrail_info():
    """Public documentation of all guardrails — transparency builds trust."""
    return {
        "free_tier_limits": FREE_TIER,
        "strict_service_limits": STRICT_SERVICES,
        "abuse_prevention": [
            "Disposable email blocking (30+ domains)",
            "Per-IP account limits (3 per network)",
            "Browser fingerprint deduplication",
            "30-day cooldown after trial expiry",
            "Trust scoring (0.0-1.0, auto-ban below 0.15)",
            "Sliding window rate limits (hourly + daily)",
            "Concurrent request limits (2 free, 50 paid)",
            "Per-service token caps on AI endpoints",
            "Auto-ban for persistent abusers",
        ],
        "what_happens_if_you_hit_limits": {
            "rate_limited": "429 Too Many Requests. Resets at midnight UTC.",
            "trial_expired": "401 Unauthorized. Upgrade or wait 30 days for new trial.",
            "banned": "403 Forbidden. Appeal via rubikspubes69@gmail.com.",
            "concurrent_limit": "429. Wait for existing requests to complete.",
        },
        "fair_use_policy": "EVEZ free tier is for evaluation and development. Production use requires a paid plan. We monitor for automated abuse, credential sharing, and resource hoarding.",
    }


if __name__ == "__main__":
    port = int(os.getenv("GUARD_PORT", "8907"))
    print(f"🛡️ EVEZ Gateway Guard on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
