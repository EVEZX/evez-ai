#!/usr/bin/env python3
"""
CONTRADICTION ENGINE v1.0
Spine-integrated UNSAT core detector with auto-test generation.

Designed for: Samsung Galaxy A16 (Termux/Python 3.x, zero external dependencies)
Architecture: Pure Python stdlib — no Z3, no numpy, no pip install required.

Usage:
    python3 contradiction_engine.py              # Run demo with Firecracker investigation
    python3 contradiction_engine.py --interactive # Interactive REPL mode
    python3 contradiction_engine.py spine.json   # Load claims from spine file

Core loop:
    1. Ingest claims (from spine or manual)
    2. Encode as propositional constraints
    3. Check satisfiability (DPLL solver)
    4. If UNSAT → extract minimal unsat core
    5. Auto-generate discriminating test from core
    6. Emit contradiction event to spine
"""

import json, hashlib, time, sys, os
from itertools import combinations, product
from typing import Dict, List, Set, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timezone

class ClaimStatus(Enum):
    ACTIVE = "active"
    QUARANTINED = "quarantined"
    CONFIRMED = "confirmed"
    REFUTED = "refuted"
    COUNTERFACTUAL = "counterfactual"

@dataclass
class Claim:
    claim_id: str
    content: str
    source: str
    trust_score: float = 0.5
    status: str = "active"
    created_at: str = ""
    hash: str = ""
    falsifier: str = ""
    evidence: List[str] = field(default_factory=list)
    def __post_init__(self):
        if not self.created_at: self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.hash: self.hash = hashlib.sha256(f"{self.claim_id}|{self.content}|{self.source}|{self.created_at}".encode()).hexdigest()[:16]

@dataclass
class Constraint:
    constraint_type: str
    claim_ids: List[str]
    description: str = ""

@dataclass
class UnsatCore:
    core_claims: List[str]
    is_minimal: bool = True
    divergence_score: float = 0.0
    generated_test: Optional[dict] = None
    timestamp: str = ""
    hash: str = ""
    def __post_init__(self):
        if not self.timestamp: self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.hash: self.hash = hashlib.sha256(f"{'|'.join(sorted(self.core_claims))}|{self.timestamp}".encode()).hexdigest()[:16]

@dataclass
class Branch:
    branch_id: str
    parent_hash: str
    assumption: str
    assumption_claim_id: str
    events: List[dict] = field(default_factory=list)
    status: str = "active"

@dataclass
class SpineEvent:
    event_type: str
    payload: dict
    timestamp: str = ""
    hash: str = ""
    prev_hash: str = ""
    def __post_init__(self):
        if not self.timestamp: self.timestamp = datetime.now(timezone.utc).isoformat()
    def compute_hash(self, prev_hash=""):
        self.prev_hash = prev_hash
        chain = f"{self.event_type}|{json.dumps(self.payload, sort_keys=True)}|{self.timestamp}|{prev_hash}"
        self.hash = hashlib.sha256(chain.encode()).hexdigest()[:16]
        return self.hash

class DPLLSolver:
    def solve(self, clauses, num_vars):
        tagged = [(i, set(c)) for i, c in enumerate(clauses)]
        result = self._dpll(tagged, {}, num_vars)
        if result is not None: return True, result, None
        core_indices = self._minimize_core(clauses, num_vars)
        return False, None, core_indices

    def _dpll(self, tagged_clauses, assignment, num_vars):
        changed = True
        while changed:
            changed = False
            for idx, clause in tagged_clauses:
                remaining, satisfied = set(), False
                for lit in clause:
                    var = abs(lit)
                    if var in assignment:
                        if (lit > 0) == assignment[var]: satisfied = True; break
                    else: remaining.add(lit)
                if satisfied: continue
                if len(remaining) == 0: return None
                if len(remaining) == 1:
                    lit = remaining.pop(); assignment[abs(lit)] = (lit > 0); changed = True
        all_sat = True
        for idx, clause in tagged_clauses:
            satisfied, has_unassigned = False, False
            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    if (lit > 0) == assignment[var]: satisfied = True; break
                else: has_unassigned = True
            if not satisfied:
                if not has_unassigned: return None
                all_sat = False
        if all_sat: return dict(assignment)
        pick = None
        for idx, clause in tagged_clauses:
            for lit in clause:
                if abs(lit) not in assignment: pick = abs(lit); break
            if pick: break
        if pick is None: return dict(assignment)
        for val in [True, False]:
            new_assign = dict(assignment); new_assign[pick] = val
            result = self._dpll(tagged_clauses, new_assign, num_vars)
            if result is not None: return result
        return None

    def _minimize_core(self, clauses, num_vars):
        core = set(range(len(clauses)))
        for i in list(core):
            test_core = core - {i}
            test_clauses = [clauses[j] for j in sorted(test_core)]
            if test_clauses:
                tagged = [(idx, set(c)) for idx, c in enumerate(test_clauses)]
                if self._dpll(tagged, {}, num_vars) is None: core = test_core
        return core

class ContradictionEngine:
    def __init__(self):
        self.claims, self.constraints, self.spine = {}, [], []
        self.branches, self.solver, self.unsat_history = {}, DPLLSolver(), []
        self._var_map, self._next_var = {}, 1

    def _get_var(self, cid):
        if cid not in self._var_map: self._var_map[cid] = self._next_var; self._next_var += 1
        return self._var_map[cid]

    def _append_spine(self, event_type, payload):
        prev = self.spine[-1].hash if self.spine else "genesis"
        e = SpineEvent(event_type=event_type, payload=payload); e.compute_hash(prev)
        self.spine.append(e); return e

    def add_claim(self, cid, content, source, trust=0.5, falsifier="", evidence=None):
        c = Claim(claim_id=cid, content=content, source=source, trust_score=trust, falsifier=falsifier, evidence=evidence or [])
        self.claims[cid] = c
        self._append_spine("claim", {"action":"add","claim_id":cid,"content":content,"source":source,"trust_score":trust,"hash":c.hash})
        self.check_consistency(); return c

    def add_observation(self, cid, content, source, trust=0.9):
        c = self.add_claim(cid, content, source, trust)
        self.add_constraint("observation", [cid], f"Observed: {content}"); return c

    def add_constraint(self, ctype, cids, desc=""):
        con = Constraint(ctype, cids, desc); self.constraints.append(con)
        self._append_spine("constraint", {"type":ctype,"claims":cids,"description":desc}); return con

    def add_mutex(self, a, b, reason=""): self.add_constraint("mutex", [a, b], reason or f"{a} and {b} mutually exclusive")
    def add_implication(self, a, b, reason=""): self.add_constraint("implies", [a, b], reason or f"{a} implies {b}")

    def _encode_constraints(self):
        clauses, clause_sources = [], {}
        active = {cid for cid, c in self.claims.items() if c.status in ("active","confirmed")}
        for con in self.constraints:
            if not all(cid in active for cid in con.claim_ids): continue
            if con.constraint_type == "mutex":
                a, b = con.claim_ids[0], con.claim_ids[1]
                idx = len(clauses); clauses.append({-self._get_var(a), -self._get_var(b)})
                clause_sources[idx] = f"mutex({a},{b}): {con.description}"
            elif con.constraint_type == "implies":
                a, b = con.claim_ids[0], con.claim_ids[1]
                idx = len(clauses); clauses.append({-self._get_var(a), self._get_var(b)})
                clause_sources[idx] = f"implies({a},{b}): {con.description}"
            elif con.constraint_type == "observation":
                a = con.claim_ids[0]; idx = len(clauses); clauses.append({self._get_var(a)})
                clause_sources[idx] = f"observed({a}): {con.description}"
            elif con.constraint_type == "requires_all":
                for cid in con.claim_ids:
                    idx = len(clauses); clauses.append({self._get_var(cid)})
                    clause_sources[idx] = f"required({cid}): {con.description}"
        return clauses, self._next_var - 1, clause_sources

    def check_consistency(self):
        clauses, num_vars, clause_sources = self._encode_constraints()
        if not clauses: return None
        sat, model, core_indices = self.solver.solve(clauses, num_vars)
        if sat: return None
        core_claim_ids, core_descriptions = set(), []
        if core_indices:
            for idx in core_indices:
                if idx in clause_sources: core_descriptions.append(clause_sources[idx])
                if idx < len(clauses):
                    for lit in clauses[idx]:
                        for cid, v in self._var_map.items():
                            if v == abs(lit): core_claim_ids.add(cid)
        test = self._generate_test(list(core_claim_ids))
        uc = UnsatCore(core_claims=sorted(core_claim_ids), generated_test=test,
                       divergence_score=self._compute_divergence(core_claim_ids))
        self.unsat_history.append(uc)
        for cid in core_claim_ids:
            if cid in self.claims: self.claims[cid].status = "quarantined"
        self._append_spine("contradiction", {"core":sorted(core_claim_ids),"core_descriptions":core_descriptions,
            "generated_test":test,"hash":uc.hash})
        return uc

    def _compute_divergence(self, core):
        scores = [self.claims[c].trust_score for c in core if c in self.claims]
        if not scores: return 0.0
        mean = sum(scores)/len(scores)
        return min(1.0, sum((s-mean)**2 for s in scores)/len(scores)*len(core)+0.1*len(core))

    def _generate_test(self, core_ids):
        if len(core_ids) < 2: return {"description":"Single claim — verify directly","target_claims":core_ids}
        sorted_by_trust = sorted(core_ids, key=lambda c: self.claims.get(c, Claim("","","")).trust_score, reverse=True)
        p, s = sorted_by_trust[0], sorted_by_trust[1]
        pc, sc = self.claims.get(p), self.claims.get(s)
        w = min(core_ids, key=lambda c: self.claims.get(c, Claim("","","")).trust_score)
        wc = self.claims.get(w)
        return {"description":f"Discriminate: '{pc.content}' vs '{sc.content}'",
                "hypothesis_a":{"claim_id":p,"assumes_true":pc.content},
                "hypothesis_b":{"claim_id":s,"assumes_true":sc.content},
                "stress_target":{"claim_id":w,"trust_score":wc.trust_score if wc else 0}}

    def fork(self, cid, reason=""):
        ph = self.spine[-1].hash if self.spine else "genesis"
        a = Branch(f"branch_{cid}_TRUE", ph, f"{cid} is TRUE", cid)
        b = Branch(f"branch_{cid}_FALSE", ph, f"{cid} is FALSE", cid)
        self.branches[a.branch_id] = a; self.branches[b.branch_id] = b
        self._append_spine("fork", {"claim_id":cid,"reason":reason,"branches":{"A":a.branch_id,"B":b.branch_id}})
        return a, b

    def merge(self, winner_id, evidence_hash, reason=""):
        w = self.branches.get(winner_id)
        if not w: return {"error":"Not found"}
        loser = None
        for bid, b in self.branches.items():
            if bid != winner_id and b.parent_hash == w.parent_hash: loser = b; break
        w.status = "merged"
        if loser: loser.status = "counterfactual"
        cid = w.assumption_claim_id
        if "TRUE" in w.branch_id and cid in self.claims: self.claims[cid].status = "confirmed"
        elif cid in self.claims: self.claims[cid].status = "refuted"
        me = self._append_spine("merge", {"winner":winner_id,"evidence":evidence_hash,"reason":reason})
        return {"winner":winner_id,"merge_hash":me.hash}

    def update_trust(self, cid, delta, reason=""):
        if cid not in self.claims: return
        c = self.claims[cid]; old = c.trust_score
        c.trust_score = max(0.0, min(1.0, c.trust_score + delta))
        self._append_spine("trust_update", {"claim_id":cid,"old":round(old,4),"new":round(c.trust_score,4),"reason":reason})

    def status_report(self):
        return {"claims":{"total":len(self.claims),"active":len([c for c in self.claims.values() if c.status=="active"]),
            "quarantined":len([c for c in self.claims.values() if c.status=="quarantined"])},
            "constraints":len(self.constraints),"contradictions":len(self.unsat_history),
            "spine_length":len(self.spine),"spine_head":self.spine[-1].hash if self.spine else "genesis"}

    def export_spine(self):
        return [{"event_type":e.event_type,"payload":e.payload,"timestamp":e.timestamp,"hash":e.hash,"prev_hash":e.prev_hash} for e in self.spine]

    def save_spine(self, path):
        with open(path, "w", encoding="utf-8") as f: json.dump(self.export_spine(), f, indent=2, ensure_ascii=False)
        print(f"[SPINE] Saved {len(self.spine)} events to {path}")

def run_firecracker_demo():
    e = ContradictionEngine()
    print("="*60); print("CONTRADICTION ENGINE v1.0"); print("Demo: Firecracker MicroVM Investigation"); print("="*60)
    print("\n[PHASE 1] Tool reports...")
    e.add_observation("obs_no_dockerenv", "/.dockerenv does not exist", "filesystem_probe", 0.95)
    e.add_observation("obs_no_cgroup", "No docker/lxc cgroup markers", "cgroup_probe", 0.95)
    e.add_observation("obs_full_caps", "CapEff=000001ffffffffff", "capability_probe", 0.99)
    e.add_observation("obs_root", "Running as uid=0", "uid_probe", 0.99)
    print("\n[PHASE 2] Standard detection hypothesis...")
    e.add_claim("hyp_bare_metal", "Bare metal Linux system", "container_detection", 0.7,
        falsifier="Any evidence of virtualization")
    e.add_implication("obs_no_dockerenv", "hyp_bare_metal", "No .dockerenv → supports bare metal")
    print("\n[PHASE 3] Deeper probes...")
    e.add_observation("obs_kvm", "dmesg: Hypervisor detected: KVM", "dmesg_probe", 0.99)
    e.add_observation("obs_no_pci", "Kernel cmdline: pci=off", "cmdline_probe", 0.95)
    e.add_claim("hyp_firecracker", "Firecracker microVM on KVM", "forensic_analysis", 0.85,
        falsifier="DMI data present, PCI bus active, no KVM in dmesg")
    e.add_mutex("hyp_bare_metal", "hyp_firecracker", "Cannot be both bare metal AND Firecracker")
    e.add_mutex("obs_kvm", "hyp_bare_metal", "KVM contradicts bare metal")
    print("\n[PHASE 4] Checking consistency...")
    core = e.check_consistency()
    if core:
        print(f"\n{'='*60}"); print("CONTRADICTION DETECTED"); print(f"{'='*60}")
        print(f"Core: {core.core_claims}")
        if core.generated_test: print(f"Test: {json.dumps(core.generated_test, indent=2)}")
    print("\n[PHASE 5] Fork & resolve...")
    bt, bf = e.fork("hyp_bare_metal", "bare metal vs Firecracker")
    r = e.merge(bf.branch_id, e.claims["obs_kvm"].hash, "KVM detected + pci=off + empty DMI")
    print(f"  hyp_bare_metal: {e.claims['hyp_bare_metal'].status}")
    e.update_trust("hyp_bare_metal", -0.3, "Container detection failed")
    e.update_trust("hyp_firecracker", 0.1, "Firecracker confirmed")
    print(f"\n{'='*60}"); print("STATUS"); print(f"{'='*60}")
    print(json.dumps(e.status_report(), indent=2))
    e.save_spine("contradiction_spine.json")
    print(f"\nDone. Spine: {len(e.spine)} events.")
    return e

def interactive_mode():
    e = ContradictionEngine()
    print("CONTRADICTION ENGINE v1.0 — Interactive Mode")
    print("Commands: add, observe, mutex, implies, check, fork, status, spine, demo, quit")
    while True:
        try: cmd = input("engine> ").strip().lower()
        except (EOFError, KeyboardInterrupt): break
        if cmd in ("quit","exit"): break
        elif cmd == "demo": run_firecracker_demo()
        elif cmd == "status": print(json.dumps(e.status_report(), indent=2))
        elif cmd == "check":
            core = e.check_consistency()
            if core: print(f"  CONTRADICTION: {core.core_claims}")
            else: print("  Consistent")
        elif cmd == "add":
            cid=input("  id: "); content=input("  content: "); source=input("  source: ")
            trust=float(input("  trust (0-1): ") or "0.5"); e.add_claim(cid,content,source,trust)
        elif cmd == "observe":
            cid=input("  id: "); content=input("  what: "); source=input("  source: ")
            e.add_observation(cid,content,source)
        elif cmd == "mutex": a=input("  a: "); b=input("  b: "); e.add_mutex(a,b,input("  reason: "))
        elif cmd == "implies": a=input("  if: "); b=input("  then: "); e.add_implication(a,b,input("  reason: "))
        elif cmd == "spine": e.save_spine(input("  file (spine.json): ") or "spine.json")
        else: print("  Commands: add, observe, mutex, implies, check, fork, status, spine, demo, quit")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--interactive","-i"): interactive_mode()
        elif sys.argv[1] in ("--demo","-d"): run_firecracker_demo()
        else:
            eng = ContradictionEngine()
            with open(sys.argv[1]) as f:
                for ev in json.load(f):
                    p = ev.get("payload", ev)
                    if "content" in p: eng.add_claim(p.get("id",f"imp_{len(eng.claims)}"), p["content"], p.get("source","import"))
            print(json.dumps(eng.status_report(), indent=2))
    else: run_firecracker_demo()
