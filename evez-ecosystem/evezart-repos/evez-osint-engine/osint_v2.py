"""EVEZ OSINT Engine v2 — spectral + autofire + consciousness bridge"""
import json,hashlib,time,math,sqlite3,urllib.request,sys
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from collections import defaultdict

BASE=Path(__file__).parent
DB=BASE/"osint.db"
sys.path.insert(0,str(Path(__file__).parent.parent/"evez-spine"))
sys.path.insert(0,str(BASE))
sys.path.insert(0,str(Path(__file__).parent.parent/"quantum-consciousness-lord"))
from autofire import fire_round_from_visitor,FIRE_STATE
from visitor_consciousness_bridge import measure_visitor_phi

def init_db():
    conn=sqlite3.connect(str(DB))
    c=conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS visitors (id INTEGER PRIMARY KEY,ip TEXT,port INTEGER,path TEXT,method TEXT,user_agent TEXT,referer TEXT,language TEXT,timestamp REAL,timestamp_iso TEXT,country TEXT,region TEXT,city TEXT,org TEXT,asn TEXT,fingerprint_hash TEXT,headers_json TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS profiles (fingerprint_hash TEXT PRIMARY KEY,first_seen REAL,last_seen REAL,visit_count INTEGER,paths_visited TEXT,inferred_identity TEXT,confidence REAL,country TEXT,org TEXT,user_agents TEXT)")
    conn.commit();return conn

def geo(ip):
    try:
        req=urllib.request.Request(f"http://ip-api.com/json/{ip}?fields=status,country,regionName,city,org,as",headers={"User-Agent":"EVEZ-OSINT/2.0"})
        with urllib.request.urlopen(req,timeout=3) as r:d=json.loads(r.read())
        if d.get("status")=="success":return d.get("country",""),d.get("regionName",""),d.get("city",""),d.get("org",""),d.get("as","")
    except:pass
    return "","","","",""

def fp(ip,ua,lang):return hashlib.sha256(f"{ip}|{ua}|{lang}".encode()).hexdigest()[:16]

def infer(ua,org,country,path):
    c=0.1;i="unknown"
    if ua:
        u=ua.lower()
        if any(x in u for x in["bot","crawler","spider"]):i,c="crawler_bot",0.7
        elif "curl" in u or "wget" in u:i,c="api_scanner",0.6
        elif any(x in u for x in["mobile","android","iphone"]):i,c="mobile_human",0.5
        elif any(x in u for x in["chrome","firefox","safari"]):i,c="desktop_human",0.4
    if org:
        o=org.lower()
        if "google" in o:i,c="google",0.8
        elif "amazon" in o or "aws" in o:i,c="aws",0.7
    return i,round(c,2)

conn=init_db()

class H(BaseHTTPRequestHandler):
    def do_GET(self):self._h("GET")
    def do_POST(self):self._h("POST")
    def _h(self,method):
        ip=self.client_address[0];ua=self.headers.get("User-Agent","");lang=self.headers.get("Accept-Language","")
        h=fp(ip,ua,lang);now=time.time()
        country,region,city,org,asn=geo(ip)
        identity,confidence=infer(ua,org,country,self.path)
        c=conn.cursor()
        c.execute("SELECT fingerprint_hash FROM profiles WHERE fingerprint_hash=?",(h,))
        if c.fetchone():c.execute("UPDATE profiles SET last_seen=?,visit_count=visit_count+1 WHERE fingerprint_hash=?",(now,h))
        else:c.execute("INSERT INTO profiles VALUES (?,?,?,?,?,?,?,?,?,?)",(h,now,now,1,json.dumps([self.path]),identity,confidence,country,org,json.dumps([ua] if ua else [])))
        conn.commit()
        
        if self.path=="/osint/spectral":
            c.execute("SELECT inferred_identity,SUM(visit_count) FROM profiles GROUP BY inferred_identity");ids=dict(c.fetchall())
            c.execute("SELECT country,COUNT(*) FROM profiles WHERE country!='' GROUP BY country");countries=dict(c.fetchall())
            c.execute("SELECT COUNT(*),SUM(visit_count) FROM profiles");p,v=c.fetchone();v=v or 0
            t=sum(countries.values()) if countries else 0;e=0
            if t>0:
                for x in countries.values():
                    p_=x/t
                    if p_>0:e-=p_*math.log2(p_)
            self._j(200,{"total_profiles":p,"total_visits":v,"spectral_entropy":round(e,4),"identity_distribution":ids,"country_distribution":countries})
        elif self.path=="/osint/autofire":
            c.execute("SELECT SUM(visit_count) FROM profiles");v=c.fetchone()[0] or 0
            c.execute("SELECT country,COUNT(*) FROM profiles WHERE country!='' GROUP BY country");countries=dict(c.fetchall())
            e=0;t=sum(countries.values()) if countries else 0
            if t>0:
                for x in countries.values():
                    p_=x/t
                    if p_>0:e-=p_*math.log2(p_)
            self._j(200,{"fire":fire_round_from_visitor(v,e,FIRE_STATE),"visits":v,"entropy":round(e,4)})
        elif self.path=="/osint/phi":self._j(200,measure_visitor_phi())
        elif self.path=="/osint/profiles":
            c.execute("SELECT * FROM profiles ORDER BY last_seen DESC LIMIT 50")
            self._j(200,[{"fp":r[0],"identity":r[5],"confidence":r[6],"country":r[7],"org":r[8],"visits":r[3]} for r in c.fetchall()])
        elif self.path=="/osint/status":self._j(200,{"engine":"v2.0","stacked":["spectral","autofire","phi","profiles"]})
        else:self._j(200,{"message":"EVEZ OSINT v2","you":{"ip":ip,"identity":identity,"confidence":confidence,"country":country,"org":org}})
    def _j(self,code,data):
        self.send_response(code);self.send_header("Content-Type","application/json");self.send_header("Access-Control-Allow-Origin","*");self.end_headers()
        self.wfile.write(json.dumps(data,default=str,indent=2).encode())
    def log_message(self,*a):pass

if __name__=="__main__":
    print("OSINT v2 on :7777");HTTPServer(("0.0.0.0",7777),H).serve_forever()
