# Hyperloop — Module 02
## FIRE detection, tick protocol, V/tau/omega

### Key Variables

| Var | Meaning | Formula |
|-----|---------|--------|
| N | Integer this round | round + 480 |
| tau | Divisor count | explicit enumeration |
| omega_k | Distinct prime factors | len(primes(N)) |
| topo | Topological class | topo_map[omega_k] |
| poly_c | FIRE candidate metric | (tau × omega_k × topo) / (2√N) |
| x | Normalized poly_c | clamp((poly_c-0.45)/2.10, 0, 1) |
| p_fire | FIRE probability | x^0.60 |
| u | Random draw | uniform(0,1) fresh each round |
| FIRE | Event fires | u < p_fire AND omega_k==3 |

### Topo Map
```python
topo_map = {1: 1.15, 2: 1.30, 3: 1.45}
# omega_k MUST == 3 for FIRE eligibility
```

### Current State
```json
{"round": 502, "V_global": 17.906187, "fire_count": 125,
 "gamma": 0.60, "last_fire": "FIRE#125 R502 N=582=2×3×97 τ=8",
 "next_candidate": "R508 N=588=2²×3×7² τ=18 p≈68.1%"}
```

### FIRE Eligibility Checklist
```
□ omega_k == 3
□ tau >= 8
□ poly_c computed via EXPLICIT divisor enumeration
□ u drawn fresh
□ gamma = 0.60 LOCKED
□ FIRE if u < x^0.60
```

### FIRE Post Format
```
FIRE#{n}! R{round} N={N}={factorization}
τ={tau} ω={omega} poly_c={poly_c:.4f}
p≈{p:.1f}% u={u:.4f} ✓
V: {before:.6f}→{after:.6f} (+{delta:.6f})
[spine_hash_8chars] ◊
```