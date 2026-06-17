# Auth Completion Guide

## ClawHub (Skills Marketplace)

**Problem:** Browser-based OAuth, CLI waiting for callback

**Solution — Complete in your terminal:**
```bash
# Run this in your local terminal (not in OpenClaw):
clawhub login
```

This will:
1. Open your browser to ClawHub
2. You log in / authorize
3. CLI receives token automatically
4. Then we can: `clawhub publish ./evez-skills/invariance-battery`

---

## X (Twitter)

**Problem:** No apps registered

**Solution — Set up once:**
```bash
# 1. Register a Twitter app at https://developer.x.com/
# 2. Get your API keys (Consumer Key/Secret)
# 3. Run in your terminal:
xurl auth oauth2
# Follow the OAuth flow to authorize
```

**Once authenticated, I can post tweets:**
```bash
xurl post "BCI stack is forming..."
```

---

## Gmail / Google Workspace

**Problem:** Requires OAuth credentials

**Solution — Set up once:**
```bash
# 1. Get OAuth credentials from Google Cloud Console
# 2. Run:
gog auth add your@email.com --services gmail,calendar
# Follow the OAuth flow
```

**Then I can send emails/dm for you.**

---

## GitHub ✅ Already Done

- Token: `GITHUB_TOKEN` env var
- Status: Logged in as EvezArt
- Ready for: pushing, PRs, issues

---

## Summary

| Service | Status | Action Needed |
|---------|--------|---------------|
| GitHub | ✅ Ready | None |
| ClawHub | ⏳ Waiting | Run `clawhub login` in your terminal |
| X/Twitter | ⏳ Waiting | Run `xurl auth oauth2` in your terminal |
| Gmail | ⏳ Waiting | Run `gog auth add` in your terminal |

Run any of those commands locally, then tell me and I'll continue deploying.