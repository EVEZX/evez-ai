# EVEZ Credit Scoring API Reference

## Base URLs
- **Supabase Edge Function**: `https://vziaqxquzohqskesuxgz.supabase.co/functions/v1/`
- **FastAPI (Fly.io)**: `https://evez-credit-api.fly.dev/` (pending deployment)

## Endpoints

### POST /credit-score
Score a single applicant.

**Request Body (inline profile)**:
```json
{
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
}
```

**Request Body (by applicant ID)**:
```json
{
  "applicant_id": "a0000000-0000-0000-0000-000000000001"
}
```

**Response**:
```json
{
  "credit_score": 720,
  "grade": "A-",
  "decision": "APPROVED",
  "default_probability": 0.0573,
  "risk_level": "low",
  "factors": {
    "payment_history": { "raw": 92, "normalized": 0.92, "weight": 0.35, "contribution": 0.322 },
    "credit_utilization": { "raw": 25, "normalized": 0.75, "weight": 0.2, "contribution": 0.15 }
  },
  "adverse_actions": [
    { "factor": "credit_age", "score": 0.4, "severity": "medium" }
  ],
  "compliance": {
    "ecoa": true,
    "fcra": true,
    "model": "EVEZ-CS-v2.0",
    "scored_at": "2026-04-25T21:42:06.432Z"
  }
}
```

### POST /portfolio-analytics
Get portfolio-wide analytics.

**Response**:
```json
{
  "total": 10,
  "average_score": 672.1,
  "approval_rate": 70,
  "decisions": { "approved": 7, "denied": 3, "manual_review": 0 },
  "score_distribution": { "excellent": 4, "good": 1, "fair": 1, "poor": 1, "very_poor": 3 },
  "avg_default_probability": 0.1791,
  "risk_breakdown": { "low": 4, "medium": 3, "high": 3 }
}
```

### POST /webhook-handler
Register and manage webhooks.

**Register webhook**:
```json
{
  "event": "register",
  "webhook_url": "https://your-endpoint.com/webhook",
  "webhook_secret": "your-secret-key"
}
```

### RPC Functions
- `SELECT get_portfolio_summary()` - Complete portfolio analytics
- `SELECT get_applicant_report('applicant-uuid')` - Full applicant dossier

### Database Views
- `v_score_trends` - Daily scoring trends
- `v_risk_concentration` - Risk level breakdown with exposure
- `v_applicant_summary` - Combined applicant + score + loan view

---
*EVEZ Credit Scoring API v2.0.0*
