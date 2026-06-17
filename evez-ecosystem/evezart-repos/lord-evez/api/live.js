async function fetchJson(url, headers = {}) {
  try {
    const response = await fetch(url, {
      headers,
      signal: AbortSignal.timeout(8000),
    });
    if (!response.ok) {
      return { ok: false, status: response.status, data: null };
    }
    return { ok: true, status: response.status, data: await response.json() };
  } catch (error) {
    return { ok: false, status: 0, error: error.message, data: null };
  }
}

function normalizeEvents(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload.slice(0, 20);
  if (Array.isArray(payload.events)) return payload.events.slice(0, 20);
  if (Array.isArray(payload.items)) return payload.items.slice(0, 20);
  return [];
}

function normalizeAgentCount(payload) {
  if (!payload) return 0;
  if (Array.isArray(payload)) return payload.length;
  if (Array.isArray(payload.agents)) return payload.agents.length;
  if (payload.agents && typeof payload.agents === 'object') return Object.keys(payload.agents).length;
  return 0;
}

function normalizeRevenue(payload) {
  if (!payload) return 0;
  if (typeof payload.total_revenue_usd === 'number') return payload.total_revenue_usd;
  if (typeof payload.revenue_usd === 'number') return payload.revenue_usd;
  if (typeof payload.total === 'number') return payload.total;
  return 0;
}

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');

  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const base = (process.env.EVEZ_OS_BASE || process.env.NEXT_PUBLIC_EVEZ_OS_BASE || '').replace(/\/$/, '');
  const apiKey = process.env.EVEZ_API_KEY || process.env.NEXT_PUBLIC_EVEZ_API_KEY || '';

  if (!base) {
    return res.status(200).json({
      ok: false,
      configured: false,
      message: 'Set EVEZ_OS_BASE or NEXT_PUBLIC_EVEZ_OS_BASE to enable live bridge',
      metrics: {
        spineHealth: 'unconfigured',
        agentCount: 0,
        fireEventCount: 0,
        isolationSignals: 0,
        revenueUsd: 0,
      },
      events: [],
      fetchedAt: Date.now(),
    });
  }

  const headers = apiKey ? { 'X-EVEZ-API-KEY': apiKey } : {};
  const [health, agents, events, isolation, revenue] = await Promise.all([
    fetchJson(`${base}/health`, headers),
    fetchJson(`${base}/api/agents/status`, headers),
    fetchJson(`${base}/api/fire/events`, headers),
    fetchJson(`${base}/api/telemetry/isolation`, headers),
    fetchJson(`${base}/api/stripe/revenue`, headers),
  ]);

  const normalizedEvents = normalizeEvents(events.data);
  const isolationSignals = Array.isArray(isolation.data)
    ? isolation.data.length
    : Array.isArray(isolation.data?.items)
      ? isolation.data.items.length
      : 0;

  return res.status(200).json({
    ok: true,
    configured: true,
    base,
    fetchedAt: Date.now(),
    metrics: {
      spineHealth: health.ok ? 'ok' : 'degraded',
      agentCount: normalizeAgentCount(agents.data),
      fireEventCount: normalizedEvents.length,
      isolationSignals,
      revenueUsd: normalizeRevenue(revenue.data),
    },
    upstream: {
      health: { ok: health.ok, status: health.status },
      agents: { ok: agents.ok, status: agents.status },
      events: { ok: events.ok, status: events.status },
      isolation: { ok: isolation.ok, status: isolation.status },
      revenue: { ok: revenue.ok, status: revenue.status },
    },
    events: normalizedEvents,
    raw: {
      health: health.data,
      agents: agents.data,
      isolation: isolation.data,
      revenue: revenue.data,
    },
  });
}
