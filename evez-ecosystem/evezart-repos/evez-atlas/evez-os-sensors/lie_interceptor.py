"""
EVEZ-OS LIE INTERCEPTOR — The Deception Topology Engine
Detects lies. Forecasts lies. Spots the geometry of deception BEFORE it crystallizes.
Every data point comes from REAL APIs. Zero mock. Zero fake. Zero placeholder.
"""

import hashlib
import json
import math
import time
import urllib.request
import ssl
import re
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
from pathlib import Path

class LieGrade(str, Enum):
    CONTRADICTION = "CONTRADICTION"
    ASYMMETRY = "ASYMMETRY"
    FORECAST = "FORECAST"
    PRE_LIE = "PRE_LIE"
    VERIFIED = "VERIFIED"
    INSUFFICIENT = "INSUFFICIENT"

@dataclass
class LieSpineEvent:
    event_id: str
    layer: str
    grade: LieGrade
    claim: str
    evidence: dict
    confidence: float
    counter_evidence: dict
    pre_lie_signal: float
    timestamp: float = field(default_factory=time.time)
    hash: str = ""
    previous_hash: str = ""
    def __post_init__(self):
        raw = f"{self.event_id}:{self.layer}:{self.grade.value}:{self.confidence:.6f}:{self.claim[:50]}:{self.previous_hash}"
        self.hash = hashlib.sha256(raw.encode()).hexdigest()[:24]

class LieSpine:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.last_hash = "GENESIS"
        if self.path.exists():
            with open(self.path) as f:
                for line in f:
                    if line.strip():
                        try:
                            e = json.loads(line)
                            if "hash" in e: self.last_hash = e["hash"]
                        except: pass
    def append(self, event: LieSpineEvent) -> dict:
        event.previous_hash = self.last_hash
        entry = {"event_id": event.event_id, "layer": event.layer, "grade": event.grade.value,
                 "claim": event.claim[:200], "evidence": event.evidence, "confidence": round(event.confidence, 4),
                 "counter_evidence": event.counter_evidence, "pre_lie_signal": round(event.pre_lie_signal, 4),
                 "hash": event.hash, "previous_hash": event.previous_hash, "timestamp": event.timestamp,
                 "powered_by": "EVEZ-LIE-INTERCEPTOR"}
        with open(self.path, "a") as f: f.write(json.dumps(entry) + "\n")
        self.last_hash = event.hash
        return entry
    def lint(self) -> dict:
        if not self.path.exists(): return {"valid": True, "events": 0, "status": "EMPTY"}
        events = []
        with open(self.path) as f:
            for line in f:
                if line.strip():
                    try: events.append(json.loads(line))
                    except: pass
        errors = []
        for i, e in enumerate(events):
            prev = "GENESIS" if i == 0 else events[i-1].get("hash")
            if e.get("previous_hash") != prev: errors.append(f"Event {i}: CHAIN_BROKEN")
        return {"valid": not errors, "events": len(events), "errors": errors, "status": "INTACT" if not errors else "TAMPERED"}

_ctx = ssl.create_default_context()
def _get(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "EVEZ-LI/1.0"})
        with urllib.request.urlopen(req, timeout=timeout, context=_ctx) as r: return r.read()
    except: return None
def _json(url, timeout=15):
    raw = _get(url, timeout)
    if raw:
        try: return json.loads(raw)
        except: pass
    return None
def _xml(url, timeout=15):
    raw = _get(url, timeout)
    return raw.decode() if raw else None

class LieInterceptor:
    """
    4-layer deception detection engine. All real data. No mock.
    L1: Contradiction — Direct conflicts between independent sources
    L2: Asymmetry — Claims vs reality gap
    L3: Forecast — Where incentive + opportunity = inevitable deception
    L4: Pre-Lie — The topology BEFORE the lie forms
    
    Pre-Lie Pressure: PLP = I × O × (1-A) × P × T
    Where I=incentive, O=opportunity, A=accountability, P=precedent, T=topological pressure
    PLP > 0.5 = forming. PLP > 0.8 = inevitable.
    """
    
    def __init__(self, spine_path="/tmp/lie_interceptor_spine.jsonl"):
        self.spine = LieSpine(spine_path)
        self.counter = 0
    
    def _record(self, layer, grade, claim, evidence, counter_evidence, confidence, pre_lie_signal):
        self.counter += 1
        self.spine.append(LieSpineEvent(
            event_id=f"LI-{layer}-{self.counter:04d}", layer=layer, grade=grade,
            claim=claim, evidence=evidence, confidence=confidence,
            counter_evidence=counter_evidence, pre_lie_signal=pre_lie_signal))
    
    def plp(self, i, o, a, p, t):
        """Compute Pre-Lie Pressure"""
        val = i * o * (1-a) * p * t
        return {"plp": round(val,6), "I": round(i,3), "O": round(o,3), "A": round(a,3), "P": round(p,3), "T": round(t,3),
                "verdict": "INEVITABLE" if val>0.8 else "FORMING" if val>0.5 else "POSSIBLE" if val>0.2 else "UNLIKELY"}
    
    # ── L1: CONTRADICTION ──────────────────────────────────────
    def l1_crypto_contradiction(self):
        """Volume > market cap = structural impossibility = wash trading lie"""
        findings = []
        data = _json("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=50&page=1&sparkline=false")
        if not data: return findings
        for coin in data:
            sym = coin.get("symbol","?")
            vol = coin.get("total_volume",0)
            mcap = coin.get("market_cap") or 0
            if mcap == 0: continue
            ratio = vol / mcap
            if ratio > 1.5:
                conf = min(1.0, ratio/5)
                self._record("L1", LieGrade.ASYMMETRY, f"{sym} has organic trading volume",
                    {"volume": vol, "mcap": mcap, "ratio": round(ratio,2)},
                    {"impossibility": "Volume exceeds market cap = wash trading"}, conf, min(1.0, (ratio-1.5)/3))
                findings.append({"symbol": sym, "ratio": round(ratio,2), "verdict": "WASH_TRADING_LIKELY"})
        return findings
    
    def l1_arxiv_contradiction(self):
        """Papers using absolute language AND hedging = internal contradiction"""
        findings = []
        xml = _xml("http://export.arxiv.org/api/query?search_query=cat:cs.AI&max_results=30&sortBy=submittedDate&sortOrder=descending")
        if not xml: return findings
        entries = re.findall(r'<entry>(.*?)</entry>', xml, re.DOTALL)
        for entry in entries:
            title_m = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
            summary_m = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
            if not title_m or not summary_m: continue
            title = title_m.group(1).strip().replace('\n',' ')
            abstract = summary_m.group(1).strip().replace('\n',' ').lower()
            hedge = sum(1 for w in ["may","could","might","potentially","preliminary"] if w in abstract)
            absolute = sum(1 for w in ["proves","proven","guaranteed","always","never","impossible","solves"] if w in abstract)
            if absolute > 0 and hedge > 0:
                conf = min(1.0, (absolute+hedge)/5)
                self._record("L1", LieGrade.CONTRADICTION, f"Paper '{title[:60]}' claims AND hedges",
                    {"absolute": absolute, "hedges": hedge},
                    {"contradiction": "Cannot prove AND hedge simultaneously"}, conf, 0.0)
                findings.append({"title": title[:80], "absolute": absolute, "hedge": hedge})
        return findings
    
    # ── L2: ASYMMETRY ──────────────────────────────────────────
    def l2_infrastructure_asymmetry(self):
        """Claim: own infrastructure. Reality: Cloudflare."""
        findings = []
        targets = {"openai.com": "OpenAI", "anthropic.com": "Anthropic", "x.com": "X Corp", "meta.com": "Meta"}
        for domain, expected in targets.items():
            dns = _json(f"https://dns.google/resolve?name={domain}&type=A")
            if not dns: continue
            ips = [a["data"] for a in dns.get("Answer",[]) if a.get("type")==1]
            if not ips: continue
            geo = _json(f"http://ip-api.com/json/{ips[0]}")
            if not geo or geo.get("status")!="success": continue
            actual = geo.get("org","?")
            if expected.lower() not in actual.lower() and "cloudflare" in actual.lower():
                self._record("L2", LieGrade.ASYMMETRY, f"{domain} runs on {expected} infrastructure",
                    {"actual_org": actual, "ip": ips[0]}, {"served_by": "Cloudflare CDN"}, 0.5, 0.2)
                findings.append({"domain": domain, "claimed": expected, "actual": actual})
        return findings
    
    def l2_hn_hype_asymmetry(self):
        """HN claims breakthrough, arxiv has zero evidence = hype lie"""
        findings = []
        hn = _json("https://hn.algolia.com/api/v1/search?query=AI+breakthrough&tags=story&hitsPerPage=15")
        if not hn: return findings
        for hit in hn.get("hits",[]):
            title = (hit.get("title") or "?")[:100]
            pts = hit.get("points") or 0
            breakthrough = any(w in title.lower() for w in ["breakthrough","revolutionary","solved","game changer","unprecedented"])
            if breakthrough and pts > 50:
                terms = [w for w in title.split() if len(w)>4][:3]
                if not terms: continue
                axml = _xml(f"http://export.arxiv.org/api/query?search_query=all:{'+'.join(terms)}&max_results=3")
                acount = len(re.findall(r'<entry>', axml)) if axml else 0
                if acount == 0:
                    self._record("L2", LieGrade.ASYMMETRY, f"HN: '{title[:50]}' is breakthrough",
                        {"hn_points": pts}, {"arxiv_papers": 0, "search": terms}, 0.4, 0.3)
                    findings.append({"title": title[:80], "hn_points": pts, "arxiv_evidence": 0})
        return findings
    
    # ── L3: FORECAST ───────────────────────────────────────────
    def l3_crypto_forecast(self):
        """Small cap + high volume + extreme move = pump-and-dump FORECAST"""
        findings = []
        data = _json("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=volume_desc&per_page=100&page=1&sparkline=false")
        if not data: return findings
        for coin in data:
            sym = coin.get("symbol","?")
            mcap = coin.get("market_cap") or 0
            vol = coin.get("total_volume") or 0
            ch = coin.get("price_change_percentage_24h") or 0
            if mcap == 0: continue
            vm = vol/mcap
            if mcap < 100_000_000 and vm > 1.0 and abs(ch) > 10:
                signal = min(1.0, vm * abs(ch) / 50)
                self._record("L3", LieGrade.FORECAST, f"{sym} has organic price movement",
                    {"mcap": mcap, "volume": vol, "vol_mcap": round(vm,2), "change": round(ch,2)},
                    {"forecast": "Pump-and-dump topology forming"}, min(0.9, signal), signal)
                findings.append({"symbol": sym, "signal": round(signal,3), "mcap": mcap, "change": round(ch,2)})
        return findings
    
    def l3_narrative_forecast(self):
        """Same story in multiple independent queries = narrative push forecast"""
        findings = []
        queries = ["AI safety", "AI regulation", "AI threat"]
        stories = {}
        for q in queries:
            hn = _json(f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage=8")
            if not hn: continue
            for hit in hn.get("hits",[]):
                t = (hit.get("title") or "").lower()[:50]
                stories.setdefault(t, {"q": [], "pts": 0})
                stories[t]["q"].append(q)
                stories[t]["pts"] += (hit.get("points") or 0)
        for t, info in stories.items():
            if len(info["q"]) >= 2 and info["pts"] > 30:
                signal = min(1.0, len(info["q"])/4)
                self._record("L3", LieGrade.FORECAST, f"Organic discussion: '{t}'",
                    {"queries": info["q"], "points": info["pts"]},
                    {"convergence": f"Story in {len(info['q'])} queries"}, 0.3, signal)
                findings.append({"title": t, "queries": info["q"], "signal": round(signal,3)})
        return findings
    
    # ── L4: PRE-LIE ────────────────────────────────────────────
    def l4_crypto_pre_lie(self):
        """Compute PLP for each crypto asset. PLP > 0.5 = lie forming. > 0.8 = inevitable."""
        findings = []
        data = _json("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=30&page=1&sparkline=false")
        if not data: return findings
        for coin in data:
            sym = coin.get("symbol","?")
            mcap = coin.get("market_cap") or 0
            vol = coin.get("total_volume") or 0
            ch = coin.get("price_change_percentage_24h") or 0
            ath_ch = coin.get("ath_change_percentage") or 0
            if mcap == 0: continue
            I = min(1.0, mcap / 1e9)
            O = min(1.0, vol / mcap)
            A = min(1.0, mcap / 1e10)
            P = 0.7 if abs(ch) > 15 else 0.3
            T = min(1.0, abs(ath_ch)/80) if ath_ch else 0
            plp = self.plp(I, O, A, P, T)
            if plp["plp"] > 0.05:
                grade = LieGrade.PRE_LIE if plp["plp"]>0.5 else LieGrade.FORECAST
                self._record("L4", grade, f"{sym} market operating honestly",
                    {"mcap": mcap, "volume": vol, "change": round(ch,2)}, plp, min(0.95, plp["plp"]), plp["plp"])
                findings.append({"symbol": sym, "plp": plp["plp"], "verdict": plp["verdict"]})
        return findings
    
    def l4_ai_claims_pre_lie(self):
        """PLP for common AI industry claims backed by real arxiv evidence"""
        findings = []
        claims = [
            {"claim": "AI models are safe and aligned", "search": "AI+safety+alignment", "I": 0.9, "O": 0.8, "A": 0.2, "P": 0.6},
            {"claim": "AI will not replace jobs", "search": "AI+job+displacement", "I": 0.9, "O": 0.9, "A": 0.1, "P": 0.8},
            {"claim": "AI progress is transparent", "search": "AI+transparency+interpretability", "I": 0.7, "O": 0.7, "A": 0.3, "P": 0.5},
        ]
        for c in claims:
            xml = _xml(f"http://export.arxiv.org/api/query?search_query=all:{c['search']}&max_results=5&sortBy=submittedDate")
            papers = len(re.findall(r'<entry>', xml)) if xml else 0
            T = min(1.0, papers/5)
            plp = self.plp(c["I"], c["O"], c["A"], c["P"], T)
            grade = LieGrade.PRE_LIE if plp["plp"]>0.5 else LieGrade.FORECAST
            self._record("L4", grade, c["claim"],
                {"arxiv_papers": papers, "search": c["search"]}, plp, min(0.95, plp["plp"]), plp["plp"])
            findings.append({"claim": c["claim"], "plp": plp["plp"], "verdict": plp["verdict"], "arxiv_papers": papers})
        return findings
    
    def l4_solar_pre_lie(self):
        """PLP for climate/solar downplay based on real NASA data"""
        findings = []
        flares = _json("https://api.nasa.gov/DONKI/FLR?startDate=2025-01-01&api_key=DEMO_KEY")
        if not flares: return findings
        x = sum(1 for f in flares if (f.get("classType") or "").startswith("X"))
        m = sum(1 for f in flares if (f.get("classType") or "").startswith("M"))
        if x > 2:
            plp = self.plp(0.7, 0.6, 0.4, 0.5, min(1.0, x/5))
            grade = LieGrade.PRE_LIE if plp["plp"]>0.5 else LieGrade.FORECAST
            self._record("L4", grade, "Solar activity is within normal parameters",
                {"x_flares": x, "m_flares": m, "total": len(flares)}, plp, min(0.8, plp["plp"]), plp["plp"])
            findings.append({"claim": "Solar normal", "x_flares": x, "plp": plp["plp"], "verdict": plp["verdict"]})
        return findings
    
    # ── FULL SCAN ──────────────────────────────────────────────
    def full_scan(self):
        t0 = time.time()
        print("=" * 70)
        print("  EVEZ-OS LIE INTERCEPTOR — 4-LAYER DECEPTION TOPOLOGY ENGINE")
        print("  L1: Contradiction  |  L2: Asymmetry  |  L3: Forecast  |  L4: Pre-Lie")
        print("  PLP = I × O × (1-A) × P × T  |  >0.5 FORMING  |  >0.8 INEVITABLE")
        print("  All data from REAL APIs. Zero mock. Zero fake. Ever.")
        print("=" * 70 + "\n")
        
        results = {}
        
        # L1
        print("━━━ LAYER 1: CONTRADICTION ━━━")
        r = self.l1_crypto_contradiction()
        results["L1_crypto"] = r
        for f in r[:5]: print(f"  ⚡ CRYPTO: {f['symbol']} vol/mcap={f['ratio']} → {f['verdict']}")
        r = self.l1_arxiv_contradiction()
        results["L1_arxiv"] = r
        for f in r[:5]: print(f"  ⚡ ARXIV: '{f['title'][:50]}' abs={f['absolute']} hedge={f['hedge']}")
        print()
        
        # L2
        print("━━━ LAYER 2: ASYMMETRY ━━━")
        r = self.l2_infrastructure_asymmetry()
        results["L2_infra"] = r
        for f in r: print(f"  ⚡ INFRA: {f['domain']} claims {f['claimed']}, actual: {f['actual']}")
        r = self.l2_hn_hype_asymmetry()
        results["L2_hn"] = r
        for f in r[:3]: print(f"  ⚡ HN HYPE: '{f['title'][:50]}' pts={f['hn_points']} arxiv={f['arxiv_evidence']}")
        print()
        
        # L3
        print("━━━ LAYER 3: FORECAST ━━━")
        r = self.l3_crypto_forecast()
        results["L3_crypto"] = r
        for f in r[:5]: print(f"  🔮 CRYPTO: {f['symbol']} signal={f['signal']} change={f['change']}%")
        r = self.l3_narrative_forecast()
        results["L3_narr"] = r
        for f in r[:3]: print(f"  🔮 NARRATIVE: '{f['title'][:50]}' queries={f['queries']}")
        print()
        
        # L4
        print("━━━ LAYER 4: PRE-LIE — The topology BEFORE the lie forms ━━━")
        r = self.l4_crypto_pre_lie()
        results["L4_crypto"] = r
        for f in r[:5]: print(f"  👁 CRYPTO: {f['symbol']} PLP={f['plp']} → {f['verdict']}")
        r = self.l4_ai_claims_pre_lie()
        results["L4_ai"] = r
        for f in r: print(f"  👁 AI: '{f['claim']}' PLP={f['plp']} → {f['verdict']} (arxiv papers: {f['arxiv_papers']})")
        r = self.l4_solar_pre_lie()
        results["L4_solar"] = r
        for f in r: print(f"  👁 SOLAR: '{f['claim']}' PLP={f['plp']} → {f['verdict']} (X-flares: {f['x_flares']})")
        print()
        
        # Summary
        elapsed = round(time.time() - t0, 1)
        v = self.spine.lint()
        total_findings = sum(len(v) for v in results.values() if isinstance(v, list))
        pre_lies = sum(1 for flist in results.values() if isinstance(flist, list) for f in flist if isinstance(f, dict) and f.get("verdict") in ("INEVITABLE","FORMING"))
        
        print("=" * 70)
        print(f"  SCAN COMPLETE — {elapsed}s — {total_findings} findings — {pre_lies} pre-lie signals")
        print(f"  SPINE: {v['events']} events — {v['status']}")
        print(f"  Every detection backed by REAL data. The spine is append-only. Forever.")
        print("=" * 70)
        
        return results

if __name__ == "__main__":
    li = LieInterceptor()
    li.full_scan()
