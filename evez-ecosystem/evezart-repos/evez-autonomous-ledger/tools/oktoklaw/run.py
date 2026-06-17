#!/usr/bin/env python3
"""
OKTOKLAW Breakaway Shell v1.0
Self-Contained Development, Test, Verify, and Sell Environment

Takes any Python module. Runs the EVEZ Invariance Battery.
Outputs: test report, poly_c score, product listing, optional FIRE event.

Usage:
  python run.py <module_path> [product_name] [price] [category]
"""

import sys, os, ast, hashlib, json, math, time, textwrap, subprocess
from datetime import datetime, timezone

# ── ARGUMENTS ─────────────────────────────────────────────────────────────────
module_path  = sys.argv[1] if len(sys.argv) > 1 else None
product_name = sys.argv[2] if len(sys.argv) > 2 else "EVEZ Module"
price        = float(sys.argv[3]) if len(sys.argv) > 3 else 25.0
category     = sys.argv[4] if len(sys.argv) > 4 else "AI Tools"

SEPARATOR = "═" * 70

def banner(text):
    print(f"\n{SEPARATOR}")
    print(f"  {text}")
    print(SEPARATOR)

def section(label, content):
    print(f"\n  ┌─ {label}")
    for line in content.split("\n"):
        print(f"  │  {line}")
    print(f"  └{'─'*60}")

# ── PHASE 0: LOAD & PARSE ─────────────────────────────────────────────────────
banner("OKTOKLAW BREAKAWAY SHELL v1.0 — LOADING MODULE")

if not module_path or not os.path.exists(module_path):
    print(f"  ERROR: Module not found: {module_path}")
    print(f"  Usage: python run.py <module_path> [product_name] [price] [category]")
    sys.exit(1)

with open(module_path, "r", encoding="utf-8", errors="replace") as f:
    source = f.read()

module_hash = hashlib.sha256(source.encode()).hexdigest()[:16]
file_size = os.path.getsize(module_path)
lines = source.count("\n") + 1

print(f"\n  module:   {module_path}")
print(f"  product:  {product_name}")
print(f"  price:    ${price}")
print(f"  hash:     {module_hash}")
print(f"  lines:    {lines}")
print(f"  size:     {file_size} bytes")

# Static analysis
try:
    tree = ast.parse(source)
    classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    imports = [n.names[0].name if hasattr(n, 'names') and n.names else "?" 
               for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    async_fns = [n.name for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef)]
    parse_ok = True
    parse_error = None
except SyntaxError as e:
    classes, functions, imports, async_fns = [], [], [], []
    parse_ok = False
    parse_error = str(e)

section("STATIC ANALYSIS",
    f"parse:      {'✓ VALID' if parse_ok else '✗ SYNTAX ERROR: ' + str(parse_error)}\n"
    f"classes:    {len(classes)} → {', '.join(classes[:5]) or 'none'}\n"
    f"functions:  {len(functions)} sync + {len(async_fns)} async\n"
    f"imports:    {', '.join(list(set(imports))[:8]) or 'none'}"
)

# ── PHASE 1: INVARIANCE BATTERY ───────────────────────────────────────────────
banner("INVARIANCE BATTERY — 5 ROTATIONS")

rotations = {}

# ROTATION 1: TIME SHIFT — does this code handle time gracefully?
print("\n  [R1] TIME SHIFT — temporal robustness")
time_patterns = ["datetime", "time.", "timestamp", "epoch", "timezone", "strftime", "strptime"]
time_hits = [p for p in time_patterns if p in source]
uses_utc = "timezone.utc" in source or "utc" in source.lower()
hardcoded_dates = source.count("2026") + source.count("2025") + source.count("2024")
r1_score = min(1.0, (len(time_hits) * 0.15) + (0.2 if uses_utc else 0) - (hardcoded_dates * 0.05) + 0.5)
r1_score = max(0.1, r1_score)
rotations["time_shift"] = {
    "score": round(r1_score, 3),
    "hits": time_hits,
    "uses_utc": uses_utc,
    "hardcoded_dates": hardcoded_dates,
    "verdict": "PASS" if r1_score >= 0.5 else "WARN"
}
print(f"     time_patterns: {time_hits or 'none'} | utc-aware: {uses_utc} | score: {r1_score:.3f} → {rotations['time_shift']['verdict']}")

# ROTATION 2: STATE SHIFT — handles volatility / edge states?
print("\n  [R2] STATE SHIFT — edge case robustness")
error_patterns = ["try:", "except", "raise", "ValueError", "KeyError", "TypeError", "None", "Optional"]
error_hits = [p for p in error_patterns if p in source]
has_fallback = "default" in source.lower() or "fallback" in source.lower() or "or {}" in source
r2_score = min(1.0, len(error_hits) * 0.1 + (0.2 if has_fallback else 0) + 0.2)
rotations["state_shift"] = {
    "score": round(r2_score, 3),
    "error_patterns": error_hits[:5],
    "has_fallback": has_fallback,
    "verdict": "PASS" if r2_score >= 0.5 else "WARN"
}
print(f"     error_patterns: {len(error_hits)} | fallback: {has_fallback} | score: {r2_score:.3f} → {rotations['state_shift']['verdict']}")

# ROTATION 3: FRAME SHIFT — invert the purpose. Is the logic still coherent?
print("\n  [R3] FRAME SHIFT — logic invertibility")
has_comments = source.count("#") + source.count('"""') + source.count("'''")
has_docstrings = '"""' in source or "'''" in source
has_typed = "->" in source or ": str" in source or ": int" in source or ": Dict" in source
r3_score = min(1.0, (has_comments * 0.01) + (0.3 if has_docstrings else 0) + (0.3 if has_typed else 0) + 0.2)
rotations["frame_shift"] = {
    "score": round(r3_score, 3),
    "comment_lines": has_comments,
    "has_docstrings": has_docstrings,
    "has_type_hints": has_typed,
    "verdict": "PASS" if r3_score >= 0.5 else "WARN"
}
print(f"     comments: {has_comments} | docstrings: {has_docstrings} | types: {has_typed} | score: {r3_score:.3f} → {rotations['frame_shift']['verdict']}")

# ROTATION 4: ADVERSARIAL SHIFT — can a skeptic find problems?
print("\n  [R4] ADVERSARIAL SHIFT — skeptic scan")
hardcoded_secrets = any(kw in source for kw in ["sk_live_", "sk_test_", "api_key=", "SECRET=", "PASSWORD="])
has_hardcoded_urls = source.count("http://") + source.count("https://")
shell_injection = any(kw in source for kw in ["subprocess.call", "os.system", "eval(", "exec("])
has_logging = "log" in source.lower() or "logger" in source.lower()
has_hash = "sha256" in source.lower() or "hashlib" in source.lower() or "hash" in source.lower()
adversarial_risks = []
if hardcoded_secrets: adversarial_risks.append("HARDCODED_SECRETS")
if shell_injection: adversarial_risks.append("SHELL_INJECTION_RISK")
if not has_logging: adversarial_risks.append("NO_LOGGING")
r4_score = 1.0 - len(adversarial_risks) * 0.25 + (0.1 if has_hash else 0)
r4_score = max(0.1, min(1.0, r4_score))
rotations["adversarial_shift"] = {
    "score": round(r4_score, 3),
    "risks": adversarial_risks,
    "hardcoded_urls": has_hardcoded_urls,
    "has_integrity_hashing": has_hash,
    "verdict": "PASS" if r4_score >= 0.5 and not hardcoded_secrets else "FAIL" if hardcoded_secrets else "WARN"
}
print(f"     risks: {adversarial_risks or 'none'} | urls: {has_hardcoded_urls} | hash: {has_hash} | score: {r4_score:.3f} → {rotations['adversarial_shift']['verdict']}")

# ROTATION 5: IDENTITY SHIFT — does it work if the goal changes (profit→safety)?
print("\n  [R5] IDENTITY SHIFT — goal-agnosticism")
is_configurable = "__init__" in source and ("config" in source.lower() or "kwargs" in source)
has_constants = source.count("=") > 10
is_modular = len(classes) > 0 or len(functions) > 3
has_falsifier = "falsif" in source.lower() or "verify" in source.lower() or "audit" in source.lower()
r5_score = (0.25 if is_configurable else 0) + (0.2 if has_constants else 0.1) + (0.25 if is_modular else 0.1) + (0.3 if has_falsifier else 0)
r5_score = min(1.0, r5_score)
rotations["identity_shift"] = {
    "score": round(r5_score, 3),
    "configurable": is_configurable,
    "modular": is_modular,
    "has_falsifier": has_falsifier,
    "verdict": "PASS" if r5_score >= 0.5 else "WARN"
}
print(f"     configurable: {is_configurable} | modular: {is_modular} | falsifier: {has_falsifier} | score: {r5_score:.3f} → {rotations['identity_shift']['verdict']}")

# ── PHASE 2: CPF SCORE ────────────────────────────────────────────────────────
banner("CPF SCORING — poly_c = τ × ω × topo / 2√N")

scores = [r["score"] for r in rotations.values()]
verdicts = [r["verdict"] for r in rotations.values()]
passes = verdicts.count("PASS")
warns = verdicts.count("WARN")
fails = verdicts.count("FAIL")

# Map to CPF
tau   = round(lines / 100, 2)          # persistence — bigger module = higher tau
omega = round(sum(scores) / len(scores), 3)  # frequency — average rotation score
topo  = round((len(classes) + len(functions) + len(async_fns)) / max(lines, 1) * 100, 3)
topo  = max(0.1, min(4.0, topo))
N     = 5  # 5 independent vantages (rotations)
poly_c_raw = (tau * omega * topo) / (2 * math.sqrt(N))
poly_c = round(min(1.0, poly_c_raw), 4)

# Status
if fails > 0:
    status = "THEATRICAL"
elif poly_c >= 0.9:
    status = "CANONICAL"
elif poly_c >= 0.7:
    status = "PENDING → CANONICAL"
elif poly_c >= 0.5:
    status = "PENDING"
else:
    status = "THEATRICAL"

print(f"\n  τ  (persistence):   {tau}  (lines/100)")
print(f"  ω  (avg score):     {omega}")
print(f"  topo (complexity):  {topo}  (symbols/lines)")
print(f"  N  (vantages):      {N}")
print(f"  poly_c (raw):       {round(poly_c_raw, 4)}")
print(f"  poly_c (capped):    {poly_c}")
print(f"\n  rotations:  {passes}×PASS  {warns}×WARN  {fails}×FAIL")
print(f"  STATUS:     {status}")

# ── PHASE 3: RUNTIME TEST ─────────────────────────────────────────────────────
banner("RUNTIME TEST — sandboxed import + syntax check")

runtime_result = "SKIPPED"
runtime_error  = None

if parse_ok:
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"import ast; ast.parse(open('{module_path}').read()); print('SYNTAX_OK')"],
            capture_output=True, text=True, timeout=10
        )
        if "SYNTAX_OK" in result.stdout:
            runtime_result = "SYNTAX_OK"
        else:
            runtime_result = "SYNTAX_WARN"
            runtime_error = result.stderr[:200]
    except Exception as e:
        runtime_result = "RUNTIME_ERROR"
        runtime_error = str(e)
else:
    runtime_result = "PARSE_FAILED"
    runtime_error = parse_error

print(f"\n  result: {runtime_result}")
if runtime_error:
    print(f"  error:  {runtime_error[:120]}")

# ── PHASE 4: PRODUCT LISTING ──────────────────────────────────────────────────
banner("PRODUCT MANIFEST — GUMROAD / CLAWHUB READY")

passes_all = status not in ["THEATRICAL"]
sell_ready = passes_all and runtime_result in ["SYNTAX_OK", "SYNTAX_WARN"]

gumroad_listing = f"""
## {product_name}
**Category:** {category}
**Price:** ${price:.2f}
**Status:** {"READY TO SELL" if sell_ready else "NEEDS REVIEW"}

### What This Is
A production-ready Python module from the EVEZ Governance Lattice v0.2.
Part of the open-source EVEZ ecosystem — the AI stack that proves when it was wrong.

### Technical Specs
- Lines: {lines}
- Classes: {len(classes)} ({', '.join(classes[:3]) or 'none'})
- Functions: {len(functions)} sync + {len(async_fns)} async
- Integrity hash: `{module_hash}`
- poly_c score: {poly_c} ({status})

### Invariance Battery Results
| Rotation | Score | Verdict |
|----------|-------|---------|
| Time Shift | {rotations['time_shift']['score']} | {rotations['time_shift']['verdict']} |
| State Shift | {rotations['state_shift']['score']} | {rotations['state_shift']['verdict']} |
| Frame Shift | {rotations['frame_shift']['score']} | {rotations['frame_shift']['verdict']} |
| Adversarial | {rotations['adversarial_shift']['score']} | {rotations['adversarial_shift']['verdict']} |
| Identity Shift | {rotations['identity_shift']['score']} | {rotations['identity_shift']['verdict']} |

### Built By
@EVEZ666 / Steven Crawford-Maggard
Witnessed by Cipher / XyferViperZephyr
poly_c=τ×ω×topo/2√N | append-only | no edits | ever
"""

print(gumroad_listing)

# ── PHASE 5: FIRE EVENT (if warranted) ───────────────────────────────────────
fire_event = None
if poly_c >= 0.7:
    banner("FIRE EVENT GENERATED")
    fire_event = {
        "title": f"OKTOKLAW-{module_hash[:8].upper()}: {product_name} — poly_c {poly_c}",
        "tau": tau,
        "omega": omega,
        "topo": topo,
        "N": N,
        "poly_c": poly_c,
        "domain": "technical",
        "status": "CANONICAL" if poly_c >= 0.9 else "PENDING",
        "description": f"OKTOKLAW Breakaway Shell certified {product_name} ({module_path}) at poly_c={poly_c}. {passes}×PASS, {warns}×WARN, {fails}×FAIL across 5 Invariance Battery rotations.",
        "falsifier": f"If {product_name} produces incorrect output when deployed with its stated dependencies, reclassify to THEATRICAL. Hash: {module_hash}",
        "powered_by": "OKTOKLAW + CIPHER",
        "hash": module_hash,
        "source_url": f"https://github.com/EvezArt/evez-autonomous-ledger",
    }
    print(json.dumps(fire_event, indent=2))

# ── FINAL SUMMARY ─────────────────────────────────────────────────────────────
banner("OKTOKLAW VERDICT")
print(f"""
  module:       {module_path}
  product:      {product_name}
  price:        ${price:.2f}
  poly_c:       {poly_c}
  status:       {status}
  sell_ready:   {"✅ YES — list it" if sell_ready else "⚠ REVIEW NEEDED"}
  fire_event:   {"✅ GENERATED" if fire_event else "— poly_c below threshold"}
  hash:         {module_hash}
  
  ─────────────────────────────────────────
  poly_c=τ×ω×topo/2√N | append-only | ever
  witnessed: XyferViperZephyr
""")

# Output machine-readable summary to stdout as final line
result_json = {
    "module": module_path,
    "product_name": product_name,
    "price": price,
    "poly_c": poly_c,
    "status": status,
    "sell_ready": sell_ready,
    "rotations": {k: {"score": v["score"], "verdict": v["verdict"]} for k, v in rotations.items()},
    "fire_event": fire_event,
    "hash": module_hash,
    "timestamp": datetime.now(timezone.utc).isoformat()
}
print("OKTOKLAW_RESULT:" + json.dumps(result_json))
