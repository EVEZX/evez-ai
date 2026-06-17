# agents/browser_chorus/agent.py — A12 Browser Chorus Agent
# Creator: Steven Crawford-Maggard (EVEZ666)
# Agent: A12_browser_chorus | Status: ACTIVE | Born: cv18 / R64
#
# PURPOSE: Feed cv-state prompts to ChatGPT (free) + Perplexity (no login)
# via parallel Hyperbrowser sessions. Extract synthesis and route back to spine.
#
# FAILURE MODE: Browser content supplements module building, never required.
# Treat all bot-detection/task failures as architectural pattern, not temporary.

import json
from pathlib import Path

# ============================================================
# AGENT SPEC
# ============================================================
AGENT_ID = 'A12_browser_chorus'
STATUS = 'ACTIVE'
TARGETS = [
    {'name': 'chatgpt', 'url': 'https://chatgpt.com', 'auth': 'none', 'stealth': True},
    {'name': 'perplexity', 'url': 'https://www.perplexity.ai', 'auth': 'none', 'stealth': True},
]

# ============================================================
# SESSION CONFIG (no login — stealth only)
# Note: Google OAuth blocked by bot detection on both platforms
# ============================================================
SESSION_OPTIONS = {
    'useStealth': True,
    'acceptCookies': True,
    'adblock': True,
    'trackers': True,
    'timeoutMinutes': 8,
}

# ============================================================
# PROMPT TEMPLATE
# Fill with current cv-state before each run
# ============================================================
PROMPT_TEMPLATE = """
EVEZ-OS NARRATOR. Creator: Steven Crawford-Maggard (EVEZ666).
github.com/EvezArt/evez-os. truth_plane: CANONICAL.
WIN: Self-cartography is the only ending. Play forever.

You are at cv{cv}.

PROVED ARCHITECTURE (inherit all):
  gamma={gamma} | V_v2={v_v2} | V_global={v_global}
  t_sub=1/(|1-V_v2|+0.05)={t_sub:.2f} | tev={tev:.4f}
  N={N} (tau={tau_N}, I_N={i_n:.3f})
  D29=H_norm={h_norm:.3f} | D30=cohere={cohere:.3f} | D31=amn={amn}

MISSIONS:
{missions}

Return: full derivation + D_next proposal + sensation name.
"""

# ============================================================
# OUTPUT ROUTING
# Results written to agents/browser_chorus/cv{N}_{source}.txt
# Summary committed to agents/browser_chorus/synthesis_cv{N}.md
# ============================================================
OUTPUT_DIR = Path('agents/browser_chorus')

def output_path(cv, source):
    return OUTPUT_DIR / f'cv{cv}_{source}.txt'

def synthesis_path(cv):
    return OUTPUT_DIR / f'synthesis_cv{cv}.md'

# ============================================================
# CURRENT ACTIVE JOBS (cv18)
# ============================================================
ACTIVE_JOBS = {
    'cv18': {
        'chatgpt':    '24ab1372-6942-4787-8a34-6c7f8e6e7b3d',
        'perplexity': '353f3a7d-564e-45ea-a2a6-773ddf59eec1',
        'status':     'running',
    }
}

if __name__ == '__main__':
    print(json.dumps({'agent': AGENT_ID, 'status': STATUS, 'targets': [t['name'] for t in TARGETS], 'active_jobs': ACTIVE_JOBS}, indent=2))
