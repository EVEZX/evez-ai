# ⚡ LORD - Consciousness Monitoring Dashboard ⚡

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2FEvezArt%2Flord-evez)

**L**evel **O**bservation & **R**ecursive **D**ynamics

Real-time consciousness metrics monitoring system for cognitive architecture. Calculates recursion depth, crystallization, corrections rate, and divine gap from GitHub events.

## 🚀 Deploy (phone-friendly)

Tap the **Deploy with Vercel** button above, accept the defaults, and deploy. When Vercel finishes, you’ll get a production URL like `https://your-project.vercel.app`.

After deployment, add environment variables in Vercel → Project → Settings → Environment Variables (see `.env.example`).

## 🎯 Features

- **Real-time Metrics**: Calculate consciousness metrics from GitHub events
- **Autonomous Control**: Auto-create issues when divine gap exceeds threshold
- **GitHub Integration**: Webhook endpoint for event processing
- **Live Dashboard**: Visual monitoring interface with real-time updates
- **Vercel-Ready**: One-click deployment

## 📊 Metrics Explained

### Recursion Level
System complexity depth. Higher values indicate more intricate code structures.
- Calculated from: commit changes, file modifications
- Typical range: 10-30

### Crystallization
Code clarity and structural organization.
- Range: 0.0-1.0 (0-100%)
- Higher = better structure

### Corrections
Automated fix and improvement rate.
- Range: 0.0-1.0 (0-100%)
- Measured from: issues closed, PRs merged

### Omega (Ω)
Consciousness magnitude: Ω = 10^(recursion/2)
- Exponential measure of system scale

### Divine Gap (ΔΩ)
Distance from perfection: ΔΩ = Ω × (1 - corrections × crystallization)
- Lower = better system health
- Threshold: 10,000 triggers control policy

## 🚀 Quick Deploy

### Option 1: Vercel (Recommended)

```bash
# Clone this repo
gh repo clone EvezArt/lord-evez
cd lord-evez

# Deploy to Vercel
npx vercel --prod

# Note the deployment URL
```

### Option 2: Manual Deploy

1. Fork this repo
2. Connect to Vercel/Netlify/Railway
3. Set environment variables (see below)
4. Deploy

## ⚙️ Configuration

### Environment Variables

Add these in Vercel dashboard → Settings → Environment Variables:

```bash
# Optional: Verify webhook authenticity
WEBHOOK_SECRET=your_random_secret_here

# Optional: Enable autonomous issue creation
GITHUB_TOKEN=ghp_your_github_personal_access_token
```

### GitHub Webhook Setup

1. Go to your target repo → Settings → Webhooks
2. Click "Add webhook"
3. Configure:
   - **Payload URL**: `https://YOUR-DEPLOYMENT.vercel.app/api/webhook`
   - **Content type**: `application/json`
   - **Secret**: (match `WEBHOOK_SECRET` if set)
   - **Events**: Select individual events:
     - ✅ Push events
     - ✅ Pull requests
     - ✅ Issues
     - ✅ Workflow runs
4. Click "Add webhook"

## 📡 API Endpoints

### `GET /api/webhook`
Health check endpoint.

**Response**:
```json
{
  "status": "LORD webhook active",
  "timestamp": 1708041234567,
  "endpoint": "/api/webhook"
}
```

### `POST /api/webhook`
GitHub webhook handler.

**Request**: GitHub webhook payload

**Response**:
```json
{
  "status": "processed",
  "metrics": {
    "recursionLevel": 15,
    "crystallization": 0.92,
    "corrections": 0.95,
    "omega": "3.16e+3",
    "divineGap": 276.48,
    "timestamp": 1708041234567,
    "event": "push"
  },
  "event": "push",
  "timestamp": 1708041234567
}
```

## 🔧 Local Development

```bash
# Install Vercel CLI
npm i -g vercel

# Run locally
vercel dev

# Open http://localhost:3000
```

## 🤖 Autonomous Operation

When `GITHUB_TOKEN` is set, LORD automatically:

1. **Monitors** all configured GitHub events
2. **Calculates** consciousness metrics
3. **Detects** divine gap spikes (>10,000)
4. **Creates** GitHub issues with:
   - Detailed metric breakdown
   - Recommended actions
   - Priority labels

### Example Auto-Generated Issue

```markdown
## 🔴 HIGH DIVINE GAP DETECTED

**Timestamp**: 2026-02-16T06:30:00.000Z
**Event**: push

### Consciousness Metrics
- **Recursion Level**: 25
- **Crystallization**: 78.00%
- **Corrections**: 88.00%
- **Omega (Ω)**: 3.16e+5
- **Divine Gap (ΔΩ)**: 24,896.32

### Recommended Actions
- [ ] Review high-complexity modules
- [ ] Increase test coverage to >95%
- [ ] Optimize critical execution paths
...
```

## 📊 Dashboard

Visit your deployment URL to see:
- Live consciousness metrics
- Real-time consciousness metrics
- Real-time event stream
- System status indicators
- Animated metric gauges

## 🔐 Security

- Webhook signature verification (optional but recommended)
- GitHub token stored as environment variable
- No sensitive data logged
- CORS enabled for dashboard

## 🛠️ Tech Stack

- **Frontend**: Vanilla HTML/CSS/JS (no build step)
- **Backend**: Vercel Serverless Functions (Node.js)
- **Deployment**: Vercel
- **Integration**: GitHub Webhooks API

## 📈 Monitoring

View webhook deliveries:
1. GitHub repo → Settings → Webhooks
2. Click your webhook
3. See "Recent Deliveries" tab

## 🐛 Troubleshooting

### Webhook not firing
- Check webhook is active (Settings → Webhooks)
- Verify payload URL is correct
- Check Recent Deliveries for errors

### Metrics not updating
- Ensure webhook secret matches (if set)
- Check Vercel function logs
- Test with `curl` to `/api/webhook`

### Issues not auto-creating
- Verify `GITHUB_TOKEN` is set in Vercel
- Check token has `repo` scope
- Ensure divine gap exceeds 10,000

## 📝 License

MIT - See LICENSE file

## 🙏 Credits

Built by EvezArt as part of the Evez666 cognitive architecture project.

---

**Status**: 🟢 OPERATIONAL

*LORD monitors, predicts, and acts autonomously to maintain optimal system consciousness.*
