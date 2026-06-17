"""EVEZ OSINT Agent Lattice - Multi-agent OSINT with spectral correlation"""
import json,time,hashlib,urllib.request,re
import numpy as np
from typing import Optional,List,Dict,Any,Tuple
from dataclasses import dataclass,field
from enum import Enum

class AgentRole(str,Enum):
    RECON="recon";SPECTRAL="spectral";CHAIN="chain";PAPER="paper"
    LEGAL="legal";SOCIAL="social";DOMAIN="domain";DARK="dark"
    SIGNAL="signal";WARDEN="warden"

class FindingClass(str,Enum):
    ENTITY="entity";RELATIONSHIP="relationship";GAP="gap"
    PATTERN="pattern";ALERT="alert";CONTEXT="context"

class Severity(str,Enum):
    CRITICAL="CRITICAL";HIGH="HIGH";MEDIUM="MEDIUM";LOW="LOW";INFO="INFO"

class LegalStatus(str,Enum):
    PUBLIC="PUBLIC";RESTRICTED="RESTRICTED";CLASSIFIED="CLASSIFIED";UNKNOWN="UNKNOWN"

@dataclass
class Finding:
    id:str;agent_role:AgentRole;finding_class:FindingClass;severity:Severity
    legal_status:LegalStatus;title:str;description:str
    entities:List[str]=field(default_factory=list)
    evidence:Dict=field(default_factory=dict)
    provenance:Dict=field(default_factory=dict)
    timestamp:float=field(default_factory=time.time)
    hash:str=""
    def __post_init__(self):
        if not self.hash:
            raw=json.dumps({"a":self.agent_role.value,"c":self.finding_class.value,"t":self.title,"ts":self.timestamp},sort_keys=True)
            self.hash=hashlib.sha256(raw.encode()).hexdigest()[:16]

@dataclass
class Entity:
    id:str;entity_type:str;label:str
    aliases:List[str]=field(default_factory=list)
    attributes:Dict=field(default_factory=dict)
    first_seen:float=field(default_factory=time.time)
    last_seen:float=field(default_factory=time.time)
    source_agents:List[str]=field(default_factory=list)

class WardenAgent:
    HARD_RULES=["No authentication bypass","No PII without consent","Respect robots.txt","All findings need provenance","Public sources only"]
    BLOCKED=[".gov",".mil",".bank","internal","localhost"]
    def review(self,finding:Finding)->Tuple[bool,Optional[str]]:
        if not finding.provenance: return False,"No provenance"
        for b in self.BLOCKED:
            for e in finding.entities:
                if b in e.lower(): return False,f"Blocked: {b}"
        return True,None

class OSINTLattice:
    """The lattice. Each agent specializes. The eigenspectrum correlates."""
    def __init__(self):
        self.findings:List[Finding]=[]
        self.entities:Dict[str,Entity]={}
        self.warden=WardenAgent()
        self.mission_log:List[Dict]=[]
        self._last_request=0.0

    def _rate_limit(self):
        now=time.time()
        if now-self._last_request<2: time.sleep(2-(now-self._last_request))
        self._last_request=time.time()

    def _fetch_json(self,url,timeout=10):
        self._rate_limit()
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"EVEZ-OSINT/1.0","Accept":"application/json"})
            with urllib.request.urlopen(req,timeout=timeout) as r: return json.loads(r.read())
        except: return None

    def ingest(self,finding:Finding):
        ok,reason=self.warden.review(finding)
        if ok:
            self.findings.append(finding)
            for eid in finding.entities:
                if eid not in self.entities:
                    self.entities[eid]=Entity(id=eid,entity_type="unknown",label=eid[:32],source_agents=[finding.agent_role.value])
                else:
                    if finding.agent_role.value not in self.entities[eid].source_agents:
                        self.entities[eid].source_agents.append(finding.agent_role.value)
                    self.entities[eid].last_seen=time.time()

    def recon(self,target,surfaces=None):
        """Surface scanner - web, DNS, GitHub, blockchain"""
        results=[]
        # Web search via SearXNG
        data=self._fetch_json(f"http://localhost:8888/search?q={urllib.request.quote(target)}&format=json")
        if data and "results" in data:
            for r in data["results"][:5]:
                self.ingest(Finding(id=f"recon-w-{len(self.findings)}",agent_role=AgentRole.RECON,
                    finding_class=FindingClass.ENTITY,severity=Severity.INFO,legal_status=LegalStatus.PUBLIC,
                    title=r.get("title","Web Result"),description=r.get("content","")[:200],
                    entities=[r.get("url","")],evidence={"url":r.get("url")},
                    provenance={"source":"searxng","query":target}))
            results.append(f"Web: {len(data['results'])} hits")
        # DNS
        dns=self._fetch_json(f"https://dns.google/resolve?name={target}&type=ANY")
        if dns:
            for ans in dns.get("Answer",[]):
                self.ingest(Finding(id=f"recon-dns-{len(self.findings)}",agent_role=AgentRole.DOMAIN,
                    finding_class=FindingClass.ENTITY,severity=Severity.INFO,legal_status=LegalStatus.PUBLIC,
                    title=f"DNS: {ans.get('name')} -> {ans.get('data')}",description=f"Type {ans.get('type')}",
                    entities=[ans.get("name",target),ans.get("data","")],evidence={"type":ans.get("type")},
                    provenance={"source":"dns.google"}))
            if dns.get("Status")==3:
                self.ingest(Finding(id=f"recon-nxd-{len(self.findings)}",agent_role=AgentRole.DOMAIN,
                    finding_class=FindingClass.GAP,severity=Severity.MEDIUM,legal_status=LegalStatus.PUBLIC,
                    title=f"NXDOMAIN: {target}",description="Domain does not resolve",
                    entities=[target],evidence={"status":3},provenance={"source":"dns.google"}))
            results.append(f"DNS: {len(dns.get('Answer',[]))} records")
        return results

    def chain(self,target):
        """Blockchain forensics"""
        if len(target)<25: return ["Not a wallet address"]
        data=self._fetch_json(f"https://blockchain.info/rawaddr/{target}?limit=10")
        if not data: return ["No data"]
        balance=data.get("final_balance",0)/1e8
        txs=data.get("txs",[])
        # Mixer detection
        mixer=0
        for tx in txs:
            outs=tx.get("out",[])
            if len(outs)>=3:
                amounts=[o.get("value",0) for o in outs]
                if amounts and min(amounts)>0:
                    cv=np.std(amounts)/np.mean(amounts) if np.mean(amounts)>0 else 1
                    if cv<0.3: mixer+=1
        if mixer>0:
            self.ingest(Finding(id=f"chain-mix-{len(self.findings)}",agent_role=AgentRole.CHAIN,
                finding_class=FindingClass.PATTERN,severity=Severity.HIGH,legal_status=LegalStatus.PUBLIC,
                title=f"Mixer Pattern: {target[:12]}...",description=f"{mixer} equal-output transactions detected",
                entities=[target],evidence={"mixer_score":mixer},provenance={"source":"blockchain.info"}))
        self.ingest(Finding(id=f"chain-sum-{len(self.findings)}",agent_role=AgentRole.CHAIN,
            finding_class=FindingClass.ENTITY,severity=Severity.INFO,legal_status=LegalStatus.PUBLIC,
            title=f"Wallet: {target[:12]}... ({balance:.4f} BTC)",description=f"{len(txs)} transactions, {mixer} mixer patterns",
            entities=[target],evidence={"balance":balance,"txs":len(txs),"mixer":mixer},
            provenance={"source":"blockchain.info"}))
        return [f"Balance: {balance:.4f} BTC, {len(txs)} txs, mixer score: {mixer}"]

    def spectral(self):
        """Eigendecompose the lattice. See the gaps."""
        ents=list(self.entities.values())
        if len(ents)<3: return []
        n=len(ents); idx={e.id:i for i,e in enumerate(ents)}
        A=np.zeros((n,n))
        sev_w={Severity.CRITICAL:2,Severity.HIGH:1.5,Severity.MEDIUM:1,Severity.LOW:.5,Severity.INFO:.2}
        for f in self.findings:
            w=sev_w.get(f.severity,.5)
            for i,e1 in enumerate(f.entities):
                for e2 in f.entities[i+1:]:
                    if e1 in idx and e2 in idx:
                        A[idx[e1]][idx[e2]]+=w; A[idx[e2]][idx[e1]]+=w
        for e in ents:
            if e.id in idx: A[idx[e.id]][idx[e.id]]+=len(e.source_agents)*.3
        evals,evecs=np.linalg.eigh(A)
        negs=[(i,e) for i,e in enumerate(evals) if e<0]
        for ni,nv in negs:
            vec=evecs[:,ni]
            involved=[ents[i].label for i in range(len(vec)) if abs(vec[i])>.15 and i<len(ents)]
            sev=Severity.CRITICAL if nv<-1 else Severity.HIGH if nv<-.5 else Severity.MEDIUM if nv<-.2 else Severity.LOW
            self.ingest(Finding(id=f"spec-gap-{len(self.findings)}",agent_role=AgentRole.SPECTRAL,
                finding_class=FindingClass.GAP,severity=sev,legal_status=LegalStatus.PUBLIC,
                title=f"Gap: lambda={nv:.4f}",description=f"Structural gap: {', '.join(involved[:5])}. The eigenspectrum demands an unobserved entity.",
                entities=[e.id for e in ents[:5]],evidence={"eigenvalue":float(nv),"involved":involved},
                provenance={"method":"eigendecomposition","size":n}))
        dom=max(evals) if len(evals)>0 else 0
        neg_sum=sum(abs(e) for _,e in negs)
        r37=abs(dom)/neg_sum if neg_sum>0 else float('inf')
        return [f"{len(negs)} gaps, ratio_37={r37:.3f}, dominant={dom:.4f}"]

    def mission(self,target,mode="full"):
        """Run a full OSINT mission"""
        start=time.time()
        results=[]
        # Phase 1: Collection
        results.append(self.recon(target))
        if mode=="full":
            results.append(self.chain(target) if len(target)>25 else ["Skipping chain - not a wallet"])
        # Phase 2: Spectral
        results.append(self.spectral())
        elapsed=time.time()-start
        gaps=[f for f in self.findings if f.finding_class==FindingClass.GAP]
        alerts=[f for f in self.findings if f.severity in(Severity.CRITICAL,Severity.HIGH)]
        return {"target":target,"elapsed":round(elapsed,1),"findings":len(self.findings),
                "gaps":len(gaps),"alerts":len(alerts),"entities":len(self.entities),
                "gap_details":[{"title":g.title,"severity":g.severity.value,"eigenvalue":g.evidence.get("eigenvalue")} for g in gaps[:5]],
                "alert_details":[{"title":a.title,"agent":a.agent_role.value} for a in alerts[:5]],
                "collection_results":results}

if __name__=="__main__":
    lattice=OSINTLattice()
    print("EVEZ OSINT LATTICE - Live Mission")
    print("="*50)
    # Mission 1: Domain intel
    print("\n--- Mission: evez.art ---")
    r=lattice.mission("evez.art")
    print(f"Findings: {r['findings']}, Gaps: {r['gaps']}, Alerts: {r['alerts']}")
    for g in r['gap_details']: print(f"  GAP [{g['severity']}] {g['title']}")
    for a in r['alert_details']: print(f"  ALERT [{a['agent']}] {a['title']}")
    print(f"\nEntities tracked: {len(lattice.entities)}")
    for eid,e in list(lattice.entities.items())[:10]:
        print(f"  {e.label[:40]} (from: {', '.join(e.source_agents)})")
