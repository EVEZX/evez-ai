# 🔐 EVEZ Secrets Manifest

Every GitHub Actions secret required across the EVEZ ecosystem.
Set via: repo **Settings → Secrets and Variables → Actions**.

---

## evezstation — Fly.io Deploy

| Secret | Description | Source |
|--------|-------------|--------|
| `FLY_API_TOKEN` | Fly.io deploy token | `flyctl auth token` |
| `SUPABASE_URL` | Supabase project URL | `https://vziaqxquzohqskesuxgz.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service_role key | Supabase → Settings → API |
| `GROQ_API_KEY` | GroqCloud API key | console.groq.com/keys |
| `AWS_ACCESS_KEY_ID` | S3 key | Fly.io Tigris addon |
| `AWS_SECRET_ACCESS_KEY` | S3 secret | same |
| `AWS_ENDPOINT_URL_S3` | S3 endpoint | e.g. `https://<acct>.r2.cloudflarestorage.com` |
| `AWS_REGION` | S3 region | `auto` for R2 |
| `BUCKET_NAME` | Bucket name | your bucket |

❌ `FLY_API_TOKEN` missing → deploy blocked (EVE-59)

---

## moltbot-live — VCL Stream

| Secret | Description | Source |
|--------|-------------|--------|
| `FLY_API_TOKEN` | Fly.io deploy token | `flyctl auth token` |

❌ `FLY_API_TOKEN` missing → VCL stream blocked (EVE-27)

---

## evez-agentnet — Income Loop

| Secret | Description | Source |
|--------|-------------|--------|
| `GROQ_API_KEY` | Groq inference | console.groq.com/keys |

---

## Root Cause: Why CI Is Red Everywhere

```
PRIMARY BLOCKER (EVE-5)
  GitHub billing failure → runners not allocated → empty job steps
  Fix: github.com/settings/billing

SECONDARY (now fixed in evezstation, PR open for evez-os)
  evez-os:      Missing pip install before OODA Python [PR open]
  evezstation:  Missing GROQ_API_KEY in deploy.yml   [MERGED]

STILL NEEDS MANUAL ACTION
  evezstation + moltbot-live: FLY_API_TOKEN not set in repo secrets
  evezstation:  SUPABASE_SERVICE_KEY, AWS_* not set
  evez-agentnet: GROQ_API_KEY not set
```

## Quick Checklist

- [ ] Fix GitHub billing → github.com/settings/billing  
- [ ] `flyctl auth token` → add as `FLY_API_TOKEN` to evezstation + moltbot-live  
- [ ] Supabase service_role key → `SUPABASE_SERVICE_KEY` in evezstation  
- [ ] GroqCloud key → `GROQ_API_KEY` in evezstation + evez-agentnet  
- [ ] Merge PR: fix/ci-deps-health-monitor into evez-os main  
