#!/usr/bin/env python3
"""
EVEZ-OS Funding Monitor
Watches grant databases, government solicitations, and foundation cycles
for opportunities matching our keywords.
"""
import hashlib
import json
import os
import time
from datetime import datetime

# Keywords that match our capabilities
KEYWORDS = [
    # UAP/Transparency
    "UAP", "unidentified anomalous", "transparency", "FOIA", "Freedom of Information",
    "disclosure", "redaction", "declassification", "AARO", "anomaly resolution",
    # Information integrity
    "information integrity", "censorship", "misinformation", "information operations",
    "narrative analysis", "information warfare", "open government",
    # Computational social science
    "computational social science", "spectral analysis", "network analysis",
    "eigenvalue", "graph theory", "information extraction",
    # Security
    "gap detection", "vulnerability analysis", "architectural security",
    "information security", "structural analysis",
    # AI/ML
    "AI search", "search engine", "natural language", "document analysis",
    "automated analysis", "pattern detection",
]

# Sources to monitor
SOURCES = {
    "grants.gov": {
        "url": "https://grants.gov/search-results",
        "method": "keyword_search",
        "keywords": ["UAP", "transparency", "FOIA", "information integrity", "computational social science"],
        "cadence": "daily",
    },
    "sam.gov": {
        "url": "https://sam.gov/search",
        "method": "opportunity_search",
        "keywords": ["UAP", "transparency technology", "FOIA automation", "information analysis"],
        "cadence": "daily",
    },
    "darpa_baa": {
        "url": "https://www.darpa.mil/work-with-us/opportunities",
        "method": "baa_monitor",
        "keywords": ["gap detection", "structural analysis", "information extraction", "spectral"],
        "cadence": "weekly",
    },
    "nsf_css": {
        "url": "https://www.nsf.gov/funding/opportunities",
        "method": "program_monitor",
        "keywords": ["computational social science", "information integrity", "network analysis"],
        "cadence": "weekly",
    },
    "knight_foundation": {
        "url": "https://knightfoundation.org/grants/",
        "method": "grant_cycle",
        "keywords": ["information", "journalism technology", "transparency"],
        "cadence": "monthly",
    },
    "iarpa": {
        "url": "https://www.iarpa.gov/research-programs",
        "method": "program_monitor",
        "keywords": ["information extraction", "analysis", "detect"],
        "cadence": "weekly",
    },
}

STATE_FILE = os.path.join(os.path.dirname(__file__), "funding_monitor_state.json")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"seen": {}, "last_check": {}, "matches": []}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def check_source(name, config, state):
    """Check a funding source for new matching opportunities."""
    now = datetime.now().isoformat()
    matches = []

    # In production, this would fetch and parse each source
    # For now, log the check and return structured output
    key = hashlib.md5(f"{name}:{now}".encode()).hexdigest()[:8]
    
    check_result = {
        "source": name,
        "url": config["url"],
        "checked_at": now,
        "keywords_matched": [],
        "new_opportunities": 0,
        "status": "checked",
    }

    state["last_check"][name] = now
    return check_result


def run_monitor():
    """Run one monitoring cycle across all sources."""
    state = load_state()
    all_results = []
    new_matches = []

    for name, config in SOURCES.items():
        result = check_source(name, config, state)
        all_results.append(result)
        if result.get("new_opportunities", 0) > 0:
            new_matches.append(result)

    state["last_run"] = datetime.now().isoformat()
    save_state(state)

    return {
        "timestamp": datetime.now().isoformat(),
        "sources_checked": len(all_results),
        "new_matches": len(new_matches),
        "results": all_results,
        "keywords_monitored": len(KEYWORDS),
    }


if __name__ == "__main__":
    result = run_monitor()
    print(json.dumps(result, indent=2))
