# EVEZ Credit Scoring Engine v2.0

## Real-Time, FICO-Equivalent Credit Scoring

Unlock instant, compliant credit decisions with our open-source 8-factor scoring API — 300-850 range, ECOA/FCRA compliant, powered by Supabase Edge Functions.

### Features
- **8-factor, 300-850 score** matching FICO methodology
- **Zero-latency real-time API** via Supabase Edge Functions
- **Fully open source** on GitHub, ECOA/FCRA compliant

### Quick Start
```bash
curl -X POST https://vziaqxquzohqskesuxgz.supabase.co/functions/v1/credit-score \
  -H 'Content-Type: application/json' \
  -d '{
    "profile": {
      "payment_history": 92,
      "credit_utilization": 25,
      "credit_age": 10,
      "credit_mix": 4,
      "new_inquiries": 1,
      "dti_ratio": 28,
      "derogatory_marks": 0,
      "total_accounts": 12
    }
  }'
```

### Response
```json
{
  "credit_score": 720,
  "grade": "A-",
  "decision": "APPROVED",
  "default_probability": 0.0573,
  "risk_level": "low"
}
```

### Endpoints
| Endpoint | Description |
|----------|-------------|
| `/credit-score` | Score single applicant |
| `/portfolio-analytics` | Portfolio-wide analytics |
| `/webhook-handler` | Webhook management |
| `/health-check` | System health status |

### Try EVEZ Now
[GitHub Repository](https://github.com/EvezArt/evez-credit-api) | [API Docs](docs/API_REFERENCE.md) | [Model Validation](docs/MODEL_VALIDATION.md)
