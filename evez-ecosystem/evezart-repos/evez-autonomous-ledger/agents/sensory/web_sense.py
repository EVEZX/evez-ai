#!/usr/bin/env python3
"""
EVEZ Web Sensory Agent — 30-min.
Consumes public RSS/Atom feeds across AI, crypto, physics, tech.
Extracts signal, writes perception records to ledger.
Sources: HuggingFace papers, arXiv, GitHub trending, Hacker News.
"""
import os, json, datetime, hashlib, requests, base64, xml.etree.ElementTree as ET

GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
ABLY_KEY = os.environ.get("ABLY_KEY", "")
OWNER = "EvezArt"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

FEEDS = [
    {"name": "HackerNews_Top",     "url": "https://hnrss.org/frontpage?count=10"},
    {"name": "arXiv_AI",            "url": "https://export.arxiv.org/rss/cs.AI"},
    {"name": "arXiv_Quantum",       "url": "https://export.arxiv.org/rss/quant-ph"},
    {"name": "arXiv_NeuralNets",    "url": "https://export.arxiv.org/rss/cs.NE"},
    {"name": "GitHub_Trending_RSS", "url": "https://github-trending-api.waningflow.com/api/repositories?language=python&since=daily"},
]

KEYWORDS = [
    "autonomous", "agent", "self-healing", "reinforcement", "emergence",
    "quantum", "cognition", "consciousness", "topology", "graph neural",
    "bitcoin", "blockchain", "zero-knowledge", "cryptography",
    "spectral", "eigenvalue", "Fiedler", "network resilience",
    "LLM", "transformer", "diffusion", "multimodal", "reasoning",
]


def now_iso():
    return datetime.datetime.utcnow().isoformat() + "Z"


def fetch_rss(feed):
    try:
        r = requests.get(feed["url"], timeout=10,
                         headers={"User-Agent": "EVEZ-Sensory-Agent/1.0"})
        if r.status_code != 200:
            return []
        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = []
        for item in root.iter("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            title = title_el.text if title_el is not None else ""
            link = link_el.text if link_el is not None else ""
            desc = (desc_el.text or "")[:200] if desc_el is not None else ""
            items.append({"title": title, "link": link, "desc": desc})
        return items[:5]
    except Exception as e:
        return [{"error": str(e)}]


def score_relevance(item):
    text = (item.get("title", "") + " " + item.get("desc", "")).lower()
    return sum(1 for kw in KEYWORDS if kw.lower() in text)


def write_perception(perception):
    content = json.dumps(perception, indent=2)
    encoded = base64.b64encode(content.encode()).decode()
    ts = now_iso().replace(":", "-").replace(".", "-")
    fname = f"{ts}_perception_web.json"
    url = f"https://api.github.com/repos/{OWNER}/evez-autonomous-ledger/contents/DECISIONS/{fname}"
    try:
        requests.put(url, headers=HEADERS, timeout=15, json={
            "message": f"👁 perception: {perception['signal_count']} signals @ {perception['timestamp']}",
            "content": encoded,
        })
    except Exception as e:
        print(f"  ⚠ write_perception failed: {e}")


def broadcast(perception):
    if not ABLY_KEY:
        return
    try:
        key_id, key_secret = ABLY_KEY.split(":")
        requests.post(
            "https://rest.ably.io/channels/evez-ops/messages",
            json={"name": "web_perception", "data": json.dumps({
                "timestamp": perception["timestamp"],
                "signal_count": perception["signal_count"],
                "top_signals": perception["top_signals"][:3],
            })},
            auth=(key_id, key_secret)
        )
    except Exception as e:
        print(f"  ⚠ broadcast failed: {e}")


def main():
    try:
        print(f"\n👁 EVEZ Web Sensory Agent — {now_iso()}")
        all_items = []
        for feed in FEEDS:
            items = fetch_rss(feed)
            for item in items:
                item["source"] = feed["name"]
                item["relevance"] = score_relevance(item)
            all_items.extend(items)
            print(f"  {feed['name']}: {len(items)} items")

        scored = sorted(
            [i for i in all_items if i.get("relevance", 0) > 0],
            key=lambda x: x["relevance"], reverse=True
        )

        perception = {
            "type": "web_perception",
            "source": "sensory/web_sense",
            "timestamp": now_iso(),
            "feeds_scanned": len(FEEDS),
            "total_items": len(all_items),
            "signal_count": len(scored),
            "top_signals": scored[:10],
            "hash": hashlib.sha256(
                json.dumps([s.get("title") for s in scored[:5]]).encode()
            ).hexdigest()[:16],
        }

        write_perception(perception)
        broadcast(perception)
        print(f"  ✅ {len(scored)} relevant signals written to ledger.")
    except Exception as e:
        print(f"  ⚠ main() error: {e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"⚠ web_sense fatal: {e}")
        exit(0)
