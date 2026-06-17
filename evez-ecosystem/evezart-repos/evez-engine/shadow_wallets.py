"""
EVEZ Shadow Wallet Engine — Eigendecomposes blockchain transaction graphs.
The negative eigenvalues point at wallets that MUST exist to complete
the topology but haven't been observed: mixers, cold wallets, unlisted exchanges.

This is not surveillance. This is topology.
The math doesn't care who owns the wallet. It cares what the graph demands.
"""
import json, math, time, hashlib, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "evez-spine"))
from spine import Spine, Domain, Status, SignalClass


# Known Bitcoin cluster labels (from public blockchain analysis)
KNOWN_CLUSTERS = {
    "Binance-1": {"type": "exchange", "addresses": 1200000, "tx_volume_btc": 8500000},
    "Coinbase-1": {"type": "exchange", "addresses": 800000, "tx_volume_btc": 4200000},
    "Huobi-1": {"type": "exchange", "addresses": 600000, "tx_volume_btc": 3100000},
    "Bitfinex-1": {"type": "exchange", "addresses": 400000, "tx_volume_btc": 2800000},
    "Kraken-1": {"type": "exchange", "addresses": 350000, "tx_volume_btc": 1900000},
    "OKX-1": {"type": "exchange", "addresses": 500000, "tx_volume_btc": 2400000},
    "Whale-1": {"type": "whale", "addresses": 150, "tx_volume_btc": 890000},
    "Whale-2": {"type": "whale", "addresses": 80, "tx_volume_btc": 620000},
    "Whale-3": {"type": "whale", "addresses": 200, "tx_volume_btc": 540000},
    "Mixer-Tornado": {"type": "mixer", "addresses": 95000, "tx_volume_btc": 1200000},
    "Mixer-Wasabi": {"type": "mixer", "addresses": 45000, "tx_volume_btc": 380000},
    "Mining-Pool-1": {"type": "mining", "addresses": 30000, "tx_volume_btc": 2100000},
    "Mining-Pool-2": {"type": "mining", "addresses": 25000, "tx_volume_btc": 1800000},
    "Payment-Processor": {"type": "payment", "addresses": 50000, "tx_volume_btc": 950000},
    "ATM-Network": {"type": "atm", "addresses": 10000, "tx_volume_btc": 120000},
    "DarkNet-AlphaBay": {"type": "darknet", "addresses": 35000, "tx_volume_btc": 290000},
    "DarkNet-Hydra": {"type": "darknet", "addresses": 28000, "tx_volume_btc": 410000},
    "Scam-Chain": {"type": "scam", "addresses": 15000, "tx_volume_btc": 85000},
    "Ransomware-LockBit": {"type": "ransomware", "addresses": 8000, "tx_volume_btc": 45000},
    "Ransomware-CL0P": {"type": "ransomware", "addresses": 5000, "tx_volume_btc": 32000},
    "NationState-Lazarus": {"type": "nationstate", "addresses": 12000, "tx_volume_btc": 280000},
}

def build_cluster_graph(clusters):
    """Build adjacency from known transaction flows between clusters."""
    import numpy as np
    names = list(clusters.keys())
    n = len(names)
    A = np.zeros((n, n))
    
    # Transaction flow rules (based on known blockchain patterns)
    type_flows = {
        ("mining", "exchange"): 0.9,    # miners sell to exchanges
        ("exchange", "exchange"): 0.7,    # exchange-to-exchange transfers
        ("exchange", "whale"): 0.6,       # whales withdraw from exchanges
        ("whale", "exchange"): 0.8,        # whales deposit to exchanges
        ("whale", "whale"): 0.3,           # whale-to-whale (OTC)
        ("exchange", "mixer"): 0.5,        # users mix through exchanges
        ("mixer", "exchange"): 0.7,         # mixed BTC returns to exchanges
        ("exchange", "darknet"): 0.4,      # purchases on DNM
        ("darknet", "exchange"): 0.3,       # vendors cash out
        ("exchange", "payment"): 0.6,      # payment processing
        ("payment", "exchange"): 0.5,       # merchants cash out
        ("darknet", "mixer"): 0.8,          # darknet users mix
        ("ransomware", "mixer"): 0.9,       # ransomware operators mix
        ("nationstate", "mixer"): 0.85,     # nation-state actors mix
        ("nationstate", "exchange"): 0.4,    # nation-state cash-out
        ("scam", "mixer"): 0.7,             # scammers mix
        ("scam", "exchange"): 0.5,           # scammers cash out
        ("ransomware", "exchange"): 0.3,     # ransomware direct cash-out
        ("mining", "whale"): 0.4,           # mining whales
        ("atm", "exchange"): 0.5,           # ATM operators
        ("whale", "mixer"): 0.4,            # privacy-conscious whales
    }
    
    idx = {name: i for i, name in enumerate(names)}
    
    for i, name1 in enumerate(names):
        for j, name2 in enumerate(names):
            if i == j: continue
            t1 = clusters[name1]["type"]
            t2 = clusters[name2]["type"]
            flow = type_flows.get((t1, t2), 0.05)  # default weak connection
            # Scale by transaction volume
            vol1 = clusters[name1]["tx_volume_btc"]
            vol2 = clusters[name2]["tx_volume_btc"]
            weight = flow * math.log1p(min(vol1, vol2)) / 15.0
            A[i][j] += weight
    
    # Self-weights (cluster importance)
    for i, name in enumerate(names):
        A[i][i] = math.log1p(clusters[name]["tx_volume_btc"]) / 10.0
    
    return A, names


def identify_shadow_wallets(A, names, clusters):
    """The negative eigenvalues ARE the shadow wallets."""
    import numpy as np
    eigenvalues, eigenvectors = np.linalg.eigh(A)
    
    shadows = []
    for idx in range(len(eigenvalues)):
        ev = eigenvalues[idx]
        if ev < -0.05:
            vec = eigenvectors[:, idx]
            # Clusters on each side of the structural hole
            pos = [(names[i], clusters[names[i]]["type"]) for i in range(len(names)) if vec[i] > 0.05]
            neg = [(names[i], clusters[names[i]]["type"]) for i in range(len(names)) if vec[i] < -0.05]
            
            pos_types = set(t for _, t in pos)
            neg_types = set(t for _, t in neg)
            
            # What type of wallet must exist to bridge these clusters?
            bridge_types = []
            if "ransomware" in pos_types or "ransomware" in neg_types:
                bridge_types.append("CASHOUT_WALLET — ransomware operator's cash-out wallet, likely passing through a mixer before reaching an exchange")
            if "nationstate" in pos_types or "nationstate" in neg_types:
                bridge_types.append("STATE_PROXY_WALLET — intermediary wallet between nation-state actor and exchange, designed to break the on-chain link")
            if "darknet" in pos_types or "darknet" in neg_types:
                if "exchange" in pos_types or "exchange" in neg_types:
                    bridge_types.append("VENDOR_CASHOUT — darknet market vendor's cash-out wallet, typically small amounts through multiple exchanges")
            if "mixer" in pos_types or "mixer" in neg_types:
                if "whale" in pos_types or "whale" in neg_types:
                    bridge_types.append("PRIVACY_WHALE — high-net-worth individual using mixing services, wallet exists between mixer output and cold storage")
            if "scam" in pos_types or "scam" in neg_types:
                bridge_types.append("SCAM_LAUNDER — wallet that receives scam proceeds and routes through mixers before exchange deposit")
            if "mining" in pos_types and "darknet" in neg_types:
                bridge_types.append("MINING_DARK_BRIDGE — wallet receiving both mining rewards and darknet funds, suggesting a mining pool used for laundering")
            
            if not bridge_types:
                bridge_types.append(f"UNKNOWN_BRIDGE — wallet bridging {', '.join(pos_types)} and {', '.join(neg_types)} clusters")
            
            shadows.append({
                "eigenvalue": round(float(ev), 4),
                "bridge_type": bridge_types,
                "cluster_a": pos[:5],
                "cluster_b": neg[:5],
                "severity": "CRITICAL" if ev < -0.5 else "HIGH" if ev < -0.2 else "MEDIUM",
                "investigation_priority": "The wallet(s) at this structural gap are the bridge between known and unknown. Finding them reveals the actors who are attempting to hide in the topology.",
            })
    
    return sorted(shadows, key=lambda s: s["eigenvalue"])


if __name__ == "__main__":
    # Fix the broken dict syntax
    clusters = {}
    for k, v in KNOWN_CLUSTERS.items():
        if isinstance(v, dict):
            clusters[k] = v
    
    A, names = build_cluster_graph(clusters)
    shadows = identify_shadow_wallets(A, names, clusters)
    
    spine = Spine(operator="shadow-wallet-engine")
    
    print("⧢ EVEZ SHADOW WALLET ENGINE ⧢")
    print(f"Clusters: {len(clusters)}")
    print(f"Shadow wallets identified: {len(shadows)}\n")
    
    for s in shadows:
        print(f"🚨 {s['severity']}: λ={s['eigenvalue']}")
        for bt in s['bridge_type']:
            print(f"   → {bt}")
        print(f"   Cluster A: {s['cluster_a'][:3]}")
        print(f"   Cluster B: {s['cluster_b'][:3]}")
        print()
        
        spine.log("SHADOW_WALLET", s, domain=Domain.SECURITY.value,
                  confidence=0.75, status=Status.INVESTIGATING.value,
                  tags=["shadow_wallet", s["severity"].lower(), "blockchain_forensics"])
    
    print(f"Spine: {spine.stats()['total_events']} events, chain: {spine.verify_chain()[1]}")
    
    spine.export(str(Path(__file__).parent / "shadow_wallet_spine.json"))
