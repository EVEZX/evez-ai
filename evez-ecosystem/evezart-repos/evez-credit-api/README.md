# EVEZ Credit Scoring API

**8-factor FICO-equivalent credit scoring engine. Scores 300–850 with ECOA/FCRA compliance.**

## What It Does

Takes a credit profile (payment history, utilization, credit age, mix, inquiries, DTI, derogatory marks, total accounts) and produces:

- **Credit score** (300–850, weighted factor model)
- **Grade** (A+ through F)
- **Decision** (APPROVED / MANUAL_REVIEW / DENIED)
- **Default probability** (logistic model)
- **Adverse action reasons** (FCRA-compliant, with AA codes)
- **Full factor breakdown** with per-factor contribution

## API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Service health check |
| POST | `/register` | No | Create API key (`{email, plan}`) |
| POST | `/score` | Yes | Score a single applicant |
| POST | `/batch` | Yes | Score multiple applicants |
| GET | `/model-info` | Yes | Model weights, factors, thresholds |
| GET | `/usage` | Yes | Your usage stats & remaining credits |

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run
uvicorn main:app --port 8080

# Create an API key
curl -X POST http://localhost:8080/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "plan": "free"}'

# Score an applicant
curl -X POST http://localhost:8080/score \
  -H "Authorization: Bearer evez_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_history": 92,
    "credit_utilization": 25,
    "credit_age": 10,
    "credit_mix": 4,
    "new_inquiries": 1,
    "dti_ratio": 28,
    "derogatory_marks": 0,
    "total_accounts": 12
  }'
```

### Docker

```bash
docker build -t evez-credit-api .
docker run -p 8080:8080 evez-credit-api
```

## Architecture

```
main.py                  FastAPI app, auth, rate limiting, routing
evez_credit_engine.py    Pure scoring logic (no I/O, no framework deps)
credit_db.py             SQLite persistence (scoring_requests, api_keys, usage_logs)
tests/                   pytest suite for the scoring engine
```

**Scoring model (EVEZ-CS-v2.0):**
- 8 weighted risk factors (weights sum to 1.0)
- Each factor normalized 0–1 then weighted
- Weighted sum → linearly mapped to 300–850
- Logistic function for default probability
- Grade thresholds at standard breakpoints
- Adverse action codes (AA01–AA08) for factors scoring <0.6

## What's Real vs. Planned

| Feature | Status |
|---------|--------|
| 8-factor scoring engine | ✅ Working |
| FICO-equivalent 300–850 range | ✅ Working |
| ECOA/FCRA adverse action codes | ✅ Working |
| API key authentication | ✅ Working (SQLite) |
| Rate limiting (per-key) | ✅ Working (in-memory) |
| SQLite persistence | ✅ Working |
| Batch scoring | ✅ Working |
| Stripe integration | 🔲 Planned |
| PostgreSQL migration | 🔲 Planned |
| Dashboard/UI | 🔲 Planned |
| Model validation/backtesting | 🔲 Planned |

## Configuration

Copy `.env.example` to `.env` and fill in values. All vars are optional with sensible defaults.

## License

MIT
