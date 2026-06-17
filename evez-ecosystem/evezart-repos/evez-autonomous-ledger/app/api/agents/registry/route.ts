import { NextResponse } from 'next/server';
import { DEFAULT_AGENT_REGISTRY } from '@/lib/agents/registry';

export const runtime = 'nodejs';

export async function GET() {
  return NextResponse.json({
    ok: true,
    agents: DEFAULT_AGENT_REGISTRY,
    ts: new Date().toISOString(),
  });
}
