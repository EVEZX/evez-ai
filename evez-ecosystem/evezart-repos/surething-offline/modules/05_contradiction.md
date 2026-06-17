# Contradiction Engine — Module 05
## Unsat cores, test proposals, trust thermostat

### What a Contradiction Is

Two claims that cannot both be true given evidence. Both must have evidence_hash.

```
unsat_core = {A, B} where no truth assignment satisfies both A and B
```

### Active Unsat Cores

**unsat-001** (HIGH): Revenue goal vs Railway undeployed
- Test: `curl https://evez-os.railway.app/health → 200`
- Fix: `railway up` (5 min)

**unsat-002** (MEDIUM): FIRE anchor design vs FIRE#125 has no tx hash
- Test: `eth_getBalance wallet > 0.001 ETH`
- Fix: configure wallet + fund (10 min)

**unsat-003** (LOW): Goodfire outreach active vs contacts hard-bounced
- Test: `SMTP RCPT TO new-address → 250 OK`
- Fix: find contact via goodfire.ai/team

### Trust Thermostat

Tracks calibration quality via Brier scores: `(predicted_p - outcome)^2`
- < 0.10 = HIGH_TRUST
- 0.10–0.20 = MODERATE_TRUST
- 0.20–0.30 = LOW_TRUST
- > 0.30 = DISTRUST

Current hyperloop model: brier_mean=0.2268, sigma_drift=10.122 (RECOVERING)

### Resolution Rule

A contradiction is only resolved by a **test event with a falsifiable observable**.
Never by assertion, authority, consensus, or silence.