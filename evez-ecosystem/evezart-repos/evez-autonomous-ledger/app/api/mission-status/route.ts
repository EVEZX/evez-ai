import { NextResponse } from 'next/server';
import { DEFAULT_AGENT_REGISTRY } from '@/lib/agents/registry';

export const runtime = 'nodejs';

export async function GET() {
  return NextResponse.json({
    ok: true,
    status: 'ready',
    surfaces: {
      health: '/api/health',
      run: '/api/run',
      resume: '/api/resume',
      stop: '/api/stop',
      registry: '/api/agents/registry',
      workspacePlan: '/api/workspace-plan',
      executionFeed: '/api/execution-feed',
      activeContext: '/api/active-context',
    },
    counts: {
      enabledAgents: DEFAULT_AGENT_REGISTRY.filter((a) => a.enabled).length,
    },
    ts: new Date().toISOString(),
  });
}
